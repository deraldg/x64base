# AI BBS M4.1 -- per-session identity design (v1)

Status: **design-only** (review-needed). Authored in a mounted sandbox that cannot
build or run the engine; every code claim below is read from source, not compiled.
The build + proof steps are a maintainer-operated handoff.

Owner: `member.derald`
Author: `member.ai.claude.cowork`
Lane: AIF-052 (BBS agent-server) -- concurrency milestone M4.1. **AIF number to be
claimed host-side** (`claim-aif` shells to `git grep`; not runnable here).
Prior art read: `AI_BBS_LANE_V1.md` (S4 "Serialized handling", S8 "M4.1"),
`AGENCY_MODEL_V1.md` ("No per-session identity"), `src/bbs/bbs_server.cpp`,
`src/tools/bbsd_main.cpp`, `src/identity/identity_admin.cpp`.

## 1. What M4.1 is, and what it is NOT

**M4.1 is one thing:** make the identity a **per-connection** value so the accept
loop can serve more than one connection at a time. Today the loop is serialized
*because* identity is a single process-global; that is the whole reason for the
simplex gate and the idle-timeout "cascade guard" (`bbs_server.cpp` S99-103).

**M4.1 is NOT** the Ollama-as-agent work. Giving the local model its own identity
(`member.ai.ollama.local`) with bounded permissions and a proof harness is a
**separate downstream milestone** that M4.1 merely unblocks. The taxonomy
(`AI_ROLES_TAXONOMY_V1.md`) is explicit: Ollama is a model an agent invokes, not an
agent. Conflating the two is the trap. This doc draws the boundary at S7 and stops.

## 2. Current state (read from source, exact)

The socket path keeps **all** mutable session state in three process-global strings
in one anonymous namespace, `src/identity/identity_admin.cpp` S310-312:

```
std::string g_principal    = kAnon;   // "member.public"
std::string g_acting       = kAnon;
bool        g_authenticated = false;
```

Every socket read of identity funnels through free functions over those globals:
`acting_member_key()` (S366), `principal_key()` (S363), `session_authenticated()`
(S364), `current_member()` (S372), `agent_permitted()` (S447). Every mutation is
`login()` (S381), `logout()` (S404), `set_acting_member()` (S367), `act_as()` (S429).

The accept loop, `src/bbs/bbs_server.cpp` S353-360:

```
while (!stop) {
    socket_t c = ::accept(srv, nullptr, nullptr);
    set_recv_timeout(c, idle);
    stop = handle_conn(c, model, operator_key);   // serialized: one at a time
    sock_close(c);
}
```

`handle_conn` (S277) calls `login()` (writes the globals), runs the command loop,
then restores with `logout()` + `set_acting_member(operator_key)` (S308-309). A
second concurrent connection is impossible not by a lock but by construction: it
would clobber the same three globals mid-request. That save/restore dance is the
manual stand-in for what per-connection storage should do automatically.

**Concurrency finding (the reason M4.1 is tractable).** The only shared mutable
process state on the socket path is those three globals:

- The **BBS store** path (`src/bbs/bbs_store.cpp`) carries **no** process-global or
  static mutable state (grep for `static`/`g_`/`thread_local`: none). `read_board`
  and `post_new` take the store directory as a parameter and, per repo doctrine
  (CLAUDE.md "Shared store + locking"), the write path already takes a per-append
  table FLOCK via `xbase::locks`. Cross-process append safety exists today.
- The **identity store** (`identity_store()`) is loaded from DBF once at startup and
  is **read-only over the socket** -- `login`/`agent_permitted`/`current_member` only
  read it. The socket protocol exposes no path that writes it (`set_password`,
  `act_as`-persist, member add/remove are CLI-only, never reachable from
  `handle_conn`'s command set: AUTH/CHAT/BBS/QUIT/SHUTDOWN).
- The **Ollama bridge** (`http_post_local`, S167) opens its own socket per call and
  shares nothing.

So the concurrency problem is narrow: isolate the three identity globals per
connection, and confirm the shared *reads* are safe under concurrent readers.

## 3. Target

Two viable shapes. Recommend A for M4.1 scope; record B as the eventual "proper"
form so the choice is deliberate, not defaulted.

### Approach A (recommended for M4.1): thread-local session, thread-per-connection

Change the storage class of the three globals from plain to `thread_local`, spawn
one worker thread per accepted connection, and let each worker's login/logout touch
its own copy. The identity API signatures do **not** change, so blast radius is
confined to (a) three lines in `identity_admin.cpp` and (b) the accept loop.

- `thread_local std::string g_principal / g_acting; thread_local bool g_authenticated;`
- Each worker thread begins with fresh defaults (`kAnon`, unauthenticated) -- which is
  exactly correct: a new connection must AUTH before it can act. The per-connection
  `logout()` + `set_acting_member(operator_key)` restore dance in `handle_conn`
  becomes unnecessary (thread isolation replaces it); leave a single defensive
  `logout()` at thread end so nothing lingers if threads are ever pooled.
- The main thread keeps the operator identity for its own bookkeeping only; workers
  never touch it.

Why thread_local and not a lock around the globals: a mutex would re-serialize the
very thing we are trying to parallelize (each request holds identity across its whole
lifetime, including the multi-second Ollama call). Per-thread storage removes the
sharing instead of contending on it.

### Approach B (eventual, out of M4.1 scope): explicit `Session` object

Thread a `Session&` (principal, acting, authenticated) through every
`agent_permitted`/`current_member`/`acting_member_key` call. Architecturally clean
(no hidden globals, no TLS), but the blast radius is every caller across the CLI
(`cmd_*.cpp`) and the socket. That is a broad refactor and should be its own lane,
not smuggled into M4.1. Note it so the TLS choice is understood as a scoped
compromise, not the end state.

## 4. The concurrency change, precisely

1. **`identity_admin.cpp` S310-312:** add `thread_local` to the three declarations.
   Nothing else in that file changes; all accessors already go through them.
2. **`bbs_server.cpp` accept loop:** replace the in-line `handle_conn` call with a
   worker launch. Recommended: a **bounded** worker count (not unbounded detach) so
   N concurrent connections cannot spawn N concurrent Ollama model calls without
   limit. The existing `listen(srv, 4)` backlog and a small max-inflight counter
   (atomic, e.g. default 4, env `DOTTALK_BBS_MAX_INFLIGHT`) keep the loopback
   educational daemon from over-committing the box. Over the cap: either queue or
   reply `ERR busy` and close -- pick one and document it.
3. **Shutdown:** `SHUTDOWN` today sets a local `stop` that breaks the loop. With
   workers, promote it to a `std::atomic<bool>` the owner's worker sets, plus a
   self-connect or `accept` timeout so the main loop wakes and exits. Join
   outstanding workers before `sock_close(srv)`.
4. **Shared sinks:** `print_info` (stderr) and `selfdoc::record_event` (S305) can now
   be hit by multiple threads. stderr interleaving is cosmetic. `record_event`
   (`selfdoc/event_record.cpp`, read this pass) writes a **per-call unique
   timestamped file** with no shared handle, no process global, and no store
   mutation -- it is essentially thread-safe as written. Two trivial caveats, neither
   a corruption risk: (a) two events with the same kind+slug in the same wall-clock
   second collide on filename (one overwrites the other) -- add a thread id or counter
   to the name; (b) it uses `std::localtime`, which returns a pointer into a shared
   static buffer (a benign data race that can garble the timestamp string, not the
   store) -- switch to `localtime_r`/`localtime_s`. Both are one-line fixes.

## 5. Invariants to preserve (do not regress)

- **Loopback only.** `bind` stays `127.0.0.1` (S337-338); concurrency does not widen
  exposure.
- **AUTH-first per connection.** Each worker starts unauthenticated; the first line
  must be AUTH (S280-290) or the connection is dropped. Fresh thread_local defaults
  enforce this automatically.
- **No socket-reachable identity-store writes.** The command set stays
  AUTH/CHAT/BBS/QUIT/SHUTDOWN. If a future command would mutate the identity store,
  the read-only-under-concurrency assumption breaks and this design must be revisited.
- **Attribution stays single-sourced (AIF-075).** `current_member()` remains the one
  authorship resolver; per-thread identity means concurrent posts attribute to the
  correct distinct authors instead of whoever last wrote the global.
- **Owner exemption unchanged.** `agent_permitted` owner-exemption (S452-454) is a
  pure read; safe under concurrent readers.

## 6. Proof plan (maintainer-operated; sandbox cannot run it)

1. Build both targets Release (`dottalkpp`, `dottalk_bbsd`), daemon rebuild requires
   `Stop-ScheduledTask -TaskName 'DotTalkBBSD'` first (CLAUDE.md).
2. **Concurrency proof:** two clients AUTH as two *different* members and each POST at
   the same time; confirm two posts land with the two correct distinct `author_id`s
   (not one author for both, not author-zero). This is the test that fails today.
3. **Isolation proof:** client A holds a slow CHAT while client B does a BBS READ;
   confirm B is served without waiting for A (the simplex gate is gone) and A's
   identity is not visible to B.
4. **Cap proof:** open `MAX_INFLIGHT + 1` connections; confirm the policy (queue or
   `ERR busy`) holds and the daemon does not spawn unbounded threads/model calls.
5. **Shutdown proof:** owner `SHUTDOWN` with workers in flight; confirm clean join and
   no orphaned threads (and the port frees for restart).
6. Regression: existing M4/M6 single-client AUTH/CHAT/POST proofs still pass.

## 7. Boundary -- what M4.1 unblocks but does not do

Once identity is per-connection, a *distinct* identity can act per session. That is
the prerequisite the taxonomy names for giving the local model its own agency. The
**next** milestone (call it M4.2, separate lane/AIF) would: create
`member.ai.ollama.local`, grant it a bounded permission set (`bbs.read`, `bbs.post`,
`chat.invoke` -- **never** `source.mutate` or `host.network.egress`), stand up a
harness that drives an Ollama turn under that identity, and produce a proof that it
posts as itself while the egress block holds. M4.1 stops at the mechanism. Do not
create `member.ai.ollama.local` in this milestone -- it has nothing to bind to until
per-session identity exists, and adding it now would be an ungated identity with no
proof.

## 8. No open source reads remain

Every code claim in this design is grounded in source read this pass:
`bbs_server.cpp`, `bbsd_main.cpp`, `identity_admin.cpp` (session block S300-464),
`bbs_store.cpp` (no shared mutable state), and `selfdoc/event_record.cpp` (per-call
file, thread-safe modulo the two one-line caveats in S4). What remains is build +
proof (S6), which is a maintainer-operated handoff -- the sandbox cannot compile or
run the engine. Recommended order for the coding session: (1) the three one-line
fixes (thread_local declarations, record_event filename + localtime_r), (2) the
accept-loop worker launch with the bounded in-flight cap, (3) the shutdown join, then
the S6 proofs in sequence.
