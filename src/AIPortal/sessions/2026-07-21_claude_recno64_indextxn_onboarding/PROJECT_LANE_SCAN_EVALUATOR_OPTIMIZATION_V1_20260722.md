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
- **M3 — compile the predicate once.** ✅ **LANDED 2026-07-22 (build-verified; done ahead of M1/M2
  because profiling showed per-row recompile was the dominant cost).** The scan path
  (`cli::scan::collect_selected_recnos`) re-ran the *entire* `eval_bool` pipeline per row —
  `expand_value_builtins`, `fold_constant_date_algebra`, DotScript-bridge probe, and either a
  fast-path re-parse or a full `compile_where_program` AST build — on a constant predicate string.
  New `compile_bool_predicate` / `eval_bool_compiled` API (`value_eval.{hpp,cpp}`) compiles once
  (AST + one reusable live `RecordView`) and evaluates per row; `collect_selected_recnos` compiles
  before the loop. Parity-safe by construction: hoists only when preprocessing is a proven no-op
  and the predicate is not a `$`/`{` bridge form — everything else falls back to per-row `eval_bool`
  (identical behavior). `match_current` retained unchanged for LOCATE/CONTINUE.

  *Measured (1M pinocchio STUDENTS, same host; parity: COUNT anchors stayed `1000000`):*

  | op | floor | after M3 | speedup |
  |---|---:|---:|---:|
  | `SUM GPA` (no predicate path) | 19.5 s | 18.7 s | ~flat (expected) |
  | `COUNT FOR GPA>=0` (1 term) | 38.5 s | 28.3 s | 1.36× |
  | `COUNT FOR … 3 terms` | 70.5 s | 35.7 s | 1.98× |
  | marginal per added term | 16.0 s/1M | 3.7 s/1M | **4.3×** |

  Compile-once nearly eliminated the per-added-term cost (16→3.7 µs/row). The residual ~9.6 s/1M on
  the *first* term is now the field-access layer inside the compiled eval (per-row name resolve +
  `std::string` extract + `stod`) — exactly what M1 + M2 remove next.
- **M1 — bind fields once.** ✅ **LANDED 2026-07-22 (build-verified).** Added a per-view field-name→
  index cache in `make_record_view` (`glue_xbase.cpp`, `field_index_ci_cached`), shared via
  `shared_ptr` so the compile-once scan reuses it across every row — after row 1 all field
  resolutions are cache hits (no more per-access uppercased linear scan of the field descriptors).
  Parity-safe: pure memoization of a deterministic lookup over a fixed layout; counts stayed
  `1000000`.

  *Measured — and a methodology note.* Raw `ELAPSED` is **not** comparable across runs: run-to-run
  machine variance (thermal/background) moved the predicate-free `SUM GPA` baseline 18.7 s → 22.8 s
  (+22%) between the M3 and M1 runs. Compare the **predicate cost normalized to the in-run scan
  baseline** (`DECx − SUM`), which cancels that variance:

  | metric | M3 run | M1 run | change |
  |---|---:|---:|---|
  | predicate cost, 1 term (`DEC1 − SUM`) | 9.64 s | 8.81 s | −9% |
  | marginal per term (`(DEC3 − DEC1)/2`) | 3.68 s | 3.40 s | −8% |

  Small but real, as predicted — the name scan was a minor slice. Henceforth read the benchmark as
  `DECx − SUM`, not raw `ELAPSED`.
- **M2 — selective + allocation-free decode.** ✅ **LANDED 2026-07-22 (build-verified; parity green
  across `REGRESSION ALL` + `SCAN_PARITY`).** Profiling revealed the dominant residual was not the
  predicate at all — `readCurrent()` eagerly decodes *every* field of the record into `std::string`
  (`loadFieldsFromBuffer`) on every row, whether the predicate reads it or not. New additive core
  path: `DbArea::readCurrentRaw()` (loads the record buffer, skips the eager field decode),
  `decodeFieldFromBuffer()` (one field, all types, memo-aware — same codec as the full path), and
  `fieldNumFromBuffer()` (N/F → `double` via `strtod`, no heap). A selective-decode record view
  (`make_record_view_raw`) decodes only the fields the predicate touches; `collect_selected_recnos`
  uses it (via `compile_bool_predicate(..., allow_raw)`) when a compiled predicate is present and no
  persistent `SET FILTER` is active (the filter needs the full record). Gated + fallback-safe;
  `match_current` unchanged for LOCATE/CONTINUE.

  *Measured (1M pinocchio STUDENTS, 9 fields; parity: counts stayed `1000000`).* Because `SUM`/`DEC1`
  now use different decode strategies, read the predicate scans normalized to the run's full-decode
  `SUM` baseline:

  | metric | floor | M1 | M2 | vs floor |
  |---|---:|---:|---:|---:|
  | `DEC1 / SUM` (1-term scan) | 1.97× | 1.39× | **0.93×** | **2.1×** |
  | `DEC3 / SUM` (3-term scan) | 3.62× | — | **1.30×** | **2.8×** |

  **DEC1 is now faster than SUM** — a one-field predicate scan beats a full-field aggregate scan,
  because it decodes only GPA (1 of 9 fields) instead of all nine. The marginal per-term cost is
  ~unchanged (M2's win is skipping *unused* fields, not cheaper accessed ones). Remaining floor is
  the per-row record I/O (`gotoRec` + `readCurrentRaw` seek+read ≈ 18 µs/row) — a bulk/sequential
  scan opportunity in the record-iteration subsystem, outside this evaluator lane.
- **M4 — apply across consumers.** ✅ **LANDED 2026-07-22 (build-verified; `REGRESSION ALL` green;
  `SUM GPA` value `2.99933e+06` preserved).** COUNT / LIST FOR / SET FILTER / SCAN-selection were
  already free via the shared `collect_selected_recnos` choke point (M1–M3). This milestone extended
  selective decode to `cmd_aggs` (both the single `SUM`/`AVG`/`MIN`/`MAX` loop and multi `AGGS ALL`):
  `eval_value_plan` gained a raw mode (direct-field via `fieldNumFromBuffer`/`decodeFieldFromBuffer`,
  compiled-numeric via the raw record view), gated to no-FOR/WHERE-and-no-active-filter (a predicate
  or filter still needs the full record for `filter::visible`).

  *Measured — via the variance-immune within-run `SUM / DEC1` ratio (both scan 1M rows; the only
  difference is how many fields each decodes):*

  | run | `SUM / DEC1` | interpretation |
  |---|---:|---|
  | M2 (SUM full-decodes 9 fields) | 24.61 / 22.82 = 1.078 | SUM pays ~8% extra for 8 unused fields |
  | M4 (SUM selective-decodes GPA) | 21.26 / 21.28 = 0.999 | SUM == a 1-field scan; tax removed |

  The ~8% is small only because STUDENTS is narrow (9 fields); it scales with field count.

## Lane status — COMPLETE (evaluator), 2026-07-22

M1–M4 are landed and build-verified; parity green across `REGRESSION ALL` + `SCAN_PARITY`; all
benchmark counts/values unchanged. Net vs the M0 floor (normalized to the run's scan baseline):
**DEC1 predicate scan ~2×, DEC3 ~2.6–2.8×**, and **aggregates no longer full-decode**. The lane's
falsifiable ≥40× / sub-1s target was **not** reached — and the profiling explains why: after M1–M4
the per-row cost is no longer in the evaluator or field decode at all. Both a bare aggregate and a
1-field predicate scan now sit at ~21 µs/row, essentially all of which is **per-row record I/O**
(`gotoRec` + `readCurrentRaw` = one seek + one read per record). That is a different subsystem
(record iteration), and the orders-of-magnitude now live there → **spin-off: a bulk/sequential
record-scan lane** (read records in blocks / stream the file once, instead of seek-per-row). The
evaluator is no longer the bottleneck.

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

## Promotion status — source → mirror

**Source of truth:** `D:\code\ccode` (committed `eba9a7012`, plus `cmd_regression.cpp`'s
`PHASE0_DECODE_COST` which landed in an earlier same-day commit; working tree clean for all six
M0 files). Website benchmark page published in `x64base-site` (`24480861`).

**Mirror `C:\x64base` (2026-07-22): M0 promoted, surgically.** Promotion was **not** a wholesale
file copy — the mirror is behind ccode on two unrelated lanes whose dependencies it lacks, so a
blanket copy would have broken its build (the same failure mode as the earlier `shell_commands.cpp`
over-copy). What landed on the mirror:

- `src/cli/expr/fn_date.cpp` — byte-identical (clean M0-only delta).
- `dottalkpp/data/scripts/pinocchio/ticketb_phase0_decode_cost.dts` — byte-identical (new file).
- `src/cli/shell.cpp` — **surgical**: only the `shell_execute_instrumented` timer strip.
- `src/cli/shell_api.cpp` — **surgical**: only the `shell_execute_line` timer + `<chrono>`/
  `cli/settings.hpp` includes.
- `src/cli/cmd_regression.cpp` — **surgical**: only the `PHASE0_DECODE_COST` entry (array 19→20).

**Deliberately NOT promoted to the mirror (separate, dependency-complete promotions still owed):**
AIF-037 `dotscript_lexing` consolidation (mirror lacks `src/cli/dotscript_lexing.{hpp,cpp}`);
AIF-044 `build::ui::prompt_char_default` (mirror still `char prompt_char = '.'`); and the
`BUILD_VECTORS` + `IDENTITY_PERSIST` regression entries. The mirror's M0 changes are uncommitted
pending the maintainer's x64base build + commit.

## Cross-references

- Origin / kill: `TICKET_B_TUPLE_NATIVE_INMEMORY_STORE_V1` (Phase-0 result).
- Benchmark: `dottalkpp/data/scripts/pinocchio/ticketb_phase0_decode_cost.dts`, registered as
  regression `PHASE0_DECODE_COST` (`cmd_regression.cpp`, `in_default_suite=false` — **exempt from
  `REGRESSION ALL`**; run explicitly via `REGRESSION PHASE0_DECODE_COST`). Long-running (~2+ min),
  requires the 1M-row pinocchio fixture; it is the M1–M4 speedup floor, not a pass/fail gate.
- Evaluator surfaces: `src/cli/predicate_eval.cpp`, `src/cli/expr/value_eval.cpp`,
  `src/cli/shell_bool_eval_adapter.cpp`; consumers `cmd_count/aggs/locate/list/scan/setfilter`.
