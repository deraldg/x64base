---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-008
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local
  git:
    branch: development
    baseline_commit: fb7106e0
    working_tree: dirty
    note: >
      Baseline is the RUNTIME banner stamp reported by the running binary
      ("dottalk++ v0.6 (2026-08-15, fb7106e0 dirty)"), not `git rev-parse HEAD`.
      The evidence below is runtime-observed against that exact binary.
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: maintainer (member.derald), in-session, live AIF-112 Phase-1 run
    scope: >
      Finding report. Discovered while executing AIF-112 Phase-1 Step 4 on a live
      instance. No source mutation. AIF-116 claimed host-side by the owner via
      session_coordinator.py claim-aif; not self-assigned.
  lane: AIF-116
  lane_discovered_in: AIF-112
  lane_blocking_dependency: AIF-113
  lane_parent_defect_class: AIF-031
  report:
    path: docs/maintenance/LOCK_OWNER_STRING_LOCALE_GROUPING_DEFEATS_MUTUAL_EXCLUSION_V1.md
    kind: defect_report
  primary_topics:
    - "xbase_locks"
    - "mutual exclusion"
    - "AIF-031"
    - "locale grouping"
    - "stale lock recovery"
---

# Locale Grouping in the Lock Owner String Defeats Mutual Exclusion (V1)

**Status:** runtime-observed, reproduced, root-caused to file:line, **and FIXED
and re-proven the same session at build `fe42666e`** -- see section 13.
**Severity:** high. Cross-process mutual exclusion did not hold, deterministically,
for every table and record lock in the engine.
**Evidence class:** `runtime_observed` -- every claim below was produced by a live
two-process run on 2026-08-15 against banner stamp `fb7106e0 dirty`, or is a
file:line read of the binary's own source.

## 1. Summary

`xbase::locks` writes the lock owner's pid into the `.lock` sidecar through an
un-imbued stream. A grouping locale is active at runtime, so the pid is written
with thousands separators (`pid=16,984`). The reader parses it back with
`std::stoul`, which stops at the comma and returns `16`. The liveness check then
asks whether pid `16` is alive, gets `false`, concludes the lock is **stale**,
force-removes it, and grants the lock to the second process.

The result is that **any process always sees any other process's lock as stale.**
Locks are observable but not enforced.

This is not a race and not intermittent. It fires on every acquisition.

## 2. What was observed

Two `dottalkpp` processes, same data root, same table
(`dottalkpp/data/dbf/sandbox/INVITEM.dbf`), reached via `do sandbox`.

**Window A** (pid 49640) takes the table lock:

```
. LOCK TABLE
LOCK: table locked.
. LOCK STATUS
Table: LOCKED (owner GRIMWOOD:49,640:1,786,832,702,834)
Record 3: unlocked
```

**Window B** (pid 16984), while A still holds it:

```
. LOCK STATUS
Table: LOCKED (owner GRIMWOOD:49,640:1,786,832,702,834)
Record 1: unlocked
. LOCK TABLE
LOCK: table locked.
```

B read A's lock correctly, then granted itself the same lock. **Detection works.
Enforcement does not.**

The sidecar on disk afterwards, showing B's pid and a single surviving lock file:

```
> Get-Content D:\code\ccode\dottalkpp\data\dbf\sandbox\*.lock
DotTalk++ lock
owner=GRIMWOOD:16,984:1,786,832,989,047
pid=16,984
ms=1,786,832,989,048
```

Only one `.lock` file exists (`INVITEM.dbf.lock`, 87 bytes). A's lock file was
removed and replaced by B's, which is the signature of the stale-recovery branch
having run.

## 3. Mechanism, at source

**Write side.** `src/xbase/xbase_locks.cpp`, two number-emitting sites, both bare:

```cpp
// make_owner_string(), :55-57
std::ostringstream os;
os << host << ":" << pid << ":" << ms;
return os.str();
```

```cpp
// lock file writer, :157-160
f << "DotTalk++ lock\n";
f << "owner=" << owner.id << "\n";
f << "pid="   << pid      << "\n";
f << "ms="    << ms       << "\n";
```

Neither stream is imbued. **`grep -c imbue src/xbase/xbase_locks.cpp` returns 0.**
With a grouping locale installed, `<<` on an integer emits separators, which the
observed output and the on-disk file both confirm.

**Read side.** `read_lock_meta()`, :112-117:

```cpp
} else if (line.rfind("pid=", 0) == 0) {
    try {
        meta.pid = static_cast<unsigned long>(std::stoul(line.substr(4)));
    } catch (...) {
        meta.pid = 0;
    }
}
```

`std::stoul` parses the longest valid prefix and **does not throw** on trailing
junk, so the `catch` never fires. Verified by compiling and running it:

```
stoul("16,984") = 16 (no throw)
```

**Decision side.** `try_lock_*`, :238-247:

```cpp
// Re-entrant lock in same process/session.
if (meta.owner == me.id) {
    return true;
}

// Stale lock: owner process is gone.
if (!is_pid_alive(meta.pid)) {
    std::string ignored;
    if (!force_remove(path, &ignored)) { ... }
```

`is_pid_alive(16)` -> `OpenProcess` fails or the process is not `STILL_ACTIVE`
-> `false` -> `force_remove` -> lock stolen.

Note the re-entrancy guard above it compares `meta.owner` as a whole **string**,
which is why same-process re-locking still behaves. The bug only bites across
processes, which is exactly the case locks exist for.

## 4. Blast radius

`try_lock_table` / `try_lock_record` callers outside the locks TU:

| Site | Meaning |
|---|---|
| `src/bbs/bbs_store.cpp:95` | the BBS daemon's per-append table FLOCK |
| `src/cli/append_support.cpp:326,416,450,500` | every APPEND path |
| `src/cli/cmd_commit.cpp:233` | COMMIT record lock |
| `src/cli/cmd_delete.cpp:216` | DELETE record lock |
| `src/cli/cmd_recall.cpp:234` | RECALL record lock |
| `src/cli/cmd_calcwrite.cpp:712` | CALCWRITE record lock |
| `src/cli/cmd_lock.cpp:161,175,199` | the explicit LOCK verbs (Class B) |

Every write path in the engine, plus the daemon. `dottalkpp` and `dottalk_bbsd`
share the on-disk store with no IPC between them, and cooperative locking is the
only thing standing between them. It is not standing.

## 5. Relationship to existing lanes

**AIF-031** is the same defect class, already named and already swept:
"no thousands grouping in stored values." The sweep imbued
`std::locale::classic()` at roughly twenty sites -- `cmd_calc`, `cmd_replace`,
`cmd_calcwrite`, `row_codec_fixed`, `fn_numeric`, `fn_string`, `shell_api`,
`rhs_eval`, `date_utils`, `cmd_aggs`, `shell_eval_utils`, `cmd_replace_multi`.
`SESSION_CLOSEOUT_FIELDTYPE_CODEC_2026-07-19.md` records the follow-up as open:

> **AIF-031 numeric-formatting sweep** (intake task #100): audit other CLI/engine

`src/xbase/xbase_locks.cpp` is what that unfinished audit missed. The lane was
filed as a numeric-formatting cosmetic issue; in this file the same root cause
silently disables mutual exclusion. **The severity of a defect class is not
uniform across the sites it touches, and an audit scoped by "formatting" will
not find the site where formatting is load-bearing.**

**AIF-113** (`LOCK_RELEASE_AND_RECOVERY_LANE_V1.md`, claimed) covers three dead
recovery functions and a command that never releases -- the **release** half of
the lock subsystem. This finding is the **acquisition** half. Same file, same
subsystem, different failure, and this one is the more severe.

**Resolved 2026-08-15: this took its own number.** `AIF-116`, claimed host-side
by the owner (`coordination/aif/AIF-116.claim`, run `COWORK-20260815-001`, lane
`lock-owner-locale-grouping`). Own number rather than widening AIF-113 because
acquisition and release are different failures with different remedies -- but
they are a hard pair in the other direction, see section 10: AIF-113 is a
**blocking dependency** of AIF-116's fix, not merely a neighbour. AIF-113's
charter should gain a cross-reference saying so, since it was chartered as
housekeeping and is not.

**AIF-112** discovered it and is not the lane that fixes it.

## 6. Remedy, smallest first

0. **Fix the cause at the install point** -- `include/runtime/utf8_init.hpp:80`
   takes the whole native locale when it wants only the encoding. See section
   12c: keep the UTF-8 facets, take `numeric` from `classic()`. One line, fixes
   every site in the process at once. *This item was added after the section 12
   thread was closed; it outranks everything below it.*
1. **Imbue both streams** in `xbase_locks.cpp` with `std::locale::classic()`,
   matching the AIF-031 convention already used elsewhere in the tree. This is
   the one-line-per-site fix and it stops new bad sidecars. Still worth doing
   alongside item 0, as defence against the next global-locale change.
2. **Harden the reader** so it does not silently accept a truncated parse:
   reject a `pid=` line with trailing non-digits rather than trusting the prefix.
   Defence in depth -- existing `.lock` files on disk are already malformed, and
   a corrupted owner must fail closed, not fail stale.
3. **Fail closed on an unparseable owner.** Today an unreadable pid degrades to
   "assume stale, steal the lock." The safe default is the opposite: an owner
   that cannot be verified is an owner that is presumed alive.
4. **Finish the AIF-031 audit** across the engine, not only the CLI.
5. Add a two-process regression that asserts the second acquisition is refused.
   There is currently no test that would have caught this.

Item 3 is the one worth arguing about, and it is a design question rather than a
bug fix: the current code chooses availability over safety when it cannot read
the owner. That choice was probably never made explicitly.

**Sequencing warning -- do not ship item 1 alone.** See section 10. Fixing the
locale bug by itself converts a safety failure into a liveness failure, because
the broken stale-detection is currently the only thing cleaning up leaked locks.
Item 1 must land together with an exposed recovery path (AIF-113).

## 7. What this does to the AIF-112 Phase-1 spike

Steps 1 to 3 completed and are reportable. Step 4 (exclusive proof refused under
FLOCK) **fails** -- not because the ledger design is wrong but because the
substrate underneath it does not enforce. Steps 5 and 6 cannot be scored until
this is fixed: "release and re-acquire" is not meaningful when acquisition never
refuses.

The sharpest consequence is for Step 6, whose mandatory requirement was
**"`EXPAT` lease reclaim without any force path."** Under this defect,
`force_remove` runs on *every* acquisition, silently, inside `try_lock_*`. A spike
run to completion would have reported Step 6 green while a force path executed
underneath it.

That is the same failure shape recorded in
`proof.governance.availability_is_not_adoption` -- a green proof bar over an
untouched hole -- arriving a second time by a different route. There it was the
wrong substrate; here it is the right substrate with an unverified property. Both
cases pass the stated check and prove nothing.

The counter-case is worth stating plainly: had AIF-112 kept its original SQLite
ledger, this defect would still be sitting in the engine, unfound. The DBF
correction is what put the spike on top of `xbase_locks` at all.

## 8. Reproduction

```
# Window A
./datarun.ps1
do sandbox
CREATE X64 INVITEM (ITEM_ID I, ITEM_KEY C(64), KIND C(16), REF C(200), STATE C(12), AUTHOR C(32), CREATED D, SUP L, NOTES M)
SELECT 1
USE INVITEM
LOCK TABLE
LOCK STATUS

# Window B, while A holds
./datarun.ps1
do sandbox
SELECT 1
USE INVITEM
LOCK STATUS      && reads A's lock correctly
LOCK TABLE       && EXPECTED: refused.  ACTUAL: "LOCK: table locked."
```

Then inspect the sidecar:

```
Get-Content D:\code\ccode\dottalkpp\data\dbf\sandbox\INVITEM.dbf.lock
```

A correct run shows `pid=16984`. A defective run shows `pid=16,984`.

## 9. Secondary findings from the same run

Recorded here because they were observed in the same session and would otherwise
be lost. None is load-bearing for the above.

| Id | Finding |
|---|---|
| A3 | The `WORKSPACE CATALOG` footer instructs `USE + APPEND BLANK`. The runtime registers `APPEND` and `APPEND_BLANK` as separate verbs, so the spaced form is refused and the caller's subsequent REPLACEs clobber the current record. This is a third surface for `proof.engine.append_blank_catalog_drift` (AIF-086, R-APPEND-BLANK), which recorded only `shell_commands.cpp` and `command-catalog.mdx`. |
| A4 | No `inv.*` permissions exist, and the 19 permissions are compiled into `identity_bootstrap.cpp` with literal ids, not seeded. Adding inventory permissions is a code change, not a data operation -- a Phase-2 cost the schema sketch did not price. |
| A5 | Phase 1 needs no new permission: `database.mutate` (id 5, Medium, no approval) already covers ledger writes. Only `inv.break` warrants its own, and the house shape for it already exists -- `role.assign` (12) and `authorization.grant` (13), both Critical plus approval. |
| C1 | `DBAREA` reports the X64 extended types `I` and `T` as `Other` while naming `Character`, `Logical`, `Memo`, and `Date` correctly. The reporter's type table was never taught the X64 additions. `STRUCT` is correct. |
| D1 | `CREATE` silently overwrote two existing tables with no prompt, while `ERASE` refused to delete without `CONFIRM`. The safety is inverted: the destructive path is the unguarded one. `cmd_create.cpp:56` documents this as unknown ("possible_overwrite: depends on dbf_create backend behavior for existing paths"); it is now measured. Harmless at 0 records, silent data loss on a populated table. |
| E1 | The lock owner string renders with thousands separators. Filed above as the root cause, not a cosmetic issue. |
| F1 | **A `REPLACE` whose right-hand side fails to evaluate stores BLANK and reports SUCCESS.** `REPLACE ACQUIRED WITH DATEADD(TODAY, -2)` printed nothing and left the `D` field empty; `REPLACE ACQUIRED WITH DATEADD(DATE(), -2)` stored `20260813`. The difference is that bare `TODAY` resolves as a whole right-hand side but not as a function ARGUMENT, where it parses as an identifier -- the catalog's own example is `DATEADD(DATE(), 7)`, with parens. `DATEADD` is properly registered (`fn_date.cpp:440`, arity 2), so this is not an AIF-114 phantom. The defect is the silence: `validate_field_value_for_store` has a `case 'D'` returning `"invalid date for field"`, an error path that exists and did not fire. Same family as A3's silent clobber and E2 below -- **this engine's failures are quietest exactly where quiet costs most.** A field silently left blank by a typo in a date expression is a data-integrity hazard in any ledger built on this surface, AIF-112's included. |
| E2 | `UNLOCK` on a record that is not locked reports success: `LOCK STATUS` showed `Record 3: unlocked`, and a subsequent bare `UNLOCK` answered `UNLOCK: record 3 unlocked.` A release verb that cannot distinguish "released it" from "there was nothing to release" gives the operator no way to detect that a lock they believed they held was already gone -- which is the exact condition this defect produces. Minor on its own, misleading in combination. |

Retracted during the run: an apparent `STRUCT` column misalignment did not
reproduce and was paste noise, not a defect. Recorded so it is not re-reported.

## 10. Locks are never released except by an explicit UNLOCK -- and this bug is hiding it

Asked by the owner during the run: does entering a new work area, or closing,
clear a lock held by another session? **No. Nothing does.**

| Path | Releases? |
|---|---|
| `CLOSE` / `CLOSE ALL` (`cmd_close.cpp`) | no -- the TU never mentions locks |
| `CLEAR` (`cmd_clear.cpp`) | no -- never mentions locks |
| `USE` / `OPEN` (`cmd_use.cpp`) | no -- its only lock references are I5 design comments |
| `DbArea::close()` (`dbarea.cpp:59`) | no -- clears `_fp`, detaches index hooks, closes memo. No lock cleanup. |
| `~DbArea()` (`dbarea.cpp:57`) | no -- calls `close()`, which does not release |
| process exit | no -- nothing removes the sidecar |
| `UNLOCK` (`cmd_unlock.cpp`) | **yes -- the only path** |
| `release_held()` | exists, called by nothing (AIF-113) |

Class A sites are fine: they pair acquire and release within one operation, by
RAII (`bbs_store.cpp:99`, `cmd_workspace.cpp:2117`) or by an explicit unlock on
every exit path (`append_support`, `cmd_commit`, `cmd_delete`, `cmd_recall`,
`cmd_replace`, `cmd_calcwrite`, `dbarea.cpp:275`). The exposure is Class B --
`LOCK TABLE` held across operations, which only `UNLOCK` ends.

So a session that takes `LOCK TABLE` and then closes the table, switches work
area, or exits leaves a live `.lock` sidecar with no owner able to reach it.

**The two defects currently mask each other, and that is the dangerous part.**
Leaked locks are being silently cleaned up by the broken stale-detection: every
orphan looks stale because every lock looks stale. Repair the locale bug on its
own and orphans stop being reclaimable at all -- and there is no exposed FORCE
verb to clear them by hand, because `force_unlock_table` and
`force_unlock_record` are dead code (AIF-113). A single abandoned `LOCK TABLE`
would then wedge that table permanently for every process on the machine.

**Therefore: the enforcement fix and the recovery path must land together.**
Fixing safety first creates a liveness failure with no manual escape. This also
raises AIF-113 from housekeeping to a blocking dependency, which was not its
status when it was chartered.

## 11. There is no regression test for locking

`grep -rln "try_lock_table\|try_lock_record\|LOCK TABLE\|xbase::locks" tests/`
returns nothing. No test file references the lock subsystem in any form.

That is the reason a deterministic, every-single-time defect survived in every
committed version of the file since 2026-07-14. It is not a subtle bug and it
does not need a clever test -- the two-process reproduction in section 8 is the
whole test, and any assertion that the second acquire is refused would have
caught it on day one.

Minimum coverage to add with the fix:

1. Second process is **refused** while the first holds a table lock.
2. Second process is refused while the first holds a **record** lock.
3. A lock whose owner process is genuinely gone **is** reclaimed as stale.
4. An owner string that cannot be parsed **fails closed** (presumed alive).
5. Round-trip: the pid written to the sidecar reads back byte-identical, under a
   grouping locale. This is the direct regression guard for this defect.

Test 5 is the one that generalises: it would also catch the next site the
AIF-031 audit misses.

## 12. On the owner's recollection that this once worked

The owner's read during the run was that locking behaved correctly when first
written and broke when timestamps were added. Git cannot confirm or refute that:
`src/xbase/xbase_locks.cpp` enters recorded history at `fecc3951e` (2026-07-14,
a bulk "Checkpoint runtime source" import) already containing `make_owner_string`
with `ms`, the `pid=` line, `is_pid_alive`, the `stoul` parse, and zero `imbue`
calls. Across its entire recorded life the only substantive change is a
`uint32_t` -> `uint64_t` recno widening. Any pre-timestamp version predates
version control.

But the recollection is probably right in substance, by a different route.
**This code does not have to change in order to break.** It emits grouping only
when a grouping locale is installed, and a repo-wide search finds no
`std::locale::global` or `setlocale` call in `src/` or `include/` at all -- only
the roughly twenty `imbue(std::locale::classic())` defences added by AIF-031.
A sweep of twenty sites is what a team does *after* something starts installing
a locale; the defences are evidence of the event.

So the likely history is: the lock code was written correct-by-default under the
classic locale, something later introduced a grouping locale at runtime, AIF-031
was the cleanup, and `xbase_locks.cpp` was missed. That matches "it used to work
and I did not change it."

### 12a. Thread closed -- the installation point, found

`include/runtime/utf8_init.hpp:80`, reached from `src/cli/main.cpp:233` as one of
the first things `main()` does:

```cpp
// 4) Locale only. Do not force stdout/stderr mode here.
// Leave output mode decisions to the console layer.
try {
    std::locale::global(std::locale(""));
} catch (...) {
    // best effort only
}
```

**The intent was character encoding. `std::locale("")` is the whole native
locale, and it brings `numpunct` with it.** The function is named `init_utf8`
and the comment says "Locale only", meaning *only the locale, not the stream
modes* -- the author was reasoning about `codecvt`. Nothing in the name, the
comment, or the call site suggests it also changes how every integer in the
process serialises. On a US Windows host the native locale groups thousands, and
from that line onward every un-imbued stream in the program does too.

It landed **2025-08-31**, in `d506195ce` "Alpha 5.0 shake-down baseline" -- the
earliest commit in that file's history, and ten and a half months before
`xbase_locks.cpp` enters recorded history.

**This vindicates the owner's recollection precisely.** The lock code did not
change. The ground under it did, in 2025, for an unrelated reason, in a header
about console encoding. If the lock code predates Alpha 5.0 -- and its style
suggests it does -- then it was written correct and was correct when written.

It also explains AIF-031 completely. A sweep imbuing `classic()` at twenty CLI
sites is not a coding standard, it is **damage control after a global locale was
installed**, applied wherever the damage was noticed. `xbase_locks.cpp` was
simply somewhere nobody looked, because nobody was reading lock sidecars for
pretty numbers.

### 12b. The defect is Windows-only

The `#else` branch of the same function installs `C.UTF-8`, which is the C locale
with UTF-8 encoding -- **classic `numpunct`, no grouping**. Linux and WSL builds
therefore write `pid=16984` and lock correctly. Only the documented fallback path
is exposed: if `C.UTF-8` is unavailable the code tries `en_US.UTF-8`, which does
group.

Three consequences:

1. Any regression test for this **must run on Windows**. A green suite on WSL
   proves nothing about it, which is a plausible reason it was never caught.
2. The two platforms have been running different locking semantics -- one
   enforcing, one not -- with no note anywhere saying so.
3. `dottalk_bbsd` and `dottalkpp` share a store on Windows, which is the
   configuration in daily use here and the one that is broken.

### 12c. Remedy, revised -- fix the cause, not the twenty symptoms

Imbuing the two lock sites (section 6 item 1) still stops the bleeding and is
worth doing. But the cause is one line, and fixing it there fixes every site at
once, including the twenty AIF-031 already patched and every future one:

```cpp
// UTF-8 encoding from the native locale; numeric formatting from "C".
std::locale native("");
std::locale::global(std::locale(native, std::locale::classic(),
                                std::locale::numeric));
```

The three-argument `std::locale` constructor takes `native` as the base and
replaces the `numeric` category facets from `classic()`. The program keeps the
UTF-8 behaviour `init_utf8` exists to provide and loses the digit grouping it
never wanted.

**Argue about this before doing it, on three points.** (a) It changes global
numeric formatting, so anywhere grouping is genuinely wanted for *display* must
imbue deliberately -- a search of this tree suggests that is nowhere, since
AIF-031 has been removing grouping wherever it appears. (b) It changes parsing as
well as formatting, which is the direction that matters more for correctness and
should be tested, not assumed. (c) The existing `imbue(classic())` calls should
stay: they become redundant rather than wrong, and defence in depth is cheap
against a global that any future line could change again.

**And the durable version is still a gate.** A one-line fix at the install point
is correct today and reversible by anybody who adds another
`std::locale::global` for another good local reason. Per
`PREPUSH_GATE_REFERENCE_V1.md` -- "obligations carrying a gate held 83-94 percent
compliance; the one without a gate held 33" -- the rule worth enforcing is that
**no value serialised to disk may depend on the ambient locale**, and the cheap
approximation of it is a gate that fails any new `std::locale::global` call that
is not accompanied by a `numeric`-category override.

## 13. Fixed and re-proven, same session, build `fe42666e`

The owner elected to fix before reporting to the steward. Four source changes,
authored by the scribe, built and run host-side by the owner.

### 13a. The changes

| File | Change |
|---|---|
| `include/runtime/utf8_init.hpp` | **the cause.** Encoding facets from the native locale, `numeric` category from `std::locale::classic()`, via the three-argument `std::locale` constructor. The POSIX `en_US.UTF-8` fallback gets the same override; `C.UTF-8` needed none. |
| `src/xbase/xbase_locks.cpp` (owner-string builder) | `os.imbue(std::locale::classic())` -- defence in depth. |
| `src/xbase/xbase_locks.cpp` (sidecar writer) | `f.imbue(std::locale::classic())` -- the sidecar is a machine-read protocol file, not output. |
| `src/xbase/xbase_locks.cpp` (`read_lock_meta`) | new `LockMeta::pid_valid`. The field must parse **whole** -- `std::stoul` with a `pos` out-param, compared against the field length. A prefix parse is now a failure, not a value. |
| `src/xbase/xbase_locks.cpp` (three stale checks) | **fail closed.** `:285` requires `pid_valid && !is_pid_alive`. `:360` denies when the foreign owner is alive **or unknown**. `:366` reclaims only when provably dead. |
| `src/xbase/xbase_locks.cpp` (includes) | `<locale>` made explicit rather than arriving transitively through `<sstream>`. |

Two of those sites were nearly missed. The record-lock path checks the *table*
lock at `:356`/`:362`, and both tests read `is_pid_alive(tmeta.pid)` unguarded --
with an unparseable pid the deny branch evaluated false and fell straight through
to the reclaim, so a malformed table lock would have granted a record lock
underneath it. Found by auditing every call site rather than the ones already
touched.

Strict-parse behaviour confirmed by compiling and running it before the build:
`16984` valid; `16,984`, `12abc` and empty all rejected.

### 13b. The proof

Build `fe42666e dirty`, `Aug 15 2026 16:05:32`. Two processes, both on the new
binary, same table, same data root.

**The sidecar is clean:**

```
DotTalk++ lock
owner=GRIMWOOD:48408:1786835282963
pid=48408
ms=1786835282964
```

**77 bytes. It was 87.** The ten-byte difference is exactly the ten grouping
separators the old build wrote -- five in the owner line, one in `pid`, four in
`ms`. The corruption was measurable in the file size.

**Mutual exclusion holds.** Process 48408 (started 16:07:59) held the table
lock. Process 71628 (started 16:08:52) ran `LOCK TABLE` and was **refused**:

```
. LOCK TABLE
LOCK: failed (lock exists).
. LOCK STATUS
Table: LOCKED (owner GRIMWOOD:48408:1786835282963)
Record 1: unlocked
```

Both pids verified alive at the time of refusal via `Get-Process`. The refusing
process is provably not the owner -- the owner string is a process singleton, so
a same-process attempt would have returned re-entrant success rather than an
error.

**The FLOCK primitive therefore enforces.** Precise about what that is and is
not: this proves the substrate property Step 4 depends on. It is **not** Step 4,
which requires a ledger-level refusal with scan and append in one lock scope.
The scribe conflated the two in an interim report to the owner and claimed a
pass that had not happened; corrected on re-reading the template. Step 4 proper
was run afterwards as `dbf/sandbox/aif112_step4.dts` and passes -- see
`AIF112_PHASE1_EVIDENCE_AND_STEWARD_HANDOFF_4_V1.md`.

**Cross-process release and re-acquire also verified.** 48408 ran
`UNLOCK TABLE`; 71628 then read `Table: unlocked`, acquired, and became owner
`GRIMWOOD:71628:1786835345327`. Again a substrate property, not the ledger-level
Step 5, which was run separately.

**Step 6 passes -- and this is the one that could not have been honestly scored
before today.** (Recorded here because the reclaim exercised the fixed lock path;
the full Phase-1 scoring, including the backdating substitution this step used,
belongs to the evidence return, not to this defect report.) Its mandatory requirement was `EXPAT` lease reclaim *without any
force path*, and until this morning `force_remove` executed inside every
acquisition, so any green here would have been a green over a running force
path. Final ledger state:

```
CHK_ID ITEM_ID HOLDER          STATE    ACQUIRED EXPIRES  RELEASED SUP
     1       1 member#4/kind0  expired  20260813 20260814 20260815  T
     2       1 member#4/kind1  held     20260815 20260822            F
```

The expired lease is superseded with a release date and its history retained;
the live lease belongs to a **different holder**; the whole transition ran inside
one ordinary `LOCK TABLE` / `UNLOCK TABLE` pair which reported `Table: unlocked`
on exit. No `force_unlock`, no hand-removed sidecar. This is the `WORKSPACES`
supersede idiom from finding A2 carried onto leases, which is the reuse the
Step 1 audit predicted.

### 13b-ii. The recovery half, which is the half that could have been broken

Fail-closed cuts both ways, and a parser that is too strict converts an
enforcement fix into a permanent lock. Tested directly.

A session took a table lock and **quit while holding it**. Both sidecars survived
process death (`INVCHKOUT.dbf.lock`, `INVITEM.dbf.lock`), and `Get-Process
dottalkpp` returned nothing -- confirming from observation what section 10
established from source: nothing releases on exit.

A fresh session then reclaimed both:

```
. LOCK STATUS
Table: LOCKED (owner GRIMWOOD:38444:1786836161477)
. LOCK TABLE
LOCK: table locked.
```

Same for `INVITEM`, whose sidecar named a different dead process
(`GRIMWOOD:53828:...`). Both reclaimed, both then released with
`UNLOCK TABLE` reporting `table unlocked`.

**So both directions now hold: a live foreign owner is respected, a provably
dead one is reclaimed.** That is the behaviour the stale reaper was always
written for and never delivered.

**Method note, recorded because the instinct is the transferable part.** The
reclaiming process reported owner pid `3844`, replacing a dead owner with pid
`38444` -- the same digits less the last one. On a day spent chasing a number
that lost its shape in transit, that resemblance was not something to wave past.
`Get-Process` returned `3844`, started 16:31:24. Genuine coincidence; both are
valid Windows pids (multiples of four). No second defect. **The point is that
"expected" and "measured" were one command apart, and the whole lane exists
because someone once settled for expected.**

### 13c. What this does not yet cover

- ~~**No regression test exists yet.**~~ **CLOSED 2026-08-15.**
  `tools/regression/lock_mutual_exclusion_regression.ps1`, 12 assertions across
  5 tests, all green at `fe42666e`. Covers section 11's list: pid round-trips
  with no grouping (the direct guard), a dead owner IS still reclaimed, a live
  foreign owner is refused and its sidecar left intact, a malformed pid fails
  CLOSED, and a record lock is refused under a live foreign table lock. Skips
  on non-Windows by design -- the defect cannot reproduce under `C.UTF-8`
  (12b), so a green run there would be meaningless and a red one worse.
  **Method note worth keeping.** It is PowerShell, not a `.dts`, because the
  property is cross-process and a script inside one engine instance cannot
  express it. Tests 3 to 5 FABRICATE a `.lock` sidecar with a chosen pid rather
  than orchestrating a second live engine, which makes "alive" and "dead"
  deterministic instead of timing-dependent; the cost is that the harness
  hardcodes the sidecar FORMAT, so a deliberate format change will fail it.
  That coupling is intentional -- the format is a cross-process protocol -- and
  is recorded in the script header rather than left to be discovered.
  **And it caught itself first.** T5 failed on the first run, reporting that a
  record lock had been granted under a foreign table lock. It had not: the
  fixture table was empty, `GO TOP` had nothing to land on, and `LOCK` returned
  "no current record" -- which matched neither success nor the expected refusal
  string. A test whose fixture fails silently and then reports a defect is the
  same disease as AIF-117. Fixed by making setup verify persistence in a third
  process and by asserting the cursor is on a real record before judging the
  lock. Recorded because the first version would have sent someone hunting a
  defect that was not there.
- **The gate is not built.** Section 12c's durable remedy -- fail any new
  `std::locale::global` that does not override the `numeric` category -- is
  still a proposal. Without it the one-line fix is reversible by the next person
  with a good local reason, exactly as it was the first time.
- **AIF-113 is unaffected and still owed.** The three recovery functions remain
  dead and no FORCE verb is exposed. This session demonstrated why within the
  hour: pre-existing sidecars carrying `pid=16,984` are, under the new
  fail-closed reader, correctly unparseable and therefore presumed alive -- and
  clearable by no command. They had to be deleted from PowerShell. **That is
  AIF-113's missing escape hatch, encountered in practice, on the same day it
  was re-ranked to a blocking dependency.**
- **Scope of the locale change is untested beyond locking.** It alters global
  numeric formatting *and parsing* for the whole process. Nothing else was
  exercised. The full regression suite should run before this is called safe.

---

**Recorded by** `member.ai.claude.cowork` from a live run driven by the owner.
**Owner** `member.derald`. The run was operated host-side; the scribe has no
runtime access and verified every source claim against the tree at
`fb7106e0`.
