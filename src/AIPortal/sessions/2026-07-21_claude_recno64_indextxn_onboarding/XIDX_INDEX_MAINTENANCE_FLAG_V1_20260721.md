# Design Decision — Index Maintenance Mode Flag (`SET INDEXTXN`)

**Date:** 2026-07-21
**Applies to:** lanes `XIDX-TXN-01` (LMDB) and `XIDX-TXN-02` (CNX), and the M1 patch + M2 regression.
**Author:** Claude (hosted AI), grounded in `include/cli/settings.hpp` + `src/cli/cmd_setunique.cpp` patterns.
**Status:** `review-needed` (naming + default awaiting ratification).

---

## 0. Intent (as I understood it — correct if wrong)

- **Keep the batch-rebuild capability** (`REBUILD` for CNX, `REINDEX` for INX/IDX, `BUILDLMDB` for LMDB) permanently, for backwards-compatibility services and as the reconciliation path.
- Add a **flag** so transactional (incremental, in-COMMIT) index updates can be **delayed/disabled while testing**.
- **Default = OFF**: transactional maintenance off by default; the engine behaves exactly as it does today until the flag is turned on.

## 1. The flag

Runtime, process-wide, boolean, default **OFF** — mirrors `SET TALK`/`SET DELETED`.

```cpp
// include/cli/settings.hpp — add to struct Settings, under "Data handling":
std::atomic<bool> index_txn_on{false};   // SET INDEXTXN — transactional in-COMMIT index maintenance
                                          // OFF (default): legacy batch behavior (REBUILD/REINDEX/BUILDLMDB)
// convenience:
static bool indexTxnOn()        { return instance().index_txn_on.load(); }
static void setIndexTxn(bool on){ instance().index_txn_on.store(on); }
```

Command surface (model on `cmd_setunique.cpp` / the `SET` dispatch in `cmd_set.cpp`):

```
SET INDEXTXN            -> report current state
SET INDEXTXN ON|OFF     -> toggle
SET INDEXTXN USAGE
```

Optional CI/headless override (mirrors `DOTTALK_INDEX_TRACE` / `DOTTALK_DEV_DIAGNOSTICS`): env `DOTTALK_INDEX_TXN=1` seeds the default ON for a regression run without editing scripts. Runtime `SET` always wins.

> **Naming note (ratify):** you called this the "batch index updates" flag. I named the *setting* `INDEXTXN` so that **ON = the new batched-transactional path** and **OFF = legacy batch rebuild** — because "batch" alone is ambiguous (it could mean the bulk-txn batching *or* the rebuild). Alternatives if you prefer: `SET INDEX MAINTENANCE REBUILD|TRANSACTIONAL` (default `REBUILD`), or literally `SET BATCHINDEX ON|OFF`. Pick one; the semantics below are unchanged.

## 2. Behavior matrix (flag × backend)

| `INDEXTXN` | LMDB lane (CDX) | CNX lane | INX / IDX |
|---|---|---|---|
| **OFF (default)** | **today's behavior**: `auto_reindex_if_needed` skips CDX; index reconciled by explicit `BUILDLMDB` | rebuild-on-commit (`cmd_REBUILD`) | reindex-on-commit (`cmd_REINDEX`) |
| **ON** | transactional in-COMMIT bulk maintenance (`XIDX-TXN-01` M1) | in-mem delta + `CnxDocument::save()` (`XIDX-TXN-02` M1), fallback rebuild | unchanged (reindex) |

**Guarantee:** `INDEXTXN OFF` reproduces current behavior **byte-for-byte** — landing M1 changes nothing until someone opts in. That is the safe-rollout property and the "delay while testing" lever.

## 3. Gate change in the M1 patches

Replace the backend-only gate with a flag-AND-backend gate. LMDB lane (`commit_one_area`):

```cpp
bool maintain_index = false;
#if DOTTALK_HAS_XINDEX
auto& im = xindex::ensure_manager(A);
maintain_index = cli::Settings::indexTxnOn() && im.isCdx();   // <-- flag gates the new path
if (maintain_index) { if (!im.beginBulkWrite(&berr)) { ... } }
#endif
```

CNX lane (`auto_reindex_if_needed` CNX branch):

```cpp
if (orderstate::isCnx(A)) {
    if (cli::Settings::indexTxnOn() /* && payload present && delta bounded */) {
        // transactional: apply in-mem delta + CnxDocument::save(); fallback to rebuild on miss
    } else {
        cmd_REBUILD(A, args);            // legacy batch rebuild (unchanged default)
    }
}
```

When OFF: LMDB stays on the existing skip path, CNX stays on `cmd_REBUILD` — no new code executes.

## 4. Regression implication (important)

Because the default is OFF, the M2 proof script **must** enable the flag or it will exercise the legacy path and the gate steps won't test the new behavior. Add right after index setup, before the gate steps:

```
SET INDEXTXN ON
```

(Already added to `index_txn_lmdb_maintenance.dts` in this revision.) The CNX guard script, being a *correctness-retention* test, should run **both** states: `SET INDEXTXN OFF` (legacy rebuild) and `SET INDEXTXN ON` (delta+save) must each keep `SEEK` correct.

## 5. Edit sites

- `include/cli/settings.hpp` — add `index_txn_on` + accessors.
- `src/cli/cmd_set.cpp` (or new `src/cli/cmd_setindextxn.cpp`) — `SET INDEXTXN ON|OFF|USAGE` handler + message ids.
- `src/cli/cmd_commit.cpp` — gate the LMDB bulk wrap and the CNX branch on `Settings::indexTxnOn()`.
- Message catalog — `SetIndexTxnUsageText` / status text.
- Docs/HELP — register `SET INDEXTXN`; note default OFF and the retained batch-rebuild fallback.

## 6. Cross-lane record

- `XIDX-TXN-01` M1 patch: gate updated to `Settings::indexTxnOn() && im.isCdx()`.
- `XIDX-TXN-02` M1: CNX branch honors the same flag; `cmd_REBUILD` retained as the OFF path and the fallback.
- Both lanes: **the batch-rebuild capability is a permanent, supported path, not deprecated** — it is the default and the crash/stale reconciliation route (ties to D3(a)).
