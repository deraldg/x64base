---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260910-COWORK-202
  recorded_at_utc: 2026-09-10T20:40:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260910-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 95096c507
  authorization:
    requested_by: steward (member.derald), in-session 2026-09-10 -- authorized the
      WORKDESK spec repair ("go", "green"), the metadata-report scan, the
      workareas.hpp triage ("together"), ruled that "an unqualified table name
      should open/select in the current workspace always -- then most legacy
      scripts will work by default" ("of course"), authorized the MWXSHAKE
      repair with the standing instruction "always go gold unless the cost is
      platinum", and asked for the structures to be written up for the AI
      portal.
    scope: |
      Lanes AIF-078 (multi-workspace), AIF-070 (MINIDB), rulings R131 and R134,
      open question Q8. Write access exercised in this session, and no wider:
        src/cli/cmd_select.cpp, src/cli/cmd_use.cpp, src/cli/workareas.hpp,
        src/cli/cmd_regression.cpp, src/workspace/workarea_utils.hpp,
        dottalkpp/data/scripts/workspace_minidb_multi_shakedown.dts,
        docs/maintenance/WORKSPACE_WORKAREA_WORKDESK_STRUCTURE_MAP_V1.md,
        docs/maintenance/SESSION_CLOSEOUT_WORKSPACE_SCOPING_AND_WORKDESK_2026-09-10.md,
        docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md.
      Plus the removal of the dead cli workdesk header and its translation
      unit, both deleted in this change set and so deliberately not spelled as
      live paths here.
      NOT authorized and NOT touched: the pseudo chat board, the help DBFs and
      the cmdhelp translation unit (concurrent session), the publication
      staging tree on the C drive, the ERP system, and the correction pending
      on the cmd_workdesk header, which is drafted and deliberately unstaged
      because the duplicate-open ruling behind it is the owner's to make.
      This report is review-needed. The author does not self-approve.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_WORKSPACE_SCOPING_AND_WORKDESK_2026-09-10.md
    kind: session_closeout
---

# Session closeout -- workspace scoping, WORKDESK, and what first-wins was hiding
# 2026-09-10

Status: **review-needed.** Owner: member.derald. Author:
member.ai.claude.cowork. Baseline `95096c507`.
Lanes: AIF-078 (multi-workspace), AIF-070 (MINIDB), R131, R134, Q8.

---

## 1. The sentence this session turns on

> **"I played with it. The first thing I noticed is when I was in workspace 3,
> I selected students and it grabbed the first one it found instead of the
> students in workspace 3."** -- owner, 2026-09-10

Then, after the qualified-name syntax was recovered from the record rather than
reinvented:

> **"I think an unqualified table name should open/select in the current
> workspace always. Then most legacy scripts will work by default."**

That is the whole session. Everything below is either implementing that
sentence or dealing with what implementing it revealed.

---

## 2. What was ruled, and where it already lived

The ruling is **not new**. It was already closed and the session's first job
was to find that out instead of re-deciding it:

- **Q8** (closed 2026-08-27, P6 / Grok precepts packet
  `AIPR-20260827-GROK-001`, owner-accepted): unqualified names resolve to the
  current workspace's member; qualified form `SALES:STUDENTS.FNAME`. The packet
  says *"do not re-open it."*
- **R134** (2026-08-31, owner): *the alias is the path, COMPOSED not stored.*
  The alias namespace is GLOBAL, the alias is `WS:TABLE`, unique by
  construction; `logicalName()` keeps returning the bare name and the qualified
  form is DERIVED.
- A bracket spelling (`ws[3]:students`) was considered in August and
  **WITHDRAWN** -- it dies in the shipped parser and would be a third address
  spelling beside a working one.

What 2026-09-10 added is that `USE` obeys the same scoping as `SELECT`, which
is the owner's sentence above.

---

## 3. Code that moved

| file | change | state |
|---|---|---|
| `src/cli/cmd_select.cpp` | rewritten around `owner_of(i)` / `area_answers_to()` / `all_slots_answering()`; splits on the first `:`, resolves the workspace, filters the loop by owner. Refusal NAMES where the table actually is and suggests the spelling. `@dottalk.usage` gained `SELECT <workspace>:<name>`. | uncommitted |
| `src/cli/cmd_use.cpp` | alias uniquing scoped: `find_open_area_by_alias()` and `derive_distinct_alias()` take a workspace handle; call sites pass `current_handle()`. Refusals now say "in this workspace (`<name>`)". | uncommitted |
| `src/cli/workareas.hpp` | three changes -- see section 4 | uncommitted |
| `src/workspace/workarea_utils.hpp` | annotated: the spec stayed here, the implementation moved, and did not meet it until today | uncommitted |
| `include/cli/cmd_workdesk.hpp` | `WorkAreaSet` paragraph corrected after `print()` was deleted | committed `95096c507` |
| `dottalkpp/data/scripts/workdesk_arm_regression.dts` | third cut -- two directories, two files sharing a basename | committed `95096c507` |
| `dottalkpp/data/scripts/workspace_minidb_multi_shakedown.dts` | see section 5 | uncommitted |
| `src/cli/cmd_regression.cpp` | WORKDESK validator + entry; WSMULTI entry corrected; MWXSHAKE entry rewritten; the MWXSHAKE summary split into four adjacent string literals after it crossed MSVC's 16384-byte per-literal cap (`C2026`) | uncommitted |

**The refusal is the deliverable, not the scoping.** A scoped resolver that
just says "not found" would have made the owner's own session harder, not
easier. What ships instead:

```
SELECT: 'STUDENTS' is not open in ws3. It IS open in DEFAULT (area 8),
        ws2 (area 21) -- qualify it, e.g. DEFAULT:STUDENTS. Nothing was selected.
```

The suggested spelling comes from the first workspace actually NAMED, not from
`elsewhere.front()`, so the example is always a spelling that works.

---

## 4. `workareas.hpp` -- three defects, one of which needed no second workspace

Triage began here at owner direction ("start triage with workareas.hpp"),
because it is the file every level-1 report reads through.

**A. `occupied_desc()` was a RANGE over a SET.** It printed `{front..back}`, so
open slots `{0,3}` rendered `{0..3}` -- four areas claimed where two were open.
The four-line contract (`{}` / `{5}` / `{0..16}` / `{0..19,50..54}`) had been
sitting in `src/workspace/workarea_utils.hpp:25-29` the whole time; the
definition moved to `src/cli/workareas.hpp` and left its spec behind. Repaired
against those four lines and verified in a standalone harness against seven
inputs including all four documented examples.

**It needed no second workspace to be wrong.** `USE <t> IN 3` with area 0 open
produces exactly that arrangement, and `USE_ARGS` `U_T4` sets it up on purpose.
Two workspaces only made it routine.

**B. `WorkArea::file_name()` returned the ALIAS.** Its only consumers are in
`cmd_wsreport.cpp`, one of which prints it under the literal column heading
`FILE`. So the report answered "which file" with a name that is not a file and
that both same-named areas share. Twelve such pairs were measured in one
session across an x64 and an x32 workspace. It now returns
`DbArea::filename()`; `label()` keeps returning the alias; the header carries
the instruction that they must not collapse back into one function.

**C. `WorkAreaSet::print()` and the free `workareas::print()` had ZERO
callers** and were deleted. The only surviving mention of their `Slot Cur Name`
format was a comment in `cmd_workdesk.hpp` citing it as canonical -- **that
comment was the formatter's only audience.** `<iostream>` was deliberately
KEPT, with a note: hundreds of translation units have been getting it
transitively, and dropping it is a separate change with its own blast radius.

---

## 5. MWXSHAKE -- five red markers, and none of them an engine regression

Scoping `SELECT` turned five MWXSHAKE markers red in one run. Every one was an
arm reaching into a workspace it was not standing in, which first-wins had been
quietly completing for it.

**Three classes of defect, one indistinguishable green:**

1. **Wrong spelling, right intent** -- `MWX_G1a`, `MWX_G1b`, `MWX_T3`,
   `MWX_T4`, `MWX_T7`. Each arm's own English already named the workspace it
   meant. Qualified to `MWXONE:MWXP`, `MWXTWO:MWXQ`, `MWXKID:MWXK`.
2. **Passing on RESIDUE** -- `MWX_T3` and `MWX_T7` did NOT go red, which is
   worse. A refused `SELECT` leaves the current area untouched, so an arm whose
   previous select happened to land well reads the right field for the wrong
   reason. T7's residue was T6's successful select of the very table it wanted.
3. **The arm never touched the thing it was named for** -- `MWX_T1` read `MWXQ`
   as proof that `OPEN ... AS MWXAS` named a workspace. MWXQ **cannot** be a
   member of MWXAS: the directory open's re-entry guard
   (`src/cli/cmd_workspace.cpp:1509`) asks whether the FILE is open ANYWHERE,
   MWXTWO had opened it twenty lines earlier, so MWXAS is born holding only
   MWXSHARE.
4. **The arm could not distinguish its outcome from its opposite** -- `MWX_T2`
   documented parking the cursor on a NON-DEFAULT row and parked with `GO 1`,
   the row a re-open lands on, over a one-row fixture. It passed either way,
   and had since 2026-08-28.

T1 and T2 were rebuilt to read `MWXAS:MWXSHARE`; B's `MWXSHARE` gained a second
row so `GO 2` is a real park. **Runtime-proven 2026-09-10 on the repaired
build: 48 markers, 17 guards and 31 arms, all `.T.`** -- and T2's post-re-entry
read now shows `Recno: 2`, which the old arm could never have shown.

**`MWX_T5` is left UNCHANGED, still green, and annotated as UNPROVEN** -- see
section 7. Its premise is false about this script and the verb it tests refuses
the operation outright.

**The header's marker count was stale a fourth time**: 40/14/26 declared
against an artifact of 48/17/31, while the REGISTRY ENTRY has recorded 48 since
the 2026-08-29 promotion. Two declarations of one number disagreed in the tree
for twelve days and the one that is CHECKED was right throughout.

---

## 6. What was written for the portal

- `docs/maintenance/WORKSPACE_WORKAREA_WORKDESK_STRUCTURE_MAP_V1.md` -- **the
  three structures and how they interact**, which did not exist anywhere.
  Twenty-seven documents under `docs/maintenance` carry workspace material and
  every one answers a single question; two of the three levels (`WorkArea` /
  `WorkAreaSet`, and WORKDESK) had no document at all. Thin where the record is
  thick, with a routing table; thick where nothing existed.
- Project docs: `FACT_ONLY_CMD_USE_UNIQUIFIES_A_LOGICAL_NAME.md`,
  `FINDING_THE_FIXTURE_USED_THE_ONE_ROUTE_THAT_COULD_NOT_PRODUCE_THE_CONDITION.md`,
  `SCAN_20260910_METADATA_REPORTS_UNDER_THE_MULTI_WORKSPACE_MODEL.md`,
  `FINDING_FIRST_WINS_WAS_COMPLETING_THREE_ARMS_ADDRESSES_FOR_THEM.md`.

---

## 7. Open, and stated rather than implied

1. **Is the duplicate-open guard GLOBAL or PER-WORKSPACE?** It is global in all
   three verbs that have one -- `WORKSPACE OPEN` (`cmd_workspace.cpp:1509`),
   `WORKSPACE ADD` (`:5947`), and `USE`'s open guard -- and all three were
   written when there was one workspace. `MWX_T5` turns on it. So does the
   already-open item that a bare `USE` in ws3 still demands `AGAIN` when DEFAULT
   holds the file. **One question, three verbs, one ruling.**
2. **`include/cli/cmd_workdesk.hpp:100-102` is FALSE.** The `NameFanout` struct
   comment says the fanout is *"SUPPORTED -- `USE <t> AGAIN` asks for it on
   purpose"*, which is the exact inversion: `USE ... AGAIN` is the one route
   that cannot produce it. The corrected passage landed in the .cpp
   (`src/cli/cmd_workdesk.cpp:175-180`) and not in the .hpp. One struct, two
   comments, opposite claims, and the header is the one a reader meets first.
   **Prepared, deliberately NOT applied** -- it is an `include/cli` edit that
   was not authorized and the owner was mid-build.
3. **Four verified falsehoods in metadata reports**, from the 2026-09-10 scan,
   proposed as one commit and not yet authorized: `cmd_cdx.cpp:145` (tests
   `isCnx` under a comment saying "if a CDX is currently active" --
   `cmd_cnx.cpp:143` has the identical line correctly), `cmd_setorder.cpp:662`
   and `cmd_setlmdb.cpp:179` (print a direction with no `isNaturalOrder()`
   test), `cmd_setlmdb.cpp:243` (reports an envdir under INDEXES when the
   engine opens one under LMDB). Systemic finding: `grep -ic workspace` over
   the eighteen index/order/container display files returns **ZERO**.
4. **R131 Q3** remains unruled: `WORKSPACE OPEN <dir> AS <name>` does not stamp
   roots from the directory it opened, and `WORKSPACES.dbf` declares `DBF_ROOT`
   and `IDX_ROOT` only, so the LMDB slot has no durable column at all.
5. **A citation in `include/xbase/workspace_membership.hpp:51` cannot be
   resolved.** It names a cursor_hook header as the house's cautionary example;
   no such file exists under `include/`, `include/xbase/` or
   `include/workspace/`. The ARGUMENT stands; the example does not.
6. **WORKDESK has no HELP entry** -- `[WARN] HELP (1): WORKDESK` on every
   commit. Owner: *"let it mellow."*

---

## 8. Two mistakes this session made, recorded

**A gate prediction that was wrong.** The WORKDESK commit was BLOCKED on
`check-site-artifacts`: adding one element to a counted array moved
`total_specs` 81 -> 82 and the site still said 81. The prediction had been
about the provenance STAMP and never checked the NUMBER underneath it.
**Predicting a gate means predicting what the gate MEASURES, not what it last
printed.**

**A near-miss that did not ship.** A stale staged copy of `cmd_wsreport.cpp`
nearly produced a false defect report against a function the live file no
longer has. Re-staging from the device before asserting is the only reason it
did not. Disclosed unprompted.

**And one that did ship, briefly.** The MWXSHAKE registry entry crossed MSVC's
per-literal string cap and broke the build (`C2026`). Split into four adjacent
literals; the text is unchanged. The next-largest entry in that file is 14,936
bytes -- under the 16,384 cap, but not by much.

---

## 9. Not claimed

- Nothing here is committed except `95096c507`. Seven files are uncommitted on
  disk and want BUILD, TEST, THEN COMMIT.
- The site tree has four uncommitted files (two re-derived artifacts, two
  `.mdx`). **Publishing is the owner's act.**
- `C:\x64base` promotion is not touched.
- No DBF, HELP table, metadata catalogue, manual, fixture or publication output
  was mutated.

Ships **review-needed**. The author does not self-approve.
