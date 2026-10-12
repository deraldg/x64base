# DDICT shared catalog view implementation record -- 2026-10-09

Status: local source implemented and focused native checks passed; application
executables not rebuilt; no promotion or publication.
Authorization: maintainer's "make it so" after the curation sequence, followed
by the explicit requirement to dogfood x64base with long file/table/field names.

## Scope and contract preflight

Owning subsystems: datadict inspection, CLI DDICT, GUI dictionary panel, memo
inspection. Source targets: include/datadict/ddict_dbf_reader.hpp,
src/datadict/ddict_dbf_reader.cpp, include/datadict/ddict_catalog_view.hpp,
src/datadict/ddict_catalog_view.cpp, src/datadict/ddict_object_resolver.cpp,
include/memo/memostore.hpp, src/memo/memostore.cpp, src/cli/cmd_ddict.cpp,
src/gui/wx/main_frame.cpp, src/gui/core/CMakeLists.txt, src/CMakeLists.txt,
src/tests/CMakeLists.txt, src/tests/test_ddict_catalog_view.cpp. Runtime usage
text in src/help/helpdata_messages.cpp is also updated for FAMILY selection.

Read authority: AI_TIER1_SEED_V1, AI_AGENT_LAWS_SEED_V1, source mutation gate,
contracts README/registry/lifecycle, DATABASE_SAFETY_CONTRACT_V1,
UNIFIED_GUI_CORE_V1, repository-role and closeout contracts. These are binding
constraints; reading them does not assert their runtime enforcement. The
source/evidence crosswalk and catalog authority report document historical
migration drift. No catalog replacement or refresh is authorized by this work.

Behavioral effect: both preserved catalog families feed one explicit read view;
long X64M field and table identities survive inspection; memo text is read using
the existing DTX backend without header writes; origin and original IDs remain
available; x64 references are isolated from legacy IDs and source-artifact
references from DDSOURCE. Invalid present tables produce diagnostics; missing
optional family files do not invalidate usable rows. TAGS requires an actual
CDX/LMDB artifact before reporting physical index artifacts.

Proof plan: targeted native C++ test using create_dbf(Flavor::X64), explicit
logical table identity, DbArea append/set/write, and native MemoStore; test
long physical/logical/field names, colliding prefixes, fields above 255 bytes,
13-row geometry, bad/truncated files, empty/missing distinction, family ID
collision, typed attribute endpoints, decoded memo text, denied writes and
unchanged bytes/write times. Inspect maintained catalogs read-only with before
and after hashes. Compile changed CLI and GUI consumers. Do not infer a rebuilt
application from a source check or an older executable.

## Evidence as produced

- Initial CMake target attempt failed before compilation because vcpkg tried to
  write outside the workspace. Retried with installed dependencies and
  VCPKG_MANIFEST_INSTALL=OFF; compiler discovery then hit Windows SDK registration
  access. Requested narrow build escalation. Build logs live under build/.
- No maintained catalog or index data has been changed by implementation.
- Work remains local and uncommitted. Shared-tree git mutation is not performed.

## Verified result

The CLI and GUI now call `read_catalog_view`. This adapter preserves both schema
families and original long-name fields, translates consumer keys explicitly,
isolates X64 family IDs with `x64:`, and preserves source artifacts as a separate
reference domain. Family means schema origin: legacy DD* files themselves can
also use the native x64 disk format. The old physical-reader signature remains
available to the metadata consumer.

`DDICT FIELDS DATA_DICTIONARY_OBJECTS` now displays the actual long physical
field names and widths before the curated owner-based field metadata.
`DDICT OBJECTS FAMILY X64` exposes the supplemental objects within the listing
limit. Full names, IDs and memo text are no longer clipped by column widths.
TAGS no longer treats a DBF's existence as evidence of an index. The Workbench
adds family and evidence-detail columns, resolves typed attribute targets, and
limits attribute-linked evidence to the selected object.

## Native proof and practical limits

[Validation evidence](DDICT_CATALOG_VIEW_VALIDATION_2026-10-09.json) records the
source/binary hashes, commands, build outputs, fixture roots, and complete final
CTest output. Windows x64 / MSVC 19.44 (VS 2022 toolset 14.44.35207), Release:

- Native dogfood test: **159 explicit checks passed**. These include native
  CREATE, APPEND, field writes and exact read assertions, not 159 separate
  scenarios. No test assertion is disabled by NDEBUG.
- CTest: both DDICT catalog tests passed (directory resolver and shared view).
- Actual production `cmd_DDICT`, output router, command-output helpers and message
  text are compiled and linked into the focused test. FIELDS, OBJECTS, REL,
  EVIDENCE, TAGS and HELP output assertions passed against disposable native
  catalogs. No command implementation is mocked.
- The GUI core rebuilt. `main_frame.cpp` compiled under its existing Workbench
  wxWidgets project. The reader also compiled under the C++17 `dt_meta` target.
- The installed `dottalkpp.exe` and Workbench executables were **not relinked or
  launched**. Interactive GUI behavior and full-shell integration are not proven
  by this focused test. The current CMake configuration has WX disabled; the
  existing wx project was used only to compile the changed display file.
- No HELP/metadata catalog, workspace schema, maintained DBF, DTX, CDX, or LMDB
  data was rewritten. Source usage text was updated; generated publications and
  historical curation snapshots remain separate.

Native fixtures prove: long physical filenames; a different long logical table
identity; two long field names with the same initial ten characters; a
1,024-byte character field; thirteen-row x64 header geometry; empty vs missing
vs malformed files; required-field rejection; cross-family ID collision;
attribute-target relations; native DTX text; write rejection and move behavior
in read-only mode; unchanged memo bytes and write time; absent sidecar handling;
and explicitly invalid space-filled imported memo links.

## Maintained catalog findings -- data repair remains separate

[Read proof](DDICT_CATALOG_VIEW_READ_PROOF_2026-10-09.json) contains complete
before/after hashes, initial file timestamps, final command output and triage.
All **35 direct catalog files retain their initial SHA-256** after inspection.
No maintained table was opened through a writable DbArea.

| View | Legacy + supplemental | Combined rows |
| --- | --- | --- |
| Objects | 100 + 10 | 110 |
| Attributes | 423 + 127 | 550 |
| Relations | 89 + 16 | 105 |
| Evidence | 1 + 7 | 8 |

All seventeen physical DBFs decode. The long-name data is not fully consistent:

- Four memo-bearing supplemental DTX files contain only their 4,096-byte headers.
  Thirteen nonzero binary references have no retrievable memo object: two runs,
  one attribute, seven evidence records and three gates.
- Another 126 attribute memo cells contain eight ASCII spaces, which are not
  native x64 null links. They are labeled invalid, not coerced to empty text.
- Fourteen relation endpoint lookups cannot resolve within their origin family.
  The reader does not invent cross-family joins to hide these gaps.
- The final live inspector therefore exits **2 (review required)** with nineteen
  grouped diagnostics/endpoint findings. This is intentionally separate from
  the passing native-fixture test. Existing legacy memo text is readable.

Recovering the missing bodies, repairing links, assigning canonical write
ownership and physically consolidating duplicate directories are future scoped
work. The duplicates and recovery material were retained.

## Housekeeping and replay

All authored work is local/uncommitted. No staging, commit, branch change, push,
archive, or data migration was performed. The validation evidence classifies
owned paths and records other dirty paths as untouched; a dirty shared tree is
not described as a release defect. The snapshot lists 7,177 other dirty paths.
Git could not enumerate the inaccessible `.pytest_cache/` directory; no
clean-tree claim is made. Thirty-one local documentation links passed. Scoped
C++ typography checks passed; unrelated existing em-dash text in the message
file was retained outside the two DDICT usage lines changed here.

Disposable native tables and their deliberately malformed cases are retained
under `build/ddict-dogfood/<run>/`; exact run directories are recorded in the
validation evidence. Focused build/test logs remain under `build/ddict_*` and
the essential outputs are embedded in the maintained validation JSON.
One first escalated configure attempt used an unexpected home-directory working
folder and produced only an error log at
`C:/Users/deral/build/ddict_catalog_view_configure.log`; it did not configure a
project. It is reported as residue, not used as evidence.

The package-install cache setting was temporarily OFF to reuse installed
packages, and was restored to ON after verification without running an install.
No persistent shell environment changes were made. Future compilation still
needs the installed VS/Windows SDK and dependencies; the test is part of the
normal CMake test-target enumeration, not an undocumented standalone build.

Replay from the repository after normal maintainer configuration:

```text
cmake --build build --config Release --target dottalkpp_ddict_catalog_view_test
ctest --test-dir build -C Release -R "^dottalkpp_ddict_catalog_(view|dir)_test$" -V
build\src\tests\Release\dottalkpp_ddict_catalog_view_test.exe --inspect dottalkpp\data\datadict
```

The last command currently returns 2 for the documented data findings. An
application rebuild and interactive Workbench smoke remain the integration
handoff; the scoped source and native-command proof do not claim deployment.
