# Foundation Drop — RECNO64 L1 (index build + cursor)

**Steward package:** AIF-027 residual (`STEWARD_PACKAGE_AIF-027-RESIDUAL_RECNO64_NAV_INDEX_V1`). **Slice:** foundation (Layer 1). **Owner:** Derald. **Steward:** Claude. **Status:** `review-needed`, source-evidenced, not built.
**Note:** `RECNO64_END_TO_END_64BIT_ADDRESSING_LANE_V1.md` is dev-only (not in the public snapshot) — this drop aligns to the AIF-027 dashboard row language instead.

---

## 1. Intent (why this first)

Make the **bottom** of the RECNO64 stack — the code that *produces* recnos — speak full 64-bit, as a self-contained buildable increment, before any consumer-layer widening. It is the exact layer AIF-027's sparse-file proof skipped (that test proved *storage* addressing past 2³¹; it never *built* or *walked* a populated index there). After this drop, "does it truncate?" collapses to the mechanical "does this consumer still narrow?" for every layer above.

## 2. Files (2 changes, 2 targets)

| Change | File · target | Kind |
|---|---|---|
| **BUILDLMDB builder loop** — index the full 64-bit range | `src/cli/cmd_buildlmdb.cpp` · CLI/`dottalkpp` | `cmd_buildlmdb.recno64.patch` (unified diff) |
| **O11 CDX cursor decode** — stop truncating recno to uint32 | `src/xindex/cdx_backend.cpp` · `xindex.lib` | `cdx_backend.recno64_cursor.EDITSPEC.md` (helper hunk + 4 identical-line edits) |

Correction to an earlier note: this touches **both** `xindex.lib` (cdx_backend) **and** the CLI target (cmd_buildlmdb is a command), not `xindex.lib` alone.

## 3. What each does

- **`cmd_buildlmdb.cpp`** — `build_tag_lmdb_from_field`: `int32_t total = recCount()` → `int64_t total = recCount64()`; `for (int32_t rn …)` → `for (int64_t rn …)` with `gotoRec64`. The value packer already emits 8-byte LE (`pack_recno_le8((uint64_t)rn)`). Without this, the index is only *populated* to 2³¹ regardless of any reader fix.
- **`cdx_backend.cpp`** — `decode_recno_from_cursor_key(…, uint32_t& out)` → `uint64_t& out` (drop both `static_cast<uint32_t>` narrowings); the four `LmdbCursor::first/next/last/prev` locals `std::uint32_t r` → `std::uint64_t r`. `RecNo = std::uint64_t`, so `IndexManager::scan()` now yields untruncated recnos to `order_collect_recnos_asc` / `order_stream_display`.

## 4. Apply

```
copy/paste per the EDITSPEC into src/xindex/cdx_backend.cpp   (helper + 4 spots)
git apply <drop>/cmd_buildlmdb.recno64.patch                 (or hand-apply the hunk)
```

## 5. Build & test

```
cmake --build build --config Release --target dottalkpp     # rebuilds xindex.lib + CLI
```

- **Expected:** build-green, warning-clean.
- **Regression (no behavior change on normal tables):** `REGRESSION RUN INDEX_X64` (v64 CDX/LMDB smoke) still passes; CURSOR x32/CNX unaffected. On a normal (<2³¹) table nothing observable changes — recnos were already ≤ 2³¹.
- **This drop does NOT prove past-2³¹ end-to-end** (see §6).

## 6. What it does and does NOT achieve (foundation honesty)

- **Does:** the index is *built* for and the cursor *returns* full 64-bit recnos. The 64-bit contract now holds at the bottom.
- **Does NOT:** make `SEEK`/`SMARTLIST`/ordered `TOP`/`BOTTOM`/`SKIP` correct past 2³¹ — those consumers (`order_step_cdx` O9, `order_nav`, `navsel::pick_recno`, `scan_selector`, SMARTLIST `RecordConsumer`) still narrow until the **M4 order slice** and **M5 consumer sweep** land. A solid foundation under an un-widened consumer still truncates *at that consumer*.
- **Closing proof (later):** `dottalkpp_recno64_ordered_e2e_test` — a populated CDX/LMDB index with entries > 2³¹, proving ordered/index reads return the true recno. Structurally impossible with the sparse fixture.

## 7. Next slices (recorded in the steward package)

1. **M4 order slice (atomic):** `order_step_cdx` (O9) + `order_nav.hpp` endpoints + `navsel::pick_recno`.
2. **M5 consumer sweep:** `scan_selector`, `cmd_seek`, `cmd_skip`, `RecordConsumer` typedef + implementers, `cmd_validate_unique`, `A.recno()` display sites.
3. **Doc correction:** amend the AIF-027 dashboard "M4-5 done" wording to distinguish *storage* addressing (proven) from *index/nav* addressing (this residual).
