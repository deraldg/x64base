---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260723-002
  recorded_at_utc: 2026-07-23T20:55:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-4-8
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: claude-cowork:not_exposed
  project:
    id: project.ai_friendly
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 10fa7e4a59b5e1ad93067431bad0bb33e981c205
  authorization:
    requested_by: maintainer
    scope: >
      Register Arctic Fox Batch (local Ollama runtime) as app.labtalk.afb in
      labtalk/registries/apps.yaml, at direct maintainer request ("add ollama to
      the labtalk portal application").
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_AFB_OLLAMA_APP_REGISTRATION_2026-07-23.md
    kind: session_closeout
---

# Session Closeout — Register Arctic Fox Batch (Ollama) as a LabTalk app

## What changed

- **`labtalk/registries/apps.yaml`** — appended one app entry:
  - `id: app.labtalk.afb`
  - `name: Arctic Fox Batch — Local Ollama AI Lab`
  - `kind: local_ai_lab`  ·  `status: alpha_experimental`
  - `languages: [bash, powershell, markdown]`  ·  `root: D:/code`
  - `concepts: [concept.ai_friendly.visibility, concept.evidence.review, concept.contract.usage]` (all already referenced by existing apps)

No other file was modified. No source, HELP, metadata, catalog, proof, or runtime data changed.

## Why

Maintainer directed adding Ollama (the AFB local runtime) to the LabTalk portal's application registry. This closeout accompanies the registry mutation as required by `AI_REPORT_AUDIT_CONTRACT_V1` ("an AI that mutates an AI Portal-owned artifact must create an audited closeout in the same changeset").

## Honesty / status

- **Egress isolation** of the AFB runtime is `runtime-evidenced` (2026-07-23; see `AFB_ENVIRONMENT_20260723.md` in the accompanying change package). Ceiling: *"verified revocable egress isolation,"* not an air-gap.
- **App maturity** is registered as `alpha_experimental` — the lab integration is new even though the isolation property is proven. Status must be earned, not assumed.
- `root: D:/code` reflects where the AFB tooling currently lives (`verify_egress.sh`, `pull-with-window.sh`); the runtime executes under WSL (`/mnt/c/Users/deral/code`). AFB tooling is host-local and outside the `ccode` source tree — noted for accuracy.

## Open / recommended

1. Run the registry/portal validators before relying on this entry:
   - `python .\labtalk\ai_portal\audit_trail.py` (validates this closeout's envelope, report-ID uniqueness, project-root/path agreement).
   - LabTalk Portal truth audit (confirms `kind: local_ai_lab` and the concept refs are acceptable; `local_ai_lab` is a **new kind** — add it to any kind-vocabulary allowlist if one exists).
2. Confirm `app.labtalk.afb` id is unique across registries.
3. If AFB should later have a home inside `ccode`, move the tooling there and update `root`.

## Provenance

Claude Cowork session, 2026-07-23. Session id not exposed by host (`not_exposed`). No transcript, credential, or account data recorded.
