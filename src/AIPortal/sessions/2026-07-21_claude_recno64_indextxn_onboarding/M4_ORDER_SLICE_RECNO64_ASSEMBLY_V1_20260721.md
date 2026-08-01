# M4 Order Slice — RECNO64 (assembly)

**Steward package:** AIF-027 residual · **Slice:** M4 (order layer) · **Owner:** Derald · **Steward:** Claude · **Status:** `review-needed`, source-evidenced, **not built**.
**Atomic unit — 4 files, one compile:** widening `order_step_cdx` and `order_first/last_recno` signatures forces their callers; apply all four together or the build breaks. Precise before→after (not a fragile full-file retype of the 600-line header).

**Prereq:** the L1 Foundation Drop (O11 cursor + BUILDLMDB loop) should land first — this slice returns 64-bit recnos *from* that cursor.

---

## File 1 — `include/cli/order_iterator.hpp` (1 line)

```diff
-OrderStep order_step_cdx(xbase::DbArea& area, int index_delta, int32_t& out_recno);
+OrderStep order_step_cdx(xbase::DbArea& area, int index_delta, std::int64_t& out_recno);
```

## File 2 — `src/cli/order_iterator.cpp` · `order_step_cdx` (5 edits)

```diff
-OrderStep order_step_cdx(xbase::DbArea& area, int index_delta, int32_t& out_recno)
+OrderStep order_step_cdx(xbase::DbArea& area, int index_delta, std::int64_t& out_recno)
 {
     out_recno = 0;
@@
-    const int32_t cur = area.recno();
-    if (cur < 1 || cur > area.recCount()) return OrderStep::Unavailable;
+    const std::int64_t cur = static_cast<std::int64_t>(area.recno64());
+    if (cur < 1 || cur > static_cast<std::int64_t>(area.recCount64())) return OrderStep::Unavailable;
@@
     if (cdx->stepOrdered(baseKey, static_cast<xindex::RecNo>(cur), forward, steps, landed, located)) {
-        if (landed >= 1 && static_cast<int32_t>(landed) <= area.recCount()) {
-            out_recno = static_cast<int32_t>(landed);
+        if (landed >= 1 && static_cast<std::int64_t>(landed) <= static_cast<std::int64_t>(area.recCount64())) {
+            out_recno = static_cast<std::int64_t>(landed);
             return OrderStep::Moved;
         }
         return OrderStep::Unavailable;
     }
```
(`stepOrdered` already takes/returns `xindex::RecNo = uint64` — `cur` promotes cleanly.)

## File 3 — `include/cli/order_nav.hpp` (primary paths; fallback cache = M5)

### `order_first_recno` — signature + CDX/CNX bodies
```diff
-static inline bool order_first_recno(xbase::DbArea& area, int32_t& out_recno) {
+static inline bool order_first_recno(xbase::DbArea& area, std::int64_t& out_recno) {
     out_recno = 0;
     ...
     case xindex::fmt::IndexFormat::CDX: {
         ...
-        int32_t rn = 0;
+        std::int64_t rn = 0;
         cli::order_stream_display(area, /*reverse=*/false,
             [&](std::uint64_t recno) -> bool {
-                rn = static_cast<int32_t>(recno);
+                rn = static_cast<std::int64_t>(recno);
                 return false;
             });
-        if (rn >= 1 && rn <= area.recCount()) { out_recno = rn; return true; }
+        if (rn >= 1 && rn <= static_cast<std::int64_t>(area.recCount64())) { out_recno = rn; return true; }
         ...
-        out_recno = asc ? static_cast<int32_t>(cache.recnos.front())
-                        : static_cast<int32_t>(cache.recnos.back());
+        out_recno = asc ? static_cast<std::int64_t>(cache.recnos.front())
+                        : static_cast<std::int64_t>(cache.recnos.back());
         return (out_recno != 0);
     }
     case xindex::fmt::IndexFormat::CNX: {
         ...
-        out_recno = asc ? static_cast<int32_t>(cache.recnos.front())
-                        : static_cast<int32_t>(cache.recnos.back());
+        out_recno = asc ? static_cast<std::int64_t>(cache.recnos.front())
+                        : static_cast<std::int64_t>(cache.recnos.back());
         return (out_recno != 0);
     }
     case xindex::fmt::IndexFormat::INX: {
         ...  // first/last are int32 (V32 INX); assigning to int64 out_recno promotes — no edit needed
         out_recno = asc ? first : last;
         return (out_recno != 0);
     }
```

### `order_last_recno` — identical shape to `order_first_recno`
Signature `int32_t&`→`std::int64_t&`; the CDX `int32_t rn` + `static_cast<int32_t>(recno)` + `recCount()`; the CNX `static_cast<int32_t>(cache…)` → `std::int64_t`; INX unchanged (promotes).

### `order_top` / `order_bottom`
```diff
 static inline bool order_top(xbase::DbArea& area) {
-    int32_t rn{};
-    if (order_first_recno(area, rn) && rn >= 1 && rn <= area.recCount()) {
-        if (!area.gotoRec(rn)) return false;
+    std::int64_t rn{};
+    if (order_first_recno(area, rn) && rn >= 1 && rn <= static_cast<std::int64_t>(area.recCount64())) {
+        if (!area.gotoRec64(static_cast<std::uint64_t>(rn))) return false;
         return area.readCurrent();
     }
     ...
 }
```
`order_bottom` is identical with `order_last_recno`.

### `order_skip` — CDX **primary** fast path only
```diff
     case xindex::fmt::IndexFormat::CDX: {
         ...
         {
-            int32_t rn = 0;
+            std::int64_t rn = 0;
             const cli::OrderStep st = cli::order_step_cdx(area, delta_eff, rn);
             if (st == cli::OrderStep::Moved) {
-                if (rn < 1 || rn > area.recCount()) return false;
-                if (!area.gotoRec(rn)) return false;
+                if (rn < 1 || rn > static_cast<std::int64_t>(area.recCount64())) return false;
+                if (!area.gotoRec64(static_cast<std::uint64_t>(rn))) return false;
                 return area.readCurrent();
             }
             if (st == cli::OrderStep::Boundary) return false;
         }
         // --- fallback position-map cache below: LEFT int32 (M5, O2). See note. ---
```
**M5 boundary (do NOT widen in this slice):** the `order_skip` fallback cache block (`const int32_t cur = area.recno();` … `cache.pos.find((uint32_t)cur)` … `const int32_t rn = (int32_t)cache.recnos[next]` … `gotoRec(rn)`), plus `build_cdx_recnos_from_lmdb`/`cdx_endpoint_from_lmdb`/`cdx_cache_build`/`CnxCache.recnos` (all uint32). These are the *fallback* to the O(log n) `order_step_cdx` fast path (which IS fixed here); widening them (O2) belongs to the M5 sweep with `scan_selector`. Add a one-line `// TODO(RECNO64 M5): fallback cache still 32-bit` at that block.

## File 4 — `include/cli/nav_select.hpp` · `navsel::pick_recno` (RawOrder internals)

Widen the internal locals so they bind to the now-`int64` `order_first/last_recno` out-params; **keep the `int32_t` public signature** (widening it cascades to `cmd_skip`/`cmd_scan` — that's M5). Cast at return, matching the existing LogicalView pattern.

```diff
     case Mode::RawOrder:
         {
-            int32_t rn = 0;
+            std::int64_t rn = 0;
             switch (step) {
             case Step::First:
-                if (order_first_recno(A, rn)) return rn;
-                return (A.recCount() > 0 ? 1 : 0);
+                if (order_first_recno(A, rn)) return static_cast<int32_t>(rn);
+                return (A.recCount64() > 0 ? 1 : 0);
             case Step::Last:
-                if (order_last_recno(A, rn)) return rn;
-                return (A.recCount() > 0 ? A.recCount() : 0);
+                if (order_last_recno(A, rn)) return static_cast<int32_t>(rn);
+                return (A.recCount64() > 0 ? static_cast<int32_t>(A.recCount64()) : 0);
             case Step::Next:
             {
-                const int32_t save = A.recno();
-                const int32_t start = (from_recno > 0 ? from_recno : save);
+                const std::int64_t save = static_cast<std::int64_t>(A.recno64());
+                const std::int64_t start = (from_recno > 0 ? static_cast<std::int64_t>(from_recno) : save);
                 if (start <= 0) return 0;
-                if (start != save) { if (!A.gotoRec(start) || !A.readCurrent()) return 0; }
+                if (start != save) { if (!A.gotoRec64(static_cast<std::uint64_t>(start)) || !A.readCurrent()) return 0; }
                 const bool ok = order_skip(A, +1);
-                rn = ok ? A.recno() : 0;
-                if (save > 0) { (void)A.gotoRec(save); (void)A.readCurrent(); }
-                return rn;
+                rn = ok ? static_cast<std::int64_t>(A.recno64()) : 0;
+                if (save > 0) { (void)A.gotoRec64(static_cast<std::uint64_t>(save)); (void)A.readCurrent(); }
+                return static_cast<int32_t>(rn);
             }
             case Step::Prior:  // identical to Next with order_skip(A, -1)
             ...
```
Update the existing `NOTE(RECNO64 M3)` comment: RawOrder now carries 64-bit internally; the residual narrow is only `pick_recno`'s `int32_t` return/param (M5, cascades to `cmd_skip`).

---

## Build & test
```
cmake --build build --config Release --target dottalkpp    # order_iterator + CLI recompile
```
- **Expected:** build-green, warning-clean (returns cast explicitly).
- **Regression:** `REGRESSION RUN INDEX_X64` (CDX ordered TOP/BOTTOM/SEEK/SKIP) + `INDEX_X32` (CNX) still pass — no behavior change on <2³¹ tables.
- **What M4 now makes correct past 2³¹:** unfiltered ordered `SKIP` positioning (`order_step_cdx`→`order_skip`→`gotoRec64`) and `order_top/bottom` endpoints. **Still M5:** filtered `SKIP` (via `pick_recno` int32 return), `scan_selector`, `cmd_seek`, display `recno()` lines, the `order_skip` fallback cache.

## Steward record
Update `STEWARD_PACKAGE_AIF-027-RESIDUAL…` and `RECNO64_CARRIER_AUDIT`: mark `order_step_cdx`/`order_first-last_recno`/`order_top/bottom`/`order_skip primary`/`pick_recno internals` **fixed (M4)**; keep fallback cache + `pick_recno` signature + `scan_selector` + `cmd_seek/skip` + `RecordConsumer` **pending (M5)**.
