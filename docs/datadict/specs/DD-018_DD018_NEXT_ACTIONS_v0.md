# DD-018 Next Actions v0

## Immediate next safe step

DD-019 should define the catalog-staging import plan for DD-018 outputs, still without creating x64base tables.

Recommended DD-019 scope:

```text
- map DD018 CSV/JSON outputs to candidate x64base DBF table shapes
- define import order
- define primary keys and indexes
- define review gates
- define rollback/non-mutation rules
- keep catalog execution unauthorized
```

## Do not do yet

```text
- do not import DD018 rows into live x64base metadata DBFs
- do not mutate HELP DATA
- do not rebuild CMDHELP artifacts
- do not treat synthetic DD017 fixtures as project runtime proof
- do not promote educational/sample schema rows into engine core
```

## Runtime proof still needed

DD-018 can merge evidence, but runtime proof still requires locally captured transcripts from DD-014/DD-016 proof plans.
