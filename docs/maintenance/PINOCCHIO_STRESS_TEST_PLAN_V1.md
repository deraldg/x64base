# Pinocchio — Engine Stress-Test Lane (Plan v1)

Codename: **Pinocchio** — "can the educational database be a *real boy*?"
Status: **MILESTONE — Phase 1 (performance at scale) PASSED at 1M / 5.5M on
2026-07-15.** Correctness green across load, ordered-by-key, SEEK (both parent
and child), secondary order, and predicate scan. See
`SESSION_CLOSEOUT_PINOCCHIO_PHASE1_2026-07-15.md`. **Phase 1.1 (per-command
timings) DONE** — captured via top-level REPL; headline: `TOP` is O(n) and owns
~115s of the ~116s battery while `SEEK`/`COUNT`/`SMARTLIST` are all sub-0.35s.
The ordered-navigation defect is now resolved in development: `TOP` on the
5,501,358-row ENROLL table moved from 66.09 s to 0.0013 s. Promotion review,
deleted-record semantics, build-stage timing, and fault injection remain open.
Scope of this phase: **performance at scale** (Phase 1). Fault injection
(concurrency, crash/recovery, durability) is Phase 2, defined but deferred.

## The question

MCC is a 200-student toy. Pinocchio asks whether the same x64 + CDX + LMDB
engine stays correct and reasonably fast when the data grows ~1,000× — real
mid-size-database territory. It is a capability test, not a correctness proof:
it does not establish ACID guarantees (those remain **Unverified**, per
`acid-and-glass-box`). It establishes whether the engine *performs like* a real
database at real volume.

## Target scale (Phase 1)

- **STUDENTS ≈ 1,000,000** rows (MCC schema: SID, LNAME, FNAME, DOB, GENDER,
  MAJOR, ENROLL_D, GPA, EMAIL).
- **ENROLL ≈ 5–8,000,000** rows (SID, CLS_ID), ~5–8 per student — the child
  side, where index-ordered walks and joins are exercised.
- Supporting dims (MAJORS, CLASSES) small.

Scale is parametrized in the generator; ramp with `-Students`.

## Isolation — Pinocchio never touches the MCC foundation

Pinocchio uses **its own lane directories** and is fully derived/disposable:

- Generated CSV → `dottalkpp/data/tmp/pinocchio/`
- Built tables → `dottalkpp/data/dbf/pinocchio/`
- Indexes → `dottalkpp/data/indexes/pinocchio/`
- LMDB envs → `dottalkpp/data/lmdb/pinocchio/`

**None of these publish.** Only the scripts and this plan are versioned; the CSV,
DBF, CDX, and LMDB output are gitignored like every other derived artifact. The
MCC sample set (`dbf/{og,x32,vfp,x64}`) is never read or written by this lane.

## The path

1. **Generate** (`gen_pinocchio_data.ps1`, PowerShell) — deterministic, seeded,
   streamed CSVs at the chosen scale. Record 1 is the MCC canary
   (SID `50000000`, `Taylor Quinn`) so the same freshness assertion holds at
   scale.
2. **Build** (`pinocchio_build.dts`) — `CREATE X64 <table> (…)` makes the x64
   structure using **advanced field types** (the `SID` key is the native integer
   `I`, not legacy `N`), then `IMPORT <csv>` bulk-loads the rows, then
   `CDX CREATE`/`ADDTAG` and `BUILDLMDB ... MAPSIZE nG`. `SET TIMER ON` captures
   build, import, and index times.

   Ingest maturity (maintainer-confirmed): **IMPORT and EXPORT are tested and
   fairly mature**; **CREATE is the intended structural create** (`status:
   supported`). **AUTODBF is deliberately off the critical path** — it needs
   more testing, so it is not the load-bearing step of a benchmark. x64 tables
   support advanced field types (I, Y currency, M memo, and more); Pinocchio
   uses `I` now and a later variant can push currency/datetime/double/vector.
3. **Measure** (`pinocchio_measure.dts`) — the timed query battery below,
   each command's elapsed printed by the shell timer, each result
   correctness-asserted.
4. **Collect** (`run_pinocchio.ps1`) — orchestrates the three, tees transcripts
   to `data/tmp/pinocchio/*.log`, and prints a summary table.

## The battery (Phase 1)

Macro operations whose elapsed time is meaningful at scale (single-row micro-ops
like one `SEEK` are too fast to time without a loop harness — that is Phase 1.1):

| # | Operation | What it measures |
| - | --------- | ---------------- |
| 1 | `COUNT` on STUDENTS | full physical scan throughput (rows/s) |
| 2 | `BUILDLMDB` per table | index build time + LMDB mapsize behavior |
| 3 | `SET ORDER TO TAG SID` + full `SMARTLIST ALL` | ordered traversal via LMDB |
| 4 | `SET ORDER TO TAG LNAME` + `TOP` + `SMARTLIST 20` | ordered seek-to-top cost |
| 5 | `LIST FOR MAJOR = "CSCI"` | predicate scan over 1M rows (large result) |
| 6 | ENROLL `SET ORDER TO TAG SID` + `SMARTLIST ALL` | 5–8M-row child ordered walk |
| 7 | `SEEK` a known SID on STUDENTS + ENROLL | point-lookup lands (correctness) |

## Pass / fail (first-run thresholds — tune after baseline)

Green if all hold; otherwise record the number and the first failure mode:

- **Correctness first.** STUDENTS `COUNT` == generated N; canary record 1 by SID
  reads `50000000 Taylor Quinn`; `SHOW COLUMNS` types are sane (SID numeric).
  A wrong count or canary invalidates the run regardless of speed.
- `BUILDLMDB` completes without a mapsize/`FAIL` error at the chosen MAPSIZE.
- Full ordered STUDENTS traversal completes and stays in tag order (spot-check).
- ENROLL child walk completes; no crash, no silent truncation.
- Provisional speed goals (revise once we have a baseline number, don't pre-judge
  the engine): build ≤ a few minutes for 1M; ordered scans stream, not stall.

A zero exit code is **not** proof — read the transcripts. The DotScript runner
reports unknown commands and continues, so confirm every `AUTODBF` / `CDX` /
`BUILDLMDB` line actually reported success, and that the counts are exact.

## Commands to confirm on the first trace run

Grounded in source (`cmd_create.cpp` and `cmd_import.cpp` both `status:
supported`, `cmd_set.cpp` SET TIMER, mcc transcripts) and the maturity notes
above. Still verify these the first time, since the `.dts` are **CANDIDATE /
REVIEW_BEFORE_EXECUTION**:

- `CREATE X64 <t> (…)` — table reports v64 and `SHOW COLUMNS` matches the spec
  (SID is `I`).
- `IMPORT <csv>` — header→field mapping is case-insensitive; confirm the date
  fields (`D`) accept the YYYYMMDD strings (else make DOB/ENROLL_D `C(8)`).
- `BUILDLMDB MAPSIZE 4G YES` — unit suffix accepted; a mapsize that holds
  1M–8M keys.
- `SET TIMER ON` output format (so the orchestrator can parse elapsed).

## Division of labor

Same as the cold-clone certification: **the AI builds the generator, scripts,
and thresholds; the maintainer runs `dottalkpp` on the real machine** (the host
lives outside this environment, and the databuild is PowerShell + the host-guard
anyway). We read the numbers together and record them in a session closeout.

## Historical engine benchmarks

Pinocchio now keeps a machine-readable historical ledger at
`PINOCCHIO_HISTORICAL_ENGINE_BENCHMARKS_V1.csv`. The initial baseline records
both Phase 1 timings and the ordered-navigation before/after proof. These are
engine-development baselines, not cross-hardware rankings.

### Ordered-navigation baseline

| Dataset / operation | Before | After | Improvement |
| --- | ---: | ---: | ---: |
| ENROLL 5,501,358 — `TOP SID` (paired nav run) | 66.09 s | 0.0013 s | 50,838× |
| ENROLL 5,501,358 — `BOTTOM SID` | 66.51 s | 0.0010 s | 66,510× |
| ENROLL 5,501,358 — first `SKIP` | 65.9 s | 0.0015 s | 43,933× |
| ENROLL 5,501,358 — `SKIP 1000000` | 87.1 s | 0.021 s | 4,148× |
| ENROLL 5,501,358 — `SKIP -1000000000` to top | 529 s | 0.11 s | 4,809× |
| ENROLL 5,501,358 — `TOP SID` (Phase 1 cross-run) | 72.169 s | 0.0013 s | 55,515× |
| STUDENTS 1,000,000 — `TOP SID` | 19.478 s | 0.001–0.002 s | 9,739–19,478× |
| STUDENTS 1,000,000 — `TOP LNAME` | 23.231 s | 0.001–0.002 s | 11,616–23,231× |

Correctness remained green: SID `TOP` lands on record 1 (`50000000 Taylor
Quinn`), LNAME order begins at `Anderson`, descending order swaps endpoints,
and the documented `SKIP` sequences and boundaries land correctly.

### Machine identity rule

The historical Phase 1 and navigation artifacts did not record manufacturer,
model, CPU, memory, or OS. Their `machine_type` is therefore `UNRECORDED`; the
current workstation profile must not be retroactively attached to them.

Future runs write `data/tmp/pinocchio/machine_profile.json`. The runner accepts
`-MachineType <label>` for a stable lab label and otherwise attempts Windows
CIM discovery with an environment fallback. A benchmark row is not comparable
until at least `machine_type`, engine state, dataset rows, operation, timer
source, and evidence path are populated.

The current observed workstation profile is retained in
`PINOCCHIO_MACHINE_PROFILE_CURRENT_V1.json` as an input for future runs only;
its `historical_run_binding` remains `UNVERIFIED`.

### Evidence boundary

Phase 1 retains the raw `measure_timed` transcript locally with SHA-256
`383FEC725E8ABA9D2F33A55CCEC78CB003B2BBDBD6DF7AD6E30B10AFD05A24A2`.
The navigation before/after values are preserved in the July 18 closeout, but
the raw after transcript was not located in the repository scan. The ledger
marks that distinction; a narrated closeout is not silently relabeled as a
retained raw transcript.

## Phase 2 (defined, deferred) — fault injection

The "behave like a real database under stress" axis: concurrent sessions,
crash-mid-write + reopen, and durability after forced termination. These target
exactly the guarantees the engine currently rates **Unverified**, so expect them
to surface known gaps. Run only against the Pinocchio lane (disposable), never
the MCC foundation. Scoped in a later plan revision.
