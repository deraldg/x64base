# DotTalk++ Contract Intake Queue v1

Status: active queue.

## Purpose

This queue captures contract candidates that are visible but not yet fully
registered, proven, or normalized.

Items should either graduate into `CONTRACT_REGISTRY_V1.md`, become source/test
work, or be marked rejected/superseded.

## Open Intake

| Candidate | Kind | Evidence now | Needed next |
| --- | --- | --- | --- |
| Command usage extraction as general contract model | Usage | Source-defined in `src/meta/metacollect.cpp` | Registry crosswalk from harvested commands to contract rows |
| `@dottalk.contract` header annotations | Source/provenance | Source-defined in include headers | Scanner report and policy for annotation fields |
| File format contracts for x64/v128/DBF/memo/index families | Data | Scattered source/docs | Central file-format contract index |
| Build option and dependency contracts | Build | CMake/options/docs scattered | Build contract document and registry rows |
| Destructive command safety contracts | Safety/usage | Runtime/source scattered | Command-by-command safety matrix |
| Import/export locale contracts | Data/safety | Design need identified | Contract doc or section under value/locale |
| GUI request/event/result schema | UI/runtime | Source skeleton | Schema contract and Python/C++ mirror checks |
| Python/C++ binding contract | Runtime/binding | Early pydottalk/preview behavior | Binding contract once pydottalk surface stabilizes |
| Test fixture contracts | Test/data | Fixtures exist ad hoc | Fixture manifest and purpose map |
| Shared command-message dedup (catalog) | Normalization/i18n | During the messaging pass, identical/near-identical message strings recur per command, each getting its own `COMMAND:X`-owned `MessageId`: e.g. `"No table is open. Use USE <file> first."` (DELETE `DeleteNoTableOpenText`, RECALL `RecallNoTableOpenText`, likely more), the `"warning - active index/order may now be stale after ... Rebuild/rebind indexes if needed."` index-stale warning (DELETE `DeleteIndexStaleWarningText` w/ `{stage}`, RECALL `RecallIndexStaleWarningText`), and the `"{count} deleted"`/`"{count} recalled"` result-line family. Catalog is uniformly `COMMAND:`-owned (1069 entries), so no shared-owner convention exists yet. | After the per-command walk maps every variant: decide a shared-owner tag (e.g. `COMMON`) or canonical `MessageId`s for no-table-open, index-stale, and count-result families; migrate call sites; keep per-command IDs only where wording legitimately differs. Do it as one deliberate sweep, not ad hoc mid-walk (which would split the convention). |
| Shared field-store pipeline for data-mutation commands | Normalization/dedup | `REPLACE`, `REPLACE_MULTI`, and `CALCWRITE` each re-implement the same store pipeline: RHS eval → currency normalize (`cli_currency::validate_and_normalize_currency_pair_field`) → x64 memo convert (`memo_field_store::build_x64_memo_stored_value`) → type validate/normalize (`validate_field_value_for_store` + `normalize_date/logical/numeric`) → buffered-vs-direct write. `cmd_replace.cpp` additionally carries its own legacy lexer/parser (`eval_legacy_replace_expr`) for quoted strings / string fns / field refs / `+` concat that overlaps the newer `dottalk::expr::eval_rhs` (`rhs_eval`) layer. Three commands, one pipeline, three copies. | Extract one shared field-store helper (evaluate → currency → memo → validate → write) called by all three; reconcile REPLACE's legacy parser against `rhs_eval` (keep or retire). Payoff: one place to set `set_last_error` per failure mode when ERRORSTOP lands (vs three). Data-mutation code — needs its own regression before extraction. Pairs with the ERRORSTOP and messaging-normalization rows below. |

## Runtime Findings — Observed Behavior Awaiting a Contract Decision

Surfaced by the MCC databuild session, 2026-07-14. Full transcripts and context
in `docs/maintenance/SESSION_CLOSEOUT_MCC_DATABUILD_2026-07-14.md`. These are
runtime observations, not yet contracts: source may be correct and the docs
wrong, or vice versa. Each needs a maintainer decision before it becomes a
registered rule or a source fix (through
`SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`).

| Finding | Kind | Evidence now | Needed next |
| --- | --- | --- | --- |
| `SETLMDB PHYSICAL` is not a valid form; fails as missing container `PHYSICAL.cdx.d`. Correct form `SETLMDB 0`. | Usage/runtime | Runtime transcript 2026-07-14; also failing silently in `canaries/mcc_exhaustive_full_regression_canaries_lmdb.dts` | Decide: fix the canary, and either accept `SETLMDB 0` as the only clear form or add `PHYSICAL` as an alias in `cmd_setlmdb.cpp`. |
| `BUILDLMDB` and `SETLMDB` report different LMDB env directories for the same container (`LMDB\x64\...` vs `INDEXES\x64\...`). `SET INDEX` agrees with `BUILDLMDB`. | Runtime/data/path | Runtime transcript 2026-07-14 | Reconcile the env-path resolution in `cmd_setlmdb.cpp` against `cmd_buildlmdb.cpp`; two of three surfaces agree. |
| `SHOW TABLE` misreports the table path (drops `dbf\<lane>`), and on a VFP readback reported an `indexes\x32` container while the VFP one was attached. Behavior correct, display wrong. | Runtime/display | Runtime transcript 2026-07-14 | Fix the `SHOW TABLE` path/index display. It is exactly the kind of misreport that sends work chasing ghosts. |
| Bare `ASC` errors (`ASC expects 1 argument(s)`) and does not undo `DESC`; runner continues, leaving descending order silently active. | Usage/runtime | Runtime transcript 2026-07-14 | Decide whether bare `ASC` should reset ascending, or document `SET ORDER TO TAG` as the canonical reset. |
| `CREATE X64 ... (SID I)` truncates an 8-digit key: bare `I` → `I(4)` keeps ~4 high-order digits (`50000000` → `5000`), corrupting the stored value, the index key (broken order + failed SEEK) and the display; `N(8)` holds it. `LNAME` (`C(20)`) indexed fine on the same rows. | Type/data/runtime | Pinocchio 1M run, `SESSION_CLOSEOUT_PINOCCHIO_PHASE1_2026-07-15.md`; clean A/B (I vs N(8)) | Decide: is bare `I` a 4-byte int32 (then this is a store/index/display bug for wide values), or does `I` need an explicit width for 8-digit keys? Fix or document in `cmd_create.cpp`. |
| `SMARTLIST NEXT <n>` restarts from the top after `SEEK`: `SEEK 50000500` reports "Found at 501 / 2749" correctly, but the following `SMARTLIST NEXT` lists from record 1, not the sought record — consistent on parent and child. | Usage/runtime | Pinocchio 1M / 5.5M run, same closeout | Decide whether `SMARTLIST NEXT` should continue from the current (sought) record; if the implicit `TOP` is intended, document it. |
| `SET TIMER` is not exercised per-command when nested under `DOTSCRIPT` / `DOTSCRIPT TRACE`: the CLI treats `DOTSCRIPT` as one command, so the timer wraps the whole script (one aggregate) and never descends to the nested lines. | Runtime/tooling | Pinocchio measure runs; maintainer-diagnosed | Decide whether nested lines under `DOTSCRIPT` should be individually timed, or document that per-command timing requires top-level REPL execution. |
| `TOP` (position at first record in tag order) is O(n) and dominates all query cost: 19.5s @1M (SID), 23.2s @1M (LNAME), 72.2s @5.5M (SID) — ~115s of a ~116s battery. Time scales with table size, not with the single record it returns. Every other op on the same tables is sub-0.35s: `SEEK` 3–18ms, `COUNT` ~1.5ms, `SMARTLIST NEXT` 50–350ms, `LIST FOR` (first 20) 0.24s. `SEEK` proves the LMDB tag supports fast positioning, so `TOP` should be able to jump to the first key rather than walk to it. | Performance/runtime | Pinocchio Phase 1.1 per-command capture, `tmp/pinocchio/measure_timed`, `SESSION_CLOSEOUT_PINOCCHIO_PHASE1_2026-07-15.md` | Profile `TOP` under an active LMDB tag order; determine why it does not use the tag's first-key entry the way `SEEK` uses key lookup. Likely the single biggest at-scale performance win. |
| DotScript does not stop on error, and command failures do not propagate. Handlers are `void` (`Handler = std::function<void(DbArea&, istringstream&)>`), so `registry().run`/`shell_execute_line`'s bool means "recognized," not "succeeded." Converting every handler to bool is the expensive path and loses severity. | Runtime/design | `cmd_dotscript.cpp` run loop (~L550); `shell_api.cpp` `shell_execute_line`; `include/cli/command_registry.hpp` Handler type | **ERRORSTOP proposal:** add `SET ERRORSTOP ON\|OFF\|WARN`; in the DotScript loop `clear_last_error()` before each line and after `shell_execute_line` break when `get_last_error().get_severity() == error` (or `>= warning` under WARN). No signature change: reuse the existing `xbase_error_context.hpp` thread-local. Incremental — commands set the code at failure sites via `cmdout::print_error`. Freebie: map `shell_execute_line`'s existing `false` to `set_last_error(e_unknown())` for stop-on-unknown-command. **Default OFF (decided 2026-07-15): the regression suite runs with stop-on-error off — negative/expected-error cases execute past failures; fail-fast is opt-in via `SET ERRORSTOP ON`.** |
| Messaging/output is not normalized: 88/184 `cmd_*.cpp` route through `cli::cmdout`, 98 still raw `std::cout`, 0 use severity-coded `print_error/print_warning`, and `cmdout` is not wired to `set_last_error`. The localized, severity-aware delivery vehicle already exists (`cmdout` + `message_catalog` + Phase 23 locale spine) but is ~half-adopted. | Normalization/i18n/runtime | `src/cli/command_output.*`; `message_catalog.*`; `LOCALE_PHASE23*`; ledger in `MESSAGING_NORMALIZATION_LANE_PLAN_V1.md` | Open the **Messaging Normalization lane**: wire `cmdout::print_error/print_warning` → `set_last_error` first (pairs with ERRORSTOP above), then walk the registry routing diagnostics through `cmdout` with catalogued `MessageId`s. Boundary: localize diagnostics, NOT tabular result payload (`LIST`/`DUMP`/`SMARTLIST` stay on the data channel). See lane plan. |

## Recently Seeded

| Contract | Current state |
| --- | --- |
| Value/Locale/Collation Contract | Design-intended, registered |
| Database Safety Contract | Design-intended, registered |
| Windowed Application Contract | Design-intended, registered |
| Contract Lifecycle | Active process contract |
| Contract Registry | Active registry |

## Queue Rules

- Do not leave a candidate here indefinitely without a next action.
- Prefer graduating candidates into the registry with honest low evidence over
  losing them.
- Mark rejected ideas explicitly when they were considered and declined.
- Link to reports or source when the candidate becomes stronger than design
  intent.

