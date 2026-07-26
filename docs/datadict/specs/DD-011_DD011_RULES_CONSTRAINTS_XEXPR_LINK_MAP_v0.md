# DD-011 Rules / Constraints / xexpr Dictionary Link Map v0

Date: 2026-05-27

Scope: report-only organization of the rules, field constraints, validation, expression-engine, and xexpr surfaces that should connect to the DotTalk++ / x64base data dictionary.

## Inputs

- Corrected C++ repo archive: `ccode_homegrown_20260527-055727.zip`
- Prior DD-005 physical source map
- Prior DD-006 physical manifest schema
- Prior DD-008 source-contract / MetaFact extension
- Prior DD-009/DD-010 HELP and diagnostics maps

## Result counts

| Item | Count |
|---|---:|
| Rule / constraint / expression source anchors | 82 |
| Bootstrap field constraints extracted | 8 |
| Rule-file contract rows | 17 |
| Validation command/surface rows | 4 |
| xexpr / CLI expression module rows | 62 |
| Function catalog seed rows | 63 |
| Dictionary catalog extension rows | 9 |
| Trust gate rows | 8 |
| Dependency edge rows | 8 |
| Warnings / review notes | 4 |

## Core finding

The repo already has three distinct validation/expression layers that the dictionary should not collapse into one vague bucket:

1. **Field constraint behavior** in `field_constraints.cpp` / `field_constraints.hpp`.
2. **External rule catalog contract** in `rule_catalog.cpp`, expecting `SCHEMAS/rules.meta` and `SCHEMAS/tables/<TABLE>.rules`.
3. **Expression and function infrastructure** under `src/cli/expr`, `include/cli/expr`, and the newer `xexpr` bridge.

The data dictionary should model these as related but separately trusted evidence.

## Bootstrap constraints observed

DD-011 extracted bootstrap source constraints for field-name patterns including GPA, AGE, DRIVER_AGE, STATUS, PRICE, AMOUNT, BALANCE, and STATE. These are implemented source behavior, but should remain marked as `source_bootstrap_constraint` until reviewed and reconciled with proper rule catalog files or runtime validation transcripts.

## Rule-file contract observed

`rule_catalog.cpp` provides a reusable rule-file contract:

- `SCHEMAS/rules.meta` defines named rules with `[RULE <name>]` sections.
- `SCHEMAS/tables/<TABLE>.rules` binds table fields to named rules with `[TABLE <table>]` sections.
- Supported rule properties include REQUIRED/NOTNULL/NOT_NULL, MIN, MAX, ENUM/IN, PATTERN, MESSAGE, DEFAULT, UNIQUE, and PRIMARY.
- TYPE is accepted for documentation/future compatibility, while field storage type still comes from `DbArea::fields()`.

No actual `.rules` or `rules.meta` files were present in the corrected source zip, so this package records the contract and source-code evidence, not runtime rule-file proof.

## xexpr / expression finding

`src/cli/expr/function_catalog.cpp` currently provides the most concrete function-documentation seed for `DD_FUNCTION`. The newer `src/xexpr/function_registry.cpp` appears to be a Phase 1 placeholder, so DD-011 keeps the active function catalog sourced from the legacy/current CLI expression catalog until the xexpr registry bridge is implemented and proven.

## Proposed catalog additions

- `DD_RULE`
- `DD_RULE_PROPERTY`
- `DD_RULE_BINDING`
- `DD_FIELD_CONSTRAINT`
- `DD_VALIDATION_SURFACE`
- `DD_EXPR`
- `DD_FUNCTION`
- `DD_FILTER_EXPR`
- `DD_EXPR_DIAGNOSTIC`

## Boundary

No repo mutation, no source edits, no build, no runtime launch, no validation command execution, no HELP/META/CMDHELPCHK mutation, and no DBF/CDX/LMDB/catalog mutation occurred.
