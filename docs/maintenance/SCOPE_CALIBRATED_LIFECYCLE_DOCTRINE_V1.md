# Scope-Calibrated Lifecycle Doctrine v1

Status: **accepted maintainer doctrine; development documentation**  
Recorded: 2026-07-22  
Applies to: PDLC, DotTalk++ SDLC, LabTalk SDLC, maintenance SDLC,
AI-assisted work, and publication

## Decision

Best practice is not the maximum process that can be applied. Best practice is
the smallest process that responsibly covers the change's actual consequences.

This project has two legitimate contexts:

- As a **laboratory and teaching system**, it may intentionally traverse the
  complete lifecycle so students can see requirements, design, code, tests,
  contracts, HELP, metadata, documentation, delivery, maintenance, and
  deprecation as one coherent system.
- As an **empirical working system**, it must scale effort to scope. A localized,
  reversible change does not automatically justify a source-wide regression,
  metadata reharvest, manual rebuild, documentation flush, and website release.

The teaching exercise is valid because the traversal itself is part of the
product. The same traversal would be disproportionate production work unless
the change's blast radius, uncertainty, or release state actually required it.

## Lifecycle vocabulary

These terms are related but not interchangeable:

| Lifecycle | Scale | Governing question |
| --- | --- | --- |
| **PDLC -- Programming Development Life Cycle** | One program or feature; and the product, lab, lesson, workshop, dashboard, manual, or public page that delivers it | How does a programmer analyze, design, code, test/debug, document, and maintain this change -- and what package are we delivering, to whom, with what setup, proof, support, and retirement path? |
| **SDLC -- Software/Systems Development Life Cycle** | Runtime, subsystem, or whole system | What behavior exists, how is it controlled, and what evidence keeps it trustworthy? |

PDLC work nests inside an SDLC when the unit is a change, and packages reviewed
SDLC and LabTalk truth when the unit is a deliverable; it cannot promote an
unproven behavior merely because the teaching or public wrapper is complete.

> **Merge note, 2026-08-07 (member.derald).** "PLDC -- Product/Lab Delivery
> Cycle" was retired and merged into **PDLC**. The former PLDC row's scale and
> governing question were folded into the PDLC row above, so PDLC's SCOPE now
> spans both the change and the deliverable. Its NAME is unchanged: PDLC remains
> the **Programming** Development Life Cycle, the craft-scale cycle taught in
> `PDLC_STUDENT_WORKING_MODEL_LANE_V1.md`. Supersedes ruling R1 in
> `X64BASE_AGENT_SKILL_PDLC_LANE_V1.md`.

## Operating modes

Every material task declares one mode before its gate depth is selected:

| Mode | Purpose | Normal posture |
| --- | --- | --- |
| `laboratory` | Teach, explore, or expose the lifecycle itself. | A full traversal may be intentional. Label which stages are instructional and which claims are empirically proven. |
| `production` | Deliver a bounded behavior or product change. | Run the smallest sufficient affected gates; avoid unrelated regeneration and ceremony. |
| `maintenance` | Integrate, repair, deprecate, or replace existing parts. | Preserve compatibility, provenance, migration, rollback, and consumer impact. |
| `incident` | Contain active harm or restore service. | Containment and recovery first; reconstruct missing documentation and evidence in a named follow-up. |

The mode describes why the work is being performed. It does not weaken safety,
authority, or honesty requirements.

## Build target and product composition

Scope also follows the artifact being built. The repository does not require
every engine change to be treated as a full DotTalk++ product change.

| Selection | Meaning | Normal proof boundary |
| --- | --- | --- |
| `xbase` / x64base engine-only | Compile and consume the table/record engine as the `xbase` static-library target without assuming the `dottalkpp` CLI is the deliverable. | Engine build, engine contracts, affected data-format tests, and direct engine consumers. |
| `dottalkpp` runtime | Build the CLI/runtime executable over the selected engine, index provider, components, and front ends. | Runtime build, affected commands, HELP/metadata, scripts, and runtime consumers. |
| Product profile | Select `LEAN`, `PROFESSIONAL`, `EDUCATIONAL`, or `DEVELOPMENT` through `DOTTALK_PRODUCT`. | Only the components and user-facing surfaces included by that profile, plus shared dependencies. |
| Index profile | Select `NONE`, `LEGACY`, or `LMDB` through `DOTTALK_INDEX_MODE`. | Only the selected provider boundary and the behavior that depends on it. |

These axes are independent. `LEAN` is a smaller product composition, not a
synonym for engine-only or no-index. A lean DotTalk++ executable may still use
LMDB; an x64base engine-only task may have no CLI, LabTalk, manual, or website
surface at all. Conversely, a change in shared xbase behavior may require
downstream DotTalk++ checks when impact analysis shows that the runtime consumes
the changed contract.

The selected target/profile narrows the default gate set. Dependency evidence,
not the product's largest possible assembly, determines when the gate expands.

## Change classes and minimum gates

| Class | Typical change | Minimum expected gate |
| --- | --- | --- |
| `C0` | Read-only investigation, wording correction, or non-behavioral record update | Verify the authority and affected document; no runtime gate unless a behavior claim changed. |
| `C1` | Localized, reversible implementation change with a narrow interface | Targeted build/test and direct dependent documentation or contract check. |
| `C2` | Contract, schema, command, persistence, or public-interface change | Affected consumer tests; contract, HELP, metadata, migration, and compatibility review as applicable. |
| `C3` | Cross-cutting subsystem or authority-chain change | Impact map, broader regression, affected metadata/documentation reharvest, durable progress record, and review. |
| `C4` | Release, source promotion, manual/publication baseline, or public deployment | Full provenance, exact staging scope, release/publication build, deployment readback, and live verification. |

Laboratory mode may deliberately run gates above the minimum. When it does, the
record must say that the extra depth is an educational walkthrough rather than a
claim that every production change requires that cost.

## Scope decision factors

Gate depth is determined from evidence, not file count alone:

- behavioral and data-mutation blast radius;
- compatibility and public-interface impact;
- reversibility and rollback cost;
- persistence, security, and user-safety risk;
- uncertainty or known drift in the affected authority chain;
- number and type of downstream consumers;
- release/publication exposure;
- instructional intent;
- available time, budget, tooling, and organizational constraints.

Budget or corporate limitation may defer work, but it does not convert an
unverified claim into a verified one. Record the missing gate, residual risk,
responsible owner, and next opportunity instead of silently lowering the truth
label.

## Documentation proportionality rule

Documentation scope follows behavior and audience scope.

- A minor internal correction normally receives a targeted contract/doc check.
- A changed command or public contract updates its affected HELP, metadata, tests,
  and consumers.
- A cross-cutting change may require reharvest and broad documentation
  reconciliation.
- A release or publication change requires the full provenance and live-readback
  path.
- A teaching exercise may intentionally demonstrate the complete chain.

Do not launch a major documentation flush after a minor change merely because the
pipeline exists. Do launch one when the change crosses the authority chain, when
drift makes the affected set uncertain, when a new baseline is being accepted, or
when the lifecycle traversal is the named educational objective.

## AI Portal rule

Before proposing work, an AI records:

```text
operating_mode: laboratory | production | maintenance | incident
change_class: C0 | C1 | C2 | C3 | C4
build_target: xbase_engine | dottalkpp_runtime | binding | frontend | documentation_only
product_profile: LEAN | PROFESSIONAL | EDUCATIONAL | DEVELOPMENT | not_applicable
index_profile: NONE | LEGACY | LMDB | inherited | not_applicable
scope_reason:
affected_authorities:
minimum_gate_set:
optional_educational_gates:
deferred_gates_and_residual_risk:
```

The AI selects the smallest sufficient evidence set, explains any expansion, and
does not infer a full-stack flush from the existence of the full-stack machinery.
It also must not silently down-scope a change whose contracts, data, consumers, or
publication exposure require broader proof.

## Student lesson

Students should first see the complete lifecycle because hidden stages cannot be
scoped intelligently. They should then learn to classify a change and contract the
process without losing truth, safety, or maintainability.

The mature lesson is therefore:

> Learn the whole system. Apply the part the change requires. Record what was
> intentionally omitted and why.

## Non-goals

This doctrine does not weaken source-mutation gates, permission boundaries,
evidence labels, or publication authority. It does not prescribe one corporate
methodology or pretend that unconstrained laboratory time is typical production
economics. It makes that difference explicit and teachable.
