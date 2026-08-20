cmake_minimum_required(VERSION 3.21)

# ============================================================================
# uidef_wx_demo -- build a wx frontend FROM A UIDEF DOCUMENT. AIF-120 R76.
#
# WHAT IS ACTUALLY BEING BUILT
#   A UIDEF document is a DBF "design table". This target treats it as a SOURCE:
#   author the document, generate C++ from it, compile the C++, link it against
#   the engine. `cmake --build` does all four. That is the point of the lane --
#   if the document is a source, the build should say so.
#
#       author_cases.py / author_frame.py   ->  FRAMEDEMO.DBF     (the document)
#       uidef_wx.py --stream                ->  framedemo_ui.cpp  (generated C++)
#       wx_host.cpp                         ->  the host (R72)
#
#   Nothing here is checked in except the scripts. The .DBF and the .cpp are
#   build outputs, which is why R75 made the fixtures reproducible rather than
#   committing them.
#
# STANDALONE, ON PURPOSE -- the pydottalk precedent (AIF-119)
#   Configuring the root build to produce one window would also build dottalkpp:
#   roughly 400 cmd_*.cpp, plus whatever else is on by default. pydottalk hit
#   exactly this in August and the answer was a standalone project that adds the
#   libraries it needs by DOTTALK_ROOT and lets them describe themselves. Same
#   answer here, same reason, and this file does not restate one line of
#   src/xbase, src/memo, src/xexpr or src/help.
#
# NOT `DOTTALK_WITH_WX`, AND NOT `DOTTALK_WITH_GUI`
#   The root CMakeLists already has both:
#       DOTTALK_WITH_GUI  "Build GUI-neutral application services"       OFF
#       DOTTALK_WITH_WX   "Build wxWidgets windowed GUI frontend"        OFF
#   Owner, 2026-08-20: those two build the **template samples** -- the wx GUIs
#   written in parallel as tests, for someone to copy from. They are not a
#   permanent product and this target is not one of them.
#
#   So this file defines its own target and does not attach to either switch.
#   Wiring `uidef_wx_demo` into `DOTTALK_WITH_WX` would fuse a generated frontend
#   into the sample's build and make one option mean two things. If the root
#   build should ever gain this target, the house pattern is a new option plus a
#   `cmake/AddUidefWxIfPresent.cmake` on the AddPydotTalkIfPresent model -- an
#   owner decision, not made here.
#
# THE ONE LIST THIS FILE DOES CARRY, AND WHY IT IS NOT A DUPLICATE
#   Measured with `nm` (R72 section 5c): a wx frontend that fills one grid needs
#   46 house translation units. 16 of them already belong to a library target and
#   are linked, never re-listed. The other 29 belong to NO library -- they are
#   globbed straight into the dottalkpp executable by src/CMakeLists.txt:92.
#   Listing them here is not a second copy of someone's list; it is the first
#   list those files have ever had.
#
#   The right end state is a `dottalk_cli_rt` static library that both dottalkpp
#   and this target link. That is an engine-build change, it belongs to whoever
#   owns src/CMakeLists.txt, and it is R61's boundary with a build consequence.
#   Until then this list drifts LOUDLY: a new dependency fails at link, not
#   silently at runtime.
# ============================================================================

if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
  set(UIDEF_STANDALONE TRUE)
else()
  set(UIDEF_STANDALONE FALSE)
endif()

if(UIDEF_STANDALONE)
  project(uidef_wx_demo LANGUAGES CXX)
  set(CMAKE_CXX_STANDARD 20)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
  set(CMAKE_CXX_EXTENSIONS OFF)
endif()

# ---- Locate the repository, and fail HERE if it is wrong -------------------
# gui/uidef/ -> gui/ -> repo root. Verified against a file that exists only at
# the root, so a wrong answer fails at configure rather than as a missing-header
# error two hundred lines into the build. Same check pydottalk makes.
if(NOT DEFINED DOTTALK_ROOT OR DOTTALK_ROOT STREQUAL "")
  get_filename_component(DOTTALK_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
  set(DOTTALK_ROOT "${DOTTALK_ROOT}" CACHE INTERNAL "DotTalk++ repository root")
endif()
if(NOT EXISTS "${DOTTALK_ROOT}/include/xbase.hpp")
  message(FATAL_ERROR
    "uidef: DOTTALK_ROOT resolved to '${DOTTALK_ROOT}', which does not contain "
    "include/xbase.hpp. Standalone expects this file at <repo>/gui/uidef/.")
endif()

option(DOTTALK_WITH_INDEX "Enable LMDB-backed xindex support" OFF)
set(UIDEF_DOCUMENT "FRAMEDEMO" CACHE STRING
    "UIDEF document stem to build a frontend from")

find_package(wxWidgets REQUIRED COMPONENTS core base)
include(${wxWidgets_USE_FILE})

find_package(Python3 REQUIRED COMPONENTS Interpreter)

# ---- Globals the ROOT build supplies silently ------------------------------
# AIF-118 measured this exact failure for pydottalk: "extracting it exposed four
# globals the parent had been supplying silently", and the FIRST item on that
# list was the generated `dottalk/build_vectors.hpp`. Standalone hits the same
# two, and neither is subtle once seen -- xbase.hpp includes build_vectors.hpp
# unconditionally, and src/help includes "cli/...", so both need a path nobody
# below the root sets.
#
# Reused, not restated: this runs the root's own build_vectors.cmake and its own
# .hpp.in template. A second hand-kept capacity table would be exactly the
# drift AIF-119 forbids.
include("${DOTTALK_ROOT}/config/build_vectors.cmake")
configure_file(
    "${DOTTALK_ROOT}/config/build_vectors.hpp.in"
    "${CMAKE_BINARY_DIR}/generated/dottalk/build_vectors.hpp"
    @ONLY)

# Directory-scoped ON PURPOSE: the library subprojects below do not take include
# paths as parameters, and the root build sets these the same way for the same
# reason (root CMakeLists.txt:300).
include_directories(
    "${CMAKE_BINARY_DIR}/generated"
    "${DOTTALK_ROOT}/include"
    "${DOTTALK_ROOT}/src"
    "${DOTTALK_ROOT}/src/cli")

# ---- The libraries describe themselves -------------------------------------
if(UIDEF_STANDALONE)
  add_subdirectory("${DOTTALK_ROOT}/src/xbase" "${CMAKE_BINARY_DIR}/xbase")
  add_subdirectory("${DOTTALK_ROOT}/src/memo"  "${CMAKE_BINARY_DIR}/memo")
  add_subdirectory("${DOTTALK_ROOT}/src/xexpr" "${CMAKE_BINARY_DIR}/xexpr")
  add_subdirectory("${DOTTALK_ROOT}/src/help"  "${CMAKE_BINARY_DIR}/help")
endif()

# ---- The 29 files no library owns -------------------------------------------
set(UIDEF_CLI_SOURCES
  src/cli/command_catalog.cpp      src/cli/command_output.cpp
  src/cli/db_tuple_stream.cpp      src/cli/memo_display.cpp
  src/cli/order_state.cpp          src/cli/output_router.cpp
  src/cli/predicate_chain.cpp      src/cli/predicate_eval.cpp
  src/cli/relations_status.cpp     src/cli/set_relations.cpp
  src/cli/table_state.cpp          src/cli/tuple_builder.cpp
  src/cli/workarea_util.cpp        src/cli/workareas_engine_bridge.cpp
  src/cli/expr/api.cpp             src/cli/expr/eval.cpp
  src/cli/expr/fn_custom.cpp       src/cli/expr/fn_date.cpp
  src/cli/expr/fn_numeric.cpp      src/cli/expr/fn_string.cpp
  src/cli/expr/glue_xbase.cpp      src/cli/expr/lexer.cpp
  src/cli/expr/parser.cpp          src/cli/expr/rhs_eval.cpp
  src/cli/expr/text_compare.cpp    src/cli/expr/value_eval.cpp
  src/cli/expr/date/date_arith.cpp src/cli/expr/date/date_utils.cpp
  src/common/path_resolver.cpp     src/common/path_state.cpp
)
list(TRANSFORM UIDEF_CLI_SOURCES PREPEND "${DOTTALK_ROOT}/")
foreach(_s IN LISTS UIDEF_CLI_SOURCES)
  if(NOT EXISTS "${_s}")
    message(FATAL_ERROR "uidef: closure source missing: ${_s}")
  endif()
endforeach()

# ---- The document is a build input ------------------------------------------
set(_doc "${CMAKE_CURRENT_BINARY_DIR}/${UIDEF_DOCUMENT}.DBF")
set(_gen "${CMAKE_CURRENT_BINARY_DIR}/${UIDEF_DOCUMENT}_ui.cpp")

add_custom_command(
  OUTPUT "${_doc}"
  COMMAND ${CMAKE_COMMAND} -E env PYTHONDONTWRITEBYTECODE=1
          ${Python3_EXECUTABLE} "${CMAKE_CURRENT_SOURCE_DIR}/author_frame.py"
          "${UIDEF_DOCUMENT}"
  WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
  DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/author_frame.py"
          "${CMAKE_CURRENT_SOURCE_DIR}/uidef.py"
  COMMENT "UIDEF: authoring document ${UIDEF_DOCUMENT}.DBF")

add_custom_command(
  OUTPUT "${_gen}"
  COMMAND ${CMAKE_COMMAND} -E env PYTHONDONTWRITEBYTECODE=1
          ${Python3_EXECUTABLE} "${CMAKE_CURRENT_SOURCE_DIR}/uidef_wx.py"
          "${_doc}" "${_gen}" --stream
  DEPENDS "${_doc}"
          "${CMAKE_CURRENT_SOURCE_DIR}/uidef_wx.py"
          "${CMAKE_CURRENT_SOURCE_DIR}/uidef.py"
  COMMENT "UIDEF: generating wx C++ from ${UIDEF_DOCUMENT}.DBF")

add_executable(uidef_wx_demo "${_gen}" wx_host.cpp ${UIDEF_CLI_SOURCES})

target_include_directories(uidef_wx_demo PRIVATE
  "${DOTTALK_ROOT}/include"
  "${DOTTALK_ROOT}/src"
  "${DOTTALK_ROOT}/src/cli"
  "${DOTTALK_ROOT}/generated")

target_link_libraries(uidef_wx_demo PRIVATE
  xbase memo xexpr dottalk_helpdata ${wxWidgets_LIBRARIES})

target_compile_definitions(uidef_wx_demo PRIVATE
  DOTTALK_WITH_INDEX=$<BOOL:${DOTTALK_WITH_INDEX}>)

if(EXISTS "${DOTTALK_ROOT}/cmake/MSVCWarnings.cmake")
  include("${DOTTALK_ROOT}/cmake/MSVCWarnings.cmake")
  target_enable_warnings(uidef_wx_demo)
endif()

message(STATUS "uidef: document=${UIDEF_DOCUMENT}  index=${DOTTALK_WITH_INDEX}  root=${DOTTALK_ROOT}")
