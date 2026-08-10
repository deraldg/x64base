# Cascade Precision Mfg ERP -- system bundle

Layout ruled by member.derald 2026-08-10 (recorded in
`docs/maintenance/CASCADE_ERP_METADATA_ETL_LEARNING_GOLD_STANDARD_LANE_V1.md`).
One home for everything Cascade; the template for future systems (MCC,
biblebase, pinocchio) if it earns it.

| Dir | Contents | Authority |
| --- | --- | --- |
| `sqlite/` | The sealed V1 package, moved INTACT: carrier, full dump, `checksums.sha256`, README, queries, 34 table CSVs, `x64base_mirror/` generator output | **V1 data/provenance authority** (AIF-105) |
| `dbf/` | 43 `CASCADE_*.dbf` -- 34 table mirrors + 9 `CASCADE_v_*` materialized view snapshots | generated projection |
| `meta/` | 172 generated JSON sidecars (`*.ddl/indexes/load/schema.copy.json`) | **measured mirror metadata** (source for the .dtschema) |
| `indexes/` | `*.cdx` physical indexes (built by `scripts/cascade_erp_build_indexes.dts`) | derived |
| `lmdb/` | LMDB environment (local, never committed) | derived |
| `schema/` | `CASCADE_ERP.dtgraph` (attributed relation graph: fields, tag orders, relations -- NOT `.dtschema`, which is the engine's WORKSPACE snapshot format), `CASCADE_ERP.graph.mmd` (58-edge Mermaid), `CASCADE_ERP.graph.html` (browser viewer, Mermaid CDN) | generated projections; regenerate via `tools/cascade_erp/generate_dtschema.py` |
| `scripts/` | `cascade_erp.dts` (DBF env), `cascade_sql.dts` (SQLite env), `cascade_erp_build_indexes.dts` (physical tag build) | authored + generated |

Entry points, from the data root (`datarun.ps1` cwd):

    DOTSCRIPT systems/cascade_erp/scripts/cascade_erp.dts     && x64base side
    DOTSCRIPT systems/cascade_erp/scripts/cascade_sql.dts     && SQLite side

Retired locations (all files were untracked; moves invisible to git):
`data/cascade_precision_erp/` -> `sqlite/`; `data/dbf/cascade_erp/` -> `dbf/` +
`meta/`. Legacy duplicates `data/dbf/cascade_dbf/` and `data/dbf/cascade_og/`
remain in place pending triage disposition (support-rule: RETIRE candidates,
owner + AIF-105 steward approval).
