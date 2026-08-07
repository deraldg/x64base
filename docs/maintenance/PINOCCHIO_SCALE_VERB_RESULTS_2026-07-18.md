# Pinocchio Phase 1.3a -- Indexing/Scale Verb Sweep, Results (2026-07-18)

Read-only battery `pinocchio_scale_readonly.dts` run on the host at build
`Jul 17 2026 18:15:42` (banner `1ce8f45d dirty`), branch
`homegrown-cnx-20251112-branch`. Same battery on `STUDENTS` (1,000,000) and
`ENROLL` (5,501,358); `SET TIMER ON` per-command `ELAPSED` is the datum.
Machine: Alienware m16 R2 / Core Ultra 9 185H (maintainer-attested project
workstation). Machine-readable rows in
`PINOCCHIO_SCALE_VERB_BENCHMARKS_V1.csv` (PIN-SCALE-001..043).

## Evidence tier (honesty boundary)

These numbers are bound to a **directly-teed runner transcript**, produced on the
host by `run_pinocchio_scale_teed.ps1`:

| Log | SHA-256 | Rows |
| --- | --- | --- |
| `labtalk/proofs/runs/scale_readonly_teed_20260718T154349Z.log` | `9769C1D8476A51F638EB08F8745E64CDE6D7562A82696EE4FEB1E0D51075B068` | PIN-SCALE-001..043 |

The on-disk bytes were re-hashed and match the runner-reported SHA-256 exactly;
the log is complete (full COMPLETE banner, clean shutdown) and carries
per-command ELAPSED. CSV `evidence_tier` is `RAW_TEED_TRANSCRIPT`. Encoding
caveat (load-bearing for the hash): the log is UTF-16LE with embedded ANSI color
codes -- the raw PowerShell console capture, left untouched; decode UTF-16 to read
it, and do **not** re-encode or line-ending-normalize it or the SHA-256 drifts.
`.gitattributes` already marks `labtalk/proofs/runs/*.log` as `binary`. Values in
this doc match the earlier interactive capture (superseded by this teed run).
Correctness signals are taken from the engine's own `Found at N` / `COUNT`
output, which is authoritative regardless of tier.

## Result 1 -- FLAT verbs stay flat at 5.5x the rows (nav fix holds at scale)

| Verb | STUDENTS 1M | ENROLL 5.5M |
| --- | ---: | ---: |
| `COUNT` (no filter) | 0.0023 s | 0.0014 s |
| `GO TOP` / `GO BOTTOM` / `GO n` | ~0.002-0.0035 s | ~0.002 s |
| `TOP` / `BOTTOM` | ~0.002 s | ~0.002 s |
| `SKIP +/-100000` | 0.003-0.006 s | 0.004-0.007 s |

`COUNT`, `GO`, `TOP`, `BOTTOM`, and `SKIP` are all independent of table size --
identical timings across a 5.5x row increase. This is the direct confirmation
that the Phase 1.2 ordered-navigation fix scales.

## Result 2 -- LINEAR verbs scale as O(n)

| Verb | STUDENTS 1M | ENROLL 5.5M |
| --- | ---: | ---: |
| `COUNT FOR` | 33.3 s | 63.5 s |
| `COUNT` under `SET FILTER` | 20.7 s | 60.4 s |
| `AVG` / `SUM` / `MIN` / `MAX` (each) | ~17 s | ~59 s |
| `LIST FOR` (1-5 row result) | 34.7 s | 121.1 s |
| `LOCATE` near-end | 27.3 s | 94.2 s |
| `SCAN...ENDSCAN` (empty body) | 31.0 s | 114.9 s |

All make a full pass. **Comparison caveat:** the two tables differ in row *width*
as well as count -- STUDENTS has 9 fields (incl. EMAIL), ENROLL has 2 -- so
absolute ratios are not a clean 5.5x. The cleanest pure-iteration measure is
`SCAN...ENDSCAN`: ~31 us/row on STUDENTS, ~21 us/row on ENROLL (narrower rows).
The O(n) character is unmistakable regardless.

Plain `COUNT` confirmed O(1) here (0.0014-0.0023 s reading the header); the cost
is only in the `FOR`/filter forms. This corrects the earlier "COUNT was the
problem" shorthand -- the problem is *predicated* COUNT and the other scan verbs.

## Result 3 -- SEEK sentinel confirmed (headline; next optimization target)

`SEEK` holds a CDX cursor but walks it linearly instead of a keyed range-seek
(`cmd_seek.cpp:210-298`), so cost tracks the key's position in the order:

| Case | STUDENTS 1M | ENROLL 5.5M |
| --- | ---: | ---: |
| `SEEK` first key (50000000) | 0.0018 s | 0.0022 s |
| `SEEK` near-last key (50999999) | 16.6 s (`Found at 1000000`) | 57.0 s (`Found at 5501354`) |
| `SEEK` canary under `DESCEND` (now last) | 17.1 s | 58.7 s |

~9,000x (1M) to ~26,000x (5.5M) slower for a far key than a near key, and the
far-key cost itself scales 16.6 s->57.0 s with row count -- a full linear index
walk. All lands are correct (`Found at` recnos verified). This is the same defect
class already fixed for `TOP`/`BOTTOM`/`SKIP`; fixing it (issue a keyed
`MDB_SET_RANGE`, then step) is Phase 1.3c.

## Correctness findings

- **Canaries green:** `COUNT` = 1,000,000 / 5,501,358; `TOP` = record 1 SID
  50000000 (Taylor Quinn / W26BIOL288); GPA aggregates AVG 2.99933, MIN 2, MAX 4;
  SID aggregates MIN 50000000, MAX ~51000000; every `SEEK`/`LOCATE` `Found at`
  recno correct; `LIST FOR SID = 50999999` returns the right 1 (STUDENTS) / 5
  (ENROLL) rows.
- **DISCREPANCY -- RESOLVED 2026-07-18: `SET FILTER` vs `COUNT FOR` on an
  unquoted string literal.** `COUNT FOR MAJOR = CSCI` -> **90700**, but
  `SET FILTER TO MAJOR = CSCI` then `COUNT` -> **0** -- `CSCI` was parsed as an
  undefined identifier, not the string. Fixed by applying the same
  `normalize_unquoted_rhs_literals` in `cmd_setfilter.cpp` that `COUNT FOR` uses.
  Confirmed: `setfilter_fix_proof` (sha `7B791221...`) F1=F2=F3=90700, numeric
  F4=1, char F5=F5b=72420, no regressions. PIN-SCALE-010.
- **Minor display quirk:** `SMARTLIST ... NEXT 1` after a `SEEK` lists from the tag
  top, not the sought cursor position (e.g. after `SEEK 50999999 -> Found at
  1000000`, the follow-up SMARTLIST printed record 1). `SEEK`'s own `Found at`
  line is correct; the SMARTLIST-after-SEEK cursor coupling is the cosmetic gap.

## Secondary observation -- aggregates don't share a scan (ADDRESSED)

Four aggregates over `GPA` cost ~17 s **each** (~68 s total); a single-pass
multi-aggregate collapses that to one scan. **Done 2026-07-19:** added
`AGGS ALL <expr>` (`cmd_aggs.cpp`) computing COUNT/SUM/AVG/MIN/MAX in one scan,
reusing the standalone verbs' exact parse/eval/visibility path.
See `SESSION_CLOSEOUT_PINOCCHIO_AGGS_ALL_2026-07-19.md` +
`pinocchio_aggs_all_proof.dts` (pending host rebuild + proof).

## Phase 1.3b -- destructive verb profile (1M scratch clone)

`pinocchio_scale_destructive.dts` (v2 diagnostic) run to completion on a
disposable `SCR_DESTR` clone of `STUDENTS` (1,000,000 rows). Evidence tier:
interactive `./datarun` chat-sourced capture (the teed runner can hash-bind it).
All correctness canaries green: clone `COUNT` = 1,000,000, recno 1 = 50000000
Taylor Quinn; each `DELETE` marked 9999 and each `RECALL ALL` returned to 0;
`PACK` kept 990001; `ZAP` -> 0.

| Verb | ELAPSED | Class |
| --- | ---: | --- |
| `COPY TO ... AS X64` (full clone) | 85.7 s | O(n) copy |
| `BUILDLMDB` (1 tag) | 18.5 s | O(n log n) build |
| `REINDEX CDX CLEAN` | 18.5 s | O(n log n) rebuild |
| `DELETE FOR` (~9999), **active CDX order** | 65.4 s | O(n) scan + per-delete surcharge |
| `DELETE FOR` (~9999), **order cleared** | 40.0 s | O(n) predicate scan |
| `RECALL ALL` (~9999) | ~51 s | O(n) scan + per-recall work |
| `COUNT DELETED` | ~18 s | O(n) scan |
| `PACK` (drop 9999 of 1M) | 0.54 s | O(n) bulk rewrite (fast) |
| `ZAP` | 0.030 s | O(1) header |

**Finding 3 (corrected). `DELETE`/`RECALL` cost = an O(n) predicate scan plus a
large per-affected-row constant; the active CDX order adds a reposition
surcharge -- but it is *linear in the number of deletes*, not quadratic.** The
order-cleared `DELETE FOR` (40 s) is dominated by the full 1M predicate scan --
the same O(n) cost as `COUNT FOR`/`LIST FOR`. Under the active order, `DELETE`
adds ~25 s over that for 9999 rows ~= **~2.5 ms per deleted row** of
cursor-reposition/index-maintenance overhead (~2500x a raw flag-set). That
penalty is per-delete, so v1's ~500k-row delete ~= 500k x 2.5 ms ~= **21 min**,
matching the ~24-min non-completion before it was killed -- it would have
finished. (An earlier note here called this ~O(n^2); the measurement shows it is
linear-in-deletes with a big constant, because the reposition is local, not a
from-top index walk. Corrected.)

Implications for 1.3c: the keyed range-seek fix squarely targets `SEEK`/`FIND`/
`LOCATE`-by-key (the read-only sentinel). It does **not** remove `DELETE FOR`'s
dominant cost, which is the inherent O(n) predicate scan; only the ~25 s
active-order surcharge is in the same family. `PACK` (0.54 s) and `ZAP`
(0.030 s) are not scale concerns and need no work.

### Root cause of the DELETE/RECALL active-order surcharge (traced 2026-07-18)

Not `refresh_current` (that is cheap: `readCurrent` + optional TALK print,
`include/cli/nav_move.hpp:57`). The ~2.5 ms/row is **one LMDB write transaction
per index key per deleted row**:
`cmd_delete.cpp delete_targets_by_recno` -> `delete_current_with_lock` ->
`IndexManager::apply_delete_snapshot` (`index_manager.cpp:499`, loops the record's
keys) -> `on_delete` -> **`CdxBackend::erase` (`cdx_backend.cpp:399`)**, which does
`reset_ro_txn_()` + `begin_rw_txn_()` + `mdb_del` + `end_txn_commit_()`
(`mdb_txn_commit` fsyncs the meta page) + `reset_ro_txn_()` **every call**. A
9,999-row delete = ~9,999 commits ~= 25 s. `RECALL ALL` is the same shape
(re-insert per row). This is *necessary* index maintenance -- the keys must be
removed to keep the index in sync with the DBF -- it is simply un-batched.

**Recommended fix (next session, not rushed): batch the index writes.** Split
the bulk delete into (1) per-row DBF mark + snapshot capture under lock, then
(2) a single write transaction that erases all captured index keys, committed
once (per tag DBI). Must preserve exact results (COUNT DELETED / RECALL -> 0 /
canaries) and handle the multi-tag case; the win is ~N commits -> O(tags)
commits. Deliberately deferred: it restructures the correctness-critical
index/DBF-sync path and should get its own build + proof cycle, not an
end-of-night untested change. Tracked as a task.

**RESOLVED 2026-07-19 (Phase 1.3d).** Implemented a bulk write-transaction mode
on `CdxBackend` (with a bulk-aware `setTag` so `capture`'s per-field setTag does
not open a conflicting second transaction / deadlock), passed through
`IndexManager`, and wrapped the DELETE/RECALL loops with chunked (10k) commits.
Proven: `DELETE FOR` under an active order dropped **65.4 s -> 37.8 s** (now ==
the order-cleared 41.3 s baseline -- surcharge gone), canaries green, no deadlock.
See `SESSION_CLOSEOUT_PINOCCHIO_DELETE_BATCH_2026-07-19.md`
(teed sha `0294344D...`). RECALL's symmetric upsert-batching path is implemented
but not yet directly measured (the script clears the order before RECALL).

## Next steps

1. Optional: run `run_pinocchio_scale_teed.ps1` to hash-bind these numbers, then
   flip `evidence_tier` in the CSV to `RAW_TEED_TRANSCRIPT`.
2. Phase 1.3b -- destructive battery (`DELETE`/`RECALL`/`PACK`/`ZAP`/`REINDEX`),
   with a lane rebuild afterward.
3. Phase 1.3c (cleanup/polish) -- fix the `SEEK`/`LOCATE` linear walk (keyed
   range-seek) and the `SET FILTER` unquoted-string-literal discrepancy.
