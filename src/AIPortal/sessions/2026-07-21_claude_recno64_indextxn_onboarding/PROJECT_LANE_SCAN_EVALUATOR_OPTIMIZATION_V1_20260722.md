# PROJECT LANE — Scan / Expression-Evaluator Optimization (bind-and-compile-once)

**Type:** optimization lane · **Status:** chartered (candidate; not started) · **Filed:** 2026-07-22
· **Author:** Claude (steward) · **Authority:** Derald. **Origin:** the Phase-0 gate of
`TICKET_B_TUPLE_NATIVE_INMEMORY_STORE_V1` — which **killed** Option B and, in doing so, found the
*actual* bottleneck. **AIF:** candidate new lane; maintainer assigns the number (ceiling was AIF-043).

## Why this lane exists (the finding)

Ticket B (typed-vector store) was gated on proving that field **decode** was a measurable cost.
The Phase-0 benchmark instead proved the store is not the problem — the **per-row expression
evaluator** is. Wall-clock over the 1,000,000-row pinocchio STUDENTS table
(`data/scripts/pinocchio/ticketb_phase0_decode_cost.dts` + a `Measure-Command` harness, because
in-script `SECONDS()`/`SET TIMER` report 0):

**Self-timed baseline (2026-07-22, build-verified).** Re-measured in-process with the now-working
`SET TIMER` (steady_clock), cross-checked to ~0.01 s by the fixed fractional `SECONDS()`. This
supersedes the earlier external `Measure-Command` numbers and is cleaner: it isolates the pure
aggregate (`SUM`, no predicate) from the predicate scan.

**Bench host:** Alienware m16 R2 — Intel Core Ultra 9 185H (Meteor Lake, 16C/22T; successor to
the mobile i9 line, not a literal i9 part), 64 GB DDR5-5600, Windows 11 Pro Build 26200.8875;
project tree + pinocchio fixtures on **D: = Samsung 970 EVO 1 TB NVMe**. This is the same attested
workstation used for the Phase 1 / navigation baselines — canonical record in
`docs/maintenance/PINOCCHIO_STRESS_TEST_PLAN_V1.md` (§ Machine identity rule) and
`PINOCCHIO_MACHINE_PROFILE_CURRENT_V1.json` (`historical_run_binding: MAINTAINER_ATTESTED`).
Absolute times are machine-specific — compare speedups as ratios against this floor, re-measured
on the same host.

| measure | time (1M rows) | per-row | isolates |
|---|---|---|---|
| `SUM GPA` | 19.48 s | ~19.5 µs | iterate + 1-field decode + accumulate (no predicate) |
| `COUNT FOR GPA >= 0` (DEC1, 1 term) | 38.51 s | ~38.5 µs | + predicate machinery, 1 term |
| `COUNT FOR GPA>=0 .AND. SID>=0 .AND. MAJOR<="ZZZZ"` (DEC3, 3 terms) | 70.54 s | ~70.5 µs | + 2 more terms |
| predicate machinery over bare aggregate | DEC1 − SUM ≈ 19.0 s / 1M | ~19 µs/row | resolve-by-name + parse_double + tree-walk + compare, per term |
| marginal per added term | (DEC3 − DEC1)/2 ≈ 16.0 s / 1M | ~16 µs/row | one extra predicate term |

Prior external run (superseded, retained for history): DEC1 39.07 s, DEC3 92.52 s.

A single-field predicate scan at **~39 µs/row is ~1000–10000× slower than it should be**
(a fixed-width scan belongs in the ns/row range). Option B would run this same loop over typed
cells and not fix it. The leverage is here, in Option A, with no tuple-core changes.

## Root cause (grounded in source)

Per row, per predicate term, the evaluator (`src/cli/predicate_eval.cpp`,
`src/cli/expr/value_eval.cpp`, `src/cli/shell_bool_eval_adapter.cpp`) repeats work that is
constant for the whole scan:

1. **Field resolved by name every row** — `resolve_field_index(db, name)` does a
   case-insensitive scan of the field descriptors *per term per row* (predicate_eval.cpp:62).
2. **Byte→string→number round-trip** — the field is extracted into a `std::string`, then
   `parse_double(const std::string&, …)` parses it (predicate_eval.cpp:47) — a heap allocation
   and a general parse per term per row.
3. **Tree-walked, boxed comparison + AND-node** — `eval_triplet` re-parses functor tokens and
   re-derives operands each row (predicate_eval.cpp:143), no compiled form retained.

So the ~26.7 µs/term is dominated by name-resolution + allocation + general parse + tree-walk —
none of which Option B removes (B changes cell *storage*, not the evaluator).

## Thesis: bind-and-compile ONCE per scan, not per row

Move the constant work out of the row loop:
- **Bind** each field reference to `{offset, len, type}` at scan setup (resolve the name once).
- **Compile** the FOR/predicate expression once into a closure/bytecode over the bound fields
  (no per-row token re-parse, no tree re-walk).
- **Decode in place**, allocation-free: fixed-width bytes → `double`/`int64`/date directly, no
  intermediate `std::string`, no boxed `Value` where a scalar suffices.
- **Short-circuit** compiled `.AND./.OR.` without re-deriving operands.

This is Option A, additive to the engine's evaluator; the store stays byte-image.

## Milestones (each bench-gated; prove the speedup before the next)

- **M0 — reliable timing + baseline.** ✅ **DONE 2026-07-22 (build-verified).** Both timers now
  fire in scripts and agree to ~0.01 s; self-timed baseline table above is the regression floor.
  Two structural defects fixed: (1) `SECONDS()` derived from the HHMMSS `time6`
  string → integer-only resolution; rewritten in `src/cli/expr/fn_date.cpp` (`dt_seconds`) to
  return seconds-since-midnight with millisecond precision via `std::chrono`. (2) `SET TIMER` only
  fired in the interactive wrapper `shell_execute_instrumented` (`src/cli/shell.cpp`); script/DO
  lines call the canonical `shell_execute_line` (`src/cli/shell_api.cpp`) directly and were never
  timed. Moved the timer into `shell_execute_line` — the single chokepoint every front-end routes
  through (REPL, DO/DOTSCRIPT, init/shutdown, loop bodies) — and stripped the now-duplicate branch
  from the interactive wrapper. `SET TIMER ON` now reports per-command `ELAPSED` inside scripts.
  Benchmark `ticketb_phase0_decode_cost.dts` updated to v5 (self-timing). Baseline table above is
  the regression floor.
- **M1 — bind fields once.** Resolve field name→index/offset at scan setup; kill per-row
  `resolve_field_index`. Expected: large drop in per-term cost.
- **M2 — allocation-free in-place decode.** Fixed-width bytes → scalar without `std::string`.
- **M3 — compile the predicate once.** Expression tree → closure/bytecode over bound fields;
  evaluate per row with no re-parse.
- **M4 — apply across consumers.** `cmd_count` (COUNT FOR), `cmd_aggs` (SUM/AVG/MIN/MAX),
  `cmd_locate`, `cmd_list` (LIST FOR), `SET FILTER`, `cmd_scan`.

## Falsifiable success criteria

- **Speed:** `COUNT FOR GPA >= 0` over 1M rows drops from ~39 s toward **< 1 s** (target ≥ 40×);
  per-added-term cost drops proportionally. Bench = the Phase-0 harness.
- **Parity:** identical results — reuse the pinocchio proofs + a new scan-parity regression
  (COUNT/SUM/LOCATE/LIST FOR over a fixture must match pre-optimization counts exactly).
- **Additive + reviewed:** changes land in the evaluator/field-access path
  (`predicate_eval.cpp`, `expr/`, DbArea field decode), maintainer-reviewed; no behavior fork.

## Governance / boundary

Engine expression + field-access surface (not the maintainer-owned tuple core Ticket B would have
touched). Same discipline: prove each milestone's speedup on the benchmark before proceeding;
report-only until reviewed. This lane is where the orders-of-magnitude actually are.

## Spun-off micro-ticket

**Fix in-script timing.** ✅ RESOLVED 2026-07-22 (code landed; awaiting user's Windows build to
verify). `SECONDS()` / `SET TIMER ON` did not report elapsed inside `DO <script>` (both read 0
while wall-clock showed 39–92 s). Root causes: `SECONDS()` was integer-only (HHMMSS-derived) and
`SET TIMER` lived only in the interactive wrapper, bypassing the script executor. Both fixed —
see M0 above for the exact surfaces. Benchmarks and self-timing scripts now work.

## Cross-references

- Origin / kill: `TICKET_B_TUPLE_NATIVE_INMEMORY_STORE_V1` (Phase-0 result).
- Benchmark: `dottalkpp/data/scripts/pinocchio/ticketb_phase0_decode_cost.dts`, registered as
  regression `PHASE0_DECODE_COST` (`cmd_regression.cpp`, `in_default_suite=false` — **exempt from
  `REGRESSION ALL`**; run explicitly via `REGRESSION PHASE0_DECODE_COST`). Long-running (~2+ min),
  requires the 1M-row pinocchio fixture; it is the M1–M4 speedup floor, not a pass/fail gate.
- Evaluator surfaces: `src/cli/predicate_eval.cpp`, `src/cli/expr/value_eval.cpp`,
  `src/cli/shell_bool_eval_adapter.cpp`; consumers `cmd_count/aggs/locate/list/scan/setfilter`.
