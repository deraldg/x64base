# AI Portal Scope Calibration Seed v1

Status: **mandatory for planning material work**  
Authority: `docs/maintenance/SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`

## Precedence against the SDLC fast-start seed (AIF-082, 6.5c)

Two documents ask for overlapping field blocks. Settled 2026-07-31:

- **`SDLC_FAST_START_SEED_V1.md` "Mandatory Task Fields" is the superset** (20
  fields) and is what a task packet, change package, or closeout carries.
- **The block below is the planning subset** (10 fields), seven of which also
  appear there: `operating_mode`, `change_class`, `build_target`,
  `product_profile`, `index_profile`, `scope_reason`, and the gate set.

**Fill this one first, while planning; it feeds the other.** Filling this block
satisfies its seven shared fields wherever they appear. Neither document
overrides the other on a shared field -- they must agree, and if they cannot,
that is a finding to report rather than a choice to make.

The three fields unique to this block (`affected_authorities`,
`optional_educational_gates`, `deferred_gates_and_residual_risk`) have no
equivalent in the superset and are the reason this block exists separately.

## Rule

The AI Portal exposes the complete PDLC/SDLC/PLDC, but the existence of the full
pipeline is not standing instruction to run every gate for every change.

Before planning, classify:

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

## Calibration

- `laboratory`: a complete lifecycle walkthrough may itself be the learning
  product; label the added gates as instructional.
- `production`: use the smallest sufficient affected gates.
- `maintenance`: emphasize integration, compatibility, provenance, migration,
  rollback, and deprecation.
- `incident`: contain and recover first, then create an explicit evidence and
  documentation follow-up.

Change classes rise from `C0` non-behavioral work through `C4` release or public
deployment. A minor correction does not automatically trigger a complete source,
HELP, metadata, manual, and website flush. A contract, schema, persistence,
cross-cutting, or publication change must not be mislabeled as minor to avoid its
real gates.

## Product-boundary rule

Do not assume that every task targets the full DotTalk++ assembly.

- `xbase_engine` means the compiled `xbase` static-library target and its direct
  contracts/consumers are the starting boundary.
- `dottalkpp_runtime` means the CLI/runtime executable is in scope.
- `DOTTALK_PRODUCT` independently selects `LEAN`, `PROFESSIONAL`,
  `EDUCATIONAL`, or `DEVELOPMENT` components.
- `DOTTALK_INDEX_MODE` independently selects `NONE`, `LEGACY`, or `LMDB`.

`LEAN` does not mean engine-only and does not mean no-index. Expand from an
x64base or lean gate to full DotTalk++, LabTalk, manual, or publication gates
only when a changed shared contract, an affected consumer, a release boundary,
or the stated teaching objective requires it.

## Relationship to the lifecycle stack

- **PDLC** teaches the programmer's six-step craft cycle.
- **SDLC** owns system behavior and proof.
- **PLDC** packages labs, lessons, products, manuals, and public views.

PLDC cannot outrun SDLC evidence. Educational depth can exceed the production
minimum, but it must be recorded as educational depth.

## Expected AI behavior

1. State mode, class, reason, and affected authorities.
2. Propose the minimum gate set.
3. Separate optional teaching gates from required proof.
4. Record deferred gates and residual risk honestly.
5. Expand scope only when evidence, dependencies, drift, or explicit instruction
   justifies it.

The canonical doctrine contains the complete decision matrix and examples.
