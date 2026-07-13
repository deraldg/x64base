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

# The base IndexManager and file-backed legacy backends are required by
# DbArea even in the portable core profile. Only the direct LMDB backend source
# is removed when LMDB support is disabled; CdxBackend supplies its compiled
# no-LMDB implementation through its existing feature guard.
if (NOT DOTTALK_WITH_INDEX)
  list(FILTER XINDEX_SOURCES EXCLUDE REGEX ".*/lmdb_backend\\.cpp$")
endif()

add_library(xindex STATIC ${XINDEX_SOURCES})

# Explicitly add CNX sources that live outside src/xindex.
target_sources(xindex PRIVATE
  "${CMAKE_SOURCE_DIR}/src/xindex/cnx_backend.cpp"
  "${CMAKE_SOURCE_DIR}/src/cnx/cnx_document.cpp"
  "${CMAKE_SOURCE_DIR}/src/cnx/cnx_file.cpp"
)

target_include_directories(xindex
  PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_compile_definitions(xindex
  PUBLIC DOTTALK_WITH_INDEX=$<BOOL:${DOTTALK_WITH_INDEX}>
)

if (MSVC)
  target_compile_options(xindex PRIVATE /W4 /permissive- /MP)
else()
  target_compile_options(xindex PRIVATE -Wall -Wextra -Wpedantic)
endif()

if (DOTTALK_WITH_INDEX)
  find_package(unofficial-lmdb CONFIG REQUIRED)
  target_link_libraries(xindex PRIVATE unofficial::lmdb::lmdb)
endif()
