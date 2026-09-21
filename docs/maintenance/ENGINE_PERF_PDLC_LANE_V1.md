# Engine Performance Lane -- charter seed (AIF-168)

    Status:  SEED / REVIEW-NEEDED. Owner: member.derald.
    Author:  member.ai.claude.cowork, run AIPR-20260920-001. Date: 2026-09-21.
    Claim:   coordination/aif/AIF-168.claim
    Origin:  owner question during the Phase 3a rerun, with Task Manager open on
             a saturated single core and an idle disk: "how do we utilize the
             entire machine instead of one core?"

## 1. Lane identity and the measured premise

The engine's execution profile is MEASURED, not assumed (AIF-167, 2026-09-20/21,
teed transcripts + operator observation): memory-resident (D: disk 0% active,
0 KB/s during a 5.5M-row scan -- the ~225 MB fixture set is cache-resident after
first touch), SINGLE-CORE (one saturated logical processor reads as ~11% on this
box), and COMPUTE-BOUND at ~200-400 us/row -- roughly half a million
instructions per row of TupleRow construction, per-cell string materialization,
and AST-walking predicate interpretation. Zero hardware wait.

Calibrated single-thread rates (benchmarks ledger, PIN-REL3A rows):
simple-WHERE scan ~208 us/row; function-WHERE ~345 us/row; correlated glue
~427 us/row; native COUNT FOR ~26 us/row; CDX-seek join processed 5.5M
candidates in 274 s. The gap between 26 us (native scan loop) and 208-345 us
(SQLsel row pipeline) is the first target: it is pure software.

Mission: make the machine's capacity available to the engine, in two slices
whose product is the payoff -- cheaper rows, then more cores multiplying the
cheaper rows. Indicative ceiling on the observed box: 200 us -> ~15 us/row
(~13x) x ~16 cores = the 3a battery's 20-minute identities in seconds.

## 2. Decisions already made (adopted here, not reopened)

- **R21 (AIF-120, runtime-proven): navigation alone corrupts a concurrent
  walk** -- SEEK moves the shared cursor even when nothing writes; the unit of
  serialization is the handler body. Consequence adopted as this lane's first
  law: PARALLEL WORKERS NEVER SHARE A DbArea. Each worker owns a private row
  source (own file handle, own LMDB read transaction). The shared-cursor hazard
  is designed out, not locked around.
- **R11 (AIF-120): the house threading vocabulary is ratified** -- worker
  threads produce immutable values, identified and cancellable (TaskId,
  terminal states), lifetime by RAII join (AsyncSession is the worked example).
  This lane extends the vocabulary from one worker to a bounded read-only pool;
  it does not invent a second idiom.
- **dev-08: DBF is fixed-width.** Record n lives at header + n*reclen, so
  recno-range partitioning is exact arithmetic with no coordination.
- **LMDB supports lock-free concurrent readers by design**; one read
  transaction per worker is the intended use, not a trick.
- **The SQLsel manual disclaims row order without ORDER BY**, so range-ordered
  merge of parallel partitions is semantics-preserving; ORDER BY already
  materializes and sorts after the scan.
- **Writes stay single-lane** (R11.4/R21 serialization; TBJ/WAL single-writer;
  AIF-160 group commit). This lane parallelizes READ-ONLY row streams and
  nothing else. DML never enters the pool.
- **The flag pattern is SET INDEXTXN's** (default OFF, env-seedable for CI,
  runtime override) and **the proof pattern is EVALDIFF's**: parity between
  two implementations is asserted on exact counts, because two paths agreeing
  on a wrong answer must be impossible to read as green.
- **R23/R25 (SQLsel lane): gold by default; platinum priced and deferred.**

## 3. Sequencing -- blocked, and by exactly what

BLOCKED BEHIND ED-01a and P4.0b (SQLsel charter). The classic evaluator IS a
shared DbArea cursor (R21 hazard embodied); only the row-stateless TupleRow
path can fan out. P4.0b migrates SQLsel's WHERE to that path once EVALDIFF is
green with CORRECT verdicts. This lane starts the day that gate closes, and
not before. (The hash-set IN fix and validate-before-materialize repairs from
AIF-167's findings are SQLsel-lane work, not this lane -- they remove
algorithmic cliffs; this lane lowers the constant and multiplies it.)

## 4. The two slices

### PERF-1 -- the per-row constant (target: 208 -> ~15-30 us/row)

Reduce the SQLsel row pipeline cost with NO semantic change: field-offset
resolution hoisted out of the loop (resolve once per statement, not per row);
cell access without per-cell std::string allocation (views over the record
buffer, materialize only what the select list emits); predicate execution
tightened from AST-walk toward a flat op sequence. NULL-READY seams (SQLsel
R29) are respected -- the kind tag stays.
Gate G-P1: the FULL 3a + star batteries rerun with identical identity results
(I1-I13 exact), and the ELAPSED ratio per statement is the datum. A single
divergent count fails the slice regardless of speed. Oracle unchanged (SQLite
gates stay green).

### PERF-2 -- SET PARALLEL <n>: partitioned read-only scans

A bounded worker pool; recno-range partitions; per-worker private row source
(R21 law); per-partition partial results merged as monoids (COUNT/SUM/MIN/MAX
add, GROUP BY hashes merge, row batches concatenate in range order); ORDER BY
sorts the merged set exactly as today. Joins fan out over OUTER ranges with
per-worker seek cursors into LMDB read transactions. DML and any statement
holding a write fence run exactly as today (pool bypassed).
`SET PARALLEL <n>` default OFF; `DOTTALK_PARALLEL` env seed; the access-path
report line grows a `workers=<n>` field so every transcript names its mode.
Gate G-P2: differential OFF-vs-ON -- the same battery both modes, identities
EXACT both modes, plus a torn-partition probe (partition boundaries land
mid-CSCI-cluster) and a DELETED-flag probe per partition. The speedup curve
(1, 2, 4, .. n workers) is recorded in the benchmarks ledger; sublinear is
expected and honest, wrong is impossible to miss.

### Platinum, priced and deferred (R25 pattern)

Parallel join pipelines, concurrent GROUP BY, work stealing, NUMA placement.
Not scheduled; revisited when PERF-2's curve flattens.

## 5. Open rulings, placed where they block

- OQ-P1 (blocks PERF-2 design freeze): worker count default when ON --
  physical cores, logical processors, or fixed cap? MEASURED BASELINE
  (owner's box, Get-CimInstance 2026-09-21): Intel Core Ultra 9 185H,
  16 cores / 22 logical processors -- a HYBRID part: 6 P-cores (HT, 12
  threads) + 8 E-cores + 2 LP E-cores. Three core classes running the same
  interpreter at different rates means "one worker per core" is not one
  number on this machine. Proposed: default 6 (P-core count), and let the
  PERF-2 speedup curve (1,2,4,6,8,12,16,22) decide empirically whether
  E-cores help or drag; never assume topology, always read it at startup.
- OQ-P2 (blocks PERF-2): does REL's linear child walk join the pool, or stay
  single-lane until its own slice? Proposed: stay out in v1 (REL walks the
  child via the relation engine, a different row source).
- OQ-P3 (blocks PERF-1 exit): is 26 us/row (native COUNT FOR) the floor to
  chase, or does the typed TupleRow pipeline accept a stated premium (2-3x)
  for its type fidelity? Proposed: accept the stated premium; record it.

## 6. What this lane refuses

No speculative caching layers, no query planner, no rewrite of storage. The
engine's honesty properties (reported paths, reported counts, fail-closed
refusals) are load-bearing; any optimization that would trade a report away
is out of scope by definition.
