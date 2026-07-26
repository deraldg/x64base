---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260722-007
  recorded_at_utc: 2026-07-22T23:59:00Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 3231ae0c9
    head_commit: 0f06d1060
  authorization:
    requested_by: maintainer
    scope: optimize the scan/expression evaluator (spun off from AIF-043 Ticket B Phase-0 kill); commit + document; stage the follow-on bulk-I/O lane
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_SCAN_EVALUATOR_LANE_2026-07-22.md
    kind: session_closeout
---

# Session Closeout — Scan-Evaluator Optimization Lane, M0–M4 (2026-07-22)

Owning lifecycle: DotTalk++ SDLC (`project.x64base.runtime`, AIF-046).
Operating mode: `development`.
Change class: `C2` (hot-path evaluator + core record-read additions; additive, gated).
Build target: `dottalkpp_runtime`.
Truth state: build-verified (MSVC Release) + parity-verified (`REGRESSION ALL` + `SCAN_PARITY` green) at each milestone; benchmark counts/values unchanged throughout.
Promotion state: committed to dev (`eba9a7012`, `0f06d1060`, M4 + docs by maintainer). Mirror `C:\x64base` has **M0 only**; M1–M4 mirror promotion owed. Not pushed to public by this lane.

## Origin

This lane is the **redirect from the Phase-0 gate of `TICKET_B_TUPLE_NATIVE_INMEMORY_STORE_V1`** (AIF-043, in-memory tables). Phase-0 was meant to prove that field *decode* was a measurable cost worth a typed-vector store; instead it proved the store was not the problem — the **per-row expression evaluator** was ~1000× slower than a fixed-width scan should be. Ticket B was KILLED with evidence, and this lane captured the real leverage in Option A's evaluator, no tuple-core changes.

## Outcome

The scan/expression evaluator is no longer the bottleneck. Across M0–M4, a physical-order predicate scan over the 1,000,000-row pinocchio STUDENTS table dropped **~2× (1-term) to ~2.8× (3-term)** versus the M0 floor, aggregates stopped full-decoding every field, and every measured count/value stayed identical. The residual is now **per-row record I/O**, a different subsystem — captured as the staged Bulk Record-I/O lane.

Milestones (each bench-gated, parity-verified before the next):

- **M0 — reliable timing + baseline.** Fixed two defects that made scripts un-timeable: `SECONDS()` was integer-only (HHMMSS-derived) → rewritten to millisecond resolution via `std::chrono` (`src/cli/expr/fn_date.cpp`); `SET TIMER` only fired in the interactive wrapper → moved into the canonical `shell_execute_line` (`src/cli/shell_api.cpp`), stripped the duplicate from `shell_execute_instrumented` (`src/cli/shell.cpp`), so scripts self-time. Benchmark `ticketb_phase0_decode_cost.dts` → v5 self-timing; registered regression `PHASE0_DECODE_COST` (exempt from `REGRESSION ALL`). Self-timed floor (Alienware m16 R2 / Core Ultra 9 185H): SUM ~19.5s, DEC1 ~38.5s, DEC3 ~70.5s. Committed `eba9a7012`; benchmark page published to the site.
- **M3 — compile the predicate once** (done first; profiling showed per-row recompile dominated). `compile_bool_predicate`/`eval_bool_compiled` (`value_eval.{hpp,cpp}`) compile the FOR predicate once (AST + reusable live `RecordView`) and evaluate per row; `collect_selected_recnos` compiles before the loop. Parity-safe: hoists only when preprocessing is a proven no-op and it is not a `$`/`{` bridge predicate, else per-row `eval_bool` fallback. Marginal per-term cost 16→3.7 µs/row.
- **M1 — bind fields once.** Per-view field-name→index cache in `make_record_view` (`glue_xbase.cpp`, `field_index_ci_cached`), reused across every row of a compile-once scan.
- **M2 — selective + allocation-free decode.** Found the dominant residual: `readCurrent()` eagerly decodes *every* field to `std::string` each row. Added (additive) `DbArea::readCurrentRaw()`, `decodeFieldFromBuffer()`, `fieldNumFromBuffer()` (`xbase.hpp` + `record_view.cpp`) and a selective-decode record view (`make_record_view_raw`), used by `collect_selected_recnos` when a predicate is compiled and no `SET FILTER` is active. Result: **DEC1 became faster than SUM** (a 1-field predicate scan beat a full-field aggregate scan). Committed with M1/M3 as `0f06d1060`.
- **M4 — apply to aggregates.** Extended selective decode to `cmd_aggs` (single `SUM`/`AVG`/`MIN`/`MAX` + `AGGS ALL`), same no-predicate/no-filter gate. Variance-immune within-run `SUM/DEC1` ratio moved 1.078 → 0.999 — the full-decode tax on aggregates is gone. `SUM GPA` value `2.99933e+06` unchanged.

## Evidence

Benchmark `PHASE0_DECODE_COST` on the attested host (normalized to the run's own scan baseline to cancel machine variance):

| metric | M0 floor | after lane | reduction |
|---|---:|---:|---:|
| `DEC1 / SUM` (1-term predicate scan) | 1.97× | 0.93× | 2.1× |
| `DEC3 / SUM` (3-term predicate scan) | 3.62× | 1.30× | 2.8× |
| marginal per predicate term | 16.0 µs/row | 3.7 µs/row | 4.3× |
| aggregate full-decode tax (`SUM/DEC1`) | 1.078 | 0.999 | removed |

Parity: `COUNT FOR GPA>=0` and the 3-term count stayed `1000000`; `SUM GPA` stayed `2.99933e+06`; `REGRESSION ALL` + `SCAN_PARITY` green at every milestone. Because `collect_selected_recnos` is the shared selector, COUNT / LIST FOR / SET FILTER / SCAN-selection / DELETE FOR / RECALL FOR all inherited the change and stayed parity-green.

## Files (committed to dev)

- M0 (`eba9a7012`): `src/cli/expr/fn_date.cpp`, `src/cli/shell_api.cpp`, `src/cli/shell.cpp`, `src/cli/cmd_regression.cpp`, `dottalkpp/data/scripts/pinocchio/ticketb_phase0_decode_cost.dts`.
- M1–M3 (`0f06d1060`): `include/xbase.hpp`, `src/xbase/record_view.cpp`, `include/cli/expr/glue_xbase.hpp`, `src/cli/expr/glue_xbase.cpp`, `include/cli/expr/value_eval.hpp`, `src/cli/expr/value_eval.cpp`, `src/cli/scan_selector.cpp`.
- M4 (maintainer-committed): `src/cli/cmd_aggs.cpp`.
- Lane docs: `src/AIPortal/.../PROJECT_LANE_SCAN_EVALUATOR_OPTIMIZATION_V1_20260722.md` (charter + M0–M4 results log), `src/AIPortal/.../PROJECT_LANE_BULK_RECORD_IO_SCAN_V1_20260722.md` (staged spin-off), session index Lane E.

## Honest reach / open items

- The lane's own falsifiable ≥40× / sub-1s target was **not** reached — and the profiling explains why: after M1–M4 the per-row cost is no longer in the evaluator or field decode. Both a bare aggregate and a 1-field predicate scan sit at ~21 µs/row, essentially all **per-row record I/O** (`gotoRec` + one seek + one read per record). That is the record-iteration subsystem, chartered as the **STAGED Bulk Record-I/O lane** (Phase-0 go/no-go owed; may KILL if already at memory bandwidth).
- **Mirror promotion owed:** `C:\x64base` has M0 only; the M1–M4 code (core `readCurrentRaw`/decoders + glue/value_eval/scan_selector/cmd_aggs) still needs surgical promotion with per-file byte-diff, the same discipline as the M0 promotion.
- Selective decode is **gated** (physical evaluation only when a compiled predicate is present and no `SET FILTER` is active); ordered/bridge/filtered paths retain the full-decode path unchanged. This is deliberate, not a gap.

## Cross-references

- Charter + results: `PROJECT_LANE_SCAN_EVALUATOR_OPTIMIZATION_V1_20260722.md`.
- Spin-off: `PROJECT_LANE_BULK_RECORD_IO_SCAN_V1_20260722.md`.
- Origin: `TICKET_B_TUPLE_NATIVE_INMEMORY_STORE_V1_20260721.md` (Phase-0 KILL).
- Registry: session index `_SESSION_INDEX_AND_CURATION_V1` Lane E; intake AIF-046; dashboard Current Lane State + Session Log.
