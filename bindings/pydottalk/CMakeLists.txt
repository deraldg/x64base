cmake_minimum_required(VERSION 3.21)

# ============================================================================
# pydottalk -- STANDALONE Python binding build.
#
# WHY THIS IS ITS OWN PROJECT (2026-08-17)
#   pydottalk used to be a switch inside the main build. When it moved here it
#   kept being a SUBDIRECTORY of that build, which meant `build_pydottalk.ps1`
#   configured the entire tree and then ran:
#
#       cmake --build <dir> --target dottalkpp pydottalk
#
#   So producing a 4-file Python module also built dottalkpp.exe -- roughly 400
#   cmd_*.cpp translation units -- plus dottalk_tvui.lib and the tvision vcpkg
#   package, because `tv` is on by default in build.ps1 and the wrapper never
#   passed -NoTV. Measured from the build log 2026-08-17.
#
#   The binding links THREE libraries: xbase, memo, xindex. It references
#   dottalkpp, tvision and dottalk_tvui exactly zero times. Everything else was
#   compiled and discarded.
#
# WHAT THIS FILE DELIBERATELY DOES NOT DO
#   It does not re-list the sources of xbase/memo/xindex. Those lists are
#   globbed in their own CMakeLists, and a second hand-kept copy here would be
#   the defect this repository keeps finding: two restatements that drift
#   silently, so a file added to src/xbase lands in the CLI and quietly goes
#   missing from the binding. Instead this adds those three directories as
#   subprojects and lets them describe themselves.
#
#   That is what DOTTALK_ROOT is for. The three libraries used to hardcode
#   ${CMAKE_SOURCE_DIR} for include/ and for three cnx sources, which is correct
#   only while the repo root is the top of the configure. They now read
#   DOTTALK_ROOT, which the root CMakeLists sets to the same value (no change to
#   that build) and which this file sets to the repo root two levels up.
#
# NOT A REPLACEMENT FOR THE MAIN BUILD
#   Use this when you want the module. Use the root build when you want the CLI,
#   the TUI, the BBS daemon or the test suite. Both produce the same .pyd from
#   the same sources; this one just refuses to build the parts nobody asked for.
# ============================================================================

# ---- TWO MODES, and the guard that tells them apart ------------------------
# This file is BOTH the standalone project and the subdirectory the root build
# adds via cmake/AddPydotTalkIfPresent.cmake. Getting that wrong is not subtle:
# calling add_subdirectory(src/xbase) while the root build has already created
# `xbase` is a duplicate-target error that breaks -DBUILD_PYDOTTALK=ON for the
# whole tree. Caught 2026-08-17 by checking who add_subdirectory's this file
# before trusting that "standalone" was the only caller.
#
# STANDALONE  : this directory is the top of the configure. Declare a project
#               and pull in the three libraries ourselves.
# SUBDIRECTORY: the root build owns the libraries and the toolchain. Touch
#               neither -- only define the module.
if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
  set(PYDOTTALK_STANDALONE TRUE)
else()
  set(PYDOTTALK_STANDALONE FALSE)
endif()

if(PYDOTTALK_STANDALONE)
  project(pydottalk_standalone LANGUAGES CXX)

  if(POLICY CMP0144)
    cmake_policy(SET CMP0144 NEW)
  endif()

  set(CMAKE_CXX_STANDARD 20)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
  set(CMAKE_CXX_EXTENSIONS OFF)
endif()

# ---- Position-independent code: REQUIRED on ELF, invisible on Windows -------
# The final artifact is a SHARED MODULE. On ELF platforms every object linked
# into a .so must be position-independent, and the static libraries this pulls
# in (xbase, memo, xindex) default to non-PIC.
#
# MEASURED 2026-08-17, first Linux configure of this project. Every translation
# unit compiled cleanly under GCC 11.4 -- xbase, memo, module.cpp and all three
# extra TUs -- and then the LINK failed:
#
#   relocation R_X86_64_TPOFF32 against
#   `xbase::trigger_hooks::(anonymous)::g_suppress_depth`
#   can not be used when making a shared object; recompile with -fPIC
#
# Note where it failed: not at configure, not at compile, but at link, naming a
# thread-local in an anonymous namespace three libraries deep. Nothing earlier
# hinted at it.
#
# NOT a lean-build defect. NOTHING in this repository sets PIC -- not the root
# CMakeLists, not the three library files. Windows never surfaces it because a
# DLL does not carry the constraint, so the root build with -DBUILD_PYDOTTALK=ON
# would hit exactly this the first time it ran on Linux. Set here because this
# is the file that builds a shared module; if the root build ever grows a Linux
# .so target it needs the same line.
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ---- Locate the repository -------------------------------------------------
# bindings/pydottalk/ -> bindings/ -> repo root. Verified by a file that only
# exists at the root, so a wrong answer fails here rather than as a confusing
# missing-header error 200 lines of output later.
if(NOT DEFINED DOTTALK_ROOT OR DOTTALK_ROOT STREQUAL "")
  get_filename_component(DOTTALK_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
  set(DOTTALK_ROOT "${DOTTALK_ROOT}" CACHE INTERNAL "DotTalk++ repository root")
endif()
if(NOT EXISTS "${DOTTALK_ROOT}/include/xbase.hpp")
  message(FATAL_ERROR
    "pydottalk: DOTTALK_ROOT resolved to '${DOTTALK_ROOT}', which does not "
    "contain include/xbase.hpp. Standalone expects this file to live at "
    "<repo>/bindings/pydottalk/; in the root build DOTTALK_ROOT comes from "
    "the top-level CMakeLists.")
endif()

# ---- Index mode: the HOUSE index and LMDB are different things -------------
# Corrected 2026-08-17 on owner challenge: "don't we distinguish between index
# and lmdb in our builds -- our house index system should ship even when lmdb
# doesn't". It does, and this file had flattened the distinction.
#
# src/xindex/CMakeLists.txt already encodes three states in its own comment:
#
#   LMDB   -- everything, including lmdb_backend.cpp; find_package(unofficial-lmdb)
#   LEGACY -- "retains the manager and file-backed index providers while omitting
#             the direct LMDB backend"  -> CNX, native CDX, index_manager, all of
#             it, with NO lmdb dependency at all
#   NONE   -- "never enters this directory or creates xindex"
#
# It selects between them with the DOTTALK_WITH_INDEX boolean, and compiles
# DOTTALK_HAS_XINDEX=1 next to DOTTALK_WITH_INDEX=0 for LEGACY -- literally
# "xindex exists, lmdb does not".
#
# THE BUG THIS REPLACES: this file wrapped add_subdirectory(xindex) in
# `if(DOTTALK_WITH_INDEX)`, which collapsed LEGACY into NONE. Passing
# -DDOTTALK_WITH_INDEX=OFF to work around a missing lmdb.h therefore threw away
# the house index engine as well, and the Linux run of 2026-08-17 was recorded
# as "index OFF" when what was actually wanted, and available, was LEGACY.
#
# DOTTALK_INDEX_MODE is the three-state name the root build already prints in
# its summary. DOTTALK_WITH_INDEX stays derived from it, because that is the
# variable the shared library file reads.
if(PYDOTTALK_STANDALONE)
  set(DOTTALK_INDEX_MODE "LMDB" CACHE STRING
      "Index engine: LMDB (full), LEGACY (house index, no lmdb), NONE (no xindex)")
  set_property(CACHE DOTTALK_INDEX_MODE PROPERTY STRINGS LMDB LEGACY NONE)

  if(NOT DOTTALK_INDEX_MODE MATCHES "^(LMDB|LEGACY|NONE)$")
    message(FATAL_ERROR
      "pydottalk: DOTTALK_INDEX_MODE='${DOTTALK_INDEX_MODE}' is not one of "
      "LMDB, LEGACY, NONE.")
  endif()

  if(DOTTALK_INDEX_MODE STREQUAL "LMDB")
    set(DOTTALK_WITH_INDEX ON)
  else()
    set(DOTTALK_WITH_INDEX OFF)   # LEGACY and NONE both omit the lmdb backend
  endif()
  message(STATUS "pydottalk: DOTTALK_INDEX_MODE=${DOTTALK_INDEX_MODE} "
                 "(lmdb backend: ${DOTTALK_WITH_INDEX})")
endif()

# ---- Python and pybind11 ---------------------------------------------------
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

set(_pybind11_hint_dirs
  "${DOTTALK_ROOT}/build-labtalk/vcpkg_installed/${VCPKG_TARGET_TRIPLET}/share/pybind11"
  "${DOTTALK_ROOT}/build-labtalk/vcpkg_installed/x64-windows/share/pybind11"
  "${DOTTALK_ROOT}/build/vcpkg_installed/${VCPKG_TARGET_TRIPLET}/share/pybind11"
  "${DOTTALK_ROOT}/build/vcpkg_installed/x64-windows/share/pybind11"
)
if(DEFINED ENV{pybind11_DIR})
  list(APPEND _pybind11_hint_dirs "$ENV{pybind11_DIR}")
endif()
foreach(_d IN LISTS _pybind11_hint_dirs)
  if(EXISTS "${_d}/pybind11Config.cmake")
    get_filename_component(_prefix "${_d}/.." ABSOLUTE)
    list(APPEND CMAKE_PREFIX_PATH "${_prefix}")
  endif()
endforeach()

find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
  find_package(pybind11 REQUIRED)
endif()

# ---- Engine feature flags the headers branch on ----------------------------
# STANDALONE ONLY. The root build emits each of these as =1 or =0 before
# add_subdirectory(src), and the engine headers test them. Leaving them
# UNDEFINED is the dangerous case, not a compile error: `#if DOTTALK_WITH_INDEX`
# treats an undefined name as 0, so the module would silently compile a
# different view of the same structs than the libraries it links -- a mismatch
# that links cleanly and misbehaves at runtime.
#
# So they are emitted explicitly, with the SAME =1/=0 discipline. Only
# DOTTALK_WITH_INDEX is a choice here; the component flags are OFF because this
# is a data binding, not the education or developer surface.
if(PYDOTTALK_STANDALONE)
  if(DOTTALK_WITH_INDEX)
    set(DOTTALK_HAS_XINDEX 1)
  else()
    set(DOTTALK_HAS_XINDEX 0)
  endif()

  foreach(_flag
      DOTTALK_HAS_XINDEX
      DOTTALK_WITH_INDEX
      DOTTALK_COMPONENT_EDU_ESSENTIALS
      DOTTALK_COMPONENT_LABTALK
      DOTTALK_COMPONENT_MAINTENANCE
      DOTTALK_COMPONENT_EXTERNAL
      DOTTALK_COMPONENT_DEV)
    if(${_flag})
      add_compile_definitions(${_flag}=1)
    else()
      add_compile_definitions(${_flag}=0)
    endif()
  endforeach()
  unset(_flag)
endif()

# ---- MSVC defaults the engine is written against ---------------------------
# STANDALONE ONLY -- the root build sets these before add_subdirectory(src) and
# every target beneath inherits them.
#
# NOMINMAX is not cosmetic here. <windows.h> defines max() as a function-like
# macro, which mangles `std::numeric_limits<T>::max()` into
# "C2589: '(': illegal token on right side of '::'". Measured 2026-08-17:
# src/xbase/dbf_file.cpp produced 30+ errors across 7 lines, none of which
# mentioned windows.h or max -- the diagnostics all pointed at syntax.
#
# The runtime-library selection matters just as much and fails later and worse:
# a module built against a different CRT than its dependencies links, loads,
# and then misbehaves at runtime rather than failing here.
if(PYDOTTALK_STANDALONE AND MSVC)
  if(DEFINED VCPKG_TARGET_TRIPLET AND VCPKG_TARGET_TRIPLET MATCHES "static")
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
  else()
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
  endif()

  add_compile_definitions(
    NOMINMAX
    _CRT_SECURE_NO_WARNINGS
  )
endif()

# ---- Build vectors: the generated capacity authority (AIF-044) -------------
# STANDALONE ONLY. xbase.hpp includes <dottalk/build_vectors.hpp>, which is not
# in the tree -- the root CMakeLists generates it from config/ and puts the
# generated/ directory on the include path for every target beneath it.
#
# A standalone configure that skipped this compiled nothing: every xbase TU
# failed with "Cannot open include file: 'dottalk/build_vectors.hpp'". Measured
# 2026-08-17, and worth stating plainly because the mistake was assuming the
# three libraries were self-describing when one of them depends on a header the
# PARENT emits.
#
# The inputs stay in config/ -- config/build_vectors.cmake and the two .in
# templates are the same files the root build reads, so the two configures
# cannot disagree about capacity. Only the emit is repeated, not the values.
if(PYDOTTALK_STANDALONE)
  if(NOT EXISTS "${DOTTALK_ROOT}/config/build_vectors.cmake")
    message(FATAL_ERROR
      "pydottalk: ${DOTTALK_ROOT}/config/build_vectors.cmake is missing; it "
      "defines the capacity vectors that generated/dottalk/build_vectors.hpp "
      "is emitted from.")
  endif()
  include("${DOTTALK_ROOT}/config/build_vectors.cmake")
  configure_file(
    "${DOTTALK_ROOT}/config/build_vectors.hpp.in"
    "${CMAKE_BINARY_DIR}/generated/dottalk/build_vectors.hpp"
    @ONLY)
  configure_file(
    "${DOTTALK_ROOT}/config/build_vectors.json.in"
    "${CMAKE_BINARY_DIR}/generated/dottalk/build_vectors.json"
    @ONLY)
  include_directories("${CMAKE_BINARY_DIR}/generated")

  # Assert the emit actually happened. configure_file does not fail loudly if
  # the template is unreadable, and a missing header here reappears 200 lines
  # later as a compile error naming xbase.hpp rather than this step.
  if(NOT EXISTS "${CMAKE_BINARY_DIR}/generated/dottalk/build_vectors.hpp")
    message(FATAL_ERROR
      "pydottalk: build_vectors.hpp was not generated into "
      "${CMAKE_BINARY_DIR}/generated/dottalk/.")
  endif()
  message(STATUS "pydottalk: build vectors emitted "
                 "(areas=${DOTTALK_MAX_AREAS} fields=${DOTTALK_MAX_FIELDS})")
endif()

# ---- The three libraries ---------------------------------------------------
# STANDALONE ONLY. In the root build these targets already exist; adding their
# directories again is a duplicate-target error, and it would break
# -DBUILD_PYDOTTALK=ON for the entire tree rather than just this module.
if(PYDOTTALK_STANDALONE)
  add_subdirectory("${DOTTALK_ROOT}/src/xbase"  "${CMAKE_BINARY_DIR}/_xbase")
  if(DOTTALK_INDEX_MODE STREQUAL "NONE")
    message(STATUS "pydottalk: index NONE -- xindex not built")
  else()
    add_subdirectory("${DOTTALK_ROOT}/src/xindex" "${CMAKE_BINARY_DIR}/_xindex")
  endif()
  add_subdirectory("${DOTTALK_ROOT}/src/memo"   "${CMAKE_BINARY_DIR}/_memo")
endif()

foreach(_lib xbase memo)
  if(NOT TARGET ${_lib})
    message(FATAL_ERROR
      "pydottalk: target '${_lib}' does not exist. Standalone builds create it "
      "from ${DOTTALK_ROOT}/src/${_lib}; inside the root build it comes from "
      "src/CMakeLists.txt. Neither happened.")
  endif()
endforeach()

# ---- Supporting translation units the module needs -------------------------
# Three files from the CLI/common trees carry symbols the module references.
# Checked individually so a rename reports WHICH file moved and what it
# provides, rather than failing at link with an undefined symbol.
set(_extra_srcs
  "src/cli/order_state.cpp|orderstate::*"
  "src/common/path_resolver.cpp|dottalk::paths::*"
  "src/common/path_state.cpp|dottalk::paths::state / get_slot"
)
set(PYDOTTALK_EXTRA_SOURCES "")
foreach(_entry IN LISTS _extra_srcs)
  string(REPLACE "|" ";" _parts "${_entry}")
  list(GET _parts 0 _rel)
  list(GET _parts 1 _why)
  if(NOT EXISTS "${DOTTALK_ROOT}/${_rel}")
    message(FATAL_ERROR "pydottalk: missing ${_rel} (needed for ${_why}).")
  endif()
  list(APPEND PYDOTTALK_EXTRA_SOURCES "${DOTTALK_ROOT}/${_rel}")
endforeach()

# ---- The module ------------------------------------------------------------
pybind11_add_module(pydottalk
  "${CMAKE_CURRENT_SOURCE_DIR}/src/module.cpp"
  ${PYDOTTALK_EXTRA_SOURCES}
)

target_include_directories(pydottalk PRIVATE "${DOTTALK_ROOT}/include")
target_compile_features(pydottalk PRIVATE cxx_std_20)

target_link_libraries(pydottalk PRIVATE xbase memo)
target_compile_definitions(pydottalk PRIVATE HAVE_XBASE=1)
# Link xindex whenever the TARGET exists, not when the lmdb backend is on.
#
# This guard used to read `if(DOTTALK_WITH_INDEX AND TARGET xindex)`, which is
# the same conflation the index-mode block above corrects: in LEGACY,
# DOTTALK_WITH_INDEX is OFF (no lmdb) while xindex very much exists.
#
# MEASURED 2026-08-17, and the first explanation was wrong. The LEGACY and NONE
# artifacts came out byte-identical at 665,336 B, which looked like "compiled 22
# TUs and linked none of them". It is not. `nm -D` on both shows the same
# symbols, and the real reason is simpler: **module.cpp does not reference the
# index at all** -- no xindex, index_manager, set_order, seek, cnx or cdx. A
# static library only contributes objects that resolve undefined symbols, so
# linking it correctly changes nothing.
#
# So the mode currently makes NO difference to this artifact, and saying
# otherwise would be a false claim in a build file. It matters the moment the
# binding gains index operations -- `seek` / `set_order` are listed as unproven
# milestones in PYDOTTALK_STARTER_README.md -- and the guard is correct in
# advance rather than needing to be rediscovered then.
if(TARGET xindex)
  target_link_libraries(pydottalk PRIVATE xindex)
endif()

set_target_properties(pydottalk PROPERTIES
  CXX_VISIBILITY_PRESET "default"
  VISIBILITY_INLINES_HIDDEN OFF
)

foreach(cfg IN ITEMS Debug Release RelWithDebInfo MinSizeRel)
  string(TOUPPER "${cfg}" CFGU)
  set_target_properties(pydottalk PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY_${CFGU} "${CMAKE_BINARY_DIR}/python"
    LIBRARY_OUTPUT_DIRECTORY_${CFGU} "${CMAKE_BINARY_DIR}/python"
    ARCHIVE_OUTPUT_DIRECTORY_${CFGU} "${CMAKE_BINARY_DIR}/python"
  )
endforeach()

include(GNUInstallDirs)
install(TARGETS pydottalk
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

# ---- Smokes ----------------------------------------------------------------
# Same two the subdirectory build registered. They run against the built module
# only; anything needing dottalkpp.exe belongs to the root build, not here.
if(PYDOTTALK_STANDALONE)
  include(CTest)
endif()
if(BUILD_TESTING)
  foreach(_t pydottalk_smoke_readonly pydottalk_xbase_contract_smoke)
    if(EXISTS "${DOTTALK_ROOT}/bindings/${_t}.py")
      add_test(NAME ${_t}
        COMMAND ${CMAKE_COMMAND} -E env
          "PYDOTTALK_BIN=$<TARGET_FILE_DIR:pydottalk>"
          "${Python3_EXECUTABLE}" "${DOTTALK_ROOT}/bindings/${_t}.py")
      set_tests_properties(${_t} PROPERTIES
        LABELS "pydottalk;xbase;smoke"
        WORKING_DIRECTORY "${DOTTALK_ROOT}")
    endif()
  endforeach()
endif()

if(PYDOTTALK_STANDALONE)
  message(STATUS "pydottalk: STANDALONE configure, root=${DOTTALK_ROOT}, "
                 "index=${DOTTALK_WITH_INDEX} -- no CLI, no TUI, no BBS")
else()
  message(STATUS "pydottalk: subdirectory of the root build "
                 "(libraries and options owned by the parent)")
endif()
