# DD-017 Static DBF Header Parser and Physical Projection Skeleton v0

## Status

Report-only skeleton package. No DotTalk++ runtime was launched, no build was run, no repo files were changed, and no project DBF/CDX/LMDB/memo data was opened or mutated.

## Purpose

DD-017 implements the first offline/static DBF header parser for the data-dictionary lane. It is designed to read DBF-like files from an explicit path and emit physical dictionary projections for:

- `DD_TABLE_VERIFY`
- `DD_FIELD_PHYSICAL`
- `DD_SOURCE`

It deliberately does **not** claim runtime proof. It produces static byte-parse evidence only.

## Why this matters

The data dictionary needs a low-risk lane between source/schema evidence and runtime transcript proof:

```text
source anchor -> declared schema -> static DBF parse -> runtime open transcript -> reviewed catalog fact
```

DD-017 fills the static DBF parse rung.

## Parser included

Tool:

```text
tools/dd017_dbf_header_parser.py
```

Supported static layouts:

```text
STANDARD_DBF_HEADER_STATIC
  Conventional DBF header and 32-byte descriptors at offset 32.

X64BASE_EXTENDED_HEADER_STATIC
  Observed x64base-style extended prefix with descriptor area at offset 96,
  64-bit mirrors for record count / header length / record length,
  and 64-bit descriptor offset/length fields.
```

## Sample run

DD-017 includes two synthetic parser fixtures:

```text
sample_inputs/standard_fixture.dbf
sample_inputs/x64style_fixture.dbf
```

Sample output counts:

```text
tables parsed: 2
fields parsed: 5
```

These are parser fixtures only. They are not project runtime data and not runtime proof.

## Static source context

A source-anchor review found 80 DBF/header/field/memo/CDX-related source context candidates in the corrected repo package. These are included only as orientation for future integration; DD-017's parser remains standalone and report-only.

## Trust boundary

Static DBF parse evidence can support candidate dictionary rows, but it cannot replace runtime proof. Promotion still requires later comparison against DotTalk++ runtime output such as `USE`, `FIELDS`, `DBAREAS`, `MEMO`, `INDEX`, `CDX`, and related transcript evidence.

## Files included

- `tools/dd017_dbf_header_parser.py`
- `sample_inputs/standard_fixture.dbf`
- `sample_inputs/x64style_fixture.dbf`
- `sample_output/dd017_sample_static_projection_v0.json`
- `sample_output/dd017_sample_tables_projection_v0.csv`
- `sample_output/dd017_sample_fields_projection_v0.csv`
- `dd017_parser_module_map_v0.csv`
- `dd017_physical_projection_schema_v0.csv`
- `dd017_static_evidence_ladder_v0.csv`
- `dd017_trust_gates_v0.csv`
- `dd017_source_anchor_review_v0.csv`

## Boundary preserved

No source edits, no build, no runtime launch, no HELP/META/CMDHELPCHK mutation, no catalog/DBF/CDX/LMDB mutation, and no project data mutation occurred.
