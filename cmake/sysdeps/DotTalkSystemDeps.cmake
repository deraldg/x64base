# DotTalkSystemDeps.cmake -- system-library (pkg-config) dependency path.
#
# WHAT THIS IS FOR. The tree's dependency calls are written against vcpkg's
# package names:
#
#   find_package(unofficial-lmdb   CONFIG REQUIRED) -> unofficial::lmdb::lmdb
#   find_package(unofficial-sodium CONFIG REQUIRED) -> unofficial-sodium::sodium
#   find_package(nlohmann_json     CONFIG REQUIRED) -> nlohmann_json::nlohmann_json
#
# The two "unofficial-*" names exist only in vcpkg. A distribution or Termux
# install ships lmdb.pc and libsodium.pc instead, so the `core` preset
# ("Portable core (system dependencies)") could not configure anywhere without
# vcpkg -- measured 2026-11-27 on Ubuntu 24.04 with liblmdb-dev and
# libsodium-dev installed: "Could not find a package configuration file
# provided by unofficial-lmdb", src/CMakeLists.txt:453.
#
# HOW. When DOTTALK_SYSTEM_DEPS is ON, this module builds GLOBAL imported
# targets carrying the vcpkg names from pkg-config (find_library fallback), and
# points <pkg>_DIR at tiny shim config files under cmake/sysdeps/ that only
# confirm those targets exist. Every existing find_package call site and every
# target_link_libraries line is left exactly as it was, so the vcpkg presets
# never reach this file and are unaffected.
#
# GLOBAL is required: the find_package calls live in four directory scopes
# (top level, src/, src/xindex/, cmake/AddUidefWorkbench.cmake), and a
# non-GLOBAL imported target made in one is invisible in the others.
#
# Primary consumer: the termux-core preset (native Android/Termux build).

option(DOTTALK_SYSTEM_DEPS
    "Resolve lmdb/libsodium/nlohmann_json from system libraries (pkg-config) instead of vcpkg packages" OFF)

# Native Termux detection. Termux's own CMake reports CMAKE_SYSTEM_NAME=Android
# when building natively on the device; TERMUX_VERSION is exported by the
# Termux app into every shell. Either is sufficient.
set(DOTTALK_TERMUX OFF)
if (CMAKE_SYSTEM_NAME STREQUAL "Android" OR DEFINED ENV{TERMUX_VERSION})
    set(DOTTALK_TERMUX ON)
endif()

if (NOT DOTTALK_SYSTEM_DEPS)
    return()
endif()

set(_dt_sysdeps_dir "${CMAKE_CURRENT_LIST_DIR}")
find_package(PkgConfig QUIET)

# _dt_sysdep(<target> <pkg-config module> <header> <library names...>)
function(_dt_sysdep target_name pc_module header)
    if (TARGET ${target_name})
        return()
    endif()
    string(MAKE_C_IDENTIFIER "${pc_module}" _id)
    string(TOUPPER "DT_PC_${_id}" _prefix)

    if (PKG_CONFIG_FOUND)
        pkg_check_modules(${_prefix} QUIET IMPORTED_TARGET GLOBAL ${pc_module})
    endif()

    add_library(${target_name} INTERFACE IMPORTED GLOBAL)
    if (${_prefix}_FOUND)
        target_link_libraries(${target_name} INTERFACE PkgConfig::${_prefix})
        message(STATUS "System deps: ${target_name} <- pkg-config ${pc_module} ${${_prefix}_VERSION}")
        return()
    endif()

    find_path(${_prefix}_INCLUDE_DIR NAMES ${header})
    find_library(${_prefix}_LIBRARY NAMES ${ARGN})
    if (NOT ${_prefix}_INCLUDE_DIR OR NOT ${_prefix}_LIBRARY)
        message(FATAL_ERROR
            "DOTTALK_SYSTEM_DEPS=ON but ${pc_module} was not found (pkg-config module "
            "'${pc_module}', header '${header}'). Install it, for example:\n"
            "  Termux:        pkg install liblmdb libsodium nlohmann-json sqlite pkg-config\n"
            "  Debian/Ubuntu: apt install liblmdb-dev libsodium-dev nlohmann-json3-dev libsqlite3-dev pkg-config")
    endif()
    target_include_directories(${target_name} INTERFACE "${${_prefix}_INCLUDE_DIR}")
    target_link_libraries(${target_name} INTERFACE "${${_prefix}_LIBRARY}")
    message(STATUS "System deps: ${target_name} <- ${${_prefix}_LIBRARY}")
endfunction()

_dt_sysdep(unofficial::lmdb::lmdb     lmdb      lmdb.h   lmdb)
_dt_sysdep(unofficial-sodium::sodium  libsodium sodium.h sodium)

set(unofficial-lmdb_DIR   "${_dt_sysdeps_dir}/unofficial-lmdb"   CACHE PATH "System-deps shim (DOTTALK_SYSTEM_DEPS)" FORCE)
set(unofficial-sodium_DIR "${_dt_sysdeps_dir}/unofficial-sodium" CACHE PATH "System-deps shim (DOTTALK_SYSTEM_DEPS)" FORCE)

# nlohmann_json upstream installs a real CMake package (Debian, Termux and
# Homebrew all ship it), so prefer that. Fall back to a header-only target only
# when no config package is present.
find_package(nlohmann_json CONFIG QUIET)
if (NOT nlohmann_json_FOUND AND NOT TARGET nlohmann_json::nlohmann_json)
    if (PKG_CONFIG_FOUND)
        pkg_check_modules(DT_PC_NLOHMANN_JSON QUIET nlohmann_json)
    endif()
    find_path(DT_NLOHMANN_JSON_INCLUDE_DIR NAMES nlohmann/json.hpp
        HINTS ${DT_PC_NLOHMANN_JSON_INCLUDE_DIRS})
    if (NOT DT_NLOHMANN_JSON_INCLUDE_DIR)
        message(FATAL_ERROR "DOTTALK_SYSTEM_DEPS=ON but nlohmann/json.hpp was not found.")
    endif()
    add_library(nlohmann_json::nlohmann_json INTERFACE IMPORTED GLOBAL)
    target_include_directories(nlohmann_json::nlohmann_json INTERFACE "${DT_NLOHMANN_JSON_INCLUDE_DIR}")
    set(nlohmann_json_DIR "${_dt_sysdeps_dir}/nlohmann_json" CACHE PATH "System-deps shim (DOTTALK_SYSTEM_DEPS)" FORCE)
    message(STATUS "System deps: nlohmann_json::nlohmann_json <- ${DT_NLOHMANN_JSON_INCLUDE_DIR} (header-only fallback)")
endif()
