# DotTalk++ Contract Shelf

Status: active index.

## Purpose

This folder is the durable home for DotTalk++ contracts.

The project already has contract-like material spread across source comments,
USAGE blocks, HELP metadata, manualgen evidence, governance notes, database
contracts, GUI contracts, and chat-derived plans. That spread is useful, but it
is not enough. Contracts need a central registry so they survive chat churn,
memory loss, partial success, abandoned branches, and repeated rediscovery.

## Core Rule

If a decision is meant to constrain future work, it needs a contract entry.

Chat can propose a contract. Code can imply a contract. Runtime can prove a
contract. But the durable place to find and track it is this shelf.

## Related Existing Systems

- Source usage contracts harvested by `metacollect`.
- `@dottalk.contract` source annotations.
- HELP/CMDHELP/CMDHELPCHK validation.
- SelfDoc and manualgen evidence trails.
- Governance authority rules under `docs/governance`.
- Database contracts under `docs/database`.
- GUI/UI contracts under `docs/gui` and `docs/ui`.

This shelf does not replace those systems. It indexes and normalizes them.

## Contract Kinds

| Kind | Meaning | Typical home |
| --- | --- | --- |
| Usage contract | Command syntax, no-arg behavior, usage access, examples | source comments, HELP, metadata |
| Runtime contract | Behavior guaranteed by executable code/tests | source, tests, docs/contracts |
| Data contract | File format, schema, value semantics, metadata shape | docs/database, include headers |
| UI contract | Shared UI concepts, event names, window behavior | docs/ui, docs/gui |
| Build contract | Configure options, dependencies, platform rules | CMake, docs/build, docs/contracts |
| Safety contract | Mutation, recovery, locks, validation, destructive operations | docs/database, docs/contracts |
| Publication contract | Manual/help/selfdoc/governance publication rules | docs/governance, docs/manuals |
| Historical contract | Old behavior retained for compatibility or provenance | docs/cases, docs/archive |

## Authority

Follow the existing authority order:

```text
Runtime proves.
Source defines.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
Master Document Organizer assembles teachable manuals.
```

Design-intended contracts are valid planning artifacts, but they must not be
described as runtime-proven until code and tests prove them.

## Files

- `CONTRACT_REGISTRY_V1.md`
  - current contract index and ownership map.
- `CONTRACT_LIFECYCLE_V1.md`
  - how contracts move from chat/design to source/test/manual.
- `CONTRACT_TEMPLATE_V1.md`
  - copyable template for future contracts.
- `CONTRACT_LANE_MANIFEST_V1.md`
  - lane definition using the project data-in/process/information-out model.
- `CONTRACT_LANE_WORKFLOW_V1.md`
  - operating workflow for intake, classification, registration, promotion, and drift review.
- `CONTRACT_INTAKE_QUEUE_V1.md`
  - queue for implied or missing contracts before they graduate into the registry.
- `CONTRACT_MANAGER_MODE_V1.md`
  - decision record for `MAINT CONTRACTS` as the first manager surface.
- `reports/CONTRACT_SCAN_BASELINE_V1.md`
  - first report-proven inventory checkpoint for the lane.

## Tooling

- `../../tools/contracts/contract_scan.py`
  - read-only scanner for contract-like docs, source `@dottalk.contract`
    annotations, and source usage markers.

## Working Rule For Agents

When a chat decision creates a rule that future contributors should remember:

1. Add or update a contract document.
2. Add it to `CONTRACT_REGISTRY_V1.md`.
3. Mark its evidence class honestly.
4. Link code/tests/docs that prove or depend on it.
5. If it is temporary, give it an expiry/review trigger.

Anything less is a note, not a contract.
