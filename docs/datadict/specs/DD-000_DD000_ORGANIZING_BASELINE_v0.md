# DD-000 Organizing Baseline v0

Status: REPORT-ONLY organizing package. No project code was run and no repo contents were modified.

Source package inspected: `ccode_homegrown_20260527-055727.zip`.

## Counts

- Files inventoried: 981
- `src/` files: 654
- `include/` files: 290
- C/C++ source/header files: 908
- Script/probe files: 20
- Build/config/manifest files: 20
- Note/transcript text files: 33

## Organizing doctrine

Core first, overlays optional.

- `x64base` must be able to stand as an engine without LabTalk/student/case/media artifacts.
- `DotTalk++` should be usable as a neutral/professional runtime without visible student artifacts by default.
- LabTalk, cases, storyboards, media, and student examples belong in optional educational overlays.
- Runtime and maintenance scripts are first-class lifecycle objects and should be cataloged, not hidden.

## First organizing lanes

1. Physical engine facts: tables, fields, indexes, memo, runtime verification.
2. Professional DotTalk++ facts: workspace, relations, rules, schema, expressions, commands, HELP, messages.
3. SelfDoc/provenance bridge: source contracts, MetaFact, runtime proof, review state.
4. Script/tooling lifecycle: build configs, launchers, DotScript, Python probes, MDO/savepoint scripts, maintenance packages.
5. Optional educational overlay: LabTalk, cases, media, student commands, teaching examples.

## Immediate boundary findings to handle later

- `DOTTALK_WITH_EDUCATION` exists at top level, but DD-000 did not find equivalent filtering/enforcement in `src/CMakeLists.txt` for `src/edu`, `src/ext`, or LabTalk paths.
- CMake option naming appears split between `DOTTALK_WITH_TV` and `DOTTALK_WITH_TVISION`.
- A status-message typo `DOTTALK_WITH_EDUCATON` appears in the top-level summary.
- The central registry policy already distinguishes built-in commands from custom/student exceptions, which is good evidence for the overlay split; it still needs a build/profile visibility audit.

## Package files

- `dd000_source_roots_v0.csv`
- `dd000_directory_summary_v0.csv`
- `dd000_subsystem_lanes_v0.csv`
- `dd000_catalog_table_proposal_v0.csv`
- `dd000_work_packages_v0.csv`
- `dd000_script_lane_seed_v0.csv`
- `dd000_build_profile_audit_v0.csv`
- `dd000_build_profile_line_hits_v0.csv`
- `dd000_proposed_repo_placement_v0.csv`
- `dd000_file_inventory_seed_v0.csv`

## Recommended gate

Accept this as `DD-000 ORGANIZING_BASELINE_REPORT_ONLY`, then move to DD-001 physical scan and DD-003 script/tooling registry in parallel.
