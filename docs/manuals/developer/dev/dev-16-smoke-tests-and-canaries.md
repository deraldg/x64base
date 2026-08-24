# DEV-16 Smoke Tests and Canaries

```yaml
page_id: DEV-16
title: Smoke Tests and Canaries
status: DRAFT_PATCHED
last_verified: 2026-07-07
```

## Canary classes

- Runtime canaries
- HELP/META evidence canaries
- Manual-generation canaries
- Publication-lane canaries

## Proof levels

`OBSERVED`, `SCRIPTED`, `VALIDATED`, `REGRESSION`, `CATALOGED`.

CATALOGED is not the same as PROVEN.

## Current regression rule

Regression scripts are expected to bootstrap their own environment.

Practical rule:

- start by setting the lane, for example `DO x32`, `DO x64`, `DO cmdhelp`, or
  `DO metadata`
- then open tables, workspaces, schemas, or ERSATZ paths
- if an older script still has value but assumes caller-owned state, fix it
- if it no longer has value, retire it

The curated `REGRESSION` launcher is not meant to expose every historical
DotScript. It is the stable top-layer entrypoint for reviewed regression
surfaces.

## Current documentation canary stack

For command/reference/help drift, the current verified canary stack is:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Verified 2026-07-07 outcome:

- legacy compatibility rows refreshed
- current HELP DATA harvested `REGISTRY`, `DOTREF`, `FOXREF`, `EDREF`,
  `SHARED_MSG`, `SOURCE_MINER`, and `USAGE_CONTRACT`
- structural validation passed

## Named current canary examples

- `dottalkpp/data/scripts/canaries/x64_matrix_metrics_boundary_canary.dts`
- curated `REGRESSION HARVEST` top-layer shakedown
- reflection/public-surface checks via `CMDHELPCHK`

## Standing canary rules

- HELP breadth is not behavior proof.
- META absence is not project absence.
- SOURCE_MINER inference is not public documentation.
- Runtime proof is path-specific.
- Canaries remain visible until closed with evidence.
- Website/manual polish is not authority by itself.
