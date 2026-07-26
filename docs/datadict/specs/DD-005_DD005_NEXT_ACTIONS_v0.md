# DD-005 Next Actions v0

## Immediate next move: DD-006

Create a manifest schema for the first physical dictionary extractor.

Suggested canonical machine outputs:

```text
dd_source.json
dd_table.json
dd_field.json
dd_field_name_policy.json
dd_memo_status.json
dd_index.json
dd_workarea.json
dd_relation.json
dd_runtime_proof.json
```

Suggested human/audit outputs:

```text
dd006_manifest_schema.md
dd006_manifest_schema.csv
dd006_required_fields.csv
dd006_validation_rules.csv
```

## DD-006 guardrails

- Report-only.
- No source edits.
- No generated HELP/CMDHELPCHK/META mutation.
- No runtime DBF/CDX/LMDB mutation.
- Do not require LabTalk/student/case/media artifacts.
- Use Python 3.12 for future extractor tooling, but do not generate extractor code until separately authorized.

## DD-007 after DD-006

Create a Python 3.12 extractor skeleton only after the manifest schema is accepted.

The extractor should read from:

```text
repo source files
schema JSON sidecars
known script registry
optional runtime transcript inputs
```

It should emit candidate manifests only.

## DD-008 after DD-007

Plan runtime adapter surfaces for:

```text
FIELDS
MEMO STATUS / VERIFY
CDX STATUS
WORKSPACE
RELATIONS
SCHEMAS
RULE
```

This adapter should produce runtime proof rows that can be compared against source/schema declarations.
