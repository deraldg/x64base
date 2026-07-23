# First Promotion Checklist — new `PROMOTE.manifest` → `main`

Companion to `PROMOTION_PROCESS.md`. This is the ordered runbook for the FIRST
promotion after the manifest restructure, with the drift audit wired in as a
pass/fail gate. Existing scripts are referenced by their real names in
`tools/staging/`; the one NEW piece is `audit-drift.ps1`.

Most steps are report-only until an explicit `-Execute` / `--execute`. Read each
script's own help first — do not assume flags.

## 0. Pre-flight (one-time decisions for this promotion)

- [ ] **Confirm the broad source globs.** The new manifest publishes
      `src/**/*.cpp|hpp|h` and `include/**/*.hpp|h`. Confirm you intend ALL
      engine source public. If any subtree must stay private, narrow the glob
      before promoting.
- [ ] **Reconcile `BUILDING.md`.** Manifest promotes it at repo root; `main`
      carries it at `docs/getting-started/BUILDING.md`. Pick one location.
- [ ] **Commit the manifest + process docs on `development`** (done:
      `965b39650`) and `git push`.
- [ ] Place `audit-drift.ps1` in `tools/staging/` and commit it.

## 1. Preserve current staging state

- [ ] `python tools/staging/preserve_staging_worktree.py`  (Python 3.12)
      Binds branch/HEAD/status/hashes and backs up every dirty staging file
      with a byte-verified manifest. Writes nothing to `C:\x64base`.

## 2. Escrow the recoverable baseline

- [ ] `python tools/staging/create_public_baseline_escrow.py`
      Git bundle + tar snapshot + SHA-256 ledger + preserved dirty/ignored
      layers. Required before any destructive `-Fresh` rebuild.

## 3. Plan the overlay (report-only)

- [ ] `python tools/staging/plan_gate5_staging_overlay.py`
      Expands the manifest delta, compares blob identity to clean HEAD, and
      FAILS if the plan touches any preserved dirty path beyond the expected
      `PROMOTE.manifest` delta. Resolve any failure here before executing.

## 4. Rebuild staging (report, then execute)

- [ ] `pwsh tools/staging/rebuild-staging.ps1`            # report-only
- [ ] Review the expanded file set — especially the newly-added `src/**`,
      `include/**`, docs, and tooling globs. This is the moment a bad glob is
      caught cheaply.
- [ ] `pwsh tools/staging/rebuild-staging.ps1 -Execute`   # apply
      (or the bound executor: `python tools/staging/execute_gate5_staging_rebuild.py --execute`)

## 5. Purge junk & non-publish lanes from `main`

Run in the `C:\x64base` (main) clone. These were leaking into the public repo:

- [ ] `git rm -r --cached **/__pycache__`  and add `__pycache__/` + `*.pyc` to
      `.gitignore`   (58 files)
- [ ] `git rm -r --cached` the messaging/metadata lanes now in `main`  (41 files):
      `docs/maintenance/lanes/messaging`, `docs/maintenance/lanes/metadata`,
      `dottalkpp/data/messaging`, `dottalkpp/data/indexes/messaging`,
      `dottalkpp/data/scripts/messaging`, `dottalkpp/docs/messaging`

## 6. DRIFT GATE (pass/fail) — the verification step

- [ ] `pwsh tools/staging/audit-drift.ps1`
      PASS requires: **0 off-allow-list DIFF**, **0 `__pycache__`/`*.pyc`**,
      **0 non-publish-lane files**. Nonzero exit = do not push.
      - GONE files are reported, not fatal (staging-authored docs like
        `CHANGELOG.md`). Use `-StrictGone` only if you expect none.
      - `-ReportOnly` prints the report without failing (for a dry look).
- [ ] If it FAILS on off-allow-list DIFF: either add those paths to the
      manifest (see `PROMOTE.additions.manifest`) and re-run from step 4, or
      purge them from `main`.

## 7. Change-set gate + push

Run in the `C:\x64base` (main) clone:

- [ ] `python tools/staging/prepush_gate.py`   # inspects the staged change set
      (exit 0 clean · 2 hard-block · 3 warn-needs-ack). Use `--allow-data` only
      for a fixture change you deliberately named.
- [ ] `git commit` then `git push` to `main`.
- [ ] In `D:\code\ccode`: `git fetch --prune` (drop the old branch ref);
      in `C:\x64base`: `git fetch --prune`.

## 8. Post-promotion

- [ ] Re-run `pwsh tools/staging/audit-drift.ps1` — should be a clean PASS with
      off-allow-list DIFF trending to 0.
- [ ] Retire or rewrite `WORKFLOW_X64BASE.md` (superseded by
      `PROMOTION_PROCESS.md`).
- [ ] Consider `python tools/staging/prepush_gate.py --install-hook` so the
      change-set gate runs automatically on every commit.

## Gate summary

| Gate | Script | Scope | Fail = |
|---|---|---|---|
| Overlay plan | `plan_gate5_staging_overlay.py` | overlay vs clean HEAD | touches unexpected dirty path |
| **Drift** | **`audit-drift.ps1`** | **tree parity dev↔main + allow-list** | **off-list DIFF / junk / non-publish lane** |
| Change-set | `prepush_gate.py` | staged diff | build junk / binaries / unacked data |
