# Performance: Where the Time Goes and How to Buy It Back

```yaml
page_id: USER-PERF-01
title: Performance
audience: runs real queries on real tables; wants them faster
status: DEVELOPMENT-RUNTIME-VERIFIED
last_verified: 2026-09-23
runtime_scope: development
```

This chapter is about processor usage: what one statement costs, why it used
to cost more, and the one knob you own -- `SET PARALLEL`. Memory, disk I/O
and index-backed access deserve sections of their own and are OWED, not
covered (section 7 records the debt). Every number here is a measurement
from the engine performance lane (September 2026, the reference 185H box),
transcribed from `docs/maintenance/ENGINE_PERF_PDLC_LANE_V1.md` -- the lane
record holds the full curves and the falsification runs.

## 1. The shape of the cost

A scan statement costs roughly:

```text
(per-row constant) x (rows) / (cores actually working)
```

When the lane opened, the per-row constant was about 200 microseconds and
the divisor was 1 -- every query ran one row-interpreter on one core. The
September work attacked both factors in order, cheapest first, because
parallelizing an expensive row "rents cores to multiply waste": you pay for
eight workers and each one burns most of its time in the same per-row
overhead.

The headline compound: the reference function-WHERE statement over the
1M-row fixture took **46.6 s** when the lane opened and runs in **2.08 s at
12 workers** on the current build -- **22x**. A bare 1M `COUNT` fell from
about 21 s to **0.94 s**. The "typed premium" -- typed SQLSEL rows once
costing 8x what a native scan cost -- is eliminated; for calibration, a
native `COUNT FOR` over the same table runs 28-29 s, so the typed path is
now the fast path.

## 2. SET PARALLEL -- the knob you own

```text
SET PARALLEL             report the current setting
SET PARALLEL <n>         exact worker count (2..64)
SET PARALLEL ON          the session default (compiled 8; see below)
SET PARALLEL OFF         serial (the startup default)
SET PARALLEL DEFAULT <n> move what ON means for this session
SET PARALLEL STATUS      same report, spelled longer
```

`DOTTALK_PARALLEL_ON=<n>` in the environment moves the ON width at startup.

Eligible statements are READ-ONLY single-table scans. The engine partitions
by recno range, gives each worker a private cursor, and prints its access
path -- `parallel (workers=N, rows=R, recno-range partitions)` -- so the
evidence is in your transcript like every other path report. Read it: a
statement you expected to fan out that prints a decline instead is telling
you which rule it hit.

The engine DECLINES parallelism, with the reason printed, rather than
running a statement it cannot serve honestly: DML, subquery predicates, memo
columns, and small tables (under 2000 rows -- partition overhead would
exceed the work) all scan serial. Joins, transactions and every write path
are untouched by design. Answers are proven identical to serial by a
differential spec in the default suite (SQLSEL_PARALLEL: OFF==ON pairs,
deleted-row exclusion across partition seams, worker clamping), so
correctness is not the price of the speed.

## 3. Choosing a worker count

Measured on the reference box (1M-row fixture, current build):

```text
workers   function-WHERE        bare COUNT
OFF       46.6 s  1.0x          ~21 s   1.0x
8          2.36 s               0.92 s
12         2.08 s  <- best      0.94 s
..22       no degradation observed
```

`SET PARALLEL ON` compiles to 8 -- a deliberate general-purpose choice from
the earlier curve (OQ-P1), kept by owner ruling after later work moved the
optimum: on the current build 12 wins both probe statements, and nothing
degrades through 22. So: **ON is a safe default; try `SET PARALLEL 12` on a
machine with 12 or more hardware threads and read your own curve.** The
curve is machine-shaped -- P-core/E-core mixes move it -- and the path
report plus a stopwatch is the whole measurement kit. Oversubscribing past
your hardware thread count is clamped and reported, not punished.

## 4. Why it was slow: three walls, told honestly

Worth knowing because each wall is a pattern you may meet in your own code.

**The per-row interpreter constant (PERF-1a/1b/1c).** Every row paid for
generic accessor plumbing, per-row string copies and allocations. Reusable
row contexts, a compiled projection plan, and buffer-decode-in-place cut
the constant from ~208 us toward ~51 us -- 3-6x on the converted loops
before a second core was ever engaged (the biggest single ratio: a UNION
probe, 832.7 s -> 207.0 s).

**The unwinder lock (PERF-3).** Adding workers plateaued, and the plateau
was EXCEPTIONS, not allocations: numeric conversion threw on non-numeric
text, and concurrent throws serialize on the C++ unwinder's global lock --
so every worker queued at one door. Conversion moved to `std::from_chars`
(non-throwing, non-allocating, locale-free) and one wall fell. The lesson
travels: exceptions on a hot multi-threaded path are a hidden global lock.

**The heap lock (PERF-4).** The next plateau was per-row heap traffic
serializing on the allocator. One row buffer per scan, refilled in place,
broke it: 6.1 s -> 2.08 s at 12 workers on top of everything prior, and
the worker curve stopped capping at 8. What remains above 12 is the actual
function evaluation -- honest work, parked as PERF-5 (the ~4.8 us/row
function-eval surcharge), scheduled only if a workload demands it.

## 5. Practical habits

1. Leave `SET PARALLEL OFF` for scripts whose timing you compare across
   builds; turn it ON (or 12) for interactive work over big tables.
2. Read the path report and the decline reasons; they are the diagnosis.
3. Expect no effect on DML, joins, or transactions -- that is design,
   not a missing feature.
4. On a laptop on battery, fewer workers can beat more; measure once.
5. A statement still slow at 12 workers has an expensive per-row
   expression -- simplify the WHERE before adding cores.

## 6. Verification

`REGRESSION ALL` runs the SQLSEL_PARALLEL differential on every pass (it
joined the default suite 2026-09-22). The lane record with every curve,
prediction and refutation is `docs/maintenance/ENGINE_PERF_PDLC_LANE_V1.md`.

## 7. Owed sections (recorded, not written)

- **Memory**: working-set behavior of wide scans, the one-row-buffer
  design's RAM profile, LMDB mapsize sizing.
- **Disk and index-backed access**: when a CDX seek beats a partitioned
  scan, BUILDLMDB costs, cold-cache behavior.
- **CPU topology**: P-core/E-core scheduling beyond the one measured note
  (E-cores help cheap rows modestly; 12 > 8 there).

Each becomes a dated section here when it is measured, not before -- this
manual carries transcribed numbers only.
