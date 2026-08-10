# M0 Findings — Lane `XIDX-TXN-02` (CNX native transactional mutations)

**Lane:** `XIDX-TXN-02`
**Gate:** M0 — Discovery / approach locked
**Date:** 2026-07-21
**Author:** Claude (hosted AI), source-read only.
**Verdict:** M0 **met** — C1–C5 settled below. One reshaping finding: **CNX correctness is already satisfied by rebuild-on-commit**, so this lane's proof is *regression-retention + crash-atomicity + performance*, **not** a red→green correctness flip (unlike `XIDX-TXN-01`).

---

## 0. Reshaping finding (read first)

`commit_one_area` → `auto_reindex_if_needed` **already calls `cmd_REBUILD` for CNX** at every COMMIT. So a buffered `REPLACE`+`COMMIT` on a CNX-ordered table **already yields a correct `SEEK` today** (the `.cnx` is fully rebuilt). Therefore:

- The lane's value is **not** correctness — it is **eliminating the full DBF re-scan** (perf) and enabling **true transactional/incremental** maintenance + **atomic persistence** instead of unconditional rebuild.
- The M2 gate is **not** "SEEK flips FAIL→PASS." It is: (i) correctness **retained** through the change (regression guard stays green), (ii) the new `save()` path is **crash-atomic** (dirty-flag fallback), (iii) `ROLLBACK` neutral, (iv) **perf**: COMMIT no longer performs a full re-scan for a bounded key delta.

This adjusts the lane's M2 exit conditions (see §7).

---

## 1. C1 — Approach (A / B / C)  → **decided: A for v1, B target, C fallback**

- **A (in-memory delta + atomic `save()`):** implement `CnxBackend::upsert/erase` to mutate the loaded in-memory `InxPayload` (insert/remove `(key,recno)` keeping sorted order) and mark dirty; at COMMIT, persist via `CnxDocument::save()` (currently a stub) with atomic temp+fsync+rename; `ROLLBACK`/abort restores the pre-image payload. Removes the O(n·log n) DBF re-scan; still O(n) file write.
- **B (reserved B-tree pages):** implement the pages the header already reserves (`root_page_off`, `page_size`, `*_HDRF_DIRTY`) for O(log n) native writes with COW root swap / page journal. Target.
- **C (status quo):** keep `cmd_REBUILD`-on-commit. Documented fallback.

**Author format-neutrally (per the twin-format finding `XIDX_NATIVE_FORMAT_FINDINGS_V1`):** write the mutable path against the shared primitives so the same code serves `.cnx` (V32) and a future `.cdx` (V64) native store — unlocking `XIDX-NATIVE-CDX-01` almost for free.

## 2. C2 — V32 capacity  → **RESOLVED (report exists; enforce at call sites)**

- `CnxBackend::maxRecordNumber()` returns `UINT32_MAX` (confirmed; class comment "record numbers in 4 bytes — 32-bit ceiling"). `IIndexBackend::maxRecordNumber()` defaults to `UINT64_MAX`; CDX/LMDB inherit the default (V64).
- `IndexManager::recordNumberFitsBackend(rec)` / `backendMaxRecordNumber()` already expose the gate. **Remaining task:** the append/insert path must **call** the gate and reject a `recno > UINT32_MAX` binding to a CNX backend with a clear error (per the `index_manager.hpp` note "reject … rather than truncate"). Enforcement, not new capability.

## 3. C3 — Atomicity of the `.cnx` swap  → **mechanism present**

- `cnxfile::` exposes `set_dirty`/`CNX_HDRF_DIRTY`, `flush_header`, `append_bytes`/`write_at`. `save()` should: write a fresh, consistent `.cnx` to a temp path, fsync, atomically rename over the original, clearing `CNX_HDRF_DIRTY` last. On open, a set `CNX_HDRF_DIRTY` (torn write) ⇒ fall back to `rebuild()`.
- **Confirm:** Windows rename-over atomicity (`ReplaceFile`/`MoveFileEx`); the dirty flag is the backstop if the platform swap is non-atomic.

## 4. C4 — COMMIT contract change  → **specified**

`auto_reindex_if_needed` CNX branch: replace unconditional `cmd_REBUILD` with:
1. if a live in-memory payload is present and the buffered key delta is bounded → apply deltas in-mem + `CnxDocument::save()` (fast path);
2. else (no payload / stale / unbounded delta / capacity reject) → fall back to full `rebuild()`.
Keep `cmd_REBUILD` reachable as the fallback and the crash-recovery path.

## 5. C5 — Immediate vs buffered parity  → **RESOLVED**

- `TABLE OFF` REPLACE fires the `index_hooks` seam → `apply_replace_snapshot` → `CnxBackend::upsert/erase`, which are **no-ops that mark `stale_`** today. So immediate CNX edits are **not** maintained either — both immediate and buffered currently rely on rebuild.
- **Decision:** implement `upsert/erase` as in-memory delta ops (Approach A) so **both** paths maintain via the same seam. Persist on COMMIT (buffered) or immediately via `save()` (TABLE OFF autocommit). This mirrors the LMDB lane's seam reuse — CNX's "bulk txn" analogue is *in-mem delta + one `save()`*.

## 6. Edit sites (anchors)

- `src/cnx/cnx_document.cpp` → implement `save()` (atomic temp+fsync+rename, RUN1 writer already exists in `cnx_backend::rebuild` — factor it out); dirty-flag lifecycle.
- `src/xindex/cnx_backend.cpp` → real `upsert/erase` (in-mem payload insert/remove + dirty); a `flush()`/persist entry the COMMIT path calls; `invalidate()`/reload for `ROLLBACK`.
- `src/cli/cmd_commit.cpp` → `auto_reindex_if_needed` CNX branch per C4; optional CNX begin/abort/commit analogue to the LMDB bulk wrap (snapshot payload for rollback).
- `include/cnx/cnx_backend.hpp` / `cnx_document.hpp` → declarations.
- Capacity: wherever appends bind a recno to the backend → gate on `recordNumberFitsBackend`.

## 7. Revised M2 exit conditions (supersede lane §6 M2)

1. **Correctness retained:** CNX buffered `REPLACE`/`DELETE` + `COMMIT` → `SEEK` correct (stays green; today via rebuild, after via delta+save).
2. **Crash-atomicity:** kill mid-`save()` → reopen sees `CNX_HDRF_DIRTY` → rebuild fallback → `SEEK` correct.
3. **ROLLBACK neutral:** buffered CNX edits + `ROLLBACK` → `.cnx` unchanged; `SEEK` old key still hits.
4. **No full re-scan (perf):** COMMIT of a bounded key delta does not re-scan all rows — measured artifact (`cnx_txn_bench_v1.md`), since a `.dts` cannot assert timing.
5. **Capacity:** binding a `> UINT32_MAX` recno to CNX errors clearly (no truncation).

## 8. Gate status

C1 ✔ (A) · C2 ✔ · C3 ✔ · C4 ✔ · C5 ✔ · edit sites ✔ · M2 reshaped. **M0 met → M1-ready.**
Next: M1 patch (implement `save()` + in-mem `upsert/erase` + C4 COMMIT branch), and a CNX regression **guard** script mirroring `index_x32_inx_cnx_smoke.dts` (asserts correctness is retained; the perf claim rides the M3 bench).
