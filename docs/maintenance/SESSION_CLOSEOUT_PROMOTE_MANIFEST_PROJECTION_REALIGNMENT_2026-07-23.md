---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260723-001
  recorded_at_utc: 2026-07-23T23:11:16Z
  agent:
    provider: Anthropic
    product: Cowork (Claude)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: promotion manifest projection realignment
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 10fa7e4a5
  authorization:
    requested_by: maintainer
    scope: rename integration branch; restructure PROMOTE.manifest publish scope; add drift gate + runbook
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_PROMOTE_MANIFEST_PROJECTION_REALIGNMENT_2026-07-23.md
    kind: session_closeout
---

# Session Closeout — PROMOTE.manifest projection realignment

Date: 2026-07-23.
Owning lifecycle: maintenance.
SDLC lane: promotion.
Truth state: mixed (source-defined seeds + observed git/tracked state).
Proof state: report (static analysis; not build-proven, gate not yet executed by maintainer).

## One-line summary

Reworked the dev→staging→main promotion controls, then — after re-onboarding
through the AI Portal — caught and corrected a design error where engine source
had been added to `PROMOTE.manifest`, realigning the manifest to
`PROMOTION_MODEL_SEED_V1.md` (manifest = data/doc projection only; source is
git-managed).

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Git branch | `homegrown-cnx-20251112-branch` → `development` | Local + remote rename; old remote deleted; maintainer-authorized. Already reflected in `AI_README.md`. |
| Promotion allow-list | `PROMOTE.manifest` | Restructured, then realigned. Now a projection-only allow-list (80 globs). |
| Projection gate | `tools/staging/audit-drift.ps1` | New. Judges git-tracked files; skips git-managed source; flags projection drift / off-projection / junk / non-publish lanes. |
| Process docs | `PROMOTION_PROCESS.md`, `PROMOTION_CHECKLIST.md` | New. Authority chain + first-promotion runbook. |

Commits on `development`: `965b39650`, `8cb2afc37`, `2a2ae2f83`,
`10fa7e4a5` (realignment). All pushed to `origin/development`.

## Correction recorded (honesty)

An intermediate version of `PROMOTE.manifest` (commit `2a2ae2f83`) added
`src/**`, `include/**`, `bindings/**`, `cmake/**`, `CMakeLists.txt`,
`CMakePresets.json`, and `vcpkg*.json` to the allow-list, and the audit tool
treated all off-manifest tracked files (including source) as drift. This
contradicts `labtalk/ai_portal/PROMOTION_MODEL_SEED_V1.md` — "The manifest does
NOT carry engine source"; source reaches `main` via git (branch → cold-clone
build → merge). Re-onboarding through `AI_README.md` → the flow-authority seed →
the promotion-model seed surfaced this. Commit `10fa7e4a5` removes those globs
and rewrites the gate to skip git-managed source (blind spot by design).

## Verified (proof performed this session)

Static analysis only (no build, no maintainer gate run):

- Projection-audit simulation against `git ls-files` of the current `C:\x64base`
  working tree (2,388 tracked): 1,071 git-managed engine/build (skipped), 489
  on-projection, 754 off-projection metalevel, 74 non-publish MDO lanes, 0
  tracked `__pycache__`/`*.pyc`.
- Manifest glob→regex parity between the PowerShell gate and a Python replica
  reproduced known counts before realignment (200/342 on the prior manifest).

NOT done: cold-clone build, `audit-drift.ps1` executed by maintainer,
`rebuild-staging.ps1`, escrow, or any push to `main`. A zero exit code was not
observed because the gate has not been run in-environment.

## AI-facing docs updated (AIF-006 gate)

- This closeout: created.
- `AI_README.md`: already carries the branch rename (not changed this session).
- `docs/agents/CURRENT_TARGET.md`: **update still owed** — it does not yet
  record the promotion-scope rework as an objective/lane. Flagged as open below.

## Published

Dev-only. `development` pushed to `origin/development`. **Not promoted to
`main`.** `main` advanced independently this session with unrelated AI Portal
commits (`4c2b82bbd`…) and already carries the surgical scan-evaluator M0 mirror
commit `7f0d1efa2` (AIF-046, source-of-truth in dev per `CURRENT_TARGET`).
`C:\x64base` and `origin/main` are currently diverged (local M0 commit vs remote
AI Portal commits) — reconciliation owed before any product publish.

## Still open — for the next session

1. **Scope decision (maintainer):** the model-compliant projection historically
   included docs, portal seeds, and manualgen tools. The current lean product
   scope purges 754 metalevel files from `main`. Confirm the lean cut, or widen
   the projection.
2. **C:\x64base divergence:** rebase the local `7f0d1efa2` onto `origin/main`
   (disjoint files) or reconcile per `DEVELOPMENT_FLOW_AUTHORITY_SEEDS` Seed 3.
3. **Publish path (unrun):** escrow → `rebuild-staging.ps1` → `audit-drift.ps1`
   PASS → `prepush_gate.py` exit 0 → commit/push `main`.
4. **CURRENT_TARGET update owed** (this closeout's AIF-006 residual).
5. Retire/rewrite `WORKFLOW_X64BASE.md` (superseded; references removed
   `D:\code\ccode\x64base` tree).
6. Reconcile `BUILDING.md` canonical location (root vs `docs/getting-started/`).

## Provenance pointers

- `labtalk/ai_portal/PROMOTION_MODEL_SEED_V1.md` (governing authority)
- `labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md`
- `AI_README.md`, `docs/agents/CURRENT_TARGET.md`
- `PROMOTE.manifest`, `tools/staging/audit-drift.ps1`
- `PROMOTION_PROCESS.md`, `PROMOTION_CHECKLIST.md`
