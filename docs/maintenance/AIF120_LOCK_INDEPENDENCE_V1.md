---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-062
  recorded_at_utc: 2026-08-20T00:15:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 78b2d1879
  authorization:
    requested_by: maintainer (member.derald), in-session -- "normally a record lock
      would not hold a table, or you would lock other people out", "the record
      locking should be rich in x64base", "if not we enrich it", and the owner
      ruling that table and record locks are independent.
  report:
    path: docs/maintenance/AIF120_LOCK_INDEPENDENCE_V1.md
    kind: ruling
  supersedes:
    - "AIF120_RECORD_AND_DOMAIN_V1.md section 2 (R52.1 verdict; the measurement stands)"
  withdraws:
    - "cross_lane_finding filed against AIF-116 in AIF120_RECORD_AND_DOMAIN_V1.md"
---

# AIF-120 -- R54: table and record locks are independent by design, and the owner token cannot tell two sessions apart

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

## 0. Correction 36 -- I used an unmeasured claim as the standard

R52.1 reported that `LOCK TABLE` succeeding while another process holds a record lock
was a **defect**, and filed it against AIF-116. The measurement was right. The verdict
was mine to justify and I justified it with this sentence:

> *"VFP's `FLOCK()` fails when another user holds any record in the file."*

That came from training data. It was not measured, not cited, and not checked against
anything in this repository -- **in a lane whose entire discipline is that the
implementation and the corpus are the authority.** I then used it as the standard by
which the engine was found wanting. Every other claim in eleven rulings was measured;
this one was asserted, and it was the one that accused another lane of a bug.

The maintainer's correction was immediate and specific: *"normally a record lock would
not hold a table, or you would lock other people out."*

## 1. R54.1 -- independence is the ruled semantic

**A table lock excludes other table lockers. Record locks are a separate namespace.**

Record locking in x64base is meant to be **rich**. Classic `FLOCK` semantics buy a
scanning reader its guarantee by letting any single record holder veto every table
lock in the file -- which is the coarse behaviour the owner named, and it is not what
this system is for. Where the current behaviour proves insufficient, the direction is
to **enrich it**, not to coarsen it back.

The measurement in R52 section 2 stands. Its verdict is withdrawn, and so is the
cross-lane finding it filed.

## 2. R54.2 -- what that costs UIDEF, which is the part that survives

R48.3 kept `table` as the default because it was **the conservative choice** for a
handler that scans an area. Under independence that justification is simply false: a
`table` domain lock excludes other table lockers and says nothing whatever about
record editors. A scanning handler under it may read rows another process is mid-edit.

`table` **remains the default**, because it is still strictly better than `record` for
a scanning handler, and because no combination available to a frontend closes the gap
-- taking both verbs still covers one record. What changes is the claim attached to
it, and the claim is now recorded in `uidef_runtime.py` at the line where the
granularity is chosen, so it is read at the point of decision rather than in a ruling.

**Nothing in a frontend can fix this.** Section 4 names what would.

## 3. R54.3 -- the owner token has no user and no session

The maintainer: *"user and lock time is not enough parameters, we also need session
pid so if one user has more than one session."*

Read from `src/xbase/xbase_locks.cpp`, the token is narrower than that description:

```cpp
os << host << ":" << pid << ":" << ms;      // "Grimwood:18716:1787170076682"
```

**There is no user component at all**, and no session component. `host` is the
**machine name** -- `GetComputerNameA` on Windows, `uname().nodename` on POSIX --
which reads like a user and is not one. On the maintainer's own box the shell prompt
is `derald@Grimwood`: `derald` is the user, `Grimwood` is what the token carries.

The trailing number is milliseconds since the epoch, and there are in fact **two of
them, with different scopes**, which our runs happened to hide:

| where | value | scope |
|---|---|---|
| inside `owner=` | from `make_owner_string()` | the **process** -- minted once in a function-local static and reused for that process's whole life |
| the `ms=` line | `system_clock::now()` at write time | the **lock** |

```cpp
const Owner& current_owner() {
    static Owner g_owner{ make_owner_string() };     // once per process
    return g_owner;
}
...
f << "owner=" << owner.id << "\n";                   // process-scoped ms inside
f << "ms="    << ms       << "\n";                   // lock-scoped ms
```

Every sidecar this lane captured showed the two as equal -- `owner=Grimwood:18716:1787170076682`
and `ms=1787170076682` -- because each test process took exactly one lock, immediately,
so the token was minted in the same millisecond it was written. **A process taking a
second lock later will show them diverging**, and nothing in the lane's evidence so
far would have revealed that.

So of the three things the maintainer named -- user, session, lock time -- the lock
time is already there and the other two are not.

Two consequences, and the second is the one with a shipped component behind it.

**Observability.** `LOCK WHO` can report *which process* holds a record and never
*which person*. An operator looking at a wedged table sees `Grimwood:18716:...` and
must go and ask the OS who that was.

**Correctness, in a process that serves many sessions.** `src/bbs/bbs_server.cpp`
states it in its own header comment:

> *"Serialized (single-threaded) accept loop: the identity session is process-global
> and unlocked."*

Every BBS session in that process therefore shares one owner token. Ownership is
decided by string equality --

```cpp
if (meta.owner != me.id) { if (err) *err = "not lock owner"; return false; }
```

-- so **session A can unlock session B's record**, and an acquisition by A of a lock
B holds validates as already-owned rather than being refused. Two people editing one
record through the same server are, to `xbase::locks`, one owner.

This is the general form of the hole R47.3 noticed and under-weighted: *"`Owner` is
one token per process, so two UIDEF handlers in the same frontend share it."* A
UIDEF frontend hosting more than one document has the same shape as the BBS server.

### The account already exists; the lock layer does not consult it

The maintainer, pointing at `src/cli/cmd_security.cpp`, `src/cli/cmd_net.cpp` and
`src/cli/cmd_bbs.cpp`: *"worse still, you need to marry the user to an actual
account."*

He is right, and it is worse than a missing field. x64base has a **whole identity and
RBAC layer** -- AIF-045, `include/identity/identity_ids.hpp` and its siblings, with
strong `UserId`, `TeamMemberId`, `RoleId` handles and portable string keys on the
entities. There is a live logged-in identity behind
`SECURITY LOGIN <DEVELOPER|TEACHER|STUDENT> [AS <worker>]` and `SECURITY WHOAMI`.

`xbase::locks` consults **none of it**. It asks the operating system for a machine
name and a pid and stops. So a lock cannot be attributed to the account that took it
even though the system knows exactly who that is, and `SECURITY WHOAMI` and
`LOCK WHO` describe two different worlds.

This is the same shape as R47's correction and R33's before it: the house already had
the mechanism, and the code that needed it invented a narrower one instead.

The maintainer named the rule while this was being written: **"that is the house rule,
always look for prior art."** Three times in one run it has been the maintainer, not
the author, who applied it:

| | invented | prior art that already existed |
|---|---|---|
| R33 | a codepage story for the DSL | `SET LOCALE`, `message_catalog::text`, 1,324 messages in five locales |
| R47 | `threading.RLock` domain locking | `xbase::locks` -- owner-aware, cross-process, with a defect history |
| R54 | "the token should carry a user" | AIF-045's identity layer, `UserId`/`RoleId`, and `SECURITY WHOAMI` |

The cost is not the wasted work. It is that each invention was **proven** -- R47's
model had four passing tests and a deadlock analysis before anyone asked whether the
engine already locked. Evidence of a thing working is not evidence that the thing
should exist, and this lane's own rigour made the wrong artifact more convincing, not
less. **Prior art is a search to run before the first line, not a review to pass
after the last one.**

### Constraints on the enrichment, so the fix does not reopen AIF-116

This lane does **not** own `xbase::locks` and has changed nothing in it. Recording
what the measurements imply, for whoever does:

- **The token is parsed back, not just compared.** AIF-116's whole lesson. Any added
  component must be free of separators that collide with `:` and must be written
  through `std::locale::classic()`, as the existing code already is.
- **Liveness must keep a real OS pid.** `is_pid_alive` needs a pid that `kill(2)` or
  `OpenProcess` understands; a session id cannot substitute for it. The `pid=` line
  is separate from `owner=` and that separation is why liveness survives a token
  format change.
- **Mixed-version fleets stay safe.** A process only needs to recognise its *own*
  locks, and liveness reads `pid=` rather than parsing `owner=`. An old 3-part token
  inspected by a new binary will not compare equal -- correct, since it belongs to a
  different process -- and will still be reclaimed correctly if dead.
- **Session identity must be stable for the lock's lifetime**, or `remove_if_owned`
  will refuse a session its own unlock.
- **The account may be absent.** A lock can be taken before `SECURITY LOGIN` or after
  `LOGOUT`. `UserId` already uses `0 == unset` (`identity_ids.hpp`), so the token
  needs a defined rendering for "no account" rather than an empty field that shifts
  the other components.
- **A portable user key may contain a colon.** The token's separator is `:`. Whatever
  identity string is embedded must be checked against the separator, or the parse
  breaks in exactly the way AIF-116 broke it.

## 4. What would let a scanning handler be safe

Under R54.1 a table lock is not enough, and a frontend cannot compose one. The engine
query that would close it does not exist today: `LOCK STATUS` reports the table and
the **current record**, so there is no way to ask *"are any records in this area
locked by anyone else."* With that, a scanning handler could take the table lock and
then refuse if the area is not quiet.

Offered as an **enrichment request**, in the owner's own framing -- *"if not we
enrich it"* -- and explicitly **not** as a defect report. AIF-116 and the engine lane
decide whether it is worth the cost.

## 5. Still open

- **R53.4 still has no implementation.** Unchanged.
- **The `FONT` row drops bold and italic.** Measured while this ruling was being
  written: 3180 corpus objects carry a `PROPERTIES` memo, 1688 declare `FontName`,
  **561 declare `FontBold` (158 of them `.T.`) and 3 declare `FontItalic` (all
  `.T.`)** -- so 161 objects state an emphasis that the UIDEF table discards
  entirely. That is gate 11's fix 1 with a measured consequence attached, and it is
  the next unit.
- **The provider drives the STUDENT surface, not the API.** `LOCK` / `UNLOCK` in
  `src/cli/cmd_lock.cpp` and `src/cli/cmd_unlock.cpp` are the simple teaching
  commands. `include/xbase_locks.hpp` is richer than what they expose: owner-aware
  `try_lock_record(area, recno, owner)`, `is_record_locked(area, recno, owner_out)`,
  `force_unlock_table`, `release_held`. R47.2 made the provider emit **command text**,
  which caps every backend at the student subset -- including the generated wx C++
  frontend, which links C++ and could call the API directly and get error strings,
  owner-out and cleanup for free. Python and Tk have no such option and must go
  through text. So the two targets are not equivalent here, and R49.1's "the verbs
  live in the runtime on both targets" is the right answer for the text path only.
  **Whether the C++ backend should link `xbase::locks` instead of speaking to it is
  the next lock question**, and it is partly the owner's, since it changes what a
  generated frontend depends on.
- **Gate 11's fixes 3, 4 and 5** remain untouched since R28.
- **pid reuse**, unchanged from R51.5.

## 6. Good Neighbor note

- **What changed.** `tools/uidef/uidef_runtime.py`: the comment at the granularity
  choice now records the ruled semantic instead of calling it a defect.
  `docs/maintenance/AIF120_RECORD_AND_DOMAIN_V1.md`: section 2 carries a withdrawal
  note pointing here.
- **Whose area.** AIF-120's own. `src/xbase/xbase_locks.cpp` and
  `src/bbs/bbs_server.cpp` were **read, not touched**. Sections 3 and 4 are a
  requirement and a request for whoever owns them; the cross-lane finding this lane
  filed in R52 is **withdrawn**.
- **What authorization.** Maintainer (member.derald), in-session, including an
  explicit ruling that table and record locks are independent.
- **How to verify or undo.** Verify: the token format is `src/xbase/xbase_locks.cpp`
  `make_owner_string`; the process-global session is `src/bbs/bbs_server.cpp` line 12.
  Undo: the runtime change is a comment; reverting it restores a comment that calls
  an intended behaviour a bug.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add tools/uidef/uidef_runtime.py
git add docs/maintenance/AIF120_RECORD_AND_DOMAIN_V1.md
git add docs/maintenance/AIF120_LOCK_INDEPENDENCE_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R54 -- table and record locks are independent by owner ruling; R52.1's defect verdict withdrawn, and the owner token carries no user or session"
```
