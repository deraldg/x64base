# DD-010 HELP Artifact and CMDHELPCHK Validation Plan v0

Date: 2026-05-27  
Status: REPORT_ONLY_PLAN_CREATED  
Input package: `ccode_homegrown_20260527-055727.zip`  
Boundary: no repository mutation, no runtime launch, no CMDHELP BUILD, no CMDHELPCHK execution, no HELP/META/CMDHELPCHK/catalog/DBF mutation.

## Purpose

DD-010 organizes the validation side of HELP and diagnostics for the data dictionary. DD-009 mapped the HELP/message/diagnostic surfaces; DD-010 turns that into a guarded validation plan.

The key distinction is now explicit:

```text
CMDHELP BUILD        = generated HELP DATA writer; mutating generated artifacts
CMDHELP              = report current HELP DATA; read-only after artifacts exist
CMDHELPCHK REFLECT   = reflected metadata validation; read-only validator
CMDHELPCHK ARTIFACTS = HELP DATA v2 artifact validator; read-only validator
CMDHELPCHK <dir>     = legacy commands.dbf/.dbt validator; compatibility lane
```

## Counts from static source inspection

```text
HELP/source anchor rows:        392
HELP artifact writer families:  4
Known HELP artifact names:      4
CMDHELP mode rows:              6
CMDHELPCHK mode rows:           4
Validation gate rows:           6
Catalog extension rows:         7
Artifact mention rows:          9
```

## Generated HELP DATA v2 artifact family

Source writer: `src/help/helpdata_export_dbf.cpp`.

The writer evidence identifies four current HELP DATA v2 output families:

| Artifact | Role |
|---|---|
| `help_artifacts.dbf` + `help_artifacts.dbt` | Memo-backed authoritative HELP DATA v2 artifacts. |
| `help_topic.dbf` | Browse-friendly topic summary. |
| `help_section.dbf` | Browse-friendly section index. |
| `help_line.dbf` | Browse-friendly fixed-width line fragments. |

These should map into data-dictionary catalog objects, but the dictionary must not silently trigger the writer.

## Legacy HELP compatibility lane

`CMDHELPCHK <dir> [limit]` still validates legacy `commands.dbf/.dbt` paths. That lane should be preserved for compatibility and historical validation, but it should not be confused with the default HELP DATA v2 dictionary path.

## Proposed dictionary additions

```text
DD_HELP_ARTIFACT
DD_HELP_TOPIC
DD_HELP_SECTION
DD_HELP_LINE
DD_MESSAGE
DD_VALIDATION_SURFACE
DD_HELP_LEGACY_LINK
```

These are DotTalk++ professional/runtime dictionary objects. They are not LabTalk/student overlays.

## Report-only validation sequence

1. Static source scan confirms HELP writer, HELP reader, CMDHELPCHK, message catalog, and diagnostic anchors.
2. Artifact contract is extracted from `helpdata_export_dbf.cpp`.
3. CMDHELP mutating paths are separated from CMDHELPCHK read-only validator paths.
4. Runtime validation is held until explicitly authorized and a runtime/help artifact directory is identified.
5. Only after validation should any HELP DATA outputs be converted into dictionary staging rows.

## Safety boundary

DD-010 did not run:

```text
CMDHELP
CMDHELP BUILD
CMDHELPCHK
DotTalk++ runtime
CMake/build tools
DBF/CDX/LMDB writers
```

DD-010 only scans source text in the uploaded repo package and emits reports.

## Recommended next step

DD-011 should be a **Rules / Constraints / xexpr Dictionary Link Map**, report-only. That will connect field constraints, rule catalog, xexpr, index/filter expressions, and validation messages into the same dictionary/provenance model.
