# Manualgen Review Disposition Contract v1

Status: active for the post-HELP-refresh 49-topic review queue.

## Purpose

Convert the explicit curation review queue into evidence-backed section-factory
inputs without treating missing evidence as permission to publish or silently
turning aliases, diagnostics, and source-mined phrases into commands.

## Evidence order

Each review topic is joined to:

1. exact physical HELP command identity;
2. active public `META_SYSCMD` identity and handler;
3. topic status, primary source, and confidence;
4. existing canonical topic targets;
5. the explicit disposition policy in
   `tools/manualgen/manualgen_lib/disposition.py`.

## Dispositions

| Disposition | Count | Meaning |
| --- | ---: | --- |
| `INCLUDE_WITH_RUNTIME_EVIDENCE` | 20 | Active public SYSCMD identity permits a candidate section while retaining original topic status. |
| `INCLUDE_PARTIAL_HELP_REFERENCE` | 3 | Physical HELP identity exists; include only in the visibly partial-reference packet. |
| `MERGE_ALIAS_TO_CANONICAL` | 9 | Do not create a duplicate section; record one or more validated canonical topic targets. |
| `ROUTE_SOURCE_FACT_APPENDIX` | 6 | Preserve a source-mined phrase as evidence, not as a command. |
| `ROUTE_DEVELOPER_DIAGNOSTIC_APPENDIX` | 2 | Preserve diagnostic/documentation-provider contracts outside public command prose. |
| `DEFER_NO_RUNTIME_IDENTITY` | 9 | Retain the topic but withhold it from section generation until stronger runtime authority exists. |

All 49 topics have exactly one disposition. Missing and extra policy rows are
fatal. Every alias target must already exist. Runtime-backed inclusions must
join an active public SYSCMD row. Partial HELP inclusions must join an exact
physical HELP command.

## Section-factory outputs

The passing candidate contains 462 unique topics:

- 239 developer command-reference topics;
- 173 FOX compatibility topics;
- 29 education concepts;
- 18 runtime-evidenced supplemental topics;
- three partial HELP-reference topics.

These totals comprise the 439 supported base topics plus 20 runtime-backed and
three partial-HELP review dispositions. Alias, appendix, and deferred rows do
not enter section-factory packets.

## Current proof

`MANRUN-20260717T230554Z-DB3F2DC8` reports:

- dispositions: 49/49;
- approved section topics: 462;
- missing policy rows: 0;
- extra policy rows: 0;
- invalid canonical targets: 0;
- invalid runtime-backed inclusions: 0;
- invalid HELP-backed inclusions: 0;
- status: `PASS`.

## Boundary

The outputs are section-factory candidates. They do not replace the existing
25 section sources, combined manual, canonical harvest, accepted MAN catalogs,
reader pointer, or any external publication. Promotion requires a separate
human-view comparison and authorization gate.
