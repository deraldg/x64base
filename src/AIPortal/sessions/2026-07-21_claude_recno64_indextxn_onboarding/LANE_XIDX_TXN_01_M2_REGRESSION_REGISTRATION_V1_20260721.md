# Lane `XIDX-TXN-01` — M2 Regression Registration & Scoring (v2)

**Date:** 2026-07-21
**Artifact:** `index_txn_lmdb_maintenance.dts` (M2 proof) — now authored to match the real curated idioms in `dottalkpp/data/scripts/`.
**Placement:** file under the **migrated** scripts location (per Derald) — `dottalkpp/data/scripts/migrated/index_txn_lmdb_maintenance.dts`.
**Status:** `review-needed` — mirrors `index_v64_cdx_lmdb_smoke.dts` bootstrap/copy/cleanup; adds the TABLE ON→COMMIT path the sibling smoke does not cover.

---

## 1. What the real scripts confirmed

- Comment token is `*`; narration via `ECHO` / `? "..."`; `SET TALK ON` for verbose command output; scripts end with a banner (some with `QUIT`).
- Verified idioms lifted from `index_v64_cdx_lmdb_smoke.dts`: `SET PATH DBF|INDEXES|LMDB ...`, `WORKSPACE CLOSE`, `ERASE <t> CONFIRM`, `USE`, `COPY TO <t> WITH SIDECARS OVERWRITE`, `CDX CREATE` / `CDX ADDTAG <field>`, `BUILDLMDB CLEAN YES`, `SET INDEX TO <t>`, `SET ORDER TO TAG <field>`, `SEEK`, `TUP`/`TUPLE`.
- Presence/absence counting idiom from `SELECTOR_REGRESSION_V1.DTS`: `COUNT FOR LNAME = "X"`.

## 2. Two corrections baked into v2

1. **The sibling smoke does NOT cover the gap.** `index_v64_cdx_lmdb_smoke.dts` mutates in **immediate mode (TABLE OFF)** and seeks the mutated value — that path already works today via the `replaceFieldStored` index hook. The M2 script therefore drives **TABLE ON → REPLACE → COMMIT** explicitly; that is the unmaintained path.
2. **Freshness must be proven by `SEEK`, not `COUNT FOR`.** `COUNT FOR LNAME = "X"` scans the **DBF**, so it returns 1 even when the index is stale (COMMIT wrote the field). Only `SEEK` consults the index. The gate lines are `SEEK <new>` / `SEEK <old>` + `TUP` to show the landed row.

## 3. Registration (one entry in `kRegressionSpecs`, `src/cli/cmd_regression.cpp`)

```cpp
{
    "INDEX_TXN",
    "migrated\\index_txn_lmdb_maintenance.dts",
    "LMDB index key maintenance inside COMMIT (lane XIDX-TXN-01 M2 proof)",
    false   // keep OUT of default suite until M1 lands (FAILS pre-M1 by design)
},
```

Run:
```
REGRESSION RUN INDEX_TXN
REGRESSION SHOW INDEX_TXN
```
Flip `in_default_suite` to `true` only after M1 lands and STEP 2 + STEP 4 pass.

## 4. Scoring rubric (SEEK-based gate)

| Step | PASS (post-M1) | FAIL (pre-M1) |
|---|---|---|
| STEP 1 baseline | `SEEK WHITE` found | (setup) |
| **STEP 2** (gate) | after TABLE ON→REPLACE→COMMIT: `SEEK ZZ_TXN_BUFFERED` found; `SEEK WHITE` **not** found — no BUILDLMDB between | new key not found, and/or old key `WHITE` still resolves (now pointing at a row whose LNAME is the sentinel) |
| STEP 3 rollback | `SEEK ZZ_TXN_ROLLBACK` not found; `SEEK MARTIN` found | (passes regardless — no bulk opened) |
| **STEP 4** (gate) | after TABLE ON→DELETE→COMMIT: `SEEK CLARK` **not** found | `SEEK CLARK` still resolves (deleted row) |
| STEP 5 CNX control | native CNX unchanged (rebuild-on-commit) | n/a |

**Gate = STEP 2 + STEP 4.** Both flip FAIL→PASS when the M1 patch lands, with no rebuild between mutation and seek → the `runtime-evidenced` promotion to M2.

## 5. Reconcile-before-run checklist (now small)

- **Fixture keys.** Script uses `WHITE`, `MARTIN`, `CLARK` (all present in the SANDBOX `students` fixture per the sibling smoke). Confirm they exist; substitute if the SANDBOX fixture differs.
- **`SET TALK ON` output.** Confirm `SEEK` prints a found/not-found line under TALK ON so a not-found is legible (STEP 2/4 old-key and deleted-key checks rely on it). If `SEEK` is silent on miss, add a following `TUP` diff (already present) — a not-found leaves the cursor at EOF/unchanged.
- **`migrated\` slot.** Confirm the SCRIPTS slot resolves `migrated\...`; the other curated entries use `canaries\` and `main\` subpaths, so a `migrated\` subdir should resolve the same way.

## 6. Safe to add pre-M1

Registered `in_default_suite = false`, so `REGRESSION ALL` is unaffected. `REGRESSION RUN INDEX_TXN` today yields the **red baseline** (STEP 2/4 fail) — the falsifiable acceptance test M1 must satisfy.
