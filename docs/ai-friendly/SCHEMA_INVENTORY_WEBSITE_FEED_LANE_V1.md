# Schema Inventory Website Feed Lane v1

Status: **planned implementation / read-only generator**  
Owner: x64base runtime / AI Portal / website  
Tool: `schema_inventory`

## Contract

The C++ tool scans `D:\code\ccode` and considers schema-bearing files under
`docs/`, `include/`, `src/`, and `dottalkpp/`. It emits deterministic JSON to
`docs/generated/schema_inventory.json`. The website can copy or consume that
feed into a dedicated schema catalog section; publication remains a separate
review gate.

Run from the repository root:

```text
schema_inventory D:\code\ccode D:\code\ccode\docs\generated\schema_inventory.json
```

The feed is an inventory, not a claim that every schema is runtime-authoritative.
Each item carries a relative path, detected kind (`json-schema`, `sql`, `dbf`,
or `schema-document`), and byte size. Source/runtime authority and review state
must remain visible in the website section.

## SDLC gates

Analyze the scan boundary; design the JSON and website projection; build the
tool; test deterministic ordering and exclusion rules; document provenance;
maintain the feed after schema changes. Do not publish generated output without
the normal website content and source-authority review.
