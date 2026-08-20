---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-074
  recorded_at_utc: 2026-08-20T14:20:00Z
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
    baseline_commit: 8145e0880
  authorization:
    requested_by: maintainer (member.derald), in-session "add those to the vocabulary
      and update the locking methodology", answering R65.7's owner decision.
  report:
    path: docs/maintenance/AIF120_FRAME_KINDS_V1.md
    kind: ruling
---

# AIF-120 -- R66: the vocabulary gains the frame the engine draws, and the lock provider stops believing what it is told

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

R65 measured `ERSATZ GRID` and found the design table could not name a single region
of it, and R64.1 measured that the CLI's `UNLOCK` reports success it never checked.
The owner ruled on both: *"add those to the vocabulary and update the locking
methodology"*. This is both, done.

## 1. Five kinds, and three constraints written in with them

Contract section 4 goes from fourteen kinds to nineteen; new section 4b defines the
five. They are the first kinds in this vocabulary with a **runtime** provenance --
taken from a program that was running, not from an intersection of target platforms
over a corpus.

| `KIND` | region | `BINDING` | `PROPS` |
|---|---|---|---|
| `grid` | `TUPLE GRID` | tuple spec | `RowLimit`, `Order`, `ReadOnly` |
| `tree` | `RELATION TREE` | bare alias (the root) | `Order` |
| `detail` | `CURRENT ROOT RECORD` | tuple spec, usually `alias.*` | `ReadOnly` |
| `summary` | `DESCENDANT SUMMARY` | bare alias (the root) | -- |
| `statusbar` | the frame's state line | **empty** | `Shows` |

**(a) `tree` and `summary` carry no child rows.** Their shape is the `SOURCE`
relation graph the document already states once (R36, R26). Child rows would be a
second copy of the closure that can drift from the first.

**(b) `grid` and `detail` are read-only in v1, and a document may not say
otherwise.** `ReadOnly` = false is **refused, naming BETA-7.1** -- not ignored and
not honoured. This was written into the kind at the moment the kind was added, as
R65.7 asked, so no document can ever have been authored against a permissive reading.
The reason is measured rather than cautious: R57.2 found a handler's record lock does
not survive its own write and R59 found a table lock does, so an editable grid over a
relation closure is a row-at-a-time write path across areas the author never named --
R26's exact hazard, unproven. `ReadOnly` becomes real when that is proven.

**(c) A `statusbar` reports; it does not compute.** `Shows` is closed to `rows`,
`limit`, `order`, `root`, `recno`, `status`; a value the reader cannot supply is
omitted, never invented.

### R6 is answered, not overruled

`grid` was on the contract's deliberately-absent list because a VFP grid generates
its columns from a `ColumnCount` property -- implicit children, which UIDEF does not
model. **R66's `grid` declares its columns in its `BINDING`.** Nothing is implied and
nothing is generated, so R6's objection does not reach it; a VFP grid with a
`ColumnCount` and no `RecordSource` is still refused on import. The absent-kinds list
now says so rather than silently dropping the entry.

## 2. `BINDING` on a frame kind is a tuple spec -- new section 10c

R65.2 measured that `alias.field` is a strict subset of BETA-4.4's `*`, `AREA.*`,
`AREA.FIELD`, `#n`. v1 adopts three and refuses the fourth:

- `alias.field,alias.field,...` and `alias.*` and `*` -- accepted on `grid` and
  `detail` only. On the other seventeen kinds a spec is **refused**: *"a tuple spec
  binds a ROW; a text binds one field"*.
- **`*` resolves against the FIRST alias in `SOURCE`, never "the current work
  area".** Section 10 refuses ambient resolution for `Table` and 10b for a bare
  field; this is the same rule a third time.
- **A spec naming two aliases requires a `Relation` edge between them.** The row it
  describes is a join, so R26's lock domain must already cover both. Refused
  otherwise.
- **`#n` refused**, and the message says why it is refused: *"ordinal spec is
  unreachable through the shell (AIF-037 cuts `#` to end of line); name the field"*.
  R65.3 measured that BETA-4.4 declares a form the lexer deletes. This is not
  "bad binding" and must not be reported as one.

## 3. Four targets render it, and they were run

`gui/uidef/author_frame.py` writes the frame as a UIDEF document -- deliberately
the same screen the engine draws, so the two can be read against each other.

**Character cells** (`uidef_text.py`), which is the target the kinds were measured
on:

```
+- Relational Browser ------------------------------------------+
|CURRENT ROOT RECORD                                            |
|(every field of STUDENTS, from the schema at render time)      |
|RELATION TREE                                                  |
|STUDENTS                                                       |
|  -> ENROLL   ON SID                                           |
|DESCENDANT SUMMARY                                             |
|ENROLL     : n                                                 |
|TUPLE GRID                                                     |
|LNAME       FNAME       CLS_ID      GRADE                      |
|----------------------------------------------                 |
|..........  ..........  ..........  ..........                 |
|ROWS SHOWN: n | LIMIT m | ORDER: physical | ROOT: STUDENTS | ...|
+---------------------------------------------------------------+
```

- **Tk**: `ttk.Treeview` is both the grid (`show='headings'`, columns from the spec)
  and the tree (`show='tree'`, edges from `SOURCE`). Six widgets built and **all
  mapped**, grid columns `('LNAME', 'FNAME', 'CLS_ID', 'GRADE')`, under Xvfb.
- **HTML**: `<table class="grid">` with a `<th>` per declared column, `<ul
  class="tree">`, `<dl class="detail">`, `<div class="statusbar">`.
- **wx C++**: `wxListCtrl` in `wxLC_REPORT` with `InsertColumn` per spec,
  `wxTreeCtrl` with `AddRoot`/`AppendItem`, `wxStaticBoxSizer` for detail and
  summary, and `wxFrame::CreateStatusBar()` when the statusbar's parent is the form
  -- because a frame owns its status bar, and adding a bordered static text instead
  compiles and renders something that is not one (R40's lesson). **Builds clean under
  `-Wall -Wextra`** and runs to exit under Xvfb.

The grid's read-only rule survives into the generated C++ as a construction fact
rather than a convention: `wxLC_REPORT` without `wxLC_EDIT_LABELS`, with the reason
in a comment beside it.

## 4. Eight refusals, measured

`manifest.py` enforces 4b and 10c. Every case below was authored and run against the
real `STUDENTS`/`ENROLL` schemas:

| document | refused |
|---|---|
| `grid` with `ReadOnly=.F.` | BETA-7.1, contract 4b(b) |
| `tree` with a child row | 4b(a) -- a second copy of the closure |
| `statusbar` with a `BINDING` | 4b(c) -- it is not bound to data |
| `statusbar` with `Shows "rows gpa"` | 4b(c) -- closed list |
| `grid` bound to `#2,#3` | AIF-037 cuts `#`; name the field |
| `grid` spanning two aliases, no `Relation` | 10c |
| `text` bound to a two-part spec | 10c -- a spec binds a row |
| `tree` bound to `students.lname` | 4b(a) -- a tree binds the root |

`*` and `enroll.*` on a `grid`, and the frame document itself, pass clean.

## 5. R66.1 -- a pre-existing defect found while wiring this up

`manifest.py` built its alias table with `parse_props(r['SOURCE'])['alias']`.
`parse_props` returns a **dict**, so a `SOURCE` declaring four work areas kept only
the **last one** -- in the field whose entire purpose is to declare several.

R26's lock domains survived it because the `Relation` edges carry the closure
independently, which is why nothing had ever failed. What could not work was the
`alias is not declared in SOURCE` refusal (it checked the schema table instead), and
contract 10c's "first alias" had no first. Fixed with `uidef.doc_alias_tables`,
which keeps every alias in declaration order.

**This is the shape of defect the lane keeps finding: not a wrong answer, an answer
that could not be wrong because the check never ran.**

## 6. The locking methodology, updated

The rule is now stated, and it is general:

> **If the surface returns a STATUS, use it. If the surface only PRINTS, confirm with
> an observer before believing it. Never infer a lock from the absence of an error.**

R64.1 is why. `src/cli/cmd_unlock.cpp` calls the `void` best-effort overload of
`xbase::locks::unlock_*` at all three call sites and prints success unconditionally,
while `include/xbase_locks.hpp` also ships a `bool` + `err` overload. So a provider
that dogfoods the command layer -- which is the charter -- gets a message, not a
result.

`uidef_runtime.LockProvider` now takes an `observe` callable and confirms **every
acquire and every release** against the house's own `LOCK STATUS`. Without an
observer it still runs -- a frontend with no engine attached must -- but it warns
once that it is **UNVERIFIED**, rather than reporting an unverified lock as a lock.

Two constraints landed on the same command, which is worth recording: R64.2 measured
that `LOCK STATUS` reports the CURRENT record rather than the locked one, which would
make it useless for confirming `LOCK <n>` -- and `LOCK <n>` is the verb R47 already
forbids this provider from emitting, for the AIF-116 grouped-locale reason. The
observer is exactly right for the only record verb the provider is allowed to use.

### It runs against the real shell

`gui/uidef/shell_session.py` is the smallest possible glue: it sends a command line
to a live `dottalkpp` over a pipe and returns what the shell printed, framed by a
sentinel it asked the shell to echo. It translates nothing. (It is not
`shell_execute_line` -- that is the in-process C++ entry a compiled frontend embeds,
R61 -- it is the same command surface over a pipe, for the Python runtime and for
tests.)

`gui/uidef/lock_shell_provider_test.py`, run against
`dottalk++ v0.6 (2026-08-19, 8969de78 dirty)`:

```
A acquire domain {STUDENTS, ENROLL} : True   confirmed [True, True]
B release confirmed : True   free [True, True]
C wrong release verb: acquire True  release reports False  still held True
D unverified provider: warned True
   note: UNLOCK on STUDENTS reported success and LOCK STATUS still shows
         the lock held -- R64.1

PASS -- 4 case(s), 0 failure(s)
```

**Case C is the point.** It reproduces correction 34 exactly -- acquire with
`LOCK TABLE`, release with bare `UNLOCK`, the shape R47.2, R48 and R49 all shipped --
and the provider refuses to report the release. That defect cost three rulings and
was found by reading `src/cli/cmd_unlock.cpp` by hand. **The release path now finds it
by itself, on the first run, and names the ruling.**

## 7. Correction 45

`uidef_tk.load()` returned three values and I widened it to four to carry the parsed
`SOURCE`. `dispatch_test.py` and `uidef_tk_menu.py` both unpack exactly three, and
both broke immediately. Reverted; the parse moved to a separate `source_of(path)`.

A shared helper's signature is a contract, and changing its shape is a change to
every caller whether or not you looked at them. Cheap here because a test failed in
the same minute. It is the same class as R22.1, which is a lane lesson I have now
re-learned rather than applied.

## 8. Evidence tier

**runtime-proven**: sections 3, 4, 5 and 6 -- four backends rendered or built from
the authored document, eight refusals authored and run against real schemas, and the
provider run against a live `dottalkpp`. The wx target was built with
`-Wall -Wextra` and run; the Tk target was built under Xvfb and every widget
confirmed mapped.
**Regression swept**: `lock_provider_test`, `lock_semantics_test`, `dispatch_test`
and `scope_test` all still pass, and `AUTHORED.DBF` still renders on all targets.
**planned**: nothing in this ruling. The contract change is stated and implemented.

## 9. Still open

- **`import_scx.py` does not map anything onto the new kinds.** A VFP `grid` is
  still refused on import, which is correct until the `RecordSource` -> tuple spec
  mapping is measured over the corpus. The kinds exist for *authored* documents
  today.
- R64.1, R64.2, R65.3 and R65.4 are still reported and not fixed; they are
  `src/cli/`, `ERSATZ` and AIF-037's areas. R66's provider works **around** R64.1
  rather than fixing it -- if `cmd_unlock` adopts the `bool` + `err` overloads, the
  confirmation step becomes belt-and-braces instead of load-bearing, which is the
  better end state.
- Unchanged: R55.2 (one of two documents is still wrong); the section 13 query limit
  (R62.2); per-handler metadata on `HANDLERS`; the typed C++ provider at the 2^31
  boundary (R63.6) and its lack of an `observe` equivalent; pinocchio-scale;
  whether the lane's other harnesses should become `.dts` (R64).

## 10. Good Neighbor note

- **What changed.** Contract sections 4, 4b (new) and 10c (new). `uidef.py`
  (vocabulary, `doc_source`, `doc_alias_tables`), `manifest.py` (frame checks, spec
  resolution, the R66.1 alias fix), all four backends, and `uidef_runtime.py` (the
  verified provider). New: `author_frame.py`, `shell_session.py`,
  `lock_shell_provider_test.py`.
- **Whose area.** AIF-120's own, entirely. **No engine source was edited** --
  `src/cli/`, `ERSATZ` and the lexer are named in findings and untouched. The
  `dottalkpp` binary was run read-only against the shipped `STUDENTS` and `ENROLL`,
  taking and releasing table locks and leaving both unlocked.
- **What authorization.** Maintainer (member.derald), in-session *"add those to the
  vocabulary and update the locking methodology"*.
- **How to verify or undo.** Verify: `python3 gui/uidef/author_frame.py FRAMEDEMO`
  then render on any target, and
  `python3 gui/uidef/lock_shell_provider_test.py <dottalkpp>` for the provider.
  Undo: the contract sections and the tool diffs revert independently -- the five
  kinds are additive and no existing document uses them.

## 11. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

R65 is still uncommitted; run it first.

```powershell
cd D:\code\ccode

git add dottalkpp/data/scripts/aif120/aif120_tuple_spec_regression.dts
git add docs/maintenance/AIF120_TUPLE_SPEC_V1.md
git diff --cached --stat
git commit -m "AIF-120: R65 -- the grid already ships and the design table cannot describe it; BINDING is a subset and #n is deleted by the lexer"

git add docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md
git add gui/uidef/uidef.py
git add gui/uidef/manifest.py
git add gui/uidef/uidef_text.py
git add gui/uidef/uidef_html.py
git add gui/uidef/uidef_tk.py
git add gui/uidef/uidef_wx.py
git add gui/uidef/uidef_runtime.py
git add gui/uidef/author_frame.py
git add gui/uidef/shell_session.py
git add gui/uidef/lock_shell_provider_test.py
git add docs/maintenance/AIF120_FRAME_KINDS_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R66 -- five frame kinds measured from ERSATZ, read-only written in; the lock provider confirms instead of believing"
```
