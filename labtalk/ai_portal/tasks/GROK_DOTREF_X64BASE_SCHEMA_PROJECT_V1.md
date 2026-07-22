# GROK Project Packet — DOTREF x64base Metadata Authority and Generated Fallback v1

Status: **Assigned — design and external proposal**  
Assignee: **GROK**  
Maintainer and acceptance authority: **Derald**  
Owning project: `project.dotref_metadata_authority`  
Owning lifecycle: **DotTalk++ SDLC plus metadata/help maintenance lanes**  
Current SDLC lane: **design**

## Authority and Baseline

```text
Authoritative development source: D:\code\ccode
Curated publication staging:     C:\x64base
Public repository:                https://github.com/deraldg/x64base
Public branch:                    main
Public baseline for this packet:  4384820d2b82289fa76e789336218e0c1df1b290
AI Portal entry:                  https://github.com/deraldg/x64base/blob/main/AI_PORTAL.md
```

The public repository is the analysis baseline available to GROK. It is not newer
or stronger authority than the current contents of `D:\code\ccode`.

This assignment does not authorize GROK to write to local development, create or
change branches, commit, push, publish, mutate maintained DBFs, or approve its own
proposal.

## Problem

`include/dotref.hpp` currently holds the project-native DotTalk++ reference catalog
as a compiled static vector. Each entry contains:

- canonical command/reference name;
- syntax text;
- summary or long-form help text;
- supported state.

This design is operationally simple and resilient, but it concentrates command
identity, syntax, prose, support state, aliases, and transitional notes into one
large hand-maintained header. The project already has live x64base metadata tables
for commands, subcommands, entry variants, arguments, help text, functions, and
messages.

## Pinned Direction to Evaluate

The preferred target is a **hybrid authority model**, not schema-only runtime loading:

```text
source implementation and usage contracts
              +
reviewed x64base metadata authority
              |
              v
deterministic generated compiled DOTREF fallback
              |
              v
DOTHELP / HELP / SelfDoc / manualgen consumers
```

The schema should become the maintained/canonical metadata lane where practical.
A compiled and searchable DOTREF catalog should remain available for bootstrap,
recovery, damaged-data-root, standalone-test, and simple packaging scenarios.

GROK may challenge this direction, but must identify concrete evidence and failure
modes rather than replacing it by preference alone.

## Current Relevant Surfaces

Primary targets and evidence include:

- `include/dotref.hpp`
- `src/cli/cmd_dothelp.cpp`
- `include/browser/cmd_help_resolver.hpp`
- `dottalkpp/data/metadata/SYSCMD.dbf`
- `dottalkpp/data/metadata/SYSSUBCMD.dbf`
- `dottalkpp/data/metadata/SYSENTVAR.dbf`
- `dottalkpp/data/metadata/SYSARGS.dbf`
- `dottalkpp/data/metadata/SYSHELP.dbf`
- `dottalkpp/data/schemas/metadata/syscmd_catalog.dtschema`
- `dottalkpp/data/meta/SYSTEM_METADATA_SCHEMA_v1.dts`
- `dottalkpp/docs/authority/help_message_reference_authority_model_v1.md`
- `docs/maintenance/lanes/metadata/METADATA_FAMILY_SYSTEM_GUIDE_v1.md`
- `labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md`

GROK must inspect the current public versions and state exactly which files were
actually available and read.

## Assignment Objectives

1. Inventory the structure and consumers of `dotref.hpp`.
2. Separate implementation truth, identity metadata, syntax, summaries, aliases,
   detailed prose, support state, compatibility evidence, and generated artifacts.
3. Crosswalk each current `dotref::Item` field into the existing `SYS*` metadata
   family.
4. Determine whether the existing schema is sufficient or whether narrowly scoped
   schema extensions are required.
5. Design a deterministic metadata-to-C++ generator that preserves a compiled
   searchable fallback catalog.
6. Define runtime load/fallback policy without making `DOTHELP` responsible for
   opening metadata DBFs directly.
7. Produce a staged migration and equivalence-proof plan.
8. Identify drift, corruption, packaging, localization, ordering, memo, indexing,
   and bootstrap failure modes.

## Required Design Questions

GROK must answer at least these questions:

1. Should `dotref.hpp` remain the public API wrapper while generated data moves to
   a separate `.hpp` or `.inc` artifact?
2. Which fields belong in `SYSCMD`, `SYSSUBCMD`, `SYSENTVAR`, `SYSARGS`, and
   `SYSHELP`?
3. Should `supported` be stored, derived, or split into implementation, registration,
   reachability, visibility, and proof states?
4. How should multiline summaries, examples, notes, and ordering be represented?
5. How will aliases and multiword commands retain stable identity?
6. How will generation be deterministic across Windows and other platforms?
7. How will the generated catalog remain usable before a workspace is open?
8. What exact equivalence tests prove that current `DOTHELP` behavior was preserved?
9. What drift gate prevents source, metadata, generated DOTREF, HELP, and manualgen
   from silently disagreeing?
10. What is the smallest useful first implementation milestone?

## Preferred Metadata Crosswalk

Treat this as the initial hypothesis to validate:

| Current DOTREF fact | Candidate canonical home |
| --- | --- |
| canonical command identity | `SYSCMD` |
| multiword/routed command identity | `SYSSUBCMD` |
| aliases, shortcuts, re-expressions | `SYSENTVAR` |
| argument structure | `SYSARGS` |
| syntax line | `SYSHELP` syntax fragment plus structured `SYSARGS` |
| summary and detailed prose | sequenced `SYSHELP` rows/memos |
| supported state | derived from active/implementation/reachability/proof facts |
| compiled lookup/search data | generated DOTREF artifact |

Do not create a disconnected monolithic `DOTREF.dbf` unless the analysis proves the
existing metadata family cannot represent the required facts cleanly.

## Allowed Scope

GROK may propose changes for:

- DOTREF data modeling;
- metadata schema additions narrowly required for DOTREF;
- deterministic generator design or source;
- generated-header layout;
- `DOTHELP` catalog abstraction and fallback selection;
- validators, drift checks, and targeted tests;
- migration/import scripts and reviewed seed artifacts.

## Excluded Scope

- unrelated HELP or metadata cleanup;
- replacement of source implementation authority with documentation data;
- removal of compiled fallback capability;
- direct runtime DBF opening from `DOTHELP` without explicit architectural review;
- binaries, generated databases, indexes, LMDB environments, build output, secrets,
  credentials, or local machine state;
- branch creation, branch switching, commit, push, publication, or local mutation;
- claims of compilation or runtime proof that GROK did not perform.

## Required Deliverables

Return an external-AI package conforming to
`labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md` containing:

```text
x64base-ai-change-package/
  MANIFEST.md
  DESIGN.md
  SCHEMA_CROSSWALK.md
  GENERATOR_CONTRACT.md
  MIGRATION_PLAN.md
  TEST_PLAN.md
  NOTES.md
  changes.patch          # optional; proposal only
  new-files/             # only for genuinely new text source files
```

The package must include:

- complete AI report audit envelope;
- exact public baseline commit;
- files and contracts actually read;
- proposed changed/added/deleted files;
- compatibility and mutation effects;
- actual checks performed versus recommended local checks;
- unresolved conflicts and questions;
- explicit acknowledgment that local `D:\code\ccode` may have advanced.

## Acceptance Criteria

The project is ready for Derald's local review when the package:

- preserves implementation authority in source;
- uses the existing metadata family rather than inventing avoidable parallel tables;
- preserves a compiled bootstrap/recovery fallback;
- defines stable identities and deterministic ordering;
- defines a deterministic generator and reproducible output comparison;
- provides a no-loss mapping for every current DOTREF entry;
- separates structural metadata from localizable/rendered prose;
- defines exact lookup, search, unsupported-state, and multiline-output equivalence tests;
- identifies a reversible first milestone;
- makes no unsupported compilation, integration, or runtime claims.

## Next Gate

GROK returns the required package. Derald then compares it against the current
`D:\code\ccode` source and contracts, accepts/rejects the architecture, and separately
authorizes any implementation work.
