---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260804-006
  recorded_at_utc: 2026-08-04T04:10:00Z
  agent:
    provider: Anthropic
    product: Cowork (Claude)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: untracked-tree triage after milestone closeout
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: b7d789b4a
  authorization:
    requested_by: maintainer
    scope: charter a REPO_HYGIENE pass over the 2026-08-04 untracked pile (plan only; no bulk mutation)
  report:
    path: docs/maintenance/REPO_HYGIENE_TRIAGE_CHARTER_2026-08-04.md
    kind: lane_charter
---

# REPO_HYGIENE Triage Charter -- 2026-08-04 untracked pile

Status: proposed (claim an AIF before executing any slice below).
Owning lifecycle: maintenance / repo hygiene.
Prior art: `REPO_HYGIENE_PLAN.md`,
`docs/maintenance/REPO_HYGIENE_{CURRENT_FINDINGS,DELETION_CANDIDATES,MOVE_CLOSEOUT,RELOCATION_CHECKLIST_SUMMARY}_2026-06-30.md`,
`docs/maintenance/CCODE_TOPLEVEL_TRIAGE_2026-07-07.md`. This charter is the
2026-08-04 continuation, not a new discipline.

## Problem statement

`git status` on `development` shows several HUNDRED untracked paths spanning
whole subtrees (`dottalkpp/data/**`, `docs/**`, `bindings/**`,
`dottalkpp/tools/help/**`, `dottalkpp/docs/**`). This is NOT a loose-file sweep
and MUST NOT be treated as one. Three facts govern the whole pass:

1. **The `.gitignore` is already a commented, deliberate policy.** It explicitly
   leaves large amounts VISIBLE on purpose:
   - "does NOT ignore dottalkpp/data DBF/index TABLES ... 84 tracked fixtures
     (a track-the-source-tables policy)"
   - "indexes/ left VISIBLE on purpose: mixed 36 tracked / 75 untracked"
   So a visible-but-untracked file is frequently the intended steady state.
   **Zeroing out the untracked list is NOT a goal of this lane.**
2. **The prepush gate blocks binaries and build trees, and warns on data
   fixtures.** A bulk `git add` would hard-fail (there is an ELF binary in the
   pile) and would fight the source-tables policy. NEVER `git add -A`/`git add .`
   (AIF-050): scoped slices only, `git status --short` between add and commit.
3. **`labtalk/` is a nested git repo** (`labtalk/.git` exists). Embedded repos
   are a structural cause of the noise and need an explicit decision, not a sweep.

## Non-goals

- Do NOT try to make `git status` clean.
- Do NOT bulk-add `dottalkpp/**` (data/index/workspace/binary).
- Do NOT adjudicate provenance blindly. Some of this may be another session's
  work in progress (this ambiguity was raised earlier in the tree). Confirm
  ownership before tracking anything under active development by others.

## Buckets and dispositions

### Bucket A -- TRACK NOW (clear deliverables, gate-safe, no binaries/data)

Real, reviewable, and currently unprotected by git:

- `.github/workflows/build-windows.yml` -- CI workflow, untracked. Highest value:
  loss/edit is silent today.
- `BUILDING.md`.
- `docs/manuals/developer/dev/dev-00-evidence-rules.md` .. `dev-19-*.md` -- the
  20-part developer manual (prose .md only; NOT the generated/ or .docx outputs).
- `docs/cases/CASE_*.md` and `docs/cases/runtime_proofs/ENG-*_RUNTIME_PROOF.md`
  and `docs/cases/CASE_FRAMEWORK.md`, `docs/cases/README_CASES_v0.md`.
- `docs/governance/00_*.md` .. `05_*.md`, `docs/governance/anti_drift_best_practices.md`.
- `docs/contracts/DOTTALK_SOURCE_OBJECT_AND_LOCATION_CONTRACT_V1.md`.
- `src/schemas/`, `src/cli/schema_json_v1.schema.json` -- schema source paired
  with `src/tools/schema_inventory_main.cpp` (tracked earlier this session).

Expect the prepush data-fixture WARNING on any `.csv` that rides along; it is a
warn, not a block.

### Bucket B -- LEAVE VISIBLE (track-the-source-tables policy owns these)

Do not touch in this lane; they are adjudicated by the existing `.gitignore`
policy and its per-table decisions:

- `dottalkpp/data/**` DBF (`*.dbf`), indexes (`*.cdx`), workspaces
  (`*.dtschema*`, `*.erz`), and `dottalkpp/data/scripts/**` regression/canary
  `.dts`. Some are already tracked; new ones need the same per-table call, not a
  sweep.

### Bucket C -- GITIGNORE (build/binary artifacts leaking into status)

- `dottalkpp/bin/dottalkpp` -- ELF 64-bit executable. `.gitignore` ignores
  `dottalkpp/bin/dottalkpp.exe` but NOT the extensionless ELF. Add a rule
  (`/dottalkpp/bin/dottalkpp`) or delete the staged copy; never commit it.
- Image/icon blobs dropped in `dottalkpp/bin/` (`*.png`, `*.jpg`, `*.ico`) unless
  a specific one is a needed asset.

### Bucket D -- QUARANTINE / DELETE (AI chat-paste junk)

**Invariant: the ccode sidecar never goes to GitHub.** The sidecar/quarantine
area is a LOCAL-only holding zone. Its files, and the bookkeeping lists
(`quarantine_files.txt`, `sidecar_*.txt`), are never `git add`-ed, never tracked,
never pushed -- they stay untracked-and-visible on disk until deleted. So Bucket D
work is entirely git-free: append to the lists, move via the sidecar script,
delete. No slice in this bucket ever touches the index.

Files whose names are fragments of chat transcripts or shell one-liners (spaces,
sentence-like names, `& $py12 ...`, `httpschatgpt...`, `expectation vs
availability...`, `A task isn't done until the houseke...`, `Before I hand you
commands...`, `I forgot you are a new chat...`). These are not artifacts. Append
them to `quarantine_files.txt` and route through `move_to_sidecar_first_pass.ps1`,
then delete. They exist across root, `docs/`, `docs/maintenance/`, and
`dottalkpp/data/**`.

### Bucket E -- STRUCTURAL DECISIONS (owner only)

1. **`labtalk/` nested repo.** Decide: promote to a real submodule (record the
   gitlink + `.gitmodules`), absorb into this repo (remove `labtalk/.git`, track
   contents here), or leave embedded and documented. Until decided, `labtalk/**`
   entries in `git status` are misleading and should be excluded from any slice.
2. **Root helper scripts vs sidecar.** Many root `.ps1` (`run-*.ps1`,
   `homegrown_*.ps1`, `clean_dottalkpp_staging*.ps1`, `backup_*_drop.ps1`, the
   `*.datarun.*` variants) are one-offs already partly captured in
   `sidecar_oneoff_ps1.txt`. `launch-common.ps1` was the exception (a live
   dependency, tracked this session). Decide which remaining root scripts are
   durable workflow (track) vs one-off (sidecar).
3. **`.docx` doc binaries** (`docs/*.docx`, `dottalkpp/docs/*.docx`). Decide
   whether generated Word docs belong in git or are regenerable outputs.

## Execution order

1. Land Bucket A as scoped slices (see below). Push.
2. Apply Bucket C gitignore rule; delete the ELF.
3. Owner settles Bucket E (nested repo + script/docx policy).
4. Run Bucket D through the existing sidecar/quarantine machinery.
5. Bucket B: no action; re-affirm the source-tables policy in a short note if any
   new table needs a per-table decision.

Gate discipline throughout: scoped `git add` per logical slice, `git status
--short` before each commit, ASCII-only added lines, expect the data-fixture
warning, never `git add -A`. Sandbox agents hand git to the maintainer.

## Bucket A -- ready-to-run slices

```
git add .github/workflows/build-windows.yml BUILDING.md
git commit -m "ci+build: track windows build workflow and BUILDING.md"

git add docs/manuals/developer/dev/dev-00-evidence-rules.md docs/manuals/developer/dev/dev-01-project-identity.md docs/manuals/developer/dev/dev-02-build-and-runtime-layout.md docs/manuals/developer/dev/dev-03-source-tree-map.md docs/manuals/developer/dev/dev-04-architecture-overview.md docs/manuals/developer/dev/dev-05-command-system.md docs/manuals/developer/dev/dev-06-dotscript.md docs/manuals/developer/dev/dev-07-dbarea-and-table-engine.md docs/manuals/developer/dev/dev-08-dbf-x32-x64-formats.md docs/manuals/developer/dev/dev-09-indexing-inx-cnx-cdx-lmdb.md docs/manuals/developer/dev/dev-10-memo-system.md docs/manuals/developer/dev/dev-11-expression-engine.md docs/manuals/developer/dev/dev-12-relations-workspaces-and-tuple-traversal.md docs/manuals/developer/dev/dev-13-browsers-and-tui.md docs/manuals/developer/dev/dev-14-help-metadata-and-cmdhelpchk.md docs/manuals/developer/dev/dev-15-selfdoc-pipeline.md docs/manuals/developer/dev/dev-16-smoke-tests-and-canaries.md docs/manuals/developer/dev/dev-17-contributor-rules.md docs/manuals/developer/dev/dev-18-known-red-paths.md docs/manuals/developer/dev/dev-19-help-meta-crosswalk-and-manual-generation.md
git commit -m "docs(dev-manual): track 20-part developer manual prose"

git add docs/cases/CASE_FRAMEWORK.md docs/cases/README_CASES_v0.md "docs/cases/CASE_ENG_010_INDEX_NAVIGATION_CDX_LMDB.md" docs/cases/CASE_ENG_020_SEEK_VS_SCAN.md docs/cases/CASE_ENG_030_BUFFERING_COMMIT_LIFECYCLE.md docs/cases/CASE_ENG_040_METADATA_DATA_DICTIONARY.md docs/cases/CASE_ENG_050_FILE_ENGINE_SEPARATION.md docs/cases/CASE_HIST_000_DATA_TRAIL_OVERVIEW.md docs/cases/CASE_HIST_010_COBOL_CONNECTED_COMPUTERS.md docs/cases/CASE_HIST_020_JUMPS_73C_ARMY_SYSTEM.md docs/cases/CASE_HIST_030_UNISYS_CODASYL_ALCOA.md docs/cases/CASE_HIST_040_XBASE_MAJOR_PLATFORM.md docs/cases/CASE_HIST_050_EARTHKIDS_CAREPAX.md docs/cases/CASE_HIST_060_TITLESCAN_PAXON_DATABASE_TRANSFERS.md docs/cases/CASE_HIST_070_ERP_SQL_AUTOID_INDUSTRIAL_SCALE.md docs/cases/CASE_HIST_080_HYNIX_SEMICONDUCTOR_PROCESS_DATA.md docs/cases/CASE_HIST_090_DOTTALK_LABTALK_AI_FUTURE.md docs/cases/runtime_proofs/ENG-010_RUNTIME_PROOF.md docs/cases/runtime_proofs/ENG-020_RUNTIME_PROOF.md docs/cases/runtime_proofs/ENG-030_RUNTIME_PROOF.md docs/cases/runtime_proofs/ENG-040_RUNTIME_PROOF.md docs/cases/runtime_proofs/ENG-050_RUNTIME_PROOF.md
git commit -m "docs(cases): track ENG/HIST case studies + runtime proofs"

git add docs/governance/00_about_this_manual.md docs/governance/01_evidence_classes.md docs/governance/02_selfdoc_and_mdo_roles.md docs/governance/03_glossary_policy.md docs/governance/04_reporting_mismatches.md docs/governance/05_publication_readiness.md docs/governance/anti_drift_best_practices.md docs/contracts/DOTTALK_SOURCE_OBJECT_AND_LOCATION_CONTRACT_V1.md
git commit -m "docs(governance+contract): track governance manual and source-object contract"

git add src/cli/schema_json_v1.schema.json src/schemas/
git commit -m "schema: track schema_json_v1 + src/schemas source (pairs with schema_inventory_main)"
```

Note: run each `git add` then `git status --short` to confirm the slice is
exactly what you intend before committing. Confirm none of the Bucket A files are
another session's in-flight work before landing. Exclude anything under
`labtalk/` until Bucket E.1 is decided.

## Delete, do not track

`src/cli/cmd_transaction.cpp` (0 bytes -- accidental touch).
```
git status  # confirm still untracked/empty
Remove-Item src/cli/cmd_transaction.cpp
```
