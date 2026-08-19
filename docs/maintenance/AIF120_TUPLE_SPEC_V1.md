---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-073
  recorded_at_utc: 2026-08-20T11:40:00Z
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
    requested_by: maintainer (member.derald), in-session "your charter was to write a
      front end gui api for an engine that is already built ... but we dogfood".
  report:
    path: docs/maintenance/AIF120_TUPLE_SPEC_V1.md
    kind: ruling
---

# AIF-120 -- R65: the grid already ships, and the design table cannot describe it

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

The maintainer restated the charter: *"your charter was to write a front end gui api
for an engine that is already built, I understand you need glue, but we dogfood"*.
Taken literally, that reorders the lane's work. The language's job is to **describe
what the engine already renders and already projects**, not to invent a vocabulary
beside it. So I measured what the engine renders and projects.

## 1. The result: five regions the design table has no words for

`ERSATZ GRID`, on the shipped x64 school tables with one relation added:

```
ERSATZ Relational Browser
ROOT: STUDENTS  RECNO: 1
PATH: ENROLL
LIMIT: 3
ORDER: physical

CURRENT ROOT RECORD
  SID      : 50000000
  LNAME    : Taylor
  ...
RELATION TREE
  STUDENTS
   -> ENROLL   ON SID

DESCENDANT SUMMARY
  ENROLL : 4

TUPLE GRID
LNAME                FNAME           GENDER CLS_ID     GRADE
Taylor               Quinn           X      S26PHYS210 IP
Taylor               Quinn           X      W26CHEM200 IP
Taylor               Quinn           X      S26MATH140 C+

ROWS SHOWN: 3 / LIMIT 3 | STATUS: OK
```

Five regions, and the lane's `KIND` vocabulary can name **none** of them:

| the frame has | UIDEF `KIND` |
|---|---|
| a detail panel of `label : value` for the root record | `label` + `field` exist, but nothing binds a whole record |
| a relation tree with the join condition on each edge | no `tree` |
| a per-child count summary | no `summary` |
| a tuple grid whose columns span two work areas | **`grid` is refused** |
| a status footer with rows-shown, limit and status | no `statusbar` |

**R65.1.** The design table was built to describe VFP `.SCX` forms, and it does. It
was never measured against the browses this house actually ships, so it cannot
express the one screen the engine renders by itself. That is the charter's gap, and
it is larger than the single refused `grid` KIND that gate 11 has been carrying.

## 2. R65.2 -- `BINDING` is a strict subset of the engine's own spec grammar

R53 gave `BINDING` the syntax `alias.field` and refused everything else, with four
distinct refusal reasons. **BETA-4.4** freezes the engine's spec resolution as
`*, AREA.*, AREA.FIELD, #n`. Measured, all in
`dottalkpp/data/scripts/aif120/aif120_tuple_spec_regression.dts`:

| spec | engine | `BINDING` |
|---|---|---|
| `LNAME,FNAME` (bare) | resolves | **refused** (R53's bare-field reason) |
| `*` | all fields of the current area | cannot be said |
| `STUDENTS.LNAME,ENROLL.GRADE` | resolves across two areas | accepted |
| `ENROLL.*` | all fields of a named area | cannot be said |
| `#2,#3` | see R65.3 | cannot be said |

`TUPLE ... --AREA-PREFIX` prints headers as `STUDENTS.LNAME | ENROLL.GRADE`, which
is R53's exact syntax -- the engine already writes the lane's binding form as output.
And `--STRICT` produces `ERROR: field 'NOSUCH' not found in area slot 1.`, which is
R53's fourth refusal reason already implemented in the engine.

**The refusal was right and the vocabulary is short.** A `grid` binding needs
`ENROLL.*` the way a `field` binding needs `ENROLL.GRADE`; the contract cannot
currently say "every column of this child".

**Proposed, not applied.** Extending contract section 10b to the engine's four forms
is a change to a shipped ruling (R53) and to the design-table contract. I have not
edited either. The author does not self-approve.

## 3. R65.3 -- `#n` is declared by one house document and removed by another

**Finding, runtime-proven, three ways.**

```
TUPLE #2,#3 --HEADER
  -> 50000000 | Taylor | Quinn | 19921225 | X | CSCI | ... (every field, no header)

TUPLE LNAME,#3 --HEADER
  -> Taylor                                                (LNAME alone, no header)

TUPLE #1
  -> 50000000 | Taylor | Quinn | ...                       (every field)
```

The spec parser never sees the ordinal. The canonical comment vocabulary frozen by
**AIF-037** -- *"Inline comments: `&&` and `#` (cut to end of line)"*, stated in
`lexing/comment_handling_regression.dts` -- cuts `#` and everything after it before
the command is parsed. `TUPLE #1` becomes bare `TUPLE`; `TUPLE LNAME,#3 --HEADER`
becomes `TUPLE LNAME,` and loses its own `--HEADER` flag.

So **BETA-4.4 declares a spec form that the lexer deletes on both the prompt path and
the script path.** The two frozen contracts contradict each other. Neither is wrong
in isolation; they cannot both hold.

This is not a silent failure -- it is worse. `TUPLE #1` prints ten fields and looks
like a working command. A student writing `#3` for "the third field" gets a plausible
answer to a question they did not ask.

**Not fixed here.** The resolution is a house decision (change the ordinal sigil, or
drop `#n` from BETA-4.4, or make `#` comments require leading whitespace), and the
lexer is AIF-037's area. Reported.

## 4. R65.4 -- `ERSATZ GRID` renders three of five regions blind

**Finding.** `ERSATZ GRID` prints `ROOT: (none)  RECNO: 0`, `CURRENT ROOT RECORD
(none)` and `RELATION TREE (none)` while `PATH`, `DESCENDANT SUMMARY`, `TUPLE GRID`
and the footer are all correct in the same frame. `ERSATZ REFRESH` renders the same
state complete. Running `REFRESH` and then `GRID` again returns the blank header --
so `GRID` is a second renderer that never resolves those three regions, not a stale
cache.

Two frames with different titles (`ERSATZ GRID Relational Browser` versus `ERSATZ
Relational Browser`) over one state, and one of them is missing its subject.

**Not fixed here.** `ERSATZ` is not this lane's area. Reported.

## 5. On dogfooding the command layer -- and where it currently cannot be done

R61 established the design: primitives in the libraries, complex commands at the
dottalkpp level via `shell_execute_line`. The charter reminder says the glue should
call that layer rather than reach past it. For `USE`, `SELECT`, `COMMIT` and
`ROLLBACK` that is straightforwardly right and R61 already recorded it.

**For the lock verbs it currently costs the provider its error signal.** R64.1
measured it: `cmd_unlock.cpp` calls the `void` best-effort overload and prints
success unconditionally, so a provider that issues `UNLOCK TABLE` through
`shell_execute_line` gets a success string whether or not anything was released.
`xbase::locks::unlock_table(a, owner, &err)` returns a `bool`. R57's typed provider
needs that bool to honour R47's all-or-nothing acquisition.

**Reported as a gate that blocks the right design, per house rule.** The dogfood
instruction and the command layer's current error handling point in opposite
directions for exactly one family of verbs. Options, for the owner:

1. `cmd_unlock` / `cmd_lock` adopt the `bool` + `err` overloads and report truthfully;
   the provider then dogfoods the command layer for locks as well. (Recommended --
   it fixes R64.1 and unblocks the design in one change, and it is a change to
   `src/cli/`, not to the library.)
2. The provider keeps calling `xbase::locks` for acquire/release and uses
   `shell_execute_line` for everything else, with this ruling as the recorded reason.
   (What it does today, now documented rather than accidental.)

I have not changed the provider. Option 2 is the current state and is honest only
while this ruling stands.

## 6. Evidence tier

**runtime-proven** for sections 1 through 4 -- every transcript above is from
`dottalk++ v0.6 (2026-08-19, 8969de78 dirty)` built from the current tree, run in the
container, driven by the committed `.dts`.
**planned** for section 2's proposal and section 5's option 1 -- both are owner
decisions.

## 7. Still open

- **The `KIND` vocabulary gap (R65.1) is not closed.** Adding `tree`, `detail`,
  `summary`, `statusbar` and `grid` to the contract is the obvious next unit and it
  is a contract change, so it waits on the owner. **BETA-7.1** ("SuperBrowser scope
  locked: read-only only, editing explicitly disabled") constrains what a `grid`
  KIND may be allowed to do, and that constraint should be written into the KIND
  before it is added, not after.
- R65.2's `BINDING` extension, R65.3's sigil collision and R65.4's renderer are
  reported, not fixed.
- Unchanged: R55.2 (still one of two documents is wrong); the section 13 query limit
  (R62.2); per-handler metadata on `HANDLERS`; the typed provider at the 2^31
  boundary (R63.6); pinocchio-scale; R64's open question of whether the lane's other
  harnesses should be converted to `.dts`.

## 8. Good Neighbor note

- **What changed.** One new file:
  `dottalkpp/data/scripts/aif120/aif120_tuple_spec_regression.dts`. No shipped code
  changed. The design-table contract, R53 and `manifest.py` are **untouched** --
  section 2 is a proposal, not an edit.
- **Whose area.** The script sits beside R64's under
  `dottalkpp/data/scripts/aif120/`. R65.3 is AIF-037's area (the lexer) and BETA-4.4's
  (the tuple spec); R65.4 is `ERSATZ`'s. Reported to their owners, not edited.
- **What authorization.** Maintainer (member.derald), in-session charter restatement.
- **How to verify or undo.** Verify: run
  `DOTSCRIPT aif120/aif120_tuple_spec_regression.dts` and read it against the
  EXPECTED OUTPUT block in the script header. It opens STUDENTS and ENROLL read-only,
  adds one relation and clears it, and closes the workspace. Undo: delete the one
  file.

## 9. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add dottalkpp/data/scripts/aif120/aif120_tuple_spec_regression.dts
git add docs/maintenance/AIF120_TUPLE_SPEC_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R65 -- the grid already ships and the design table cannot describe it; BINDING is a subset and #n is deleted by the lexer"
```
