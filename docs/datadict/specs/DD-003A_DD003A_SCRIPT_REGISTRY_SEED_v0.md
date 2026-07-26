# DD-003A Script / Runtime / Maintenance Registry Seed v0

Date: 2026-05-27

Status: REPORT_ONLY / ORGANIZING_BASELINE

## Purpose

DD-003A converts the previously reserved script lane into concrete catalog seeds. It treats scripts, build configs, DotScript runtime files, workspace schema files, probes, launchers, and maintenance scripts as lifecycle artifacts that deserve dictionary identity.

This is intentionally separate from C++ source ownership. The dictionary should be able to say not only what table or command exists, but which script configured it, launched it, validated it, saved it, documented it, or appended its maintenance savepoint.

## Inputs

- Corrected C++ repo package: `ccode_homegrown_20260527-055727.zip`
- Prior script-estate inventory: `dottalk_script_inventory_v0.csv`, derived from `ccode_homegrown_20260527-044819.zip`
- Existing DD-000, DD-001, and DD-002 organizing outputs

## Counts

### Registry seed rows by source

- ccode_homegrown_20260527-055727.zip: 41
- ccode_homegrown_20260527-044819.zip / prior script estate inventory: 174

### Registry seed rows by lane

- archival_backup_script: 14
- binding_test_or_probe: 20
- build_config: 17
- build_or_configure: 2
- maintenance_manualgen_mdo_package: 22
- maintenance_savepoint_journal: 105
- maintenance_utility: 8
- manifest: 1
- python_probe: 20
- runtime_launcher_or_smoke: 3
- schema_json: 3

### Boundary classes observed

- build_dependency_contract: 1
- build_mutates_build_graph: 15
- build_mutates_configuration: 1
- declared_schema_contract: 2
- declared_schema_sample: 1
- external_probe_no_core_dependency: 20
- external_probe_or_maintenance: 20
- guarded_generated_docs_mutator_or_report_only: 22
- maintenance_journal_mutator: 105
- read_only_inventory: 1
- review_before_execution: 24
- runtime_launcher: 3

### C++ script-support anchors by theme

- DotScript resolution: 187
- Init script runner: 26
- MCC script launcher: 58
- Test script command: 4
- Workspace schema scripts: 50

## Key finding

The corrected C++ repo has the runtime mechanisms for script execution and resolution, especially `cmd_dotscript.cpp`, `script_reader`, `init_script_runner`, `cmd_init.cpp`, `cmd_mcc.cpp`, `cmd_workspace.cpp`, and shell/API integration.

The earlier uploaded script-estate package contributes the broader maintenance lifecycle: MDO packages, savepoint appenders, launch/smoke helpers, cleanup/bundle utilities, and Python probes. These should be cataloged, but not confused with engine source or mandatory student artifacts.

## Catalog families reserved

```text
DD_SCRIPT
DD_SCRIPT_ROLE
DD_SCRIPT_DEP
DD_SCRIPT_RUN
DD_SCRIPT_OBJECT
DD_SCRIPT_BOUNDARY
DD_BUILD_PROFILE
DD_SAVEPOINT
DD_RUNTIME_PROOF
```

## Proposed DD_SCRIPT core fields

```text
SCRIPT_ID
SCRIPT_NAME
RELATIVE_PATH
SCRIPT_KIND
ROLE
BOUNDARY_CLASS
PROFILE_SCOPE
CORE_RELEVANCE
SOURCE_PACKAGE
HASH
FIRST_SEEN_RUN
LAST_VERIFIED_RUN
MUTATION_SCOPE
REVIEW_STATUS
SOURCE_REF
```

## Proposed DD_SCRIPT_DEP fields

```text
DEP_ID
FROM_SCRIPT_OR_COMMAND
TO_SCRIPT_OR_OBJECT
RELATIONSHIP
EDGE_CLASS
EVIDENCE_SOURCE
REVIEW_STATUS
```

## Proposed DD_SCRIPT_RUN fields

```text
RUN_ID
SCRIPT_ID
RUN_TIMESTAMP
OPERATOR_OR_AGENT
WORKING_DIRECTORY
ARGUMENTS
STATUS
LOG_PATH
MUTATION_CLASS
PROTECTED_SYSTEM_MUTATION_FLAG
SAVEPOINT_REF
RUNTIME_PROOF_REF
```

## Boundary doctrine

- x64base must build and operate as an engine without student or LabTalk artifacts.
- DotTalk++ should support a professional runtime profile with no visible student layer by default where practical.
- LabTalk, cases, student examples, storyboards, and media belong in optional overlay packages.
- Scripts needed for runtime or maintenance are first-class infrastructure, but each script must carry a boundary class before it is promoted into a trusted lifecycle role.

## Immediate design consequence

DD-003A should not simply add a `scripts` folder list. It should model script identity, role, dependency edges, execution evidence, and mutation boundaries. This lets SelfDoc and the data dictionary preserve regeneration proof without blurring core engine boundaries.

## Generated files

- `dd003a_script_registry_seed_v0.csv`
- `dd003a_script_support_cpp_anchors_v0.csv`
- `dd003a_dependency_edges_seed_v0.csv`
- `dd003a_boundary_matrix_v0.csv`
- `dd003a_roots_and_resolution_v0.csv`
- `DD003A_NEXT_ACTIONS_v0.md`
- `DD003A_AUTOLOG_v0.md`
