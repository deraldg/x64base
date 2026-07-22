# Virtual Disk — RAM Sizing Algorithm & Admin Config (AIF-043)

> **▶ REPOSITIONED 2026-07-21 (substrate re-flip): OPTIONAL LMDB-in-RAM add-on, not M1.**
> M1's primary substrate is now the self-owned **in-process VFS** (`xbase::ramfs`) — no
> third-party RAM-disk driver, no license to vet. This symlink/RAM-disk route survives only as
> the *optional* path for **LMDB-in-RAM** (LMDB must mmap a real OS file, so it can't use the
> in-process VFS). Everything below applies when a user opts into that add-on; it is not
> required for DBF + native-CDX in RAM. Driver-licensing caveat: the ImDisk **Toolkit** is GPL;
> prefer the permissive **core ImDisk driver** (ltr-data.se) if bundling.


**Stage:** design (report-only). **Author:** Claude (steward) · **Authority:** Derald ·
**Date:** 2026-07-21. Companion to the lane charter (`PROJECT_LANE_IN_MEMORY_TABLES_V1`) and
the `mem` flavor script (`data/scripts/mem.dts`). Records the co-planned decision to back
in-memory tables with a **symlinked RAM volume** and how its size is chosen and governed.

## The substrate (recap)

In-memory tables are ordinary `.dbf`/`.cdx`/LMDB files written into a **virtual-disk root**
that is an OS symlink/junction to a RAM filesystem. `DO mem` points the DBF/INDEXES/LMDB
path slots at that root (`data/scripts/mem.dts`). No new record/create/loader code — the OS
provides RAM residency. LMDB rides along because a tmpfs file is a real mmap-able file.

- **Linux:** `/dev/shm` is tmpfs (real RAM), zero setup. Symlink the `mem` subfolders there.
- **Windows (dev truth):** no native tmpfs; a RAM disk needs a driver (ImDisk/OSFMount).
  Junction (`mklink /J`, no admin) the `mem` subfolders to the mounted RAM volume. A junction
  to an ordinary folder is still disk — the RAM comes from the *target*, not the link.

## Why two layers

The **hard** size limit belongs to the OS mount (tmpfs / RAM-disk driver), which the engine
did not create and cannot unilaterally resize. So sizing is split:

- **Layer 1 — provisioning recommendation.** A number the engine *computes and reports* for
  an admin (or a provisioning script) to size the RAM volume. Advisory, not enforced by us.
- **Layer 2 — engine soft budget.** A byte counter the engine *does* own: it tracks bytes
  written under the vdisk root, warns at a high-water mark, and applies an `on_full` policy.
  Portable and honest even when the OS mount size is out of our hands.

## Layer 1 — default sizing algorithm (`mode = auto`)

```
total  = physical RAM (bytes)
avail  = available RAM at startup (bytes)   ; respect current load, not just total
budget = clamp(PERCENT * avail, FLOOR, CEIL)
budget = min(budget, HARDCAP_FRACTION * total)   ; never starve the host
```

Defaults (tuned for an educational engine: small tables, but "the whole show" should fit):

| Knob | Default | Rationale |
|------|---------|-----------|
| `PERCENT` | 25% of **available** | leaves headroom for OS + app + file cache |
| `FLOOR` | 64 MB | always fits the sample dataset + a CDX or two |
| `CEIL` | 2 GB | caps a runaway from eating the machine |
| `HARDCAP_FRACTION` | 0.50 of **total** | matches the tmpfs `/dev/shm` convention |

Worked examples:
- 16 GB box, 10 GB free → 25%·10 = 2.5 GB → clamp to CEIL 2 GB → 2 GB < 8 GB cap → **2 GB**.
- 4 GB box, 1.5 GB free → 25%·1.5 = 384 MB → above FLOOR, under caps → **384 MB**.
- 1 GB box, 300 MB free → 25%·300 = 75 MB → above FLOOR 64 MB → **75 MB** (degrades gracefully).

## Layer 2 — engine soft budget

The engine keeps a running `used_bytes` for files under the vdisk root:
- At **`warn_pct`** (default 80%) of the effective budget, emit a one-line note
  (`VDISK: RAM disk 80% full (1.6/2.0 GB)`), non-fatal.
- At **100%**, apply `on_full`:
  - `warn` — allow the OS write to fail naturally (ENOSPC), surface a clear engine message.
  - `spill` — fall back to the real-disk slot for new writes ("convert RAM → disk"); the
    RAM-resident tables stay, new ones go to disk. (M3 hook; M1 may stub to `warn`.)
  - `fail` — refuse the mutation before the OS does, with a clean, actionable error.

The soft budget is advisory relative to the OS hard limit: whichever triggers first wins.

## Admin config — `[vdisk]` block in `init.ini`

Same `.ini` idiom `INIT` already processes (system `dottalkpp.ini`, user `init.ini`),
alongside the path slots. **Entirely optional** — absent block = feature off, existing
setups unaffected.

```
[vdisk]
enabled   = 1                      ; 0 = ignore mem flavor's RAM intent, treat as plain disk
root      = D:\ramdisk\dottalk     ; the symlink/junction target (the RAM volume)
mode      = auto | fixed | percent ; auto = the Layer-1 clamp above
size_mb   = 512                    ; used when mode = fixed
percent   = 25                     ; used when mode = percent (of available RAM)
floor_mb  = 64                     ; bounds even fixed/percent overrides
ceil_mb   = 2048                   ; bounds even fixed/percent overrides
warn_pct  = 80                     ; Layer-2 high-water warning
on_full   = warn | spill | fail    ; Layer-2 policy at 100%
```

Rules:
- `mode = auto` runs the clamp; `fixed`/`percent` are explicit admin overrides.
- `floor_mb`/`ceil_mb` clamp **even the overrides**, so a fat-fingered `size_mb` can't wedge
  the host.
- Missing keys take the defaults in the table above; a missing `[vdisk]` block = disabled.
- `root` is where an admin mounted the RAM volume; the `mem` flavor's `DBF/mem` etc. junctions
  should resolve there.

## Admin setup (one-time, per machine)

1. Mount a RAM volume (Linux: use `/dev/shm`; Windows: mount a RAM disk with a driver).
2. Create the three junctions the `mem` flavor expects, pointing into that volume:
   - `data/dbf/mem`     → `<ram>/dbf`
   - `data/indexes/mem` → `<ram>/indexes`
   - `data/lmdb/mem`    → `<ram>/lmdb`
   (Windows: `mklink /J data\dbf\mem <ram>\dbf`, etc.)
3. Add the `[vdisk]` block to `init.ini` with `root = <ram>` and any size overrides.
4. `DO mem` → `CREATE X64 …`/`USE …` now land in RAM. `DO x64` switches back to disk.

## Scope

- **M1:** the `mem` flavor + `[vdisk]` parser + Layer-1 recommendation + Layer-2 warn (spill
  may stub to warn). Proof `.dts` verifies `DO mem` → CREATE/APPEND/nav in RAM, disk
  untouched under the x64 slots.
- **M3 hooks:** `on_full = spill` (RAM→disk), `VDISK SNAPSHOT` (persist the RAM root / pack
  as memo). Logged here so the surface is designed once.
