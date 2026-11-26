# Shared-tree cleanup plan, 2026-11-26

    author   : member.ai.claude (project thread "onboarding fixes")
    status   : PROPOSAL for member.derald. Owner said yes 2026-11-26 15:42Z.
               Applied: 3a-3c gitignore entries (untracked 7,353 -> 4,813).
               NOT applied: the 3a "commit build scripts" half (lane-owned);
               3d deletes (the help.bak-* dirs wait for AIF-171 Phase 8 to
               close; `_to_delete/aif170_superseded/` was verified as the
               charter AIF-175 replaces, but the agent was not permitted to
               delete it, so the owner removes it by hand).
    measured : D:\code\ccode, Windows host, `git --no-optional-locks status --porcelain -uall`
               at 798c4c1e3, 2026-11-26 ~15:10Z

## 1. Starting point and what is already done

At session start the tree had 241 modified and 7,570 untracked paths. Done today,
all reversible, nothing deleted:

- Six scoped commits on `development` (b2d9d5948 .. 798c4c1e3): the xbbs skill
  slice, the Tier 1 Codex co-author rule, AIF-175 (the renumbered search-limiter
  charter), refreshed identifier status and truth audit, the AIF-174 follow-up
  record, and seven `.gitignore` entries (217 paths: `help.bak-*`,
  `generated/backups`, datadict promotion backups, `terminals/`, staged `bin-wsl*`).
- Now: **234 modified, 7,353 untracked.**

## 2. Buckets (untracked count, size, date range)

| # | Bucket | Untracked | Modified | Size | Dates | Proposed |
| --- | --- | ---: | ---: | ---: | --- | --- |
| B | runtime data under `dottalkpp/data/` (dbf, systems/cascade_erp, scripts, datadict, indexes) | ~1,390 | 14 | ~340 MB | 2025-08 .. today | split: commit build scripts, gitignore products (3a) |
| C | `dottalkpp/docs/generated/` (proposals, reports, packages, patches) | ~860 | 0 | 20 MB | 2026-05 .. 07 | gitignore or archive (3b) |
| D | `docs/maintenance/lanes/full_stack_documentation/runs/` | 869 | 0 | 436 MB | 2026-05 .. 10 | gitignore, too large to commit (3b) |
| E | `docs/manuals/developer/manualgen/` packets + 169 modified published pages | 437 | 169 | 2 MB | 2026-05 .. 10 | HELP/manual lane decides (4) |
| F | `docs/datadict/` packages, contracts, review queue | 1,913 | 1 | 24 MB | 2026-05 .. 10 | DDICT lane decides; likely commit contracts, archive packages |
| G | `docs/messaging/`, `docs/locale/` | 556 | 0 | 3 MB | 2026-05 .. 06 | archive or commit as one historical slice |
| H | `docs/maintenance/` lane docs (56 top-level, incl. 17 AIF-171 Phase 8 closeouts) | 264 | 4 | 16 MB | 2026-05 .. 11-25 | commit per lane (4) |
| J | `dottalkpp/docs/Bible/` KJV dataset | ~30 | 0 | ~380 MB | | gitignore; >100 MB file cannot go to GitHub (3c) |
| K | `labtalk/registries/runs.d` (18), `proofs.d` (3), `proofs/runs` (18) | 43 | 14 | 2 MB | 2026-08 .. 11 | commit with their lanes (4) |
| L | `tools/`, `src/`, root scripts (`scripts/`, `smoke/`, `tools/vfp`) | ~340 | 24 | 24 MB | 2025-08 .. 11-21 | review; most look like dead ad-hoc scripts |

## 3. Needs a yes from Derald

a. **Runtime data (B).** Per the staging rule (dottalkpp/ is runtime+testing, each
   database ships build scripts), propose: commit the `.dts`/`.ps1` build scripts,
   gitignore `/dottalkpp/data/systems/`, `/dottalkpp/data/dbf/cascade_*/`,
   `/dottalkpp/data/dbf/sandbox/` and their indexes. Ignore deletes nothing.
b. **Generated outputs (C, D).** Gitignore `/dottalkpp/docs/generated/` and
   `/docs/maintenance/lanes/full_stack_documentation/runs/`. Optional: move them
   to a sidecar outside the repo first, with an undo manifest.
c. **Bible dataset (J).** Gitignore `/dottalkpp/docs/Bible/` except
   `assemble_bible_zip.ps1`, or keep it out of the repo entirely.
d. **Deletes, only if you say so:** `_to_delete/aif170_superseded/` (3 files,
   superseded by AIF-175 today); the three `dottalkpp/data/help.bak-AIF171-*`
   dirs (131 MB, now ignored) once AIF-171 Phase 8 is closed.

## 4. Lane-owned work that should be committed by (or for) its owner

- **HELP / manual regeneration (E + 9 `dottalkpp/data/help/*.dbf`, manualgen_lib,
  fullstack_docs tools and tests).** One uncommitted regeneration, Oct 13-15,
  AIF-171 Phase 8 by its run fragments. It is also the "governed HELP refresh"
  AIF-174 is waiting on. Land or revert it as one slice before anyone refreshes HELP.
- **AIF-171 Phase 8 closeouts** (17 top-level `SESSION_CLOSEOUT_AIF171_*`) and
  their 12 `CODEX-202610*` run fragments: one scoped commit, Codex co-author trailer.
- **DDICT engine edits:** `src/datadict/ddict_catalog_view.cpp`,
  `ddict_object_resolver.cpp`, two tests, `tools/datadict/tests/test_ddict_feed.py`,
  `current_ddict_feed.json`, `DDICT_FEED_CONTRACT_V1.md`. Needs a build + ctest
  before commit.
- **Portal tooling:** `labtalk/ai_portal/README.md`, `validate_portal_identifiers.py`
  (+ untracked test), `labtalk/portal/tests/test_headless_audit.py`,
  `publication/ai-portal.mdx`, `portal_feeds.yaml`, `portal_assertions.yaml`, then
  re-commit `portal_feed_status_latest.*` (refreshed locally, deliberately not
  committed: its inputs are these uncommitted registries).
- **Prior thread's brief:** `docs/agents/ONBOARDING_REPORT_REVIEW_2026-11-25_CODEX.md`.
- **Board and registers** (`PSEUDO_CHAT_BOARD.md`, `R_RULING_REGISTER_V1.md`,
  `OPEN_ITEMS.md`, dashboard): maintainer transcription.

## 5. Suggested order

1. Push the 13 local `development` commits (needs your go-ahead).
2. 3a-3c gitignore entries: about 3,100 paths leave the untracked list, no deletes.
3. HELP/manual slice, then the AIF-171 closeouts, then DDICT, then portal tooling.
4. What is left (G, L, F packages) gets a per-directory keep/archive pass.
