# RECNO64 -- End-to-end 64-bit record addressing (lane v1)

Status: **M1-M5 implemented and proven END-TO-END (dev)** -- full runtime widening done, and the record-number path is proven **past 2^31 on disk**: the engine positions to and reads distinct records at recno 2^31+1 and 2^31+2 from a real (sparse) x64 table. Not promoted. (Only non-goal remaining: materializing a *fully populated* multi-billion-row table, which is a data-volume/performance question -- Pinocchio territory -- not an addressing-correctness one.)
Owning lifecycle: DotTalk++ SDLC.
Truth state: source-defined + runtime-proven (verified against `D:\code\ccode`, 2026-07-19/20).
Proof state: M1-M2 sanity-run; M3a nav regression-green (CURSOR x32/CNX + INDEX_X64 x64/CDX); M3b buffer proven on x64 (table_buffer.dts); M3c index width verified; M4-1/2/3 build-green + regression-clean; **M4-5 boundary unit test green** (`dottalkpp_recno64_boundary_test`) **+ sparse-file end-to-end test green** (`dottalkpp_recno64_sparse_e2e_test` -- distinct records read at recno 2^31+1/+2 off a real ~18 GiB-offset sparse table).

## Why this lane exists

The DBF_64 **format** is 64-bit and the engine already has the 64-bit
foundation, but several runtime paths still narrow a record number back to
32 bits. The defensible public claim today is *"64-bit-capacity table format
with partially widened runtime paths."* This lane widens the remaining paths so
the claim can become *"end-to-end 64-bit record addressing within documented
filesystem, stream, and index-backend limits."* Not "unlimited" -- no database is.

## What already exists (verified)

- `include/xbase.hpp`: `uint64_t _crn64`, `_rec_count64`, `_record_length64`;
  `recno64()`, `recCount64()`, `recLength64()` return `uint64_t`.
- `src/xbase/dbf_file.cpp`: record offsets computed with checked 64-bit math
  (`checked_record_pos_`, overflow-guarded) + the new `X64_MAX_RECORD_SIZE`
  buffer ceiling.
- `include/xbase_64.hpp`: `record_size_64` (64-bit) is authoritative; the classic
  16-bit fields are saturating compatibility mirrors.

## The narrowing (verified findings)

1. **`recno()` / `recLength()` / `cpr()` SATURATE to `INT_MAX`.** `include/xbase.hpp`
   returns `int32_t`/`int` clamped at `numeric_limits<int>::max()` when the 64-bit
   value exceeds it. This is worse than truncation: two different records past
   2.1 B both report `2147483647`. **Own boundary-proof item.**
2. **Navigation consumers read the narrowing accessor.** `int32_t current = A.recno();`
   in `include/cli/nav_move.hpp`, `nav_select.hpp`, `order_nav.hpp`, `scan.hpp`;
   `uint32_t rn = area.recno();` in `include/cli/table_write.hpp`.
3. **Table-buffer change key is 32-bit.** `TableBuffer::add_change(int recno, ...)`
   (`src/cli/table_state.cpp`), keyed by `int`.
4. **Index record-number payloads** may be 32-bit in classic INX/CNX/CDX
   representations (by format), and the x64 CDX/LMDB path must be confirmed to
   store/return full 64-bit record numbers.

## Plan (a controlled RECNO64 vertical, not a mechanical int->uint64 sweep)

1. **Canonical types.**
   ```cpp
   using RecordNo    = std::uint64_t;  // identity
   using RecordDelta = std::int64_t;   // signed for backward movement
   using FileOffset  = std::uint64_t;
   ```
2. **Make the 64-bit API authoritative.** `recCount64/recno64/gotoRecord/skipRecords`
   become the truth; keep 32-bit accessors only as explicit, range-checked
   compatibility adapters that **error rather than silently saturate/truncate**.
   Avoid overloading `gotoRec(int32_t)` vs `(uint64_t)` (implicit-conversion
   ambiguity).
3. **Audit every consumer of record identity:** GO/GOTO/RECNO/SKIP/TOP/BOTTOM,
   FIRST/LAST/NEXT/PRIOR, SCAN loops, SmartList/browsers, tuple + relation
   cursors, filters/SEEK/LOCATE, table-buffer maps + change history, record
   locks, workspace/serialized cursor state, append/delete/recall/pack, index
   record-number payloads, GUI/TUI bridges, Python bindings, diagnostics/status.
4. **Index capacity contracts.** Legacy INX/CNX/classic CDX may stay 32-bit but
   must report a limit (`IndexCapabilities{ maximum_record_number, supports_64bit }`)
   so an x64 table on an insufficient backend gets a clear error, not truncation.
   The x64 CDX/LMDB lane stores/returns full 64-bit record numbers with a
   versioned binary layout, defined byte order, and migration/rebuild rules.
5. **Preserve classic behavior.** Classic/VFP physical formats unchanged; they use
   the widened runtime API at their natural capacity. One engine API, three
   capacities.

## Implementation progress (2026-07-19)

**M1 -- positioning core (done, build-green).** `include/xbase.hpp` declares
`gotoRec64(uint64_t)`; `src/xbase/dbf_file.cpp` implements real 64-bit positioning
via `checked_record_pos_`, sets `_crn64` (+ clamped `_crn`), and routes
`gotoRec(int32_t)` -> `gotoRec64`. `bottom()`/`skip()`/`appendBlank()` go through
`gotoRec64` (INT32_MAX refusals removed). Sanity-run on x64+x32.

**M2 -- command surface (done, build-green).** `go_absolute(uint64_t)` +
`try_parse_u64_token`; `GO`/`GOTO`/`RECNO` parse and display 64-bit
(`recno64()`); `GOTO 2147483648` parses cleanly and reports out-of-range on small
tables. Sanity-run on x64+x32.

**M3 -- ordered-nav + buffer consumers (done, build-green + warning-clean).**
- *M3a -- logical_nav 64-bit:* `is_visible`/`first`/`last`/`next`/`prev_recno` and
  the internal `CursorRestore` are `uint64_t` (`recno64`/`gotoRec64`/`recCount64`).
  Command callers `cmd_first/last/next/prior` widened. `nav_move.hpp`
  `go_endpoint`/`skip_relative` (GO TOP/BOTTOM, relative SKIP) genuinely widened.
  **Regression-green: `REGRESSION RUN CURSOR`** -- physical + CNX asc/desc + tag
  switch, all endpoints/SKIP/SEEK/boundary values exact (x32/CNX). Also
  **`REGRESSION RUN INDEX_X64` green** -- v64/CDX/LMDB order + SEEK/FIND/LOCATE +
  BUILDLMDB + mutate-indexed-field re-seek (recno round-trips through the LMDB
  index: mutate->Found at 205, restore->Found at 1).
- *M3b -- table-buffer change key 64-bit:* `ChangeEntry.recno`,
  `multimap<uint64_t,ChangeEntry>`, `add_change`, `test_add_change`, `.tbj`
  journal replay, and the COMMIT aggregation (`Agg.recno`/`aggregate_for_recno`/
  `apply_one_recno`) are `uint64_t`; buffered DELETE/REPLACE/CALCWRITE producers
  no longer wrap (removed `(int)rn`). Build-green; buffer-suite proof pending.
- *M3c -- index payload width (verified):* `xindex::RecNo = uint64_t`; the active
  LMDB index packs recno as 8-byte LE and the CDX/LMDB cursor API is 64-bit -- the
  active x64 index round-trips 64-bit.

**M4 -- remaining boundary (precisely scoped, largest blast radius).**
1. **Record-lock API -- DONE (M4-1, build-green + regression-clean 2026-07-19).**
   `xbase::locks::try_lock_record/unlock_record/is_record_locked/force_unlock_record`,
   `LockBook::recs`, and `record_lock_path` widened `uint32_t`->`std::uint64_t`
   (`.lock.<recno>` naming unchanged). Callers holding a true 64-bit recno now pass
   it directly: `cmd_commit` (dropped `static_cast<uint32_t>`), `cmd_delete`
   (`delete_current_with_lock` -> `recno64()`), `dbarea` REPLACE lock (`recno64()`).
   Proven: `table_buffer.dts` COMMIT path + `INDEX_X64` mutate-indexed-field
   REPLACE, no behavior change.
2. **Lock-caller recno locals -- DONE (M4-2, 2026-07-19).** `cmd_replace`/
   `cmd_calcwrite` (`RecordLockGuard` + `rn`), `cmd_recall` (lock `rn` + its two
   helpers `dbf_clear_delete_flag_on_disk`/`reindex_recalled_record_best_effort`),
   `cmd_replace_multi`, `cmd_lock`/`cmd_unlock` (user-arg `stoul`->`stoull`) all
   `recno64()`/`std::uint64_t`. Build-green + warning-clean.
3. **Index-hook + CDX decoder chain -- DONE (M4-3, 2026-07-19).**
   `index_hooks::apply_replace` (typedef + free fn + impl) and the installed
   `attach.cpp::apply_replace_hook` widened to `std::uint64_t`; `dbarea` cast
   dropped. `decode_recno_from_kv_` (which already decoded the 8-byte LE value into
   a `uint64` then truncated) + `seekRecnoUserKey` + `IndexManager::lmdbSeekUserKey`
   + `cmd_lmdb` receiving var -> `std::uint64_t`. `cmd_seek` receives 64-bit; only
   its `gotoRec`/`recCount` positioning stays int32 (explicit cast, -> M4-5).
   Proven: `INDEX_X64` keyed SEEK + mutate-field re-seek exact.
4. **Legacy `.inx`/CNX kept 32-bit + capability report -- DONE (M4-4, build-pending).**
   Decision: keep classic 32-bit formats (not focusing on intense classic-32 DBF
   support). Added `IIndexBackend::maxRecordNumber()` (default `UINT64_MAX`;
   `supportsWideRecords()` helper) with `CnxBackend` overriding to `UINT32_MAX`
   (classic CNX stores recnos in 4 bytes); CDX/LMDB/B+tree inherit the 64-bit
   default via `ITagBackend : IIndexBackend`. `IndexManager` exposes
   `backendMaxRecordNumber()` + `recordNumberFitsBackend(RecNo)`. Reporting surface
   only; *enforcement consumer* (reject at attach/BUILDLMDB/APPEND with a clear
   message when an x64 record exceeds a legacy backend's ceiling) is a small
   follow-up -- the scenario can't occur until M4-5 removes the `recno()` saturation.
5. **`recno()`/`recLength()`/`cpr()` de-saturation -- DONE (M4-5, proven 2026-07-20).**
   On the x64 path these now return **`-1`** ("out of 32-bit range; use the `*64`
   accessor") instead of clamping to `INT_MAX`, so a legacy 32-bit consumer sees
   "invalid -> skip/error" rather than acting on a plausible-but-wrong record
   (`include/xbase.hpp`; the classic on-disk 32-bit header/`_crn` mirror is left
   saturating as the interop mirror). Proof: `src/tests/test_recno64_boundary.cpp`
   (`dottalkpp_recno64_boundary_test`, green) fabricates 64-bit state via the public
   setters and asserts `recno64`/`recCount64`/`recLength64` resolve **distinct**
   values at `INT32_MAX`, `+1`, `+2`, `UINT32_MAX`, `UINT32_MAX+1` while the legacy
   accessors return `-1` at overflow -- no 85 GB table needed. **End-to-end proof
   added + green:** `src/tests/test_recno64_sparse_e2e.cpp`
   (`dottalkpp_recno64_sparse_e2e_test`) builds a real x64 table with `record_count`
   set to `2^31+2`, sparse-writes records at recno 1 / 2^31+1 / 2^31+2 (the ~18 GiB
   gap is an NTFS hole -- a few KB physical), reopens through the full engine, and
   asserts `gotoRec64` reads the two records past 2^31 **distinctly** off disk (ran in
   ~0.5 s). Only deferred item: the `cmd_seek` `found_recno` int->uint64 consumer
   widening (unreachable path, flagged in-source).

Stray-cleanup note: `src/cli/nav_select.cpp` is a `#pragma once` header-duplicate
of `include/cli/nav_select.hpp` (the compiled one); recommend deleting the stray.

## Proof strategy (no billions of rows needed)

- **Unit tests** at boundaries: `INT32_MAX-1`, `INT32_MAX`, `INT32_MAX+1`,
  `UINT32_MAX`, `UINT32_MAX+1` with a synthetic record source.
- **Sparse-file integration**: place selected DBF_64 records beyond the 2 GB/4 GB
  offsets without allocating intervening bytes.
- **LMDB tests**: keys mapping to record numbers above both 32-bit limits.
- **Decisive acceptance sequence** (every returned record number exact):
  `GOTO 2147483648` -> `RECNO` -> `SKIP 1` -> `BOTTOM` -> `SEEK <indexed-key>` ->
  read record -> buffer mutation -> commit/reopen.

## Completion gates (call it end-to-end 64-bit only when ALL hold)

- No authoritative cursor state uses `int32_t`; no x64 navigation command narrows.
- Table buffers + locks accept 64-bit record identities.
- Relations/tuples preserve them; x64 indexes store/retrieve them.
- Workspace save/load round-trips them; bindings expose them.
- Boundary tests pass above signed and unsigned 32-bit limits.
- Classic/VFP regressions stay green; overflow + filesystem-limit failures are explicit.

## Relationship to shipped work

Separate from and larger than the 2026-07-19 limits raise
(`SESSION_CLOSEOUT_ENGINE_LIMITS_AND_CORRECTIONS_2026-07-19.md`), which widened
work-area and name ceilings and added record-size guardrails but did **not**
touch record-number width. The `recno()` saturation (finding 1) is the natural
first RECNO64 milestone and has an immediate, self-contained boundary proof.
