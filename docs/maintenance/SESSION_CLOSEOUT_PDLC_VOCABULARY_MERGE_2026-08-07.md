---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260807-003
  recorded_at_utc: 2026-08-07T18:05:00Z
  agent:
    provider: Anthropic
    product: Claude Cowork
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.labtalk.pdlc
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 9e42e318b28d1b9e17f632e51f75f23fc83e9223
  authorization:
    requested_by: maintainer
    scope: Retire the PLDC acronym, merge it into PDLC, across development and the website source.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_PDLC_VOCABULARY_MERGE_2026-08-07.md
    kind: session_closeout
---

# Session Closeout -- PLDC to PDLC vocabulary merge (AIF-094)

Date: 2026-08-07.
Owning lifecycle: maintenance.
SDLC lane: maintenance.
Truth state: observed.
Proof state: git-verified.

AIF-094 was claimed retroactively, after this closeout was first committed as
`(no lane)` and `session-log-check` correctly reported it as unattributable.
Claim: `coordination/aif/AIF-094.claim`, run `COWORK-20260807-004`, lane
`pdlc-vocabulary-merge`. Owning project: `project.labtalk.pdlc`.

## One-line summary

Retired the PLDC acronym and folded it into PDLC across two repositories, then
spent most of the session discovering that the mechanical part was the easy part.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Vocabulary merge | 68 tracked + 3 renames | `c0d3069c5`. Renames detected at R099/R096/R095, history follows |
| Doctrine | `SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md` | Two rows collapsed to one; mode-switch clause; merge note. `c0d3069c5`, `018bd0c9f`, `03282baaa` |
| Rulings | `X64BASE_AGENT_SKILL_PDLC_LANE_V1.md` | R1 struck through and superseded by new R8 |
| Lesson | `lessons.d/lesson.career.a_gitignored_path_is_invisible_to_your_sweep.yaml` + body | `7ad5adc32`, registry re-merged not hand-edited |
| Handoff | `docs/agents/HANDOFF_PDLC_MERGE_TO_PAUSED_SESSIONS_2026-08-07.md` | `f7c514fe5`, revised `03282baaa` |
| Bundle (gitignored) | `docs/ai-friendly/gptbase_bundle_v1/05_process_and_roles.md` | Two dangling paths + one heading. Not committable |
| Website source | 3 mdx + regenerated public report | `906891990` in `D:\dev\x64base-site` |

No source file was touched. No `.cpp`, `.hpp`, `.h`, or `.py` in the tree ever
contained `PLDC`.

## Verified (proof performed this session)

- **Renames carry history.** `git diff --cached -M --name-status` returned
  R099/R096/R095, not add+delete pairs.
- **Staged set contained no foreign work.** After an initial staging error (see
  below), a per-file diff of staged changed lines against the term `PDLC` left
  exactly one hit, hand-inspected and confirmed to be a context line inside a
  deliberate two-bullet merge. Shortstat went 1207/308 -> 168/162.
- **Registries still parse.** `yaml.safe_load` on all 8 touched YAML files and
  `json.load` on `portal_truth_audit_latest.json`.
- **Website build is clean.** `npm run build` passed `check-diagrams` and
  `check-public-content`; `grep -rIl PLDC out dist` returned nothing;
  `out/reports` was stripped as designed.
- **The private report stays private.** The `--public` build printed
  `SKIPPED (private per portal.yaml)` for both `BBS_ACCESS_REPORT.html` and
  `AIF_RULINGS_REPORT.html`, and the shipped `AI_PORTAL_REPORT.html` contains no
  link to either.
- **NOT verified:** `portal_truth_audit_latest.{md,json}` are hand-edited. The
  regeneration path is blocked (see "Still open").

## AI-facing docs updated (AIF-006 gate)

`PSEUDO_CHAT_BOARD.md` carries AIF-092's verification post; the maintainer
transcribed it and an `RE:` reply is owed back. No lane state changed -- this pass
opened no lane and closed none.

## Published

`D:\dev\x64base-site` committed at `906891990` and published to GitHub Pages
before the report was regenerated, so the live copy is one revision stale. A
later `publish:github-pages` was refused: the publisher requires a clean source
worktree and another session's untracked portal work is present. Not a blocker.

## Handoff left (AIF-082 gate)

`docs/agents/HANDOFF_PDLC_MERGE_TO_PAUSED_SESSIONS_2026-08-07.md`. Aimed at
AIF-092 and any session that paused during the pass: what moved, what was decided,
which PLDC survivors are deliberate, and the failure mode below.

## What went wrong, recorded because it is the useful part

**1. A blind replace would have produced incoherent doctrine.** PLDC and PDLC
were contrasted deliberately in ~8 places, and an owner ruling (R1, 2026-08-06)
had ruled the *opposite* of the merge instruction. Caught before applying;
resolved by collapsing the table, reversing R1 in place, and dating both.

**2. My staging slice fused ~570 lines of other sessions' work.** `git add <path>`
stages whole files. Ten of 81 paths carried foreign edits, four of them untracked
files belonging to other sessions. Caught by diffing staged lines against the
search term before committing, not by the gate. Unstaged and left for their owners.

**3. My "zero PLDC remains" claim was false, and no internal check could have
caught it.** Ripgrep honors `.gitignore`; `.gitignore:346` and `:323` hid a bundle
packaged for an outside model. The edit and the verification shared a tool, so
each pass raised confidence without moving coverage. An independently-scoped
session (AIF-092) found it in minutes. Written up as
`lesson.career.a_gitignored_path_is_invisible_to_your_sweep`.

**4. I changed the expansion when only the acronym was in scope, and reverted.**
"Project Development Life Cycle" came from the request; the repo had a considered
"Programming", load-bearing in `PDLC_STUDENT_WORKING_MODEL_LANE_V1.md:27`, which
teaches PDLC-at-the-desk against SDLC-at-the-org. Reverted in `03282baaa`. The
merge widened PDLC's SCOPE; its NAME never changed. **Commit subjects on
`c0d3069c5` and `018bd0c9f` still say "Project" and are wrong on that point.**

## Still open -- for the next session

- **Five tracked files hold uncommitted PDLC edits** behind other sessions' work:
  `PROMOTION_PROCESS.md`, `AI_SYSTEMS_CROSSWALK_V1.md`,
  `AI_SYSTEMS_INTEGRATION_SDLC_CHARTER_V1.md`, and two session closeouts. A grep
  for `PLDC` on a fresh clone is therefore not zero, by design.
- **`portal_truth_audit_latest.{md,json}` unregenerated.**
  `labtalk/portal/labtalk_portal.py` imports tkinter at module scope, so headless
  `--audit-write` cannot run under `.venv312`, whose vcpkg base has no `_tkinter`.
  Pre-existing defect, unrelated to this merge, not fixed because the file is not
  this session's to change. Two-line fix: move the tkinter imports into the GUI path.
- **`gptbase_bundle_v1/` is hand-corrected and gitignored.** Provenance markers
  show it is assembled from site and repo sources; text now matches upstream
  byte-for-byte, so regeneration is a no-op -- but regeneration is what it wants.
- **23 files under `docs/manuals/developer/manualgen/backups/**` still contain
  PLDC and must stay.** Dated escrow snapshots. An earlier report said ten;
  measure before acting.
- **The lesson is filed as a lesson, not a gate.** AIF-082 measured unenforced
  obligations at 33% against 83-94% for gated ones, so this is likely the weaker
  instrument. Turning it into a `prepush_gate.py` check is a change to another
  session's tool and was left undecided.
- **`RE:` reply owed to AIF-092** on the pseudo-chat board.

## Provenance pointers

- Doctrine: `docs/maintenance/SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`
- Rulings R1/R8: `docs/maintenance/X64BASE_AGENT_SKILL_PDLC_LANE_V1.md`
- Expansion defence: `docs/maintenance/PDLC_STUDENT_WORKING_MODEL_LANE_V1.md`
- Lesson: `labtalk/lessons/career/a_gitignored_path_is_invisible_to_your_sweep_v0.md`
- Handoff: `docs/agents/HANDOFF_PDLC_MERGE_TO_PAUSED_SESSIONS_2026-08-07.md`
- Verification post: `docs/ai-friendly/PSEUDO_CHAT_BOARD.md`
- Publication rules: `docs/reports/REPORTS_PUBLICATION_NOTE_V1.md`
- Commits: `c0d3069c5`, `018bd0c9f`, `7ad5adc32`, `f7c514fe5`, `03282baaa`;
  website `906891990`
