# Steward Package — RECNO64 nav/index consumer residual (AIF-027 follow-on)

**Disposition (CORRECTED 2026-07-21 vs live intake queue):** **FOLD UNDER `AIF-027`** as a milestone/residual — **NOT a new lane.** `AIF-041` is the BETA-1 stabilization lane — **do not reuse it** (earlier draft wrongly proposed 041). This work also **feeds AIF-041** M1 (RECNO64 coverage) / M2 / M3. See `HANDOFF_RECEIVED_RECONCILIATION_V1_20260721.md`.
**Parent lane:** `AIF-027` RECNO64 end-to-end 64-bit record addressing (`docs/maintenance/RECNO64_END_TO_END_64BIT_ADDRESSING_LANE_V1.md`).
**Parent project:** `project.x64base` (per AIF-040 Project ⊃ Lane ⊃ Milestone; `labtalk/registries/projects.yaml`).
**Owner / authority:** Derald (maintainer). **Drafting steward:** Claude (hosted AI). **Status:** `review-needed` (source-evidenced; not built).
**Evidence appendix:** `RECNO64_CARRIER_AUDIT_V1_20260721.md` (bottom-up carrier map) + `OBSERVATIONS_STEWARDSHIP_V1` (O1–O11).
**Recorded / maintained / assigned:** proposed dashboard row + intake row below; assign under `project.x64base` RECNO64 lane. This file is the maintainable record; update its status as slices land.

---

## 1. Why this exists (the drift)

The `AIF-027` dashboard row states **M4-5 DONE + green**, proven by `dottalkpp_recno64_boundary_test` + `dottalkpp_recno64_sparse_e2e_test` — the engine reads distinct records at recno 2³¹+1/+2 off a **sparse** x64 table. That proves **storage/positioning addressing** past 2³¹ (`gotoRec64`/`recno64`/`checked_record_pos_`).

It does **not** prove **index-ordered / nav / list** addressing past 2³¹, and the source agrees it isn't done:
- `include/cli/nav_select.hpp` — `NOTE(RECNO64 M3) … pick_recno's int32_t return (and the RawOrder path's order_nav int32_t API) still narrow … until the order_nav / pick_recno widening slice (M4) lands.`
- `src/cli/cmd_seek.cpp` — `NOTE(RECNO64 M4-5): SEEK positioning (gotoRec/recCount below) is still int32 nav-consumer; explicit narrow until that slice lands.`

A sparse table has 3 rows at high recnos — no populated **index** of billions to walk — so ordered nav / CDX scan / SMARTLIST past 2³¹ were never exercised. **This package is that residual slice.**

## 2. Scope — the nav/index consumer carriers still narrowing (by layer → your M-mapping)

| # | Carrier | File | Now→Need | Your milestone |
|---|---|---|---|---|
| O11 | CDX cursor decode `uint32` | `cdx_backend.cpp` `decode_recno_from_cursor_key`/`LmdbCursor` | uint32→uint64 | foundation (below "M4-5"; the sparse test didn't hit the cursor) |
| — | BUILDLMDB builder loop `int32_t rn` over `recCount()` | `cmd_buildlmdb.cpp` | int32→int64 + `recCount64()` | foundation (index only built to 2³¹) |
| O9 | `order_step_cdx(int32_t& out)` | `order_iterator.hpp/.cpp` | int32→int64 | M4 (order primitive) |
| — | `order_first/last_recno`, `order_top/bottom/skip`, `build_cdx_recnos_from_lmdb`/`cdx_endpoint_from_lmdb` | `order_nav.hpp` | int32/uint32→int64/uint64 | M4 (order_nav slice) |
| — | `navsel::pick_recno` int32 (RawOrder + LogicalView casts) | `nav_select.hpp` | int32→int64 | M4 (self-labeled) |
| — | `scan_selector` `(int32_t)rn` casts, `apply_scope` int, physical `int total` | `scan_selector.cpp` | int→int64 | M4/M5 (SCAN/DELETE/RECALL/COUNT selector) |
| — | `cmd_seek` `gotoRec`/`recCount` int32 nav-consumer | `cmd_seek.cpp` | int32→int64 | M4-5 (self-labeled) |
| O10 | SMARTLIST `process_record` + `RecordConsumer` | `smartlist_query.{cpp,hpp}` | int32→int64 | M4/M5 |
| — | `cmd_skip` filtered path int32 | `cmd_skip.cpp` | int32→int64 | M4/M5 |
| — | `cmd_validate_unique` int recno/scan | `cmd_validate_unique.cpp` | int32→int64 | M5 |

**Already delivered this session (consumer-layer, ahead of foundation — see prep-order note):** tuple (`tuple_types.hpp`/`tuple_builder`), `db_tuple_stream`, `smartlist_query.cpp` (needs `RecordConsumer` typedef), IOrderProvider frozen (dead).

**Clean / non-goals (do not touch):** `cli::nav` (nav_move — already 64-bit), `logical_nav` (M3, done), `cmd_goto`/`cmd_recno`/`cmd_next` (64-bit), CNX/INX on-disk formats (V32 by design), the frozen IOrderProvider (dead — AIF O8), names/mangling (already resolved).

## 3. Execution order (prep-first, per owner preference)

1. **Foundation:** O11 (`cdx_backend` cursor decode) + BUILDLMDB builder loop → `xindex.lib`. *(O11 edit spec + this note delivered.)*
2. **M4 order slice (atomic):** `order_step_cdx` (O9) + `order_nav.hpp` endpoints + `navsel::pick_recno` — one coordinated drop (interface-coupled).
3. **M5 consumer sweep (mechanical):** `scan_selector`, `cmd_seek`, `cmd_skip`, `RecordConsumer` typedef + implementers, `cmd_validate_unique`, remaining `A.recno()` display sites.

## 4. Proof that closes the drift (what the sparse test didn't do)

A **populated ordered** test past 2³¹, not just sparse storage: build (or stub) a CDX/LMDB index whose entries reference recnos > 2³¹, then prove `SEEK` / ordered `TOP`/`BOTTOM`/`SKIP` / `SMARTLIST` / `SCAN` return the true 64-bit recno (not a wrapped value). Add `dottalkpp_recno64_ordered_e2e_test` alongside the existing sparse/boundary tests. Until that is green, AIF-027 should read **"storage addressing proven; index/nav addressing past 2³¹ open (this package)."**

## 5. Proposed records (drafts for the owner to accept)

**Dashboard row (append/mark on the AIF-027 line or as AIF-041):**
> `| RECNO64 nav/index consumer residual (AIF-041, under AIF-027) | review-needed 2026-07-21; audit of remaining int32 nav/index carriers (CDX cursor decode, order_step_cdx, order_nav, navsel::pick_recno, scan_selector, BUILDLMDB builder loop, SMARTLIST RecordConsumer, cmd_seek/cmd_skip). Dashboard M4-5 proved sparse *storage* addressing; ordered index addressing past 2³¹ untested. Prep-first plan + carrier audit attached. Not built | RECNO64_CARRIER_AUDIT_V1_20260721.md; STEWARD_PACKAGE_AIF-027-RESIDUAL_RECNO64_NAV_INDEX_V1 |`

**Intake row (`AI_INTERACTION_INTAKE_QUEUE_V1.md`):** AIF-041, parent AIF-027, project.x64base, status review-needed, owner Derald.

**projects.yaml:** add lane `recno64_nav_index_residual` (or milestone M5 on the existing RECNO64 lane) under `project.x64base`.

## 6. Maintenance

Update this file's per-carrier status as slices land (foundation → M4 → M5); close by folding a `SESSION_CLOSEOUT_RECNO64_NAV_INDEX_*` + AIPR id, and correct the AIF-027 dashboard "M4-5 done" wording to distinguish storage vs index addressing.
