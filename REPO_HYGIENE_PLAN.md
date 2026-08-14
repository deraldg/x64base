# Repo Hygiene Plan

## Goal

Restore `D:\code\ccode` to a repo that can act as a source-of-truth workspace instead of a combined source tree, archive store, scratchpad, and export bucket.

This plan is intentionally conservative:

- no file deletion
- no file moves in this pass
- no history rewrites
- no assumptions that current WIP should be discarded

## What Is Going Wrong

The repo root is currently mixing several different classes of material:

- source and build configuration
- reusable scripts and tests
- generated build output
- logs and screenshots
- zip packages and export bundles
- backup drops and temporary intake folders
- scratch notes and one-off transcripts

That creates three concrete problems:

1. `git status` is too noisy to be trusted quickly.
2. Important code changes are buried under archives and local artifacts.
3. The repo root has become a generic workspace instead of a versioned project boundary.

## Repo Boundary

These items belong in the repo:

- `src/`, `include/`, `tests/`
- `cmake/`, `bindings/`, `third_party/` when intentionally versioned
- top-level build files such as `CMakeLists.txt`, `CMakePresets.json`, `vcpkg.json`
- stable project docs that are intentionally maintained
- reusable scripts and tools that are part of the development workflow

These items should not live in the repo root as ordinary working files:

- screenshots
- local logs
- zip bundles
- backup snapshots
- generated inventories
- imported package drops
- temporary MDO work directories
- copied archives of old repo states

## Proposed Taxonomy

Use the repo only for promotable project content.

Use a separate local staging area for operational clutter. A practical split is:

- GitHub/staging repo: only promotable source, docs, tests, and release-ready assets
- local archive area: zip bundles, screenshots, exports, old drops
- local scratch area: notes, transcripts, temporary probes
- local generated area: build trees, inventories, proof outputs

Suggested local directories outside the clean repo:

- `C:\dottalkpp-archive`
- `C:\dottalkpp-scratch`
- `C:\dottalkpp-generated`

If you prefer to keep them near the repo, they should still be clearly named and ignored.

## Immediate Rules Added

The updated `.gitignore` now suppresses obvious local-only noise:

- build trees and generated CMake files
- local virtual environment and editor settings
- `_drops/`, `_incoming/`, `.mdo_backups/`, backup/temp trees
- root-level zip archives and screenshots
- root-level generated inventory files
- accidental root litter such as flag-named files

This does not affect files already tracked by Git. It only reduces future untracked noise.

## Safe Relocation Plan

Move by category, not one file at a time.

### 1. Root-level archives and captures

Move these out of the repo root first:

- `*.zip`
- `Screenshot *.jpg`
- exported package manifests that are not part of source
- one-off generated text inventories such as `flattened_sources.txt`

Destination:

- archive or generated area outside the repo

### 2. Intake and backup trees

Move these next:

- `_drops/`
- `_incoming/`
- `.mdo_backups/`
- `backups/`
- `memo_backup/`
- `TMP/`

Destination:

- archive area for historical snapshots
- scratch area for active intake

### 3. Root notes and transient transcripts

Review and move or consolidate:

- ad hoc `.txt` notes
- temporary markdown summaries
- one-off command captures

Destination:

- `notes/` if intentionally versioned
- otherwise scratch area outside the repo

### 4. Generated build output

Keep these out of version control entirely:

- `build*/`
- `dist/`
- `bin/`
- `CMakeCache.txt`
- `build.ninja`

## Operating Model Going Forward

Before starting a new exploratory task:

1. Decide whether the output is source, documentation, or scratch.
2. Put scratch outputs in a non-repo staging area immediately.
3. Only promote material into the repo after it becomes reusable or authoritative.

Before staging changes for GitHub:

1. Run `git status --short`.
2. Confirm the diff is mostly source, tests, build config, or intentional docs.
3. If archives, screenshots, or backups appear, move them before staging.

## Recommended Next Cleanup Pass

The next practical pass should be operational, not conceptual:

1. inventory root-level files into `keep`, `move`, and `review`
2. identify root directories that should be promoted, relocated, or split
3. prepare a GitHub-facing subset for the cleaner staging repo at `C:\dottalkpp`

That pass can be done safely without deleting anything by generating a relocation checklist first.
