# Session Closeout -- x64base Engine and Edition Separation Research

Date: 2026-07-14  
Lane: DotTalk++ SDLC design + PLDC product boundary  
Mutation class: historical research record; implementation completed later  
Runtime/source implementation: see the implementation closeout dated 2026-07-14

## Resume here

The durable design is:

`docs/maintenance/X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md`

It separates four questions that had been collapsing into build booleans:

1. table-only versus legacy/full indexing;
2. lean versus professional/full educational content;
3. CLI/Python/TUI/wx front ends;
4. project licensing: To be determined.

Recommended first release candidate shape: **LEAN + FULL_INDEX**. Build and
prove **LEAN + TABLE_ONLY** as a secondary embedded/API product after the real
no-xindex boundary exists.

## Evidence digested

### Engine/index

- `src/CMakeLists.txt` always adds xindex before xbase.
- `src/xbase/CMakeLists.txt` links xbase publicly to xindex.
- xbase headers and sources own/use concrete `xindex::IndexManager` and key-codec
  types; xindex sources consume `xbase::DbArea`.
- `DOTTALK_WITH_INDEX=OFF` removes a direct LMDB backend source but does not
  remove xindex.
- dottalkpp separately links LMDB for its message catalog even when the
  interactive index option is off.
- existing pydottalk CTests prove physical-order table behavior through the
  existing module, not an xindex-free binary or index semantics.

### Edition/content

- `DOTTALK_WITH_EDUCATION` is not an effective build or runtime gate.
- current recursive source collection includes `src/edu` and `src/ext` in the
  main executable candidate set.
- the observed central registry has 223 add calls and unguarded education,
  history, student, maintenance, test, and external-tool surfaces.
- command registration metadata has no product component/edition field.
- HELP has education categories but no enforced product-component boundary.
- prior DD-004/DD-002 reports already identified the issue and supplied useful
  review queues; their heuristic classifications are not final dispositions.

### Packaging

- the current data install rule selects 1,159 files totaling 495.15 MiB in this
  working tree.
- `biblebase` contributes roughly 428.65 MiB before the install exclusions,
  including a 285.98 MiB SQLite file and large derivative CSVs.
- the broad install would copy two ignored/untracked COBOL executables because
  a directory install is independent of git tracking and `.gitignore`.
- a release package therefore needs a third allow-list distinct from both
  `.gitignore` and `PROMOTE.manifest`.

### Project status

- project licensing: To be determined.
- exact third-party notices are required; LMDB uses the OpenLDAP Public License,
  pybind11 is BSD-3-Clause, wxWidgets has its own exception license, Turbo
  Vision has mixed notices, and a bundled Python runtime has the PSF license
  stack.
- Project Gutenberg-derived content needs a separate content/trademark review,
  especially for commercial or transformed distribution.

Third-party texts and notices remain verbatim; they are not rewritten as
project terms.

## Design decisions recorded

- new index axis: `NONE | LEGACY | LMDB`;
- new product axis: `LEAN | PROFESSIONAL | EDUCATIONAL | DEVELOPMENT`;
- old index `OFF` must map to `LEGACY`, not silently to the new `NONE`;
- xbase core depends on a neutral optional-provider contract; xindex depends on
  xbase, never the reverse;
- pydottalk and dottalkpp are composition roots over the same selected engine;
- LEAN keeps a small `EDU_ESSENTIALS` pack but excludes `LABTALK_FULL`;
- recursive source and data globs cannot be edition/package authorities;
- command, HELP, function, script, dictionary, and data rows all need the same
  stable component ID;
- packages are built empty from tracked allow-listed inputs and include a
  manifest, SBOM, project status, notices, and content-rights inventory.

## Proposed lean education disposition

Keep for review as essentials:

- core HELP/usage/about/project status;
- one small DBF walkthrough;
- ASCII reference;
- neutral EXAMPLE behavior;
- BOOLEAN/FORMULA/EVALUATE when they are real expression-runtime capability.

Exclude from LEAN by default:

- BibleTalk/Biblebase;
- full LabTalk cases/history/campus;
- COBOL/CODASYL/DRAWIO/RETRO and ERP teaching stories;
- seasonal commands, MCC/course data, student self-registering examples;
- instructor material, large data packs, tests/canaries, and maintenance
  mutation tools.

NORMALIZE and IDX need semantic review: production operations move to neutral
runtime components; only their lessons belong in education.

## Files changed in this pass

- `docs/maintenance/X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md` -- new
  authoritative design/research plan.
- this closeout.
- AI Friendly intake/dashboard pointers for continuation.

No CMake, C++, Python, HELP DBF, data, staging, or GitHub files were changed by
this research pass.

## Verification performed

- read current CMake target/source/install rules;
- counted current source families and install-rule payloads;
- inspected command registry and HELP model fields;
- read DD-004, DD-002, DD-001, extension, SDLC, PLDC, AI Portal, and promotion
  authorities;
- inspected local vcpkg copyright files and resolved-package status;
- Project licensing: To be determined.
- checked ignored/tracked state for selected install payloads;
- reviewed official primary license pages for key dependencies/content.

No build or runtime test was needed for this documentation-only pass. The prior
two pydottalk CTests remain the physical-order table baseline.

## Next implementation pass

Start **Pass 0 only** from the main plan:

1. produce a machine-readable current source/command/HELP/data/install census;
2. give every row a proposed component or `REVIEW` disposition;
3. get maintainer approval for the `EDU_ESSENTIALS` list;
4. record the old-to-new CMake compatibility mapping;
5. draft the resolved package/SBOM report;
6. do not yet edit xbase/index lifecycle code.

After Pass 0 is accepted, implement component lists/metadata without changing
the DEVELOPMENT product surface. Invert xbase/xindex only in the following,
independently reviewed pass.

## Open maintainer decisions

1. Project licensing: To be determined.
2. Is the proposed `EDU_ESSENTIALS` set the right amount of teaching material
   for LEAN?
3. Should TABLE_ONLY become a sold product, or remain an embedded/API and
   architectural proof profile initially?

## Authority reminder

Original work stays in `D:\code\ccode`. `C:\x64base` remains disposable
staging and was not touched. No commit or publication was performed.
