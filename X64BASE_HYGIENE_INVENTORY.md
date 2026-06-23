# X64BASE Hygiene Inventory

## Purpose

This inventory classifies the current `x64base` worktree into:

- `keep`: likely promotable project content
- `move`: likely local scratch or runtime exhaust
- `review`: needs an explicit policy decision before staging to GitHub

This is a staging-oriented audit only.

No files were moved or deleted in this pass.

Update:

An aggressive local staging cleanup has now been applied to this copy.

Removed in this pass:

- `build/`
- `dottalkpp/user/`
- loose scratch `.txt` files under `src/cli/`
- loose scratch notes and helper files in `bindings/`
- loose untracked scratch notes under `src/help/`

## Current Shape

`x64base` is substantially closer to a model repo than the broader `ccode` workspace:

- compact top-level layout
- presentable README material
- coherent `src/`, `include/`, `bindings/`, `tests/`, `tools/`, `dottalkpp/`

But the worktree is still not clean:

- active source modifications across CLI, help, workspace, memo, import, and xBase areas
- many tracked deletions under `dottalkpp/data`
- scratch text files mixed into source and bindings
- generated/runtime state policy is still unclear

## Keep

These areas look like core repo content and should remain first-class staging candidates:

- `src/`
- `include/`
- `bindings/pydottalk/`
- `tests/`
- `tools/`
- `.github/`
- top-level CMake files
- `README.md`
- `README_NEW.md`
- `vcpkg.json`

These are the most likely GitHub-facing source-of-truth areas.

## Move

These items look like local scratch, notes, or accidental drop-ins and should not stay in the repo long-term:

### Source-area scratch

- `src/cli/Here’s the inventory I can defend f.txt`
- `src/cli/New Text Document.txt`
- `src/cli/SEARCH AND PREDICATE CANARY V1 START.txt`
- `src/cli/estimate one way uhaul 1 room of fu.txt`
- `src/cli/metadata.ds1.txt`
- `src/$envVCPKG_ROOT = CUsersderalvcpkg.txt`

### Binding-area scratch

- `bindings/# From the folder where you saved t.txt`
- `bindings/& $py12 -c import pydottalk; from p.txt`
- `bindings/autdbf_shakedown.txt`
- `bindings/autodbf.txt`
- `bindings/building the help files.txt`
- `bindings/doc for something.txt`
- `bindings/pydottalk.txt`
- `bindings/pydottalk_smoke.py.first.txt`
- `bindings/pydottalk_smoke.py.improved.txt`
- `bindings/release checklist.txt`

These are not source assets. They should move to a scratch or archive area before GitHub staging.

Most of these items have now been removed from this copy.

## Review

These areas need a conscious policy decision. They may be valid fixtures, or they may be runtime/local data that should not remain tracked.

### `dottalkpp/data/dbf`

This appears to contain sample DBFs, memo fixtures, sandbox state, and save copies.

Questions:

- Which files are canonical fixtures?
- Which files are generated sandbox copies?
- Which duplicates exist only for runtime testing?

Likely split:

- keep canonical fixtures
- move or ignore local sandbox/save copies

### `dottalkpp/data/scripts`

This appears to contain useful smoke tests, canaries, and suites.

Questions:

- Are these part of the public/project test surface?
- Or are some historical/operator-only scripts better relocated to `tests/` or an archive area?

Likely split:

- keep real regression and smoke suites
- archive obsolete or duplicate scripts

Terminology note:

- `.dts` is DotScript, the text-based line-interpreter script format for
  DotTalk++.
- `.dts` files are intentional runtime/test/control artifacts, not ordinary
  scratch text.

### `dottalkpp/data/workspaces`

This looks like mixed workspace fixtures and runtime session state.

Questions:

- Which workspaces are canonical examples?
- Which are user/session-generated?

Likely split:

- keep curated example workspaces
- stop tracking session/local workspaces

Terminology note:

- `.dtschema` / `.dtschemas` are workspace files
- `.erz` files are Ersatz browser artifacts

### `dottalkpp/data/help/*.dbf` and `*.dbt`

These are currently modified and may be generated/help-catalog outputs.

Questions:

- Are these source artifacts, generated artifacts, or checked-in seed catalogs?
- If generated, what is the build/regeneration path?

### `dottalkpp/user/`

This directory reads as runtime-local state and should generally not be a GitHub staging surface.

The updated `.gitignore` now treats it as local runtime state.

## Immediate Interpretation

The most important current distinction is:

- source edits are happening in legitimate project areas
- the noisiest tracked churn is concentrated under `dottalkpp/data`
- the most obvious cleanup wins are the scratch files in `src/cli` and `bindings`

That means `x64base` is usable as the cleanup target, but not yet a publishable staging baseline.

After the aggressive pass, the remaining serious staging problem is no longer root clutter.

It is tracked content policy inside `dottalkpp/data`.

## Recommended Next Pass

1. classify `dottalkpp/data` into canonical fixtures vs runtime/generated state
2. identify which tracked deletions are intentional cleanup versus accidental loss
3. relocate the `move` list into a local scratch/archive area
4. prepare a reduced GitHub-facing tree from this cleaner baseline

## Suggested Staging Principle

For GitHub, prefer this boundary:

- code
- build config
- tests
- canonical docs
- curated fixtures

Avoid carrying:

- runtime session state
- scratch notes
- duplicate sandbox data
- generated local help/state outputs unless intentionally versioned

## Current Git Triage

After the aggressive cleanup pass, the remaining `git status` in `x64base`
falls into a few distinct buckets.

### Safe cleanup already in motion

These tracked deletions look consistent with staging hygiene and should remain
in the cleanup lane unless a specific fixture is later restored:

- `bindings/*.txt` scratch and smoke notes
- `src/$envVCPKG_ROOT = CUsersderalvcpkg.txt`
- `src/cli/xbase_xindex_pydottalk.txt`
- `dottalkpp/user/default/workspaces/*`
- `dottalkpp/data/dbf/sandbox/*`
- `dottalkpp/data/dbf/x64/save/*`

Current tracked-deletion counts in these safer buckets:

- `dottalkpp/data/dbf/sandbox/*` -> 37
- `dottalkpp/data/dbf/x64/save/*` -> 28
- `dottalkpp/user/default/workspaces/*` -> 12

These read as local runtime state, sandbox copies, save snapshots, or staging
notes rather than promotable repo assets.

### Review before staging

These tracked deletions are plausible cleanup, but they touch areas that may
contain canonical fixtures or curated test assets:

- `dottalkpp/data/dbf/x32/*`
- `dottalkpp/data/dbf/x64/*`
- `dottalkpp/data/scripts/**`
- `dottalkpp/data/workspaces/*`

Current tracked-deletion counts in these review buckets:

- `dottalkpp/data/dbf/x32/*` -> 5
- `dottalkpp/data/dbf/x64/*` -> 58
- `dottalkpp/data/scripts/**` -> 80
- `dottalkpp/data/workspaces/*` -> 17

These need policy decisions before staging:

- which DBFs are canonical sample fixtures
- which scripts are still part of the public regression surface
- which workspace files are curated examples versus user/session state

### Real code changes

The modified and untracked source areas are not dominated by scratch now.
They appear to represent active feature work:

- `src/cli/*`
- `src/help/*`
- `src/manual/*`
- `src/datadict/*`
- `include/*`

Notable untracked source additions now look intentional, for example:

- `src/cli/cmd_bbox.cpp`
- `src/cli/cmd_ddict.cpp`
- `src/cli/cmd_maint.cpp`
- `src/cli/cmd_manual.cpp`
- `src/cli/cmd_msgmgr.cpp`
- `src/cli/cmd_quit.cpp`
- `src/manual/*`
- `src/datadict/*`

This means the next staging problem is not source clutter. It is deciding what
`dottalkpp/data` should look like in a GitHub-facing repo.

### Documentation promotion

A visual teaching artifact was found under the data lane and promoted toward a
better home:

- moved from `dottalkpp/data/dbf/LabTalk_DotTalkpp_Systems_Storyboard_Deck.pptx`
- to `docs/LabTalk_DotTalkpp_Systems_Storyboard_Deck.pptx`

A markdown companion was also extracted:

- `docs/LabTalk_DotTalkpp_Systems_Storyboard_Deck_NOTES.md`

Interpretation:

- this is intentional documentation/manual/classroom material
- it should be treated as docs, not as DBF fixture content

### Immediate staging interpretation

If staging began today, the safest split would be:

- keep source, include, build config, and deliberate new subsystem code
- keep deletions of obvious scratch/runtime files
- hold all `dottalkpp/data/dbf/x32`, `dottalkpp/data/dbf/x64`,
  `dottalkpp/data/scripts`, and `dottalkpp/data/workspaces` changes in review
  until fixture policy is explicit
