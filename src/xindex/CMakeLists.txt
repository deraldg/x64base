# File: src/xindex/CMakeLists.txt
# Purpose: Build the xindex library and wire optional LMDB-backed index
#          support.
# Boundary: Keep backend selection and library linkage here; command/runtime
#           policy lives in the CLI and engine layers.

cmake_minimum_required(VERSION 3.20)

file(GLOB_RECURSE XINDEX_SOURCES CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_SOURCE_DIR}/*.c"
  "${CMAKE_CURRENT_SOURCE_DIR}/*.cc"
  "${CMAKE_CURRENT_SOURCE_DIR}/*.cxx"
  "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp"
)

# LEGACY retains the manager and file-backed index providers while omitting the
# direct LMDB backend. NONE never enters this directory or creates xindex.
if (NOT DOTTALK_WITH_INDEX)
  list(FILTER XINDEX_SOURCES EXCLUDE REGEX ".*/lmdb_backend\\.cpp$")
endif()

add_library(xindex STATIC ${XINDEX_SOURCES})

# Explicitly add CNX sources that live outside src/xindex.
target_sources(xindex PRIVATE
  "${DOTTALK_ROOT}/src/xindex/cnx_backend.cpp"
  "${DOTTALK_ROOT}/src/cnx/cnx_document.cpp"
  "${DOTTALK_ROOT}/src/cnx/cnx_file.cpp"
)

# ...and CDX, for the same reason, which took three link failures to notice.
# AIF-120, 2026-08-20.
#
# `cdx_native_backend.cpp` IS in this directory and references
# xindex::CdxDocument:: and cdxfile::, whose bodies live in src/cdx and belong to
# no library. dottalkpp never noticed: its own glob over src/ compiles src/cdx
# directly, so its objects satisfy the references and xindex.lib's members are
# never pulled. Every OTHER closure that links xindex fails at link:
#
#   dottalk_bbsd  hand-globbed src/cdx/*.cpp into its own sources (CMakeLists.txt)
#   dottalk_wb    11 unresolved externals, all CdxDocument:: and cdxfile::
#
# Fixed where CNX was fixed rather than hand-copied a third time. Same guarantee
# as the CNX lines above: dottalkpp keeps compiling its own copies and the linker
# never pulls these members for it, so nothing about that target changes.
target_sources(xindex PRIVATE
  "${DOTTALK_ROOT}/src/cdx/cdx_document.cpp"
  "${DOTTALK_ROOT}/src/cdx/cdx_file.cpp"
)

target_include_directories(xindex
  PUBLIC
    ${DOTTALK_ROOT}/include
)

target_compile_definitions(xindex
  PUBLIC
    DOTTALK_HAS_XINDEX=1
    DOTTALK_WITH_INDEX=$<BOOL:${DOTTALK_WITH_INDEX}>
)

target_link_libraries(xindex PUBLIC xbase)

if (MSVC)
  target_compile_options(xindex PRIVATE /W4 /permissive- /MP)
else()
  target_compile_options(xindex PRIVATE -Wall -Wextra -Wpedantic)
endif()

if (DOTTALK_WITH_INDEX)
  find_package(unofficial-lmdb CONFIG REQUIRED)
  target_link_libraries(xindex PRIVATE unofficial::lmdb::lmdb)
endif()
