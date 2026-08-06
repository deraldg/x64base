# AI BBS M4.1 -- reviewable patch spec (v1)

Status: **patch spec, NOT applied to source.** Authored in a sandbox that cannot
compile; edits 1-2 are mechanical and ready to apply, edits 3-4 are a **reference
implementation to compile and PROVE** (concurrency correctness must be shown by the
M4.1 proofs, not assumed). Apply on the host, build Release, run the proof ladder in
`AI_BBS_M4X_BUILD_RUNSHEET_V1.md`.

Design: `AI_BBS_M4_1_PER_SESSION_IDENTITY_DESIGN_V1.md`. Owner: `member.derald`.
Complete the mutation preflight (`SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`) and a
scoped commit per file. ASCII-only added lines.

---

## Edit 1 -- `src/identity/identity_admin.cpp` (S310-312) -- APPLY AS-IS

Make the process-global session per-thread. This is the whole concurrency unlock;
every accessor already funnels through these three.

BEFORE:
```
std::string g_principal    = kAnon;
std::string g_acting       = kAnon;
bool        g_authenticated = false;
```
AFTER:
```
thread_local std::string g_principal    = kAnon;
thread_local std::string g_acting       = kAnon;
thread_local bool        g_authenticated = false;
```
Note: `kAnon` is a `constexpr const char*`; each thread's `std::string` is
initialized from it on first use. Worker threads therefore start unauthenticated
(`kAnon`) -- which is exactly correct: a fresh connection must AUTH first. The main
thread keeps its own copy (the operator identity set in `serve()`), isolated from
workers.

---

## Edit 2 -- `src/selfdoc/event_record.cpp` -- APPLY AS-IS

Two one-line thread-safety fixes (see design S4 item 4): unique filename per call so
two same-second same-slug events do not collide, and `localtime_r`/`localtime_s`
instead of the shared-buffer `std::localtime`.

Add includes near the top (after `<fstream>`):
```
#include <sstream>
#include <thread>
```
BEFORE:
```
        std::time_t t = std::time(nullptr);
        char ts[32]; std::strftime(ts, sizeof ts, "%Y%m%d_%H%M%S", std::localtime(&t));
        const std::string name = std::string(ts) + "_" + kind + "_" + slug + ".txt";
```
AFTER:
```
        std::time_t t = std::time(nullptr);
        std::tm tmbuf{};
#if defined(_WIN32)
        localtime_s(&tmbuf, &t);
#else
        localtime_r(&t, &tmbuf);
#endif
        char ts[32]; std::strftime(ts, sizeof ts, "%Y%m%d_%H%M%S", &tmbuf);
        std::ostringstream tid; tid << std::this_thread::get_id();
        const std::string name = std::string(ts) + "_" + tid.str() + "_" + kind + "_" + slug + ".txt";
```

---

## Edit 3 -- `src/bbs/bbs_server.cpp` accept loop -- REFERENCE IMPL (compile + prove)

Replace the serialized `handle_conn` call with a bounded, interruptible,
worker-per-connection loop. Uses `select()` on the listen socket so shutdown can
wake a blocked `accept()` portably (no self-connect trick), an atomic in-flight cap,
and detached workers with a bounded drain (no growing thread vector).

Add includes (with the others near S42):
```
#include <atomic>
#include <thread>
#include <chrono>
```
Add a small env-bound cap helper near `idle_timeout_sec()`:
```
int bbs_max_inflight() {
    if (const char* e = std::getenv("DOTTALK_BBS_MAX_INFLIGHT")) {
        char* end = nullptr; long v = std::strtol(e, &end, 10);
        if (end != e && v >= 1 && v <= 64) return static_cast<int>(v);
    }
    return 4;
}
```
BEFORE (S353-360):
```
    bool stop = false;
    while (!stop) {
        socket_t c = ::accept(srv, nullptr, nullptr);
        if (c == kBadSock) { continue; }
        set_recv_timeout(c, idle);                     // cascade guard: no client may wedge the gate
        stop = handle_conn(c, model, operator_key);    // serialized: one connection at a time
        sock_close(c);
    }
    sock_close(srv);
```
AFTER:
```
    std::atomic<bool> stop{false};
    std::atomic<int>  inflight{0};
    const int max_inflight = bbs_max_inflight();
    while (!stop.load()) {
        // Interruptible accept: select with a 1s timeout so a worker's SHUTDOWN
        // (stop=true) is noticed even while no client is connecting.
        fd_set rf; FD_ZERO(&rf); FD_SET(srv, &rf);
        timeval tv{}; tv.tv_sec = 1; tv.tv_usec = 0;
        if (::select(static_cast<int>(srv) + 1, &rf, nullptr, nullptr, &tv) <= 0)
            continue;                                  // timeout/interrupt: re-check stop
        socket_t c = ::accept(srv, nullptr, nullptr);
        if (c == kBadSock) continue;
        if (inflight.load() >= max_inflight) {         // bounded: do not over-commit the box
            send_line(c, "ERR busy"); send_line(c, ".");
            sock_close(c); continue;
        }
        set_recv_timeout(c, idle);
        inflight.fetch_add(1);
        std::thread([c, &model, &operator_key, &stop, &inflight]() {
            if (handle_conn(c, model, operator_key)) stop.store(true);
            sock_close(c);
            inflight.fetch_sub(1);
        }).detach();
    }
    // drain: let in-flight workers finish before closing the listen socket (bounded ~5s)
    for (int i = 0; i < 100 && inflight.load() > 0; ++i)
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    sock_close(srv);
```
Correctness to PROVE (not assume): two concurrent distinct-author POSTs land with
two correct `author_id` (needs Edit 1); the `select` loop exits promptly on
SHUTDOWN; the cap returns `ERR busy` past `max_inflight`; no worker touches a closed
socket after drain. On Windows, `select`'s first arg is ignored but pass it for
POSIX; `fd_set`/`FD_SET` are available via the already-included `winsock2.h`.

---

## Edit 4 -- `src/bbs/bbs_server.cpp` `handle_conn` tail (S304-310) -- REFERENCE IMPL

With per-thread identity the operator save/restore dance is moot (each worker's
identity dies with its thread). Keep a defensive `logout()`; drop the
operator-restore line.

BEFORE:
```
    // (M5) intake: write a proof/run transcript for this agent session.
    dottalk::selfdoc::record_event("runtime", "bbs_serve_session",
        dottalk::identity::acting_member_key(), "agent connection handled", {});
    // 3) drop this connection's session; restore the operator between connections
    dottalk::identity::logout();
    dottalk::identity::set_acting_member(operator_key);
    return shutdown;
```
AFTER:
```
    // (M5) intake: write a proof/run transcript for this agent session.
    dottalk::selfdoc::record_event("runtime", "bbs_serve_session",
        dottalk::identity::acting_member_key(), "agent connection handled", {});
    // 3) per-thread identity: this worker's session dies with the thread. A
    //    defensive logout clears it in case threads are ever pooled.
    dottalk::identity::logout();
    return shutdown;
```
`operator_key` is still used by `serve()` (main thread) at S320/S362; leave those.
It is no longer needed inside `handle_conn` -- if the signature keeps the parameter,
mark it `(void)operator_key;` or drop it from the worker capture in Edit 3.

---

## Apply / prove order

1. Edit 1, Edit 2 (mechanical) -> build -> single-client M4/M6 regression still green.
2. Edit 3, Edit 4 (threading) -> build -> run the M4.1 exit proofs
   (`AI_BBS_M4X_BUILD_RUNSHEET_V1.md`): concurrent distinct authors, CHAT/READ
   isolation, cap, shutdown join/drain, regression.
3. Commit per file, scoped. Then M4.2 (seed `member.ai.ollama.local` + harness).
