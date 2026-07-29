# AI Report-Audit Envelope v2 — Spec / Delta (AIF-050 M4)

**Spec id:** `AI_REPORT_AUDIT_V2_SPEC` · **Status:** candidate (dev-only; not promoted) · **Filed:** 2026-07-22
· **Owner:** member.derald · **Steward/author:** member.ai.claude.cowork · **Lane:** AIF-050.
· **Extends:** AIF-020 (`labtalk/ai_portal/AI_REPORT_AUDIT_CONTRACT_V1.md`, `labtalk/registries/ai_report_audit.yaml`).

`ai-report-audit-v2` adds the attribution and return-path fields v1 left as `not_exposed`, so a
closeout resolves to **who did the work**, **in which run**, **reachable how** — separate from who
owns/commits. Additive and versioned: the validator accepts v1 and v2; v1 envelopes stay valid.

> **ENFORCEMENT STATUS (corrected 2026-07-29, AIF-074):** the sentence above is
> intent, not current behavior. The live validator enforces
> `labtalk/registries/ai_report_audit.yaml`, which still pins
> `schema: ai-report-audit-v1` and REJECTS a v2 schema string (runtime-observed:
> prepush gate, 2026-07-29, `expected ai-report-audit-v1`). Until that registry
> adopts the v2 `required_fields` set (the migration step Sec. "Migration +
> validator" names), author closeouts as v1 -- from
> `docs/maintenance/SESSION_CLOSEOUT_TEMPLATE.md` -- and add v2 fields
> additively only.

## Delta from v1

Added / changed (everything else is unchanged from v1):

| field | v1 | v2 |
|---|---|---|
| `agent.member` | — | **new** — identity-catalog member key (`member.ai.claude.cowork`) |
| `authored_by` | — | **new** — the member that did the work (the true author) |
| `planned_by` | — | **new** — the member/plan the work derived from, when different (else `null`) |
| `owner` | (implicit in `authorization.requested_by`) | **new, explicit, once** — `member.derald` |
| `committer` | — | **new** — git reality (`member.derald` in this project) |
| `session.run_id` | — | **new** — stable run handle; keys `ai_runs.yaml` |
| `session.chat_handle` | `chat_reference: not_exposed` | **new** — resumable pointer (or `""`) |
| `session.handle_binding` | — | **new** — `SELF_REPORTED \| MAINTAINER_ATTESTED \| NOT_RESOLVABLE` |
| `session.continues_run` | — | **new** — prior `run_id` this session continues (or `null`) |
| `agent.model` | `not_exposed` | unchanged (`not_exposed`) — the platform still stamps it |

Design rule enforced by the shape: **`owner`/`committer` appear once**; the record foregrounds
`authored_by`/`planned_by`. The owner's name is not repeated as ceremony.

## v2 envelope — worked example (this session's real run)

```yaml
ai_report_audit:
  schema: ai-report-audit-v2
  report_id: AIPR-20260722-007
  recorded_at_utc: 2026-07-22T23:59:00Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    member: member.ai.claude.cowork        # NEW — ties to the identity catalog
    access_mode: local_write
  attribution:                              # NEW block — who did the work, vs who owns it
    authored_by: member.ai.claude.cowork
    planned_by: null                        # this lane was authored, not externally planned
    owner: member.derald                    # recorded once
    committer: member.derald                # git reality
  session:
    run_id: AIPR-20260722-007               # NEW — keys ai_runs.yaml
    chat_handle: ""                         # NEW — not self-resolvable this session
    handle_binding: MAINTAINER_ATTESTED     # NEW — owner attests what the platform hid
    continues_run: null                     # NEW
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 3231ae0c9
    head_commit: 0f06d1060
  authorization:
    requested_by: maintainer
    scope: scan-evaluator lane + AI run traceability governance lane
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_SCAN_EVALUATOR_LANE_2026-07-22.md
    kind: session_closeout
```

Compare the identity lane's row, which is the reason `planned_by` exists:
`attribution: { authored_by: member.ai.claude.cowork, planned_by: member.ai.chatgpt, owner: member.derald }`
— ChatGPT planned, Cowork implemented, Derald owns. v1 could not express that; v2 does.

## Migration + validator

- **Additive.** No v1 field is removed or renamed. A v1 envelope is still valid.
- **Version-gated required fields.** The validator adds the v2 fields to `required_fields` **only when
  `schema: ai-report-audit-v2`**; v1 envelopes are checked against the v1 list.
- **Registry cross-check.** `session.run_id` must exist in `labtalk/registries/ai_runs.yaml`, and its
  `member`/`project`/`handle_binding` must agree with the envelope (one truth, cross-validated).
- **Grandfathering.** Existing v1 closeouts are not rewritten; new closeouts SHOULD use v2 once the
  validator ships (M6 wires it into the closeout convention).

## Cross-references

- Contract: `AI_RUN_TRACEABILITY_CONTRACT_V1.md` (the roles + entities this envelope serializes).
- Registry: `labtalk/registries/ai_runs.yaml` (`session.run_id` resolves here).
- Policy to extend: `labtalk/registries/ai_report_audit.yaml` (add the v2 `required_fields` set).
