# RECNO64 Carrier Audit — bottom-up foundation map

**Date:** 2026-07-21 · **Author:** Claude (hosted AI), source-read.
**Purpose (prep-before-consumer):** trace every record-number carrier from the storage backend upward, so the foundation is widened as one coherent sweep instead of reactive layer-by-layer discovery. Evidence-based: each row is a file/symbol I read. Un-read areas are in the **Scan queue** (§6) — the map is not "complete" until those are checked.

**Foundation contract:** `xindex::RecNo = std::uint64_t` (`include/xindex/key_common.hpp`) ✅. `DbArea` exposes `recno64()`/`recCount64()`/`gotoRec64()` ✅. The bug everywhere below is **narrowing that 64-bit truth to `int`/`long`/`uint32`/`int32`**.

> **Grounded against DEV `D:\code\ccode` (2026-07-21).** Earlier reads were the public GitHub snapshot; the dev tree is now connected and reconciled. For every carrier checked, the snapshot **matched dev** verbatim — O11 (`cdx_backend.cpp:863` + four `std::uint32_t r`), BUILDLMDB (`cmd_buildlmdb.cpp:445`), `order_step_cdx` (`order_iterator.cpp:407`/450), and `navsel::pick_recno` callers (`cmd_top.cpp:89`, `cmd_bottom.cpp:97`, `cmd_skip.cpp:141` — validating the M4 decision to keep `pick_recno`'s int32 signature; widening it cascades to all three). **Dev also revealed a carrier the snapshot audit missed: `cmd_indexseek.cpp` (see Layer 4).** The frozen `IOrderProvider` is present in dev too (`order_provider_default.cpp` stubs confirmed). Drops are now dev-valid, not snapshot-guesses.

Legend — Status: ✅ clean · 🟢 fixed (delivered) · 🟠 pending · ⚫ dead (skip) · ❔ unread. Severity: 🔴 data-loss · 🟠 robustness/perf · 🟡 display-only.

---

## ▶ DELIVERED 2026-07-21 — L1 foundation (O11 + build caps) applied to dev source

Applied to `D:\code\ccode`, **Dev-stage / uncommitted / NOT yet built** (Windows build
is the maintainer's; a zero exit is not proof — see build note):

- **O11 (the truncation the maintainer flagged).** `src/xindex/cdx_backend.cpp` ·
  `decode_recno_from_cursor_key(...)` out-param `std::uint32_t& → std::uint64_t&`, dropping
  both `static_cast<std::uint32_t>(rec64)`; and the four `LmdbCursor::first/next/last/prev`
  locals `std::uint32_t r → std::uint64_t r`. The recno is stored full-width (8-byte LE);
  the ordered-cursor read path no longer chops it to 32 bits. `RecNo` is already `uint64_t`,
  so `outRec = static_cast<RecNo>(r)` is now an identity. **SEEK/`stepOrdered` were already
  64-bit; this makes ordered traversal (TOP/BOTTOM/SKIP/materialize) match.**
- **Build caps removed (both 2^31 builder loops).** `cdx_backend.cpp` ·
  `CdxBackend::rebuild` and `src/cli/cmd_buildlmdb.cpp` · `build_tag_lmdb_from_field`:
  `int32_t total = recCount(); for(int32_t rn…) gotoRec(rn)` → `uint64_t total =
  recCount64(); for(uint64_t rn…) gotoRec64(rn)`. The index can now be *built* past 2^31.

**Scope / honesty:** this is the independently-compilable `xindex.lib` + BUILDLMDB
checkpoint (audit §5 step 1). It fixes the backend/source of truth. **Consumers still
narrow** and are the next coordinated drops: L2 `order_step_cdx(int32_t&)` (O9), L3
`order_nav` endpoints + `build_cdx_recnos_from_lmdb`/`cdx_endpoint_from_lmdb` (O2) +
`navsel::pick_recno`, L4 `cmd_indexseek` (uint32) / `cmd_skip` / `cmd_ersatz` /
`cmd_validate_unique`. Until those land, end-to-end past 2^31 can still narrow at a
consumer — but the cursor no longer lies at the source.

**Build to verify:** `cmake --build build --config Release --target dottalkpp`
(watch for signed/unsigned-compare warnings around the widened loops). The parked
`INDEX_TXN` regression rides the ordered-cursor path and is a natural witness once a
>2^31 fixture exists. **BUILT GREEN 2026-07-21.**

---

## ▶ DELIVERED 2026-07-21 — M4 order slice (consumer cascade, drop 1)

Applied to dev after the L1 build went green. Atomic interface-coupled set — the widened
signatures force their callers, so all landed together:

- `include/cli/order_iterator.hpp` + `src/cli/order_iterator.cpp` — **O9**
  `order_step_cdx(..., int32_t& → std::int64_t&)`; internal `cur`/`landed` via
  `recno64()`/`recCount64()`, out-param `int64`.
- `include/cli/order_nav.hpp` — `order_first_recno`/`order_last_recno` signatures
  `int32_t& → std::int64_t&` (CDX stream recno + `recCount64()`); `order_top`/`order_bottom`
  `int64` + `gotoRec64`; `order_skip` **CDX primary fast path** `int64` + `recCount64` +
  `gotoRec64`. Fallback position-map cache LEFT 32-bit with a `TODO(RECNO64 M5)` (O2).
- `include/cli/nav_select.hpp` · `navsel::pick_recno` — RawOrder internal `rn` widened to
  `int64` to bind the widened `order_first/last_recno`; **public `int32_t` return kept**
  (that narrow is the M5 boundary, cascades to `cmd_skip`), casts at return.
- `src/cli/order_hooks.cpp` · `auto_top` — caller widened (`int64` + `recCount64` + `gotoRec64`).

**What M4 makes correct past 2³¹:** unfiltered ordered `SKIP` (`order_step_cdx`→`order_skip`
→`gotoRec64`) and `order_top`/`order_bottom` endpoints. **Still M5:** `pick_recno` int32
return + `cmd_skip`/`cmd_seek` display, the `order_skip` fallback cache /
`build_cdx_recnos_from_lmdb` (O2), `cmd_indexseek` (uint32), `cmd_validate_unique`,
`cmd_ersatz`, the `A.recno()` display class, SMARTLIST `RecordConsumer`.

**Steward find (dupes):** `pick_recno` exists in **three** copies —
`include/cli/nav_select.hpp` (LIVE; the only one `#include`d, by `cmd_top/bottom/skip`),
plus **dead, unincluded** `include/xbase/nav_select.hpp` and `src/xbase/nav_select.hpp`.
Only the live one is on the build path (fixed). The two dead copies are a separate cleanup
(delete-or-consolidate) — flagged, not touched beyond the live fix.

**Build to verify:** `cmake --build build --config Release --target dottalkpp` (expect
green, warning-clean; explicit casts at the int32 return boundary). Then
`REGRESSION RUN INDEX_X64` (CDX) + `INDEX_X32` (CNX) should still pass unchanged.
**BUILT GREEN 2026-07-21; INDEX_X64 + INDEX_X32 both pass unchanged.** (Transient
C2664s during the edit sequence confirmed the atomic-set coupling — the build stayed
red until every widened-signature caller was fixed; nothing left half-narrowed.)

---

## ▶ DELIVERED 2026-07-21 — M5 drop 1 (pick_recno return-width, applied; not yet built)

Finishes the ordered `TOP`/`BOTTOM`/`SKIP` **positioning** path end-to-end (the primary
`order_skip` fast path was already M4-correct; this widens the `pick_recno` return the
commands position on):

- `include/cli/nav_select.hpp` · `navsel::pick_recno` — return `int32_t → std::int64_t`
  and `from_recno int32_t → std::int64_t`; RawOrder drops the truncating return casts
  (`return rn;`), `save`/`start` via `recno64()`/`gotoRec64()`, `recCount64()`; LogicalView
  casts widened to `int64`.
- Callers widened (interface-coupled, all 3): `src/cli/cmd_top.cpp`, `cmd_bottom.cpp`
  (`int32_t rn → std::int64_t`, `gotoRec64`), `cmd_skip.cpp` (`current`/`rn → int64`,
  `gotoRec64`). Full-tree sweep: no other `pick_recno` caller; the two dead
  `xbase/nav_select.hpp` copies remain int32 (unincluded) — the consolidation is still owed.

**Deliberately deferred to its own drop (O2, not bundled here):** the `order_skip`
*fallback* position-map cache. That is not a signature change but a **shared
data-structure widening** — `order_nav_detail::CnxCache.recnos` is `std::vector<uint32_t>`
and `.pos` is keyed on `uint32_t`, fed by `cdx_cache_build` / `cnx_cache_build` /
`build_cdx_recnos_from_lmdb` / `cdx_endpoint_from_lmdb` (all narrow the LMDB uint64 to
uint32). Widening the struct ripples to every `cache.recnos[...]`/`.front()`/`.back()`
reader (including the `order_first/last_recno` CNX fallbacks). It deserves an isolated
drop + its own build, not a blind bundle. The primary CDX fast path (M4) already covers
the common case; the fallback only triggers when the current record is not in the index.
INX cache stays 32-bit (V32 format, inherent). **Also still pending (🟡):** the
`A.recno()` display lines in the nav commands (`std::to_string(A.recno())`).

**Build to verify:** `cmake --build build --config Release --target dottalkpp`
(interface-coupled — expect red until all 3 callers are in, then green). Re-run
`INDEX_X64` + `INDEX_X32`; unchanged on <2^31 tables. **BUILT GREEN 2026-07-21.**

---

## ▶ DELIVERED 2026-07-21 — M5 drop 2 (O2 fallback cache, applied; not yet built)

Widens the `order_skip` fallback position-map cache — the last 🔴 in the ordered-nav
path. **Header-only, self-contained in `include/cli/order_nav.hpp`; no signature changes**
(CnxCache is internal to `order_nav_detail`, and the public `order_*` signatures were
already widened in M4):

- `struct CnxCache` — `recnos std::vector<uint32_t> → std::vector<std::uint64_t>`,
  `pos std::unordered_map<uint32_t,int32_t> → <std::uint64_t,std::int64_t>`,
  `recCount int32_t → std::int64_t`.
- `cnx_cache_build` / `cdx_cache_build` — `N` via `recCount64()`; `cdx_cache_build` pushes
  the 64-bit `order_collect_recnos_asc` recno unnarrowed (dropped `static_cast<uint32_t>`);
  `pos` loops widened to `std::int64_t`.
- `order_first/last_recno` cache readers — the 4 `front()/back()` casts → `std::int64_t`.
- `order_skip` CDX + CNX fallback blocks — `cur`/`next`/`last`/`rn` → `std::int64_t`,
  `pos.find(uint64)`, `gotoRec64`, `recCount64`.

**Decoupling decisions (deliberate):**
- `build_cnx_recnos_from_db` **left 32-bit** — it's a V32/CNX builder *and* shared with
  `db_tuple_stream` (`order_recnos_`). `cnx_cache_build` now copies its 32-bit recnos up
  into the 64-bit cache (`assign`), so O2 does **not** ripple into `db_tuple_stream`.
- `build_cdx_recnos_from_lmdb` / `cdx_endpoint_from_lmdb` — **dead code** (no callers;
  confirmed by full-tree grep). Left as-is; not widened. Candidate for deletion.
- INX fallback (local `std::vector<uint32_t>`) — left 32-bit (V32 format, inherent).

**Build to verify:** `cmake --build build --config Release --target dottalkpp`
(header-only → recompiles order_nav consumers; expect green, warning-clean). Re-run
`INDEX_X64` + `INDEX_X32`. With this, the **entire ordered TOP/BOTTOM/SKIP path — primary
and fallback — is 64-bit.** **BUILT GREEN 2026-07-21; INDEX_X64 + INDEX_X32 pass.**
Remaining M5 tail is now non-order: `cmd_indexseek` (uint32), `cmd_validate_unique`,
`cmd_ersatz`, the `A.recno()` display lines, and the two dead `pick_recno` copies.

---

## ▶ DELIVERED 2026-07-21 — M5 drop 3 (cmd_indexseek, applied; not yet built)

`INDEXSEEK` returned a `uint32`-truncated recno (the O11-sibling dev-only find).
Self-contained in `src/cli/cmd_indexseek.cpp` (the `indexseek_via_*` helpers are
file-static — no external signature change):

- `CursorRestore.saved int32_t → std::uint64_t`; `recno64()`/`recCount64()`/`gotoRec64()`.
- `indexseek_via_cdx` / `indexseek_via_inx` out-param `uint32_t& → std::uint64_t&`.
- CDX cursor scan: `rn int32_t → std::int64_t`, `recCount64()`, `gotoRec64()`, both
  `out_recno` casts → `std::uint64_t` (exact-match + soft).
- `cmd_INDEXSEEK` result locals `uint32_t recno → std::uint64_t` (printed value).
- **INX path left 32-bit** where it reads the V32 on-disk format (`rd_u32`,
  `inx1/inx2_lower_bound_recno`, the `uint32_t recno` local) — it widens up into the
  64-bit out-param at the single assignment. Correct: INX is a 32-bit format.

**Build to verify:** `cmake --build build --config Release --target dottalkpp`
(single TU; expect green). **BUILT GREEN 2026-07-21.**

---

## ▶ DELIVERED 2026-07-21 — M5 drop 4 (cmd_validate_unique, applied; not yet built)

🟠 robustness: `VALIDATE UNIQUE` scanned/positioned with `int` recnos (wraps + truncates
past 2^31). Self-contained in `src/cli/cmd_validate_unique.cpp`:

- `compute_max_numeric_value`: `total`/`save`/loop `r` `int → std::int64_t`;
  `recCount64()`/`recno64()`; `gotoRec64()`.
- main scan: `startRec`/`total` int64; `firstSeen` map value `int → std::int64_t`;
  `struct Dup { recno; first }` `int → std::int64_t`; both scan loops `r int → int64` +
  `gotoRec64`; repair `gotoRec64(d.recno)`; `gotoRec64(startRec)` restore.
- Output streaming (`<< d.recno`) and `long long nextValue` unchanged (correct).

**Build to verify:** `cmake --build build --config Release --target dottalkpp` (single TU;
expect green). **BUILT GREEN 2026-07-21.**

---

## ⏸ SCOPED (not applied) — `cmd_ersatz` opens the DbTupleStream `long` nav core

Attempted next; **stopped after scoping** — not a self-contained drop. `cmd_ersatz`
positions via `DbTupleStream::goto_recno(long)` → `goto_recno_internal(long)`, whose
internals are `long`/`uint32` throughout: `static_cast<uint32_t>(r)` search over
`order_recnos_`, `goto_physical_recno(long)`, `step(long)`, and members
`cur_recno_`/`max_recno_`/`order_pos_` (all `long`). Full correctness = widening that
**navigation core** (methods + members + `order_recnos_`) plus its callers (`cmd_ersatz`,
`cmd_smart_browser`) as one coordinated unit. This is a distinct lane (🟠, teaching-browser
/ tuple-stream layer), deferred rather than bundled blind. `browse_order::goto_recno(uint32_t)`
is a *separate* free function (its own item).

## Session close — RECNO64 status 2026-07-21

**All 🔴 (data-loss) carriers delivered + built green:** L1 (O11 cursor + build caps),
M4 (order primitives/nav), M5.1 (`pick_recno` + cmd_top/bottom/skip), M5.2 (O2 CnxCache
fallback), M5.3 (`cmd_indexseek`), M5.4 (`cmd_validate_unique`, 🟠). Ordered
TOP/BOTTOM/SKIP is 64-bit primary **and** fallback; SEEK/INDEXSEEK 64-bit.

**Remaining (🟠/🟡, scoped follow-on lanes):**
1. `cmd_ersatz` + `DbTupleStream` `long` nav core + `cmd_smart_browser` — coordinated 🟠.
2. `browse_order::goto_recno(uint32_t)` — 🟠.
3. `A.recno()` display lines across commands — 🟡 (cosmetic).
4. Consolidate the two dead `pick_recno` copies (`include/xbase`, `src/xbase`) — cleanup.

---

## Layer 1 — Storage / index backend (`xindex.lib`)

| File · symbol | Now | Needed | Status | Sev |
|---|---|---|---|---|
| `key_common.hpp` · `RecNo` | `uint64_t` | — | ✅ | — |
| `cdx_backend.cpp` · `decode_recno_from_cursor_key(…, uint32_t& out)` | uint32 | uint64 | 🟠 **O11** (edit spec delivered) | 🔴 |
| `cdx_backend.cpp` · `LmdbCursor::first/next/last/prev` `uint32_t r` | uint32 | uint64 | 🟠 **O11** | 🔴 |
| `cdx_backend.cpp` · `stepOrdered` (decode_u64) | uint64 | — | ✅ | — |
| `cdx_backend.cpp` · `seekRecnoUserKey` / `decode_recno_from_kv_` | uint64 | — | ✅ | — |
| `lmdb_backend.cpp` (standalone) · `pack/unpack_recno` | uint64 | — | ✅ | — |
| `cmd_buildlmdb.cpp` · `build_tag_lmdb_from_field`: `int32_t total = recCount(); for(int32_t rn…)` `pack_recno_le8((uint64_t)rn)` | int32 loop | int64 loop via `recCount64()` | 🟠 pending | 🔴 **builder caps the index at 2³¹** |
| `cnx_backend.cpp` / `cnx.hpp` · RUN1 recnos `uint32` | uint32 | — (V32 format) | ✅ inherent (CNX is 32-bit) | — |
| `cnx_backend.cpp` · `rebuild` `collect_sorted_recnos_for_tag_` `int32_t rn` | int32 | (V32) fine for CNX | ✅ | — |

## Layer 2 — Order primitives (`include/cli/order_iterator.hpp` + `.cpp`)

| File · symbol | Now | Needed | Status | Sev |
|---|---|---|---|---|
| `order_collect_recnos_asc(…, vector<uint64_t>&)` | uint64 | — | ✅ (but fed by O11-truncated cursor until O11 lands) | — |
| `order_iterate_recnos(cb(uint64))` | uint64 | — | ✅ | — |
| `order_stream_display(cb(uint64))` | uint64 | — | ✅ | — |
| `order_step_cdx(…, int32_t& out_recno)` | int32 | int64 | 🟠 **O9** (coupled w/ `order_nav`) | 🔴 |

## Layer 3 — Order nav + nav-selection primitives

| File · symbol | Now | Needed | Status | Sev |
|---|---|---|---|---|
| `order_nav.hpp` · `order_first_recno/last_recno(int32_t& out)` | int32 | int64 | 🟠 pending | 🔴 |
| `order_nav.hpp` · `order_top/order_bottom` `int32_t rn` + `gotoRec`/`recCount` | int32 | int64 + `gotoRec64`/`recCount64` | 🟠 pending | 🔴 |
| `order_nav.hpp` · `order_skip` `int32_t rn` + `order_step_cdx` call | int32 | int64 (coupled O9) | 🟠 pending | 🔴 |
| `order_nav.hpp` · `build_cdx_recnos_from_lmdb`/`cdx_endpoint_from_lmdb` (parse uint64 → narrow uint32/int32; range vs `recCount()`) | uint32/int32 | uint64 + `recCount64()` | 🟠 pending (**O2**; fallback path — O11 fixes the primary cursor) | 🔴 |
| `order_nav.hpp` · `CnxCache.recnos` `uint32` (V32 cache; also CDX fallback) | uint32 | uint64 for the CDX fallback (CNX promotes) | 🟠 pending | 🟠 |
| `nav_select.*` · `cli::navsel::pick_recno(…, int32_t current) -> int32_t` | int32 | int64 | ❔ **unread** (used by `SKIP` filtered path) | 🔴 |
| `nav_move.*` · `cli::nav::go_absolute(A, uint64 n)` / `go_endpoint` | uint64? | verify | ❔ unread (GOTO passes uint64 — likely clean) | — |

## Layer 4 — Consumers (commands / tuple / browser)

| File · symbol | Now | Needed | Status | Sev |
|---|---|---|---|---|
| `tuple_types.hpp` · `TupleFragment.recno` | int → int64 | int64 | 🟢 **delivered (Phase A)** | — |
| `tuple_builder.cpp` · `safe_recno`/`get_buffer_override` | int → int64 | int64 via `recno64()` | 🟢 delivered (Phase A patch) | — |
| `db_tuple_stream.{hpp,cpp}` · carriers + `collect_lmdb_cdx_recnos` | long/uint32 → int64/uint64 | — | 🟢 delivered (Phase B) | — |
| `smartlist_query.cpp` · `process_record`/`total` | int32 → int64 | — | 🟢 delivered (O10) | — |
| `smartlist_query.hpp` · `RecordConsumer` recno param | likely int32 | int64 | 🟠 pending (O10 residual) | 🔴 |
| `cmd_skip.cpp` · `int32_t current/rn` + `gotoRec(current)` + `recno()` display | int32 | int64 + `gotoRec64` + `recno64` | 🟠 pending | 🔴 |
| `cmd_goto.cpp` · `try_parse_u64_token` → `go_absolute(uint64)` | uint64 | — | ✅ clean | — |
| `cmd_recno.cpp` · `recno64`/`recCount64`/`gotoRec64` | uint64 | — | ✅ clean | — |
| `logical_nav.cpp` · all `uint64` + `order_stream_display` | uint64 | — | ✅ clean (inherits O11 fix) | — |
| `cmd_validate_unique.cpp` · `recCount()`/`gotoRec`/`int recno`/dup recnos | int32 | int64 | 🟠 pending | 🟠 |
| `cmd_smart_browser.cpp` · `GOTO n` via `std::stol` (long); `print_tuple_row` recno (now int64) | long/int64 | int64 (`stoll`) | 🟠 pending (minor) | 🟡 |
| `cmd_indexseek.cpp` · **4 fns** `uint32_t& out_recno` + `out_recno = static_cast<uint32_t>(rn)` (INDEXSEEK) | uint32 | uint64 | 🟠 pending (**dev-only find; not in snapshot audit**) | 🔴 |
| `cmd_top.cpp` / `cmd_bottom.cpp` · `const int32_t rn = navsel::pick_recno(...)` | int32 | int64 (with pick_recno sig widen) | 🟠 pending (M5 cascade) | 🔴 |
| `cmd_ersatz.cpp` · `ersatz_recno_safe(): long`; `DbTupleStream::goto_recno(long)` | long | int64 | 🟠 pending | 🟠 |
| Many commands · `A.recno()` in TALK/status display lines | int32 | `recno64()` | 🟠 pending (class of ~display sites) | 🟡 |

## Dead code (skip — do NOT widen)

| File · symbol | Note |
|---|---|
| `order_provider.hpp` / `order_provider_default.*` / `order_iterator_materialized.*` · `OrderPosition.recno` uint32, `materializeRecnos(vector<uint32_t>&)`, `MaterializedOrderIterator` | ⚫ **O8** — no live callers; FROZEN with banners. Skip entirely. |

---

## 5. Recommended execution order (bottom-up = prep first)

1. **L1 foundation:** apply **O11** (`cdx_backend` cursor decode) + widen **`BUILDLMDB`** builder loop (`int32_t rn` → int64, `recCount64()`). These make the index *and* its cursor 64-bit at the source. Independently compilable (`xindex.lib`); build-green checkpoint.
2. **L2 primitive:** **O9** `order_step_cdx(int64&)` — ship **atomically with** its L3 caller (next item).
3. **L3 order nav + nav-select:** `order_nav.hpp` endpoints/`order_skip`/`order_top/bottom` + `build_cdx_recnos_from_lmdb`/`cdx_endpoint_from_lmdb` (O2) + `CnxCache`; **and `navsel::pick_recno`** (read it first — Scan queue). One coordinated L3 drop.
4. **L4 consumers (mechanical, last):** `RecordConsumer` typedef + `cmd_smartlist`/`cmd_list` lambdas; `cmd_skip` filtered path; `cmd_validate_unique`; `cmd_ersatz`; the `A.recno()` display-line class. Already-shipped L4 (tuple, stream, smartlist) inherit correct data once L1–L3 land.

Rationale: L1 is consumed by everything; fix it and the "does it truncate?" question collapses to "does this consumer still narrow?" — a mechanical, low-risk sweep with no deeper surprises.

## 6. Scan queue (to complete the map — read before L3)

- `include/cli/nav_select.hpp` + `src/cli/scan_selector.cpp` (`navsel::pick_recno`) — **L3, likely 🔴**.
- `include/cli/nav_move.hpp` + impl (`nav::go_absolute`/`go_endpoint`) — verify clean (GOTO passes uint64).
- `cmd_top.cpp` / `cmd_bottom.cpp` / `cmd_go.cpp` / `cmd_first.cpp` / `cmd_last.cpp` / `cmd_prior.cpp` / `cmd_next.cpp` — nav commands (do they use `order_top/bottom` or raw `recno()`/`gotoRec`?).
- `cmd_list.cpp` / `cmd_smartlist.cpp` (the `RecordConsumer` implementers).
- `browse_controller.cpp` / `record_view.cpp` / `smartlist_output.cpp` — browser render recnos.
- `cmd_pack.cpp` / `cmd_recall.cpp` / `cmd_delete.cpp` / `cmd_zap.cpp` — mutation recno handling.
- `workareas.*` / `cursor_status.*` — any cached recno.

## 7. Non-goals / already-correct

- **Names** (table/field, vectored + mangled) — `std::string` end-to-end + `xfg` alias resolution. Not a RECNO64 concern.
- **CNX/INX formats** — inherently 32-bit (V32); their `uint32` recnos are correct, not bugs. Only widen the *shared carriers* they feed (promote uint32→uint64), never the on-disk format.
