# Edition System Publication Plan (Path A) v1

Status: **plan — not yet executed**.
Written: 2026-07-14.
Updated: 2026-07-15.
Owning lifecycle: DotTalk++ SDLC (build + publication).

## Current State

Two separate publication states must not be confused:

1. **Path B / public `pro-md` stranger journey is complete.**
   - `BUILDING.md` describes presets that actually exist on public `main`.
   - A fresh clone was proved through configure, build, runtime staging, MCC
     databuild, LMDB generation, and ordered query.
   - Location-honesty and runtime-staging fixes were published in
     `46e021594bee25fd40fe9b79e318c691e1a714a0`.
   - The printed DotScript annotation was corrected in
     `b9d480215c036178ba99b5109a8a2489ee89b215`.

2. **Path A / edition-system source publication is still open.**
   - Products `LEAN`, `PROFESSIONAL`, `EDUCATIONAL`, and `DEVELOPMENT` exist and
     have proof in the authoritative development tree.
   - Index modes `NONE`, `LEGACY`, and `LMDB` exist and have development proof.
   - The coherent edition changeset and dedicated `windows-*` presets are not
     yet on public `main`.
   - Public `BUILDING.md` therefore correctly tells a fresh clone to use the
     older public presets such as `pro-md`, `windows-core`, `index-vcpkg`, and
     `wsl`.

This plan publishes the edition system itself. The already-published cold-clone
fixes are prerequisites and proof method, not remaining Path A work.

## Why This Plan Exists

The edition system spans build configuration, source guards, target composition,
package manifests, and tests. It cannot be safely published by copying selected
files from a mixed development working tree.

The public repository must receive one coherent, reviewable changeset that:

- defines `DOTTALK_PRODUCT` and `DOTTALK_INDEX_MODE`;
- includes every source guard and provider boundary those options require;
- includes the matching tests and package allow-lists;
- builds from a fresh clone without relying on unpublished local files;
- survives the full stranger journey, not merely compilation.

## Authority and Publication Route

```text
D:\code\ccode
  authoritative development source and proof
        |
        | coherent reviewed Git changeset
        v
review branch based on public main
        |
        | cold-clone certification
        v
main
```

`PROMOTE.manifest` is not the engine-source transport. It carries the curated
public data/documentation projection. Engine source and build configuration must
travel through a coherent Git changeset.

## Required Changeset

Identify the exact edition-work commit range in authoritative development. The
changeset is expected to include, as one consistent unit:

- `CMakePresets.json` edition/index presets;
- root and subsystem `CMakeLists.txt` composition logic;
- `DOTTALK_PRODUCT`, `DOTTALK_INDEX_MODE`, and `DOTTALK_HAS_XINDEX` definitions;
- xbase/xindex provider separation and every related source guard;
- product command/source allow-lists;
- package manifests and leak-detection tests;
- profile, binding, provider, and runtime smoke tests;
- only the documentation required to explain the source being published.

Do not reconstruct this list by memory or hand-pick files from a dirty tree.
Diff the committed development edition work against current public `main` and
review the resulting dependency-complete set.

## Procedure

1. **Identify the development changeset.**
   - Locate the committed edition-separation range.
   - Confirm local development proof for at least `NONE`, `LEGACY`, and `LMDB`.
   - Record the exact base and head commits.

2. **Create a review branch from current public `main`.**
   - Do not implement original engine changes directly in disposable staging.
   - Do not rewrite public history.

3. **Apply only the coherent edition changeset.**
   - Exclude unrelated development churn.
   - Reconcile conflicts against current `main` rather than silently taking one
     side.

4. **Reconcile the vcpkg environment-variable split.**
   - Presets currently reference both `VCPKG_ROOT` and
     `VCPKG_INSTALLATION_ROOT`.
   - Standardize on one variable or deliberately support and document both.

5. **Cold-clone certify the review branch.**
   The maintainer operates the long build. At minimum prove representative table,
   legacy-index, LMDB, and product profiles, including bindings where selected.

6. **Run the full journey from the same clone.**
   - build the selected runtime;
   - stage the executable and runtime DLLs using the published launcher;
   - run the MCC databuild;
   - generate required LMDB environments;
   - query `STUDENTS` in logical order and assert expected source paths and data.

7. **Review public documentation against the certified clone.**
   - Update `BUILDING.md` only after the presets exist and pass.
   - Update AI Portal/dashboard language from "development-only" to public only
     when the merge has actually occurred.
   - Regenerate dependent manual sections through manualgen rather than editing a
     combined output by hand.

8. **Merge and record the result.**
   - Merge only after the cold-clone gate passes.
   - Leave a dated closeout with exact commands, commits, artifacts, transcripts,
     and residual risks.

## Definition of Done

Path A is complete only when all of the following are true:

- public `main` contains the coherent product × index-mode implementation;
- documented edition presets exist in the public `CMakePresets.json`;
- representative edition/index combinations configure, build, and pass tests
  from a fresh clone;
- the same clone completes runtime staging, databuild, LMDB generation, and an
  ordered query;
- package allow-lists fail closed and do not leak excluded components;
- public docs describe only the options actually present and certified;
- development, review branch, staging, public commit, and website states are
  reported separately;
- the vcpkg variable policy is consistent and documented.

## Not Done Here

This document does not publish the edition source, authorize a branch merge, or
claim the development proof is public proof. The edition-system implementation
remains development-proven and publication-pending until the procedure above is
completed.
