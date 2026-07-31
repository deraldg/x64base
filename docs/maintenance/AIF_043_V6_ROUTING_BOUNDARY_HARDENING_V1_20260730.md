# AIF-043 -- Milestone V6: VDISK Routing Boundary Hardening

**Lane:** `AIF-043` (In-Memory Tables & Indexing). **This is a new milestone in an existing lane, not a new lane.**
**Milestone:** `V6` (follows V1-V5 in `VFS_INMEMORY_MILESTONE_PLAN_V1_20260721.md`, all of which are complete)
**Status:** `planned` *(not earned: no source landed, no runtime evidence)*
**Owner:** Derald - drafting partner: Claude (Cowork, local repo access)
**Run:** `DECLARED-CAPABILITY-VALIDATOR-20260730`
**Baseline:** `b702b5a5d1cc629c48411af9e93ff879b198e73f` on `development`
**Created:** 2026-07-30
**Findings source:** `src/AIPortal/sessions/2026-07-30_cowork_house_index_vdisk/AIF_043_VDISK_VIRTUAL_STORE_BOUNDARY_FINDINGS_V1_20260730.md`

> Findings are labelled **R1-R6** here (Routing). The lane's own milestones already use V1-V5, so the findings deliberately do not reuse a `V` prefix.

---

## 1. One-line

V1-V5 made tables and the native index live in RAM. V6 makes the **boundary honest**: every I/O layer either routes through `xbase::ramfs` or refuses a virtual path with a clear message. No layer silently writes real files under a root the operator believes is RAM.

## 2. Why this is V6 and not a defect ticket

`AIF_043_RAM_DBF_POSITIONING_AND_LIMITATIONS_V1_20260722.md` is accurate on every limitation it claims. What it does not say is whether those limitations are **enforced**. In five places they are not: the unsupported path is reachable, unguarded, and produces real files inside the RAM root.

That is a lane-scope gap, not a bug list. The lane's headline property is transparency below the `io()` byte seam, and transparency is only as complete as the set of call sites that consult `is_virtual()`. Closing that set is milestone work.

## 3. Verified routing boundary at baseline

| Layer | Routed | Anchor |
|---|---|---|
| DBF read / open | yes | `src/xbase/dbf_file.cpp:119-129` |
| DBF create (X64 only) | yes | `src/xbase/dbf_create.cpp:565, 677` |
| CNX container | yes | `src/cnx/cnx_file.cpp:215-220` |
| Native CDX container | yes | `src/cdx/cdx_file.cpp:73-76` |
| Index backend selection | yes | `src/xindex/index_manager.cpp:114-125` |
| Record locks (no-op on virtual) | yes | `src/xbase/xbase_locks.cpp:171, 203, 227` |
| Existence probes | yes | `cmd_setorder.cpp:128,487`; `cmd_cdx.cpp:115`; `cmd_reindex.cpp:509` |
| Memo (`.dtx`) | **no** | R1 |
| Legacy `.inx` / 2INX | **no** | R4 |
| LMDB (`BUILDLMDB`) | **no** | R5 |
| Write-ahead journal (`.tbj`) | **no** (opt-in only) | R6 |

## 4. Findings, in priority order

### R2 -- `VDISK UNMOUNT` with an open area (highest severity)

`ramfs::clear()` drops the file map **and the root list**; `VDISK UNMOUNT|OFF|CLEAR` calls it unconditionally with no check for open areas. Nothing crashes, which is the problem:

1. The open area holds a `unique_ptr<iostream>` whose buffer holds a `shared_ptr<RamFile>`. The buffer survives. `isOpen()` stays true. Reads and writes keep succeeding against an orphaned, unreachable buffer that `VDISK STATUS` cannot see.
2. The roots are gone, so `is_virtual()` now returns **false** for the same path. Every downstream virtual-aware decision flips to the disk branch: `xbase::locks` stops no-op'ing and begins creating real `.lock` files; `IndexManager::openCdx` stops selecting `CdxNativeBackend` and demands a real LMDB env; `cdx_file` opens a disk `fstream`.

One command splits a live area into a phantom data buffer and a disk-seeking metadata path.
**Anchors:** `src/cli/cmd_vdisk.cpp:160-164`; `src/xbase/ramfs.cpp:236-240, 83, 158, 268`; `include/xbase.hpp:401`; `src/xbase/dbf_file.cpp:129`; `src/xbase/xbase_locks.cpp:171, 203, 227`; `src/xindex/index_manager.cpp:114 vs 212-219`.

### R5 -- LMDB slot points into the RAM root, and `BUILDLMDB` is unguarded

`VDISK MOUNT` sets `Slot::LMDB = <ram>/lmdb`, which is by construction virtual. `cmd_buildlmdb.cpp` has no ramfs reference: it resolves the env dir, calls `fs::create_directories`, and `mdb_env_open`s it, creating real OS directories **inside the RAM root** and mmapping a real file there. `resolve_lmdb_env_for_cdx` is pure path arithmetic with no guard. `REINDEX ... CDX` guards correctly; the direct command does not.

"Out of scope" and "guarded" are different states.
**Anchors:** `src/cli/cmd_vdisk.cpp:141-144`; `src/cli/cmd_buildlmdb.cpp:236-245, 591, 635`; `src/common/path_resolver.cpp:168-187`; `src/cli/cmd_reindex.cpp:509-535`.

### R1 -- Memo escapes to disk

`src/memo/` and `include/memo/` contain zero ramfs references. The store wired for X64 tables is `dottalk::memo::MemoStore` (the `.dtx` sidecar), using raw `std::fstream` plus `fs::create_directories`. An in-RAM X64 table with a memo field writes a real `<ramroot>/<table>.dtx` and creates the directory to hold it. `VDISK STATUS` will not show it, and the `mem_proof.dts` zero-files property does not hold for a memo-bearing table.

*Incidental:* `X64MemoStore` (`.lob`/`.meta`) is dead code -- factory `make_x64_memo_store` has no caller. Feeds `AIF-079` instance 7.
**Anchors:** `src/memo/memo_auto.cpp:28-50, 86`; `src/memo/memostore.cpp:474, 499-519`; `include/memo/memostore.hpp:129`; `src/memo/x64_memo_store.cpp:195`.

### R3 -- The Layer-2 budget is reporting-only

`VDISK_RAM_SIZING_AND_ADMIN_CONFIG_V1` describes warn at `warn_pct`, then `on_full = warn | spill | fail`. In source the only comparison lives **inside the `VDISK STATUS` handler**; `OnFull::Spill` and `OnFull::Fail` are never branched on; no write path consults `used_bytes()`.

A runaway RAM table can exhaust host memory with no warning unless a human types `VDISK STATUS`. The dangerous part is that `VDISK CONFIG` prints `on_full = fail` and implies a guarantee that does not exist. Feeds `AIF-079` instance 3.
**Anchors:** `src/cli/cmd_vdisk.cpp:223, 226`; `include/cli/vdisk_config.hpp:30`; `src/cli/vdisk_config.cpp:89-95`.

### R4 -- Legacy `.inx` path unrouted

`InxPayload::readFromFile` / `writeToFile` use raw streams; the writers in `cmd_index.cpp` and the `.inx` branch of `cmd_reindex.cpp` use `std::ofstream`; `cmd_setindex.cpp` has no virtual check. `cmd_reindex.cpp` does include ramfs, but the guard applies only to the `.cdx` lane. Native CDX-V64 as the in-RAM index is a deliberate decision; the gap is that the non-V4 path is reachable rather than rejected.
**Anchors:** `src/xindex/inx_payload.cpp:274, 284`; `src/cli/cmd_index.cpp:241, 264`; `src/cli/cmd_reindex.cpp:384, 509-535`.

### R6 -- Write-ahead journal unrouted (conditional, lowest severity)

`table_state.cpp` uses `std::fopen` on `<dbf-path>.tbj` and fsyncs, with no ramfs awareness. Severity is limited: the default `BufferPersistenceMode` is `RamOnly` and every journal entry point short-circuits on `is_persistent_enabled()`. But when a user enables `TABLE BUFFER PERSISTENT` on a RAM table, the WAL is a real fsynced disk file next to a table that has no disk existence, inverting the durability story. Two notes: the path is correctly absolute except a narrow lazy-open fallback yielding a cwd-relative `area<N>.tbj`; and `set_persistence_mode` is commented "Stub only" (feeds `AIF-079` instance 6).
**Anchors:** `src/cli/table_state.cpp:243-251, 276-292, 358`; `include/cli/table_state.hpp:80, 85, 88`.

## 5. Scope

**In:** an open-area guard on `VDISK UNMOUNT` (R2); an `is_virtual()` refusal in `BUILDLMDB` (R5); a decision plus implementation for memo on virtual paths (R1); `on_full` enforcement or config-surface downgrade (R3); refusal or warning on the `.inx` and `.tbj` virtual paths (R4, R6).

**Out:** routing LMDB into RAM (a documented non-goal; V6 makes it refuse, not work). Concurrency and the registry mutex (separate milestone). RAM-to-disk snapshot (`VDISK SNAPSHOT` does not exist; separate).

## 6. Design note: one guard, not five

Five findings are the same shape -- a writer that does not know about virtual paths. Rather than five bespoke checks, consider a single helper that any non-routed writer calls:

```
xbase::ramfs::refuse_if_virtual(path, "<layer name>") -> bool
```

returning a uniform "this path is virtual and <layer> cannot serve it" error. The value is not the five call sites it fixes; it is that the **next** unrouted writer fails loudly instead of leaking to disk. R1-R6 are the instances found by one investigation, not a proof that the set is closed.

## 7. Milestone gates

### V6.0 -- Decisions locked -> `source-evidenced`
**Exit:** R1 memo policy decided (route through ramfs, or refuse memo fields on virtual tables); R3 decided (enforce `on_full`, or downgrade the config surface to advisory and say so); R4/R6 decided (refuse or warn); guard-helper shape (section 6) ratified.
**Proof:** decisions note appended to this document.

### V6.1 -- Guards landed -> `source-evidenced`
**Exit:** R2 and R5 implemented; the remaining decisions from V6.0 implemented; compiles on Windows/MSVC and WSL/Ubuntu.
**Proof:** build logs both toolchains; reviewed diff manifest; `git` sha.

### V6.2 -- Proven -> `runtime-evidenced`
**Exit, as DotScript assertions extending `mem_proof.dts` or a sibling script:**
1. `VDISK UNMOUNT` with an area open on a virtual path is refused (or force-closes cleanly), and no post-unmount write reaches an orphan buffer.
2. `BUILDLMDB` under a mounted vdisk errors clearly and creates **no** directory under the RAM root.
3. Per the R1 decision: either a memo write on a RAM table is visible in `VDISK STATUS` and leaves no `.dtx` on disk, or it is refused with a clear message.
4. Residency assertion: after a full RAM session exercising table plus index plus memo, a directory listing of the RAM root shows zero real files.
**Proof:** captured transcript with `.T.` markers, registered in `cmd_regression`.

## 8. Risks

- **R2 fix could break teardown ergonomics.** `VDISK UNMOUNT` is used in `mem_proof.dts` for a deterministic clean slate while areas may be open. A hard refusal could break existing scripts; force-close is probably the friendlier semantic. Decide at V6.0 and check the corpus.
- **R1 routing memo is larger than it looks.** `MemoStore` uses `fs::create_directories` and directory scans, not just stream I/O. Refusal may be the honest V6 answer with routing deferred.
- **Assertion 4 is the real prize and the most fragile.** A zero-real-files check is exactly the kind of proof that catches the next unrouted writer, and exactly the kind that fails for incidental reasons (stray logs). Scope it to the RAM root only.

## 9. Register

- Lane `AIF-043`, milestone `V6`. **No new AIF number claimed** -- these are defects in this lane's own scope.
- Feeds `AIF-079` (declared-capability validator) instances 3, 6, 7. That lane must not fix them; they are its known-answer proof set.
- Related: `XIDX-TXN-02`. `CdxNativeBackend` is both the in-RAM index backend and a carrier of the stubbed `upsert`/`erase`, which is why the in-memory lane is the cheapest place to prove incremental index maintenance (no fsync, no torn writes, no atomic-rename question). See the reconciliation note in the same session package, section 4.

## 10. Status ledger

| Date | Gate | Status | Evidence |
|---|---|---|---|
| 2026-07-30 | -- | `planned` | This declaration; R1-R6 source-verified at `b702b5a5d`, double-checked by an independent source pass |
| | V6.0 | pending | |
| | V6.1 | pending | |
| | V6.2 | pending | |
