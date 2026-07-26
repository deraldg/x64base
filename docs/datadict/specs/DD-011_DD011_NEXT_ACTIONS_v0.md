# DD-011 Next Actions v0

Recommended next package: **DD-012 Runtime Rule Artifact Inventory Plan**, still report-only.

1. Locate real runtime/data roots that may contain `SCHEMAS/rules.meta` and `SCHEMAS/tables/*.rules`.
2. Extend the DD-007 Python extractor with a rule-file reader that parses `[RULE <name>]` and `[TABLE <table>]` sections.
3. Emit `DD_RULE`, `DD_RULE_PROPERTY`, and `DD_RULE_BINDING` manifest arrays without applying them to runtime data.
4. Cross-check table/field bindings against DD-005/DD-007 physical table evidence.
5. Add expression parse status for rule properties only after a guarded parse-only stage exists.
6. Keep `VALIDATE UNIQUE REPAIR` behind explicit authorization; it is not part of report-only dictionary extraction.

Do not promote bootstrap constraints as final dictionary rules until Derald reviews them against intended rule-file and runtime behavior.
