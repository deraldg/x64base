# Pinocchio — Engine Stress-Test Lane (Plan v1)

Codename: **Pinocchio** — "can the educational database be a *real boy*?"
Status: **MILESTONE — Phase 1 (performance at scale) PASSED at 1M / 5.5M
(2026-07-15); the Phase 1.3 indexing/scale hardening is COMPLETE and proven
(2026-07-18 → 07-19).** Correctness green across load, ordered nav, SEEK,
secondary order, and predicate scan. Every fix is in development only
(`D:\code\ccode`, existing branch — nothing promoted to `C:\x64base`/GitHub),
each proven with a hash-bound directly-teed transcript under
`labtalk/proofs/runs/`:

- **Phase 1.2 — ordered nav** (`TOP`/`BOTTOM`/`SKIP`/`GO`/`GOTO`): 66.09 s → ms
  on 5.5M. (`SESSION_CLOSEOUT_PINOCCHIO_NAV_PERFORMANCE_2026-07-18.md`)
- **Phase 1.3a — read-only verb sweep** (43 verbs): flat verbs proven flat
  1M→5.5M; scan verbs characterized; `SEEK` caught as the hidden O(n). (sha
  `9769C1D8…`)
- **Phase 1.3b — destructive profile**: `COPY`/`BUILDLMDB`/`REINDEX` timed;
  `PACK` (0.54 s) / `ZAP` (0.03 s) efficient; the `DELETE`-under-active-order
  surcharge quantified. (sha `0294344D…`)
- **Phase 1.3c — SEEK + SET FILTER**: keyed `MDB_SET_RANGE` `SEEK` (both
  directions + not-found), 57 s → ms; the `SET FILTER TO … = <bareword>`
  string-literal correctness bug fixed. (sha `CF599664…`, `7B791221…`)
- **Phase 1.3d — DELETE/RECALL index-write batching**: per-row LMDB commits
  batched into one transaction; `DELETE FOR` active-order 65.4 s → 37.8 s,
  `RECALL ALL` batched (≈ baseline). (sha `0294344D…`, `0D15DADF…`)
- **Polish — `AGGS ALL`** single-pass COUNT/SUM/AVG/MIN/MAX (~4× vs four verbs;
  proven sha `5E9E7315…`). That run also surfaced a shared aggregate-`FOR`
  unquoted-string-literal bug, now fixed (normalize like `COUNT FOR`) — the
  confirm re-run is the one open proof.
- **Durability — table-buffer write-ahead log (2026-07-19).** `COMMIT`/`ROLLBACK`
  were RAM-only; now a durable, `fsync`'d redo `.tbj` makes committed
  table-buffer transactions **crash-recoverable** (replayed on `USE`), with
  `DELETE` transactional too and the retained-edit history preserved. Three
  phases, each proven (sha `938D4EC3…` / `16B938E4…` / `FBA1FC92…`). This is the
  first delivery on the **Phase 2 durability/crash-recovery axis** (below). See
  `SESSION_CLOSEOUT_TABLE_BUFFER_WAL_2026-07-19.md` +
  `TABLE_BUFFER_WAL_DESIGN_2026-07-19.md`.

**Remaining:** promotion review toward `C:\x64base` (maintainer-gated); the rest
of Phase 2 fault injection (concurrency, crash-mid-write durability on indexed
tables — the WAL's open hardening items) below. Full per-verb numbers:
`PINOCCHIO_SCALE_VERB_BENCHMARKS_V1.csv`; narrative:
`PINOCCHIO_SCALE_VERB_RESULTS_2026-07-18.md`; roll-up:
`SESSION_REPORT_PINOCCHIO_INDEXING_SCALE_2026-07-18.md`.

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

The historical Phase 1 and navigation run *transcripts* did not self-record
manufacturer, model, CPU, memory, or OS. On 2026-07-18 the maintainer attested
(with a CPU-Z 2.20.2 report) that a single workstation ran the **entire**
x64base / Pinocchio project — both the July 15 Phase 1 stress test and the
July 18 navigation before/after runs. The ledger's `machine_type` is therefore
`Alienware m16 R2 / Core Ultra 9 185H` with `machine_binding =
MAINTAINER_ATTESTED`: attributed by maintainer declaration, **not** captured
inside each run's own output. The distinction is preserved deliberately — a
future run that auto-captures a *different* profile overrides the attestation
for that run.

The workstation is an **Alienware m16 R2**: Intel **Core Ultra 9 185H**
(Meteor Lake; 16 cores / 22 threads, the successor to the mobile i9 line — not
a literal i9 part), **64 GB DDR5-5600**, dual graphics (**NVIDIA RTX 4070
Laptop 8 GB** + **Intel Arc** iGPU), Windows 11 Pro Build 26200.8875. The
project tree and all pinocchio fixtures live on **D: = Samsung 970 EVO 1 TB
NVMe** — relevant provenance for I/O-bound and Phase 2 durability runs. Full
detail is in `PINOCCHIO_MACHINE_PROFILE_CURRENT_V1.json`
(`historical_run_binding: MAINTAINER_ATTESTED`).

Future runs still write `data/tmp/pinocchio/machine_profile.json`. The runner
accepts `-MachineType <label>` for a stable lab label and otherwise attempts
Windows CIM discovery with an environment fallback. A benchmark row is not
comparable until at least `machine_type`, engine state, dataset rows, operation,
timer source, and evidence path are populated.

### Evidence boundary

Phase 1 retains the raw `measure_timed` transcript locally with SHA-256
`383FEC725E8ABA9D2F33A55CCEC78CB003B2BBDBD6DF7AD6E30B10AFD05A24A2`.

The navigation after-fix evidence is now a **directly-teed runner transcript**,
produced on the host by `run_pinocchio_nav_teed.ps1` (which runs each proof
script through `datarun`'s top-level `--script` path so per-command `SET TIMER`
fires) and hash-verified against the ledger:

| Log | SHA-256 | Ledger rows |
| --- | --- | --- |
| `labtalk/proofs/runs/nav_defect_after_teed_20260718T142513Z.log` | `AD1E6A4437E5517DDB8E713DA0E84DE9AF02D29223132ABAE0D3FEE68020DADD` | PIN-HIST-001,002,003,006,007,008 |
| `labtalk/proofs/runs/nav_filter_boundary_after_teed_20260718T142513Z.log` | `F520E661EB4685ADBFF3E015AE998B976E6026B3BCBB9527F0798329993F8AA3` | PIN-HIST-004,005 |

Ledger status for these rows is `RAW_TEED_TRANSCRIPT`. This supersedes the
interim chat-sourced capture `20260718_pinocchio_nav_after_capture_v1.md`, which
remains only as a readable `PIN-HIST → line` map.

Encoding caveat (load-bearing for the hash): the teed logs are **UTF-16LE with
BOM and embedded ANSI color codes** — the raw PowerShell console capture, left
untouched so it stays a *raw* transcript. Decode UTF-16 to read them. They must
**not** be re-encoded, stripped, or line-ending-normalized, or the recorded
SHA-256 drifts; `.gitattributes` marks `labtalk/proofs/runs/*.log` as `binary`
to prevent that.

## Phase 1.3 — indexing / scale verb sweep

Phase 1.1 timed the query battery and found `TOP` was the O(n) outlier; Phase 1.2
fixed ordered nav (`TOP`/`BOTTOM`/`SKIP`/`GO`/`GOTO`). Phase 1.3 systematically
sweeps the *remaining* command verbs that are sensitive to indexing and scale, to
confirm which stay flat and expose which still scan. It runs the same battery on
`STUDENTS` (1,000,000) and `ENROLL` (5,501,358) so flat-vs-linear shows up as the
ratio of the two `ELAPSED` values.

Source classification (2026-07-18, from `src/cli`):

| Class | Verbs | Scale behavior |
| --- | --- | --- |
| FLAT — O(1) / O(log n) | `COUNT` (no filter, header `recCount`), `GO n` / `GO TOP` / `GO BOTTOM`, `TOP`, `BOTTOM`, `SKIP ±N` (unfiltered CDX cursor) | Must not grow ~5.5× STUDENTS→ENROLL |
| LINEAR — O(n) | `COUNT FOR`, `COUNT` under `SET FILTER`, `SUM`/`AVG`/`MIN`/`MAX`, `LIST`/`LIST FOR`, `LOCATE`/`CONTINUE`, `SCAN…ENDSCAN` | Expected to grow ~with the row ratio |
| SENTINEL — *should* be O(log n), is O(scan-distance) | `SEEK` (and `LOCATE`) | Currently walks the CDX cursor linearly (`cmd_seek.cpp:210-298`) instead of a keyed range-seek |

Correction to the earlier shorthand that "`COUNT` was the problem": plain `COUNT`
is O(1) — it returns the DBF header `recCount()` (`cmd_count.cpp:407`). The costly
cases are `COUNT FOR <cond>` and `COUNT` under an active `SET FILTER`, both of
which abandon the header and run the full selector (`cmd_count.cpp:330,394`).

The headline finding is `SEEK`: even on the CDX/LMDB backend it holds a cursor but
linearly walks `first()`→`next()` comparing each key, so seeking a key near the end
of a 5.5M-row order is a near-full index walk. This is the same defect class as the
fixed `TOP`/`BOTTOM`/`SKIP` and is the top optimization target after this sweep.

(SEEK sentinel above is **resolved** — see Phase 1.3c below.)

### Sequencing (all phases complete + proven)

1. **Read-only sweep (Phase 1.3a) — DONE.** `pinocchio_scale_readonly.dts` /
   `run_pinocchio_scale_teed.ps1` (sha `9769C1D8…`). Non-mutating; 43 verbs on
   both tables. Result: flat verbs stayed flat 1M→5.5M; scan verbs O(n); `SEEK`
   exposed as the hidden O(n). It is a **multi-minute** run (every LINEAR verb
   makes a full pass — tens of seconds each on ENROLL is expected, not a fault);
   each `ELAPSED` (from `SET TIMER ON`) is the datum.
2. **Destructive profile (Phase 1.3b) — DONE.** `pinocchio_scale_destructive.dts`
   / `run_pinocchio_destructive_teed.ps1` (sha `0294344D…`). Clones `STUDENTS`
   into a disposable `SCR_DESTR`, times `COPY`/`BUILDLMDB`/`DELETE FOR`/
   deleted-aware `COUNT`/`RECALL ALL`/`REINDEX CDX`/`PACK`/`ZAP`, and `ERASE`s
   it — the fixtures are only *read*, so **no lane rebuild is required** (this
   avoids the deleted-smoke desync risk). `PACK`/`ZAP` efficient; `DELETE` active
   surcharge quantified (linear-in-deletes, ~2.5 ms/row — not O(n²)).
3. **Sentinel + correctness (Phase 1.3c) — DONE.** `SEEK` now takes a keyed
   `MDB_SET_RANGE` fast path (`seekRecnoUserKey`) for exact seeks in **either**
   direction, with full fall-through to the linear walk for prefix/deleted/miss
   (behavior-preserving); near-last `SEEK` 57 s → ms, not-found fast, descending
   fast (lands on smallest-recno duplicate). `SET FILTER` now normalizes unquoted
   RHS string literals like `COUNT FOR`. `FIND` (contains) and `LOCATE` (arbitrary
   predicate) legitimately stay O(n). Closeouts:
   `SESSION_CLOSEOUT_PINOCCHIO_SEEK_FIX_2026-07-18.md` (sha `CF599664…`),
   setfilter proof (sha `7B791221…`).
4. **DELETE/RECALL index-write batching (Phase 1.3d) — DONE.** A bulk
   write-transaction mode on `CdxBackend` (with a **bulk-aware `setTag`** so the
   per-field capture cannot open a conflicting second transaction / deadlock),
   passed through `IndexManager`, wrapping the DELETE/RECALL loops with chunked
   (10k) commits. `DELETE FOR` active-order 65.4 s → 37.8 s; `RECALL ALL`
   batched (≈ order-cleared baseline). Closeout:
   `SESSION_CLOSEOUT_PINOCCHIO_DELETE_BATCH_2026-07-19.md`
   (sha `0294344D…`, `0D15DADF…`).
5. **Polish — `AGGS ALL` (2026-07-19) — DONE (one confirm re-run open).**
   `AGGS ALL <expr>` computes COUNT/SUM/AVG/MIN/MAX in one scan (~4× vs the four
   verbs) — proven (sha `5E9E7315…`: values matched, 19.5 s vs 75.4 s). That run
   also surfaced a shared aggregate-`FOR` bug (unquoted string literals read as
   identifiers → `COUNT=0`); fixed via `normalize_agg_predicate` in both
   `run_agg` and `run_agg_all`, matching `COUNT FOR`/`SET FILTER`. The re-run to
   confirm `AGGS ALL … FOR MAJOR = CSCI` → `COUNT=90700` is the single remaining
   proof. Closeout: `SESSION_CLOSEOUT_PINOCCHIO_AGGS_ALL_2026-07-19.md`.

Source touched across Phase 1.3 (all in `D:\code\ccode`, existing branch):
`cmd_seek.cpp`, `cmd_setfilter.cpp`, `cmd_aggs.cpp`, `cmd_delete.cpp`,
`cmd_recall.cpp`, `cdx_backend.{hpp,cpp}`, `index_manager.{hpp,cpp}`.

## Phase 2 — fault injection (durability axis: FIRST DELIVERY landed)

The "behave like a real database under stress" axis: concurrent sessions,
crash-mid-write + reopen, and durability after forced termination. These target
exactly the guarantees the engine rated **Unverified**. The **durability /
crash-recovery** slice of this axis now has its first real delivery — the
table-buffer write-ahead log (below). Concurrency and broader forced-termination
testing remain scoped for a later revision. Run only against disposable tables,
never the MCC foundation.

### Durability — table-buffer write-ahead log (WAL)  [DONE + proven]

Before: table buffering, `COMMIT`, and `ROLLBACK` were **RAM-only** — `COMMIT`
wrote through to the DBF at commit time with no log and no `fsync`; `ROLLBACK`
dropped the in-memory buffer; no recovery; a crash could leave the DBF behind the
(LMDB-durable) CDX index. The journal hooks existed only as no-op stubs.

Now: a durable append-only redo log (`<dbf>.tbj`, text/line format, records
`U <recno> <priority> <H|S> <field>:<hex>` / `D <recno> <priority>`) with the
standard redo-WAL protocol.

| Phase | What | Proof (teed sha) |
| --- | --- | --- |
| **A** | Durable redo log: append during edits; on `COMMIT` write the `C` marker and **`fsync` before** the DBF apply, delete after; `ROLLBACK` discards. Full-fidelity records preserve every retained edit + priority + history/single mode. | `938D4EC3…` |
| **B** | Crash recovery-on-open: `USE` replays a committed `.tbj` into the DBF (idempotent), discards an uncommitted one, removes the log. | `16B938E4…` |
| **C** | `DELETE` routed through the buffer/log (transactional, deferred to `COMMIT`, discarded on `ROLLBACK`, replayed on recovery). Buffer-off `DELETE` keeps the Phase 1.3d batched-index write-through path. | `FBA1FC92…` |

Enabled only under `TABLE BUFFER PERSISTENT` (RamJournal); default behavior
unchanged. The multiple-retained-edits-per-field history capability is preserved
and demonstrated (`TABLE BUFFER HISTORY ON`; a field edited three times keeps
three retained records, `COMMIT` lands the highest-priority one). Files, phases,
and honesty boundaries: `SESSION_CLOSEOUT_TABLE_BUFFER_WAL_2026-07-19.md`; full
design: `TABLE_BUFFER_WAL_DESIGN_2026-07-19.md`.

**Open hardening (non-blocking, documented):** (1) a real DBF `fsync` after
replay/commit — blocked only by `std::fstream` not exposing the OS handle
portably; the residual window equals the engine's existing no-DBF-fsync
durability. (2) CDX/LMDB index reconciliation after a buffered commit/recovery —
`COMMIT` does no incremental CDX maintenance (pre-existing for buffered
`REPLACE`), so an indexed table needs a `REINDEX` after a buffered commit. These
are the last mile to full durability on indexed tables; broader ACID remains
**Unverified** per `acid-and-glass-box`.

### Phase 2 — remaining (deferred)

Concurrent sessions and forced-termination durability beyond the WAL slice, run
only against the disposable lane. Scoped in a later revision.
