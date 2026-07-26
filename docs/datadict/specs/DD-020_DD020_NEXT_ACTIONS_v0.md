# DD-020 Next Actions v0

## Immediate next safe move

DD-021 should be a repo-integration and redocumentation-cycle placement plan.

It should decide where the Data Dictionary tools, manifests, schemas, reports, staging CSVs, and run-history artifacts belong in the repo.

## Before any staging import execution

1. Complete field plans for `DD_WARNING`, `DD_PROFILE_SCOPE`, `DD_PROMOTION_QUEUE`, and `DD_IMPORT_FILE`, or mark them deferred.
2. Add DBF-width/type validation for staging CSV columns.
3. Add a previous-run comparison mode for redocumentation drift.
4. Decide what report artifacts should be checked into the repo versus treated as generated run output.
5. Keep `PROMOTION_AUTHORIZED` blocked until a later explicit promotion package.

## Still forbidden here

- no x64base DBF catalog creation;
- no import execution;
- no HELP rebuild;
- no CMDHELPCHK mutation;
- no source edits;
- no promoted dictionary fact mutation.
