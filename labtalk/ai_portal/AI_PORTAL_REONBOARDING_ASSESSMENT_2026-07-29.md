# AI Portal Re-Onboarding Assessment

Date: 2026-07-29

Status: Reviewed observation

Scope: Cold-start re-orientation of Codex through the repository-local AI
Portal after a period of work conducted with another AI development partner.

Evidence posture:

- Source-defined statements were read from current repository documents.
- Registry observations were read from current LabTalk YAML registries.
- Runtime observations were produced by read-only portal and process checks.
- Time-sensitive service observations apply only to the date of this report.
- This assessment does not replace source, runtime proof, contracts, registries,
  current-target records, or reviewed closeouts as project authority.

## Executive Finding

The AI Portal passed the re-onboarding test.

Starting without relying on old chat context, Codex could recover the repository
roles, authority chain, active development lanes, publication boundaries,
runtime services, proof posture, and unresolved synchronization issues. The
Portal is operationally useful as a development re-entry system.

Its principal weakness is synchronization. The authoritative pieces are strong,
but the declared target, current-run pointers, task feed, and rendered reports
do not all refresh together. A new AI can recover the project safely, but must
still reconcile several dated projections before identifying the freshest
active work.

## What Was Recovered

### Repository and publication roles

- `D:\code\ccode`, branch `development`, is the sole development and authoring
  workspace.
- `C:\x64base`, branch `main`, is sterilized publication staging.
- GitHub `main` is a reviewed public snapshot, not the development authority.
- `D:\dev\x64base-site` is the x64base.com website source workspace.
- Development must never be pushed or merged directly into `main`.

### Authority chain

The Portal correctly directed the session through:

1. `AI_README.md`
2. `AI_PORTAL.md`
3. the newest session closeout
4. the declared current target
5. authority and repository-role contracts
6. registries and runtime evidence
7. proof and publication boundaries

This ordering prevented a stale handoff or website projection from overriding
current source and runtime truth.

### Current work recovered

The declared target in `docs/agents/CURRENT_TARGET.md` was AIF-072, Phase 7,
Manual Web-Ascent, with a claimed/not-started posture.

The freshest implementation lane was AIF-074 SQLsel:

- Run: `AIPR-20260729-001`
- Closeout:
  `docs/maintenance/SESSION_CLOSEOUT_SQLSEL_P0_P1_2026-07-29.md`
- Observed progress: supported SQLsel work including `ORDER BY`, `COUNT(*)`,
  SQLite oracle checks, and an SQL conformance map.

This exposed a priority ambiguity rather than concealing it: the declared target
and freshest implementation lane do not currently name the same next action.

## Live Read-Only Checks

### Portal audit

Command:

```powershell
& '.venv\Scripts\python.exe' labtalk\portal\labtalk_portal.py --audit
```

Observed result:

```text
sections=14 items=244 runnable=32 proof_like=87 missing_paths=10 duplicate_ids=0 ai_report_findings=0
```

Interpretation:

- The portal graph loaded successfully.
- Registry identities were unique.
- The portal exposed runnable and proof-like items.
- Ten registered paths did not resolve and require review.

### AI report audit

Command:

```powershell
& '.venv\Scripts\python.exe' labtalk\ai_portal\audit_trail.py
```

Observed result:

```text
enforced=70 valid=70 grandfathered=9 findings=0 intake=2 intake_findings=3
```

Interpretation:

- All 70 enforced records validated.
- Nine records remained explicitly grandfathered.
- No enforced findings were reported.
- Three intake findings were advisory and should not be represented as enforced
  failures.

### Local services

- `dottalk_bbsd` was running as process 4416 and listening on
  `127.0.0.1:8765`.
- Ollama was listening on `127.0.0.1:11434`.
- No Codex BBS token was available. The session did not mint, rotate, or infer
  credentials, so `board.worklog` was not read.
- The external Claude status page reported elevated model errors on the date of
  the assessment, consistent with the reported access problem. This is
  time-sensitive context, not repository proof.

## Portal Strengths

### One front door

`AI_README.md` clearly identifies itself as the canonical start. Older and
deeper documents remain available without becoming competing startup queues.

### Explicit authority boundaries

The Portal distinguishes:

- development source
- runtime proof
- HELP and metadata
- SelfDoc preservation
- MDO review and assembly
- publication staging
- public websites and repositories

This sharply reduces the risk that an AI will treat generated prose or a public
snapshot as current development authority.

### Evidence-aware language

The documentation separates supported, planned, observed, unverified, and
published states. That is essential for an active beta system whose
documentation and runtime evolve together.

### Useful loss-of-memory recovery

The Portal provides enough local context to resume work after model outages,
session loss, or collaboration with another AI. This validates its BIOS
metaphor: it prepares an AI development partner for the environment without
granting that AI ownership or final authority.

### Safe handling of credentials

The missing BBS token remained a declared access boundary. The re-onboarding
process did not manufacture credentials or reinterpret local service
availability as authorization.

## Drift and Synchronization Findings

### Current-target ambiguity

`CURRENT_TARGET.md` identifies AIF-072, while the newest active implementation
closeout identifies AIF-074 and a later next entry. A cold-start AI must
reconcile these records manually.

### Current-run projection lag

`labtalk/registries/ai_runs.yaml` maps AIF-074 to `AIPR-20260729-001`, but the
project-level runtime pointer still references the older
`AIPR-20260727-001`.

### Task-feed lag

`labtalk/registries/ai_portal_tasks.yaml` was dated 2026-07-28 and did not
project AIF-074.

### Rendered-report lag

- `docs/reports/AI_PORTAL_REPORT.html` reflected a July 25 state.
- `labtalk/reports/portal/portal_truth_audit_latest.*` reflected a July 26
  state.

These artifacts are useful historical evidence, but their names can imply
greater freshness than their content supports.

### Missing registered paths

The live portal audit reported these unresolved locations:

1. `project.db_converter` root:
   `D:\code\ccode\Side Projects\DB_Converter`
2. `project.db_converter` documentation README
3. `project.db_converter` launcher
4. `project.sqlite_gui` root: `D:\code\ccode\sqlite-gui`
5. `project.x64base.identity` documentation:
   `D:\code\ccode\docs\## AI Portal re-examination.txt`
6. `lesson.student.properties_of_valid_data`
7. `lesson.career.entities_and_the_bridge`
8. `lesson.student.cursor_versus_set`
9. `lesson.career.a_wrong_answer_that_looks_right`
10. `lesson.career.the_tree_already_has_it`

These should be classified individually as moved, renamed, intentionally
external, planned, or erroneous. They should not be repaired by guessing.

## Recommended Next Gates

1. Define one reviewed operation that advances the declared target, lane run,
   project-level current-run pointer, and portal task projection together.
2. Add generated-at timestamps and source-run identities to every
   `latest`-named report.
3. Classify all ten missing paths before changing registry entries.
4. Decide whether AIF-072 remains the controlling target or whether AIF-074
   should be promoted into `CURRENT_TARGET.md`.
5. Preserve the successful cold-start procedure as a repeatable portal
   acceptance test.
6. Add an explicit degraded-access result for services that are live but cannot
   be queried because credentials are unavailable.

## Acceptance Verdict

The Portal is effective enough to re-orient an AI development partner safely
without old chat history. It did not remove the need for engineering judgment,
and it correctly did not claim authority over development.

The next maturity step is not more onboarding prose. It is tighter recursive
synchronization among the authoritative target, active run, registries,
generated reports, and closeout evidence.

## Mutation Record

The assessment itself was produced from read-only inspection. No source,
runtime, registry, branch, commit, staging tree, or public website was changed
during the assessment.

This file and its registry/index references were added afterward at the
maintainer's request so the result would become durable AI Portal
documentation.
