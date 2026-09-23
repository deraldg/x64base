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

#### PERF-1b slice 1 AUTHORED 2026-09-21 (pending build + regression + measurement)

Source read of build_tuple_from_spec found the materialization constant is
mostly NAME RESOLUTION, not value reading. Per predicate row the spec path:
re-concatenates and re-parses the constant spec string; re-resolves the source
area by scanning every open work area (uppercase/basename churn per area);
resolves every field name THREE times per column (twice in its own body at
tuple_builder.cpp:336/:359, a third time inside getFieldAsString) -- and
resolve_field_index_std allocates two strings per field COMPARED, so a
10-field table pays ~600 allocations per row before any value is read. The
sqlsel scan then re-concatenated every alias-prefixed column name per row.

The slice: TupleBuildPlan (tuple_builder.hpp/.cpp) -- compile_tuple_plan runs
the constant half once (same parse, same resolution, same refusal texts,
emitted at compile time instead of on row 1); build_tuple_from_plan reads
values through precomputed 1-based indices: db.get(field1) + rtrim + overlay +
memo resolve, byte-identical to the spec path's output. build_tuple_from_spec
itself is UNTOUCHED -- every other caller keeps the proven path. sqlsel
converts pass 1 (predicate rows; prototype carries the alias-prefixed names,
retiring the per-row rename loop) and pass 2 (projection), compiled at the
same execution points the per-row calls occupied so current-area-relative
resolution is unchanged. Fragment order for multi-area specs moves from
unordered-set iteration to first-touch order; it was never specified.

HONEST EXPECTATION: removes per-row parse + area scan + 3x per-column
resolution + rename concats; keeps per-value get/rtrim/memo and the AST walk.
Predicted 1.5-2.5x on the 1M/5.5M WHERE scans on top of PERF-1a (~95 ->
~40-65 us/row); R5c full-scale IN should finally move (its cost IS the inner
materialization this slice attacks). Native paths, joins (read_area_row
based), DML source (materialize_join_source based), DbTupleStream, and the
REL graph cursor are untouched. Gate: same as PERF-1a -- six regressions
green (EVALDIFF 22/22 exact), then full 3a + star teed with I1-I13 identical.

#### PERF-1b MEASURED 2026-09-22 -- G-P1 GREEN, 1.6-3.9x on top of PERF-1a

Build 9b1a2945+1b (Sep 21 2026 21:31:25, committed ca1f66cfd). Six
regressions PASS first (EVALDIFF 22/22 exact), then both batteries teed
(sha256:BEB3FCC7... relational 20260921T213210Z; sha256:76082DA5... star
20260922T073937Z) with EVERY identity IDENTICAL again -- I1-I13 exact,
paths and refusals unchanged.

Ratios, PERF-1a build -> PERF-1b build (cumulative vs pre-PERF-1 in parens):

    R6a/b/c set ops     207/256/264 -> 69.8/73.1/67.4   3.0-3.9x  (~11x)
    R4b function-WHERE   95.0 ->  51.1                  1.9x      (7.7x)
    R5a bounded IN      336.6 -> 183.6                  1.8x      (5.9x)
    R4c GROUP BY        128.7 ->  81.2                  1.6x
    R4d DISTINCT         74.5 ->  61.5                  1.2x
    R5c full-scale IN   608.8 -> 390.2 (idle probe)     1.6x      (1.4x)
    R3a/b/c joins, R4a native, star S1-S5: flat (untouched paths)

ANOMALY, CLOSED AS TRANSIENT (the R4b-2008s protocol): the teed 3a run
recorded R5c at 34129.3 s WALL CLOCK with the count exact and
uncorrelated=1. The run spanned an actively used desktop evening and the
overnight standby hours; the identical statement standalone on an idle
machine the next morning ran 390.2 s. The teed figure is DISQUALIFIED as a
duration datum (the transcript remains valid for its counts); the 390.2 s
console probe is the datum, to be promoted by a daytime teed rerun whenever
convenient. Lesson recorded: overnight-spanning batteries produce wall-clock
durations that are not compute measurements.

CONSEQUENCE: two slices took simple/function-WHERE from 208-345 us/row to
~51 us/row -- within 1.8x of the native scan loop's 26-29 us. That is
OQ-P3's question answered by measurement: the typed TupleRow premium now
STANDS AT ~1.8x, inside the 2-3x band the proposal offered to accept.
Remaining constant: the AST walk and per-access string copies
(trim/norm_by_collation) in the accessors. PERF-2 multiplies from a far
better base: 51 us/row x 6 P-cores puts the 3a battery's minutes into
seconds without touching another constant.

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

### PERF-2 slice 1 AUTHORED 2026-09-22 (pending build + differential + measurement)

Proceeding on the charter's proposed defaults per owner directive 2026-09-22
("keep going for the cores"): OQ-P1 default 6 with the curve deciding, OQ-P2
REL out of the pool in v1, OQ-P3 premium accepted at its measured 1.8x.

The slice: `SET PARALLEL <n>|ON|OFF` (settings.hpp + cmd_set.cpp, the
INDEXTXN pattern exactly -- default OFF, DOTTALK_PARALLEL env seed, runtime
override, ON = 6). When >= 2, the single-table pass-1 scan partitions
contiguous recno ranges across n workers. THE R21 LAW IS STRUCTURAL: each
worker opens a PRIVATE DbArea on the source file (own handle, own cursor,
physical walk, no index attach), compiles its OWN predicate program, owns its
own TupleViewContext, reads rows through the new build_tuple_for_area
(tuple_builder) which bypasses workareas entirely, and prints nothing.
Merge is monoid: counts add, match vectors concatenate in range order;
ORDER BY sorts the merged set exactly as serial. The ON path prints
`workers=<n>` in its access-path line (charter requirement: every transcript
names its mode).

WHAT THE POOL REFUSES, each reported when ON and falling back to the
byte-identical serial walk: subquery predicates (shared SubqueryRuntime),
memo-bearing rows (memo backend not audited for concurrent readers), tables
under 2000 rows, private-open failure (pre-flighted on the main thread so it
is a decline, not a failed statement). Writes never reach this code. Pass 2
projection and joins stay serial in slice 1 -- COUNT-shaped statements gain
fully; row-returning statements gain pass 1 only.

Thread-safety notes recorded: workers share NOTHING mutable -- programs,
contexts, areas, and result slots are all per-worker; the one known global in
the eval path (exprglue ambiguity note) is unreachable for single-table
alias-prefixed layouts (short names unique within one table). Workers carry
errors back in their result slot; any worker error fails the statement with
that text (fail closed, never a partial count).

Gate G-P2 instrument: pinocchio_parallel_diff.dts -- the same statements OFF
then ON, five torn-partition bands straddling the exact 6-worker seams of the
1M fixture, ORDER BY+LIMIT identical-rows probe, and two decline-honesty
probes (subquery, small table). The DELETED-flag-per-partition probe is
DEFERRED to the registered regression (needs a fixture with deleted rows;
the read-only pinocchio set has none) -- recorded, not waved. The speedup
curve (2,4,6,8,12,16,22) reruns D1/D3 per OQ-P1.

### PERF-2 slice 1 MEASURED 2026-09-22 -- the engine's first multi-core run

Two differential runs, both teed. Run 1 (sha256:193857DA...,
parallel_diff_teed_20260922T101304Z) declined every ON leg -- the pre-flight
handed DbArea::open the LOGICAL name instead of filename(); one-line fix
(1508008f6). That run was not waste: it witnessed the FAIL-CLOSED skeleton
under fire -- six declines, all reported, all serial-identical, every count
exact. Run 2 (sha256:D0B7B682..., parallel_diff_teed_20260922T105718Z, build
content 1508008f6, stamp Sep 22 2026 10:56:40) is the datum:

    D5  ENROLL 5.5M COUNT        81.3 -> 16.9 s    4.8x
    D2  torn-seam bands (x5)    35-41 -> 8.8-9.1   4.0-4.5x, all 100==100
    D3  bare COUNT 1M            21.1 ->  4.9 s    4.3x
    D4  ORDER BY + LIMIT         37.7 ->  9.1 s    4.1x, SAME 5 rows SAME order
    D1  function-WHERE           46.6 -> 14.4 s    3.2x
    P1  subquery outer declined (reported); INNER materialization
        parallelized on its own scan: 243.2 -> 100.3 s, 1000 exact

EVERY OFF/ON pair identical -- counts, rows, order, LIMIT reports. The five
torn-partition bands straddling the exact 6-worker seams all returned 100
both modes: partition boundary arithmetic is proven at the seams, not
assumed. 4.0-4.8x on 6 workers (67-80 percent efficiency) on the cheap-row
statements; the charter's own words apply -- sublinear is expected and
honest, wrong is impossible to miss, and nothing was wrong.

PROBE DEFECT, MINE: P2 opened the 200-row x64 sample as STUDENTS while
pinocchio STUDENTS sat open in area 1, and the by-name resolver correctly
picked the first open match -- the probe measured the wrong (1M) table and
parallelized it exactly. Script corrected to the uniquely-named 11-row
MAJORS; the small-table decline remains RUNTIME-UNWITNESSED until the next
diff run. Recorded, not waved.

COMPOUND STATE OF THE LANE after one day: 208-345 us/row serial constant ->
~51 us/row (PERF-1a+1b), x 4-4.8 on six workers (PERF-2 slice 1). The 3a
battery's 395-second R4b of two days ago answers in ~14 s ON.

#### OQ-P1 CURVE MEASURED 2026-09-22 (console; promote by teed rerun)

Fourteen rungs, every count exact (90700 / 1000000 at all seven widths):

    workers   function-WHERE          bare COUNT
    OFF       46.6 s   1.0x           21.1 s   1.0x
    2         22.1 s   2.1x            9.4 s   2.2x
    4         16.8 s   2.8x            7.3 s   2.9x
    6         16.3 s   2.9x            5.6 s   3.8x
    8         15.6 s   3.0x  <- best   4.6 s   4.6x
    12        16.9 s   2.8x            4.0 s   5.2x  <- best
    16        18.1 s   2.6x            4.5 s   4.7x
    22        18.1 s   2.6x            4.5 s   4.7x

RULING (per the charter's own terms -- "the curve decides"): DEFAULT 8.
It beats the proposed 6 on both statements and is the only width that wins
cheap and expensive rows together. SET PARALLEL ON now means 8.

THE CURVE'S SHAPE IS A DIAGNOSIS. Cheap rows scale to 5.2x at 12 before the
E-cores flatten; expensive rows cap at 3.0x at 8 and DEGRADE past it. That
is not core starvation -- it is ALLOCATOR CONTENTION: the function-WHERE
statement allocates more strings per row (function temporaries + row
values), and the heap lock becomes the wall exactly where the remaining-
constant list already pointed. PERF-1c (fewer per-row allocations:
view-based accessors, trim/norm copies) therefore buys back BOTH serial
time and parallel scaling -- it is the next slice by measurement, not
preference. E-core answer: they help cheap rows modestly (12 > 8 there),
hurt expensive rows, and 16-22 never win anything; 8 is the honest default
on this part.

Remaining before gold closes: the registered SQLSEL_PARALLEL regression
(deleted-rows-per-partition fixture + small-table decline witness) before
any default flips ON; teed promotion of the curve and the R5c probe.

#### PERF-1c slice 1 AUTHORED 2026-09-22 (pending build + regression + measurement)

The curve demanded the allocator slice; the source read found the target
bigger than predicted: gotoRec64 calls readCurrent INTERNALLY, so every
scanned row was paying TWO complete all-field decodes (one from navigation,
one from the explicit readCurrent that followed) -- N staging strings each --
before the plan builder then COPIED each needed value out of _fd via get().

Three cuts, all additive:
1. xbase gains gotoRec64Raw (the M2 selective-decode idiom extended one
   step): position + raw buffer load + deleted flag, decode NOTHING. The
   existing gotoRec64/readCurrent are untouched.
2. Both plan builders decode values straight from the record buffer
   (decodeFieldFromBuffer -- same codec, one allocation, no _fd staging);
   valid after full OR raw loads. The serial pass-1 loop drops its redundant
   explicit readCurrent (navigation already decoded); pass-2 and the
   parallel workers go fully raw (gotoRec64Raw + on-demand decode -- workers
   never pay an eager decode at all). Worker ORDER BY keys read through a
   precomputed 1-based index (the by-name getter would read stale _fd).
3. Predicate-row THINNING: an AST walk collects the fields the compiled
   predicate can read; unreferenced columns get the plan's existing
   field1=0/empty-canonical treatment, so their values are never decoded.
   The prototype keeps the FULL layout -- CiIndex and unknown-field refusal
   semantics unchanged. Fail-safe: any unrecognized AST node kind thins
   nothing. Never applied under subquery predicates (text parsed per row may
   read any column).

HONEST EXPECTATION: serial WHERE scans lose one full decode of two plus the
staging copies plus unreferenced-column decodes -- predict 1.5-2.5x serial;
workers lose the eager decode entirely AND the allocation pressure the curve
blamed for the 3.0x cap, so the parallel ceiling should RISE (the
interesting number is function-WHERE at 8-12 workers). Gate: six
regressions green (EVALDIFF 22/22), the parallel differential
pairwise-identical again, then the curve rerun.

#### PERF-1c MEASURED 2026-09-22 -- 1.3-2.2x serial; 1M rows under one second

Committed 7f26cf0cb (build stamp Sep 22 2026 12:10:53). Six regressions
PASS, then the differential (sha256:5E655922...,
parallel_diff_teed_20260922T121137Z): every pair identical AGAIN, and the
small-table decline got its first runtime witness (MAJORS, 11 exact,
"table too small to partition").

Differential, PERF-1b -> PERF-1c build:

    serial:  D5 5.5M COUNT 81.3->36.6 (2.2x)  D3 bare 21.1->12.1 (1.7x)
             D2 band ~38->~24 (1.6x)  D4 37.7->24.5  D1 func 46.6->35.6 (1.3x)
    ON-6:    D5 16.9->7.8   D3 4.9->1.70   D2 8.9->5.5   D4 9.1->5.1
             D1 14.4->10.0   P1 subquery 100.3->65.4

Curve rerun (console; serial baselines 35.6 / 12.1):

    workers      2      4      6      8      12     16     22
    func-WHERE  15.1   10.7   10.5   10.5   10.8   12.5   13.1 s
    bare COUNT   3.4    1.9    1.5    1.2    0.97   1.3    1.2 s

FINDINGS. (1) ONE MILLION ROWS COUNTED IN 0.97 s at 12 workers -- 12.5x vs
serial, superlinear because workers skip the eager decode the serial
top/skip navigation still performs. E-cores EARN their keep on cheap rows.
(2) Function-WHERE improved absolutely (15.6 -> 10.5 s) but its PLATEAU
persists (flat 6-12, degrading past): with plan-side allocations gone, the
cap is the FUNCTION EVALUATION itself -- ALLTRIM/UPPER temporaries and the
copy-returning RecordView accessor signatures. Fixing that is an
engine-wide RecordView contract change: the platinum item this charter
priced and deferred, now with a measurement attached. (3) DEFAULT STAYS 8:
ties 6/12 on the expensive case, loses 0.24 s on the trivial one.
(4) OQ-P3 CLOSED BEYOND ITS OWN TERMS: serial simple-WHERE ~22-24 us/row
and serial bare COUNT ~12 us/row are AT OR BELOW the native loop's rates
(native COUNT FOR: 28-29 s on the same table). The typed premium -- 8x when
this lane opened -- is eliminated, not merely accepted.

LANE LEDGER, Saturday to Monday: function-WHERE 394.7 s -> 10.5 s (38x);
bare 1M COUNT ~21 s serial-double-decode -> 0.97 s (22x); 5.5M COUNT
~148 s tag walk -> 7.8 s (19x). Identities exact through every step.

#### SQLSEL_PARALLEL REGISTERED 2026-09-22 (gold closure; pending first green)

The G-P2 gate is now a NAMED, RUNNABLE spec: REGRESSION RUN SQLSEL_PARALLEL
(sqlsel_parallel_regression.dts + SqlselParallelV1, capture_routed_channel
because SET PARALLEL prints through cmdout). The fixture is what the
pinocchio diff script could not be: 2400 self-bootstrapped SANDBOX rows
(ID == RECNO by construction, LOOP-generated) with DELETED rows in BOTH
2-worker partitions AND in a band straddling the seam (recno 1200/1201).
Five OFF/ON pairs pinned as EXACT blocks -- the OFF leg IS the oracle --
plus the clamp probe (request 6, must RUN and REPORT workers=2), both
declines with exact serial answers, occurrence counts for the path line and
declines, fixture-shape pins, two cursor restorations, and PARALLEL left
OFF for the next spec. Explicit-run pending first green, mutation proof
(flip one expected count, watch it FAIL, restore), and soak; promotion to
the default suite comes after that, per the DEF_FAMILY precedent -- never
before the instrument has graded.

FIRST RUN WAS RED, AND THE RED WAS THE FIXTURE, NOT THE VALIDATOR
(2026-09-22): `REPLACE ID WITH RECNO()` printed "invalid numeric for
field" on every row -- REPLACE's RHS evaluator does not resolve RECNO()
(the function catalog already records the same quirk for '?' markers), so
every ID stayed blank, the shaping UPDATE/DELETEs matched 0 rows, and the
validator failed closed on the first block with expected/actual printed
(2370 vs 2400). Everything the red run COULD witness came out right: all
six workers=2 path lines, both declines with exact serial answers, the T7
decline ordering as authored, and the T4 line ordering
(rows -> selected -> LIMIT -> ORDER BY) later confirmed at the emit sites.
Fix: the builder now increments a shell variable (`SET VAR! counter =
&counter + 1`; `REPLACE ID WITH &counter`) -- macro expansion happens per
LOOP replay through shell_execute_line, so the literal reaches REPLACE and
ID == RECNO() still holds by construction. Same run also tripped the
check-site-artifacts gate (site said 83 specs, tree says 84): both site
artifacts re-derived and the two prose pages corrected in the site tree,
site freshness 16/16 green.

FIRST GREEN 2026-09-22, second attempt, commit 28fc59aac, build e88408bb:
every pinned value exact on the first run of the repaired fixture,
including the two counts the red run could not witness (UPDATE affected
100, DELETE affected 10 x3) and both cursor markers .T.

MUTATION PROOF 2026-09-22, green-red-green on build e88408bb in one
sitting, the DEF_FAMILY control-at-both-ends shape: control PASS; ARM =
the T3 OFF band alone widened to `ID < 1301` (one more visible row) ->
`SQLSEL PARALLEL: FAIL -- PAR-T3-OFF line 2 mismatch / expected: 190 /
actual: 191`, fail-closed with both sides printed; restore via git
checkout of the committed fixture -> PASS again. The arm run carried a
second witness for free: only the OFF leg was widened, so its transcript
shows OFF=191 against ON=190 -- the OFF/ON divergence this spec exists to
catch, displayed by the instrument that catches it. With the first red
(2370 vs 2400, fixture defect) this validator has now failed closed on
two DIFFERENT wrong-count shapes. Remaining before default-suite
promotion: soak only.

PROMOTED TO THE DEFAULT SUITE 2026-09-22. The soak: two PASS runs on ONE
build, banner `dottalk++ beta 1.b, c559013d  (Sep 22 2026 17:46:44)` on
both -- the first immediately after the PERF-3 rebuild, the second an
explicit `REGRESSION RUN SQLSEL_PARALLEL` minutes later with nothing
changed between them. Rows in coordination/SOAK_EVIDENCE.md, which
check_soak_evidence.py reads when the flag flips. The first green (build
e88408bb) is deliberately NOT counted: a different build is not soak.
The soak build is itself the PERF-3 build, so the promotion run doubles
as the third suite-scale confirmation of prediction (3). THE REASON is
the RELSCOPE2/NULLASSERT precedent -- a measured coverage hole, not the
soak alone: before this spec REGRESSION ALL never executed one SET
PARALLEL statement, so a partitioning defect that lost or double-counted
rows at the seam would have shipped green through the whole suite. The
flip changes the published default-suite facts (site re-derive in the
same change-set); it needs a REBUILD to take, and REGRESSION LIST must
show SQLSEL_PARALLEL [default] BEFORE the next REGRESSION ALL is
believed -- NAV_NATURAL's wasted run is the precedent.

VERIFIED IN-SUITE 2026-09-22 on the promoting build (aeaa6a6b4): the
listing was read first and showed [default], then REGRESSION ALL LOG
read specs run 32, passed 32, VERDICT PASS, isolation arms ok at both
ends. The spec's in-suite verdict is identical to its standalone one
(5/5 pairs, clamp, 3/3 declines, cursors 2/2), and its promise to
leave PARALLEL OFF is now demonstrated rather than assumed: EVALDIFF
runs after it in declaration order and its 22/22 held. This is the
order-independence check a standalone run cannot provide -- the spec
inherited whatever the 16 specs before it left behind and re-pointed
its own three slots. Evidence: dottalkpp/data/tmp/regression_all.log
(gitignored; this paragraph is the transcription).

#### PERF-3 AUTHORED 2026-09-22 -- the plateau was EXCEPTIONS, not allocations

SANDBOX MEASUREMENT (Cowork sandbox, g++ 11.4/glibc 2.35 -- third confirmed
build-and-run per the 2026-08-12 handoff; full-engine recipe was closed this
shape by a 403ing package proxy, so the measurement is a standalone harness
over the EXACT worker code path: compile_where program -> TupleViewContext::
view_for -> Expr::eval, walker copied verbatim from sqlsel_statement.cpp:423).

THE PRICED DIAGNOSIS WAS WRONG, AND THE HARNESS SAID SO ON ITS FIRST TABLE.
The platinum item priced "ALLTRIM/UPPER temporaries and copy-returning
RecordView accessors". Measured: a BARE char comparison (BAND = 'CSCI', no
function anywhere) cost 2,982 ns/eval while ALLTRIM added only ~330 ns on
top. gprof put all instrumented code at ~260 ns of that; the missing ~2.6 us
was to_number() -- eval.hpp's stod-in-a-try, which ALLOCATES a std::string
and THROWS on non-numeric text. Cmp::eval probes BOTH sides numerically
before comparing as text, so every char-leaf row paid TWO thrown-and-caught
exceptions (~1.3 us each, measured in isolation). AND THE PLATEAU FALLS OUT
FOR FREE: concurrent throws serialize on the unwinder's global lock, which
is why char/function WHEREs flatlined at 6-12 workers while the numeric
probe scaled superlinearly. Allocations were never the story.

THE CHANGE (one function, include/cli/expr/eval.hpp): to_number() rewritten
on std::from_chars -- non-throwing, non-allocating, locale-free. Semantics
pinned in the header comment: leading whitespace and lone leading '+' kept
(stod behavior), trailing garbage still refuses, hex floats and locale
grouping now refuse DELIBERATELY (stod took "0x10" as 16; xBase numerics
are canonical decimal). Every to_number caller benefits: Cmp, bool
coercion, function args, the incompatible-literal guard.

MEASURED IN THE HARNESS, same truth counts on every probe:
  char_eq    2,982 -> 409 ns/eval (7.3x), 2 -> 0 allocs
  fn_alltrim 3,318 -> 650 ns (5.1x); fn_upper 3,323 -> 675 ns (4.9x)
  fn_nested  3,390 -> 866 ns (3.9x); simple_num unchanged (never threw)

HOST PREDICTIONS, falsifiable, for the next curve run: (1) serial
function-WHERE closes most of its gap to serial simple-WHERE; (2) the 6-12
worker plateau BREAKS -- with no unwinder lock, char/function WHEREs should
scale like the numeric probe did; (3) exact counts unchanged everywhere
(the harness held truth counts constant; SQLSEL_PARALLEL's T2/T2F pins are
the gate). A sandbox green is not a host green; the curve decides.

SIBLINGS SWEPT AND CLEARED: sqlsel value_less/value_equal and the
glue_xbase stod calls all sit behind guards that guarantee success -- no
other silent throw-per-row sites found. NAMED, MEASURED, DEFERRED
(second-order residue, in cost order): function argv/return allocations
(~250 ns/call, the demoted remains of the platinum item);
try_eval_empty_identifier prefix-scanned 2x per char leaf (~30 ns);
triple per-row name resolution where a compiled binding could resolve once
per layout (~115 ns across three CiIndex finds). None warrants the
engine-wide RecordView contract change as priced -- that item is DEMOTED
pending host confirmation of this slice.

#### PERF-3 MEASURED 2026-09-22 -- one wall down, one wall named, one prediction refuted as worded

Two full curve runs on the promoting build (banner aeaa6a6b, Sep 22 2026
18:11:41), dottalkpp/data/scripts/pinocchio/pinocchio_perf3_curve.dts, SET TIMER ON.
Run 2 is the teed datum (tmp/perf3_curve_teed.txt, sha256:0984a7681a07cc60
-- the tee reuses one filename, so run 2 OVERWROTE run 1's file); run 1 is
console-paste corroboration, uniformly a few percent faster (cooler
machine), same shape everywhere. THE BASELINE IS PIN-PERF1C-002 (the
post-PERF-1c curve of 12:10 the same day), NOT the original OQ-P1 table:
PERF-1c landed between the two curves, and grading PERF-3 against the
pre-1c numbers would claim 1c's win twice.

    workers   function-WHERE (1c -> now)     bare COUNT (1c -> now)
    OFF       35.6 -> 25.0 / 27.3   1.3-1.4x  12.1 -> 9.6 / 11.2  ~noise
    2         15.1 -> 10.0          1.5x       3.4 -> 3.4          1.0x
    4         10.7 ->  6.5          1.6x       1.9 -> 1.8          1.0x
    6         10.5 ->  5.8 / 6.3    1.7x       1.5 -> 1.4          1.0x
    8         10.5 ->  5.7          1.8x       1.2 -> 1.15         1.0x
    12        10.8 ->  6.1          1.8x       0.97 -> 0.92        1.0x
    16        12.5 ->  6.7          1.9x       1.3 -> 1.2          1.0x
    22        13.1 ->  6.9 / 7.3    1.8x       1.2 -> 1.1          1.0x

THE DIFFERENTIAL IS THE FINDING. Bare COUNT -- which never threw -- is
unchanged at EVERY width: a perfect in-run control proving the change
touched only the throwing path. Function-WHERE improved at every width,
and improved MORE in parallel (1.7-1.9x at 6-22 workers) than in serial
(1.3-1.4x) -- the fingerprint of removed LOCK CONTENTION on top of removed
per-call cost. The unwinder lock was real.

PREDICTIONS GRADED AGAINST THE RECORD:
(3) CONFIRMED EXACTLY: 90700 / 1000000 at all 16 rungs of both runs.
(2) PARTIALLY CONFIRMED: the plateau's HEIGHT halved (10.5 -> 5.7 s at 8)
    and the scaling ceiling lifted 3.4x -> 4.4x, but the SHAPE persists --
    function-WHERE still stops scaling at ~8 while bare COUNT runs to
    10.5x at 12. The exception lock was ONE wall, not the only wall.
(1) REFUTED AS WORDED, confirmed in direction. "Closes MOST of its gap"
    did not happen: the serial surcharge over bare COUNT fell from
    ~23.5 us/row to ~15.7 us/row -- one third removed, ~7.9 us/row.
    THE REFUTATION CARRIES ITS OWN CALIBRATION: 7.9 us/row over two
    throws is ~4 us per thrown-and-caught exception on MSVC x64 --
    three times the sandbox's glibc figure of 1.3 us. The sandbox
    predicted the MECHANISM correctly and the MAGNITUDE conservatively;
    "a sandbox green is not a host green" cuts both ways, and this row
    is the measured exchange rate for next time.

WHAT THE REMAINING WALL IS, BY ELIMINATION: with exceptions gone, the
~15.7 us/row serial surcharge and the persisting 8-worker cap both point
at the already-named second-order residue -- function argv/return
allocations (the heap lock under concurrency) and per-row name
resolution. The demoted platinum item stays demoted; the NEXT slice, if
taken, is the narrow argv/return-allocation cut, sized by this
differential rather than by the old engine-wide RecordView pricing.

DEFAULT UNCHANGED: 8 still wins function-WHERE (5.70 s best both runs)
and is within noise of 12 on bare COUNT; the OQ-P1 ruling stands.
Ledger: PIN-PERF3-001/002. Fixture: dottalkpp/data/scripts/pinocchio/pinocchio_perf3_curve.dts, committed with this section.

#### PERF-4 AUTHORED 2026-09-22 -- one row per scan, refilled in place

THE TARGET, SIZED BY THE PERF-3 DIFFERENTIAL: with exceptions gone, a
numeric simple-WHERE whose EVALUATION allocates nothing still pays
~10-12 us/row over bare COUNT, and function-WHERE stops scaling at ~8
workers while bare COUNT runs to 10.5x at 12. Both point at the same
place: build_tuple_from_plan / build_tuple_for_area construct a FRESH
TupleRow per row -- a deep copy of the full 10-column prototype, three
vector constructions, and a rebuilt fragment -- before the predicate
reads one byte. Serially that is construction cost; under workers those
allocations meet on the heap lock.

THE CHANGE: refill_tuple_from_plan / refill_tuple_for_area
(tuple_builder.cpp) rewrite ONLY what the record changes -- value cells
(cleared, then decoded for plan-needed items) and fragment recno +
deleted -- into a row built once per scan. Bodies mirror the fresh
builders line for line (the compile_tuple_plan precedent: proven paths
untouched); both sqlsel single-table scan loops (serial including the
subquery branch, and the R21 worker) hoist one row holder and refill
after the first build. The TupleViewContext layout guard makes the
same-object rebind free. A refilled row is byte-identical to a freshly
built one for the same record; g++ 11.4 syntax-clean in the sandbox
(named: not a host green).

SANDBOX PRICE OF THE REMOVED WORK (container mirror probe, 1M rows,
glibc, single thread): fresh 160 ns/row + 4.00 allocs/row; refill
11 ns/row + 0 allocs. NOT REMOVED, stated so nobody reads more into
it: decodeFieldFromBuffer still allocates its result string per needed
field (1-2 allocs/row survive), and the eval path's argv/return
allocations are untouched -- this slice is the ROW, not the evaluator.

PREDICTIONS ON RECORD BEFORE THE HOST RUN, shaped by PERF-3's
refutation (the sandbox prices mechanisms, not host magnitudes):
  (1) every exact count unchanged -- REGRESSION ALL (now carrying
      SQLSEL_PARALLEL by default) and the curve's 90700/1000000 are
      the gate;
  (2) serial gains MODEST by design -- the sandbox prices the removed
      serial work at ~0.15 us/row; even at a generous MSVC exchange
      rate that is under 1 us/row of a ~15.7 us surcharge;
  (3) THE LOAD-BEARING ONE: if the heap lock is the surviving 8-worker
      cap, the parallel legs improve MORE than serial again and
      function-WHERE's scaling draws toward bare COUNT's shape past 8
      workers. A NULL RESULT HERE IS A FINDING: parallel gain equal to
      serial gain refutes the heap-lock hypothesis and re-points the
      cap at a shared resource no allocator change reaches (memory
      bandwidth -- bare COUNT's 12-worker floor is already ~0.9 us/row).

Verification: rebuild, REGRESSION ALL (32/32 expected), then the same
dottalkpp/data/scripts/pinocchio/pinocchio_perf3_curve.dts unchanged.

#### PERF-4 MEASURED 2026-09-22 -- THE PLATEAU IS BROKEN

Build b340f255 (Sep 22 2026 19:09:59). Correctness first: REGRESSION
ALL LOG 32/32 PASS on the refill build -- every oracle spec, EVALDIFF
22/22, SQLSEL_PARALLEL's five OFF==ON pairs, isolation arms ok both
ends. Then the curve (dottalkpp/data/scripts/pinocchio/
pinocchio_perf3_curve.dts unchanged, teed: tmp/perf4_curve_teed.txt,
sha256:2c67dcd22a27225b), graded against PIN-PERF3-001/002:

    workers   function-WHERE (P3 -> now)     bare COUNT (P3 -> now)
    OFF       25.0 -> 15.1   1.65x            9.6 -> 10.3   ~noise
    2         10.0 ->  5.7   1.75x            3.4 ->  3.3   1.0x
    4          6.5 ->  3.4   1.9x             1.8 ->  2.0   1.0x
    6          5.8 ->  2.60  2.2x             1.4 ->  1.39  1.0x
    8          5.70->  2.36  2.4x             1.15->  1.23  1.0x
    12         6.1 ->  2.08  2.9x  <- best    0.92->  0.94  1.0x
    16         6.7 ->  2.22  3.0x             1.2 ->  1.25  1.0x
    22         6.9 ->  2.16  3.2x             1.1 ->  1.10  1.0x

THE IN-RUN CONTROL HELD AGAIN: bare COUNT unchanged at every width,
so the gain belongs to the change and nothing else.

PREDICTIONS GRADED:
(1) CONFIRMED: 90700 / 1000000 at all 16 rungs, and the whole suite.
(3) CONFIRMED, AND IT SETTLES THE DIAGNOSIS: parallel gains (2.9-3.2x
    at 12-22) far exceed serial (1.65x), and function-WHERE NO LONGER
    STOPS AT 8 -- it now peaks at 12 and holds through 22, the same
    shape as bare COUNT. Scaling vs own serial: 7.3x at 12 workers
    (was 4.4x capped at 8 after PERF-3, 3.4x after 1c, 3.0x at the
    lane's start). The heap lock was the second wall; there is no
    third within reach of this fixture.
(2) REFUTED IN THE GOOD DIRECTION, and the refutation calibrates
    AGAIN: "serial gains modest" predicted under 1 us/row from the
    sandbox's 0.16 us container price; the host removed ~9.9 us/row.
    The MSVC-heap-and-copy cost of the fresh row was ~60x the glibc
    figure -- the second measured sandbox-to-host exchange rate in
    one day (throws were 3x). RULE EARNED TWICE NOW: the sandbox
    identifies WHAT to remove; only the host prices it.

COMPOUND STATE: the function-WHERE statement that took 46.6 s serial
when this lane opened OQ-P1 runs in 2.08 s at 12 workers -- 22x in
one day, all of it named, graded and committed in slices. The serial
surcharge over bare COUNT is down to ~4.8 us/row (23.5 after 1c,
15.7 after PERF-3) -- what remains is the actual function evaluation
plus the per-needed-field decode allocation, the residuals already
named.

RULING FLAGGED FOR THE OWNER, per OQ-P1's own "the curve decides"
clause: 8 was ruled when expensive rows DEGRADED past it. On this
build 12 wins BOTH statements (2.08 vs 2.36; 0.94 vs 1.23) and
nothing degrades through 22. The data now favors SET PARALLEL ON = 12;
the flip is the owner's call and is NOT made by this section.

Ledger: PIN-PERF4-001.

## 5. Open rulings, placed where they block

- OQ-P1 -- ANSWERED BY MEASUREMENT 2026-09-22: default 8 (see the curve in
  PERF-2 MEASURED above; 8 beat the proposed 6 on both probe statements;
  E-cores help cheap rows modestly and hurt expensive ones; 16-22 never
  win). SET PARALLEL ON = 8. Original question kept for the record:
  worker count default when ON -- physical cores, logical processors, or
  fixed cap? MEASURED BASELINE (owner's box, Get-CimInstance 2026-09-21):
  Intel Core Ultra 9 185H, 16 cores / 22 logical -- 6 P-cores (HT) + 8
  E-cores + 2 LP E-cores. Proposal was 6; the curve ruled 8, per this
  charter's own "curve decides" clause and the owner's 2026-09-22
  directive.
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
