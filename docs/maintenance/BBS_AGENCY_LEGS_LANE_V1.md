# BBS Agency Legs Lane V1

    lane        : AIF-083
    claim       : coordination/aif/AIF-083.claim
    run         : 2026-07-31_cowork_bbs_agency_legs
    owner       : member.derald
    steward     : member.ai.claude.cowork
    created_utc : 2026-07-31T20:38:44Z
    updated_utc : 2026-07-31T20:38:44Z
    baseline    : 57b87f07d (development, pushed)
    parent      : project.x64base.runtime
    status      : findings recorded, NO source change landed, NO runtime evidence
    evidence    : F1-F5 source-evidenced with file:line; ZERO runtime

---

## 0. Scope calibration (declared before authoring)

```text
operating_mode: maintenance
change_class: C0 as filed (findings only). Any fix is C2 -- it changes enforcement
  behaviour on a security surface.
build_target: dottalkpp_runtime
product_profile: not_applicable
index_profile: not_applicable
owning_lifecycle: DotTalk++ SDLC
sdlc_lane: intake / design
truth_state: source-defined
proof_state: report. NO build, NO runtime, NO .dts executed. The steward cannot
  run the engine (measured: sandbox glibc 2.35 against the binary's required
  2.38). Every runtime question below is a maintainer handoff.
risk_class: the findings concern an enforcement surface, so a careless fix is
  higher risk than the defects. Nothing is fixed in this filing.
scope_reason: read-only audit of the BBS command, store, and daemon paths against
  the four legs of AGENCY_MODEL_V1.
affected_authorities: AI_BBS_OPERATIONS_RUNBOOK_V1, AGENCY_MODEL_V1, AIF-075,
  AIF-052, the bbs schema.
minimum_gate_set: file:line anchor for every claim; prior-art check before the
  claim was allocated; house style sweep.
deferred_gates_and_residual_risk: no runtime tier earned. F1-F5 are what the
  source says, not what the engine does.
```

## 1. Why this lane exists, and why it is not AIF-075 reopened

`AGENCY_MODEL_V1.md` states the frame this lane audits against:

> Agency is the capacity to act, plus accountability for having acted. Capacity
> without accountability is a hazard. Accountability without capacity is a
> fiction. This system refuses to separate them.

Four legs: **identity, authority, authentication, accountability**, ordered so
that authentication gates authority, authority is scoped to identity, and
accountability outlives all three.

AIF-075 fixed the interactive shell bypassing the RBAC and attribution the socket
enforced. **Its title scopes it to POST and REPLY**, and it did exactly that. The
findings here are the remainder of the same class on the verbs that fix did not
name. This lane does not reopen AIF-075; it finishes the sweep AIF-075 started.

The agency model also explains why the sweep was never obvious: the system
implemented agency thoroughly and never named it, so "each mechanism looked like
a local engineering choice rather than one expression of a single idea." Once the
legs are named, the missing ones are visible by inspection.

---

## 2. Findings

### F1 -- `BBS CLOSE` mutates board state with no leg but capacity

`src/cli/cmd_bbs.cpp`, `do_close`: no `agent_permitted`, no `current_member`.
The store path `bbs_store.cpp:341` `close_thread` takes a `TableLock` and writes
`STATE`, and records nothing about who did it.

Both halves matter and they are different failures:

- **Authority leg absent.** Any acting member, including the boot default
  `member.public` (unauthenticated), can close any thread by id.
- **Accountability leg absent at the SCHEMA level.** `SYSTHREAD` carries
  `OPENEDBY` and has no `CLOSEDBY` (`include/bbs/bbs_schema.hpp:64-69`). Even
  with a permission check added, the act would remain unattributable. This is not
  a missing call site; it is a missing column.

This is the model's named hazard, verbatim: capacity without accountability.

**Sharpest of the five.** It is the only BBS write path with no gate at all, and
the only one whose attribution cannot be added without a schema change.

### F2 -- `bbs.read` is enforced on one surface and ignored on the other

| Surface | READ |
| --- | --- |
| daemon `bbs_server.cpp:242` | `require(s, "bbs.read")` |
| shell `cmd_bbs.cpp` `do_read` | no check |

`bbs.read` is a declared, resolvable permission. On the socket it gates; in the
shell it does not exist. That is the AIF-079 declared-capability shape applied to
an authority leg: the permission is real, its enforcement is half-present.

Structural cause, and it is the interesting part: the daemon funnels every gated
verb through a single `require()` helper (`bbs_server.cpp:197-201`), while the
CLI calls `agent_permitted` inline at two sites and nowhere else. **One surface
has a chokepoint, the other has scattered call sites.** That asymmetry is how the
original AIF-075 drift happened and why it recurred on the verbs the fix did not
touch. A fix that only adds two more inline calls rebuilds the same trap.

### F3 -- REPLY ignores per-board post permission, and the value is already in hand

`do_post` resolves `board_postperm(dir, board)` and falls back to `bbs.post`
(`cmd_bbs.cpp:153-156`). `do_reply` enforces the bare `bbs.post`
(`cmd_bbs.cpp:174`), with an honest comment: *"reply permissions are not scoped
per board today."*

A reply IS a post: same `SYSPOST` table, `KIND=1` versus `KIND=0`
(`bbs_store.cpp:298` and `:324`). So a board whose `POSTPERM` refuses you for
POST accepts you for REPLY.

The comment reads as "unimplemented". It is closer to "unwritten":
`reply_to` already resolves the parent post's board at `bbs_store.cpp:315`
(`bid = r.u64("BOARDID")`). The value the check needs is fetched one layer down,
a few lines after the point the check would occupy.

### F4 -- `BBS READ ... LAST 20` reads every post on the board

`read_board` (`bbs_store.cpp:234-270`) scans `SYSTHREAD` and `SYSPOST` from
record 1 to `recCount64()`, filtering `BOARDID` in memory. No index. The `last_n`
window is applied **after** the full load (`:268`, `posts.erase(begin, end-n)`).

Not a defect today at board sizes of tens. It is a structural property that
collides with what the BBS is being asked to become: *Toward Persistent Memory*
makes the board the consolidation bus between sessions, so it is designed to
accumulate. An accumulating store read at O(all posts) per access, whose windowed
read is only a post-filter, does not scale into that role.

Related and adjacent: `read_board` also projects live `SYSGRANT` rows into
`board.governance` on every read (`:262-266`).

### F5 -- a BBS post body is 240 characters, and the bus cannot carry the cargo

`include/bbs/bbs_schema.hpp:47`:

```
inline constexpr std::uint32_t BODY = 240;  // M1 post body (C field; memo upgrade deferred)
```

The memory thesis names the BBS as the channel by which one session's
consolidated knowledge reaches the next. Nothing this lane produced today would
fit: the AIF-082 closeout is ~36 KB, a single Session Log row is 1-2 KB.

The schema comment already knows -- *memo upgrade deferred*. Recorded here
because two lanes now want the same work from opposite directions: AIF-082's
6.10 proposes dogfooding the read-manifest onto the 64-bit memo structure, and
the BBS needs that upgrade for its own primary purpose. **One piece of work, two
lanes wanting it**, which is worth reconciling before either starts.

---

## 3. What is NOT claimed

No runtime evidence. The steward cannot execute the engine -- measured, not
assumed: the staged `bin-wsl-lean` binary requires `GLIBC_2.38` and
`GLIBCXX_3.4.32`; the sandbox provides 2.35 and 3.4.30, and the loader refuses.

So F1-F5 state what the source says. They do not state what the engine does.
Three questions would move them to `runtime-observed`, and each is minutes of
maintainer time (section 5).

Not filed as security incidents. This is a loopback-only, single-operator system
whose daemon binds `127.0.0.1` and whose CLI runs as the owner in practice. The
findings matter because the portal admits non-owner AI members and because the
model says enforcement must be real rather than conventional -- not because a
remote attacker is implied.

---

## 4. Milestones

| Milestone | Deliverable | Gate |
| --- | --- | --- |
| **M0** | This charter: F1-F5 source-evidenced, prior art checked, agency frame applied. **DONE 2026-07-31.** | every claim carries file:line; AIF-075 scope confirmed by its own title |
| **M1** | Owner rulings on F1-F5 severity and sequence | recorded in this file |
| **M2** | Runtime evidence for the three questions in section 5 | maintainer-run transcript, committed, not left in `tmp/` |
| **M3** | F2 fix: a CLI-side `require()` chokepoint mirroring `bbs_server.cpp:197`, so the two surfaces share one gate shape | every BBS verb routes through it; adding a verb without a gate becomes visibly odd |
| **M4** | F3 fix: scope REPLY to the parent board's `POSTPERM` | a member refused POST on a restricted board is refused REPLY into it, runtime-proven |
| **M5** | F1 fix: `CLOSEDBY`/`CLOSEDAT` columns plus a permission check | closing is attributable AND authorised; schema change, so it owes a migration note |
| **M6** | F4/F5 reconciled with the memory lane before either is built | one design covering the memo body and the read path, not two |

**M3 before M4 and M5, deliberately.** Adding two more inline permission calls
would fix the symptom and rebuild the structure that produced it. The chokepoint
is the fix; the individual gates are what it then makes easy.

---

## 5. Runtime questions owed (maintainer handoff)

Each is a few commands. None requires a build.

1. **Does the shell READ bypass actually read?** As an unauthenticated session
   (boot default `member.public`), run `BBS READ board.lounge LAST 5`. If posts
   come back, F2 is runtime-confirmed. The socket path should refuse the same
   read without `bbs.read`.
2. **Does CLOSE succeed unauthenticated?** `BBS CLOSE <thread.id>` as
   `member.public`. Confirms F1's authority half.
3. **Does a 300-character body truncate or refuse?** POST a body longer than 240
   and read it back. Confirms F5's practical shape -- silent truncation would be
   a data-loss finding in its own right, and the "reports success without doing
   its job" class again.

Tokens are cached at daemon startup, so per the runbook mint while stopped and
then start. Note the two surfaces take different POST grammars: the socket wants
`<board> <subject> :: <body>`, the CLI wants `SUBJECT <s> BODY <t>`.

---

## 6. Anchor table

| Claim | Anchor |
| --- | --- |
| F1 no gate | `src/cli/cmd_bbs.cpp` `do_close`; `src/bbs/bbs_store.cpp:341` |
| F1 no CLOSEDBY column | `include/bbs/bbs_schema.hpp:64-69` |
| F2 socket gates read | `src/bbs/bbs_server.cpp:242` |
| F2 single funnel vs scattered | `src/bbs/bbs_server.cpp:197-201` vs `src/cli/cmd_bbs.cpp:155,174` |
| F3 POST is board-scoped | `src/cli/cmd_bbs.cpp:153-156` |
| F3 REPLY is not | `src/cli/cmd_bbs.cpp:172-175` |
| F3 board already resolved | `src/bbs/bbs_store.cpp:315` |
| F3 reply is a post | `src/bbs/bbs_store.cpp:298`, `:324` (KIND 0 vs 1) |
| F4 full scan | `src/bbs/bbs_store.cpp:245`, `:253` |
| F4 window applied after load | `src/bbs/bbs_store.cpp:268` |
| F5 body width | `include/bbs/bbs_schema.hpp:47` |
| agency four legs | `docs/ai-friendly/AGENCY_MODEL_V1.md` sec 1 |
| AIF-075 scope | intake queue row AIF-075 |
| runbook, token caching, POST grammar | `docs/maintenance/AI_BBS_OPERATIONS_RUNBOOK_V1.md` sec 1, 4, 5 |

---

## 7. Method note

This lane was produced by reading, on maintainer instruction to stop building and
educate first. That instruction was correct and the record should say why: the
session had previously drafted an M4 test plan for this surface from headers and
string tables alone, without reading a single implementation. Two of the five
findings above are invisible from a header -- F3's already-resolved board id and
F4's post-load windowing are properties of the function bodies.

The corollary for `AI_PORTAL.md`'s *Build It to Prove It*: reading source is not
the same as reading its interface, and an audit built on interfaces will confirm
the design rather than test it.
