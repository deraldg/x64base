# DD-009 HELP / Message / Diagnostics Link Map v0

Status: **REPORT_ONLY / SOURCE_EVIDENCE_MAP / NO_REPO_MUTATION**  
Generated: 2026-05-27T14:52:22+00:00

## Purpose

DD-009 organizes the explanation and reporting surfaces that the data dictionary will need before it can become useful to users, developers, and future validation tools.

It maps source evidence for:

- HELP routing and command help surfaces
- CMDHELP HELP DATA build/report surfaces
- CMDHELPCHK validation/report surfaces
- HELP artifact names and DBF/DBT references
- message catalog and canonical error-code surfaces
- diagnostics, warnings, and report-output producers
- command-to-usage/HELP link candidates from `@dottalk.usage v1`

This is a map, not a mutation. It does not rebuild HELP, run CMDHELPCHK, alter source, or promote catalog rows.

## Counts

| Item | Count |
|---|---:|
| focused source anchors | 344 |
| HELP surface anchors | 73 |
| HELP artifact mentions | 67 |
| message/catalog/error anchors | 139 |
| diagnostic/reporting anchors | 213 |
| command HELP link candidates | 200 |
| proposed catalog extension rows | 7 |
| reporting model rows | 7 |
| boundary rows | 6 |

## High-value source anchors

The strongest HELP/diagnostic anchors in the corrected repo are:

```text
src/cli/cmd_help.cpp
src/cli/cmdhelp.cpp
src/cli/command_helpchk.cpp
src/help/helpdata_source_miner.cpp
src/help/helpdata_messages.cpp
src/cli/message_catalog.cpp
src/cli/catalog_reader_adapter.cpp
src/cli/cmd_catalogcanary.cpp
include/xbase_error_codes.hpp
include/xbase_error_context.hpp
include/xbase_error_runtime.hpp
src/cli/cmd_error_status.cpp
src/cli/cmd_error_clear.cpp
src/cli/cmd_error_test.cpp
```

## Proposed dictionary objects

DD-009 proposes these additions to the data-dictionary object family:

| Object | Purpose |
|---|---|
| `DD_HELP_SURFACE` | HELP routers, HELP builders, HELP validators, and reference collections. |
| `DD_HELP_ARTIFACT` | HELP DATA artifacts such as `help_line.dbf`, `help_artifacts.dbf/.dbt`, `commands.dbf`, and `cmd_args.dbf`. |
| `DD_COMMAND_HELP_LINK` | Links between commands, usage access, HELP topics, source contracts, and related commands. |
| `DD_MESSAGE` | Message/error-code identifiers, severity, facility, display/stringifier evidence. |
| `DD_DIAGNOSTIC_SURFACE` | Warning/error/diagnostic producers and their report surfaces. |
| `DD_REPORT_SURFACE` | Commands/renderers that consume dictionary facts and print reports. |
| `DD_VALIDATION_SURFACE` | Validators that compare HELP, catalog, artifact, command, and runtime evidence. |

## Interpretation

The data dictionary should not only know tables and fields. It also needs to know how the system explains itself and reports what went wrong.

That means a future dictionary row can answer questions like:

```text
Which HELP topic explains this command?
Which source contract generated this help row?
Which message/error code is emitted when this validation fails?
Which report surface displays this dictionary warning?
Which CMDHELPCHK mode validates the artifact?
```

## Trust boundary

DD-009 separates several evidence levels:

```text
source string / source contract       = source evidence
command registry row                  = dispatch/registration evidence
HELP artifact mention                 = source reference, not proof that artifact exists now
CMDHELPCHK source                     = validator surface, not executed validation result
runtime transcript / smoke report     = future runtime proof
```

## Profile boundary

This package reinforces the project profile rule:

```text
x64base engine
  may own stable error-code/message primitives.

DotTalk++ professional runtime
  owns HELP, CMDHELP, CMDHELPCHK, dictionary explanation, and report surfaces.

LabTalk / education overlay
  may add educational HELP topics and cases, but should be hideable/optional in professional mode.
```

## Boundary preserved

- No repo files changed.
- No source files edited.
- No CMake files edited.
- No runtime launched.
- No `CMDHELP BUILD` run.
- No `CMDHELPCHK` run.
- No HELP/META/CMDHELPCHK/catalog/DBF/CDX/LMDB mutation.

## Next recommended package

**DD-010 — HELP artifact and CMDHELPCHK validation plan**, still report-only.

DD-010 should define non-mutating checks for:

```text
command registry coverage
source usage contract coverage
HELP DATA artifact coverage
CMDHELPCHK validation surfaces
DD_COMMAND_HELP_LINK completeness
professional vs educational HELP visibility
```
