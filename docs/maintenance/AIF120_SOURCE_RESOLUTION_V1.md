---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260821-COWORK-093
  recorded_at_utc: 2026-08-21T00:40:00Z
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
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: 3f338bc30
  authorization:
    requested_by: maintainer (member.derald), in-session -- "make the improvements",
      taking the unit R82 section 7 named.
    scope: >
      Perform the refusal contract section 10 declares, read a DTSHEMA workspace
      from Python, and make the generated wx host open the tables its own
      document names instead of a CSV from the environment. Writes gui/uidef/
      and docs/ only.
  report:
    path: docs/maintenance/AIF120_SOURCE_RESOLUTION_V1.md
    kind: ruling
---

# AIF-120 -- R83: the generated frontend reads its own document, and section 10's refusal finally happens

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

R82 found that contract section 10 has ruled on table location since 2026-08-19
and that nothing implemented it: no tool refused an unresolvable `Table`, the wx
host read its table list out of an environment variable, and all 22 fixtures
depended on that. This closes all three. `gui/uidef/workspace.py` reads a DTSHEMA
posture the way the engine reads one; `manifest.py` performs section 10's
refusal; and `wx_host.cpp` opens the tables **its own document names**, proven by
building the target and running it against the MCC x64 tables. The first thing
the new check caught was ours.

## 1. `workspace.py` -- written from the engine, not from a sample

R82.3's mistake was reading a pasted v2 workspace instead of the format. This
reader is written from `src/cli/cmd_workspace.cpp` -- `schema_load_from_stream`
at :1800 and the v3 writer at :1542 -- and two of its behaviours would not have
been guessable from any sample:

- **Root lines apply in LINE ORDER.** `DBFROOT` re-points resolution for the
  `AREA` lines that FOLLOW it (:1759). The writer always emits roots first, so it
  never shows; a hand-edited posture with them reordered means what the engine
  says it means.
- **An index resolves against `IDXROOT` first and falls back to `DBFROOT`**
  (:1820) -- and only when the first candidate actually EXISTS. A table gets no
  such fallback.

The load-time roots are **per-load**: a v3 posture re-points resolution for that
load and never mutates the global `SETPATH` slots.

The reader encodes R82.3 rather than smoothing it. **A v2 workspace returns
`dbf_root is None` and every resolution through it returns `None`**, because a v2
posture states which table and not where. A reader that quietly fell back to an
environment variable would reproduce the exact defect R82 exists to name.

## 2. `manifest.py` -- the refusal section 10 declared

Section 10 has said since 2026-08-19 that a document whose `Table` does not
resolve is **refused, never rendered unbound**, because "a width silently derived
from a schema that was never opened is worse than no width". `source_resolution()`
performs it, in the contract's own order:

1. **Document-relative** -- section 10's primary rule, measured from VFP, which
   recomputes a data-source path relative to the form on every save. A bare name
   is the zero-distance case of that rule, not a fallback.
2. **Through a declared workspace**, if one is supplied and self-locating -- R82's
   ruling, and per R82.3 that means DTSHEMA 3.
3. **Otherwise REFUSE.**

What it deliberately does **not** do is fall back to the environment. Reading
`SETPATH`, `R70_DBF` or the current directory would make every document resolve
and would report exactly the ambient dependency section 10 forbids. **An
unresolvable `Table` is the honest answer** when neither the document nor a
declared posture says where the table is.

Measured, on `N1_editable_grid`:

```
no workspace       REFUSE Table STUDENTS.DBF -- does not resolve beside the
                          document, and no self-locating workspace was supplied
the shipped v2     REFUSE Table STUDENTS.DBF -- ... the supplied workspace is
                          DTSHEMA 2 -- it declares which table, not where (R82.3)
a v3 posture       NOTE   Table STUDENTS.DBF -- resolves through the declared
                          workspace -> .../DBF/x64/STUDENTS.dbf
```

## 3. The first thing it caught was ours

`author_mainframe.py` -- R78's round trip of the house's own wx frame -- declared:

```
Alias = workspace
Table = (none -- the sample fills every grid from code)
```

**An English sentence in a field contract section 10 defines as a path.** It
survived four rulings because nothing checked `Table`; the check found it on its
first run, which is a fair advertisement for the check.

The frame really has no data source and nothing in the document binds, so the
alias was a work area that does not exist -- R70.5's class of defect, a
declaration nothing acts on. The sentence was true and worth keeping; it belongs
in `NOTES`, where prose is the point. **After the fix the generated C++ is
byte-identical**, which is the proof that the alias was decoration.

## 4. Case-insensitivity, and a citation I should not have made

Section 10 says resolution is case-insensitive (R28.3). My first resolver did
exact matching, and on Linux it reported every table missing -- the corpus writes
`STUDENTS.DBF` and the file on disk is `STUDENTS.dbf`. That looks like a policy
finding and is a filename mistake. This lane has walked into that four times in
one session; a resolver that did not implement section 10's own case rule was
going to be the fifth. `ci_path()` in the reader and `resolve_ci()` in the host
implement it, and both return the real on-disk spelling.

Separately, and worth recording: **I labelled that trap with a BETA item number in
a docstring**, hours after retargeting citations away from the BETA checklist
because the owner ruled it a template. Caught by the maintainer, corrected to a
measurement in the same file. The pull toward a familiar number is exactly why
that retargeting is still on the open list.

## 5. `wx_host.cpp` reads `SOURCE`

The host read `R70_DBF` and a CSV out of `UIDEF_TABLES`, and its own comment
called that *"the demo's stand-in for what a real host reads out of the
document's SOURCE"*. Now:

- **WHICH tables comes from the document.** `uidef_wx.py` emits
  `uidef_source_tables()` beside `uidef_attach_source` and under the SAME gate, so
  the pair cannot go missing separately (correction 54). `UIDEF_TABLES` is gone.
- **WHERE comes from the invocation**, which is the house's own answer: R82.3
  found `resolve_open_target` accepting ten slot names so that
  `WORKSPACE OPEN DBF` means the configured slot. The host asks
  `dottalk::paths::get_slot(Slot::DBF)` first -- the same slot `SETPATH` and
  `DO X64` set -- and falls back to an explicit `UIDEF_DBF_ROOT`.
- **A missing root now SPEAKS.** It used to return in silence and the frontend
  came up with every grid empty. `WORKSPACE LOAD` refuses a shortfall for exactly
  this reason; a frontend that does it quietly is the same failure with a window
  in front of it:

```
uidef_host: the document declares 2 table(s) and NOTHING SAYS WHERE THEY ARE.
The DBF path slot is unset and UIDEF_DBF_ROOT is not in the environment, so no
area was opened and every bound control will be empty. Location is a workspace
fact (AIF-120 R82).
```

## 6. Proof

| | |
|---|---|
| build | clean configure + build, **56s, 66 translation units, 2,277,368 bytes** (R76's baseline reproduced first at 51s / 2,268,520 before any change) |
| run | `docs/maintenance/evidence/AIF120_R83_source_run.png` -- opened `STUDENTS.DBF` and `ENROLL.DBF` **named by the document**, three distinct students against their own enrolments, `-> ENROLL ON SID (matches: 2)`, `ENROLL : 2`, `rec 3 / 200 [physical]` |
| without `--stream` | **22 of 22 byte-identical.** R70's opt-in invariant holds |
| with `--stream` | 7 of 22 change -- exactly the documents that bind -- and every one is **15 lines added, 0 removed.** Purely additive |
| `workspace.py --selftest` | 15 checks, including that a v2 posture must NOT resolve |
| section 10 check | proven in all three states in section 2 |
| ASCII | clean across all five changed files |

## 7. What is NOT proven, stated rather than left to be discovered

- **The v3 reader has never seen a real v3 file.** Every `.dtschema` in the tree
  is v2. `selftest()` builds a synthetic v3 and proves the PARSE, which is a proof
  about this reader and not about the engine's output. One
  `WORKSPACE SAVE mcc_x64 V3` settles it and the reader is written to be checked
  against that, not to be trusted before it.
- **Section 10 is a REPORT, not yet a generate-time refusal.** Turning it into one
  today would refuse all 22 fixtures, because they are the documents that violate
  it. Enforcement and corpus migration are ONE cut and the corpus cannot move
  until a v3 posture exists. The check exists, runs, and tells the truth in the
  meantime, which is the difference between a rule nothing checks and a rule
  nothing yet blocks on.
- **MSVC.** Unchanged. Everything here is gcc 13 / wx 3.2.4 / Linux.

## 8. Open

- **`WORKSPACE SAVE mcc_x64 V3`**, then point the fixtures at it and flip section 10 to a refusal. One commit.
- **R82.4** -- `mcc_x64.dtschema` declares `tag=none` for thirteen areas while `mcc_x32.dtschema` declares real tags. Worth deciding before the v3 save bakes it in.
- **The 26 BETA citations** -- four are still live in `manifest.py`, and one prints in its normal output.
- **`Descending`** -- R73.6, owner decision.
- **Tk through `grid()`**, **`FLOW = grid` growth**, **negotiable geometry** -- unchanged.

## 9. Good Neighbor

| | |
|---|---|
| What changed | `gui/uidef/workspace.py` (new), `manifest.py` (s10 check + `--workspace`), `uidef_wx.py` (emits `uidef_source_tables`), `wx_host.cpp` (reads SOURCE, speaks when it cannot resolve), `author_mainframe.py` (prose out of a path field); this ruling; evidence; ledger rows |
| Whose area | AIF-120. `src/` and `include/` untouched -- the engine was READ, not changed |
| Authorization | maintainer, in-session: "make the improvements" |
| How to verify | `python3 workspace.py --selftest`; `python3 manifest.py --text --workspace <f.dtschema> N1_editable_grid.DBF`; `cmake -S . -B build && cmake --build build`; run with and without `UIDEF_DBF_ROOT` |
| How to undo | `git revert`. Without `--stream` every document generates byte-identically either way |
| Risk | low. The generated change is additive, the section 10 check is a report, and the host's behaviour without a root went from silent to spoken |
