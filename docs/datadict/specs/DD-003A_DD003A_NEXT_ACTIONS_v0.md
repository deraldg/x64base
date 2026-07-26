# DD-003A Next Actions v0

Status: REPORT_ONLY_NEXT_STEPS

## Recommended next step: DD-003B

Create a guarded script-root placement plan.

Goals:

1. Separate runtime scripts from maintenance scripts.
2. Reserve a clean location for DotScript runtime assets, workspace schema assets, smoke scripts, MDO/manualgen packages, and savepoint appenders.
3. Do not move or rewrite any current repo file yet.
4. Produce a manifest that can later be imported into x64base as DD_SCRIPT rows.

## Proposed roots

```text
scripts/runtime/
  DotScript setup files, x32/x64 path setup, workspace loaders, init/shutdown templates.

scripts/tests/
  smoke and test DotScripts used by TEST or DOTSCRIPT.

scripts/maintenance/
  MDO/manualgen packages, savepoint appenders, cleanup/bundle tools.

scripts/probes/
  Python binding probes and runtime API checks.

docs/manuals/developer/manualgen/
  Generated manual workspaces and reports remain here; scripts may point into this area but should not be scattered through it without registry rows.
```

## Guardrails

- No script execution as part of DD-003B.
- No source edits.
- No HELP, META, CMDHELPCHK, DBF, or runtime data mutation.
- No movement of historical scripts without an accepted migration manifest.
- Student/education scripts must be flagged overlay, not core.

## Suggested DD-003B outputs

- `dd003b_script_root_placement_plan_v0.csv`
- `dd003b_script_migration_manifest_draft_v0.csv`
- `dd003b_runtime_required_script_candidates_v0.csv`
- `dd003b_maintenance_script_candidates_v0.csv`
- `dd003b_overlay_script_candidates_v0.csv`
