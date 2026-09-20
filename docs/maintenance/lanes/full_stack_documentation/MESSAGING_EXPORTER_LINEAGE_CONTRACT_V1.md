# Messaging Exporter Lineage Contract v1

Status: active descriptive contract.

## Decision

`dottalkpp/tools/help/generate_runtime_message_catalog_seed_v1.py` is the
canonical exporter for new runtime message seed candidates. It reads the
compiled message registries and writes reviewed import CSVs; it does not load
or mutate DBF, CDX, or LMDB stores directly.

`tools/messaging/export_message_catalog_phase6.py` is preserved as historical
report-only evidence for the earlier Phase 6 layout. It is not a default path
and must not be used to create new canonical seed candidates.

## Machine-Readable Lineage

The paths, hashes, roles, and lifecycle dispositions are recorded in
`selfdoc/messaging_exporter_lineage_v1.json` and mapped to `META-015` and
`META-016` in `selfdoc/metadata_system_registry_v1.json`.

## Authority Boundary

Compiled runtime registries are source authority. Exported CSVs are candidates.
Catalog load, HELP rebuild, or publication promotion requires a separate
reviewed action and fresh post-load proof.

## Verification

Run `python tools/selfdoc/validate_documentation_lineages.py` from the repository
root. Validation checks both exporter paths, SHA-256 values, lifecycle states,
and the non-default gate on the historical exporter without executing either
exporter.
