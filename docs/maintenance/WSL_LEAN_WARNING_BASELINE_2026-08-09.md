# WSL Lean Warning Baseline - 2026-08-09

## Scope

This is the warning inventory from the staged `wsl-lean` build supplied by the
maintainer on 2026-08-09. It is a baseline, not a claim that the warnings are
accepted or harmless.

- Staging root: `/mnt/c/x64base`
- Configure preset: `wsl-lean`
- Product/profile: `DEVELOPMENT` / `DEV`
- Index mode: `LMDB`
- Compiler: GNU C++ 13.3.0
- Reported source identity: `e74e6ee6`, dirty staging tree
- Build result: 540 of 540 steps completed; `src/dottalkpp` linked
- Test result before the profile-smoke repair: 13 of 14 passed
- Sole test failure: `dottalkpp_profile_smoke`

The failing smoke supplied Windows-style command paths to the POSIX runtime,
producing literal paths such as `dbf\\x32\\students.dbf`. The development repair
uses forward slashes, which DotTalk accepts on both Windows and POSIX.

## Counts

The captured compiler output contains 92 warning lines across 63 distinct
source locations. Of those, 62 locations are in 32 project files; one repeated
location is in the GNU standard library and is reached through project index
comparators. Repeated template/header diagnostics are counted each time the
compiler emitted them.

| Diagnostic | Emitted lines |
| --- | ---: |
| `-Wpedantic` | 20 |
| `-Wmisleading-indentation` | 15 |
| `-Wformat-truncation` | 12 |
| `-Wunused-function` | 9 |
| `-Wtype-limits` | 5 |
| `-Wmultichar` | 5 |
| `-Wstringop-overread` | 5 |
| `-Wunused-result` | 5 |
| `-Wclass-memaccess` | 3 |
| `-Wreorder` | 3 |
| `-Wunused-variable` | 3 |
| `-Wmissing-field-initializers` | 2 |
| `#pragma once in main file` | 1 |
| `-Wunused-but-set-variable` | 1 |
| `-Wignored-qualifiers` | 1 |
| `-Wunused-parameter` | 1 |
| `-Wrange-loop-construct` | 1 |

## Concentrations

The largest repeated groups in the captured output are:

- `include/cli/expr/fn_string.hpp`: 20 `-Wpedantic` emissions from anonymous
  structs at lines 63-64.
- `src/identity/identity_dbf_store.cpp`: 9 misleading-indentation sites.
- `include/value_normalize.hpp`: 7 repeated format-truncation emissions from
  the date buffer at line 138.
- `src/cli/cmd_setpath_command.cpp`: 5 multi-character constants and the same
  5 comparisons reported as always false.
- `src/xindex/bpt_backend.cpp` and `src/xindex/bptree_backend.cpp`: 5 emitted
  `-Wstringop-overread` diagnostics inside GNU `std::vector` comparison code.
- `src/cli/zip_backend_win.cpp`: 5 unused POSIX-build declarations or
  parameters.

Other warning-bearing project files in this capture are:

`src/bbs/bbs_store.cpp`, `src/cdx/cdx_file.cpp`,
`src/cli/app_smart_browser.cpp`, `src/cli/browse/browse_filters.cpp`,
`src/cli/cmd_bang.cpp`, `src/cli/cmd_browsetui.cpp`,
`src/cli/cmd_calcwrite.cpp`, `src/cli/cmd_ddict.cpp`,
`src/cli/cmd_ersatz.cpp`, `src/cli/cmd_lmdb_dump.cpp`,
`src/cli/cmd_relations.cpp`, `src/cli/cmd_replace.cpp`,
`src/cli/cmd_replace_multi.cpp`, `src/cli/cmd_tuptalk.cpp`,
`src/cli/cmd_where.cpp`, `src/cli/cmd_wsreport.cpp`,
`src/cli/console_posix.cpp`, `src/cli/expr/date/date_arith.cpp`,
`src/cli/relations_boot.cpp`, `src/cli/shell.cpp`,
`src/cli/xbase_error_codes.cpp`, `src/cnx/cnx_file.cpp`,
`src/dli/browsetui_integration.cpp`, `src/edu/edu_ascii_table.cpp`, and
`src/xbase/field_codec.cpp`, plus the related headers
`include/dli/browsetui_integration.hpp` and
`include/order_path_resolver.hpp`.

## Cleanup Order

Per the maintainer's decision, warning cleanup starts with the smaller Windows
set. After Windows is clean, rebuild `wsl-lean` and compare against this
baseline; Linux-only diagnostics can then be handled without mixing them with
warnings already exposed on Windows.

No warning count should be treated as a quality gate until the corresponding
build configuration deliberately enables that gate.
