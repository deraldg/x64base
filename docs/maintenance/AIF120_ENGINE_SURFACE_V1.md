---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-069
  recorded_at_utc: 2026-08-20T06:00:00Z
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
    requested_by: maintainer (member.derald), in-session -- "are you building a way
      to read x64 dbfs or using the api already built", "we dogfood", and "you don't
      say open(), it 'use'".
  report:
    path: docs/maintenance/AIF120_ENGINE_SURFACE_V1.md
    kind: ruling
---

# AIF-120 -- R61: `open()` is not `USE`, and the engine's linkable surface has primitives but no lifecycle

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

The maintainer asked whether this lane is building its own way to read x64 DBFs or
using the API already built. The answer is both, and the honest accounting is below.

## 1. What the lane builds itself, and whether it should

| tool | what it does | verdict |
|---|---|---|
| `tools/vfp/read_vfp_binary.py` | reads VFP **designer** containers -- `.SCX`, `.VCX`, `.FRX`, `.MNX` | **defensible.** These are design-time artifacts the engine does not read, and the importer must run with no engine present. |
| `tools/uidef/uidef.py` | **writes** UIDEF design tables as DBFs, by hand | **unexamined until now.** x64base is the DBF authority and this lane writes DBFs itself. |
| the 2^31 fixture in section 5 | patched a DBF header with `struct.pack` | **wrong.** `dbf_create` exists. |

### The one that had never been checked

Nothing had ever confirmed that a table `uidef.py` writes can be opened by the
engine. Measured, by linking `libxbase.a` and opening three of them:

```
-- /tmp/E2E.DBF
  opened: recCount64=3 fields=16 versionByte=0x30
     field 1 RECKIND    = 'DOC'
     field 2 OBJID      = 'DOC'
-- /tmp/DOMAIN.DBF   opened: recCount64=4  fields=16 versionByte=0x30
-- /tmp/EMPH.DBF     opened: recCount64=10 fields=16 versionByte=0x30
```

**They are engine-readable.** Correct version byte, correct field count, correct
names, correct record counts. The lane's design tables are real x64base tables and
not a private format that merely resembles one. That is worth having established
rather than assumed, and it is the first time it has been.

## 2. Correction 40 -- `open()` is not `USE`, and R58's claim is corrected

The maintainer: *"there are many responsibilities that must happen when you open a
table in the database. for instance you don't say open(), it 'use'."*

`src/cli/cmd_use.cpp` lists them: duplicate-open guard across work areas, memo
auto-attach, index auto-attach, resolution through the configured DBF path slot,
`NOINDEX` physical-order mode, and `AGAIN` for a second area on an open table.

Every registry this lane wrote -- R58, R59, R60 -- calls `DbArea::open(path)`. So
those areas have **no memo attached and no index attached**, and R58's claim that
R53.4 is "implemented, not merely ruled" is **too strong**. R53.4 says a frontend
opens each alias *into its own work area*; `DbArea::open()` opens a file into an
object. The distinction is exactly the one the maintainer drew.

What R58 actually implemented is the **refusal** half -- a resolver cannot answer for
an area that was never opened -- and that part stands. The opening half is a file
open wearing the name of a work area.

## 3. R61.1 -- measured: the lifecycle is not in any library

```
                                 cmd_USE  memo-attach  index-attach
  libxbase.a                        0          0            0
  libmemo.a                         0          0            0
  libxexpr.a                        0          0            0
  libdottalk_value.a                0          0            0
  libdottalk_inx_payload.a          0          0            0

  what libxbase DOES export for opening:
      T xbase::DbArea::open(std::string const&)
      T xbase::DbArea::close()
```

`cmd_COMMIT`, `cmd_ROLLBACK` and `cmd_TABLE_BUFFER` are likewise in **no archive**,
though `include/cli/table_buffer.hpp` declares all three.

**So the engine's linkable surface exposes the primitives and not the lifecycle.**

| where it lives | what is there | how a frontend reaches it |
|---|---|---|
| the **libraries** (`libxbase.a` and friends) | primitives: `xbase::locks`, `DbArea::open/close`, navigation, `replaceFieldStored` | link and call |
| the **dottalkpp target** (`src/cli/`) | the complex commands: `USE`, `TABLE ON`, `COMMIT`, `ROLLBACK`, the browses | `shell_execute_line(area, "USE ...")` after `register_shell_commands(eng, ...)` |

**And the second door is a real API, not console parsing.** `src/cli/shell_api.hpp`:

```cpp
// Canonical shell execution entry: preprocesses one raw line and dispatches it.
// This is the shared path for prompt, DOTSCRIPT, TEST, and helper replays.
bool shell_execute_line(xbase::DbArea& area, const std::string& rawLine);
```

A command line in, a `bool` out. No subprocess, no output scraping, and the same
path the prompt and DOTSCRIPT use -- so a frontend driving it is on the tested road,
not a side track. `src/cli/shell_commands.cpp` shows the registry:

```cpp
extern "C" void register_shell_commands(xbase::XBaseEngine& eng, bool include_ui_cmds);
```

An engine object, a command set, and a flag to leave the UI commands out -- which is
exactly what a generated frontend wants, since it supplies its own UI.

**This is the architecture, not an unfinished extraction.** The maintainer, on being
shown the measurement: *"the complex commands are at the dottalkpp level -- the
cli."* Primitives live in libraries; complex orchestration lives at the CLI. `USE` is
not a file open with extras bolted on, it is a command that reconciles work areas,
memo sidecars, index families and path policy -- and that reconciliation belongs
where the session state lives.

I had drafted this section as "where the extraction has reached", which reads the
layering as a job half done. It is not. That correction matters because it inverts
what a frontend should conclude, and it has three consequences.

**First, R55.3's "typed vs text" was the wrong frame twice over.** It is not typed
versus text; it is **two typed interfaces at two layers**. A frontend links the
primitives and *embeds* the command layer, and neither involves parsing output. The
wx backend should do both.

**Second, embedding the command layer is compliance, not a shortcut.**
`docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md` lists *"parsing console text as the only
contract for new native GUI features"* as an anti-pattern, carved out for *"where the
core already exposes stable state"*. Read against the layering above, the two agree:
for locks the core exposes stable typed state and a frontend should link it; for
complex commands the CLI **is** the interface, and a frontend that speaks it is using
the intended door rather than working around a missing one.

**Third, this settles R55.3 rather than reopening it.** The wx backend should link
`xbase::locks` **and** speak the CLI, permanently -- not as a migration step. A
frontend needs both because the engine has two interfaces on purpose, and a lane that
tried to reach everything typed would be arguing with the architecture rather than
using it.

## 4. R61.2 -- what a UIDEF handler should do about mutation, and what it cannot

x64base already has the transaction model this lane has been approximating with
locks. `TABLE ON` buffers with **no locks taken**; `COMMIT` fsyncs a redo log and a
`C` marker **before** applying, then applies; `ROLLBACK` discards; a crash replays.
R21.1's "the lock spans the whole handler" is this lane's answer to a question the
house answers with a write-ahead log -- and the WAL answer is strictly better,
because a held lock gives no crash atomicity at all.

Two things block adopting it today, and only one is mine:

- **It is not linkable** (section 3). A typed frontend cannot call `COMMIT`.
- **`COMMIT` locks one record at a time**: `cmd_commit.cpp`'s apply loop is
  `if !try_lock_record(A, recno): mark fail; continue`. So a commit is atomic against
  a **crash** and not against a concurrent **reader**, and a record another process
  holds is **skipped** -- a partial apply. The maintainer's own uncertainty --
  *"table locking i think, but should be record locking only, i am not sure"* -- is a
  live question, and R54 already rules out the obvious fix: a table lock during the
  apply would not exclude record holders, because the namespaces are independent.
  The fix that would work is all-or-nothing acquisition of every record the commit
  needs before applying any -- **which is R48.4 and R50.1, the rule this lane already
  implements for domains.**

That last convergence is offered to the engine lane for what it is worth: the
frontend's all-or-nothing rule and the commit loop's problem are the same shape.

## 5. Correction 41 -- I hand-patched a DBF header instead of using `dbf_create`

Testing the lock path past 2^31, I built a fixture by writing `0x80000001` into
header bytes 4-7 with `struct.pack` and sparse-writing a record at offset 234 GB.
The engine read `recCount64 = 0` and I briefly had a finding.

The fixture was invalid. `include/xbase.hpp`:

```cpp
int32_t num_of_recs;                                        // the on-disk field
_rec_count64 = (hdr.num_of_recs < 0) ? 0u : ...             // negative reads as ZERO
setRecordCount64: _hdr.num_of_recs = (n > INT32_MAX) ? INT32_MAX : n;   // saturates
```

**The classic DBF header cannot express more than `INT32_MAX` records**, and
x64base saturates it deliberately while carrying the authoritative count in
`_rec_count64`. `src/tests/test_recno64_sparse_e2e.cpp` builds such a table properly,
through `dbf_create`. I reached past the API the maintainer had just asked me about,
in the middle of answering the question, and got an invalid file for it.

R57's choice of `recno64()` over `recno()` is still **unproven at the boundary**. It
is well-founded -- `recno()` is documented to return `-1` past 2^31 rather than
clamp, and `xbase::locks` names the lock file after the record number, so a wrong
accessor would write `.lock.-1` -- but the run has not happened, and it needs the
engine's own fixture builder.

## 6. Still open

- **R53.4 needs `USE`, and `USE` is a CLI command.** Section 2. Given the layering,
  the answer is most likely that a conforming frontend opens its areas **through the
  CLI** and links only the primitives -- which makes R53.4 implementable today and
  makes R58's registries wrong rather than blocked. That is the shape of the fix and
  it has not been built or run.
- **The 2^31 lock test** (section 5), needing `dbf_create`.
- **Pinocchio is a million rows and 5.5 million rows**, dense, untracked, built by
  `pinocchio_build.dts`. Nothing in this lane has been run at that scale.
- **R55.2 and the mutation-model question** remain the owner's.

## 7. Good Neighbor note

- **What changed.** Nothing. This ruling is a measurement and three corrections.
- **Whose area.** AIF-120's own accounting. The engine was linked against and read;
  `nm` was run over its archives. Nothing outside the lane was modified.
- **What authorization.** Maintainer (member.derald), in-session, and the three
  questions quoted in the front matter.
- **How to verify or undo.** Verify: `nm -C --defined-only libxbase.a | grep -E
  "DbArea::(open|close)"` shows the two exports, and `grep -c cmd_USE` over every
  archive shows zero. Nothing to undo.

## 8. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_ENGINE_SURFACE_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R61 -- open() is not USE; the engine's linkable surface has primitives but no lifecycle, and uidef.py's tables are engine-readable"
```
