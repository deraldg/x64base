# DD-012 Next Actions v0

Recommended next package: **DD-013 Workspace / Relation / Tuple Dictionary Source Map**, report-only.

Before any runtime rule promotion, keep these holds in place:

1. Do not create or edit `SCHEMAS/rules.meta` automatically.
2. Do not create or edit `SCHEMAS/tables/<TABLE>.rules` automatically.
3. Do not treat `students.schema.json` as core engine metadata.
4. Do not promote `DD_RULE_BINDING` rows until fields and named rules both resolve.
5. Capture runtime evidence only after explicit authorization for local read-only command runs such as `RULE PATHS`, `RULE STATUS`, `RULE LIST`, and `RULE SHOW ALL`.

Safe next work after DD-012:

```text
DD-013A
  Map workspace/relation source anchors and relation runtime evidence classes.

DD-013B
  Map tuple/browser relation-aware consumers.

DD-013C
  Draft DD_REL / DD_WORKAREA / DD_TUPLE catalog extensions.
```
