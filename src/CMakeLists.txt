# src/CMakeLists.txt — build the main CLI app and local libs when present.

# ---- Options ----------------------------------------------------------------
option(DOTTALK_WITH_TV "Build Turbo Vision UI (browse TUI, palette, etc.)" OFF)
option(DOTTALK_WITH_GUI "Build GUI-neutral application services" OFF)
option(DOTTALK_WITH_WX "Build wxWidgets windowed GUI frontend" OFF)
option(DOTTALK_BUILD_OLD_PALETTE "Build legacy palette demo sources (deprecated)" OFF)
option(DOTTALK_BUILD_PALETTE_EXE "Build standalone fox_palette.exe" OFF)

# Define only if not already provided by the top-level project.
if (NOT DEFINED DOTTALK_WITH_DEV)
  option(DOTTALK_WITH_DEV "Include developer tools and transitional aliases" ON)
endif()

# ---- MSVC runtime (fixes MSVC_RUNTIME_LIBRARY errors) ------------------------
# Use the official CMake mechanism (CMP0091 + CMAKE_MSVC_RUNTIME_LIBRARY).
# This avoids brittle /NODEFAULTLIB hacks and prevents mixed-runtime crashes.
if (MSVC)
  cmake_policy(SET CMP0091 NEW)
  # Multi-config safe: Release => /MD, Debug => /MDd
  # set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
endif()

# 0) Add internal libraries first (so targets exist before linking).
# xbase is the physical table engine and never consumes xindex.  Indexed
# compositions add xindex above it; table-only compositions omit it entirely.
if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/xbase/CMakeLists.txt")
  add_subdirectory(xbase)
endif()

if (DOTTALK_HAS_XINDEX AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/xindex/CMakeLists.txt")
  add_subdirectory(xindex)
endif()

if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/memo/CMakeLists.txt")
  add_subdirectory(memo)
endif()

# Phase 1: xexpr is a facade over the existing CLI expression layer.
# It must be added before dottalkpp so the target exists for top-level common settings.
if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/xexpr/CMakeLists.txt")
  add_subdirectory(xexpr)
endif()

# ---- DotTalk Value (DTV) domain foundation -----------------------------------
# Canonical domain value + qualified-reference parser + DataAddress (tuple/PDLC,
# AIF-038 shared Phase-0). Compile-only foundation; no DbArea/tuple/expression/array
# integration yet. Built as an isolated static lib (like xexpr) so both dottalkpp and
# the foundation smoke test can link it, and excluded from the dottalkpp glob above.
if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/value/value.cpp")
  add_library(dottalk_value STATIC
    value/value.cpp
    reference/qualified_reference.cpp
    reference/data_address.cpp
  )
  target_include_directories(dottalk_value PUBLIC "${CMAKE_SOURCE_DIR}/include")
  if (TARGET memo)
    target_link_libraries(dottalk_value PUBLIC memo)   # real dottalk::memo::MemoRef
  endif()
  if (MSVC)
    target_compile_options(dottalk_value PRIVATE /W4 /permissive-)
  else()
    target_compile_options(dottalk_value PRIVATE -Wall -Wextra -Wpedantic)
  endif()
endif()

# Legacy/experimental expr/browse subdirectories, if they exist.
# These paths are relative to src/. Keep them guarded; do not assume they exist.
if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/tests/expr/CMakeLists.txt")
  add_subdirectory(tests/expr)
endif()

if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/cli/expr/CMakeLists.txt")
  add_subdirectory(cli/expr)
endif()

if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/cli/browse/CMakeLists.txt")
  add_subdirectory(cli/browse)
endif()

# 1) Collect sources for the CLI under src/
file(GLOB_RECURSE DOTTALKPP_SOURCES CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_SOURCE_DIR}/*.c"
  "${CMAKE_CURRENT_SOURCE_DIR}/*.cc"
  "${CMAKE_CURRENT_SOURCE_DIR}/*.cxx"
  "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp"
)

# 2) Exclude subtrees that are built as separate libs (and bindings)
set(_EXCLUDE_DIRS
  "${CMAKE_CURRENT_SOURCE_DIR}/xbase"
  "${CMAKE_CURRENT_SOURCE_DIR}/xindex"
  "${CMAKE_CURRENT_SOURCE_DIR}/xexpr"
  "${CMAKE_CURRENT_SOURCE_DIR}/value"      # dottalk_value (DTV) built as a separate lib
  "${CMAKE_CURRENT_SOURCE_DIR}/reference"  # dottalk_value (DTV) built as a separate lib
  "${CMAKE_CURRENT_SOURCE_DIR}/memo"
  "${CMAKE_CURRENT_SOURCE_DIR}/meta"
  "${CMAKE_CURRENT_SOURCE_DIR}/tools"
# "${CMAKE_CURRENT_SOURCE_DIR}/help"
  "${CMAKE_CURRENT_SOURCE_DIR}/bindings"
  "${CMAKE_CURRENT_SOURCE_DIR}/binding"
  "${CMAKE_CURRENT_SOURCE_DIR}/python"
  "${CMAKE_CURRENT_SOURCE_DIR}/pybind"
  "${CMAKE_CURRENT_SOURCE_DIR}/pydottalk"
  "${CMAKE_CURRENT_SOURCE_DIR}/tests"     # avoid test mains
  "${CMAKE_CURRENT_SOURCE_DIR}/tv"        # TV isolated, not globbed
  "${CMAKE_CURRENT_SOURCE_DIR}/gui"       # GUI isolated, not globbed
  "${CMAKE_CURRENT_SOURCE_DIR}/palette"   # palette handled explicitly
  "${CMAKE_CURRENT_SOURCE_DIR}/build"     # exclude src in src/build
  "${CMAKE_CURRENT_SOURCE_DIR}/common"
)

# Filter without re-globbing (avoids glob cache issues)
set(DOTTALKPP_SOURCES_FILTERED "")

# Hard safety: never compile src/bindings into dottalkpp (those are optional modules)
foreach(_src IN LISTS DOTTALKPP_SOURCES)
  string(REPLACE "\\" "/" _src_norm "${_src}")
  if(_src_norm MATCHES "/src/bindings/")
    continue()
  endif()
  set(_keep TRUE)
  foreach(_dir IN LISTS _EXCLUDE_DIRS)
    if(_keep AND _src MATCHES "^${_dir}(/|\\\\)")
      set(_keep FALSE)
    endif()
  endforeach()
  if(_keep)
    list(APPEND DOTTALKPP_SOURCES_FILTERED "${_src}")
  endif()
endforeach()
set(DOTTALKPP_SOURCES "${DOTTALKPP_SOURCES_FILTERED}")

# Product component filtering -------------------------------------------------
# Source presence, command registration, and packaged data all follow the same
# top-level product selection.  Keep these lists explicit so a lean build is
# auditable from CMake rather than inferred from a large recursive glob.

# This legacy duplicate implements DbArea methods inside the CLI.  The physical
# implementation is owned exclusively by xbase.lib.
list(REMOVE_ITEM DOTTALKPP_SOURCES
  "${CMAKE_SOURCE_DIR}/src/cli/record_view.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/index_summary_none.cpp"
)

if (NOT DOTTALK_HAS_XINDEX)
  list(FILTER DOTTALKPP_SOURCES EXCLUDE REGEX "/src/cnx/")
  list(REMOVE_ITEM DOTTALKPP_SOURCES
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_ascend.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_buildlmdb.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_cdx.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_cnx.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_descend.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_index.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_indexseek.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_list_lmdb.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_lmdb.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_lmdb_dump.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_lmdb_util.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_rebuild.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_reindex.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_scx.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_seek.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_setcdx.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_setcnx.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_setindex.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_setlmdb.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_setorder.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/index_legacy.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/index_legacy_loader.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/index_resolver.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/index_summary.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/index_utils.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/inx_meta.cpp"
  )
  list(APPEND DOTTALKPP_SOURCES
    "${CMAKE_SOURCE_DIR}/src/cli/index_summary_none.cpp"
  )
endif()

if (NOT DOTTALK_WITH_INDEX)
  list(REMOVE_ITEM DOTTALKPP_SOURCES
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_buildlmdb.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_cdx.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_list_lmdb.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_lmdb.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_lmdb_dump.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_lmdb_util.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_setcdx.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_setlmdb.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/lmdb_shared_shim.cpp"
  )
endif()

set(DOTTALKPP_EDU_ESSENTIAL_SOURCES
  "${CMAKE_SOURCE_DIR}/src/edu/edu_ascii_table.cpp"
  "${CMAKE_SOURCE_DIR}/src/edu/edu_boolean.cpp"
  "${CMAKE_SOURCE_DIR}/src/edu/edu_evaluate.cpp"
  "${CMAKE_SOURCE_DIR}/src/edu/edu_formula.cpp"
  "${CMAKE_SOURCE_DIR}/src/edu/edu_normalize.cpp"
  "${CMAKE_SOURCE_DIR}/src/edu/edu_edit.cpp"
  "${CMAKE_SOURCE_DIR}/src/edu/edu_text.cpp"
)

if (NOT DOTTALK_COMPONENT_LABTALK)
  foreach(_src IN LISTS DOTTALKPP_SOURCES)
    string(REPLACE "\\" "/" _src_norm "${_src}")
    if (_src_norm MATCHES "/src/edu/")
      list(FIND DOTTALKPP_EDU_ESSENTIAL_SOURCES "${_src}" _essential_index)
      if (_essential_index EQUAL -1)
        list(REMOVE_ITEM DOTTALKPP_SOURCES "${_src}")
      endif()
    endif()
  endforeach()

  list(REMOVE_ITEM DOTTALKPP_SOURCES
    "${CMAKE_SOURCE_DIR}/src/cli/app_army.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/app_erp.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/app_paxon.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/case_catalog.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_codaysl.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_drawio.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_erp.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_idx.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_mcc.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_retro.cpp"
  )
endif()

if (NOT DOTTALK_COMPONENT_EXTERNAL)
  list(FILTER DOTTALKPP_SOURCES EXCLUDE REGEX "/src/ext/")
  list(FILTER DOTTALKPP_SOURCES EXCLUDE REGEX "/src/ms365/")
  list(REMOVE_ITEM DOTTALKPP_SOURCES
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_bang.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_image_display.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_sftp.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_web.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_zip.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/sys_ftp.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/sys_ssh.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/zip_backend_posix.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/zip_backend_win.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/zip_service.cpp"
  )
endif()

if (NOT DOTTALK_COMPONENT_MAINTENANCE)
  list(REMOVE_ITEM DOTTALKPP_SOURCES
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_bbox.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_ddict.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_maint.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_manstar.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_manual.cpp"
    "${CMAKE_SOURCE_DIR}/src/cli/cmd_msgmgr.cpp"
  )
endif()

# 2.5) Remove duplicates/legacy demos & probes that we control explicitly
foreach(_maybe IN ITEMS
  "${CMAKE_SOURCE_DIR}/src/cli/test_app.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/palette.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/palette_app.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_palette.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/tv_sanity_probe.cpp"
  "${CMAKE_SOURCE_DIR}/src/palette/cmd_fox_palette_entry.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/test_sql_where.cpp"
  "${CMAKE_SOURCE_DIR}/tests/test_where_cache_only.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_ttestapp.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_palette_shim.cpp"
)
  if (EXISTS "${_maybe}")
    list(REMOVE_ITEM DOTTALKPP_SOURCES "${_maybe}")
  endif()
endforeach()

# 2.6) Strip any extra mains under src that aren't the CLI entry
foreach(_extra_main IN ITEMS
  "${CMAKE_SOURCE_DIR}/src/dli/demo_main.cpp"
  "${CMAKE_SOURCE_DIR}/src/tests/test_sql_where.cpp"
  "${CMAKE_SOURCE_DIR}/src/tests/test_where_cache_only.cpp"
)
  if (EXISTS "${_extra_main}")
    list(REMOVE_ITEM DOTTALKPP_SOURCES "${_extra_main}")
  endif()
endforeach()

# 2.7) Dev-only / transitional command sources
# These are deliberately filename-specific, not subtree-wide.
# Public builds should exclude backend/dev helpers and transitional wrappers.
set(DOTTALKPP_DEV_SOURCES
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_buildlmdb.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_lmdb.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_lmdb_dump.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_lmdb_util.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_setlmdb.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_setcnx.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_setcdx.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_setindex.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_setorder.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_rebuild.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_indexseek.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_list_lmdb.cpp"
)

# Optional extra dev/debug helpers that may or may not exist in your tree
foreach(_dev_optional IN ITEMS
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_area51.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_cdx.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/cmd_cnx.cpp"
)
  if (EXISTS "${_dev_optional}")
    list(APPEND DOTTALKPP_DEV_SOURCES "${_dev_optional}")
  endif()
endforeach()

# These implementations remain linked because supported core commands delegate
# to them internally (for example COMMIT/REINDEX and the SET dispatcher).
# DOTTALK_WITH_DEV controls registration and visibility, not link availability.

# 2.8) Platform-select ABOUT info implementation
# Prevent both platform files from being compiled at once.
set(_ABOUT_INFO_WIN   "${CMAKE_SOURCE_DIR}/src/cli/about_info_win.cpp")
set(_ABOUT_INFO_POSIX "${CMAKE_SOURCE_DIR}/src/cli/about_info_posix.cpp")
set(_ABOUT_INFO_OLD   "${CMAKE_SOURCE_DIR}/src/cli/about_info.cpp")

list(REMOVE_ITEM DOTTALKPP_SOURCES
  "${_ABOUT_INFO_WIN}"
  "${_ABOUT_INFO_POSIX}"
  "${_ABOUT_INFO_OLD}"
)

if (WIN32)
  if (EXISTS "${_ABOUT_INFO_WIN}")
    list(APPEND DOTTALKPP_SOURCES "${_ABOUT_INFO_WIN}")
  else()
    message(FATAL_ERROR "Missing Windows ABOUT source: ${_ABOUT_INFO_WIN}")
  endif()
else()
  if (EXISTS "${_ABOUT_INFO_POSIX}")
    list(APPEND DOTTALKPP_SOURCES "${_ABOUT_INFO_POSIX}")
  else()
    message(FATAL_ERROR "Missing POSIX ABOUT source: ${_ABOUT_INFO_POSIX}")
  endif()
endif()

# 3) Define the main CLI executable
add_executable(dottalkpp ${DOTTALKPP_SOURCES})

# The runtime message catalog maintains LMDB mirrors even when the optional
# interactive index command surface is disabled.
find_package(unofficial-lmdb CONFIG REQUIRED)
target_link_libraries(dottalkpp PRIVATE unofficial::lmdb::lmdb)

# Common shared infrastructure extracted from CLI.
# src/common stays excluded from the glob above, so these are added explicitly.
target_sources(dottalkpp PRIVATE
  "${CMAKE_SOURCE_DIR}/src/common/path_state.cpp"
  "${CMAKE_SOURCE_DIR}/src/common/path_resolver.cpp"
)

# Compile-time flag for shell registration / help visibility.
if (DOTTALK_WITH_DEV)
  target_compile_definitions(dottalkpp PRIVATE DOTTALK_WITH_DEV=1)
else()
  target_compile_definitions(dottalkpp PRIVATE DOTTALK_WITH_DEV=0)
endif()

# NOTE:
# Removed: target_link_options(dottalkpp PRIVATE "/NODEFAULTLIB:LIBCMTD")
# Rationale: when combined with other libs, it can produce mixed runtime behavior
# and hard-to-diagnose crashes. The proper runtime selection is handled above.

# 3.1) Turbo Vision UI — build isolated lib and link only when enabled
if (DOTTALK_WITH_TV)
  add_subdirectory(tv)
  target_link_libraries(dottalkpp PRIVATE dottalk_tvui)
endif()

# 3.1b) Windowed GUI architecture: GUI-neutral core only in this phase.
if (DOTTALK_WITH_GUI OR DOTTALK_WITH_WX)
  add_subdirectory(gui/core)
endif()

if (DOTTALK_WITH_WX)
  add_subdirectory(gui/wx)
endif()

# 3.2) PALETTE command: by default, provide a stub so scripts don't explode
set(_gen_dir "${CMAKE_CURRENT_BINARY_DIR}/generated")
file(MAKE_DIRECTORY "${_gen_dir}")
set(_shim "${_gen_dir}/cmd_palette_stub.cpp")
file(WRITE "${_shim}" [=[
  #include <sstream>
  #include <iostream>
  namespace xbase { class DbArea; }
  extern "C" void cmd_PALETTE(xbase::DbArea&, std::istringstream&) {
      std::cerr << "PALETTE not available in this build.\n";
  }
]=])
target_sources(dottalkpp PRIVATE "${_shim}")

# 3.3) Optional standalone fox_palette.exe (opt-in)
if (DOTTALK_WITH_TV AND DOTTALK_BUILD_PALETTE_EXE)
  add_executable(fox_palette
    ${CMAKE_SOURCE_DIR}/palette/cmd_fox_palette.cpp
    ${CMAKE_SOURCE_DIR}/palette/fox_palette.cpp
  )
  target_include_directories(fox_palette PRIVATE
    ${CMAKE_SOURCE_DIR}/palette
    ${CMAKE_SOURCE_DIR}/include
  )
  if (TARGET xbase)
    target_link_libraries(fox_palette PRIVATE xbase)
  elseif (TARGET xindex)
    target_link_libraries(fox_palette PRIVATE xindex)
  endif()
  if (TARGET memo)
    target_link_libraries(fox_palette PRIVATE memo)
  endif()
  if (TARGET tvision::tvision)
    target_link_libraries(fox_palette PRIVATE tvision::tvision)
  else()
    message(FATAL_ERROR "DOTTALK_BUILD_PALETTE_EXE=ON but tvision::tvision target not found.")
  endif()
endif()

# 4) Header search paths
set(DOTTALKPP_PUBLIC_INC "${CMAKE_SOURCE_DIR}/include")
if (EXISTS "${DOTTALKPP_PUBLIC_INC}")
  target_include_directories(dottalkpp PUBLIC "${DOTTALKPP_PUBLIC_INC}")
endif()

# Private source-tree headers still referenced by some CLI glue headers.
# Beta portability fix.
target_include_directories(dottalkpp PRIVATE
  "${CMAKE_SOURCE_DIR}/src"
  "${CMAKE_SOURCE_DIR}/src/cli"
)

# 5) Warnings
if (MSVC)
  target_compile_options(dottalkpp PRIVATE /W4 /permissive- /MP)
else()
  target_compile_options(dottalkpp PRIVATE -Wall -Wextra -Wpedantic)
endif()

# 6) Link our libs
# NOTE: top-level CMake also applies shared links through dottalk_apply_common_settings().
# These local links are retained for compatibility with the existing src-level build.
if (TARGET xbase)
  target_link_libraries(dottalkpp PRIVATE xbase)
elseif (TARGET xindex)
  target_link_libraries(dottalkpp PRIVATE xindex)
endif()

if (TARGET xexpr)
  target_link_libraries(dottalkpp PRIVATE xexpr)
endif()

if (TARGET memo)
  target_link_libraries(dottalkpp PRIVATE memo)
endif()

if (TARGET dottalk_value)
  target_link_libraries(dottalkpp PRIVATE dottalk_value)
endif()

# 7) Build summary
message(STATUS "dottalkpp: DOTTALK_WITH_DEV = ${DOTTALK_WITH_DEV}")
message(STATUS "dottalkpp: DOTTALK_WITH_TV  = ${DOTTALK_WITH_TV}")
message(STATUS "dottalkpp: DOTTALK_WITH_GUI = ${DOTTALK_WITH_GUI}")
message(STATUS "dottalkpp: DOTTALK_WITH_WX  = ${DOTTALK_WITH_WX}")

# DD-089H guarded Data Dictionary helper source wiring.
# These files support the refactored DDICT read-only catalog command surface.
if(TARGET dottalkpp)
  target_sources(dottalkpp PRIVATE
    datadict/ddict_read_helpers.cpp
    datadict/ddict_catalog_paths.cpp
    datadict/ddict_dbf_reader.cpp
    datadict/ddict_object_resolver.cpp
  )
endif()
