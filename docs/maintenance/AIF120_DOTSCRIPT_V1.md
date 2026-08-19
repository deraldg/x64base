---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-072
  recorded_at_utc: 2026-08-20T09:05:00Z
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
    baseline_commit: 64dedf551
  authorization:
    requested_by: maintainer (member.derald), in-session "educate yourself, here is a
      mini-course in dotscript", with the full ./datarun.ps1 REGRESSION ALL transcript.
  report:
    path: docs/maintenance/AIF120_DOTSCRIPT_V1.md
    kind: ruling
---

# AIF-120 -- R64: the house already had a proof language, and its lock CLI reports a success it never measured

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

The maintainer sent the complete output of `./datarun.ps1` running `REGRESSION ALL`
against `dottalk++ v0.6 (2026-08-17, eaecae1d dirty)` -- 6,491 lines -- with the
instruction *"educate yourself"*. This is what it changed.

## 1. The headline: prior-art miss number five, and the largest one

Rulings R37 (`GUI_THREADING_RAII_CONTRACT_V1.md`), R42 (staging), R55 (the shipped
GUI core) and R61 (`shell_execute_line`) were each a library or a document I had
overlooked. This one is not a library. **The house ships an entire evidence
apparatus and I built a parallel one for seventeen rulings.**

| the house has | I built |
|---|---|
| `.dts`, a script language with `VAR`/`$name`/`$a[n]`, `IF/ELSE/ENDIF`, `?`, `FORMULA` | `lock_semantics_test.py`, `lock_provider_test.py`, `nested_scope_test.py`, `page_scope_test.py` |
| `REGRESSION <NAME>` -- a named catalog with per-entry `Summary` / `Script` / `Resolved` / `Default` | a list of harness filenames in a lane document |
| `STOP_ON_ERROR`, `SET ECHO`, `SETPATH`, and the doctrine *"every test sets its own environment"* | ad-hoc environment assumptions that produced five flaky-harness incidents in R60 alone |
| a self-asserting form: `? "TAG:" + ($n = 42)` printing `TAG:.T.` | prose that a human has to read |
| bracketed markers: `DOTSCRIPT-EXPR-REGRESSION-BEGIN` ... `-END` | `tail -10`, which produced correction 30 |
| `canaries/` -- boundary proofs that build their fixture with the engine's own `CREATE X64` | correction 44: a fixture built by patching header bytes |

The gate the lane has been enforcing on itself -- *always look for prior art* -- was
being enforced on libraries and documents, and not on **method**. The lane's own
proofs are the thing that most obviously should have been written the house's way.

## 2. What I did about it: the lane's lock contract, restated in `.dts`, and run

New file: `dottalkpp/data/scripts/aif120/aif120_lock_contract_regression.dts`.
It follows the `lexing/comment_handling_regression.dts` form -- a transcript canary
with the expected output documented in the header, because lock state is not
reachable from the expression path and so the `TAG:.T.` form is not available.
Precedent for the directory: `dottalkpp/data/scripts/bbs/bbs_lane_regression.dts`.

It replaces nothing yet. It restates, in the house's language, six claims that R47
through R63 proved in three other languages.

### How it ran

Verbatim, `DOTSCRIPT aif120/aif120_lock_contract_regression.dts`:

```
AIF120-LOCK-CONTRACT-BEGIN
; --- A. the record verb and the table verb are not symmetric ---
; A1 LOCK
LOCK: record 5 locked.
Table: unlocked
Record 5: LOCKED (owner vm:9359:1787177499128)
; A2 UNLOCK
UNLOCK: record 5 unlocked.
Table: unlocked
Record 5: unlocked
; A3 LOCK TABLE
LOCK: table locked.
Table: LOCKED (owner vm:9359:1787177499128)
Record 5: unlocked
; A4 UNLOCK -- claims the record, leaves the table
UNLOCK: record 5 unlocked.
Table: LOCKED (owner vm:9359:1787177499128)
Record 5: unlocked
; A5 UNLOCK TABLE
UNLOCK: table unlocked.
Table: unlocked
Record 5: unlocked

; --- B. the owner token ---
; B1 LOCK WHO 5
LOCK WHO: record 5 owned by vm:9359:1787177499128

; --- C. an unlock that measures nothing ---
; C1 UNLOCK 77 with no lock held
UNLOCK: record 77 unlocked.
; C2 LOCK WHO 77
LOCK WHO: no lock recorded for 77.

; --- D. re-entrancy carries no depth ---
; D1 LOCK 9 twice
LOCK: record 9 locked.
LOCK: record 9 locked.
; D2 UNLOCK 9 once
UNLOCK: record 9 unlocked.
LOCK WHO: no lock recorded for 9.

; --- E. LOCK STATUS follows the cursor, not the lock ---
LOCK: record 9 locked.
; E1 LOCK STATUS at record 7 while record 9 is locked
Table: unlocked
Record 7: unlocked
LOCK WHO: record 9 owned by vm:9359:1787177499128

; --- F. two areas, two table locks (R26 lock domain) ---
Opened ENROLL (v64) : Record count 686
LOCK: table locked.
Table: LOCKED (owner vm:9359:1787177499128)
Selected area 1.
LOCK: table locked.
Table: LOCKED (owner vm:9359:1787177499128)
; F1 both areas report a table lock above
AIF120-LOCK-CONTRACT-END
```

**A3/A4 are correction 34 and R54 in one screen**, in the house's own shell, with no
harness of mine between the claim and the engine. R47.2, R48 and R49 all shipped
`UNLOCK` as the release verb for a *table* lock; A4 is what that did.

## 3. R64.1 -- `UNLOCK` reports success it did not measure

**Finding, source-evidenced and runtime-confirmed.** C1/C2 above: `UNLOCK 77` prints
`record 77 unlocked.` for a record that was never locked, and `LOCK WHO 77`
immediately says `no lock recorded for 77.`

`include/xbase_locks.hpp` offers both forms:

```
bool unlock_record  (DbArea& a, std::uint64_t recno, const Owner& owner, std::string* err = nullptr);
void unlock_record  (DbArea& a, std::uint64_t recno); // best-effort
bool unlock_table   (DbArea& a, const Owner& owner, std::string* err = nullptr);
void unlock_table   (DbArea& a);                 // best-effort: ignores failures
```

`src/cli/cmd_unlock.cpp` calls the **`void` best-effort overload** at all three call
sites (lines 107, 115, 123) and then prints the success message unconditionally.

The library ships the diagnosable path; the command layer chooses the one that
cannot fail and reports as if it had checked. A student following the CLI -- the
maintainer's own framing, *"do you lock at the cmd_lock cmd_unlock, a simple student
example"* -- cannot distinguish a released lock from a lock that was never held,
from a lock held by another process.

**Not fixed here.** `src/cli/` is not this lane's area. Reported for the CLI owner.

## 4. R64.2 -- `LOCK STATUS` reports the current record, not the locked one

**Finding.** E1 above: after `GOTO 7` and `LOCK 9`, `LOCK STATUS` prints
`Record 7: unlocked`. It is telling the truth about a record nobody asked about.
`LOCK WHO 9` answers correctly, so the information exists.

The consequence for a script is that `LOCK STATUS` cannot be used to confirm a lock
unless the cursor happens to be sitting on it -- which is precisely the case a
record-granularity frontend does not satisfy, because R57's provider locks
`recno64()` and then moves on.

## 5. R64.3 -- `WORKSPACE LOAD` cannot resolve its own posture on POSIX

**Finding.** The shipped posture `x64.dtschemas` resolves its twelve tables as
`.../DBF/x64/BUILDING.DBF`. On disk they are `.../dbf/x64/BUILDING.dbf`. On Windows
this is invisible; on the WSL build every one of the twelve fails and the load
aborts:

```
WORKSPACE LOAD: ABORTED -- the posture declares 12 table(s); 12 cannot be found:
  ? /home/claude/dtpp/data/DBF/x64/BUILDING.DBF
```

The shipped `dottalkpp_non_destructive_smoke.dts` opens its fixture with
`WORKSPACE LOAD x64.dtschemas` at line 166, so **`REGRESSION NONDESTRUCTIVE` cannot
reach sections 07 through 15 on a Linux build as shipped** -- which is where the
lock, filter, relation and index coverage lives.

This is the house's own open beta gate **BETA-1.2, "No reliance on case-insensitive
paths (CMake/file names)"**, with a concrete instance. `USE STUDENTS` resolves
correctly, so the defect is in the posture path, not in table opening. The lane's
regression above uses `USE` per area for exactly this reason.

**Not fixed here.** Reported.

## 6. What the transcript confirms about rulings already shipped

- **Correction 34** (`UNLOCK` is the record verb) was visible in the shipped
  regression output the entire time. Section 14 of the non-destructive smoke prints
  `LOCK: record 1 locked.` / `UNLOCK: record 1 unlocked.` -- the record noun on both
  lines -- and `LOCK USAGE` states `LOCK ALL | LOCK TABLE` against a bare `UNLOCK`
  that the usage block itself documents as *"unlocks the current record"*. Running
  `REGRESSION NONDESTRUCTIVE` before R47 would have cost one command and saved three
  rulings.
- **R54** (table and record locks are independent) is confirmed by A3 in the house's
  own observer, not only by my C++ probe.
- **R54's open item** (the owner token carries no user and no session) is confirmed
  by `LOCK WHO`, which is the house's *published* owner surface: `vm:9359:1787177499128`
  is host, pid and milliseconds, and nothing else. The gap is in the shipped CLI, not
  only in the library.
- **R51/R54** (re-entrancy with no depth count) is visible at the prompt: D1 locks
  record 9 twice with two success messages, and D2 releases it with one `UNLOCK`.
- **R62** (x64base is not FoxPro) is strengthened. The function inventory is the
  house's own and it is grouped its own way -- NUMERIC 21, DATE 22, STRING 17,
  SEARCH 4, LOGICAL 3, CONSTRUCTION 3, CONVERSION 3 -- with `HELP FUNCTION <name>`
  over it. `SMARTLIST FOR <expr>`, `AGGS ... FOR/WHERE`, and
  `SORT TO <out> ON <expr> FOR/WHILE/FIELDS/UNIQUE` are the predicate surface.
- **Correction 44** has a house form. `canaries/x64_matrix_metrics_boundary_canary.dts`
  proves the 32,767 and 65,535 record-width barriers by `CREATE X64` -> append ->
  close -> reopen -> read the count back. That is exactly the shape R63 arrived at
  by the long road, and the house had written it down first.

## 7. What it changes for the lane

### 7a. A character-cell frontend already ships (open item, not a ruling)

`ARCTICTALK` launches a **Turbo Vision TUI shell**; `SB` is the SuperBrowser
(read-only, pager, status footer, bounded child-tuples panel); `ERSATZ` is a third
browse. The lane has a character-cell backend (`uidef_text.py`) written as though
none existed, and it refuses the `grid` KIND -- while the maintainer said plainly,
*"note: we have simple cli browses too"*.

The beta checklist constrains this: **BETA-7.1, "Scope locked: read-only only
(editing explicitly disabled)"**. A UIDEF `grid` that binds and edits would cross a
gate the house has deliberately closed. This is where the refused `grid` KIND has to
be settled, and it is an owner decision, not mine.

### 7b. The lock domain may already be a persisted artifact

`REL SAVE AS <dataset>` / `REL LOAD AS <dataset>` persist the relation graph, and
**BETA-5.1 states "Relations are configuration (no implicit joins/flattening)"** --
which is R26's argument in the house's own words, made before mine. R36 gave
`SOURCE` a `Relation` row so a document could state its own lock domain. If the
engine already persists that graph under a name, `SOURCE` restating the edges is a
second copy that can drift.

**Open question for the owner:** should `SOURCE` cite a `REL` dataset name rather
than re-declare the edges? I have not changed the contract.

### 7c. Evidence for R55.2, which remains the owner's

`COMMIT` help states: *"COMMIT applies buffered TABLE changes with locking at commit
time"*, and `COMMIT ALL` *"applies all buffered open areas"*. The engine's own
mutation model is therefore per-area buffering with commit-time locking -- it does
not have one mutation lane. That is evidence bearing on R55.2 (the GUI contract's
one-mutation-lane rule against R26's domain concurrency). It does not decide it: the
GUI contract governs the *frontend*, and the engine governs itself. **Still the
owner's call, and one of the two documents is still wrong.**

### 7d. The HELP catalog is a design table

527 topics over 28,827 rows, keyed by KIND (`SUMMARY`, `SYNTAX`, `USAGE`, `NOTE`,
`EXAMPLE`, `RELATED`, `SOURCE_FACT`, `STATUS`, `ERROR`, `WARNING`, `HINT`, `ALIAS`,
`ARGUMENT`, `MESSAGE`, `DEPRECATION`) and by SOURCE (`SOURCE_MINER` 7,503,
`SHARED_MSG` 2,637, `DOTREF` 992, `CURATED_DOC` 868, `EDREF` 786, `FOXREF` 665,
`REGISTRY` 462). That is a typed row store with a `RECKIND` discipline and a
provenance column, generating documentation for four surfaces.

The UIDEF design table's `RECKIND` + `PROVENANCE` pair is not novel in this house;
it has a sibling. Worth citing as prior art for the format in the contract, which
currently justifies the shape from VFP alone.

## 8. Dogfood note -- the shell itself runs in the container

`dottalkpp/bin-wsl-lean/dottalkpp` links and runs under the container's Ubuntu 24.04
(the device VM is older: `GLIBC_2.38` and `GLIBCXX_3.4.32` are missing there). So
the lane can now drive the **real shell**, not only the archives R58 through R63
linked against. Every output quoted above came from
`dottalk++ v0.6 (2026-08-19, 8969de78 dirty)` built from the current tree.

This closes the loop the maintainer opened with *"are you building a way to read x64
dbfs or using the api already built"* and *"we dogfood"*: the lane no longer has to
build anything to observe the engine's behaviour. It can ask it.

## 9. Evidence tier

**runtime-proven** for sections 2, 3, 4, 5 and 8 -- run against the shell built from
the current tree, with `src/cli/cmd_unlock.cpp` and `include/xbase_locks.hpp` read
for section 3.
**source-evidenced** for section 6 (read from the maintainer's transcript and the
shipped scripts).
**planned** for every item in section 7 -- these are open questions and prior-art
notes, not decisions.

## 10. Still open

- **The lane's other harnesses have not been converted.** This is one regression, not
  a migration. Whether `lock_semantics_test.py`, the wx registries and the WSL shell
  scripts should be retired in favour of `.dts` is an owner decision with real cost:
  the wx registries test *generated C++*, which `.dts` cannot reach.
- **The regression is not in the catalog.** Adding `AIF120_LOCK` to the `REGRESSION`
  launcher is a change to the launcher's source, which is not this lane's area.
  Running it needs `DOTSCRIPT aif120/aif120_lock_contract_regression.dts`.
- R64.1, R64.2 and R64.3 are reported, not fixed.
- Unchanged: R55.2 (section 7c bears on it, does not settle it); the section 13 query
  limit (R62.2); per-handler metadata on `HANDLERS`; the typed provider at the 2^31
  boundary (R63.6); pinocchio-scale.

## 11. Good Neighbor note

- **What changed.** One new file:
  `dottalkpp/data/scripts/aif120/aif120_lock_contract_regression.dts`. No shipped
  code changed; no engine source touched; the lane's own tools are untouched.
- **Whose area.** The script sits under `dottalkpp/data/scripts/`, which is the
  shell's data directory, following the `bbs/bbs_lane_regression.dts` precedent for a
  lane-owned regression. Findings R64.1 and R64.2 are in `src/cli/` and R64.3 is in
  the shipped posture -- reported to their owners, not edited.
- **What authorization.** Maintainer (member.derald), in-session *"educate yourself,
  here is a mini-course in dotscript"*.
- **How to verify or undo.** Verify: run
  `DOTSCRIPT aif120/aif120_lock_contract_regression.dts` and read it against the
  EXPECTED OUTPUT block in the script header. The script is read-only against
  STUDENTS and ENROLL and releases every lock it takes. Undo: delete the one file.

## 12. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add dottalkpp/data/scripts/aif120/aif120_lock_contract_regression.dts
git add docs/maintenance/AIF120_DOTSCRIPT_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R64 -- the lane's lock contract in the house's own script language; UNLOCK reports a success it never measured"
```
