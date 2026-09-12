# DotTalk++ Promotion Process — `development` → `main`

_Status: formalized process. Supersedes the older `WORKFLOW_X64BASE.md`, which
describes a now-retired intermediate tree (`D:\code\ccode\x64base`) and an
outdated "C:\x64base is a mirror only" role. Reconcile or delete that file._

> **Non-negotiable:** the arrow in this title describes reviewed promotion, not
> a Git branch merge or refspec. Never push `development:main` and never merge
> the `development` branch into `main`. Original work stays in
> `D:\code\ccode`; only sterilized staging rooted at `C:\x64base` may update
> GitHub `main`.

## 1. Purpose

Define exactly how work moves from active development into the public GitHub
repository, so that:

- `main` is **canonical for downloads and pull requests**, and stays clean and
  reviewable.
- The publishable set is **explicit and auditable**, never a blanket copy.
- Drift between development and the public repo is **detectable and bounded**.

## 2. Repositories, branches, roles

| Location | Clone / branch | Role |
|---|---|---|
| `D:\code\ccode` | tracks `development` | Source of truth. All new code, fixes, data work, and docs happen here first. Formerly the `homegrown-cnx-20251112-branch`; renamed to `development` to make its role explicit and separate it from the public line. |
| `C:\x64base` | tracks `main` | Publication staging. The clone that commits and pushes to `main`. **Canonical for downloads and PRs.** Rebuildable from the verified baseline + overlay, never hand-authored as a second dev tree. |
| `github.com/deraldg/x64base` | `main` (default) | Public snapshot. `origin/HEAD → main`. |

**Authority chain (single, canonical):**

```
D:\code\ccode  (development)  --allow-list overlay-->  C:\x64base  (main)  --push-->  github/main
```

There is no intermediate curated tree. `development` is the only authoring
surface; `main` is the only public surface.

**Amended 2026-09-12: engine source uses the chain above, like everything else.**
The carve-out that used to sit here -- a promotion branch created from `main`,
carrying only a reviewed source slice -- contradicted the sentence directly above
it, and had not run since 2026-08-09. The overlay copies FILES, not history, so
it satisfies "must not inherit the development branch" by construction.
See `PROMOTE.manifest` header and `PROMOTION_MODEL_SEED_V1.md`.

## 3. What publishes: the two lanes

`main` is a **model / reference repo** — it serves both investigators (who
download and run) and contributors / AI agents (who read and extend). Every
promoted file belongs to exactly one **publish lane**. ("Publish lane" is the
audience axis for what leaves development; it is distinct from MDO content lanes
such as `messaging` or `metadata`.)

- **PRODUCT publish lane.** Needed to *use* the release: engine source and
  headers, runtime scaffold, help, sample data + the schemas needed to read it,
  databuild and smoke scripts, and rendered manuals.
- **MODEL/DEV publish lane.** Published because this is a model repo:
  documentation *engines* (generators), AI-/agent-facing docs, contracts, portal
  seeds, build rationale, and repo tooling. The principle: **publish the rendered
  output; keep the generator in the MODEL/DEV lane.**

Schemas are split, not one bucket: data/workspace schemas travel with the sample
data (PRODUCT); engine-internal schemas (manualgen JSON, `src/schemas/*.json`)
describe the tooling (MODEL/DEV).

## 4. The allow-list (`PROMOTE.manifest`)

Promotion is governed by `PROMOTE.manifest`, an **allow-list** (not an
ignore-list): of the clean files in development, these publish. It is the
counterpart to `.gitignore` (deny; universal) and they do not overlap.

Rules:

1. **Allow-list only.** A file publishes only if a manifest glob matches it.
   Broad blanket copies are prohibited.
2. **Lane-tagged.** Every entry lives under its PRODUCT or MODEL/DEV publish-lane section.
3. **`git ls-files` is the guard.** A manifest glob may only publish a file git
   TRACKS. **This rule previously read "`.gitignore` is a hard guard -- the
   rebuild re-applies the deny-list after matching". That was never true.** The
   rebuild never opened `.gitignore`; it applied a hand-transcribed 13-alternative
   regex against that file's 185 rules, and measured 2026-09-12 it was letting
   545 untracked files reach `main`, including three zero-byte launcher stubs.
   `651ce911a` replaced it with the tracked-set intersection: git already answers
   exactly the question both lists were approximating. Every dropped path is
   printed with the entry that claimed it.
4. **Non-publish lanes stay out.** `messaging`, `metadata` and `sandbox` are
   deliberately not published. They must never appear in the allow-list, and
   must not linger in `main`. **Versioning them in development is a SEPARATE
   requirement, and as of 2026-09-09 it is largely UNMET** -- see section 7.
   Do not read the exclusion as evidence that development is holding them.

## 5. Promotion procedure

Run from `D:\code\ccode` unless noted.

1. **Land changes on `development`.** Commit real work to the `development`
   branch. Never author directly in `C:\x64base`. Pushing `development` updates
   the integration branch only; it does not publish to `main`.
2. **Rebuild staging.** `tools/staging/rebuild-staging.ps1` clones `github/main`
   into `C:\x64base` (baseline), preserves the committed baseline + dirty layer
   in verified escrow, then overlays every `PROMOTE.manifest` match from
   development, applying `.gitignore` as a guard.
3. **Build + smoke in staging. GATING -- do not push on a tree that did not
   build.** Build `C:\x64base` and run the release-style smoke/proof if
   path-sensitive runtime behavior matters. Since 2026-09-12 the overlay carries
   engine source, so this build IS the cold-clone certification that used to
   justify a separate source lane. It is the step that gets forgotten -- it was
   forgotten on the 2026-09-12 promotion itself and caught only by the owner
   afterwards -- which is precisely why it is now gating rather than advisory.
3a. **Run the suite in staging. GATING.** `./datarun` then `REGRESSION ALL` in
   `C:\x64base`. A CLEAN BUILD PROVES NOTHING ABOUT THE PUBLISHED DATA, and on
   2026-09-12 that gap was measured: staging built the 1.1 engine and then four
   specs reported "script not found", INDEX_X64 ran against a fixture that is
   deliberately never published and reported no failure at all, and three
   MWXSHAKE markers went red for an LMDB env that `.gitignore` rules out and
   nothing regenerates. The build was green through all of it.
3b. **Closure check. GATING.** Of the .dts files `cmd_regression.cpp`
   registers, every one must exist in staging:

       git grep -h -o -E '"[A-Za-z0-9_\\/.-]+\.dts"' -- src/cli/cmd_regression.cpp |
         ForEach-Object { $_.Trim('"') -replace '\\','/' } | Sort-Object -Unique |
         ForEach-Object {
           $p = "dottalkpp/data/scripts/$_"
           if (-not (Test-Path "C:\x64base\$p")) { "MISSING on main: $p" }
         }

   This must print nothing. It is here because the manifest is an ALLOW-LIST
   WITH NO REACHABILITY CHECK: it was built by listing what to publish rather
   than by asking what the published tree needs in order to run. Every gap found
   on 2026-09-12 -- nine script subdirectories, five workspace postures,
   tools/notify/smtp_probe.py, data/projects, four CMake build inputs -- is that
   one defect wearing different filenames, and each was found by tripping over
   it rather than by reading. The check above is the narrow case, scoped to one
   consumer. THE GENERAL CASE IS STILL OWED: a sweep that walks the published
   tree's own references and flags anything unreachable would have caught all of
   them at once, and wants an AIF number of its own.
3c. **Regenerate the derived indexes.** LMDB is gitignored (53 GB measured
   2026-07-14) and `.gitignore` says to regenerate it locally -- a required
   post-publish step that existed only as a comment until 2026-09-12, when
   MWXSHAKE's order arms went red on main for its absence. Run
   `dottalkpp/data/scripts/mcc/mcc_build_x64_lmdb.dts` in staging.
4. **Drift audit (Section 6).** Confirm the only differences between development
   and `main` are intended promotions.
5. **Commit + push from `C:\x64base`** to `main`.
6. **Open PRs against `main`** — it is the canonical PR target.

## 6. Drift audit (verification)

Before each push, verify staging matches intent. **Run
`pwsh tools/staging/audit-drift.ps1`** -- it is the pass/fail gate for this
section and it exists. Measured 2026-09-12: it had not been in the promotion
anyone actually ran, and its first run in a while returned FAIL with 915
off-projection files. Compare by **content hash, not date** (copies/clones
rewrite timestamps):

- Compare files present in both trees; classify each as identical, DIFF
  (content differs), or GONE (in staging, no dev counterpart).
- Cross-reference every DIFF against `PROMOTE.manifest`:
  - **DIFF ∧ on allow-list** → promotion will refresh; expected.
  - **DIFF ∧ off allow-list** → a gap: either add it to the manifest or purge it
    from `main`. Should trend to zero.
  - **GONE** → staging-authored files with no dev source (e.g. `CHANGELOG.md`,
    `CONTRIBUTING.md`, `SECURITY.md`, governance docs). Keep them in the manifest
    preserve set or pull them back into development so they are not orphaned.

Target state: after a promotion run, off-allow-list DIFF = 0 and no
`__pycache__` / non-publish-lane files remain in `main`.

## 7. Non-publish lanes & junk

- **Bytecode / build junk:** `__pycache__/`, `*.pyc` — gitignore and
  `git rm -r --cached` from `main`.
- **`messaging` / `metadata` / `sandbox`:** never published. If present in
  `main`, remove them. **These lanes are SUPPOSED to be versioned in
  development and largely are not.** Measured 2026-09-09: `docs/messaging` is
  419 files with **0 tracked**; `dottalkpp/data/messaging` is 4 files with 1
  tracked (`gui_messages.csv`), the other three being two `.dbf` tables and a
  `.dtx` memo sidecar. Until 2026-09-09 this line and rule 4 in section 4 both
  said "versioned in development" AS A STATEMENT OF FACT. It was false, and the
  exclusion from `PROMOTE.manifest` was resting on it: these lanes are kept out
  of publication on the understanding that development holds them, and for
  `docs/messaging` development holds nothing. The rule being served is the
  durability rule -- "if development has no history, those lanes are gone"
  (`PROMOTION_MODEL_SEED_V1.md`) -- so for that lane the loss this rule exists
  to prevent is not a risk, it is the present state. The work is tracked as
  OI-036; the correction is R141.

## 8. Cadence & responsibilities

- Promote on a defined cadence (e.g. end of each development phase or before any
  tagged release), not ad hoc.
- No change is hand-edited in both `development` and `main`. Fix in
  `development`, then re-promote.
- After each remote change to branch names or structure, update this document
  and the `PROMOTE.manifest` header in the same commit.

## 9. Open items to reconcile

1. ~~**Retire `WORKFLOW_X64BASE.md`** or rewrite it to match this document (it
   still references the removed intermediate tree and the old branch name).~~
   **RULED 2026-08-07 (AIF-092 R4): RETIRE, do not rewrite.** It is not in
   `PROMOTE.manifest`, has no `development` source, and this document already
   supersedes it. `CONTRIBUTING.md` now carries the repository-roles table it
   partly served, and unlike this document `CONTRIBUTING.md` IS allow-listed, so
   the current statement reaches `main`. Removal happens in the
   rebuild-review-commit window. Reasoning:
   `docs/maintenance/PUBLICATION_SURFACE_RECOVERY_PDLC_LANE_V1.md` section 6c.
2. **Path mismatch:** `PROMOTE.manifest` promotes `BUILDING.md` at repo root,
   but `main` carries it at `docs/getting-started/BUILDING.md`. Pick one.
3. ~~**Expand the allow-list** using `PROMOTE.additions.manifest` so engine source
   and active docs are owned by promotion rather than frozen in the baseline.~~
   **DONE 2026-09-12 for the engine-source half**, and not via a second manifest
   file: the globs went into `PROMOTE.manifest` directly, because a second
   allow-list is a second thing wearing one name. "Frozen in the baseline" was
   measured exactly right -- frozen at 2026-08-09, 71 files behind.
   **The active-docs half is NOT done and mostly should not be**: the manifest's
   own NOT PUBLISHED section already rules those paths out deliberately, so the
   915 off-projection files are an unexecuted purge, not a pending addition.
   See `claude/TRIAGE_THE_915_OFF_PROJECTION_FILES_ON_MAIN.md`.
4. **Purge** the `__pycache__` (58) and `messaging`/`metadata` (41) files now in
   `main`.
