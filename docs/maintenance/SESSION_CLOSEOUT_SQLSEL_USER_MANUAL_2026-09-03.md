---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260903-003
  recorded_at_utc: 2026-09-03T23:02:33Z
  agent:
    provider: OpenAI
    product: Codex
    model: not_exposed
    access_mode: local_write
  session:
    id: 019fb3e1-9c71-7610-944f-eac3763c4ff4
    chat_reference: product-task:019fb3e1-9c71-7610-944f-eac3763c4ff4
    run_id: CODEX-20260903-009
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: e1217dc8cea961fd8f696a6475da79604decb4b9
  authorization:
    requested_by: maintainer
    scope: write the x64base SQLsel manual
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_SQLSEL_USER_MANUAL_2026-09-03.md
    kind: session_closeout
---

# Session Closeout -- SQLsel User Manual (AIF-074)

Date: 2026-09-03.
Owning lifecycle: SQLsel PDLC P6.
Truth state: authored and runtime-checked on `development`.
Publication state: local review-needed draft; not promoted to `main` or public
documentation.

## One-line summary

SQLsel now has a workflow-oriented user chapter that describes the behavior the
development runtime actually has, names the limits it does not cross, and was
checked against the shipped x64 tables plus all seven SQLsel/evaluator gates.

## Changed

| Area | Files | Result |
| --- | --- | --- |
| User manual | `docs/manuals/user/sqlsel.md` | Added a 729-line chapter covering setup, grammar, single-table selection, JOINs, access paths, read fences, committed truth, blanks and produced absence, workspaces, the legacy scan, recovery, the current capability matrix, complete patterns, and maintainer gates. |
| Manual navigation | `docs/manuals/user/README.md` | Added the SQLsel and workspace chapter links. |
| Source-owned examples | `src/cli/cmd_sql_select.cpp` | Made canonical one-verb SQLsel the harvested usage form and corrected the shipped ENROLL field from nonexistent `COURSE` to `CLS_ID`. The optional leading `SELECT` remains documented. |
| Durable lane state | `docs/maintenance/SQLSEL_PDLC_LANE_V1.md`; `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` | Marked the user-manual portion of P6 in progress without claiming HELP, manualgen, curriculum, main staging, or publication. |

Feature/manual commit:

- `6df5592df` -- `AIF-074: author the SQLsel user manual`.

The commit also carries the hook-generated Tier-0 refresh. Its object contains
`Authored-by: member.ai.codex.local`, `Approved-by: review-needed`, and
`Verified-by: member.ai.codex.local`.

## What the manual establishes

- `SQLSEL` is the select verb. `SQLSEL SELECT ...` remains compatible, but the
  one-verb form is canonical.
- Statement SQLsel is set-oriented and session-neutral. Legacy SQLsel is a
  current-area diagnostic scan and may move the cursor.
- SQLsel and REL/RelTalk are peers over engine seams, not interchangeable names
  for one relation graph.
- Current grammar includes single-table selection, one-field ordering, limit,
  `COUNT(*)`, and one two-table INNER/LEFT/RIGHT/FULL/CROSS join.
- JOIN path choice, cooperative read fence, and outer extension counts are
  reported rather than inferred.
- DBF blank remains a value. Produced outer-join absence has an internal kind
  and displays as `<UNMATCHED>`; it is not stored SQL NULL.
- Statement SQLsel reads committed truth and excludes deleted records.
- SQLsel has no workspace-qualified namespace. Unique names across process-wide
  open work areas are the safe current practice.
- Planned set operations, grouping, aggregates beyond `COUNT(*)`, subqueries,
  DML, and SQL transactions are visibly labeled not implemented.

## Dogfood finding and correction

The source usage contract offered this shipped-data example:

```text
SQLSEL S.LNAME,E.COURSE FROM STUDENTS S JOIN ENROLL E ON S.SID = E.SID
```

The development runtime refused it correctly because the shipped x64 `ENROLL`
table has no `COURSE` field. Its class identifier is `CLS_ID`. The corrected
statement ran against the shipped 200-row `STUDENTS` and 686-row `ENROLL`
tables, reported a canonical two-table fence and nested-loop scan, emitted
three limited rows, reported 683 more, and left both pre-positioned cursors on
their original records.

This was a documentation defect, not a JOIN evaluator defect. The source-owned
examples and new manual now say `E.CLS_ID`.

## Verification

The Release all-target build first reconfigured successfully but could not
replace `build/Release/dottalk_bbsd.exe` because a daemon held that unrelated
binary open. The narrower product target then passed:

```text
cmake --build D:\code\ccode\build --config Release --target dottalkpp
```

The rebuilt executable identified itself as version 0.6, source commit
`6df5592d`, dirty only because unrelated shared-tree work remains present.

One fresh process then ran `SQLSEL HELP` and all seven named gates:

| Gate | Result |
| --- | --- |
| `SQLSEL_SELECT_V1` | PASS -- 11/11 SQLite row sets; cursors 3/3; refusals 8/8; limit reports 2/2; sort paths 4/4 |
| `SQLSEL_INNER_JOIN` | PASS -- 4/4 SQLite row sets; cursors 2/2; refusals 3/3; paths 2 seek/2 scan |
| `SQLSEL_JOIN_EDGES` | PASS -- 4/4 SQLite row sets; cursors 4/4; refusals 4/4; fences 4/4; caller lock; paths 2 seek/2 scan |
| `SQLSEL_LEFT_JOIN` | PASS -- 4/4 SQLite row sets; absence distinction; extensions 4/4; cursors 2/2; caller lock; paths 2 seek/2 scan |
| `SQLSEL_JOIN_FAMILY` | PASS -- 10/10 SQLite multisets; RIGHT/FULL/CROSS path composition; fences 10/10; extensions 12/12; refusals 5/5 |
| `SQLSEL_BUFFER_VIS` | PASS -- 5/5 committed row sets; dirty preview 2/2; cursors 3/3 |
| `EVALDIFF` | PASS -- 22/22 exact truth/error vectors; verdict parity 17; failure parity 5; cursors 2/2 |

The feature commit hook also passed repository-role, AIF collision, reference
authority, house-style ASCII, version coherence, mandatory-tracked,
manual-link-integrity, Tier-1 budget, R-number collision, and scoped pre-push
checks. `git diff --cached --check` was clean before commit.

## Boundaries and next steps

This is a user-manual draft, not a public release claim. It does not mutate HELP
DBFs, regenerate the developer manual, add LabTalk lessons, promote to
`C:\x64base`, modify the website, or publish anything.

The next documentation steps are, in order:

1. independent technical and user-language review of this chapter;
2. harvest the corrected source contract through the protected HELP pipeline;
3. regenerate and verify the developer-manual candidate rather than hand-editing
   generated output;
4. derive a LabTalk lesson and evidence gallery only from reviewed behavior;
5. promote and publish through their own gates.

The next runtime SQLsel phase remains P4.5 DISTINCT and set operations after the
owner rules OQ-11 operand compatibility.
