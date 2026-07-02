# DotTalk++ Contract Lane Workflow v1

Status: active lane workflow.

## Purpose

This workflow turns temporary decisions into durable contracts and keeps durable
contracts from drifting away from source, runtime, HELP, metadata, and manuals.

## Intake Sources

Contracts may enter from:

- chat decisions,
- source `USAGE` blocks,
- `@dottalk.contract` annotations,
- command implementation notes,
- HELP/CMDHELP/CMDHELPCHK differences,
- database format rules,
- GUI/event/threading rules,
- build/platform rules,
- safety/destructive-operation rules,
- manualgen/SelfDoc governance rules,
- test fixtures and runtime reports.

## Intake Decision

When a new rule appears, classify it:

| Question | If yes |
| --- | --- |
| Does it constrain future behavior? | Create or update a contract |
| Is it command syntax or command behavior? | Route through usage contract lane and registry |
| Is it source/API behavior? | Add source comment/test hook when practical |
| Is it user-facing? | Plan HELP/CMDHELP alignment |
| Is it database safety or mutation behavior? | Link database safety contract |
| Is it temporary? | Add expiry/review trigger |
| Is it rejected? | Mark rejected instead of deleting context |

## Workflow

1. Capture
   - Add the rule to a contract doc or `CONTRACT_INTAKE_QUEUE_V1.md`.
2. Classify
   - Assign kind, owner area, evidence class, and review trigger.
3. Register
   - Add or update a row in `CONTRACT_REGISTRY_V1.md`.
4. Cross-link
   - Link relevant source, tests, HELP, metadata, reports, and docs.
5. Prove
   - Add tests, smoke commands, or reports when the contract claims runtime behavior.
6. Promote
   - Move from design-intended to source-defined/runtime-proven as evidence improves.
7. Check drift
   - Run the contract scanner and compare registry rows to discovered candidates.
8. Supersede or reject
   - Keep the historical decision visible instead of silently losing it.

## Contract Review Cadence

Run the contracts lane review when:

- adding a command,
- changing runtime `USAGE`,
- adding or changing file formats,
- changing index/search/collation behavior,
- adding a GUI event/request/result,
- adding write/edit behavior,
- changing locale/language behavior,
- changing build options or dependencies,
- promoting manual/help content from source evidence,
- closing a long chat thread with durable decisions.

## Initial Scanner Gate

Use:

```powershell
python tools\contracts\contract_scan.py --summary
```

The scanner should remain read-only by default. It reports:

- contract documents,
- source contract annotations,
- usage-contract markers,
- likely unregistered contract documents.
- registry rows whose source is not detected by the current scanner.

Useful modes:

```powershell
python tools\contracts\contract_scan.py --summary
python tools\contracts\contract_scan.py --markdown
python tools\contracts\contract_scan.py --json
```

## Promotion Ladder

| State | Requirement |
| --- | --- |
| Chat-intended | discussed only |
| Draft | doc or intake row exists |
| Design-intended | registry row exists |
| Source-defined | source/API/comment implements it |
| Runtime-proven | test/runtime/report proves it |
| HELP-documented | HELP/CMDHELP agrees |
| Publication-ready | SelfDoc/manualgen can cite evidence |

## Output Artifacts

Contracts lane outputs should be placed under:

- `docs/contracts`,
- `docs/contracts/reports` later if reports become numerous,
- source comments/tests when a contract becomes source-defined,
- HELP/metadata/manualgen lanes when a contract becomes user-facing.

## Anti-Drift Rule

Do not let a contract remain stronger in prose than in proof.

If a contract is only design-intended, say so. If source proves it, link the
source. If runtime proves it, link the test or report.
