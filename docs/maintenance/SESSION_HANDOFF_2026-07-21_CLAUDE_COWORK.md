# Session Handoff — 2026-07-21 (Claude / Cowork, local-access)

**To:** the other agent working `D:\code\ccode` (or its GitHub snapshot).
**From:** Claude in Cowork, with read/write access to the dev tree this session.
**Status of everything below:** dev-only, **uncommitted, unpushed, unpublished.** Nothing
promoted into staging (`C:\x64base`), GitHub, or the website. If you are working off the
public GitHub snapshot you will NOT see any of this until the maintainer commits/pushes.

---

## 1. What changed in the shared dev tree this session (all uncommitted)

**AIF-041 — BETA-1 stabilization lane, M1 regression net (built + proven green):**
- `src/cli/cmd_regression.cpp` — `kRegressionSpecs` now **15 entries** (was 9). Added:
  `DOTSCRIPT_EXPR` (default, green), `LEXING` (default, green), `DOTSCRIPT_PARITY`
  (explicit; RED on purpose — the `$name`-in-predicate parity target), `CALC`, `ERRORSTOP`,
  `WAL_COMMIT_ROLLBACK` (explicit).
- New `.dts`: `dotscript/dotscript_expr_regression.dts`,
  `dotscript/predicate_memvar_parity_regression.dts`,
  `pinocchio/wal_commit_rollback_regression.dts` (self-bootstrapping — creates+erases a
  throwaway `WALREGR` table under `DBF/SANDBOX`, never touches `students`).
- Proven on the 2026-07-21 MSVC build: `REGRESSION ALL` green; `DOTSCRIPT_EXPR`/`LEXING`
  green; `ERRORSTOP`/`CALC` green; `DOTSCRIPT_PARITY` correctly red.
- **Pulled** the legacy `commit_rollback_test.dts` from the registry — it assumed an open
  `students` table, didn't self-bootstrap, and silently no-op'd. Replaced by
  `WAL_COMMIT_ROLLBACK`. **Doctrine reinforced: every regression test sets its own
  environment** (ambient default is `STOP_ON_ERROR OFF`; tests that leave the ambient dirty
  stay out of the default suite).
- `@dottalk.usage` contract fixes at source (not the catalog): `cmd_var.cpp` (made real),
  plus `cmd_set.cpp`/`cmd_commit.cpp`/`cmd_rollback.cpp` mutation/effect fields; the VAR
  `dotref.hpp` entry now matches the corrected source contract.

**`src/CMakeLists.txt`** — added `${CMAKE_CURRENT_SOURCE_DIR}/AIPortal` to `_EXCLUDE_DIRS`.
The `src/AIPortal/` collection point is now permanently excluded from the `GLOB_RECURSE`
(like `tv`/`gui`/`build`). **Candidate source drafts there can keep native `.cpp`/`.hpp`
names — the `.txt` renaming is no longer needed for build safety.** (Build-required to take
effect. Do NOT flip-flop the existing `.txt` back-and-forth; restore to native names ONCE,
after this configures green.)

**AIF-042 — new lane opened:** `docs/maintenance/SCRIPT_HEADER_CONTRACT_LANE_V1.md` +
intake row. Extends the `@dottalk.usage` contract system to **script files** via a
language-neutral `@script.usage v1` header (one harvester, `runner:` as a field, `KIND`
column — not per-language forks). Dev-only, proposed.

## 2. Governance state you MUST respect

- **AIF id ceiling is now `AIF-042`.** Max in the live intake queue
  (`docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`) is **042**. **Next-free = AIF-043.**
  Verify against the queue before assigning — do not assign from a snapshot.
- **Collision to avoid:** the earlier AIPortal session proposed filing its RECNO64 residual
  as `AIF-041` — that id is the BETA-1 lane. Do not reuse 041.
- **Do not edit the gated system of record without the review gate:** the intake queue,
  `AI_FRIENDLY_DASHBOARD_V1.md`, `projects.yaml`, `CURRENT_TARGET.md`, and any
  `SESSION_CLOSEOUT_*` are promoted via propose→review→promote, never self-certified.
- **Do not commit / push / branch / promote** — those are the maintainer's actions only.

## 3. Reconciliation of the prior AIPortal session (`src/AIPortal/sessions/2026-07-21_…`)

That session cataloged 3 candidate lanes. Grounded against the live queue:
- **RECNO64 nav/index residual** → **fold under AIF-027**, not a new lane. Its drift flag is
  valid (AIF-027 M4-5 "done" is a *storage* sparse proof; *index/nav* addressing past 2³¹ is
  open). Also feeds AIF-041 M1/M2. Correct the AIF-027/dashboard wording accordingly. Its
  RECNO64 carriers are dev-confirmed; do not create a duplicate RECNO64 lane.
- **`SET INDEXTXN` transactional index maintenance** → possibly a genuine new lane, but it
  overlaps **AIF-023** (CDX/LMDB reconciliation) and **AIF-017** (WAL). If filed, it's
  **AIF-043**, cross-linked to 023/017. **Its source drafts are snapshot-based — re-ground
  against dev HEAD before any source proposal.**
- **Onboarding trigger** → overlaps **AIF-005** (assimilation portal) + **AIF-010** (front
  door, promoted). The one quick win: the small **`AI_README` Cowork-access insert**
  (permissions/extensions don't persist across chats).

Superseded (already flagged by that session): `AI_CHANGE_PACKAGE_NATIVE_INDEX_TXN_*` →
superseded by the `_LMDB_` version. Deletion is the maintainer's call.

## 4. Build / run queue (maintainer runs MSVC; agents don't build here)

- Reconfigure + build to pick up the `AIPortal` CMake exclusion and the
  `WAL_COMMIT_ROLLBACK` registry entry.
- `REGRESSION RUN WAL_COMMIT_ROLLBACK` → expect `W0`/`W1`/`W2` all `:.T.` (first proof of
  the new WAL regression).

## 5. Shared-tree hazard

Two sessions have written uncommitted changes into `D:\code\ccode`. Before a baseline
commit, separate "promotable engine work" from "AI session catalog" (the `src/AIPortal/`
collection) so git history stays clean. Capture `git -C D:\code\ccode rev-parse HEAD` as the
provenance anchor for any proposal.

## 6. Independent verification (read these, don't take my word)

- `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-041, AIF-042 rows)
- `docs/maintenance/BETA1_STABILIZATION_REGRESSION_LANE_V1.md`
- `docs/maintenance/SCRIPT_HEADER_CONTRACT_LANE_V1.md`
- `src/cli/cmd_regression.cpp` (`kRegressionSpecs`, 15 entries)
- `src/CMakeLists.txt` (`_EXCLUDE_DIRS` → `AIPortal`)
