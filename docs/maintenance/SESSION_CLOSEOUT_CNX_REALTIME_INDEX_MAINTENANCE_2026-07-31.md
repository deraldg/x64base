---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260731-003
  recorded_at_utc: 2026-07-31T21:40:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: claude-cowork:not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 3dd3871ef53b6f3f112fca3046373b8e59d3c38c
  authorization:
    requested_by: maintainer
    scope: >
      Give the native sorted CNX index realtime maintenance at direct maintainer
      instruction ("make cnx realtime", then "We are simply updating the sorted
      cnx style files to work realtime when lmdb is not awailable like using
      vdisk"). Includes the reverted first attempt, the regression pair split
      that followed, and two adjacent fixes surfaced by the work: SET ALTERNATE
      TO truncation (AIF-081) and repository_role_guard WSL support.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_CNX_REALTIME_INDEX_MAINTENANCE_2026-07-31.md
    kind: session_closeout
---

# Session Closeout -- CNX Realtime Index Maintenance (XIDX-TXN-02 M1)

    lane        : XIDX-TXN-02 (index transaction / realtime maintenance)
    also touches: AIF-081 (output capture), staging tooling (role guard, hooks)
    owner       : member.derald
    steward     : member.ai.claude.cowork
    run         : 2026-07-31_cowork_cnx_realtime
    host        : WSL2 Ubuntu, GCC 13.3.0, preset wsl-lean
    tier        : runtime-proven where stated; UNMEASURED items are marked

---

## 1. What this session set out to do

Make the native sorted CNX index maintain itself in realtime, so an x32/v32
table -- or an in-RAM table on the vdisk -- has a usable order without LMDB and
without a full REBUILD after every edit.

The starting position: `CnxBackend::upsert` and `CnxBackend::erase` were no-ops
that set `stale_` and returned NORMALLY. Every CNX edit left the order wrong,
and until `wasStale()` was wired into the replace seam earlier the same day, it
did so silently.

---

## 2. What landed

### 2.1 Realtime CNX maintenance (`src/xindex/cnx_backend.cpp`)

`upsert` and `erase` now maintain the loaded permutation:

- `erase(key, rec)` locates by RECNO and removes. It ignores the seam's key
  because a keyless payload has no key to match on, so it cannot disagree
  about one.
- `upsert(key, rec)` binary-searches the insertion point by comparing the
  edited record's LIVE field value against the live field value of the record
  at each probe position. About log2(n) record reads per edit.

The seam emits deletes before inserts, so `rec` is already out of the
permutation before probing starts and cannot be encountered as its own
comparand.

`stale_` is no longer set on the success path. It IS still set when maintenance
is genuinely impossible (no document, no active tag, tag names no field, an
unreadable probe), and the corrective warning still fires there.

### 2.2 Why a keyless index can be maintained at all

This is the finding the session turned on, and it was produced by a FAILED
attempt rather than a successful one.

A CNX RUN1 payload stores 4 bytes per recno and NO KEYS:

    src/cnx/cnx_document.cpp:81   entries.push_back(InxEntry{"", rn});

`CnxCursor::fill_` corroborates it by returning `outKey = Key{}`. Order lives
in the SEQUENCE of `entries_`, not in comparable key data. So `entries_` is a
PERMUTATION and the ordering authority is the live table -- the same authority
`collect_sorted_recnos_for_tag_` uses when it rebuilds.

The first attempt routed through key-ordered `InxPayload::insert/erase`. Against
an all-empty-key vector both degenerate: `lower_bound` always returns `end()`,
so the delete removed nothing and the insert appended at the bottom. Measured:

    [INDEX TRACE] apply_replace ... emitted_del=1 emitted_ins=1
                  staleBefore=no leftStale=no
    E_T2_stale_order_still_starts_at_ANDERSON:.T.

Both ops "fired", nothing moved, and the engine had stopped warning. Broken AND
silent is strictly worse than broken and honest, so it was reverted on the
owner's instruction before the cause was known. The cause was then found by
reading `cnx_document.cpp` rather than by guessing: the first post-mortem note
blamed payload lifetime and identity, which was the WRONG suspect. Identity was
fine; there were simply no keys.

### 2.3 Rebuild and realtime cannot drift

`derive_sort_entry_` and `sort_entry_less_` were factored out of
`collect_sorted_recnos_for_tag_`, and BOTH the rebuild path and the realtime
path now call them. Neither keeps its own copy of the normalisation or
comparison rules. If they drifted, a REBUILD would reorder differently from an
in-session edit and every ordering proof would flap.

`CNXLIVE` marker `L_T6` asserts this directly: a REBUILD immediately after a
maintained edit must be a NO-OP.

### 2.4 The INX side was not touched

`.inx` and `.idx` are their own formats and are not this lane's to change.
CNX reaches `InxPayload` only through its EXISTING public surface -- `entries()`
to read, `fromEntries1Inx()` to rebuild one. `include/xindex/inx_payload.hpp`,
`src/xindex/inx_payload.cpp` and `include/cnx/cnx_backend.hpp` are byte-identical
to HEAD; confirmed by their total absence from `git status`.

The cost of that constraint is an O(n) vector copy per edit. Knowingly accepted
as a first cut: correct, contained, and optimizable behind the same seam.

---

## 3. Runtime evidence

Build: wsl-lean, 2026-07-31. Default suite 8/8 green throughout.

### 3.1 CNXLIVE (`cnx_realtime_index_proof.dts`) -- realtime CNX, x32

    [INDEX TRACE] apply_replace rec=1 ... staleBefore=no leftStale=no
    REPLACE: Replaced field #2 at rec 1.        <- NO staleness warning
    L_G0_seek_works_before_mutation:.T.
    L_G1_baseline_top_is_ANDERSON:.T.
    L_T1_record_carries_new_value:.T.
    L_T2_realtime_order_top_is_AAAAA:.T.        <- TOP moved rec 2 -> rec 1, no REBUILD
    L_T3_second_row_is_ANDERSON:.T.             <- placed, did not append
    L_T4_bottom_is_ZEBRA:.T.                    <- permutation intact
    L_T5_seek_reaches_moved_record:.T.
    L_T6_rebuild_agrees_with_realtime:.T.       <- realtime order == rebuild order

Resulting permutation after the edit: AAAAA(1), ANDERSON(2), YOUNG(4), ZEBRA(3).

### 3.2 IDXSTALE (`index_maintenance_failure_proof.dts`) -- native CDX-V64, RAM

    REPLACE: record written, but index update failed; REINDEX/REBUILD needed.
    [INDEX TRACE] ... staleBefore=no leftStale=yes
    E_G0/E_G1/E_T1/E_T2/E_T3/E_T4  all .T.
    VDISK: RAM bytes = 826, RAM files = 2, nothing on disk

Ran green three times, twice on an earlier binary and once in the final pair
run. The repeat was unplanned and is the better evidence for it.

---

## 4. The regression pair, and why IDXSTALE was repointed not repurposed

When M1 landed, `IDXSTALE` E_T2 inverted to `.F.` -- correctly. That test exists
to prove maintenance CANNOT happen; CNX stopped being a valid subject for it.

The test was not wrong. Its SUBJECT moved. Its two predecessors had passed while
proving nothing, which is why every marker is a field comparison behind a cursor
guard, and discarding that would have thrown away the expensive part.

So it was repointed at `CdxNativeBackend`, whose `upsert`/`erase` are still the
same no-op stubs (`cdx_native_backend.cpp:507-519`, verified not assumed). That
is the native CDX-V64 path used by a RAM/vdisk x64 table, so the proof now
covers the in-memory lane and keeps every marker name, guard and header lesson.

`CNXLIVE` is the positive half. The pair reads as one contract with two sides:

    maintenance happens        -> CNXLIVE
    maintenance cannot happen  -> IDXSTALE, and the engine says so

Keeping both is what makes the inversion legible instead of looking like a
regression someone quietly retuned.

`CNXLIVE` adds three assertions that only become falsifiable once maintenance
actually runs: L_T3 (catches an insert that appends instead of places), L_T4
(catches a lost or duplicated entry), L_T6 (catches realtime/rebuild drift).

---

## 5. Adjacent fixes made in the same session

### 5.1 SET ALTERNATE TO truncates (AIF-081)

`output_router.cpp` opened the alternate file with `std::ios::app`. One
transcript accumulated THREE runs from three different binaries, and a
conclusion was drawn from the wrong one.

Classic xBase and FoxPro spell this `SET ALTERNATE TO <file> [ADDITIVE]`:
truncate by default, append on request. No ADDITIVE token exists here, so append
was unrequestable -- truncating removes a surprise rather than a capability.

Found because the committed AIF-081 runtime proof FAILED TO REPRODUCE ITS OWN
NUMBERS. Section 5a of that proof records the correction. Re-verified by running
the capture twice: 89 lines, one BEGIN marker, both times, matching section 4.

### 5.2 Staging tooling works from WSL (commit 3dd3871ef)

Two halves of one defect -- the staging tooling assumed Windows.

- `detect_role` compared against Windows literals through `normalized_path`,
  which calls `os.path.abspath`. On POSIX that resolves `D:\code\ccode` against
  the current directory, so the guard could not match DEVELOPMENT_ROOT to
  ITSELF and every WSL commit hard-failed.
- The generated hook body called a bare `python`, which resolves on Windows but
  not on Debian-family WSL.

Fixed by `windows_form()` / `windows_key()` and by resolving python3-then-python
in the hook. The permitted root set is UNCHANGED: verified 12/12 including six
refusals (`/mnt/d/code/other`, `/mnt/d/code`, `/mnt/e/code/ccode`,
`/home/x/ccode`, `/mnt/dd/code/ccode`, and a subdirectory of the root).

The sandbox is still refused, correctly -- its mount path is unrelated to either
declared root.

---

## 6. What is LEFT to make CNX realtime, in full

### 6.1 Wired but never exercised (tests, not code)

    APPEND with an index already attached
        apply_insert_snapshot exists and routes to upsert. CNXLIVE appends
        BEFORE creating the index, so every insert hit backend=no.

    Multi-tag container
        with_tag_switched_ saves and restores the active tag, so this is
        architecturally supported. CNXLIVE has exactly one tag; the
        save/restore path has never run against CNX.

    DELETE / RECALL
        no CNX coverage at all.

    Duplicate keys
        placement among equals is by recno via sort_entry_less_, matching
        rebuild by construction, but unasserted.

One extended proof script covers all four. Cheapest item on this list and the
most likely to surface something.

### 6.2 Genuinely missing (code)

1. SET TABLE BUFFER interaction. UNMEASURED and the worst failure mode here:
   `upsert` reads the record's LIVE value to place it, so if the edit is still
   in the buffer it places by the OLD value -- a wrong order that reports
   success. Do this first; it is cheap to measure and it lies when wrong.

2. Disk persistence. Maintenance is in-memory, so a disk CNX reverts to its
   last rebuilt order after close. RAM/vdisk is complete; disk is not. This is
   the milestone that makes "CNX is realtime" true generally rather than only
   for the vdisk case. Design seam already recorded in
   XIDX_TXN_02_M0_ADDENDUM_PERSISTENCE_SEAM_V1_20260731.md.

3. Deleted-record parity. `collect_sorted_recnos_for_tag_` walks `top()/skip()`
   so a rebuild reflects deleted visibility; realtime `upsert` does not check
   deleted status. If they disagree, REBUILD and realtime produce different
   orders. L_T6 would catch it, but only for the non-deleted case.

4. The O(n) copy per edit. Free at 4 records, roughly 8 MB of memory traffic per
   single-field REPLACE at a million. Fine for the intended RAM/vdisk scale, not
   "realtime" at large scale. Fixing it means a mutable path into the payload,
   which collides with the do-not-change-inx rule -- so it likely wants CNX
   owning its own payload type rather than borrowing InxPayload.

Suggested order: (1), then 6.1's coverage script, then (2), then (4) only if a
real workload demands it. (4) is a performance ceiling, not a defect.

---

## 7. Method notes worth keeping

Three artifacts caught their own errors this session, which is the
documentation-consumes-the-database thesis working at the author's expense
rather than in his favour:

1. The AIF-081 runtime proof existed to make its numbers re-derivable. Trying
   to re-derive them exposed the ALTERNATE append defect.
2. IDXSTALE inverted the moment the behaviour it asserted stopped being true.
   A test that goes red when the engine improves is doing its job.
3. `repository_role_guard.py` had never run outside the OS it was written on,
   and said so clearly the first time it was asked to.

Two process corrections earned the hard way:

- A finding is not a feature. A reverted attempt plus analysis is not progress
  unless the analysis is then spent.
- Verify the SUBJECT of a shared abstraction before using it. `InxPayload`
  serves two shapes -- 2INX with keys, CNX RUN1 without -- and assuming the
  first cost a full build/measure/revert cycle.

---

## 8. Provenance

    3dd3871ef  repository_role_guard: work from WSL as well as Windows

Slices prepared in this session and pending commit:

    src/cli/output_router.cpp
    docs/maintenance/AIF_081_OUTPUT_CAPTURE_RUNTIME_PROOF_V1_20260731.md
    src/xindex/cnx_backend.cpp
    dottalkpp/data/scripts/cnx_realtime_index_proof.dts
    dottalkpp/data/scripts/index_maintenance_failure_proof.dts
    src/cli/cmd_regression.cpp

Related: `XIDX_TXN_02_M0_ADDENDUM_PERSISTENCE_SEAM_V1_20260731.md` (already
committed), `OUTPUT_CAPTURE_COMPLETENESS_LANE_V1.md` (AIF-081 charter,
49dfec789), `AIF_081_OUTPUT_CAPTURE_RUNTIME_PROOF_V1_20260731.md` (0803f0f13).
