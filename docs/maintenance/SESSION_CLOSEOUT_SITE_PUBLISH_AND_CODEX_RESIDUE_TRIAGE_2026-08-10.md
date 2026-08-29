---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260810-007
  recorded_at_utc: 2026-08-10T20:15:00Z
  agent:
    provider: Anthropic
    product: Claude Cowork
    model: Claude Fable 5
    member: member.ai.claude.cowork
    access_mode: local_write
  attribution:
    authored_by: member.ai.claude.cowork
    planned_by: member.derald
    owner: member.derald
    committer: member.derald
  session:
    id: COWORK-20260810-PUBLISH-TRIAGE-001
    chat_reference: not_exposed
    run_id: AIPR-20260810-007
    chat_handle: ""
    handle_binding: NOT_RESOLVABLE
    continues_run: AIPR-20260810-006
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: ff5f50058
    head_commit: cf5caa7bb
  authorization:
    requested_by: maintainer
    scope: >
      ENVELOPE COMPLETED 2026-08-29 during AIF-078 lane work. The block was
      present but had never satisfied the contract in any commit: four required
      fields were absent (authorization.requested_by, authorization.scope,
      report.path, report.kind) and two present values were not valid. The audit
      read green only while an uncommitted working-tree copy supplied the
      difference, and a `git reset --hard` on 2026-08-29 removed that copy.
      TWO CORRECTIONS, both recorded rather than silently applied.
      (1) access_mode was `sandbox_read_host_handoff`, which is not in the
      allowed set; it occurs exactly ONCE in 135 closeouts while 53 other Claude
      Cowork closeouts use `local_write`, so it is a one-off improvisation
      rather than a pattern the registry is missing, and it is corrected to the
      house convention instead of the vocabulary being widened for a singleton.
      (2) project.id was `project.x64base.dottalkpp`, which is not registered;
      `project.x64base.runtime` is the only registered id whose root matches the
      `D:/code/ccode` this envelope already declares, so the id is determined by
      the document rather than chosen. Everything else is untouched.
      Nothing about the session's authorization was witnessed by the
      reconstructing agent, so requested_by carries the house's generic
      `maintainer` rather than a quoted instruction. Correct it if you were
      there.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_SITE_PUBLISH_AND_CODEX_RESIDUE_TRIAGE_2026-08-10.md
    kind: session_closeout
---

# Session closeout: site publish ownership + Codex residue triage (2026-08-10)

Owner: member.derald. Steward: member.ai.claude.cowork. Sandbox session;
all mutating git and the publish were executed by the owner on the host and
adjudicated here from transcripts (golden rule: verified, not assumed).

## What shipped

1. **ccode cf5caa7bb** (development, pushed): AIF-101 STANDING rule + M4
   factor-event log (Codex 24h run -> AIF-103..106; credit exhaustion until
   2026-08-16 as first M5 natural experiment; 2025-08-02 third clock per
   AIF-106). Full gate chain PASS.
2. **Site publish**: codex/lean-sites-publish pushed (ae143719d..f12001464),
   gh-pages 8db028d16 published from source f12001464. Gates PASS
   (public-content, 18 diagrams). Pagefind reindexed: 146 pages, 7802 words.
3. **Live verification** (CDN fetches, version stamp v=f12001464ed8 confirmed
   on every page): /schemas (full catalog + 3 provenance'd SVGs resolving),
   /about/ai-assisted-history (AIF-106 evidence record intact including
   evidence-boundary and limitations sections), /lms-proposal (preserved
   Copilot deck, curation framing intact). LMS nav entry live site-wide.

## Golden-rule ledger (verify before you assert)

- **Caught, then root-caused: commit stowaway.** cf5caa7bb reports 3 files
  changed; only 2 were added in the commit command. First adjudication
  ("pre-staged by Codex tooling") was WRONG -- measurement of the hook chain
  shows the managed pre-commit hook's tier0-refresh block regenerates
  `labtalk/ai_portal/TIER0_STATE.md` and silently `git add`s it AT COMMIT
  TIME (generated_utc 18:58:22Z = the commit itself). The ride-along is BY
  DESIGN (keeps Tier 0 stamped at HEAD); the silence was the defect. Fixed
  this session: the hook template now announces the staged refresh
  (`tools/staging/refresh-tier0.ps1`), and the prepush gate lists the staged
  set by name for sets of 15 paths or fewer (`tools/staging/prepush_gate.py`,
  STAGED_LIST_THRESHOLD), so a genuine stowaway is visible while it can still
  be unstaged. Both changes advisory-only per AIF-100 M3 (advisory-first);
  recorded in `GATE_GOVERNANCE_LANE_V1.md`. Hooks are not version-controlled:
  re-run `refresh-tier0.ps1 -InstallHook` per clone to deploy the announcing
  block.
- **Corrected: tree-state claim.** Earlier reorientation reported the ccode
  residue as only the two never-committed Claude files. Measurement now shows
  63 modified tracked files + 1 deletion (triage below). The earlier check
  was too shallow; this one hashed content.
- **Method note for sandbox sessions:** the mounted-git status view shows
  CRLF-conversion warnings that can mimic or mask modifications. The decisive
  test used here: compare `git cat-file blob :FILE` vs worktree with CR
  stripped from both (`tr -d '\r' | sha256sum`). All sampled diffs proved
  REAL, not line-ending phantoms.

## Codex residue triage (63 modified + 1 deleted, all UNCOMMITTED)

Coherent, additive, consistent with AIF-104/105/106; interrupted by credit
exhaustion before final commit slices. **Disposition: PRESERVE for Codex's
return (2026-08-16); do not sweep into unrelated commits.** Authorship
belongs to member.ai.codex.local. Until it lands, every commit on this clone
should check `git status --short` after staging (stowaway risk demonstrated
above; scoped adds only, never `git add -A` -- standing rule AIF-050).

- **Group A -- deliberate doc/doctrine edits (commit-worthy, Codex slices):**
  PROMOTION_CHECKLIST.md + PROMOTION_PROCESS.md (promotion doctrine rewrite,
  em-dash -> `--` normalization); docs/ai-friendly/{DASHBOARD, WORKFLOW,
  ENTITY_LIFECYCLE(+139), HISTORICAL_DATABASE_MIGRATION}; docs/contracts/
  {CONTRACT_REGISTRY, TRESPASS_AND_DELEGATED_AUTHORIZATION}; AI_SYSTEMS
  crosswalk + charter; additive appendices to three prior session
  closeouts/records; flush cookbook + DOCFLUSH continuation; labtalk READMEs.
- **Group B -- code (commit-worthy, Codex slices):** src/edu/edu_erp.cpp
  (+105/-12, AIF-105 ERP relations); src/cli/cmd_order.cpp (layer annotation
  command -> helper); uniform +9-line selfdoc/contract header sweep across 17
  tests/*.cpp|hpp + tools/app_paxon.hpp; labtalk/portal/tests/
  test_runtime_paths.py (+34). Deletion: root shell_api.cpp (hygiene; was a
  stray root-level file from f36429d6a era).
- **Group C -- portal/registry state (commit as state refresh):**
  labtalk/registries/portal.yaml (+104: AIF-105 Cascade ERP workspace),
  ai_runs.yaml (+198: run records 103..106), ai_portal_tasks.yaml,
  projects.yaml; portal_truth_audit_latest.{json,md} (regenerated).
- **Group D -- generated reports (regenerate-or-commit):** docs/reports/*.html
  (AI_PORTAL_REPORT +433), manualgen mdo_226 CSV.
- **Group E -- runtime data side effects (default: do NOT commit unless
  deliberate fixture updates):** dottalkpp/data/help/*.dbf|.dbt (HELP store
  touched by runs), indexes/x32/STUDENTS.cnx, scripts/metadata/
  SYSFUNC_IMPORT_v1.csv.

The x64base-site tree is clean (next-env.d.ts generated noise only).

## Open items carried forward

AIF-098 host build proof (runsheet: AIF098_BUILD_HANDOFF_V1.md). AIF-100 M0
gate census. Mirror lane TICKET_CDX_ON_V32 (AIF unclaimed). Main-pointer
promotion ruling (AI_PORTAL_MAIN_POINTER_DRAFT_V1.md). AIF-101: owner review
of findings + white paper; M5 predictive model (first natural experiment in
progress: Codex offline to 08-16). Tier 1 seed at 99% of byte budget (8148 of
8192) -- needs a trim pass before anything else lands there. Repo
public-vs-private question still unpinned.
