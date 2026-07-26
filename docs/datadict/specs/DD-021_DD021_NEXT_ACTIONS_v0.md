# DD-021 Next Actions v0

## Immediate next package

DD-022 should define the repeatable redocumentation orchestrator contract.

Recommended DD-022 scope:

```text
DD-022 Redocumentation Orchestrator Contract / Dry-Run Plan
  - define command-line contract for tools/datadict/run_datadict_redoc.py
  - define run_id behavior
  - define output directory creation
  - define tool execution order
  - define required schemas
  - define pass/review/fail aggregation
  - define no-mutation default
  - define local vs accepted run policy
```

DD-022 should still be report-only. It should not install the orchestrator into the repo yet.

## Near-term follow-ups

```text
DD-023  Complete DD-019 staging table field specs for DD_WARNING, DD_PROFILE_SCOPE, DD_PROMOTION_QUEUE, DD_IMPORT_FILE.
DD-024  Multi-run diff/change detection model.
DD-025  Review queue/disposition model.
DD-026  Documentation regeneration candidate map.
DD-027  Guarded repo-install patch plan for tools/datadict and docs/datadict, still without runtime/catalog mutation.
```

## Authorization boundary

Do not create x64base catalog DBFs or import staged rows until a named promotion package is explicitly authorized.
