# DD-004 Build Profile and Optional Overlay Boundary Audit v0

Status: REPORT_ONLY / NO_REPO_MUTATION

Input repo package: `ccode_homegrown_20260527-055727.zip`

## Purpose

DD-004 organizes the build/profile boundary for the data dictionary and future runtime packaging. It focuses on keeping x64base credible as an engine, DotTalk++ credible as a professional runtime, and LabTalk/student/case material as an optional overlay rather than a core dependency.

## Counts

- CMake options parsed: 12
- CMake preset cache variables parsed: 7
- DOTTALK/build/profile references captured: 166
- Files classified for profile review: 981
- Shell command registrations parsed: 198
- Education/overlay file candidates: 35
- Current recursive-glob overlay risk candidates: 75
- Boundary issues recorded: 6

## File lane counts

- professional_runtime: 618
- engine_core: 126
- unclassified_or_shared: 118
- tv_ui_optional: 65
- educational_overlay: 30
- script_maintenance: 20
- build_profile_control: 4

## Shell command profile candidate counts

- PROFESSIONAL_OR_CORE_REVIEW: 153
- INDEX_OPTIONAL: 18
- EDUCATIONAL_CANDIDATE: 15
- TV_OPTIONAL: 7
- RELATIONS_OPTIONAL: 5

## Key findings

1. `DOTTALK_WITH_EDUCATION` exists as a top-level CMake option, but this audit found no effective enforcement in the source build or shell registration path.
2. `src/CMakeLists.txt` recursively globs most of `src/` and excludes several subtrees, but not `src/edu` or education/student extension command paths.
3. `shell_commands.cpp` contains an Education / historical-computing command registration block that appears unguarded in the observed source.
4. `CMakePresets.json` uses `DOTTALK_WITH_TVISION`, while CMake defines `DOTTALK_WITH_TV`.
5. The clean profile model should be explicit: ENGINE, PROFESSIONAL, EDUCATIONAL, DEV, and TV_UI.

## Recommended next work packages

- DD-004B: produce a guarded profile-gating design, still report-only.
- DD-005: physical dictionary source map for DBF/table/field/index/memo inventory.
- DD-006: MetaFact bridge plan for dictionary evidence and runtime proof.

## Boundary

No source files were changed. No CMake files were changed. No build was run. No HELP/META/CMDHELPCHK/catalog/runtime data was mutated.
