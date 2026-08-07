# CCODE Top-Level Triage

Date: 2026-07-07
Scope: `D:\code\ccode`
Intent: classify non-core top-level directories as `keep`, `move`, `review`, or `trash`.

## Policy

`D:\code\ccode` is the dev/runtime tree, not the staging/publish tree.

This triage is therefore about:

- keeping active engine/runtime lanes in place
- moving side projects and historical copies out of the core dev tree
- identifying scratch, backup, and accidental junk for deletion
- leaving build outputs alone unless a separate disk cleanup pass is requested

## Keep

These belong in the active dev/runtime tree.

- `bindings`
- `cases`
- `cmake`
- `contracts`
- `docs`
- `dottalk-webui`
- `dottalkpp`
- `include`
- `labtalk`
- `mcc`
- `pycrud`
- `rules`
- `scripts`
- `selfdoc`
- `src`
- `tests`
- `tools`
- `user`

Notes:

- `dottalk-webui` is currently tiny and looks like a live project lane, not dead cargo.
- `mcc` is part of the sample/instructional database lane and should remain close to runtime work.

## Move

These should be moved out of `D:\code\ccode` into a broader holding area under `D:\code\...` when convenient.

- `Bible`
  - Large payload lane, about 656.74 MB.
  - Contains assembled Bible artifacts and split ZIP parts, not core engine source.
- `designs`
  - Diagram/design artifacts, about 89.93 MB.
- `drawio-libs-review`
  - Reference/design library review material, about 89.92 MB.
- `FoxApp`
  - Historical/parallel app lane with its own build tree, about 59.87 MB.
- `tv_test`
  - Experimental TurboVision lane with build output, about 59.72 MB.
- `palette`
  - Standalone experimental palette lane with build artifacts, about 58.37 MB.
- `python_misc`
  - Mixed helper and experiment lane with build output, about 24.73 MB.
- `_drops`
  - Local drop area, about 18.04 MB, not appropriate in the core repo root.
- `apps`
  - Package/drop bundles and zip artifacts.
- `books`
  - Notes/reference material, not source.
- `datadict_repo_dropin_dd023_v0`
  - Historical package/drop-in lane.
- `dbf_memo_cloner`
  - Small utility lane; could live under `D:\code\tools` or another utilities area outside `ccode`.
- `draw.io`
  - Ad hoc draw.io files, not a source lane.
- `fox`
  - Tiny historical experiment lane.
- `FoxAppShell_mtv`
  - Tiny historical experiment lane.
- `foxcli`
  - Historical experiment lane with object file present.
- `memo_sidecar_v1`
  - Legacy/side design lane.
- `ncurses`
  - Small side experiment lane.
- `patches`
  - Ad hoc patch scratch area, not canonical source.
- `payload`
  - Packaging/support lane, not core runtime source.
- `py`
  - Misc Python helpers that should be reorganized elsewhere.
- `Side Projects`
  - By name and contents, not a core repo lane.
- `third_party`
  - Vendor/reference lane; should be treated deliberately outside the main dev root if not part of active build wiring.
- `tvhc`
  - Historical experiment lane.
- `alpha-4.2-cliwrappers-buildps1-patch-20250911-2`
  - Snapshot/patch archive, not a living lane.

## Review

These need a user decision before moving or deleting because they may still carry active value.

- `autodbf_fixtures`
  - Looks like useful test fixtures for import/autodbf behavior.
  - Decision after inspection: keep in `ccode` for now.
  - This is small, semantically clear, and belongs near test/regression work until a broader fixtures lane is formalized.
- `dottalk-webui`
  - Keeping for now, but long-term ownership may need to be clarified against website/public-site work.
- `pipelines`
  - Currently empty.
  - User chose to keep as a placeholder concept lane for now.
  - Add to `.gitignore` so it does not create repo noise until activated.
- `samples`
  - Currently only contains `_drops`.
  - Likely should be folded into a cleaner sample-data strategy.
- `smoke`
  - Very small but semantically useful.
  - Decision after inspection: keep in `ccode` for now.
  - This is a valid regression/canary lane and should stay close to runtime testing until folded into a cleaner test layout.
- `cookbooks`
  - Currently empty.
  - User chose to keep as a placeholder concept lane for now.
  - Add to `.gitignore` so it does not create repo noise until activated.

## Keep In Place After Inspection

These were reviewed after the first cleanup passes and should remain in `ccode` for now.

- `autodbf_fixtures`
  - Small CSV fixture set for autodbf/import behavior.
  - Fits naturally with regression and import testing.
- `smoke`
  - Tiny but meaningful smoke/regression lane.
  - Useful as long as the scripts remain environment-aware.
- `dbf_memo_cloner`
  - Small maintenance utility with active README edits.
  - Keep near runtime/dev work for now; later it could be folded under a clearer tools/maintenance lane.

## Coupled Utility Lanes: Review Before Move

These were inspected and should not be moved blindly.

- `third_party`
  - Audit completed on 2026-07-07.
  - `nlohmann-json` is supplied by the active vcpkg manifests in `vcpkg.json` and `vcpkg-wsl.json`.
  - Active Turbo Vision resolution comes from `find_package(tvision)` or `TVISION_ROOT`, which currently defaults to `D:\code\tvision`, not `D:\code\ccode\third_party\turbovision`.
  - The `third_party\nlohmann` and `third_party\turbovision` trees are duplicate local vendor copies and can be moved out of `ccode` safely.
- `patches`
  - Small patch/reference stash.
  - Partially tracked by the dev repo; keep in place for now.
  - Audit completed on 2026-07-07.
  - Tracked examples:
    - `patches/CMakeLists_additions.txt`
    - `patches/cmd_count_add_for_example.cpp`
    - `patches/cmd_locate_add_for_example.cpp`
  - Untracked scratch/archive candidates:
    - `patches/cmdhelp_v2_default_concept.patch`
    - `patches/shell_commands_TUPEXPORT_registration.txt`
    - `patches/src_CMakeLists_phase1_snippet.txt`
  - Keep the tracked examples in place; archive the untracked scratch separately.
- `payload`
  - Audit completed on 2026-07-07.
  - Contains manualgen payload/reference material and local `__pycache__` byproducts.
  - No live source/script/runtime references were found against the `payload` directory name in active build lanes.
  - Treat as archival packaging/reference material; safe to move out of `ccode`.
- `datadict_repo_dropin_dd023_v0`
  - Audit completed on 2026-07-07.
  - Historical drop-in/spec package lane for DD023.
  - No live source/script/runtime references were found against the directory name in active build lanes.
  - Treat as archival package/spec material; safe to move out of `ccode`.

## Trash

These are strong junk/cleanup candidates.

- `,gitattibutes`
  - Typo/malformed directory.
  - Contains only `gitattributes`.
- `.backup-rename-cli`
  - Backup copy stash, not source of truth.
- `nppBackup`
  - Editor backup junk.

## Root-Level Scratch / Duplicate Files

These are not core repo-root artifacts and should be archived or deleted when convenient.

- Safe scratch/archive candidates confirmed on 2026-07-07:
  - `-RepoRoot`
  - `build_dottalkpp_release_codex.err.log`
  - `build_dottalkpp_release_codex.log`
  - `cmd_ddict.cpp.review_candidate`
  - `tmp_function_smoke.dts`
  - `tmp_smoke_curated_lanes_20260622.txt`
  - `tmp_smoke_curated_lanes_20260622_b.txt`
  - `tmp_stage_smoke_curated_lanes_20260622.txt`
  - `tmp_stage_sync_list.txt`
- Safe duplicate text copies confirmed by hash:
  - `gather_usage_backlog.ps1.txt` duplicates `gather_usage_backlog.ps1`
  - `verify_bible_sql.txt` duplicates `verify_bible_sql.ps1`
  - `x64base.com.txt` duplicates `x64base.com.ps1`
- Larger generated inventories such as `dottalkpp_tree.txt`, `flattened_sources.txt`, and harvested CSV/MD reports should be reviewed separately instead of being moved blindly.

## Build / Runtime Byproducts

These are not part of the keep/move decision and should be handled in a separate cleanup pass.

- `build`
- `build-full-msvc.backup`
- `build-gui-local`
- `build-wx-explicit-local`
- `build-wx-fixed-local`
- `build-wx-local`
- `build-wx-vcpkg-local`
- `.pytest_cache`
- `results`
- `terminals`

Build status note as of 2026-07-07:

- Canonical Windows CLI/core build root is `D:\code\ccode\build`.
- Canonical WSL/Linux build root is `D:\code\ccode\build-wsl`.
- wx launch/runtime wiring now resolves `D:\code\ccode\build` first and only falls back to `build-wx-fixed-local` as a temporary compatibility path.
- The Python GUI preview bridge now resolves `D:\code\ccode\build\python` first; any remaining legacy GUI build roots should be treated as transitional only.
- Safe archive candidates from the old ad hoc build phase are:
  - `build-full-msvc.backup`
  - `build-wx-explicit-local`
  - `build-wx-local`
  - `build-wx-vcpkg-local`
- WSL policy is now normalized:
  - [CMakePresets.json](D:\code\ccode\CMakePresets.json) uses `build-wsl`.
  - [wsl_build_dottalkpp.sh](D:\code\ccode\wsl_build_dottalkpp.sh) now builds in repo-local `build-wsl`.
  - Do not introduce fresh WSL build roots unless a lane is intentionally isolated and documented.

## Priority Order

If cleanup is done in phases, the highest-value moves are:

1. `Bible`
2. `designs`
3. `drawio-libs-review`
4. `FoxApp`
5. `tv_test`
6. `palette`
7. `python_misc`
8. `_drops`

Then clean obvious junk:

1. `,gitattibutes`
2. `.backup-rename-cli`
3. `nppBackup`

## Immediate Recommendation

Next safe pass:

1. Move large non-core lanes from `D:\code\ccode` to `D:\code\...`
2. Delete the three obvious junk candidates
3. Keep `autodbf_fixtures`, `smoke`, and `dbf_memo_cloner` in place for now
4. Leave `third_party`, `patches`, `payload`, and `datadict_repo_dropin_dd023_v0` in place until dependency/package coupling is reviewed
5. Keep `cookbooks` and `pipelines` as ignored placeholder concept lanes
6. Leave build directories for a separate cleanup pass
