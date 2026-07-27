# Historical Database Migration — Empirical Progress Lane v1

Status: **active seed / proof gap assessment**  
Owner: Laboratory Campus / DotTalk++ / x64base  
Project: `project.labtalk.historical_database_migration`  
Ticket: `AIF-058`

## Purpose

Keep the AI Portal's understanding of the historical database migration project
grounded in observed artifacts. This lane separates registered intent from
runtime evidence, preserved transcripts, review-gated historical claims, and
future publication work.

## Current empirical assessment

| Surface | Evidence state | What is actually supported |
|---|---|---|
| Project and lane registration | complete | PDLC charter and `projects.yaml` registration parse and name the authority chain. |
| Runtime starters | strong | COBOL, CODASYL, SQLite, BIBLETALK, ERP, CASE, and MCC command surfaces exist and are registered. |
| Sample databases | strong | Bible SQLite and Cascade ERP include schemas, dumps, CSV exports, manifests, and validation figures. |
| DBF/xBase and CSV | **runtime-observed, transcripts preserved** | DBF→CSV→DBF proven LOSSLESS: origin and return legs identical in rows, fields, type letters, widths and decimals. CSV→x64base proven with type/NULL/long-name fidelity. `proof.pdlc.dbf_csv_dbf.roundtrip_lossless`, `proof.pdlc.csv_to_x64base.type_fidelity`. **CORRECTED 2026-07-26 — see note below: the previously cited evidence could not execute.** |
| xBase dialect ladder | **runtime-observed** | dBASE III (0x03) → FoxPro 2.6 → VFP → x64 → x64 VECTOR via `COPY ... AS`, in-engine, no external tool. 200 rows and 9 fields at every rung; `GPA` held `N(4,2)`; `DOB`/`ENROLL_D` held type `D` with values byte-identical end to end. Indexes migrate with the dialect (CNX/INX → CDX). `proof.pdlc.dialect_ladder.dbase3_to_x64`. **This surface was absent from the previous assessment.** |
| COBOL fixed records | **runtime-observed, hop closed** | `COBOL EXPORT` wrote 200 records; file is 22,200 bytes = 200 × 111 exactly. GnuCOBOL compiled clean, program ran, `RECORDS READ: 0000200`, exit 0. Record 1 identical read by COBOL and by DotTalk++. The copybook FD sums to 109 bytes — the dBASE III record length, field for field. `proof.pdlc.cobol_fixed_record.hop_closed`. |
| DBF ↔ SQLite | **capability gap, not demonstrated** | No DBF→SQLite row pump (needs field substitution in `SCAN`/`SQLITE EXEC` or a bulk command) and no SQLite-result→file path. Asserted explicitly, not hidden, in `tests/conversion/03_04_sqlite_capability_gap_v2.dts`. The SQLite legs of the chartered chain are untraversable from inside DotTalk++ in either direction. |
| CODASYL | teaching adapter | Set/ring traversal is implemented over DotTalk work areas; this is not a physical CODASYL store. |
| Historical cases | review-gated | CASE files load structurally, but source/media alignment and fact review remain open. |
| JSON and spreadsheets | design-stage for data, **implemented for schema** | `DDL CREATE DBF <flavor> <out.dbf> FROM <schema.json>` creates flavored tables from JSON today, with `DDL VALIDATE <schema.json> USING <validator.json>` alongside. Data seeding is the gap: DDL's own notes state `SEED CSV` is "recognized but not yet implemented". So JSON schema → table works; JSON/CSV → rows does not. |
| x64base vs SQLite benchmark | planned, **storage axis blocked** | The benchmark lane is chartered; no dedicated same-machine result set is yet authoritative. **Storage-footprint comparison must not be attempted until AIF-065 is corrected** — see the note below. |
| Website publication | planned | Public evolution/case pages exist, but the sample-database catalog and migration proof pages are not yet published. |
| GnuCOBOL acknowledgement | open gate | Add the acknowledgement before public promotion. |

## Correction recorded 2026-07-26 (run `COWORK-20260726-001`)

Four rows above changed state. Three moved forward on preserved evidence; one
moved **backward**, and that one matters most.

**The previously cited evidence could not execute.** The row now reading
"runtime-observed" read "runtime-proven locally", citing
`tests/conversion/05_roundtrip_dbf_csv_dbf.dts`. Checked against the live
command grammar, **none of the five scripts in `tests/conversion/` could run**:

- `EXPORT ... DELIMITER , QUOTES RFC4180` — those options do not exist
- `IMPORT ... SCHEMA <json> REJECTS <csv>` — IMPORT accepts only `<csvfile>`
- `SQLITE QUERY "..." INTO DBF` — no QUERY subcommand, no INTO-DBF path
- `BEGIN` — not a registered command; `#FIELD` substitution unimplemented
- all five wrote to `_drops/`, a directory that does not exist

They were not stale, they were **aspirational** — written against syntax the
engine does not have. Reading them looked like evidence; running one produced
a usage error immediately. The suite has been replaced (`*_v2.dts`,
`README_SUITE_REPAIR_V1.md`) and the capability is now genuinely demonstrated —
but the lane was carrying an unsupported claim, and that is worth recording
rather than quietly overwriting.

**The COBOL diagnosis was right about the gap, wrong about the cause.** The
transcript was indeed owed. But the blockers were not GnuCOBOL, which was
installed: a BUILD/RUN extension asymmetry in `src/edu/edu_cobol.cpp` (BUILD
appended `.exe` on Windows, RUN had no fallback, so the documented sequence
could not work immediately after a successful BUILD), and a stale `ASSIGN` path
in the sample program naming a location nothing had ever written to. Both fixed;
both invisible until the hop was actually executed.

**Two surfaces were missing from the assessment entirely.** The `COPY ... AS`
dialect ladder — the most on-thesis capability in the project — was unlisted.
And `DDL CREATE DBF ... FROM <schema.json>` undercuts "JSON is design-stage".

Method note: every finding here came from *executing* an artifact that had only
ever been *written*. Recorded as `lesson.career.a_script_never_run_is_not_evidence`.

## Storage-footprint caveat recorded 2026-07-26 (AIF-065)

**No storage or footprint claim about x64base may be made from the current tree.**

`BUILDLMDB` documents a size ladder — `TINY` 32M through `HUGE` 1G, plus
`MAPSIZE <n>` — and honours it when writing an environment. Two reader-side call
sites, `src/xindex/cdx_backend.cpp:189` and `src/xindex/lmdb_backend.cpp:80`,
then hardcode a 1 GiB mapsize, so an environment grows to 1 GiB the first time
its index is attached, regardless of what was requested.

Measured across `dottalkpp\data\lmdb`: every `data.mdb` in the tree holds one of
exactly two sizes — 128 MiB (71 live files) or 1 GiB (41 live files) — the two
constants in the source, with nothing in between. A 30,124-row table and a
9-row table both occupy 1,073,741,824 bytes.

So index footprint today is a function of **attach history**, not of schema,
row count, key width or operator choice. Any x64base-vs-SQLite storage number
taken now would measure that accident. Row-count, latency and correctness axes
are unaffected and remain runnable.

Full analysis, measurements and proposed correction:
[LMDB mapsize override lane](../maintenance/LMDB_MAPSIZE_OVERRIDE_LANE_V1.md).

Two caveats on that document, both deliberate. The *effect* is measured; the
*cause* is inferred from source plus size distribution and is not yet backed by
a transcript — two `stat` calls around a `BUILDLMDB CLEAN TINY YES` will settle
it. And the proposed fix rests on LMDB adopting the meta-page map size when
`mdb_env_set_mapsize` is not called, which must be confirmed against the linked
LMDB version before the change lands.

Related but separate: `BUILDLMDB CLEAN` archives each superseded environment
with no retention limit, which had accumulated ~50 GB across four lanes since
2026-06-25. That is documented behaviour without a documented bound, and it
filled the disk mid-reload on 2026-07-26.

## Maturity boundary

`M0` registration is complete. `M1` is partially complete. The component
surfaces for `M2`–`M5` exist, but their cross-format integration proof is not
closed. `M6` JSON/spreadsheet migration, `M7` benchmarking, and `M8` website
publication remain planned.

The project must not be described as a completed historical migration until one
canonical dataset has a reproducible crosswalk:

```text
COBOL fixed record -> DBF/xBase -> CSV/JSON -> SQLite -> x64base comparison
```

**Status of that chain as of 2026-07-26** — each leg, with its evidence:

```text
COBOL fixed record <-> DBF     PROVEN   200 recs, 22,200 = 200 x 111 exactly
dBASE III -> ... -> x64        PROVEN   lossless across 4 dialects + VECTOR
DBF -> CSV -> DBF              PROVEN   lossless, schema re-inferred exactly
CSV -> x64base                 PROVEN   types, NULLs, long names preserved
JSON schema -> DBF             WORKS    DDL CREATE DBF FROM <schema.json>
JSON/CSV -> rows via DDL       GAP      SEED CSV recognised, not implemented
DBF <-> SQLite                 GAP      no row pump, no result->file path
```

Four of seven legs are now runtime-observed with preserved transcripts. The
remaining two gaps are both SQLite-facing and both are unbuilt capability
rather than unproven capability — a distinction the lane should keep sharp.

Note the chain as chartered routes through SQLite, but the *historical* spine
is the dialect ladder, which needs no external database at all. Worth deciding
whether SQLite belongs in the canonical chain or is a parallel modern branch.

Each leg must record field mapping, row counts, rejected rows, checksums or
equivalent identity checks, and output correctness. Benchmark claims must also
record machine, versions, cold/warm state, workload, and equivalent results.

## SDLC fit

This evidence lane uses the LabTalk SDLC framework as its operating cycle. The
historical migration PDLC is the subject matter; SDLC governs how each slice is
selected, built, proven, documented, and maintained.

| SDLC stage | Historical migration application | Exit evidence |
|---|---|---|
| Analyze | Select one era transition, define the logical dataset, authority, and claim boundary. | Scope note, source inventory, truth-state labels. |
| Design | Define field crosswalks, identity rules, rejected-row policy, benchmark workload, and proof packet. | Reviewed mapping and acceptance criteria. |
| Code / assemble | Use existing COBOL, DBF/xBase, CSV/JSON, SQLite, CODASYL, and x64base surfaces; add only the narrow slice authorized by the gate. | Source/configuration inventory and reproducible runner. |
| Test / debug | Execute each conversion leg, compare counts and identities, run correctness checks, and capture cold/warm benchmark conditions. | Preserved transcript, result files, hashes or equivalent checks. |
| Document | Update the case, dataset, proof, AI Portal lane, and manual/website candidate while retaining reviewed-versus-planned labels. | Evidence-linked documentation packet. |
| Maintain | Re-run the crosswalk after schema, runtime, compiler, or benchmark changes; keep provenance and supersession explicit. | Refresh record, drift review, and current status. |

The SDLC review gate is deliberately between execution and publication: a
green runtime result is not automatically a historical claim or a public web
statement. The AI Portal lane reports the SDLC state and routes the smallest
sufficient evidence packet to the next gate.

## Evidence shelf

- [PDLC project charter](../maintenance/HISTORICAL_DATABASE_MIGRATION_PDLC_PROJECT_V1.md)
- [AI Portal task registry](../../labtalk/registries/ai_portal_tasks.yaml)
- [Project registry](../../labtalk/registries/projects.yaml)
- [Cascade ERP manifest](../../dottalkpp/data/cascade_precision_erp/manifest.json)
- [Cascade ERP README](../../dottalkpp/data/cascade_precision_erp/README.md)
- [COBOL runner](../../dottalkpp/data/scripts/COBOL_test.ps1)
- [CASE review](../cases/reports/CASE_REVIEW_V1.md)

### Preserved transcripts (2026-07-26, run `COWORK-20260726-001`)

- [COBOL fixed-record hop](../../labtalk/proofs/runs/20260726T233000Z_pdlc_cobol_fixed_record_hop.txt)
- [Historical dialect ladder](../../labtalk/proofs/runs/20260726T233000Z_pdlc_historical_dialect_ladder.txt)
- [DBF→CSV→DBF round trip](../../labtalk/proofs/runs/20260726T233000Z_pdlc_dbf_csv_dbf_roundtrip.txt)
- [CSV→x64base type fidelity](../../labtalk/proofs/runs/20260726T233000Z_pdlc_csv_to_x64base_type_fidelity.txt)

### Runnable proofs

- [Suite repair record](../../tests/conversion/README_SUITE_REPAIR_V1.md)
- [Dialect ladder](../../tests/conversion/11_historical_dialect_ladder_v1.dts)
- [COBOL hop](../../tests/conversion/12_cobol_fixed_record_v1.dts)
- [SQLite capability gap](../../tests/conversion/03_04_sqlite_capability_gap_v2.dts)

> The old link to `05_roundtrip_dbf_csv_dbf.dts` has been removed: that script
> cannot execute (see the 2026-07-26 correction above). Its replacement is
> `05_roundtrip_dbf_csv_dbf_v2.dts`, cited through the transcript instead.

## Next gate

Complete the Analyze and Design stages for the first canonical crosswalk, then
produce and preserve its Test/Debug proof packet. It should be
runtime-observed, independently rerunnable, and still clearly labeled local
until the PDLC review and publication gates are passed.

## Authority rule

Runtime/source artifacts define capability. Proof packets establish empirical
state. The AI Portal selects and explains that evidence; it does not promote
historical claims or website copy by itself.
