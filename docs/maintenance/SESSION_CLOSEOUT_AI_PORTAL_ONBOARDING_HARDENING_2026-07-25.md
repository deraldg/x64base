---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260725-002
  recorded_at_utc: 2026-07-25T22:10:00Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.ai_friendly
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: dfa8c1366afd171d7f7d4101c6561c0ba5e27990
    head_commit: dfa8c1366afd171d7f7d4101c6561c0ba5e27990
  authorization:
    requested_by: maintainer
    scope: >
      Side mission from the AI-BBS lane: harden AI onboarding through the AI Portal so a partner is
      handed the engineering standards and definition-of-done up front instead of reverse-engineering
      them from source.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_ONBOARDING_HARDENING_2026-07-25.md
    kind: session_closeout
---

# Session Closeout -- AI Portal Onboarding Hardening (2026-07-25)

Owning lifecycle: DotTalk++ SDLC + AI Friendly / AI Portal hardening lane.
Lane: AIF-056 (continues the AI-BBS lane run AIPR-20260725-001).
Operating mode: `development` (docs/seeds; uncommitted at time of writing).
Change class: additive process/onboarding hardening -- one new seed + reading-path wiring; no
authority weakened, no behavior changed.
Truth state: **source-defined.** The seed and its wiring exist; behavioral verification is a future
cold-session observation (see Next).
Promotion state: dev-only, not committed, mirror `C:\x64base` and public untouched.

## Origin -- the observed failure

While building the AI-BBS lane (AIF-052..055), the onboarded AI discovered house conventions
reactively: it grepped source to learn the `@dottalk.usage` contract format, copied an existing
`.dts` to learn the regression pattern, and closed the work with a regression only when the
maintainer prompted it. The maintainer named this correctly: the AI Portal is meant to prevent
exactly that, and it did not. The portal's seeds covered *process* (SDLC entry, scope, source-mutation
gate, change-package format) but had no seed for the concrete *engineering standards + definition of
done*.

## What was done

- **New seed:** `labtalk/ai_portal/AI_ENGINEERING_STANDARDS_SEED_V1.md` -- front-loads:
  usage contracts (`@dottalk.usage`, the `experimental -> supported` publish trigger); the regression
  doctrine (self-asserting, self-bootstrapping/sandboxed, registered in `kRegressionSpecs`, socket
  smoke for server behavior); the lane close-out checklist (usage flip, `proofs.yaml`, `ai_runs.yaml`,
  intake row, closeout, lane doc, regression, runbook); house conventions (`&&` comments, ASCII / no
  em-dash, `datarun`, loopback + token trust boundary, agents never get `source.mutate`/egress, cross
  -process FLOCK); evidence classes; and a one-line done-gate.
- **Wired onto the mandatory path:** `AI_README.md` canonical ordered table (new step 6, before the
  source-mutation gate), `AI_PORTAL.md` (published mirror), `ROOT_AI_PORTAL_ENTRY_V1.md` mandatory
  start, and the `SDLC_FAST_START_SEED_V1.md` closeout rule. Logged in `AI_PORTAL_HARDENING_LANE_V1.md`.

## Files (dev, uncommitted)

- New: `labtalk/ai_portal/AI_ENGINEERING_STANDARDS_SEED_V1.md`; this closeout.
- Edits: `AI_README.md`, `AI_PORTAL.md`, `labtalk/ai_portal/ROOT_AI_PORTAL_ENTRY_V1.md`,
  `labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md`, `labtalk/ai_portal/AI_PORTAL_HARDENING_LANE_V1.md`.
- Registry: `ai_runs.yaml` (AIF-056 on run AIPR-20260725-001), `proofs.yaml`
  (`proof.ai_portal.engineering_standards_seed`, source_defined), intake queue (AIF-056 row).

## Next -- the real proof

This hardening is `source_defined` by nature; the honest gate is behavioral. Promote
`proof.ai_portal.engineering_standards_seed` to `runtime_observed` only after a **cold AI session**
enters through the front door and applies the standards -- writes a `@dottalk.usage` contract, closes
its lane with a self-asserting regression, and lands the close-out registry rows -- **without being
prompted**. Until then it is a well-placed seed, not a proven one. Commit alongside the AI-BBS lane.
