# Cascade Dual-Carrier Schema Parity Report

Status: explicit schema contract generated. Current physical runtime status, when available, is recorded in `runtime_status_latest.json`.

- SQLite tables: 34
- SQLite views: 9
- SQLite table rows: 330
- SQLite foreign-key field edges: 58
- Planned x64base DBFs: 43 (34 table mirrors + 9 materialized view snapshots)
- Canonical carrier SHA-256 unchanged: True

Relational constraints, defaults, indexes, and view SQL are complete in
`dual_schema_contract.json`. They are sidecar semantics until an x64base
runtime gate proves equivalent enforcement; DBF does not receive credit for
SQLite features it cannot natively enforce.

The earlier AUTODBF experiment was rejected for schema parity because value
inference converted declared SQLite TEXT identifiers (including account codes
and ZIP codes) to numeric fields and a NULL-only integer FK to character.

Run `build_x64base_mirror.dts` through the current DotTalk++ runtime, preserve
the transcript, and compare every emitted COUNT/FIELDS result before marking
the physical mirror runtime-observed.
