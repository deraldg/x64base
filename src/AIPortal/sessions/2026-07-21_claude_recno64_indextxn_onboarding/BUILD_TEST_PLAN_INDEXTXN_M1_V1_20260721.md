# Build & Test Plan — SET INDEXTXN M1 (candidate)

**Status:** `review-needed` proposal. Nothing applied. Baseline **`d8123d2a4`** (clean green).
**Report by stage** (AI_PORTAL): Dev → Promoted to Staging → Validated → Published. Never claim a later stage from an earlier one. Long builds are maintainer-operated (MSVC); the agent prepares, the maintainer runs.

## Apply set (all additive, all `#if DOTTALK_HAS_XINDEX`, all gated `SET INDEXTXN` default OFF)
| Diff | Target | Merge note |
|---|---|---|
| `cmd_commit.cpp.INDEXTXN.M1.d8123d2a4.patch` | `src/cli/cmd_commit.cpp` | sits **on top of** the contract fix (header untouched) |
| `settings.hpp.INDEXTXN.d8123d2a4.patch` | `include/cli/settings.hpp` | file untouched at baseline; clean |
| `cmd_set.cpp.INDEXTXN.d8123d2a4.patch` | `src/cli/cmd_set.cpp` | anchored past the contract fix (after SET DELETED) |
| `cmd_regression.cpp.INDEX_TXN.d8123d2a4.patch` | `src/cli/cmd_regression.cpp` | **+1 MERGE** onto the other session's 15 entries (16th, `in_default_suite=false`) |
| `index_txn_lmdb_maintenance.dts` | SCRIPTS slot at `migrated\` (confirm folder) | disposable-copy proof; restores `SET INDEXTXN OFF` |

## Build
No reconfigure needed — you are already LMDB mode (`DOTTALK_HAS_XINDEX=1`, `XINDEX_HAVE_LMDB`). `SET INDEXTXN` is a **runtime** toggle (default OFF), not a compile switch — it ships inert.
```
cmake --build build --config Release --target dottalkpp
```
Expected: **green, warning-clean.**

## Test (assert data, not shape)
1. **`REGRESSION ALL` → still green.** Proves the OFF-default INDEXTXN set does not regress the BETA-1 suite (WAL/COMMIT etc.).
2. **`SET INDEXTXN OFF` → `REGRESSION RUN INDEX_TXN`** → STEP 2 `SEEK ZZ_TXN_BUFFERED` **misses** (today's stale-index behavior — the RED baseline).
3. **`SET INDEXTXN ON` → `REGRESSION RUN INDEX_TXN`** → STEP 2 `SEEK ZZ_TXN_BUFFERED` **hits at rec 12**; old key misses; STEP 2b ordered `BOTTOM` lands on the sentinel; STEP 4 `DELETE`+`COMMIT` erases the key — **no `BUILDLMDB` between.** The OFF→ON flip is the proof.
4. Script restores `SET INDEXTXN OFF` at cleanup (ambient stays clean).

**Assertion standard:** score on the specific `SEEK`/`RECNO`/`TUP` output (landed row = the sentinel record), not "ran clean." A green readback that can't name its landed recno is not proof (local-access checklist).

## Coordination (shared tree)
- `cmd_commit.cpp`: rebase this diff onto `d8123d2a4`; do not overwrite the committed contract fix.
- `cmd_regression.cpp`: `+1` merge — keep the other session's 15 entries; add the 16th only.
- No `CMakeLists.txt` change. No `students` fixture mutation (disposable copy).

## Safety / rollback
Default OFF ⇒ inert until turned on. Reuses the installed `xbase::index_hooks` seam (no engine change). If any step fails, revert the isolated diffs; no data was mutated.

## Gate / lane
This is candidate. Formalizing needs: a `SET INDEXTXN` lane (**AIF-043**, x-link AIF-023/017), the Source-Mutation preflight (carried in each patch header), maintainer authorization to apply, then build + the test above. Feeds **AIF-041** M1 (RECNO64/WAL coverage) and M3 (refactor).
