# M1 Assembly — In-Memory Tables (AIF-043, drop 1)

> **▶ RESTORED AS M1 PRIMARY (2026-07-21 substrate re-flip).** Briefly demoted during the
> symlink pivot, then restored: the **in-process VFS is M1's primary substrate** after weighing
> the redistribution licensing of Windows RAM-disk drivers (signed kernel drivers, each with a
> license to vet — see the charter's "IN-PROCESS VFS PRIMARY" decisions). The symlink/ImDisk
> route is now the *optional* LMDB-in-RAM add-on only. This doc's `io()`-seam design is back on
> the critical path. The path-keyed evolution of it is `xbase::ramfs` (drop V1 — supersedes the
> single per-area `_mem` stringstream with a registry so `USE` can reopen and the sibling `.cdx`
> resolves). Two pieces already landed and are now M1-critical: (1) `serialize_x64_dbf(
> std::ostream&)` in `dbf_create.cpp` (drop 1b-i — lets `create_dbf` serialize into a RAM file);
> (2) the drop-1a `io()` seam in `xbase.hpp`/`record_view.cpp`/`dbf_file.cpp` (record-I/O routing).



**Locked decisions (2026-07-21):** durability = **C1 ephemeral**; index backend =
**B1 LMDB-in-RAM**; row storage = **A1 RAM-backed DBF byte store**. Stage: plan (not
applied). Prereq: none new (RECNO64 already in).

## Grounding (source-read)

`DbArea` (`include/xbase.hpp`) holds **one byte store**: `std::fstream _fp;` (:355).
Everything flows through it — `isOpen()` = `_fp.is_open()` (:145); record positioning is
`gotoRec64` → offset → `_fp.seekg` (`src/xbase/dbf_file.cpp:238–251`); record bytes via
`readCurrent()`/`writeCurrent()` (:161–162) using `_fp.read`/`_fp.write`; header via
`_fp.seekp(4,...)`/`write`. A separate `::CreateFileW` handle (`dbf_file.cpp:132`) exists
only for **Windows share-locking**. So the schema/record/nav logic is byte-store-agnostic
already — it never assumes a file, only seek/read/write at offsets.

## The seam (REVISED after source-read — much smaller than first drafted)

Two findings collapse the risk:

1. **Loaders are file-open-only.** `vfp_loader::peekVersion/readHeader/readFields` and
   `x64_loader::readHeader/readFields` take `std::fstream&` (`xbase_vfp.hpp:130/141/174`,
   `xbase_64.hpp:482/522`) and run **only** in `DbArea::open()` on an existing file. A
   `CREATE MEMORY` table is built fresh (header/fields populated in RAM, like
   `dbf_create.cpp`) and **never calls the loaders**. → **No loader signature changes.**
2. **Every op explicitly seeks first** (readCurrent/gotoRec64 `seekg(pos)`; appendBlank
   `seekg(0,end)`→`seekp(recPos)`→write; count writeback `seekp(4)`). Nothing relies on a
   stale get/put pointer → **a single-cursor memory stream is safe.**

So the seam is just the record-I/O path, not a storage-manager rewrite:

```
// DbArea members: keep the file stream; add a RAM stream + a flag.
std::fstream    _fp;                 // unchanged (file tables; loaders still take this)
std::stringstream _mem;             // RAM byte store for in-memory tables (M1)
bool            _in_memory{false};
std::iostream&  io() { return _in_memory ? static_cast<std::iostream&>(_mem)
                                          : static_cast<std::iostream&>(_fp); }
```

- Route the **record-I/O** sites `_fp.` → `io().`: `readCurrent`/`writeCurrent`
  (`record_view.cpp` — read next), `gotoRec64` seek (`dbf_file.cpp:251`), `appendBlank`
  (`:285–347`), header record-count writeback (`:329–341`). ~10–12 sites, all in the
  read/write/append path.
- **Leave file-only sites on `_fp`:** `open()` (`:124`), the loader calls in
  `readHeader/readFields` (`:194–229`), and the `CreateFileW` lock handle — these are the
  open-existing-file path, never used by a mem table.
- **`isOpen()`** (`xbase.hpp:145`): `return _in_memory ? true : _fp.is_open();`
- **`close()`**: if `_in_memory`, clear `_mem`/reset flag (ephemeral drop); else close `_fp`.
- **`size()` for append**: `io().seekg(0,std::ios::end)` + `tellg()` works on both
  `fstream` and `stringstream` (stringstream reports its buffer length).

Confirm `readCurrent`/`writeCurrent` bodies in `record_view.cpp` before applying (one more
read) so their `_fp.` sites route cleanly. Blast radius ~10–12 sites, **no loader/member-type
change** → still its own drop with `REGRESSION ALL` green, but far less surface than a full
storage-manager abstraction. (The heavier `IByteStore` abstraction remains a valid *later*
refactor if a non-copying, non-`stringstream` store is wanted for huge tables; `stringstream`
is fine for M1 ephemeral.)

## ▶ DROP 1a APPLIED 2026-07-21 (behavior-preserving io() seam; not yet built)

- `include/xbase.hpp`: `#include <sstream>`; `isOpen()` flag-aware
  (`_in_memory ? true : _fp.is_open()`); `std::iostream& io()` helper;
  members `std::stringstream _mem` + `bool _in_memory{false}`.
- `src/xbase/record_view.cpp`: `readCurrent`/`writeCurrent` record I/O `_fp.` → `io().`
  (incl. `!io()` / `static_cast<bool>(io())` state checks). Zero `_fp` left.
- `src/xbase/dbf_file.cpp`: `gotoRec64` seek + all of `appendBlank` → `io()`. **Left on
  `_fp` (correct):** `open()`, `readHeader`/`readFields` loaders (`std::fstream&`), the
  `CreateFileW` lock handle — the open-existing-file path a mem table never uses.
- `_in_memory` is never set true in 1a → `io() == _fp` everywhere → **byte-identical
  behavior.** Gate: `cmake` green + `REGRESSION ALL` green (proves the routing is
  transparent). Then drop 1b wires `CREATE MEMORY` (flip `_in_memory`, build header in RAM).

**Steward find (separate, pre-existing 🔴):** `readCurrent` (`record_view.cpp:69–70`) and
`writeCurrent` compute the record offset from `_crn` (the **clamped int32 mirror**), not
`_crn64`. `gotoRec64` clamps `_crn` to `INT32_MAX` past 2^31 — so read/write of a record
beyond 2^31 lands at the clamped offset (wrong record). This is a RECNO64 read/write-path
bug independent of the io() seam; fold into AIF-027 (its own small drop:
`checked_record_pos_(*this, _crn64)`).

## CREATE MEMORY (ephemeral open path)

- New verb (house-style TBD in charter §D): `CREATE MEMORY <table> (<fields>)` builds the
  DBF header **in RAM**, sets `_store = MemByteStore{}`, no file created, flavor tag
  `v64-mem`. `isOpen()` true while the area lives.
- **Ephemeral lifecycle:** `CLOSE`/quit drops the vector; nothing persisted; no `.dbf`
  written, no `ERASE` needed. `WORKSPACE` report shows the area as RAM-resident.
- **Locking:** an in-memory table is process-local/single-area → `RLOCK`/`FLOCK`/`UNLOCK`
  short-circuit to success (no `CreateFileW` handle on `MemByteStore`). Confirm
  `xbase_locks.cpp` guards on the file handle.
- **Memo:** out of scope for M1 (no `.fpt`/`.dbt` in RAM yet) — reject or ignore memo
  fields in `CREATE MEMORY` for M1; in-RAM memo is a later milestone.

## M1 proof (self-asserting, fixture-free .dts)

`CREATE MEMORY MEMTBL (ID N(4), NAME C(20))`; APPEND 3–4 rows with a dup; assert via `?`:
row read-back (`M0_row2`), `REPLACE`+read (`M1_replace`), ordered/physical `TOP/BOTTOM/GOTO/SKIP`
land correctly (`M2_nav*`), and **zero files created** (a directory check shows no
`MEMTBL.dbf`), then `CLOSE` and confirm the table is gone (`USE MEMTBL` fails). Register as
`REGRESSION MEM_TABLE` (out of default suite until stable). Gate: all markers `.T.`, no
disk artifact.

## M2 preview — LMDB-in-RAM index (next drop)

Windows has **no `/dev/shm`**, and LMDB requires a real env path. Practical "RAM-speed"
options: (i) LMDB env on a temp dir with `MDB_NOSYNC | MDB_WRITEMAP` → never fsyncs, runs
at memory speed, temp env deleted on CLOSE (ephemeral); (ii) a Windows RAM disk (ops, out
of scope); (iii) investigate an LMDB env sized to stay resident. Recommend (i): a `LMDB/MEM`
temp env, `MDB_NOSYNC`, dropped on close. The `CdxBackend` + `index_hooks` +
**SET INDEXTXN in-COMMIT maintenance** all apply **unchanged** — buffered REPLACE+COMMIT
maintains a RAM index with no BUILDLMDB. That composition is the headline of this lane.

## Risk & sequencing

The byte-store refactor is the whole M1 risk (central class, ~30 sites). Do it as one
isolated drop, `REGRESSION ALL` + `INDEX_X64/X32` green before `CREATE MEMORY` is even
wired. Then the `CREATE MEMORY` open path + proof `.dts` is a small additive second step.
Tuple-system core (`DbTupleStream`) untouched.
