# Session Report — Pinocchio Indexing & Scale (2026-07-18)

Branch `homegrown-cnx-20251112-branch`, baseline `1ce8f45d` (dirty). All original
changes in the dev repo `D:\code\ccode` only, on the existing branch — no branch
created/switched/renamed, nothing pushed to `C:\x64base` or GitHub. Machine:
maintainer-attested Alienware m16 R2 / Core Ultra 9 185H, project on the Samsung
970 EVO (D:).

## Headline

The engine's index-backed navigation and lookup are now fast at scale, and two
correctness bugs are fixed. Everything below is proven on the 1M / 5.5M pinocchio
fixtures with hash-bound teed transcripts and correctness canaries.

## Code changes (2 files, both proven)

| File | Change | Result |
| --- | --- | --- |
| `src/cli/cmd_seek.cpp` | Ascending+descending `SEEK` on the active CDX tag now uses the keyed `MDB_SET_RANGE` lookup (`seekRecnoUserKey`) instead of a linear index walk; genuine not-found short-circuits; re-verify guards fall back to the walk. | near-last `SEEK` 56.99 s → 0.00014 s; not-found 79.5 s → 0.00011 s; descending 67 s → 0.00015 s. All recnos correct. |
| `src/cli/cmd_setfilter.cpp` | Applies `normalize_unquoted_rhs_literals` (parity with `COUNT FOR`/`LIST FOR`) so unquoted string filters match. | `SET FILTER TO MAJOR = CSCI` → COUNT 90700 (was 0); numeric & quoted unchanged. |

One intended behavior change, documented: a duplicated-key **descending** `SEEK`
now lands on the smallest-recno match (e.g. `50000000 → 1`, was `8`) — consistent
with ascending; the specific duplicate was never part of SEEK's contract. Unique
keys unaffected.

## Proof evidence (hash-bound teed transcripts)

| Proof | Log | SHA-256 |
| --- | --- | --- |
| Nav (Phase 1.2) | `nav_defect_after_teed_20260718T142513Z.log` | `AD1E6A44…` |
| Nav filter/boundary | `nav_filter_boundary_after_teed_20260718T142513Z.log` | `F520E661…` |
| Scale read-only sweep (1.3a) | `scale_readonly_teed_20260718T154349Z.log` | `9769C1D8…` |
| SEEK fix (1.3c) | `seek_fix_proof_teed_20260718T204940Z.log` | `CF599664…` |
| SET FILTER fix (1.3c) | `setfilter_fix_proof_teed_20260718T204150Z.log` | `7B791221…` |

(The destructive profile 1.3b and the first scale capture are chat-sourced
`./datarun` captures, recorded as such.)

## What the scale sweep established

- **Flat / O(1)–O(log n) (proven flat 1M→5.5M):** `COUNT` (no filter), `GO`,
  `TOP`, `BOTTOM`, `SKIP` — all ~2 ms regardless of table size.
- **Linear / O(n) (honest, expected):** `COUNT FOR`, filtered `COUNT`,
  `SUM/AVG/MIN/MAX`, `LIST FOR`, `LOCATE`/`CONTINUE`, `SCAN…ENDSCAN`.
- **`SEEK` was the hidden O(n)** (a near-last key walked ~the whole index) — now
  fixed. `FIND` (contains) and `LOCATE` (arbitrary predicate) legitimately stay
  O(n) — a keyed lookup can't answer them.
- **`PACK` (0.54 s) and `ZAP` (0.030 s)** are efficient; not scale concerns.

Full per-verb numbers: `PINOCCHIO_SCALE_VERB_BENCHMARKS_V1.csv` (43 read-only +
9 destructive + 6 SEEK-fix rows). Narrative + findings:
`PINOCCHIO_SCALE_VERB_RESULTS_2026-07-18.md`.

## The one open item — DELETE/RECALL active-order surcharge (diagnosed, deferred)

`DELETE FOR` / `RECALL ALL` under an active CDX order carry ~2.5 ms/row on top of
the (inherent) O(n) predicate scan. Traced to `CdxBackend::erase`
(`cdx_backend.cpp:399`) doing **one LMDB write transaction — begin + `mdb_del` +
committing fsync — per index key per row**; a 9,999-row delete ≈ 9,999 commits ≈
25 s. This is *necessary* index maintenance, just un-batched. Corrected an earlier
overstatement: it is **linear-in-deletes with a large constant, not O(n²)**.

**Deliberately not fixed tonight.** The remedy (batch the index-key erases into
one transaction per bulk op) restructures the correctness-critical index/DBF-sync
path and must get its own build + proof cycle rather than a rushed untested
end-of-night change. Designed and tracked.

## Governance / closeouts

- `SESSION_CLOSEOUT_PINOCCHIO_SEEK_FIX_2026-07-18.md` — envelope AIPR-20260718-002,
  `stage: proven_by_teed_transcript`.
- `PINOCCHIO_STRESS_TEST_PLAN_V1.md` — Phase 1.3 (a/b/c) documented.
- Machine profile enriched from CPU-Z with maintainer attestation
  (`MAINTAINER_ATTESTED`), honesty boundary preserved.

## Suggested next session

1. Batch the DELETE/RECALL index-erase transaction (the diagnosed fix above).
2. Optional: single-pass multi-aggregate (`SUM/AVG/MIN/MAX` currently scan
   independently — ~17 s each on 1M).
3. Promotion review of the proven nav + SEEK + filter changes toward `C:\x64base`
   (maintainer-gated).
