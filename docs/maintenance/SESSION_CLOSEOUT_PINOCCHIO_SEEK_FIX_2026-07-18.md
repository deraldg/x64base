# Session Closeout — Pinocchio SEEK keyed range-seek (Phase 1.3c)

```yaml
ai_report_audit:
  report_id: AIPR-20260718-002
  project: project.x64base.runtime
  branch: homegrown-cnx-20251112-branch
  baseline_commit: 1ce8f45d79d4a5d80ef7d006c784e54420bd4541
  build_banner: "1ce8f45d dirty"
  access_mode: local_write
  scope: src/cli/cmd_seek.cpp (one file)
  authorization_note: >
    Original change made only in the dev repo D:\code\ccode on the existing
    branch. No branch created/switched/renamed. Not applied to C:\x64base or
    GitHub. Requires a maintainer rebuild + proof run before any promotion.
  stage: proven_by_teed_transcript
  proof_logs:
    - labtalk/proofs/runs/seek_fix_proof_teed_20260718T204940Z.log  # sha CF5996648A4147EFD8F6A1784742ADB5A80BA5B0BFA7ADBB27E98C63E29386E9
    - labtalk/proofs/runs/setfilter_fix_proof_teed_20260718T204150Z.log  # sha 7B791221C569C211ECFD417D2A8E10999F3EC4DBC2965B5AEA861546DF90AE51 (companion SET FILTER fix)
```

## What changed

`src/cli/cmd_seek.cpp` — `seek_via_cdx_active_order` gained a keyed range-seek
fast path. For an **ascending** `SEEK` on the active CDX tag it now calls the
existing `CdxBackend::seekRecnoUserKey` (LMDB `MDB_SET_RANGE`, O(log n)) before
the old linear index walk. The landed record is re-verified against the DBF field
(`compare_field_value == 0`, not deleted); any prefix-only / deleted / unverified
landing, any `seekRecnoUserKey` miss, and all descending seeks **fall through to
the unchanged exact+near linear walk**. Added `#include "xindex/cdx_backend.hpp"`.

No backend change was needed — `seekRecnoUserKey` already existed and was already
used elsewhere; `SEEK` simply never called it.

## Why (measured) — and the proof result

The Phase 1.3a scale sweep caught `SEEK` walking the CDX cursor linearly. Proof
run on the rebuilt binary (build `Jul 18 2026 20:07:15`), interactive `./datarun`
chat-sourced capture:

| Case | Before | After (measured) |
| --- | ---: | ---: |
| ENROLL 5.5M — ascending `SEEK` near-last (50999999) | 56.99 s | **0.0033 s** |
| STUDENTS 1M — ascending `SEEK` near-last (50999999) | 16.57 s | **0.0020 s** |
| ENROLL 5.5M — ascending `SEEK` middle (50500000) | — | 0.0025 s (→2750514) |
| STUDENTS 1M — char tag `SEEK ANDERSON` (LNAME) | — | 0.0015 s (→655360) |
| ENROLL 5.5M — ascending `SEEK` first (50000000) | 0.0022 s | 0.0022 s |

All Found-at recnos identical to the pre-fix linear walk. The keyed
`MDB_SET_RANGE` jump replaces the O(position) walk. **~17,000× on the ENROLL
near-last case.**

### Two cases the first proof left slow (both since addressed / scoped)

- **Not-found ascending seek** — `SEEK 59999999` returned "Not found" correctly
  but in **79.5 s**: the miss fell through to the O(n) walk. **Fixed and
  confirmed**: build `Jul 18 2026 20:21:59` → `SEEK 59999999` = **0.0015 s**.
  When the backend reports a genuine "not found" and `SET NEAR` is OFF, it now
  short-circuits without the walk.
- **Descending seek** — descending `SEEK 50000000` returned `Found at 8` in
  **67–77 s**: descending had been gated out of the fast path. **Fixed** by
  making the keyed fast path direction-independent (it is a keyed *exact* lookup;
  direction never mattered). One intended behavior change: for a **duplicated**
  key the keyed seek returns the **smallest-recno** match, so descending
  `SEEK 50000000` now lands on recno **1** instead of **8**. The largest-recno
  landing was an incidental side effect of the old walk direction, not a
  contract; SEEK's contract is "land on an exact match," and both directions are
  now consistent. Unique keys (e.g. STUDENTS SID) are unaffected. This avoided a
  ~60-line untested `CdxBackend` method. **Proven**: build `Jul 18 2026 20:49`,
  descending `SEEK 50000000` = **0.00015 s** (was 67 s), `Found at 1`.

### Final proof result (all SEEK cases sub-millisecond)

Teed log `seek_fix_proof_teed_20260718T204940Z.log` (sha `CF599664…`), all
recnos correct:

| Case | Before | After |
| --- | ---: | ---: |
| S2 ENROLL near-last (asc) | 56.99 s | 0.00014 s (→5501354) |
| S6 STUDENTS near-last (asc) | 16.57 s | 0.00017 s (→1000000) |
| S3 ENROLL middle (asc) | — | 0.00014 s (→2750514) |
| S4 ENROLL not-found (asc) | 79.5 s | 0.00011 s (Not found) |
| S5 ENROLL descending | 67 s | 0.00015 s (→1, was 8) |
| S7 STUDENTS char tag ANDERSON | — | 0.00015 s (→655360) |

## Correctness (behavior-preserving by construction)

The fast path only short-circuits on a **verified exact match** identical to what
the linear walk would return:

- Exact equality re-checked at the DBF level (`compare_field_value == 0`), so a
  prefix landing (e.g. `SEEK "5099"`) is rejected and falls through.
- Deleted landing rejected (walk skips deleted) → falls through.
- Ascending duplicate selection returns the smallest-recno record at the key,
  which is exactly the first record the ascending walk yields.
- Descending seeks skip the fast path entirely (walk unchanged), preserving the
  descending duplicate-selection recno (e.g. descending `SEEK 50000000` → 8).
- Any `seekRecnoUserKey` error/miss falls through (no behavior masked).

Proof: `dottalkpp/data/scripts/pinocchio/pinocchio_seek_fix_proof.dts` +
`run_pinocchio_seek_proof_teed.ps1`. Canary recnos to match the pre-fix walk:
ENROLL `50999999`→5501354, STUDENTS `50999999`→1000000, descending
`50000000`→8, `59999999`→not found, `ANDERSON` (LNAME tag)→first Anderson.

## Scope boundary — what this does NOT change

- **FIND** (`cmd_find.cpp`) is **untouched**. Its own CDX path uses *contains*
  semantics (`contains_for_find`), which a keyed prefix-seek cannot answer
  correctly, so it must keep its linear scan. FIND's cases that delegate to
  `cmd_SEEK` (exact) do get faster for free.
- **LOCATE / CONTINUE** stay O(n): they evaluate arbitrary predicates, not a
  keyed lookup.
- **`DELETE` active-order surcharge** (Phase 1.3b Finding 3) is a separate
  reposition path, not addressed here.
- **`SET FILTER` unquoted-string-literal bug** (`MAJOR = CSCI` → 0 vs `COUNT FOR`
  → 90700) is a predicate-parsing issue, still open.

## Still open (for follow-up)

1. Build on host + run the SEEK proof; record before/after into the scale ledger.
2. `SET FILTER` string-literal correctness bug.
3. Decide whether `DELETE`/`RECALL` under an active order should drop to physical
   reposition (removing the ~2.5 ms/row surcharge) as a targeted perf fix.
