# C:\x64base Source Currency Audit — 2026-07-12 v1

Status: complete, promotion blocked pending review
Owning lifecycle: DotTalk++ SDLC with LabTalk publication staging
SDLC lane: proof
Truth state: development tree is authoritative
Proof state: static SHA-256 content comparison
Risk class: high
Source path: `D:\code\ccode`
Staging path: `C:\x64base`
Next gate: select the clean promotion set, copy it to staging, then rebuild and
run targeted regression proof
Owner: maintainer

## Conclusion

`C:\x64base` does **not** contain the latest authoritative source from
`D:\code\ccode`.

The audit compared source-like files by relative path and SHA-256 content. It
excluded Git data, build output, dependency/cache directories, generated
material, archival drops, backups, and candidates.

| Result | Count |
| --- | ---: |
| Development inventory | 3,047 |
| Staging inventory | 3,005 |
| Shared paths | 2,935 |
| Exact content matches | 2,899 |
| Shared paths with different content | 36 |
| Development-only source-like paths | 112 |
| Development-only paths in selected current source roots | 18 |
| Staging-only source-like paths | 70 |

The inventories include C/C++, Python, PowerShell, shell, CMake, DotScript,
JavaScript/TypeScript, and recognized root build manifests.

## Different shared files

### C++ and headers

- `bindings/pydottalk/src/module.cpp`
- `include/dotref.hpp`
- `include/foxref.hpp`
- `src/cli/cmd_erase.cpp`
- `src/cli/cmd_help.cpp`
- `src/cli/cmd_regression.cpp`
- `src/cli/cmd_retro.cpp`
- `src/cli/cmd_version.cpp`
- `src/cli/cmdhelp.cpp`
- `src/cli/command_catalog.cpp`
- `src/cli/reference_collection.cpp`
- `src/cli/shell_commands.cpp`
- `src/cli/shell_commands.hpp`
- `src/edu/edu_christmas.cpp`
- `src/gui/wx/main_frame.cpp`
- `src/help/helpdata_messages.cpp`

### Python

- `bindings/pydottalk/src/table.py`
- `pycrud/pydottalk_api/app/api/routes.py`
- `pycrud/pydottalk_api/app/utils/xbase_meta.py`
- `pycrud/ui/app.py`
- `tools/gui_preview/dottalk_gui_backend.py`
- `tools/gui_preview/gui_cli_bridge.py`

### Build and launch control

- `CMakeLists.txt`
- `CMakePresets.json`
- `build.ps1`
- `launch_portal.ps1`
- `run-wx-next.ps1`
- `run-wx.ps1`
- `wsl_build_dottalkpp.sh`

### DotScript proof scripts

- `dottalkpp/data/scripts/canaries/x64_matrix_metrics_boundary_canary.dts`
- `dottalkpp/data/scripts/dottalkpp_non_destructive_smoke.dts`
- `dottalkpp/data/scripts/index_v64_cdx_lmdb_smoke.dts`
- `dottalkpp/data/scripts/index_x32_inx_cnx_smoke.dts`

### Documentation maintenance tools

- `dottalkpp/docs/tools/doccheck_header_contract_batch3_metadata_hygiene_v1.ps1`
- `dottalkpp/docs/tools/metacollect_runtime_harness_reboot_recovery_check_v1.ps1`
- `dottalkpp/docs/tools/metacollect_runtime_harness_v1.ps1`

Development timestamps are newer for every differing shared file, but the
finding is based on content hashes rather than timestamps.

## Missing current-source candidates

The following development files are absent from staging and appear relevant to
the current implementation or its proof/tooling lanes:

- `include/dottalk/version.hpp`
- `src/cli/retro_render.cpp`
- `src/cli/retro_render.hpp`
- `src/cli/retro_screen.cpp`
- `src/cli/retro_screen.hpp`
- `src/edu/edu_hanukkah.cpp`
- `src/labtalk/__init__.py`
- `src/labtalk/lms/__init__.py`
- `src/labtalk/lms/pipe.py`
- `tools/diagram/diagram_provenance.py`
- `tools/docs_drift_check.ps1`
- `tools/version_info.py`
- `dottalkpp/data/scripts/main/harvest_top_shakedown.dts`

`cmd_retro.cpp` in development includes the missing `retro_render.hpp` and
`retro_screen.hpp`. `cmd_version.cpp` and the wx main frame include the missing
`dottalk/version.hpp`. These must be reviewed and promoted as coherent sets,
not as isolated file copies.

Five other development-only files are temporary, backup, or packaging
candidates and are not presumed publishable by this audit.

## Staging-only observations

The 70 staging-only source-like paths consist primarily of:

- 43 files under the legacy `sqlite-gui` tree;
- 14 generated Next.js files under `dottalk-webui/public-site/_next`;
- 10 older `py` and `python_misc` utilities;
- two staging-only launchers;
- one generated `src/cmake_install.cmake` file.

These do not establish source currency. Generated `_next` and CMake install
output should not be treated as authoritative development source.

## Git-state caution

Both trees are dirty. Several authoritative development files are untracked,
and several staging files are modified or untracked. Promotion must therefore
use an explicit reviewed path list. A bulk mirror, blanket `git add`, or branch
comparison alone would be unsafe.

### Post-audit publication correction — 2026-07-12

The initial promotion verified development-to-staging working-copy hashes but
did not separately require a committed-blob check for every build input. Human
review of the development build exposed that `src/cli/cmd_concat.cpp` was
byte-identical in `C:\x64base` and participated in the staged CMake build, but
was still untracked and therefore absent from publication commit `fdb882a0`.

The resulting committed-blob audit covered all 980 current C/C++ and header
paths under `src`, `include`, and `bindings`. It found the coherent `EXITS`
source set in the same state: `src/cli/cmd_exits.cpp`,
`src/cli/extension_manifest.cpp`, and `src/cli/extension_manifest.hpp` were
byte-identical in development and staging and available to the local glob-based
build, but were not tracked by the publication commit. All four files were then
selected explicitly for Git publication.

The correction gate is now explicit: source currency must verify development
content, staged working-copy content, and Git index/commit inclusion. A local
build can consume an untracked file and cannot by itself prove GitHub
completeness.

A subsequent full blob comparison found 58 tracked C/C++ paths whose C working
copies matched development but whose committed blobs were stale. The explicit
set was staged after correcting eight whitespace-hygiene findings in
authoritative development. Six of those paths then matched their existing
committed content, leaving 52 substantive current-source updates. The final
pre-commit Git-index audit covered all 980 C/C++ and header paths and reported
zero missing paths and zero content differences from `D:\code\ccode`.

## Build interpretation

The staging executable linked successfully at 2026-07-12 20:59:32, but it was
built from the older staging source identified above. A successful build does
not prove staging matches development.

## Required next gate

1. Review the 36 differing paths and the coherent missing-source sets.
2. Separate publishable current source from private, temporary, generated, and
   legacy material.
3. Promote only the approved paths from development to staging.
4. verify hashes again;
5. perform a clean/incremental staging rebuild as appropriate;
6. run targeted HELP/CMDHELP, version, RETRO, Python binding, GUI/PyCRUD, and
   DotScript canary proof;
7. stage only the reviewed publication set for commit.

No source, staging, or Git mutation was performed by this audit.
