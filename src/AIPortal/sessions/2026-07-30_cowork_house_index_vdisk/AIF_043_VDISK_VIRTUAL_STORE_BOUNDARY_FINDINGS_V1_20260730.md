# AIF-043 -- VDISK / Virtual Store: Routing Boundary Findings

**Lane:** AIF-043 (In-Memory Tables & Indexing)
**Date:** 2026-07-30
**Author:** Claude (hosted AI), **source-read only -- no build, no runtime**
**Evidence tier:** `source-evidenced`. Every claim carries a file:line anchor (section 7) and was re-verified by a second independent source pass. No runtime proof.
**Status:** `review-needed`
**Relationship to existing docs:** complements `AIF_043_RAM_DBF_POSITIONING_AND_LIMITATIONS_V1_20260722.md`. That document is an honest positioning note and its limitation table is accurate. This one covers a different axis: **which I/O layers are actually ramfs-routed and which silently are not.** Nothing here contradicts the positioning note; five of the six findings are simply not in it.

---

## 0. What is already on the record (not repeated here)

The positioning note already states, correctly: single-process/single-thread, no MVCC, registry not locked, ephemeral with no in-RAM WAL, LMDB out of scope, row-oriented, no buffer pool, X64 only. Verified -- all still true. This document does not re-litigate any of it.

**The gap it leaves:** it describes the *design* boundary ("LMDB is out of scope," "no in-RAM WAL") without stating whether the boundary is **enforced**. In five places it is not -- the unsupported path is reachable, unguarded, and writes real files under a root the operator believes is RAM.

---

## 1. Architecture, briefly

`xbase::ramfs` is a process-global registry mapping normalized absolute paths -> growable byte buffers, plus a `std::iostream` over a custom `ramfilebuf`. A path is virtual iff it sits under a mounted root. Roughly 270 lines.

`VDISK MOUNT` sets three path slots -- `DBF`, `INDEXES`, `LMDB` -- under the RAM root (default `<DATA>/ram`), then mounts that root. `DO mem` is the one-line script wrapper. The whole thing sits **beneath the engine's `io()` byte seam**, which is why the entire xBase command surface works unchanged. That design instinct is sound and is the reason the capability-to-line-count ratio is as good as it is.

The consequence, though, is that transparency is only as complete as the set of call sites that consult `is_virtual()`. Any layer that opens a file by other means bypasses the VFS entirely and writes to disk -- silently, because the path *looks* like it is under the RAM root.

---

## 2. The routing boundary (verified)

| Layer | ramfs-routed? | Anchor |
|---|---|---|
| DBF read / open | **yes** | `src/xbase/dbf_file.cpp:119-129` |
| DBF create (X64 only; other flavors rejected) | **yes** | `src/xbase/dbf_create.cpp:565, 677` |
| CNX container | **yes** | `src/cnx/cnx_file.cpp:215-220` |
| Native CDX container | **yes** | `src/cdx/cdx_file.cpp:73-76` |
| Index backend selection | **yes** | `src/xindex/index_manager.cpp:114-125` |
| Record locks (no-op on virtual) | **yes** | `src/xbase/xbase_locks.cpp:171, 203, 227` |
| Existence probes (SET ORDER / CDX / REINDEX) | **yes** | `cmd_setorder.cpp:128,487`; `cmd_cdx.cpp:115`; `cmd_reindex.cpp:509` |
| **Memo (`.dtx`)** | **no** | section R1 |
| **Legacy `.inx` / 2INX index** | **no** | section R4 |
| **LMDB (`BUILDLMDB`)** | **no** | section R5 |
| **Write-ahead journal (`.tbj`)** | **no** (conditional) | section R6 |

---

## 3. Findings

### R1 -- Memo escapes to disk (RAM tables are not actually file-free once a memo field is used)

`src/memo/` and `include/memo/` contain **zero** ramfs references. The store actually wired for X64 tables is `dottalk::memo::MemoStore` -- the `.dtx` sidecar -- using raw `std::fstream` plus `fs::create_directories`.

So an in-RAM X64 table carrying a memo field writes a real `<ramroot>/<table>.dtx` to disk, and creates the directory to hold it. The positioning note lists `M` among supported data types; that is true functionally, but not in the RAM-residency sense the lane advertises. `VDISK STATUS` will not show it, and the `mem_proof.dts` "zero files on disk" property does not hold for a memo-bearing table.

*Incidental:* `X64MemoStore` (`.lob`/`.meta` per object) is **dead code** -- its factory `make_x64_memo_store` has no caller in `src/` or `include/`.

### R2 -- `VDISK UNMOUNT` with an open area is the sharpest hazard in the subsystem

`ramfs::clear()` drops both the file map **and the root list**, and `VDISK UNMOUNT|OFF|CLEAR` calls it unconditionally with no consultation of open `DbArea`s.

What follows is worse than a crash, because nothing crashes:

1. The open area holds a `unique_ptr<iostream>` whose buffer holds a **`shared_ptr<RamFile>`**. The buffer survives `clear()`. `isOpen()` stays true. Reads and writes keep succeeding -- against a now-orphaned, unreachable buffer that `VDISK STATUS` cannot see and nothing can recover.
2. Because the roots are gone, `is_virtual()` now returns **false** for that same path. Every downstream virtual-aware decision silently flips to the disk branch: `xbase::locks` stops no-op'ing and begins creating real `.lock` files; `IndexManager::openCdx` stops selecting `CdxNativeBackend` and starts demanding a real LMDB env; `cdx_file` opens a disk `fstream`.

So one command splits a live area into a phantom data buffer and a disk-seeking metadata path. This is the finding I would act on first -- the cheapest fix is to refuse `UNMOUNT` while any area is open on a virtual path, or to force-close such areas, rather than to make orphaning safe.

### R3 -- The Layer-2 budget is reporting-only; `on_full` is not implemented

`VDISK_RAM_SIZING_AND_ADMIN_CONFIG_V1` describes a soft budget: warn at `warn_pct`, then apply `on_full = warn | spill | fail` at 100%.

In source, the only comparison -- `if (pct >= cfg.warn_pct)` -- lives **inside the `VDISK STATUS` handler**. `OnFull::Spill` and `OnFull::Fail` are never branched on anywhere; `on_full_name()` is a string mapper. No write path (`ramfs::open`, the streambuf grow path, `dbf_create`, `cdx_file`) consults `used_bytes()` or any budget.

Net: a runaway RAM table can exhaust host memory with no warning at all unless a human happens to type `VDISK STATUS`. The config surface is complete and the enforcement is absent -- which is the more dangerous shape, because `VDISK CONFIG` prints `on_full = fail` and implies a guarantee that does not exist.

### R4 -- The legacy `.inx` index path is unrouted

`InxPayload::readFromFile` / `writeToFile` use raw `ifstream`/`ofstream`; the writers in `cmd_index.cpp` and the `.inx` branch of `cmd_reindex.cpp` use `std::ofstream`; `cmd_setindex.cpp` has no virtual check. `cmd_reindex.cpp` *does* include ramfs, but the guard applies only to the `.cdx` lane.

Native CDX-V64 being the M1 in-RAM index is a deliberate, documented decision. The gap is that the non-M1 path is reachable rather than rejected: `INDEX ON` / `SET INDEX` with `.inx` under a mounted vdisk quietly produces real disk files inside the RAM root.

### R5 -- `MOUNT` points the LMDB slot into the RAM root, and `BUILDLMDB` is unguarded

`VDISK MOUNT` sets `Slot::LMDB = <ram>/lmdb` -- a path that is by construction virtual. `cmd_buildlmdb.cpp` contains no ramfs reference; it resolves the env dir, calls `fs::create_directories`, and `mdb_env_open`s it. `resolve_lmdb_env_for_cdx` is pure path arithmetic with no virtual guard.

So direct `BUILDLMDB` under a mounted vdisk creates real OS directories **inside the RAM root** and mmaps a real file there -- precisely the thing the design says is out of scope. `REINDEX ... CDX` guards correctly and routes to `CdxNativeBackend`; the direct command does not.

"Out of scope" and "guarded" are different states. This one should be a clear refusal message, and it is a small change.

### R6 -- The write-ahead journal is unrouted (conditional, lower severity)

`table_state.cpp` uses `std::fopen` on `<dbf-path>.tbj` and `fsync`s it, with no ramfs awareness. Severity is limited because the default `BufferPersistenceMode` is `RamOnly` and every journal entry point short-circuits on `is_persistent_enabled()` -- journaling is opt-in via `TABLE BUFFER PERSISTENT`.

But when a user enables it on a RAM table, the WAL is a real disk file, fsynced, next to a table that has no disk existence -- inverting the intended durability story (the volatile thing is durable; the durable thing is volatile). Two smaller notes: the path is correctly absolute (derived from `DbArea::filename()`), *except* a narrow lazy-open fallback that yields a cwd-relative `area<N>.tbj`; and `set_persistence_mode` is commented "Stub only."

---

## 4. Strategic observation: vdisk is the ideal proving ground for `XIDX-TXN-02`

This connects the two investigations, and I think it is the most useful thing in this document.

`CdxNativeBackend` is *both* the backend selected for virtual `.cdx` **and** one of the two backends carrying the stubbed `upsert`/`erase` identified in the CNX lane. So today, mutating data in a RAM table marks the in-RAM index stale and requires a full rebuild -- the same defect, in the environment where it costs least to fix.

In RAM, the hardest parts of `XIDX-TXN-02` simply do not exist:

| `XIDX-TXN-02` concern | On disk | In RAM |
|---|---|---|
| `CnxDocument::save()` / `InxPayload::writeToStream` stubs | blocking | **irrelevant** -- container never persisted |
| Atomic temp+fsync+rename | must design | **irrelevant** |
| Windows rename-over atomicity | open question | **irrelevant** |
| `CNX_HDRF_DIRTY` torn-write recovery | must wire | **irrelevant** -- no torn writes |
| Payload mutation API (N1) | required | **required** |
| Recno-precise `erase` (N3) | required | **required** |
| Multi-tag capture (N4) | required | **required** |

Everything that remains is pure in-memory logic -- exactly the part that is hard to get *right* rather than hard to make *durable*. And a RAM regression is fixture-free, fast, and deterministic, which is the profile the existing `mem_proof.dts` already demonstrates.

**Suggested consequence for sequencing:** split `XIDX-TXN-02` M1b again. Prove incremental key maintenance **in RAM first** (`CdxNativeBackend`, no persistence), then port to disk with the durability machinery. That inverts the current lane order, which starts with `save()` -- the part that RAM does not need and that carries all the platform risk.

---

## 5. Suggested next steps, in priority order

1. **R2** -- refuse `VDISK UNMOUNT` while an area is open on a virtual path (or force-close). Smallest change, worst failure mode averted.
2. **R5** -- guard `BUILDLMDB` on `is_virtual()` with a clear refusal. Small, and it makes a documented non-goal actually unreachable.
3. **R1** -- decide the memo story: route `MemoStore` through ramfs, or reject memo fields on virtual tables with a clear message. Either is defensible; silence is not. Also consider deleting the dead `X64MemoStore`.
4. **R3** -- either implement `on_full` enforcement at the ramfs write path, or downgrade the config surface so it stops advertising a policy that does not run.
5. **R4 / R6** -- lower severity; at minimum a warning when an unrouted writer targets a virtual path.

A generic backstop worth considering ahead of any of these: a single guard helper that any non-routed writer can call -- *"this path is virtual and this layer cannot serve it"* -- so the next unrouted writer fails loudly instead of leaking to disk.

---

## 6. Pattern worth naming (for the validator tier)

Across both this investigation and the `XIDX-TXN-02` one, the same shape recurs: **capability declared at the interface, absent at the leaf.**

`wasStale()` (no consumers) - `CNX_HDRF_DIRTY` (never tested) - `on_full = spill|fail` (never branched) - `CnxDocument::save()` (stub) - `InxPayload::writeToStream` (stub) - `set_persistence_mode` ("Stub only") - `make_x64_memo_store` (no callers).

Each is individually reasonable -- a placeholder for planned work. Collectively they are a class of defect your evidence taxonomy is well positioned to catch but does not currently target: the declaration is `source-evidenced` (the symbol genuinely exists) while the behavior is only `planned`. A validator that flags **declared-but-unreferenced capability** -- public API with no caller, enum values with no branch, config keys with no read at the enforcement site -- would catch all seven mechanically. That seems like a higher-yield validator than another documentation-shape check, and it fits "Runtime proves. Validators enforce." precisely.

---

## 7. Evidence index

| Claim | Anchor |
|---|---|
| ramfs model / registry / streams | `include/xbase/ramfs.hpp`; `src/xbase/ramfs.cpp:69-78, 179-269` |
| No mutex (documented intentional) | `src/xbase/ramfs.cpp` (no `<mutex>`); `include/xbase/ramfs.hpp:31-32` |
| MOUNT sets DBF/INDEXES/LMDB slots | `src/cli/cmd_vdisk.cpp:138-145` |
| Six VDISK verbs; no snapshot/persist | `src/cli/cmd_vdisk.cpp:129, 160, 166, 185, 209, 240` |
| DBF read routed | `src/xbase/dbf_file.cpp:119-129` |
| DBF create routed; X64-only gate | `src/xbase/dbf_create.cpp:565, 677` |
| CNX / native CDX routed | `src/cnx/cnx_file.cpp:215-220`; `src/cdx/cdx_file.cpp:73-76` |
| Virtual `.cdx` -> `CdxNativeBackend` | `src/xindex/index_manager.cpp:114-125` |
| R1 memo unrouted; `.dtx` store is the live one | `src/memo/memo_auto.cpp:28-50, 86`; `src/memo/memostore.cpp:474, 499-519`; `include/memo/memostore.hpp:129` |
| R1 `X64MemoStore` dead | `src/memo/x64_memo_store.cpp:195` (no callers) |
| R2 `clear()` drops files **and** roots | `src/xbase/ramfs.cpp:236-240` |
| R2 UNMOUNT unconditional | `src/cli/cmd_vdisk.cpp:160-164` |
| R2 area holds surviving `shared_ptr` | `include/xbase.hpp:401`; `src/xbase/dbf_file.cpp:129`; `src/xbase/ramfs.cpp:83, 158, 268` |
| R2 downstream flip after roots drop | `src/xbase/xbase_locks.cpp:171, 203, 227`; `src/xindex/index_manager.cpp:114 vs 212-219`; `src/cdx/cdx_file.cpp:73` |
| R3 budget compared only in STATUS | `src/cli/cmd_vdisk.cpp:223, 226` |
| R3 `Spill`/`Fail` never branched | `include/cli/vdisk_config.hpp:30`; `src/cli/vdisk_config.cpp:89-95` |
| R4 `.inx` writers unrouted | `src/xindex/inx_payload.cpp:274, 284`; `src/cli/cmd_index.cpp:241, 264`; `src/cli/cmd_reindex.cpp:384` |
| R4 `.cdx`-only guard in REINDEX | `src/cli/cmd_reindex.cpp:509-535` |
| R5 LMDB slot virtual; BUILDLMDB unguarded | `src/cli/cmd_vdisk.cpp:141-144`; `src/cli/cmd_buildlmdb.cpp:236-245, 591, 635`; `src/common/path_resolver.cpp:168-187` |
| R6 journal raw `fopen` + fsync | `src/cli/table_state.cpp:288-292, 358`; `include/cli/table_state.hpp:88` |
| R6 default RamOnly (opt-in) | `include/cli/table_state.hpp:80, 85`; `src/cli/table_state.cpp:235, 239-241` |
| R6 cwd-relative fallback; stub note | `src/cli/table_state.cpp:276-289, 249-251` |
| section 4 `CdxNativeBackend` stubs | `src/xindex/cdx_native_backend.cpp:507-519` |
| Locks no-op on virtual | `src/xbase/xbase_locks.cpp:171, 203, 227` |
| `DO mem` / proof script | `dottalkpp/data/scripts/mem.dts`; `mem_proof.dts` |

---

## 8. Delivery note

Per the Outside-AI Delivery Rule this is a `review-needed` draft. No source was modified. Suggested home: `src/AIPortal/sessions/2026-07-30_.../`, filed against AIF-043, cross-referenced from `XIDX-TXN-02` for the section 4 sequencing point.
