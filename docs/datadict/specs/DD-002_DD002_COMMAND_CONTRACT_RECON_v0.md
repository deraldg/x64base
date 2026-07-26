# DD-002 Command / Usage Contract Reconciliation v0

Mode: **REPORT_ONLY**  
Protected mutations: **0**

## Inputs

- Parsed `@dottalk.usage v1` contracts: 208 rows.
- Parsed command registry entries: 223 rows.

## Method

This pass compares usage blocks to registry entries by:

1. Exact command name.
2. Alias expansion for forms such as `ERP / EDU_ERP`.
3. Compact matching for multiword commands such as `SET PATH` -> `SETPATH`.

This is a **review queue**, not a defect list. Some apparent differences are expected because several usage contracts describe command families, aliases, subcommands, shims, or non-registered helper surfaces.

## Summary

| Reconciliation status | Count |
|---|---:|
| registry_has_usage_alias | 184 |
| exact_registry_match | 167 |
| registry_without_matched_usage_block | 39 |
| alias_or_compact_registry_match | 18 |
| usage_contract_not_matched_to_registry | 15 |
| usage_block_without_command_token | 8 |


## Profile boundary signal

The scan identified 23 command/usage rows that look educational, student, demo, or case-related. Those should be assigned to optional overlay visibility unless deliberately promoted.

## Dictionary implication

DD-002 should feed:

```text
DD_COMMAND
DD_COMMAND_ALIAS
DD_USAGE_CONTRACT
DD_HELP_LINK
DD_COMMAND_OBJECT
DD_MUTATION_CLASS
```

and should add a profile field:

```text
visibility_profile = ENGINE | PROFESSIONAL | EDUCATIONAL | DEV_ONLY | MAINTENANCE
```

## Next action

Review `dd002_registry_without_usage_v0.csv` and `dd002_usage_without_registry_v0.csv`. The likely next useful step is to classify each as one of:

```text
OK_ALIAS_OR_FAMILY
OK_SUBCOMMAND
OK_INTERNAL_HELPER
NEEDS_USAGE_BLOCK
NEEDS_REGISTRY_REVIEW
EDUCATIONAL_OVERLAY
DEPRECATED_OR_SHIM
```
