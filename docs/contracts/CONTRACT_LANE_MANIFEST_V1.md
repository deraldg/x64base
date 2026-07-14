# DotTalk++ Contract Lane Manifest v1

Status: active lane seed.

## Purpose

The contracts lane is the durable memory lane for rules that should constrain
future DotTalk++ work. It exists because usage contracts, source annotations,
architecture rules, safety rules, and chat decisions can otherwise scatter
across source, HELP, reports, manuals, and old conversations.

## Lane Model

| Part | Description |
| --- | --- |
| Runtime surface | `MAINT CONTRACTS` first; future `CONTRACTS` alias only after stabilization |
| Data in | chat decisions, source `USAGE` blocks, `@dottalk.contract` annotations, HELP/CMDHELP evidence, governance docs, database/UI/build/safety contracts |
| Blackbox process | intake, classify, register, cross-link, validate, promote, supersede |
| Information out | contract registry, lifecycle state, intake queue, contract scan reports, drift reports, promotion tasks |
| Current state | docs shelf, registry, first scanner, baseline report, and first `MAINT CONTRACTS` / `BBOX CONTRACTS` runtime surfaces exist |
| Next gate | connect usage-contract harvesting and source annotations to a generated contract inventory report |

## Lane Boundaries

The contracts lane does not replace:

- source comments,
- runtime `USAGE`,
- HELP/CMDHELP,
- CMDHELPCHK,
- SelfDoc,
- manualgen,
- database/UI planning docs.

It indexes and governs them.

## Current Artifacts

| Artifact | Role |
| --- | --- |
| `README.md` | lane entry point |
| `CONTRACT_REGISTRY_V1.md` | active contract index |
| `CONTRACT_LIFECYCLE_V1.md` | state model and promotion path |
| `CONTRACT_TEMPLATE_V1.md` | template for new contracts |
| `CONTRACT_LANE_MANIFEST_V1.md` | this lane manifest |
| `CONTRACT_LANE_WORKFLOW_V1.md` | operating workflow |
| `CONTRACT_INTAKE_QUEUE_V1.md` | queue for implied or missing contracts |
| `CONTRACT_MANAGER_MODE_V1.md` | manager-surface decision across MAINT, BBOX, DDICT, and future commands |
| `tools/contracts/contract_scan.py` | first repeatable inventory scanner |

## Evidence Policy

Every contract must carry an honest evidence class:

- Design-intended,
- Source-defined,
- Runtime-proven,
- HELP-documented,
- Metadata-staged,
- Report-proven,
- Historical,
- Deferred,
- Unknown,
- Rejected.

The registry must not describe a contract as runtime-proven unless a test,
runtime command, or reproducible report proves it.

## First Validation Gate

The first lane gate is intentionally modest:

1. Inventory docs that look like contracts.
2. Inventory source files with `@dottalk.contract`.
3. Inventory source usage-contract markers.
4. Compare the inventory with `CONTRACT_REGISTRY_V1.md`.
5. Produce a report listing unregistered candidates.

Later gates can become stricter and understand command metadata, HELP rows,
manualgen evidence, and runtime tests.

## Working Rule

No future architectural rule should depend only on chat memory.

If a rule matters, put it in this lane.
