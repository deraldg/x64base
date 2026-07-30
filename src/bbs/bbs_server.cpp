// @dottalk.file v1
// subsystem: bbs
// layer: glue
// owns: 
// project: project.x64base.runtime
// lane: AIF-052
// owner: member.derald
// status: supported

// bbs_server.cpp -- localhost token-authenticated BBS/agent server + Ollama bridge (M4).
//
// Serialized (single-threaded) accept loop: the identity session is process-global and unlocked.
// Auth reuses the real credential path via login() (Argon2id in M3). Chat is bridged to the local
// Ollama over a minimal raw-socket HTTP/1.1 client (localhost plaintext; no TLS).
//
// Protocol (line-based, UTF-8; server frames each response with a lone "." line):
//   -> AUTH <member.key> <token>
//   <- OK <display> | ERR <reason>          (must AUTH first)
//   -> CHAT <text...>                        (requires chat.invoke)
//   -> BBS READ <board.key>                  (requires bbs.read)
//   -> BBS POST <board.key> <subject> :: <body>   (requires bbs.post)
//   -> QUIT                                  (close connection)
//   -> SHUTDOWN                              (owner only; stops the server)
//
// THIS IS THE HIGHEST-RISK SLICE. Review the bind address, the auth gate, and the request-size
// caps before trusting it. Requires M3 (token crypto) -- do not run on placeholder crypto.
//
// LANE NOTE (AIF-076): this server carries THREE distinct concerns that must not be conflated.
// (1) BBS = the persistence substrate (durable, attributed posts; Lane 1). (2) CHAT = the Ollama
// agent<->model bridge (Lane 3). (3) pseudo-chat = live agent<->agent/owner conversation (Lane 2,
// the future PSEUDO command) which is NOT the same as CHAT. Lanes 2 and 3 persist THROUGH the BBS
// substrate via the attributed post path. See DESIGN_bbs_pseudochat_two_lanes.md.

#include "bbs/bbs_server.hpp"
#include "bbs/bbs_store.hpp"
#include "identity/identity_admin.hpp"
#include "identity/identity_bootstrap.hpp"     // find_member_by_key, identity_store
#include "selfdoc/event_record.hpp"            // M5: runtime->doc intake

#include <nlohmann/json.hpp>

#include <cctype>
#include <iostream>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

#if defined(_WIN32)
#  include <winsock2.h>
#  include <ws2tcpip.h>
#  pragma comment(lib, "ws2_32.lib")
   using socket_t = SOCKET;
   static const socket_t kBadSock = INVALID_SOCKET;
   static int  sock_close(socket_t s) { return ::closesocket(s); }
   static int  sock_errno()           { return ::WSAGetLastError(); }
   static constexpr int kSendFlags = 0;             // no SIGPIPE on Windows
#else
#  include <sys/socket.h>
#  include <netinet/in.h>
#  include <arpa/inet.h>
#  include <unistd.h>
#  include <sys/time.h>
#  include <cerrno>
#  include <csignal>
   using socket_t = int;
   static const socket_t kBadSock = -1;
   static int  sock_close(socket_t s) { return ::close(s); }
   static int  sock_errno()           { return errno; }
   // Linux has MSG_NOSIGNAL per-send; macOS/BSD do not (they use SO_NOSIGPIPE or a global
   // handler). We also ignore SIGPIPE process-wide below, so a peer that drops mid-write
   // yields EPIPE instead of killing the daemon on every POSIX platform.
#  if defined(MSG_NOSIGNAL)
   static constexpr int kSendFlags = MSG_NOSIGNAL;
#  else
   static constexpr int kSendFlags = 0;
#  endif
#endif

using nlohmann::json;

// Status logging decoupled from cli::cmdout so the standalone dottalk_bbsd daemon need not link
// the message-catalog subsystem. Goes to stderr (both dottalkpp and the daemon share this).
static void print_info(const char* cmd, const std::string& s) {
    std::cerr << (cmd && *cmd ? std::string(cmd) + ": " : std::string()) << s << "\n";
}

namespace dottalk::bbs {
namespace {

constexpr std::size_t kMaxLine = 64 * 1024;   // per-request cap (defends against unbounded reads)

// Cascade guard for the simplex gate. The accept loop is serialized: one connection at a time. A
// client that connects and then waits for the next line (for example two agents each trying to hold
// a live chat through this one-at-a-time gate) would block recv_line forever and wedge the single
// slot, and every other client queues behind it indefinitely -- the "rabbit hole". A receive timeout
// makes an idle connection drop itself so the gate frees. Default ON; overridable via the
// DOTTALK_BBS_IDLE_TIMEOUT_SEC environment variable (0 disables). This does NOT bound a CHAT: the
// Ollama call happens server-side between reads, not while waiting on the client.
constexpr int kIdleTimeoutSec = 120;

int idle_timeout_sec() {
    if (const char* e = std::getenv("DOTTALK_BBS_IDLE_TIMEOUT_SEC")) {
        char* end = nullptr;
        long v = std::strtol(e, &end, 10);
        if (end != e && v >= 0 && v <= 86400) return static_cast<int>(v);
    }
    return kIdleTimeoutSec;
}

void set_recv_timeout(socket_t s, int seconds) {
    if (seconds <= 0) return;                  // 0 = disabled (blocking, legacy behavior)
#if defined(_WIN32)
    DWORD ms = static_cast<DWORD>(seconds) * 1000u;
    ::setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, reinterpret_cast<const char*>(&ms), sizeof ms);
#else
    timeval tv{}; tv.tv_sec = seconds; tv.tv_usec = 0;
    ::setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, reinterpret_cast<const char*>(&tv), sizeof tv);
#endif
}

// ---- winsock lifecycle ----
struct NetInit {
    bool ok = true;
#if defined(_WIN32)
    NetInit()  { WSADATA w{}; ok = (WSAStartup(MAKEWORD(2,2), &w) == 0); }
    ~NetInit() { if (ok) WSACleanup(); }
#else
    // Ignore SIGPIPE so a client that disconnects mid-send does not terminate the daemon.
    // send() then returns -1/EPIPE, which send_all() already treats as a failed write.
    NetInit()  { ::signal(SIGPIPE, SIG_IGN); }
#endif
};

bool send_all(socket_t s, const char* p, std::size_t n) {
    while (n) {
        int m = ::send(s, p, static_cast<int>(n), kSendFlags);
        if (m <= 0) return false;
        p += m; n -= static_cast<std::size_t>(m);
    }
    return true;
}
bool send_line(socket_t s, const std::string& line) {
    std::string out = line; out += "\r\n";
    return send_all(s, out.data(), out.size());
}

// Read one line (up to kMaxLine), stripping trailing CR/LF. Returns false on close/error/overflow.
bool recv_line(socket_t s, std::string& out) {
    out.clear();
    char c;
    for (;;) {
        int m = ::recv(s, &c, 1, 0);
        if (m <= 0) return false;
        if (c == '\n') break;
        if (c != '\r') out.push_back(c);
        if (out.size() > kMaxLine) return false;
    }
    return true;
}

// ---- minimal HTTP/1.1 POST to a localhost plaintext endpoint (Ollama) ----
// Returns the response body; sets err and returns empty on failure.
std::string http_post_local(const char* host, std::uint16_t port,
                            const std::string& path, const std::string& body, std::string& err) {
    socket_t s = ::socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (s == kBadSock) { err = "socket() failed"; return {}; }
    sockaddr_in addr{}; addr.sin_family = AF_INET; addr.sin_port = htons(port);
    ::inet_pton(AF_INET, host, &addr.sin_addr);
    if (::connect(s, reinterpret_cast<sockaddr*>(&addr), sizeof addr) != 0) {
        err = "connect to Ollama failed (is it running on 127.0.0.1:11434?)"; sock_close(s); return {};
    }
    std::string req =
        "POST " + path + " HTTP/1.1\r\n"
        "Host: " + std::string(host) + "\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: " + std::to_string(body.size()) + "\r\n"
        "Connection: close\r\n\r\n" + body;
    if (!send_all(s, req.data(), req.size())) { err = "send to Ollama failed"; sock_close(s); return {}; }

    std::string resp; char buf[4096];
    for (;;) {
        int m = ::recv(s, buf, sizeof buf, 0);
        if (m <= 0) break;                 // Connection: close -> read to EOF
        resp.append(buf, static_cast<std::size_t>(m));
    }
    sock_close(s);
    auto pos = resp.find("\r\n\r\n");
    if (pos == std::string::npos) { err = "malformed HTTP response from Ollama"; return {}; }
    return resp.substr(pos + 4);           // body (non-stream JSON)
}

// ---- capability check for the currently-acting member ----
bool require(socket_t s, const char* perm) {
    dottalk::identity::Decision d = dottalk::identity::agent_permitted(perm);
    if (!d.allowed()) { send_line(s, std::string("ERR ") + perm + " denied: " + d.reason); send_line(s, "."); return false; }
    return true;
}

// ---- one CHAT request -> Ollama -> reply ----
void do_chat(socket_t s, const std::string& model, const std::string& text) {
    if (!require(s, "chat.invoke")) return;
    json reqj = { {"model", model}, {"prompt", text}, {"stream", false} };
    std::string err;
    std::string body = http_post_local("127.0.0.1", 11434, "/api/generate", reqj.dump(), err);
    if (!err.empty()) { send_line(s, "ERR " + err); send_line(s, "."); return; }
    std::string reply;
    try { json j = json::parse(body); reply = j.value("response", std::string()); }
    catch (const std::exception& e) { send_line(s, std::string("ERR bad JSON from Ollama: ") + e.what()); send_line(s, "."); return; }
    send_line(s, "OK");
    // send the reply as data lines, then a lone "." terminator
    std::size_t start = 0;
    while (start <= reply.size()) {
        std::size_t nl = reply.find('\n', start);
        std::string ln = (nl == std::string::npos) ? reply.substr(start) : reply.substr(start, nl - start);
        if (ln == ".") ln = " .";           // dot-stuffing so a lone '.' isn't a terminator
        send_line(s, ln);
        if (nl == std::string::npos) break;
        start = nl + 1;
    }
    send_line(s, ".");
}

// ---- BBS READ / POST over the wire (identity-bound author) ----
std::uint64_t current_member_id(int& kind_out) {
    // Delegate to the shared identity helper so the socket and the interactive CLI attribute
    // authorship identically (AIF-075).
    std::uint64_t id = 0;
    dottalk::identity::current_member(id, kind_out);
    return id;
}

void do_bbs(socket_t s, std::istringstream& iss) {
    std::string op; iss >> op;
    for (auto& c : op) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    const std::string dir = dottalk::bbs::default_bbs_dir();
    std::string err;
    if (op == "READ") {
        if (!require(s, "bbs.read")) return;
        std::string board; iss >> board;
        std::vector<Thread> th; std::vector<Post> po;
        if (!read_board(dir, board, std::nullopt, 0, th, po, err)) { send_line(s, "ERR " + err); send_line(s, "."); return; }
        send_line(s, "OK");
        // AIF-075: mark pre-fix author-zero posts as unattributed history over the wire too, so a
        // client can never mistake them for authenticated authorship. Non-destructive.
        for (const auto& p : po)
            send_line(s, "#" + std::to_string(p.id) + (p.author_id == 0 ? " [unattributed history] " : " ") + p.body);
        send_line(s, ".");
    } else if (op == "POST") {
        std::string board; iss >> board;
        std::string rest; std::getline(iss, rest);
        auto sep = rest.find(" :: ");
        if (board.empty() || sep == std::string::npos) { send_line(s, "ERR POST needs: <board> <subject> :: <body>"); send_line(s, "."); return; }
        // Honor the board's own POSTPERM (e.g. board.guestbook -> bbs.guest) instead of a single
        // global bbs.post. Unknown/legacy boards fall back to bbs.post; post_new rejects the
        // read-only board.governance regardless.
        std::string need = dottalk::bbs::board_postperm(dir, board);
        if (need.empty()) need = "bbs.post";
        if (!require(s, need.c_str())) return;
        std::string subject = rest.substr(0, sep);
        // trim leading space
        std::size_t b = subject.find_first_not_of(' '); if (b != std::string::npos) subject = subject.substr(b);
        std::string body = rest.substr(sep + 4);
        int kind = 0; std::uint64_t author = current_member_id(kind);
        std::uint64_t pid = 0;
        if (!post_new(dir, board, subject, body, author, kind, pid, err)) { send_line(s, "ERR " + err); send_line(s, "."); return; }
        send_line(s, "OK posted #" + std::to_string(pid)); send_line(s, ".");
    } else {
        send_line(s, "ERR BBS READ|POST"); send_line(s, ".");
    }
}

// ---- handle one authenticated connection; returns true if server should shut down ----
bool handle_conn(socket_t s, const std::string& model, const std::string& operator_key) {
    bool shutdown = false;
    // 1) AUTH gate -- must be first line.
    std::string line;
    if (!recv_line(s, line)) return false;
    {
        std::istringstream iss(line); std::string cmd, member, token;
        iss >> cmd >> member >> token;
        for (auto& c : cmd) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        if (cmd != "AUTH" || member.empty() || token.empty()) { send_line(s, "ERR AUTH <member> <token> required first"); send_line(s, "."); return false; }
        dottalk::identity::AdminResult r = dottalk::identity::login(member, token);   // Argon2id verify (M3)
        if (!r.ok) { send_line(s, "ERR auth failed"); send_line(s, "."); return false; }   // do not leak which of member/token was wrong
        send_line(s, "OK " + dottalk::identity::acting_member_key()); send_line(s, ".");
    }
    // 2) command loop
    while (recv_line(s, line)) {
        std::istringstream iss(line); std::string cmd; iss >> cmd;
        std::string U = cmd; for (auto& c : U) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        if (U == "QUIT" || U.empty()) break;
        if (U == "CHAT")  { std::string text; std::getline(iss, text); if (!text.empty() && text[0]==' ') text.erase(0,1); do_chat(s, model, text); }
        else if (U == "BBS") { do_bbs(s, iss); }
        else if (U == "SHUTDOWN") {
            if (dottalk::identity::is_owner_member(dottalk::identity::acting_member_key())) { send_line(s, "OK shutting down"); send_line(s, "."); shutdown = true; break; }
            send_line(s, "ERR SHUTDOWN is owner-only"); send_line(s, ".");
        }
        else { send_line(s, "ERR unknown command"); send_line(s, "."); }
    }
    // (M5) intake: write a proof/run transcript for this agent session.
    dottalk::selfdoc::record_event("runtime", "bbs_serve_session",
        dottalk::identity::acting_member_key(), "agent connection handled", {});
    // 3) drop this connection's session; restore the operator between connections
    dottalk::identity::logout();
    dottalk::identity::set_acting_member(operator_key);
    return shutdown;
}

} // namespace

bool serve(std::uint16_t port, const std::string& model, std::string& err) {
    NetInit net;
#if defined(_WIN32)
    if (!net.ok) { err = "WSAStartup failed"; return false; }
#endif
    const std::string operator_key = dottalk::identity::acting_member_key();   // saved; restored on exit

    socket_t srv = ::socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (srv == kBadSock) { err = "socket() failed"; return false; }
    // Exclusive port ownership. On Windows, SO_REUSEADDR lets a SECOND process co-bind the same
    // addr:port and silently hijack/split connections -- that is what produced the double-daemon
    // instances. SO_EXCLUSIVEADDRUSE makes a second instance fail bind() loudly ("address in use")
    // instead. POSIX has no such hijack (SO_REUSEADDR there only rebinds a TIME_WAIT port and cannot
    // steal an active listener), so it stays the right choice for fast restart.
    int yes = 1;
#if defined(_WIN32)
    ::setsockopt(srv, SOL_SOCKET, SO_EXCLUSIVEADDRUSE, reinterpret_cast<const char*>(&yes), sizeof yes);
#else
    ::setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, reinterpret_cast<const char*>(&yes), sizeof yes);
#endif

    sockaddr_in addr{}; addr.sin_family = AF_INET; addr.sin_port = htons(port);
    // LOOPBACK ONLY. Never INADDR_ANY -- this is the network-exposure boundary.
    ::inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr);
    if (::bind(srv, reinterpret_cast<sockaddr*>(&addr), sizeof addr) != 0) {
        err = "bind 127.0.0.1:" + std::to_string(port) + " failed (err " + std::to_string(sock_errno()) + ")";
        sock_close(srv); return false;
    }
    if (::listen(srv, 4) != 0) { err = "listen failed"; sock_close(srv); return false; }

    print_info("BBS SERVE", "listening on 127.0.0.1:" + std::to_string(port) + "  model=" + model +
                            "  (loopback only; Ctrl-C or owner SHUTDOWN to stop)");

    const int idle = idle_timeout_sec();
    if (idle > 0)
        print_info("BBS SERVE", "simplex cascade guard: idle connections drop after " +
                                std::to_string(idle) + "s (DOTTALK_BBS_IDLE_TIMEOUT_SEC to change; 0 = off)");

    bool stop = false;
    while (!stop) {
        socket_t c = ::accept(srv, nullptr, nullptr);
        if (c == kBadSock) { continue; }
        set_recv_timeout(c, idle);                     // cascade guard: no client may wedge the gate
        stop = handle_conn(c, model, operator_key);    // serialized: one connection at a time
        sock_close(c);
    }
    sock_close(srv);
    dottalk::identity::set_acting_member(operator_key);   // ensure operator restored
    print_info("BBS SERVE", "stopped");
    return true;
}

} // namespace dottalk::bbs
