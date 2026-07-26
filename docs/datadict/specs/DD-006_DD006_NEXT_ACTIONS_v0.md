# DD-006 Next Actions v0

## Immediate next step: DD-007

Create a report-only Python 3.12 extractor skeleton.

Scope:

```text
Input:
  corrected repo zip or extracted repo root

Output:
  physical_dictionary_manifest_v0.json
  extraction summary markdown
  extraction warnings CSV

Allowed evidence:
  source files
  CMake/config files
  schema files
  scripts as files
  prior DD source maps

Not allowed yet:
  launching DotTalk++
  opening live DBFs
  creating DBF catalog tables
  writing HELP/META/CMDHELPCHK
  changing source files
```

## DD-007 source-scan targets

Start with facts that can be captured without runtime execution:

```text
sources[]
  source file rows for physical dictionary anchors

tables[]
  only declared or candidate rows from schemas/scripts/source if available

fields[]
  FieldDef / FieldSpec / FieldNamePlan structural evidence

field_name_policy[]
  policy source facts from include/xbase/field_name_policy.hpp

schemas[]
  schema sidecar file inventory

warnings[]
  unresolved/missing/not-yet-runtime facts
```

## DD-008 later

After DD-007 is green, design a runtime-read-only probe plan:

```text
Open sample DBFs read-only
Capture table/header/field/memo/index facts
Emit runtime_proof[] rows
Compare runtime facts against declared/source facts
```

That should still avoid promoted catalog mutation until reviewed.
