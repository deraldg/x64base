---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260910-001
  recorded_at_utc: 2026-09-10T04:05:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: 01XMzP8acDeeY3kCxDyQ7FHV
    chat_reference: claude-code-session:01XMzP8acDeeY3kCxDyQ7FHV
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 85401cbad
  authorization:
    requested_by: maintainer
    scope: >-
      Engine work on SQLsel transactions and the SQLSEL surface; site prose and
      artifact correction; publication of the site on explicit instruction;
      registry promotion of SQLsel to a project on explicit ruling.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_SQLSEL_RETIREMENT_AND_SITE_2026-09-10.md
    kind: session_closeout
---

# Session Closeout -- SQLsel retirement, commit verdict, and the site (AIF-074)

Also carries **AIF-159** (sqlsel-transactions), which ran inside this surface
rather than beside it.

Date: 2026-09-10.
Owning lifecycle: DotTalk++ SDLC for P0-P5 work; PDLC for the publication half.
SDLC lane: publication.
Truth state: mixed -- source-defined where stated as such, runtime-proven where named.
Proof state: transcript + build + git-verified.

**`baseline_commit` is the abbreviated form.** This session had no shell on the
device (`device_bash` reported no mounts for its entire duration), so every
command was run by the maintainer and pasted back. The abbreviation is what was
observed; it was not expanded to 40 hex rather than invent digits.

## One-line summary

Two lanes closed -- COMMIT gained a verdict SQLsel can read, and SQLSEL's legacy
predicate form was retired so the verb has one answer to which rows are in scope
-- then the published site was corrected to stop describing two retired surfaces
and republished as release 144.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Commit verdict | `include/cli/table_buffer.hpp`, `src/cli/cmd_commit.cpp`, `src/cli/cmd_rollback.cpp`, `src/cli/sqlsel_statement.cpp` | `Verdict`/`Outcome` moved out of an anonymous namespace so the answer can leave the translation unit; sibling entry points because `SYSCMD.dbf` dispatches by function pointer |
| Native-verb guards | `src/cli/cmd_commit.cpp`, `src/cli/cmd_rollback.cpp`, `dottalkpp/data/scripts/trigger_veto_arm_work.dts`, `src/cli/cmd_regression.cpp` | Refuse a native COMMIT/ROLLBACK inside a live SQL transaction; `TRG_W3`/`TRG_W4` added so the guards fire in a spec |
| SQLSEL retirement | `src/cli/cmd_sql_select.cpp` | 618 lines -> 225; private `DelMode`, raw walk, tokenizer and legacy body deleted |
| Lane docs | `docs/maintenance/SQLSEL_PDLC_LANE_V1.md` | `ONE OF TWO COPIES` closed; section 5 closed to zero open rows; plan-of-record citation corrected |
| Registry | `labtalk/registries/projects.yaml` | `project.x64base.sqlsel` promoted per AIF-040 |
| Gate wording | `tools/staging/check_site_artifacts.py` | Advisory narrowed to the scope it reads, twice |
| Proof | `labtalk/proofs/runs/20260910_aif074_sqlsel_legacy_predicate_retired.txt` | Hand transcript |

Commits, oldest first: `57df59c49`, `9079b6dda`, `9ed32fee6`, `3c95aac58`,
`a76cbb37b`, `1a96dac9b`, `052a9e980`, `d876f3358`, `dbfc49db3`, `85401cbad`.

## Verified (proof performed this session)

- `REGRESSION TRIGGERVETO NORMAL` and `SELFTEST` green with `TRG_W3` and
  `TRG_W4` present, each requiring the refusal text verbatim. **A planned hand
  proof of the COMMIT guard failed first** -- `SQLSEL BEGIN` refuses outside SQL
  mode -- and the guard was held back rather than committed on an argument.
- `SQLSEL LNAME = "SMITH"` printed the five-line retirement message verbatim at
  an interactive prompt, build stamp `Sep 09 2026 19:40:48` (`a76cbb37 dirty`).
  No spec in the tree can reach that message: every SQLSEL line in the tree
  carries a FROM, is a comment, or is `SQLSEL HELP`. Transcript committed.
- `SQLSEL_INNER_JOIN`: PASS -- 4/4 row sets equal SQLite, cursors 2/2, refusals
  3/3, access paths 4/4 (CDX seek 2, scan 2). NONDESTRUCTIVE green.
- `git ls-files "*IMPLEMENTATION_PLAN_SQLSEL*"` returned empty: the charter's
  Plan of Record has never been tracked in this repository.
- Every commit passed `prepush-gate`. Nothing here rests on a zero exit code
  alone; each claim above names the output that carried it.

## AI-facing docs updated (AIF-006 gate)

`AI_INTERACTION_INTAKE_QUEUE_V1.md` carries the AIF-159 row and its addenda.
`labtalk/registries/projects.yaml` gained `project.x64base.sqlsel`.
`docs/agents/CURRENT_TARGET.md` NOT modified -- no lane became the named target.

## Published

- Site source: `ab4cf2211`, `a184a12a3`, `07db783aa` on
  `codex/lean-sites-publish`, pushed to `origin`.
- `gh-pages`: `c29ded440 -> 4761fbd04`. **Release 144, verified live** at
  `https://x64base.com/artifacts/site-release.json` after three propagation
  polls reading 143.
- `C:\x64base` staging: **NOT promoted.** Owner direction: hold until SQLsel
  closes so the promotion carries one coherent slice. The last promotion is
  `9470a50d9` and predates every commit above.

## Handoff left (AIF-082 gate)

**Owed and NOT satisfied by this closeout, stated rather than papered over.**
The session's durable how-to-work-here output is four findings about
instruments that report green on questions they structurally cannot ask. Three
are written -- see Provenance -- but they live in the Claude project and in an
untracked `claude/` directory, not in `docs/agents/`, and no `docs/agents/`
handoff was written. That is an open item, not a satisfied gate.

## Still open -- for the next session

1. **P6 is the whole SQLsel remainder.** (a) HELP DBF regeneration is BLOCKED --
   the entire `dottalkpp/data/help/*.dbf` and `*.dbt` set carries a concurrent
   session's uncommitted work, and refreshing now would fuse two sessions into
   one slice. (b) No LabTalk lessons exist; authoring, sized by owner decision.
   (c) No evidence gallery exists under any name searched; wants a scope ruling
   that may delete the item. (d) Public-site promotion substantially discharged.
2. **`C:\x64base` promotion owed.** 15 commits unpushed per Tier 0; the last
   promotion predates all of today.
3. **Two contract fields changed on the author's judgment**, flagged for owner
   review: `noargs` `scan/report` -> `corrective-error`, `requires_open_table`
   `yes except usage` -> `no`, both on SQLSEL.
4. **`index_failed` suppresses only the AFTER trigger**, so a record is counted
   as applied with its index entry unwritten. First move is to read AIF-157's
   answer on whether that staleness is durable -- NOT to write a probe.
5. **The capability sweep reads pages in one polarity.** A retired surface has
   no entry in an authority listing what ships. Fix is a retired-entry polarity
   in `x64base-site/scripts/engine-capabilities-v1.json`; site-tree change.
6. **`prepush_gate.py` restates the site-artifact advisory in its own words.**
   After today the two copies differ. Benign now; a second copy either way.
7. **The Plan of Record was never tracked.** Section 4 of the charter is the
   plan of record in fact. Locating or re-deriving the original is open.
8. **`PORTAL_SEARCH_MAP_V1.md:58` cites `claude/FINDING_DOTSCRIPT_SCOPING_IS_BUILT_NOT_WIRED.md`**,
   which has never existed in the tree. `cited-paths` did not catch it because
   that document has not been in a change set since.

## Provenance pointers

- `docs/maintenance/SQLSEL_PDLC_LANE_V1.md` -- the charter; sections 4, 5, 8.
- `labtalk/proofs/runs/20260910_aif074_sqlsel_legacy_predicate_retired.txt`
- `labtalk/proofs/runs/20260909_aif159_*` -- the four trigger-veto captures.
- `labtalk/ai_portal/AI_REPORT_AUDIT_CONTRACT_V1.md` -- this envelope's contract.
- Project docs (Claude project, mirrored untracked to `claude/`):
  `FINDING_ONE_VERB_TWO_ANSWERS_TO_WHICH_ROWS_ARE_IN_SCOPE.md`,
  `FINDING_THE_PROSE_SWEEP_READS_PAGES_IN_ONE_POLARITY_ONLY.md`,
  `SESSION_LEDGER_20260910_TWO_LANES_AND_THE_SITE.md`.
