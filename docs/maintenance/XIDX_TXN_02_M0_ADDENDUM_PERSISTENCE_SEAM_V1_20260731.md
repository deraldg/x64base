# XIDX-TXN-02 M0 Addendum -- the persistence seam V1

    lane        : XIDX-TXN-02 (CNX native transactional mutations)
    amends      : LANE_XIDX_TXN_02_M0_FINDINGS_V1_20260721.md
                  section 1 (format-neutral directive) and section 3 (C3, atomicity)
    date        : 2026-07-31
    author      : member.ai.claude.cowork
    status      : M0 addendum -- design only, NO source changed
    evidence    : source-evidenced (API read, no runtime probe)

---

## 1. Why this addendum exists

M0 locked approach A and specified persistence as "write a fresh, consistent
`.cnx` to a temp path, fsync, atomically rename over the original, clearing
`CNX_HDRF_DIRTY` last" (C3), with a note to confirm Windows rename-over
atomicity.

Section 1 separately directs that the mutable path be authored
FORMAT-NEUTRALLY, so the same code serves `.cnx` (V32) and a future native
`.cdx` (V64) store.

Those two requirements are in tension and M0 does not resolve it. The native
CDX store is the one that can be RAM-resident: the `MEM` regression builds an
x64 table AND its native CDX-V64 index entirely in RAM, RUN8, no LMDB, zero
files on disk. Temp-plus-fsync-plus-rename has no meaning there.

Left unresolved, this surfaces in M1 as a rewrite of `save()` rather than a
decision, which is the expensive order.

---

## 2. Finding -- ramfs has no rename

`include/xbase/ramfs.hpp` exposes, in full:

    mount(abs_root)                          :45
    unmount(abs_root)                        :46
    mounted(abs_root)                        :47
    is_virtual(abs_path)                     :51
    exists(abs_path)                         :54
    size(abs_path)                           :55
    erase(abs_path)                          :56
    list(abs_root)                           :60
    clear()                                  :64
    used_bytes()                             :68
    open(abs_path, create) -> iostream       :76

There is no rename, no move, and no atomic-replace primitive. `erase` plus a
fresh `open(create=true)` is a two-step with an observable window between them,
which is precisely what the temp-and-rename dance exists to avoid.

`fsync` is separately meaningless on a RAM file, but that is benign: a no-op,
not a correctness hole.

---

## 3. Resolution -- the requirement does not transfer, because the THREAT does not transfer

Crash-atomicity exists to stop a torn write from SURVIVING to the next open. A
RAM file cannot survive the process that holds it: `clear()` and `unmount()`
drop it, and process death takes the registry with it. There is no next open in
which a half-written RAM payload could be observed.

So the correct reading is not "emulate rename in ramfs." It is:

| container       | durability requirement | persistence mechanism                    |
|-----------------|------------------------|------------------------------------------|
| disk `.cnx`     | required               | temp + fsync + rename, `CNX_HDRF_DIRTY` backstop |
| disk `.cdx` nat | required               | same shared implementation               |
| RAM-resident    | **out of scope by construction** | single in-place full write, or no save at all |

This keeps section 1's format-neutral directive intact. The FORMAT is shared;
the DURABILITY POLICY is a property of the residency, not of the container
format. That is the same axis separation AIF-080 argues for one level up, and
it holds here for the same reason.

---

## 4. The seam already has its discriminator

`ramfs::is_virtual(abs_path)` (`ramfs.hpp:51`, implemented `ramfs.cpp:201`) is
exactly the predicate the persistence policy needs. No new capability is
required -- only that `save()` consult it and select a policy, rather than
assuming a filesystem underneath.

Recommended shape: `save()` resolves a persistence policy ONCE and delegates.
Two implementations, one interface, chosen by residency.

---

## 5. Hazard -- capture the policy at OPEN, never re-evaluate at SAVE

This is the part that will bite if it is not written down now.

`is_virtual()` is not stable for the lifetime of an open container. AIF-043
finding R2 (`AIF_043_V6_ROUTING_BOUNDARY_HARDENING_V1_20260730.md:44`, recorded
at HIGHEST SEVERITY) is exactly this: `VDISK UNMOUNT` with an open area flips
`is_virtual()` false while the stream buffer survives, splitting a live area
into a phantom RAM buffer and a disk-seeking metadata path.

Applied to this lane: a payload mutated under the RAM policy, then saved after
an intervening `UNMOUNT`, would select the DISK policy at save time and attempt
a temp-and-rename against a path that has no RAM backing and no disk file.

The near-term failure is at least loud rather than silent: `ramfs::open`
returns `nullptr` when `is_virtual()` is false (`ramfs.cpp:252`), so a save
attempted through the RAM path after an unmount fails to acquire a stream. But
"fails loudly with a dirty in-memory payload in hand" is still data loss unless
the fallback is specified.

**Rule for M1:** resolve the persistence policy when the container is opened,
store it on the backend, and use the stored policy for the life of that open.
Do not call `is_virtual()` from `save()`.

R2 remains unfixed and is not this lane's to fix. This lane must not depend on
it being fixed.

---

## 6. Open items -- confirm, do not assume

1. **Truncate semantics.** `ramfs::open(abs_path, create=true)` (`ramfs.cpp:250`,
   create branch at `:261`) -- does it truncate an existing file or position for
   append? An in-place full rewrite is only correct if it truncates. NOT
   verified; read the branch before relying on it.
2. **Does the native CDX store persist at all today?** If it is RAM-only by
   construction, the RAM policy is "no save," which is simpler than an in-place
   write and should be preferred. If it can also live on disk, both policies are
   reachable from one backend and the residency capture in section 5 is
   load-bearing rather than defensive.
3. **Windows rename-over atomicity** (`ReplaceFile` / `MoveFileEx`) remains open
   from C3 and is unchanged by this addendum.

---

## 7. Effect on the M0 gate and the M2 exit conditions

C3 is amended, not overturned: its mechanism stands for disk-resident
containers and is declared inapplicable to RAM-resident ones, with the
discriminator named and the capture rule specified.

M2 exit condition 2 ("crash-atomicity: kill mid-save, reopen sees
`CNX_HDRF_DIRTY`, rebuild fallback, SEEK correct") should be read as scoped to
disk-resident containers. It is not merely hard to test in RAM; it is
meaningless there, and a test asserting it would pass vacuously -- which is the
failure class this project keeps finding.

No other M0 decision changes. C1 (approach A), C2, C4 and C5 stand as written.
