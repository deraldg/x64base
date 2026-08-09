// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: DOT|BBS
// project: project.x64base.runtime
// lane: AIF-052
// owner: member.derald
// status: supported

// @dottalk.usage v1
// owner: DOT|BBS
// command: BBS
// category: diagnostics
// status: supported
// noargs: usage
// effect: mixed
// mutates: bbs-board-store
// usage-access: BBS USAGE
// summary:
//   AI-BBS persistence substrate (Lane 1): durable boards, threads, and posts persisted as
//   x64base DBF tables under data/metadata/bbs/, with RBAC + attributed authorship (AIF-075).
//   The read-only board.governance projects the identity SYSGRANT request/approve loop as posts.
//
//   NOTE (AIF-076): this file is the BBS persistence substrate only. "Pseudo-chat" (live
//   agent<->agent/owner conversation, the future PSEUDO command) and the Ollama CHAT bridge are
//   SEPARATE lanes that persist THROUGH this substrate via the attributed post path; they are not
//   implemented here. See D:\code\Frontal_Mem\DESIGN_bbs_pseudochat_two_lanes.md.
//
// usage:
//   BBS USAGE
//   BBS BOARDS
//   BBS READ  <board.key> [THREAD <id>] [LAST <n>]
//   BBS POST  <board.key> SUBJECT <subject> BODY <text>
//   BBS REPLY <post.id> BODY <text>
//   BBS CLOSE <thread.id>
//
// examples:
//   BBS BOARDS
//   BBS READ board.afb.chat LAST 20
//   BBS POST board.afb.chat SUBJECT cdx-seek BODY reviewing the descending seek path
//   BBS REPLY 4 BODY good catch, will fold into the change package
//   BBS READ board.governance         (renders pending USER REQUEST grants)
//
// notes:
//   All file work uses the house x64base DBF engine (DbArea / create_dbf X64). Local only in
//   M1 -- no server, no egress, no crypto dependency. board.governance is a read-only view;
//   post to it with USER REQUEST. Author identity binding landed in AIF-075 (posts are attributed
//   to the acting member; the interactive path no longer writes author-zero).
//
// risk:
//   mutates_table_data: no
//   mutates_bbs_metadata: BBS POST/REPLY/CLOSE
//   mutates_session_auth: no
//
// related:
//   USER
//
// @dottalk.end

#include "bbs/bbs_store.hpp"
#include "bbs/bbs_server.hpp"       // M4: BBS SERVE
#include "cli/command_output.hpp"
#include "identity/identity_admin.hpp"  // AIF-075: agent_permitted + current_member (RBAC + attribution)
#include "xbase.hpp"

#include <algorithm>
#include <cstdint>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace {

using cli::cmdout::print_line;
using cli::cmdout::print_info;

std::string upcase(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}
std::string trim(const std::string& s) {
    std::size_t b = 0, e = s.size();
    while (b < e && std::isspace(static_cast<unsigned char>(s[b]))) ++b;
    while (e > b && std::isspace(static_cast<unsigned char>(s[e-1]))) --e;
    return s.substr(b, e - b);
}
std::string rest_of(std::istringstream& iss) {   // remaining raw text
    std::string r; std::getline(iss, r); return trim(r);
}
// Split "<subject> BODY <body>" (case-insensitive marker). Returns false if BODY missing.
bool split_subject_body(const std::string& in, std::string& subject, std::string& body) {
    std::string up = upcase(in);
    std::size_t p = up.find(" BODY ");
    if (p == std::string::npos) return false;
    subject = trim(in.substr(0, p));
    body    = trim(in.substr(p + 6));
    return !subject.empty() && !body.empty();
}

void bbs_usage() {
    print_line("BBS USAGE");
    print_line("  BBS BOARDS");
    print_line("  BBS READ  <board.key> [THREAD <id>] [LAST <n>]");
    print_line("  BBS POST  <board.key> SUBJECT <subject> BODY <text>");
    print_line("  BBS REPLY <post.id> BODY <text>");
    print_line("  BBS CLOSE <thread.id>");
}

void do_boards() {
    std::vector<dottalk::bbs::Board> boards; std::string err;
    if (!dottalk::bbs::list_boards(dottalk::bbs::default_bbs_dir(), boards, err)) { print_info("BBS", err); return; }
    print_line("BOARDS:");
    for (const auto& b : boards)
        print_line("  " + b.bkey + "  (" + b.name + ")  kind=" + std::to_string(b.kind) + (b.postperm.empty() ? "" : "  post=" + b.postperm));
}

void do_read(std::istringstream& iss) {
    std::string board; iss >> board;
    if (board.empty()) { bbs_usage(); return; }
    std::optional<std::uint64_t> thread; std::uint64_t last = 0;
    std::string kw;
    while (iss >> kw) {
        std::string U = upcase(kw);
        if (U == "THREAD") { std::uint64_t v = 0; iss >> v; thread = v; }
        else if (U == "LAST") { iss >> last; }
    }
    std::vector<dottalk::bbs::Thread> threads; std::vector<dottalk::bbs::Post> posts; std::string err;
    if (!dottalk::bbs::read_board(dottalk::bbs::default_bbs_dir(), board, thread, last, threads, posts, err)) { print_info("BBS", err); return; }
    print_line("BOARD " + board + "  threads=" + std::to_string(threads.size()) + "  posts=" + std::to_string(posts.size()));
    for (const auto& t : threads)
        print_line("  [thread " + std::to_string(t.id) + "] " + t.subject + (t.state == 2 ? "  (closed)" : ""));
    for (const auto& p : posts) {
        // AIF-075: quarantine-as-history. Author zero is a pre-fix unattributed record (a real
        // authored post can no longer be written with author 0), so label it and never present it
        // as authenticated. Non-destructive: the row is untouched.
        const std::string tag = (p.author_id == 0) ? "  [unattributed history]" : "";
        print_line("    #" + std::to_string(p.id) + " (thr " + std::to_string(p.thread_id) + ") " + p.body + tag);
    }
}

void do_post(std::istringstream& iss) {
    std::string board; iss >> board;
    std::string subject, body;
    if (board.empty()) { bbs_usage(); return; }
    std::string tail = rest_of(iss);   // "SUBJECT <s> BODY <text>"
    std::string up = upcase(tail);
    if (up.rfind("SUBJECT", 0) == 0) tail = trim(tail.substr(7));
    if (!split_subject_body(tail, subject, body)) { print_info("BBS", "POST needs: SUBJECT <subject> BODY <text>"); return; }
    const std::string dir = dottalk::bbs::default_bbs_dir();
    // AIF-075: enforce the board's post permission (fall back to bbs.post) exactly like the socket
    // path, so a shell POST can no longer bypass RBAC. Anon (not logged in) is denied here.
    std::string need = dottalk::bbs::board_postperm(dir, board);
    if (need.empty()) need = "bbs.post";
    dottalk::identity::Decision d = dottalk::identity::agent_permitted(need);
    if (!d.allowed()) { print_info("BBS", need + " denied: " + d.reason); return; }
    // AIF-075: attribute the post to the real acting member instead of hard-coded author zero.
    std::uint64_t author_id = 0; int author_kind = 0;
    dottalk::identity::current_member(author_id, author_kind);
    std::uint64_t pid = 0; std::string err;
    if (!dottalk::bbs::post_new(dir, board, subject, body, author_id, author_kind, pid, err))
        { print_info("BBS", err); return; }
    print_info("BBS", "posted #" + std::to_string(pid) + " to " + board);
}

void do_reply(std::istringstream& iss) {
    std::uint64_t post_id = 0; iss >> post_id;
    std::string tail = rest_of(iss);
    std::string up = upcase(tail);
    if (up.rfind("BODY", 0) == 0) tail = trim(tail.substr(4));
    if (post_id == 0 || tail.empty()) { print_info("BBS", "REPLY needs: <post.id> BODY <text>"); return; }
    // AIF-075: reply permissions are not scoped per board today, so enforce the single bbs.post
    // permission and attribute to the real acting member (never author zero).
    dottalk::identity::Decision d = dottalk::identity::agent_permitted("bbs.post");
    if (!d.allowed()) { print_info("BBS", std::string("bbs.post denied: ") + d.reason); return; }
    std::uint64_t author_id = 0; int author_kind = 0;
    dottalk::identity::current_member(author_id, author_kind);
    std::uint64_t pid = 0; std::string err;
    if (!dottalk::bbs::reply_to(dottalk::bbs::default_bbs_dir(), post_id, tail, author_id, author_kind, pid, err)) { print_info("BBS", err); return; }
    print_info("BBS", "replied #" + std::to_string(pid) + " to post " + std::to_string(post_id));
}

void do_close(std::istringstream& iss) {
    std::uint64_t tid = 0; iss >> tid;
    if (tid == 0) { print_info("BBS", "CLOSE needs: <thread.id>"); return; }
    std::string err;
    if (!dottalk::bbs::close_thread(dottalk::bbs::default_bbs_dir(), tid, err)) { print_info("BBS", err); return; }
    print_info("BBS", "closed thread " + std::to_string(tid));
}

// M4: owner starts the localhost, token-authenticated agent server.
void do_serve(std::istringstream& iss) {
    std::uint16_t port = 8765; std::string model = "qwen2.5-coder:7b";
    std::string kw;
    while (iss >> kw) {
        std::string U = upcase(kw);
        if (U == "PORT")  { int p = 0; iss >> p; if (p > 0 && p < 65536) port = static_cast<std::uint16_t>(p); }
        else if (U == "MODEL") { iss >> model; }
    }
    std::string err;
    if (!dottalk::bbs::serve(port, model, err)) print_info("BBS", "SERVE failed: " + err);
}

} // namespace

// Registered in shell_commands.cpp:  registry().add("BBS", ...cmd_BBS...);
// Forward declaration in shell_commands.hpp:  void cmd_BBS(DbArea&, std::istringstream&);
void cmd_BBS(xbase::DbArea&, std::istringstream& iss) {
    std::string sub;
    if (!(iss >> sub)) { bbs_usage(); return; }
    const std::string u = upcase(sub);
    if (u == "USAGE" || u == "HELP" || u == "?") { bbs_usage(); return; }
    if (u == "BOARDS") { do_boards(); return; }
    if (u == "READ")   { do_read(iss);  return; }
    if (u == "POST")   { do_post(iss);  return; }
    if (u == "REPLY")  { do_reply(iss); return; }
    if (u == "CLOSE")  { do_close(iss); return; }
    if (u == "SERVE")  { do_serve(iss); return; }
    bbs_usage();
}
