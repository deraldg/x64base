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

## 3. Sequencing -- CORRECTED 2026-09-21: the gate already closed

This section shipped 2026-09-21 claiming the lane was BLOCKED BEHIND ED-01a
and P4.0b. THAT WAS STALE ON ARRIVAL: both evaluator defects were repaired on
2026-09-03 and P4.0b was COMPLETED in the same run -- SQLsel WHERE evaluates
committed-truth TupleRows through the {TRUE,FALSE,ERROR} seam, EVALDIFF is
22/22 green under a fail-closed exact-vector validator, and both are
DEFAULT-SUITE PROMOTED (EVALUATOR_DIFFERENTIAL_HARNESS_SCOPE_V1.md,
"2026-09-03 repair result"; SQLSEL_PDLC_LANE_V1.md phase register, P4.0a/b).
The error: the charter author cited the 2026-07-30 handoff's phase state
without re-reading the scope doc's September section -- the OI-024 shape,
recorded here so the correction travels with the claim.

CONSEQUENCE: this lane is START-READY. The R21 reasoning above stands (only
the row-stateless TupleRow path fans out) -- it is now a satisfied
precondition, not a blocker. PERF-1 can begin immediately. PERF-2 still waits
on PERF-1's exit (parallelizing a 208 us/row interpreter rents cores to
multiply overhead) and on the OQ-P1..P3 rulings where marked. (The hash-set
IN fix and validate-before-materialize repairs from AIF-167's findings landed
2026-09-21, commit 54d1a7231 -- SQLsel-lane work that removed algorithmic
cliffs; this lane lowers the constant and multiplies it.)

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

#### PERF-1a AUTHORED 2026-09-21 (pending build + regression + measurement)

Source read found the constant's largest single component NOT in the AST walk
but in view construction: `exprglue::make_record_view` (expr_tuple_glue.hpp)
built a CiIndex (two hash maps over every column) per call and then copied
BOTH the TupleRow and that index BY VALUE into three separate std::function
closures -- three deep copies of every cell string, per row evaluated, at
every `evaluate_tuple_predicate` call site (WHERE scans, join ON loops, HAVING,
DML selection) plus the projection loop, which built the view even when every
select-list item was a direct column and nothing read it.

The slice: `TupleViewContext` (expr_tuple_glue.hpp) builds the index once per
column LAYOUT and rebinds rows by pointer assignment; accessor bodies are the
same code reading through the pointer, so semantics are identical, including
ProducedAbsent, the EMPTY-identifier path, and ISNULL's deliberate refusal. A
layout guard (column count + first/last names) rebuilds on shape change.
`evaluate_tuple_predicate` gains a context overload; eight hot loops hoist a
context (chain ON, chain WHERE, two-table ON, join WHERE, HAVING, single-table
scan, UPDATE, DELETE); the projection loop binds lazily and skips the view for
all-direct select lists. Cold one-shot sites keep the old signature through a
wrapper that is itself cheaper (no row copies). EVALDIFF's own harness path
(cmd_evaldiff.cpp) is deliberately UNTOUCHED so the differential oracle stays
byte-identical.

HONEST EXPECTATION: this removes per-row-eval 3x row deep copy + 4x hash-map
build/copy + 3x std::function churn; it does NOT touch build_tuple_from_spec's
all-column string materialization, the per-row alias rename loop, or the AST
walk itself. Predicted 1.5-3x on the 3a battery's WHERE scans (wider rows gain
more); the 208 -> 15-30 us target still needs PERF-1b. The measured claim
comes from the G-P1 rerun, not from this paragraph.

PERF-1b backlog, pinned to lines during the same read (sqlsel_statement.cpp
post-slice numbering): build_tuple_from_spec materializes every column per
predicate row (:2996); the alias rename loop reconcatenates every column name
per row (:3002); evaluate_store_expression RE-COMPILES the value expression
per UPDATE row (:3722); db_tuple_stream::passes_filter_on_tuple and
tuple_graph_cursor still call the copying make_record_view (browser FOR and
REL-graph paths, outside this battery's gate).

#### PERF-1a MEASURED 2026-09-21 -- G-P1 GREEN, 3-6x on the converted loops

Build eac74271 (Sep 21 2026 17:10:36). Correctness first: all six SQLsel
regressions PASS including EVALDIFF 22/22 exact, then the FULL 3a + star
batteries reran teed (sha256:A86C83C4... relational_readonly 20260921T184455Z;
sha256:B7696D5F... star_readonly 20260921T203206Z) with EVERY identity
IDENTICAL -- I1-I13 exact, path reports unchanged, refusal texts intact. The
gate's terms were met before any ratio was read.

Measured ratios, pre-PERF-1a baseline -> this build:

    R3c join + WHERE filter over 5.5M   1907.7 s -> 306.9 s   6.2x
    R4b function-WHERE scan (1M)         394.7 s ->  95.0 s   4.2x
    R6a UNION                            832.7 s -> 207.0 s   4.0x
    R5a bounded pure-IN                 1084.2 s -> 336.6 s   3.2x
    R6b INTERSECT                        757.3 s -> 255.6 s   3.0x
    R6c EXCEPT                           763.8 s -> 263.9 s   2.9x
    R3a seek join (simple-equi path)     274.0 s -> 243.3 s   ~1.1x
    R5c full-scale IN                    564.1 s -> 608.8 s   ~0.9x
    R4a native COUNT FOR (control)        ~26 s  ->  28.3 s   ~1.0x
    Star S1-S3 (seek joins, GROUP BY)    169.9/207.2/394.2 -> 195.5/175.0/397.4

The SHAPE is the finding: converted WHERE loops gained 3-6x, with the WIDEST
rows (R3c's combined join tuples) gaining most -- three deep copies per row
priced by row width, exactly as diagnosed. Untouched paths are flat: the
native control, the tag walks, the simple-equi seek joins (fluctuating inside
the fixture's documented +/-15%), star GROUP BY, and R5c, whose cost is the
inner materialization + hash-set build that PERF-1a deliberately did not
touch. The 1.5-3x prediction missed LOW; recorded per discipline.

CONSEQUENCE for the constant: simple-WHERE is now ~95 us/row (was 208). The
dominant remaining term is build_tuple_from_spec's all-column materialization
per predicate row -- the top PERF-1b backlog item above. OQ-P3's premium
question should be re-asked against the ~95 us number, not 208.

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
