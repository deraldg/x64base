---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260804-012
  recorded_at_utc: 2026-08-04T07:55:00Z
  agent:
    provider: Anthropic
    product: Cowork (Claude)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: DBF-native tracking layer (dogfood x64base for portal state)
  project:
    id: project.ai_systems.integration
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 05f049b57
  authorization:
    requested_by: maintainer
    scope: charter the DBF-native tracking tables + migration + derivation (design only, no build)
  report:
    path: docs/maintenance/TRACKING_STATE_DOGFOOD_LANE_V1.md
    kind: lane_charter
---

# Tracking-State Dogfood -- lane charter (v1)

Status: **proposed / Phase-0 design.** No build. Claim an AIF and sign Phase-0
before any source. Schema-first, exactly like `SYSRULING`: the steward authors the
table specs; a maintainer builds and seeds (the sandbox cannot run the engine).

Parent: AI Systems Integration SDLC (**AIF-086**, M1 -- must not claim M2 without
owner acceptance). Builds on: `SYSTEM_SCHEMA_MAP_AND_NORMALIZATION_V1.md` (the
divide), `ruling_schema.hpp` / `RULING_STATE_DOGFOOD_V1.md` (the precedent, one
table), AIF-050 (the run model), AIF-042 (`@dottalk.file`), AIF-045 (identity),
AIF-052 (BBS).

## Thesis (one line)

Give the document/task/project/lane tracking layer its own x64base tables so the AI
Project stores its OWN governance in the database it builds, and every report/
dashboard/current-work view DERIVES from those rows. Authored state drifts; derived
state cannot. The engine already does this for identity, boards, and rulings -- this
turns it on the project's own process.

## Design rules (carried from the precedent)

1. **Table = state, markdown = argument.** These tables hold what is short and
   machine-answerable (keys, ids, status, timestamps, one-line note). The long
   prose (the intake Notes cell, a proof's evidence essay) stays in the markdown/
   YAML it is good at. This deliberately avoids a FIFTH claimant on the 64-bit memo
   work (AIF-070 / 082 6.10 / 083 F5); `NOTE` is one line, never the argument.
2. **Append-only where history matters** (runs, status transitions), current state
   = highest timestamp per key -- same as SYSPOST / SYSRULING.
3. **Every row is attributed** through `SYSMEMBER` ids (identity spine) and
   gate-able through `SYSPERM` (e.g. `lane.create`, `run.record`).
4. Physical names <= 10 chars; 64-bit ids/epochs `N(20,0)`; enums small `N`; bools
   `L`; `VFROM/VTHRU/ROWVER` where durable. Namespace `dottalk::portal::schema`,
   stored under `data/metadata/portal/` alongside `SYSRULING`.

## Proposed tables

### SYSLANE -- the AIF lanes (from the intake queue + claim files)

| Field | Type | Meaning |
|---|---|---|
| ID | N(20) | row id |
| LKEY | C(16) | lane key, `AIF-087` (unique) |
| TITLE | C(160) | short title (prose Notes stay in the intake markdown) |
| OWNERID | N(20) | -> SYSMEMBER (usually member.derald) |
| STEWARDID | N(20) | -> SYSMEMBER (the AI steward) |
| PROJECT | C(48) | project id, `project.x64base.runtime` |
| SDLCLANE | C(24) | design / code / test / ... |
| STATUS | N(2) | 0 proposed / 1 active / 2 partial / 3 landed / 4 closed / 5 retired |
| CLAIMED | L | a `coordination/aif/LKEY.claim` exists |
| ANCHOR | C(160) | primary evidence doc path |
| OPENAT | N(20) | epoch opened |
| CLOSEAT | N(20) | epoch closed (0 = open) |
| ROWVER | N(20) | version stamp |

### SYSRUN -- the five-role run records (from `ai_runs.yaml`, AIF-050)

| Field | Type | Meaning |
|---|---|---|
| ID | N(20) | row id |
| RKEY | C(48) | run id, `AIPR-20260804-004` / `COWORK-20260804-001` |
| MEMBERID | N(20) | -> SYSMEMBER (the acting member) |
| ROLE | C(24) | implementer / steward / author |
| OWNERID | N(20) | -> SYSMEMBER |
| COMMITID | N(20) | -> SYSMEMBER (committer) |
| AUTHORID | N(20) | -> SYSMEMBER (authored_by) |
| PLANID | N(20) | -> SYSMEMBER (planned_by) |
| PROJECT | C(48) | project id |
| STATUS | N(2) | 0 active / 1 closed |
| STARTAT | N(20) | epoch started |
| BRANCH | C(48) | git branch |
| HANDLE | C(48) | handle_binding (`MAINTAINER_ATTESTED`) |
| REPORTID | C(48) | ai_report_audit report_id |
| ROWVER | N(20) | version stamp |

### SYSRUNLANE -- run <-> lane crosswalk (a run touches many lanes; mirror SYSROLEPERM)

| Field | Type | Meaning |
|---|---|---|
| RUNID | N(20) | -> SYSRUN.ID |
| LANEID | N(20) | -> SYSLANE.ID |

`current_by_lane` becomes a derived query: newest SYSRUN per SYSLANE via SYSRUNLANE.

### SYSPROOF -- the proof ledger (from `proofs.yaml`)

| Field | Type | Meaning |
|---|---|---|
| ID | N(20) | row id |
| PKEY | C(64) | proof key, `proof.bbs.m4_serve` |
| LABEL | C(160) | one-line label |
| STATE | C(24) | runtime_observed / source_defined / validated / design_intended |
| LANEID | N(20) | -> SYSLANE (0 if none) |
| SOURCE | C(160) | source/evidence doc path |
| OBSAT | N(20) | epoch observed (0 = not yet) |
| ROWVER | N(20) | version stamp |

### SYSTASK -- operational tasks (from `ai_portal_tasks.yaml`)

| Field | Type | Meaning |
|---|---|---|
| ID | N(20) | row id |
| TKEY | C(48) | task key |
| TITLE | C(160) | short title |
| ASSIGNID | N(20) | -> SYSMEMBER |
| STATUS | N(2) | 0 open / 1 in_progress / 2 done / 3 returned / 4 parked |
| CHANNEL | C(24) | pseudo_chat / intake / ... |
| LANEID | N(20) | -> SYSLANE (0 if none) |
| DUEAT | N(20) | epoch due (0 = none) |
| DONEAT | N(20) | epoch done (0 = open) |
| ROWVER | N(20) | version stamp |

## Cross-links (why this closes the graph)

Every id above resolves into the spine that already exists: `OWNERID/STEWARDID/
MEMBERID/ASSIGNID -> SYSMEMBER`; a lane/run creation can `POST` to a governance
`SYSBOARD` thread (accountability) and carry `SYSPOST.RUNID -> SYSRUN.RKEY`,
`SYSPOST.REFGRANT -> SYSGRANT`. So identity (who), BBS (announced + accountable),
and tracking (what/where) become one referential store instead of three
representations that must be kept in sync by hand.

## Migration + derivation

1. **Seeder (one-time, idempotent):** read the authored registries and write rows --
   intake-queue markdown -> SYSLANE; `ai_runs.yaml` -> SYSRUN + SYSRUNLANE;
   `proofs.yaml` -> SYSPROOF; `ai_portal_tasks.yaml` -> SYSTASK. Attribution comes
   from the existing `@dottalk`/AIF-050 records. Idempotent by key (upsert on
   LKEY/RKEY/PKEY/TKEY).
2. **Write surface (CLI):** new commands mirroring `USER`/`BBS` -- `LANE ADD|STATUS`,
   `RUN RECORD|CLOSE`, `PROOF ADD`, `TASK ADD|DONE` -- each writes a row, gated by
   `agent_permitted` and optionally auto-posting to a governance board. This is the
   "one lifecycle": work -> a command writes a row -> views derive.
3. **Derivation:** `build_reports.py` reads FROM the DBF tables instead of parsing
   markdown/YAML (behind a flag until proven), so the dynamic gateway already in
   place serves derived-from-DBF reports. The AIF-087-not-shown gap disappears at
   the root: a landed lane IS a SYSLANE row with SYSRUN rows, so it cannot be
   missing from a view that queries the table.
4. **Transition:** dual-read during proof (author still edits YAML/MD, seeder
   re-imports); flip the system-of-record to DBF once the derived reports match the
   authored ones; then generate a human-readable MD projection FROM the tables (like
   the website projections) so humans keep a readable copy that cannot drift.

## Phase-0 decisions (owner)

| # | Question | Note / recommendation |
|---|---|---|
| A | System of record | DBF as SoR with a derived MD projection (recommended, kills drift) vs dual-write with MD authoritative until proven |
| B | Memo ceiling | keep prose in markdown (table=state, sheet=argument) so v1 has NO 64-bit-memo dependency (recommended) vs block on AIF-070 |
| C | v1 table set | SYSLANE + SYSRUN + SYSRUNLANE first (they drive the reports and fix the drift we hit); SYSPROOF + SYSTASK second -- or all five now |
| D | Write surface | new CLI commands (`LANE`/`RUN`/`PROOF`/`TASK`) now vs seeder-only migration + continued MD editing until the read path is proven |
| E | Accountability | auto-POST lane/run creation to a governance SYSBOARD thread (recommended: the BBS becomes the audit log) vs no board coupling |
| F | Permissions | which `SYSPERM` gates writes (`lane.create`, `run.record`, `proof.add`) and who holds them (owner + stewards) |
| G | Derivation cutover | when `build_reports.py` switches its source to DBF (behind `--source dbf` until parity is proven against the YAML render) |

## Non-goals / governance

- No build, seed, or runtime in this charter. Schema-authoring only; maintainer
  builds and seeds (sandbox glibc cannot run the engine).
- Does NOT claim AIF-086 M2 architecture; this is M1 discovery/design.
- Does NOT remove the authored registries until the derived path is proven at parity.
- No identity, BBS, or engine behavior changes; these are new SYS* tables + a seeder
  + optional CLI, all additive.

## Next steps

1. Claim an AIF for this lane (host-side).
2. Owner signs Phase-0 A-G.
3. Author the schema headers (`portal/tracking_schema.hpp`) mirroring
   `ruling_schema.hpp`; then the seeder; then the derived read path in
   `build_reports.py` behind a flag; then the CLI write commands. Each step is its
   own gated slice with a smoke test (per the AIF-085 rule, run the test before the
   commit).
