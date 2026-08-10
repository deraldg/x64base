# Handoff Received & Reconciled — 2026-07-21 (Claude / Cowork)

Digested the parallel session's handoff and **verified it against the live intake queue**
(`docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`, rows read directly): confirmed
**AIF-041 = BETA-1 stabilization & regression lane**, **AIF-042 = script-header contract
(`@script.usage`) lane**. **Ceiling = AIF-042; next-free = AIF-043.** AIF-041 M1 explicitly
scopes "RECNO64" and "WAL/COMMIT durability" coverage — so this collection's work intersects
it directly.

## Corrections to THIS collection's AIF proposals (supersede the earlier files)

1. **RECNO64 nav/index residual — FOLD UNDER AIF-027, not a new lane.**
   The earlier `_SESSION_INDEX` / `STEWARD_PACKAGE` proposed **AIF-041** — that id is BETA-1.
   **Do not reuse 041.** Correct disposition: a milestone/residual under the existing
   **AIF-027** lane. It also **feeds AIF-041** (BETA-1) M1 RECNO64 coverage, M2 full sweep,
   and M3 refactor analysis. The carriers are dev-confirmed (O11 `cdx_backend.cpp:863`,
   BUILDLMDB `cmd_buildlmdb.cpp:445`, `order_step_cdx` `order_iterator.cpp:407`, plus the
   dev-only find `cmd_indexseek.cpp`). The drift flag stands: AIF-027 "M4-5 done" is a
   *storage* sparse proof; *index/nav* addressing past 2³¹ is open.

2. **`SET INDEXTXN` transactional index maintenance — if filed = AIF-043**, cross-linked to
   **AIF-023** (WAL / CDX-LMDB reconciliation) and **AIF-017**. **Source drafts are
   snapshot-based — re-ground against dev HEAD before any source proposal.** Overlaps the
   other session's `cmd_commit.cpp` contract fixes + `WAL_COMMIT_ROLLBACK` regression;
   coordinate (my M1 patch edits `cmd_commit.cpp`).

3. **Onboarding — not a new lane.** Overlaps **AIF-005** (assimilation portal) + **AIF-010**
   (front door, promoted). The single quick win is the small **`AI_README` Cowork-access
   insert** in `CANDIDATE_onboarding_trigger_and_AI_README_insert_V1`.

## Stewardship observations feed AIF-041 M3 (code-refactor analysis, Rule of Three)
`OBSERVATIONS_STEWARDSHIP_V1` O1–O11 are direct inputs to AIF-041 M3: **O4** (three
duplicated LMDB recno scanners), **O8** (dead `IOrderProvider` subsystem — delete/freeze),
**O1** (same LMDB env opened in ≥4 places), **O11** (cursor recno truncation). Route them there.

## Build / `.txt` note (do NOT act now)
The other session added `AIPortal` to `src/CMakeLists.txt` `_EXCLUDE_DIRS`, so
`GLOB_RECURSE` no longer sees `src/AIPortal/`. **After that configures green**, the
`candidate_source/*.cpp.txt` / `*.hpp.txt` should be restored to native names **ONCE**
(per the handoff — no flip-flopping). Not done here; gated on the maintainer's build.

## Shared-tree hazard — acknowledged
Two sessions have uncommitted work in `D:\code\ccode`. This AIPortal collection is
namespaced under `src/AIPortal/sessions/` and now CMake-excluded, so it separates cleanly
from the other session's **promotable engine work** (`cmd_regression.cpp`, new `.dts`,
contract fixes, `src/CMakeLists.txt`) — which **landed as commit `d8123d2a4`** on
`homegrown-cnx-20251112-branch` (dev-only, unpushed; 16 files, +962/-87).

**PROVENANCE ANCHOR = `d8123d2a4`.** All proposals in this collection
(RECNO64 residual, `SET INDEXTXN`, onboarding) anchor to this baseline. The
`src/AIPortal/` collection itself remained uncommitted/untouched by that commit.

**Stale-source alert:** my `SET INDEXTXN` M1 `cmd_commit.cpp` draft
(`candidate_source/cmd_commit.cpp.txt`) predates `d8123d2a4`, which now carries the
`@dottalk.usage` contract fixes to `cmd_commit.cpp`. **RESOLVED 2026-07-21:** re-grounded diff delivered as
`cmd_commit.cpp.INDEXTXN.M1.d8123d2a4.patch` — additive (8 hunks) on top of `d8123d2a4`,
header untouched, gated by `SET INDEXTXN` (default OFF → inert). The full-file
`candidate_source/cmd_commit.cpp.txt` is **SUPERSEDED — do not apply it.**
**Companion re-ground DONE 2026-07-21:**
- `settings.hpp.INDEXTXN.d8123d2a4.patch` — `settings.hpp` is untouched at `d8123d2a4`; applies clean.
- `cmd_set.cpp.INDEXTXN.d8123d2a4.patch` — anchored *past* the contract fix (insert after `SET DELETED`,
  before `SET ERRORSTOP`); helpers verified present at baseline (`up_copy`:152, `parse_on_off`:356, `print_line`:501).
The full `SET INDEXTXN` M1 source set (cmd_commit + settings.hpp + cmd_set.cpp) is now baseline-anchored to
`d8123d2a4` as additive diffs, superseding the snapshot-based `candidate_source/` drafts. Still candidate/gated:
needs a `SET INDEXTXN` lane (AIF-043) + build + `REGRESSION RUN INDEX_TXN` before it's a formal proposal.

**Build/test package added 2026-07-21 (all candidate, baseline `d8123d2a4`):**
- `cmd_regression.cpp.INDEX_TXN.d8123d2a4.patch` — **+1 MERGE** onto the other session's 15 `kRegressionSpecs`
  (16th entry `INDEX_TXN`, `in_default_suite=false`); confirmed it slots after `WAL_COMMIT_ROLLBACK`.
- `index_txn_lmdb_maintenance.dts` — **updated**: restores `SET INDEXTXN OFF` at cleanup (ambient hygiene).
- `BUILD_TEST_PLAN_INDEXTXN_M1_V1_20260721.md` — staged apply→build→test plan (REGRESSION ALL green; INDEX_TXN
  OFF=miss / ON=hit flip; assert data not shape; report by stage). No `CMakeLists.txt` change (runtime toggle).

**APPLIED to live source 2026-07-21 (maintainer-authorized):**
- `include/cli/settings.hpp` — `index_txn_on` flag + `indexTxnOn()/setIndexTxn()` + env default.
- `src/cli/cmd_commit.cpp` — 10 hunks (includes, `apply_one_recno` capture/apply, bulk begin/commit/abort per exit, `reconcile_after_mutation`).
- `src/cli/cmd_set.cpp` — `SET INDEXTXN ON|OFF` branch.
- `src/cli/cmd_regression.cpp` — `kRegressionSpecs` 15→16 (`INDEX_TXN`, out of default suite).
- `dottalkpp/data/scripts/migrated/index_txn_lmdb_maintenance.dts` — placed (ON gate + OFF restore).
Stage: **Dev — applied, uncommitted, NOT built, NOT promoted.** Build: `cmake --build build --config Release --target dottalkpp`.

**Open proof (other session / maintainer, task #170):** `REGRESSION RUN WAL_COMMIT_ROLLBACK`
is committed but unproven — expect `W0/W1/W2` all `:.T.` after rebuild.

## What I did NOT touch
Build code, `cmd_regression.cpp`, `src/CMakeLists.txt`, the intake queue, dashboard,
`projects.yaml`, `CURRENT_TARGET.md`, any `SESSION_CLOSEOUT_*`. Report-only into my own
collection; promotion stays maintainer-gated.
