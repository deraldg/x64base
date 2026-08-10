# EDIT SPEC — O11: widen `CdxBackend` cursor recno decode to 64-bit

**File:** `src/xindex/cdx_backend.cpp` (inside `#if XINDEX_HAVE_LMDB`) · **Lib:** `xindex.lib`
**Why:** root CDX recno truncation — the cursor decodes 8-byte recno into `uint32`. `RecNo = std::uint64_t`. See `OBSERVATIONS_STEWARDSHIP` O11.
**Risk:** low, localized. No public signature change (the helper is file-static; `LmdbCursor::first/next/last/prev` keep their signatures). Rebuilds `xindex.lib`.

Delivered as an edit spec rather than a unified diff because the four `std::uint32_t r = 0;` lines are byte-identical across the four cursor methods (a positional patch is fragile); apply the one-line change inside each method.

---

## Change 1 — the decode helper (one hunk)

```diff
-static inline bool decode_recno_from_cursor_key(bool composite, const MDB_val& k, const MDB_val& v, std::uint32_t& out) {
+static inline bool decode_recno_from_cursor_key(bool composite, const MDB_val& k, const MDB_val& v, std::uint64_t& out) {
     std::uint64_t rec64 = 0;
     if (decode_u64_le_local(v.mv_data, v.mv_size, rec64)) {
-        out = static_cast<std::uint32_t>(rec64);
+        out = rec64;
         return true;
     }
     if (composite && k.mv_size >= 8 &&
         decode_u64_le_local(static_cast<const unsigned char*>(k.mv_data) + (k.mv_size - 8), 8, rec64)) {
-        out = static_cast<std::uint32_t>(rec64);
+        out = rec64;
         return true;
     }
     return false;
 }
```

## Change 2 — the four cursor methods (identical one-line edit in each)

In **`CdxBackend::LmdbCursor::first`**, **`::next`**, **`::last`**, and **`::prev`**, change the recno local:

```diff
-    std::uint32_t r = 0;
+    std::uint64_t r = 0;                 // O11: RecNo is uint64; do not truncate
     if (!decode_recno_from_cursor_key(composite_, k, v, r)) return false;
```

The existing `outRec = static_cast<RecNo>(r);` now widens `uint64 → RecNo(uint64)` (a no-op cast — leave it or drop the cast).

---

## Effect

After this, `IndexManager::scan()` → `CdxBackend::LmdbCursor` yields full 64-bit recnos, so `order_collect_recnos_asc` / `order_stream_display` (and everything above them: SMARTLIST, SCAN, `order_nav`, `db_tuple_stream`) get untruncated CDX recnos. This is the single most important RECNO64 fix and pairs with Phase A/B (tuple + raw-scan) already delivered.

## Not covered here (separate items)
- **O9** `order_step_cdx(int32_t& out)` → int64 — must ship **with** its `order_nav.hpp::order_skip` caller (interface-coupled).
- **order_nav.hpp endpoints** (`order_first/last_recno` int32, `order_top/bottom` `gotoRec`/`recCount`) → int64/`gotoRec64`/`recCount64`.
- **O10** `smartlist_query.cpp` — delivered as a full file this drop.
- The order_nav *fallback* scanners (`build_cdx_recnos_from_lmdb`/`cdx_endpoint_from_lmdb`, O2) also narrow to uint32 — but they're the fallback; O11 fixes the primary cursor path they back up.
