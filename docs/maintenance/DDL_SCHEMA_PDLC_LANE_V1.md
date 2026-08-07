# DDL Schema PDLC Lane v1

Status: active development lane; M1 flavor parity seed implemented; COPY
output-flavor repair registered.
Ticket: AIF-063.
Owner: member.derald.
Steward: Codex local agent, until reassigned by the owner.
Parent projects: `project.x64base.runtime`, `project.labtalk.pdlc`,
`project.ai_friendly`.

## Purpose

Bring `DDL` from a useful schema-definition command into a complete,
contract-backed JSON <-> DBF/xBase schema lane. The lane owns the PDLC for
`src/cli/cmd_ddl.cpp` and its companion schema, sidecar, validation, import, and
index-plan behavior.

The command is already registered and useful. It is not yet complete across all
DBF flavors or sidecars. This lane makes that honest and gives future agents a
single start point.

## Current Truth

Runtime/source anchors:

- `src/cli/cmd_ddl.cpp`
- `src/cli/cmd_ddl.hpp`
- `src/cli/schema_json_v1.schema.json`
- `src/cli/schema_loader.cpp`
- `src/xbase/dbf_create.cpp`
- `include/xbase.hpp`
- `src/cli/cmd_create.cpp`
- `src/cli/cmd_copy.cpp`
- `src/cli/cmd_autodbf.cpp`
- `src/cli/cmd_index.cpp`
- `src/cli/cmd_cdx.cpp`
- `src/cli/cmd_cnx.cpp`

Contract anchors:

- `docs/database/DATABASE_SAFETY_CONTRACT_V1.md`
- `docs/database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md`
- `docs/contracts/CONTRACT_REGISTRY_V1.md`
- `labtalk/ai_portal/SCOPE_CALIBRATION_SEED_V1.md`
- `labtalk/ai_portal/SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`

Observed current behavior after the 2026-07-26 M0/M1 seed:

- `DDL VALIDATE` parses the target schema and validator JSON, then enforces the
  in-tree `schema_json_v1` contract subset: required top-level fields, field
  enums and bounds, index declarations, index field references, and relation
  pair shape.
- `DDL CREATE DBF` parses a JSON `fields` array and routes physical DBF
  creation through `xbase::dbf_create::create_dbf`.
- `DDL CREATE DBF` supports explicit `MSDOS`/`DBASE`, `FOX26`/`FOXPRO`, `VFP`,
  and `X64` flavor tokens. It defaults to legacy `MSDOS`/`DBASE`.
- `SEED BLANK` appends records through `DbArea::appendBlank`, including X64
  record-count handling.
- `SEED CSV` is advertised but returns "not yet implemented".
- `EMIT SIDECARS` writes schema/load/index metadata sidecars with DBF flavor,
  logical field names, descriptor names, copied index declarations, and a
  metadata-only warning for indexes.
- JSON schema supports fields, indexes, and relations. `cmd_ddl.cpp` now uses
  fields and index declarations; relations remain sidecar/round-trip backlog.
- Companion COPY inspection on 2026-07-27 found that `COPY TO <dest> AS
  <flavor>` already performs logical DBF flavor conversion for `MSDOS`/`DBASE`,
  `FOX26`/`FOXPRO`, `VFP`, and `X64`; `COPY TO <dest>` remains a binary file
  copy. The repair risk is not flavor syntax. The risk is output honesty:
  x32-style output does not mean traditional xBase index/memo support. The
  supported indexing lane is x64base's own CNX path, and memo behavior remains
  stub/limited unless separately proven. Logical `COPY AS` also does not
  restore the source cursor, and converted output is intentionally data-only
  unless indexes are explicitly rebuilt later.
- Traditional x32/xBase support is split into its own proposed feasibility lane:
  `docs/maintenance/X32_TRADITIONAL_XBASE_SUPPORT_LANE_V1.md`. COPY R1 should
  link to that lane rather than expanding into traditional `.ndx`/`.mdx`/`.cdx`
  or `.dbt`/`.fpt` compatibility by default.

## PDLC Scope

### Analyze

Done for the seed: DDL is not fully compliant with JSON, DBF flavor creation,
memo semantics, index identity, CSV seeding, or schema validation. Indexes are
optional derived artifacts for table creation, but required for fast seek,
ordered navigation, unique constraints, relation acceleration, and compatibility
when the JSON schema declares them. For x32-style output, this means x64base
CNX indexing, not traditional xBase index-file support, unless another lane
proves and accepts that compatibility.

### Design

Design target:

1. Make `DDL` a schema orchestration command, not a second DBF writer.
2. Reuse `xbase::dbf_create::create_dbf` for physical DBF flavor creation.
3. Treat JSON `indexes` as a build plan and sidecar identity record, not as a
   silent promise that indexes exist.
4. Reuse the hardened AUTODBF CSV record parser/value conversion path for seed
   data rather than creating another CSV parser.
5. Preserve full logical field names in sidecars and detect DBF descriptor-name
   truncation/collision before writing.
6. Keep JSON validation, DBF physical creation, seed import, sidecar emission,
   and index build/attach as separately testable gates.

### Code

Planned source slices:

M0 - Validation truth:
- Wire `DDL VALIDATE` to the in-tree schema contract. Done in
  `src/cli/cmd_ddl.cpp` with internal `schema_json_v1` contract enforcement.
- Add negative tests for missing required fields, invalid type, and invalid
  index declaration. Done as runtime proof with invalid-name, invalid-type, and
  missing-index-field rejection.

M1 - Flavor parity:
- Add explicit flavor syntax for `MSDOS`, `DBASE`, `FOX26`, `FOXPRO`, `VFP`,
  and `X64`. Done in `src/cli/cmd_ddl.cpp`.
- Replace hand-written DBF header output with `xbase::dbf_create::create_dbf`.
  Done in `src/cli/cmd_ddl.cpp`.
- Preserve CREATE's X64 field-name fallback and metadata policy. Done for
  descriptor names and sidecars.

R1 - COPY output flavor repair:
- Treat `src/cli/cmd_copy.cpp` as a companion repair surface for DDL/schema
  parity because COPY is the runtime conversion command users will naturally
  reach for after schema creation.
- Preserve the current distinction between binary `COPY TO` and logical
  `COPY TO ... AS <flavor>`.
- Repair or explicitly warn when COPY encounters memo-bearing DBFs, because
  memo behavior is stub/limited and x32-style output does not imply traditional
  `.dbt`/`.fpt` support.
- Restore the source work-area cursor after logical `COPY AS`.
- Keep index creation explicit: converted tables may carry a plan or warning,
  but CNX indexes must not be silently reused or rebuilt without an explicit
  mode.
- Add focused COPY flavor regression coverage for memo warnings, long-name
  collision, unsupported type down-conversion, source-cursor preservation, and
  `AS X64 VECTOR` behavior.
- Link any future request for traditional x32 indexes or memo files to
  `X32_TRADITIONAL_XBASE_SUPPORT_LANE_V1`; do not fold that work silently into
  COPY R1.

M2 - Sidecar normalization:
- Emit `.ddl.json`, `.load.json`, `.indexes.json`, and copied schema from one
  canonical data model.
- Record DBF flavor, encoding, date/null/logical policies, logical names,
  descriptor tokens, and truncation/collision decisions.

M3 - CSV seed:
- Implement `SEED CSV` using the shared/hardened CSV record semantics.
- Support rejects output with row number, field, value, and error code.

M4 - Index plan:
- Parse JSON `indexes`. Done for sidecar metadata.
- Emit index identity even when no physical index is built. Done with
  `metadata_only` and `physical_index_built: false`.
- Add an explicit build mode before creating CNX/CDX/LMDB artifacts.
- Do not silently reuse stale or incompatible indexes.

M5 - Round-trip proof:
- Add an inspect or round-trip path: DBF plus sidecars -> canonical JSON ->
  DBF, with a machine-readable loss report.

### Test / Debug

Minimum gates:

- Unit/schema tests for JSON validation.
- CLI smoke for each supported flavor.
- Memo semantics smoke for memo-bearing schemas, clearly distinguishing current
  stub/limited support from traditional `.dbt`/`.fpt` compatibility.
- COPY flavor smoke for `MSDOS`/`DBASE`, `FOX26`/`FOXPRO`, `VFP`, `X64`, and
  `X64 VECTOR`, including current memo warning/stub behavior and CNX-only index
  expectations.
- CSV seed smoke with quoted commas, doubled quotes, embedded newlines, blank
  values, numeric/date/logical conversion, and rejects.
- Index-plan smoke proving absent indexes are reported as planned/unbuilt and
  built indexes carry compatible identity.
- Regression registered under the DotTalk++ regression runner before promotion.

Current focused runtime proof:

- Build: `cmake --build D:\code\ccode\build --target dottalkpp --config Debug`
- Regression: fresh Debug executable with
  `--script dottalkpp\data\scripts\ddl\ddl_schema_flavor_regression.dts`
- Validation proof: both classic and X64 schema fixtures emit
  `DDL VALIDATE: OK` with `contract = schema_json_v1`.
- Negative validation proof: invalid schema emits `DDL VALIDATE: FAILED` with
  invalid identifier, bad field type, and undeclared index-field reference.
- Markers: `DDL_T1_CLASSIC_ID:.T.`, `DDL_T2_CLASSIC_LABEL:.T.`,
  `DDL_T3_X64_LONG_NAME:.T.`, `DDL_T4_X64_LABEL:.T.`
- File readback: classic `0x03` with one row; X64 `0x64` with two rows;
  sidecars carry copied index declarations marked metadata-only.

### Document

Update together:

- `@dottalk.usage` in `src/cli/cmd_ddl.cpp`
- command HELP/CMDHELP harvested output
- schema JSON contract docs
- AI Portal task row and dashboard row
- relevant database contracts if new sidecar/index policy becomes binding

### Maintain

Do not let `DDL` become a parallel implementation of CREATE, AUTODBF, COPY,
memo, or index logic. The command owns orchestration and schema authority; the
runtime subsystems own physical storage behavior.

## Scope Calibration

operating_mode: active development lane.
change_class: schema/file-format orchestration with data-import and index
metadata impact.
build_target: `dottalkpp` runtime.
product_profile: DEVELOPMENT first; later PROFESSIONAL/EDUCATIONAL publication
after proof.
index_profile: inherited plus explicit NONE/LEGACY/LMDB gates.
scope_reason: DDL touches DBF creation, JSON schema interpretation, sidecars,
seed data import, and possible index build plans.
minimum_gate_set: analyze/design record, source contract preflight, focused
runtime build, DDL regression, sidecar readback, and AI Portal closeout.
deferred_gates_and_residual_risk: public website/manual promotion, full
cross-format migration proof, and destructive migration flows stay separate.

## Next Gate

M3/M4 continuation package:

1. Repair or warn on COPY memo semantics, document that x32-style output uses
   x64base CNX indexing rather than traditional xBase index support, and
   restore the source cursor after logical `COPY AS`; register focused COPY
   flavor regression.
2. Implement `SEED CSV` through the shared CSV parser/value conversion lane.
3. Add an explicit `BUILD INDEXES`/equivalent mode before creating physical
   CNX/CDX/LMDB artifacts from JSON declarations.
4. Add sidecar/round-trip coverage for `relations`.
