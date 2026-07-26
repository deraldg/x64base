# DD-000 Next Actions

## Recommended sequence

1. Accept DD-000 as an organizing baseline only.
2. Run DD-001 as a report-only physical table/field/index/memo inventory.
3. Run DD-003 as a report-only script/tooling registry, explicitly including DotScript, PowerShell/MDO/savepoint, Python probes, launchers, and build configs.
4. Run DD-004 as a build-profile audit before any source edits: ENGINE, PROFESSIONAL, EDUCATIONAL.
5. Defer promoted catalog tables until reports are reviewed and accepted.

## Guardrails

- No HELP DATA rebuild.
- No CMDHELPCHK mutation.
- No production metadata promotion.
- No source edits.
- No runtime DBF mutation.
- No educational overlay dependency in x64base engine mode.

## First implementation stance

Use Python 3.12 for cross-platform report-only harvesters, then import/catalog accepted outputs into x64base/DotTalk++ as proof-of-the-pudding once the reports stabilize.
