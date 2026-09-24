# AIF-169 -- Cascade differential battery: SQLSEL and REL vs SQLite (charter seed)

    status  : review-needed; lane seeded, NOTHING RUN under this number yet
    owner   : member.derald
    steward : member.ai.claude.cowork (run AIPR-20260920-001)
    claim   : coordination/aif/AIF-169.claim (2026-09-24, lane cascade_differential)
    origin  : owner, 2026-09-23: "two parallel (schemas) ... we will use for
              sqlsel and rel vs sqlite testing"

## 0. Prior art (walked 2026-09-24 -- AFTER the owner asked, not before)

The steward drafted this charter and only then was told "look for prior
art first, to see if its claimed" -- the second B2-shape miss in two
days (the first is recorded in ONBOARDING_REPORT_REVIEW R2). The walk
found three things that rescope this lane:

- **AIF-105 is the sole Cascade lane identifier** (its row says so in
  those words): `cascade_erp_metadata_etl_learning`, chartered in
  `docs/maintenance/CASCADE_ERP_METADATA_ETL_LEARNING_GOLD_STANDARD_LANE_V1.md`,
  claimed by `member.ai.codex.local`, with `member.ai.claude.cowork`
  already a Class A coworker of record. This lane does NOT reopen it.
- `project.labtalk.historical_database_migration` (projects.yaml:426)
  already names a lane **`benchmark_x64base_vs_sqlite`** -- "compares
  equivalent x64base and SQLite workloads" -- with no AIF number found
  attached to it. AIF-169 is proposed as that lane's number, scoped to
  the query-surface differential.
- AIF-105's intake row states the exact gap this lane fills: the
  43-object run "proves creation/import structure only; it does not
  prove field, value, NULL, constraint, index, relation, view, or
  round-trip parity." The differential battery IS that missing parity
  evidence, delivered as a downstream consumer of AIF-105's fixtures
  -- coworker posture per the AIF-070 precedent (participate, note it,
  leave the claim holder's lane theirs).

- **The case-study track was walked too (owner: "look in case studies
  too") and does not claim this** -- `dottalkpp/docs/cases/` has no
  cascade or sqlite mention anywhere. What it has is a CONSUMER:
  `CASE_HIST_070_ERP_SQL_AUTOID_INDUSTRIAL_SCALE.md` is a registered
  stub (`stub_registered`, `needs_source_review`, every section "To be
  developed", `source_docs: to_be_attached_or_reviewed`). This lane's
  teed transcripts and divergence findings are exactly the source
  evidence that stub is waiting to attach -- the database and the
  documentation co-developing, each dogfooding the other.

So: AIF-169 = the benchmark/differential slice, downstream of AIF-105,
consuming its fixtures, feeding parity evidence back to its ledger, and
feeding source material forward to HIST-070.

## 1. What exists (inventoried 2026-09-23; flavors and row counts NOT measured)

Three parallel materializations of one ERP dataset (Cascade Precision Mfg):

- `dottalkpp/data/dbf/cascade_dbf/` -- 43 CASCADE_* DBF tables: 34 base
  tables plus 9 materialized `v_*` views (AP/AR aging, available stock,
  BOM explosion, open sales orders, reorder alert, three-way match,
  trial balance, work order status). Owner, 2026-09-23: parallel schema
  with `cascade_og`.
- `dottalkpp/data/dbf/cascade_og/` -- per-table provenance sidecars:
  `.ddl.json`, `.indexes.json`, `.load.json`, `.schema.copy.json`.
- `dottalkpp/data/systems/cascade_erp/` (AIF-105's system bundle) --
  the same system three ways: `dbf/` + built `indexes/` (43 .cdx +
  .meta), `meta/` sidecars, and `sqlite/` (full dump, schema.sql,
  seed_data.sql, sample_queries.sql, per-table CSVs, checksums.sha256)
  plus `sqlite/x64base_mirror/` with `dual_schema_contract.json`,
  per-table `.schema.json`, materialized `views/*.csv`,
  `PARITY_REPORT.md`, and three dual-schema runtime proofs dated
  2026-08-10 (run lineage AIPR-20260810-002).

All the dbf/cascade_* content is UNTRACKED today. The engine links
SQLite natively (banner: "SQLite available: 1, version 3.50.4"), so the
third surface runs in the same process as the first two.

## 2. Method

The AIF-167 discipline carried over: CROSS-ORACLE IDENTITIES, not
parity diffs alone. The nine `v_*` views are the ready-made oracles --
each has a DBF materialization (cascade_dbf), a mirror CSV
(x64base_mirror/views), and a defining SELECT (schema.sql /
sample_queries.sql). One query, three answers, every aggregate anchored
to a non-relational count. Where AIF-167 proved REL/ENUM against SQLSEL
on pinocchio, this lane adds the external oracle pinocchio never had:
an engine this project did not write (the AIF-091 M1 lesson -- a
self-written round trip cannot distinguish agreeing-wrong from
correct). AIF-105's Gate 0 posture is honored: local structural mirror
evidence is NOT accepted as complete parity; this lane is how parity
gets measured rather than asserted.

Read rule inherited from the pinocchio dims work: flavor printed on
every open, tag attach proven (no silent CNX fallback), row-identical
results across surfaces as the gate.

## 3. Milestones (proposed, none authorized to run yet)

- M0  Fixture acceptance: measure what section 1 only inventories --
      flavor byte per table, row counts vs the SQLite side and the
      .load sidecars, checksums, and RECONCILE `dbf/cascade_dbf` vs
      `systems/cascade_erp/dbf` (same bytes or a fork?). Decide
      tracked-vs-untracked with the owner; a cascade zip restore point
      before any mutation (pinocchio precedent).
- M1  Read-only differential battery, script-first: the nine views as
      oracle queries, SQLSEL vs REL/ENUM vs sqlite, teed transcripts.
      Findings feed the AIF-105 ledger as the parity evidence its row
      names missing.
- M2  Divergence triage: any mismatch becomes either an engine finding
      or a documented semantic difference (NULL handling, collation,
      numeric width) -- recorded, never papered over.
- M3  (later, owner-gated) DML differential on disposable clones only,
      per the AIF-167 3b pattern.

## 4. Not claimed

That any table's flavor, count, or checksum matches its sidecar (M0's
job); that `dbf/cascade_dbf` and the AIF-105 system bundle are the same
bytes (M0 reconciles); that the 2026-08-10 mirror proofs still hold on
today's binary; that the `v_*` DBF materializations are current against
their base tables; that SQLSEL's semantics should match SQLite's where
the house has ruled otherwise -- divergence is a finding either way,
not automatically a defect; that this lane owns anything AIF-105
governs (metadata, ETL, migration, curation -- those stay with their
claim holder). Ships review-needed; the author does not self-approve.
