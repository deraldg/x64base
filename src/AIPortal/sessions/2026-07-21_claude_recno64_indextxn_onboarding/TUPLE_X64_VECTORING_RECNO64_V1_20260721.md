# Change Package — Tuple / Nav x64 Vectoring (RECNO64 widening)

**Date:** 2026-07-21 · **Status:** `review-needed`
**Author:** Claude (hosted AI), source-read. Outside-AI Delivery Rule: reviewable package.
**Scope:** widen record-number carriers in the **tuple system** and **ordered-nav** layer from 32-bit to 64-bit so x64 (vectored/DBF64) tables above `UINT32_MAX` records are not truncated. Long names and field types are already supported (see §1).

---

## 1. Already supported (no change)

- **Long table & field names + fallback mangling.** The tuple system is `std::string` end-to-end (`TupleColumn.name/field`, `basename_upper`, `A->logicalName()`, `A->dbfBasename()`, `A->fields()[i].name`). No fixed-size buffers, no truncation. And `tuple_builder` already resolves *"authoritative display name by schema or x64 fallback alias"* via `xfg::resolve_field_index_std` — so both the full vectored name **and** its standard-size mangled form (the x64 name-mangling fallback) resolve to the same field. Vectored/long/mangled x64 names flow through as-is.
- **Field types (VFP + x64 extended + custom).** `tuple_builder` does **not** switch on type; it calls `xfg::getFieldAsString(area, field)` and `cli_memo::resolve_display_value` for x64 memo object-ids. So it inherits the full codec set (VFP currency/int/double/datetime, x64 types, and registered custom `fieldcodec` types) transitively. *Action: none in tuple layer; keep `xfg`/`fieldcodec` as the single source of type truth (verify `xfg` coverage separately — asserted current).*

## 2. The gap — RECNO is narrowed to 32-bit at the CLI layer

The engine and the index backend already carry 64-bit recnos:
- `DbArea::recno64()`, `recCount64()`, `gotoRec64()` — 64-bit.
- `cli::order_collect_recnos_asc(area, std::vector<std::uint64_t>&, …)`, `order_stream_display(area, reverse, cb(std::uint64_t recno))` — 64-bit.
- `CdxBackend`/`BUILDLMDB` store recno as **uint64 LE** (8-byte value).

But the CLI tuple + ordered-nav layer narrows them. Truncation catalog:

| File | Symbol | Now | Should be |
|---|---|---|---|
| `src/cli/tuple_types.hpp` | `TupleFragment.recno` | `int` | `std::int64_t` |
| `src/cli/tuple_builder.cpp` | `safe_recno()` | `int` via `recno()` | `std::int64_t` via `recno64()` |
| `src/cli/tuple_builder.cpp` | `get_buffer_override(…, int recno, …)` | `int` | `std::int64_t` |
| `src/cli/db_tuple_stream.hpp` | `cur_recno_`, `max_recno_`, `goto_recno(long)`, `goto_pos(long)` | `long` (32-bit on MSVC) | `std::int64_t` |
| `src/cli/db_tuple_stream.hpp` | `order_recnos_` | `std::vector<uint32_t>` | `std::vector<std::uint64_t>` |
| `src/cli/db_tuple_stream.cpp` | `collect_lmdb_cdx_recnos`: `out.push_back(static_cast<uint32_t>(rn64))` | **truncates uint64→uint32** | keep `uint64_t` |
| `src/cli/db_tuple_stream.cpp` | `safe_rec_count()` via `recCount()` | `long`/int32 | `std::int64_t` via `recCount64()` |
| `src/cli/db_tuple_stream.cpp` | `goto_rec_safe` uses `recCount()`/`gotoRec` | int32 | `recCount64()`/`gotoRec64()` |
| `include/cli/order_provider.hpp` | `OrderPosition.recno` | `uint32_t` | `std::uint64_t` |
| `include/cli/order_provider.hpp` | `IOrderProvider::materializeRecnos(…, std::vector<uint32_t>&)`, `firstRecno/lastRecno → std::optional<uint32_t>` | 32-bit | 64-bit |
| `include/cli/order_iterator_materialized.hpp` / `.cpp` | `MaterializedOrderIterator::recnos_` (`std::vector<uint32_t>`) | 32-bit | `std::uint64_t` |
| `include/cli/order_nav.hpp` | `build_cdx_recnos_from_lmdb`, `cdx_endpoint_from_lmdb`, `cdx_cache_build`, `order_first_recno/last_recno` | parse `uint64` then narrow to `uint32`/`int32`; range-check vs `recCount()` int32 | keep `uint64`; range-check vs `recCount64()` |

**Note:** CNX and INX are inherently 32-bit on-disk formats (their recnos fit in uint32), so widening the *shared* carriers to 64-bit is loss-free for them (values just fit). The widening matters for the **CDX/LMDB (V64)** path. `build_cnx_recnos_from_db` / `load_inx_recnos` can keep emitting into a 64-bit vector unchanged (uint32 → uint64 promotion).

## 3. Widening plan (interface-first, phased)

**Phase A — tuple system (self-contained, ships now).** `tuple_types.hpp` `TupleFragment.recno → std::int64_t`; `tuple_builder.cpp` `safe_recno → recno64()`, `get_buffer_override` recno param → `std::int64_t`. Concrete source in this drop (`tuple_types.hpp`, `tuple_builder.recno64.patch`). Compiles standalone; tuple provenance now carries 64-bit recno. `print_tuple_row` (`<<` int64) unaffected.

**Phase B — ordered-nav carriers. ✅ DELIVERED in this drop** (`db_tuple_stream.hpp` + `db_tuple_stream.cpp`, full replacements). Widened `cur_recno_`/`max_recno_`/`order_pos_`/`last_emitted_recno_` `long`→`std::int64_t`; `order_recnos_` `vector<uint32_t>`→`vector<uint64_t>`; `goto_recno`/`goto_pos`/`order_count`/`current_pos` to 64-bit (non-override, safe); `safe_rec_count`/`goto_rec_safe` now use `recCount64()`/`gotoRec64()`; and **fixed the `collect_lmdb_cdx_recnos` truncation** (`push_back(rn64)`, no `uint32` cast). The CNX/INX (V32) loaders still fill a local `vector<uint32_t>` which is promoted loss-free into the 64-bit carrier, so `order_nav_detail` signatures are untouched (deferred to Phase D). `skip(long)` kept as the base override.

**Phase C — order-provider interface.** `OrderPosition.recno → uint64`, `materializeRecnos(vector<uint64_t>&)`, `firstRecno/lastRecno → optional<uint64_t>`, `MaterializedOrderIterator::recnos_ → vector<uint64_t>`. This is an interface change; enumerate implementors (`order_provider_default.cpp`, `order_iterator_materialized.*`) and all callers before flipping. Do it as one atomic commit so the vtable/signature change is consistent.

**Phase D — `order_nav.hpp` endpoints.** `order_first_recno/last_recno(int32_t&)` → `std::int64_t&`; range-checks against `recCount64()`; the LMDB parsers already decode uint64 — just stop narrowing. Update callers (`order_top/bottom/skip`, `orderhooks::auto_top`).

Suggested order: A (now) → B → D → C. A is loss-reducing immediately; C is the interface churn, done last with all implementors in one commit.

## 4. Guardrail note

Ties to the RECNO64 capability model already in `IIndexBackend::maxRecordNumber()` (CNX=UINT32_MAX, CDX/LMDB=UINT64_MAX). Once carriers are 64-bit, the range-checks should compare against `recCount64()` and reject/annotate a recno beyond a bound-backend's capacity (per the `index_manager.hpp` "reject rather than truncate" note) instead of silently casting.

## 5. Test

- Phase A: run any `TUPLE`/`SMARTBROWSE` on a normal table → unchanged output; `TupleFragment.recno` now `int64` (no visible change until a >2^31 table exists).
- Full: a synthetic DBF64 fixture with a recno > `UINT32_MAX` (or a stubbed `recCount64` returning >2^32 with a sparse index) → ordered `BOTTOM`/`SKIP` and `SMARTBROWSE` position must show the true 64-bit recno, not a wrapped value. Add to `INDEX_X64`/a new `INDEX_X64_WIDE` regression once a wide fixture exists.

## 6. Files in this drop (Phase A + B)

Phase A (tuple system):
- `tuple_types.hpp` — full replacement (`TupleFragment.recno → std::int64_t`).
- `tuple_builder.recno64.patch` — `safe_recno` via `recno64()`, `get_buffer_override` recno param widened, `#include <cstdint>`.

Phase B (ordered-nav carriers):
- `db_tuple_stream.hpp` — full replacement (64-bit members + widened non-override methods).
- `db_tuple_stream.cpp` — full replacement (64-bit carriers, `recCount64`/`gotoRec64`, **`collect_lmdb_cdx_recnos` truncation fixed**, CNX/INX promote via temp uint32 vector).

Apply order: A then B (B `#include`s `tuple_types.hpp` via `tuple_builder.hpp`; both compile together). No interface (vtable) change yet — `order_nav_detail` and `IOrderProvider` untouched.

## 7. Remaining (revised after caller audit)

**Phase C is CANCELLED — it targeted dead code.** A repo-scoped caller audit (see `OBSERVATIONS_STEWARDSHIP` O8) shows the `IOrderProvider` subsystem (`makeDefaultOrderProvider`, `buildActiveOrderSpec`, `DefaultOrderProvider`, `MaterializedOrderIterator`, `OrderPosition`) has **zero callers** — the live surface uses the free-function order primitives instead. Don't widen it; delete or freeze it (separate decision). `DbTupleStream` builds its **own** `order_recnos_` vector, not `MaterializedOrderIterator`.

**The real remaining RECNO64 work (one small coordinated package):**
- **`order_step_cdx(int index_delta, int32_t& out_recno)`** (`include/cli/order_iterator.hpp` + `src/cli/order_iterator.cpp`) → `std::int64_t& out_recno`. The lone 32-bit hole in the *live* order interface (siblings already `uint64`). Caller: `order_nav.hpp::order_skip`.
- **`order_nav.hpp` endpoints** — `order_first_recno/last_recno(int32_t&)` → `std::int64_t&`; `order_top/bottom/skip` recno vars → `int64` + `gotoRec64`/`recCount64` range-checks. The CNX/INX caches stay `uint32` (V32) and promote; the CDX endpoints already decode uint64 — stop narrowing.
- **`smartlist_query.cpp`** (O10) — `process_record(int32_t)` + `gotoRec`/`recCount()` → `int64`/`gotoRec64`/`recCount64`; the `order_iterate_recnos` callback already gets `uint64`.

**Delivered in this drop:**
- **O11 root fix** — `cdx_backend.recno64_cursor.EDITSPEC.md`: widen the `CdxBackend` cursor recno decode `uint32 → uint64`. This is the **most important** RECNO64 fix (the CDX cursor was truncating at the source, under `order_collect_recnos_asc`/`order_stream_display`). Phase B only fixed the raw-scan path; this fixes the cursor path.
- **O10** — `smartlist_query.cpp` (full): `process_record`/`total` → 64-bit + `gotoRec64`/`recCount64`. **Residual:** `RecordConsumer`'s recno param (in `smartlist_query.hpp`) is likely still `int32_t`, so the value re-narrows at the consumer boundary — widen the typedef + its implementers (cmd_smartlist/cmd_list consumer lambdas) to finish.
- **IOrderProvider frozen** (O8) — 3 headers with UNUSED banners (`order_provider.hpp`, `order_provider_default.hpp`, `order_iterator_materialized.hpp`).

**Still coupled / next drop (must land together):**
- **O9** `order_step_cdx(int32_t& out)` → `std::int64_t&` (`order_iterator.hpp` + `order_iterator.cpp`) **and** its caller `order_nav.hpp::order_skip` — interface-coupled, ship as one unit.
- **`order_nav.hpp` endpoints** — `order_first/last_recno(int32_t&)` → `int64_t&`; `order_top/bottom/skip` → `gotoRec64`/`recCount64`; the CDX fallback scanners (`build_cdx_recnos_from_lmdb`/`cdx_endpoint_from_lmdb`, O2) `uint32 → uint64`.
- **`RecordConsumer`** typedef widening (O10 residual above).
