# DD-012 Runtime Rule Artifact Inventory Plan v0

Status: `REPORT_ONLY_RULE_ARTIFACT_INVENTORY_PLAN`

Input package: `ccode_homegrown_20260527-055727.zip`

DD-012 continues the data-dictionary lane after DD-011 by turning the rule/constraint/xexpr design map into a concrete runtime artifact inventory plan. It does **not** execute DotTalk++, does **not** run validation commands, and does **not** create or mutate any rule files.

## Result summary

| Item | Count |
|---|---:|
| Rule/source artifact rows | 8 |
| Expected runtime artifact rows | 6 |
| Rule-file grammar rows | 13 |
| Rule path-resolution rows | 9 |
| Validation touchpoint rows | 17 |
| Bootstrap constraint rows | 8 |
| Schema constraint rows | 6 |
| RULE command surface rows | 6 |
| Catalog extension rows | 7 |
| Trust gate rows | 7 |

## Key finding

The corrected repo package contains the rule/constraint **source contract**:

```text
src/cli/rule_catalog.cpp
src/cli/rule_catalog.hpp
src/cli/cmd_rule.cpp
src/cli/field_constraints.cpp
include/cli/field_constraints.hpp
src/schemas/spec/schema_json_v1.schema.json
src/schemas/students.schema.json
```

The uploaded repo package does **not** contain runtime rule artifacts such as:

```text
SCHEMAS/rules.meta
SCHEMAS/tables/<TABLE>.rules
```

That is acceptable and useful evidence: DD-012 distinguishes implemented parser/path contract from actual runtime rule-artifact presence. Missing rule files are not defects by themselves; they are runtime/package inventory items that need local path evidence later.

## Rule artifact contract captured

`rule_catalog.cpp` establishes the external rule-file contract:

```text
Global catalog:
  SCHEMAS/rules.meta

Table bindings:
  SCHEMAS/tables/<TABLE>.rules
```

The path resolver starts from the active `DbArea`, walks upward looking for `SCHEMAS` or lowercase `schemas`, includes a fallback for expected DotTalk++ data layout, and finally returns a deterministic `p / "SCHEMAS"` path if nothing exists. The caller then reports no external rule constraint if the expected files do not exist.

## Rule grammar captured

DD-012 captures these parser-compatible surfaces:

```text
rules.meta:
  [RULE <name>]
  REQUIRED / NOTNULL / NOT_NULL
  MIN
  MAX
  ENUM / IN
  PATTERN
  MESSAGE
  DEFAULT
  UNIQUE
  PRIMARY

SCHEMAS/tables/<TABLE>.rules:
  [TABLE <table>]
  <FIELD>=<RULE>
```

`TYPE` is accepted in rule files for documentation/future compatibility according to source comments, while actual field storage type still comes from `DbArea::fields()`.

## Runtime validation distinction

The current system has three different rule/constraint evidence classes:

1. **Bootstrap constraints** in `field_constraints.cpp`.
2. **External runtime rule files** through `rules.meta` and table `.rules` files.
3. **Declared schema constraints** in JSON schema files such as `students.schema.json`.

These should not be collapsed. The data dictionary should preserve source and trust class:

```text
BOOTSTRAP_SOURCE
EXTERNAL_RULE_ARTIFACT
DECLARED_SCHEMA
RUNTIME_TRANSCRIPT
```

## Proposed catalog additions

DD-012 proposes these dictionary tables or catalog views:

```text
DD_RULE_SOURCE
DD_RULE
DD_RULE_PROPERTY
DD_RULE_BINDING
DD_FIELD_CONSTRAINT
DD_VALIDATION_SURFACE
DD_RULE_VERIFY
```

The most important rule is that a `DD_RULE_BINDING` should not become active unless both sides are proven:

```text
field exists in DD_FIELD / runtime table evidence
rule exists in DD_RULE / rules.meta evidence
```

## Boundary

No repository files were changed. No source files were edited. No build ran. DotTalk++ was not launched. RULE commands were not executed. No HELP, META, CMDHELPCHK, DBF, CDX, LMDB, or catalog mutation occurred.

## Files in this package

- `dd012_rule_artifact_inventory_v0.csv`
- `dd012_expected_runtime_rule_artifacts_v0.csv`
- `dd012_rule_file_grammar_v0.csv`
- `dd012_rule_path_resolution_model_v0.csv`
- `dd012_validation_touchpoints_v0.csv`
- `dd012_bootstrap_constraint_inventory_v0.csv`
- `dd012_schema_constraint_inventory_v0.csv`
- `dd012_rule_command_surface_v0.csv`
- `dd012_catalog_extension_v0.csv`
- `dd012_execution_plan_v0.csv`
- `dd012_trust_gates_v0.csv`
- `dd012_summary_v0.json`
