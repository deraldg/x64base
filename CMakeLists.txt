cmake_minimum_required(VERSION 3.21)

# ============================================================
# Policies
# ============================================================

# Honor CMAKE_MSVC_RUNTIME_LIBRARY on MSVC.
if (POLICY CMP0091)
    cmake_policy(SET CMP0091 NEW)
endif()

# Honor *_ROOT hints more consistently.
if (POLICY CMP0144)
    cmake_policy(SET CMP0144 NEW)
endif()

# ============================================================
# Project
# ============================================================

project(DotTalkpp VERSION 0.6 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Default build type for single-config generators (e.g. Ninja).
if (NOT CMAKE_CONFIGURATION_TYPES AND NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE RelWithDebInfo CACHE STRING "Build type" FORCE)
endif()

# ============================================================
# Version Metadata
# ============================================================

set(DOTTALKPP_VERSION_LABEL "${PROJECT_VERSION}")

execute_process(
    COMMAND git -C "${CMAKE_SOURCE_DIR}" rev-parse --short=8 HEAD
    OUTPUT_VARIABLE DOTTALKPP_GIT_SHA
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
)
execute_process(
    COMMAND git -C "${CMAKE_SOURCE_DIR}" log -1 --format=%cs
    OUTPUT_VARIABLE DOTTALKPP_VERSION_DATE
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
)
execute_process(
    COMMAND git -C "${CMAKE_SOURCE_DIR}" status --porcelain
    OUTPUT_VARIABLE _dottalk_git_status
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
)

if (NOT DOTTALKPP_GIT_SHA)
    set(DOTTALKPP_GIT_SHA "nogit")
endif()

if (NOT DOTTALKPP_VERSION_DATE)
    string(TIMESTAMP DOTTALKPP_VERSION_DATE "%Y-%m-%d")
endif()

if (_dottalk_git_status)
    set(DOTTALKPP_GIT_DIRTY 1)
else()
    set(DOTTALKPP_GIT_DIRTY 0)
endif()

# ============================================================
# User Options
# ============================================================

option(DOTTALK_WITH_TV        "Enable Turbo Vision features" OFF)
option(DOTTALK_WITH_GUI       "Build GUI-neutral application services" OFF)
option(DOTTALK_WITH_WX        "Build wxWidgets windowed GUI frontend" OFF)
option(DOTTALK_TV_TESTS       "Build Turbo Vision probe tests" ON)
option(DOTTALK_WITH_INDEX     "Compatibility switch: enable LMDB-backed xindex support" OFF)
option(DOTTALK_WITH_EDUCATION "Compatibility switch: include the full education surface" ON)
option(BUILD_PYDOTTALK        "Build Python bindings" OFF)
option(DOTTALK_WITH_RELATIONS "Enable relationship support" ON)
option(DOTTALK_BUILD_METACOLLECT "Build the developer metadata collector" OFF)

# Transitional / developer-only command surfaces.
# Build profile: use this to steer capacity and diagnostics defaults.
set(DOTTALK_PROFILE "DEV" CACHE STRING "Build profile: DEV or PROD")
set_property(CACHE DOTTALK_PROFILE PROPERTY STRINGS DEV PROD)

# Maximum visible work areas for the shell / CLI layer.
# This may be overridden by the profile block below.
set(DOTTALK_MAX_AREA "" CACHE STRING "Maximum open work areas (empty = choose from profile)")

string(TOUPPER "${DOTTALK_PROFILE}" DOTTALK_PROFILE)
if (NOT DOTTALK_PROFILE STREQUAL "DEV" AND NOT DOTTALK_PROFILE STREQUAL "PROD")
    message(FATAL_ERROR "DOTTALK_PROFILE must be DEV or PROD")
endif()

set(_dottalk_with_dev_default ON)
set(_dottalk_extra_diagnostics_default ON)
if (DOTTALK_PROFILE STREQUAL "PROD")
    set(_dottalk_with_dev_default OFF)
    set(_dottalk_extra_diagnostics_default OFF)
endif()

# Transitional / developer-only command surfaces.
option(DOTTALK_WITH_DEV "Include developer tools and transitional aliases" ${_dottalk_with_dev_default})

# Authoritative engine/product selections.  The older boolean options remain
# as compatibility outputs so existing source guards and build scripts keep
# working while the product matrix becomes explicit.
set(DOTTALK_INDEX_MODE "" CACHE STRING "Index engine: NONE, LEGACY, or LMDB")
set_property(CACHE DOTTALK_INDEX_MODE PROPERTY STRINGS NONE LEGACY LMDB)

if (DOTTALK_INDEX_MODE STREQUAL "")
    if (DOTTALK_WITH_INDEX)
        set(DOTTALK_INDEX_MODE "LMDB" CACHE STRING "Index engine" FORCE)
    else()
        # Historical WITH_INDEX=OFF disabled LMDB only; legacy xindex remained.
        set(DOTTALK_INDEX_MODE "LEGACY" CACHE STRING "Index engine" FORCE)
    endif()
endif()
string(TOUPPER "${DOTTALK_INDEX_MODE}" DOTTALK_INDEX_MODE)
if (NOT DOTTALK_INDEX_MODE MATCHES "^(NONE|LEGACY|LMDB)$")
    message(FATAL_ERROR "DOTTALK_INDEX_MODE must be NONE, LEGACY, or LMDB")
endif()

if (DOTTALK_INDEX_MODE STREQUAL "NONE")
    set(DOTTALK_HAS_XINDEX OFF)
    set(DOTTALK_WITH_INDEX OFF CACHE BOOL "LMDB-backed xindex enabled" FORCE)
elseif (DOTTALK_INDEX_MODE STREQUAL "LEGACY")
    set(DOTTALK_HAS_XINDEX ON)
    set(DOTTALK_WITH_INDEX OFF CACHE BOOL "LMDB-backed xindex enabled" FORCE)
else()
    set(DOTTALK_HAS_XINDEX ON)
    set(DOTTALK_WITH_INDEX ON CACHE BOOL "LMDB-backed xindex enabled" FORCE)
endif()

set(DOTTALK_PRODUCT "DEVELOPMENT" CACHE STRING
    "Product composition: LEAN, PROFESSIONAL, EDUCATIONAL, or DEVELOPMENT")
set_property(CACHE DOTTALK_PRODUCT PROPERTY STRINGS LEAN PROFESSIONAL EDUCATIONAL DEVELOPMENT)
string(TOUPPER "${DOTTALK_PRODUCT}" DOTTALK_PRODUCT)
if (NOT DOTTALK_PRODUCT MATCHES "^(LEAN|PROFESSIONAL|EDUCATIONAL|DEVELOPMENT)$")
    message(FATAL_ERROR
        "DOTTALK_PRODUCT must be LEAN, PROFESSIONAL, EDUCATIONAL, or DEVELOPMENT")
endif()

set(DOTTALK_COMPONENT_EDU_ESSENTIALS ON)
set(DOTTALK_COMPONENT_LABTALK OFF)
set(DOTTALK_COMPONENT_MAINTENANCE OFF)
set(DOTTALK_COMPONENT_EXTERNAL OFF)
set(DOTTALK_COMPONENT_DEV OFF)

if (DOTTALK_PRODUCT STREQUAL "EDUCATIONAL")
    set(DOTTALK_COMPONENT_LABTALK ON)
elseif (DOTTALK_PRODUCT STREQUAL "DEVELOPMENT")
    set(DOTTALK_COMPONENT_LABTALK ON)
    set(DOTTALK_COMPONENT_MAINTENANCE ON)
    set(DOTTALK_COMPONENT_EXTERNAL ON)
    set(DOTTALK_COMPONENT_DEV ON)
endif()

set(DOTTALK_WITH_EDUCATION ${DOTTALK_COMPONENT_LABTALK}
    CACHE BOOL "Include full education surface" FORCE)
set(DOTTALK_WITH_DEV ${DOTTALK_COMPONENT_DEV}
    CACHE BOOL "Include developer tools and transitional aliases" FORCE)

foreach(_dottalk_bool IN ITEMS
    DOTTALK_HAS_XINDEX
    DOTTALK_WITH_INDEX
    DOTTALK_COMPONENT_EDU_ESSENTIALS
    DOTTALK_COMPONENT_LABTALK
    DOTTALK_COMPONENT_MAINTENANCE
    DOTTALK_COMPONENT_EXTERNAL
    DOTTALK_COMPONENT_DEV)
    if (${_dottalk_bool})
        add_compile_definitions(${_dottalk_bool}=1)
    else()
        add_compile_definitions(${_dottalk_bool}=0)
    endif()
endforeach()
unset(_dottalk_bool)

# Optional extra diagnostics.
option(DOTTALK_EXTRA_DIAGNOSTICS "Enable extra internal diagnostics/logging" ${_dottalk_extra_diagnostics_default})

# ============================================================
# Profile Resolution
# ============================================================

if (DOTTALK_PROFILE STREQUAL "DEV")
    if (DOTTALK_MAX_AREA STREQUAL "")
        set(DOTTALK_MAX_AREA "256" CACHE STRING "Maximum open work areas" FORCE)
    endif()
else()
    if (DOTTALK_MAX_AREA STREQUAL "")
        set(DOTTALK_MAX_AREA "128" CACHE STRING "Maximum open work areas" FORCE)
    endif()
endif()

# ============================================================
# Environment / Local Hints
# ============================================================

# Optional Turbo Vision local source hint.
set(_TV_ENV "$ENV{TVISION_ROOT}")
if (_TV_ENV)
    set(TVISION_ROOT "${_TV_ENV}" CACHE PATH "Local Turbo Vision source tree")
elseif (EXISTS "${CMAKE_SOURCE_DIR}/../tvision/CMakeLists.txt")
    set(TVISION_ROOT "${CMAKE_SOURCE_DIR}/../tvision" CACHE PATH "Local Turbo Vision source tree")
else()
    set(TVISION_ROOT "" CACHE PATH "Local Turbo Vision source tree")
endif()

# Optional vcpkg root hint.
set(_VCPKG_ENV "$ENV{VCPKG_ROOT}")
if (_VCPKG_ENV)
    set(VCPKG_ROOT "${_VCPKG_ENV}" CACHE PATH "vcpkg root (hint)")
else()
    set(VCPKG_ROOT "" CACHE PATH "vcpkg root (hint)")
endif()

# ============================================================
# MSVC / Windows Defaults
# ============================================================

if (MSVC)
    if (DEFINED VCPKG_TARGET_TRIPLET AND VCPKG_TARGET_TRIPLET MATCHES "static")
        set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
    else()
        set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
    endif()

    add_compile_definitions(
        NOMINMAX
        _CRT_SECURE_NO_WARNINGS
    )
endif()

# ============================================================
# Prefix Search Hints
# ============================================================

if (EXISTS "${CMAKE_BINARY_DIR}/vcpkg_installed/x64-windows-static")
    list(INSERT CMAKE_PREFIX_PATH 0 "${CMAKE_BINARY_DIR}/vcpkg_installed/x64-windows-static")
endif()

if (VCPKG_ROOT AND EXISTS "${VCPKG_ROOT}/installed/x64-windows-static")
    list(INSERT CMAKE_PREFIX_PATH 0 "${VCPKG_ROOT}/installed/x64-windows-static")
endif()

if (EXISTS "${CMAKE_BINARY_DIR}/vcpkg_installed/x64-windows")
    list(APPEND CMAKE_PREFIX_PATH "${CMAKE_BINARY_DIR}/vcpkg_installed/x64-windows")
endif()

if (VCPKG_ROOT AND EXISTS "${VCPKG_ROOT}/installed/x64-windows")
    list(APPEND CMAKE_PREFIX_PATH "${VCPKG_ROOT}/installed/x64-windows")
endif()

# ============================================================
# Main Source Tree
# ============================================================

include(CTest)

# ============================================================
# Build Vectors — generated capacity authority (AIF-044)
# ============================================================
# CMake owns selectable build inputs; configure_file emits the one compiled authority
# (generated/dottalk/build_vectors.hpp). include_directories() here (before any target)
# makes it findable by every subdirectory target that includes xbase.hpp.
include("${CMAKE_SOURCE_DIR}/config/build_vectors.cmake")
configure_file(
    "${CMAKE_SOURCE_DIR}/config/build_vectors.hpp.in"
    "${CMAKE_BINARY_DIR}/generated/dottalk/build_vectors.hpp"
    @ONLY)
configure_file(
    "${CMAKE_SOURCE_DIR}/config/build_vectors.json.in"
    "${CMAKE_BINARY_DIR}/generated/dottalk/build_vectors.json"
    @ONLY)
include_directories("${CMAKE_BINARY_DIR}/generated")

add_subdirectory(src)

# Add Python binding helper after code targets exist.
include(cmake/AddPydotTalkIfPresent.cmake OPTIONAL)

# ============================================================
# Turbo Vision Detection
# ============================================================

set(_tvision_found OFF)
set(_tvision_origin "not-found")

if (DOTTALK_WITH_TV)
    find_package(tvision CONFIG QUIET)

    if (TARGET tvision::tvision AND NOT TARGET tvision)
        add_library(tvision INTERFACE IMPORTED)
        target_link_libraries(tvision INTERFACE tvision::tvision)
    endif()

    if (TARGET tvision)
        set(_tvision_found ON)
        set(_tvision_origin "config-package")
    endif()

    if (NOT _tvision_found AND TVISION_ROOT AND EXISTS "${TVISION_ROOT}/CMakeLists.txt")
        message(STATUS "Turbo Vision: using local source at ${TVISION_ROOT}")
        add_subdirectory("${TVISION_ROOT}" _tvision_local EXCLUDE_FROM_ALL)

        if (TARGET tvision)
            set(_tvision_found ON)
            set(_tvision_origin "local-source")
        endif()
    endif()
endif()

# ============================================================
# SQLite Detection
# ============================================================

set(_sqlite_found OFF)
set(_sqlite_origin "not-found")

find_package(SQLite3 QUIET)
if (SQLite3_FOUND)
    set(_sqlite_found ON)
    set(_sqlite_origin "official")
else()
    find_package(unofficial-sqlite3 CONFIG QUIET)
    if (TARGET unofficial::sqlite3::sqlite3)
        set(_sqlite_found ON)
        set(_sqlite_origin "unofficial")
    endif()
endif()

# JSON is used by the DDL/schema command surface and is a core dependency.
find_package(nlohmann_json CONFIG REQUIRED)

# ============================================================
# Target Helper
# ============================================================

function(dottalk_apply_version_metadata target_name)
    if (NOT TARGET ${target_name})
        return()
    endif()

    target_compile_definitions(${target_name} PRIVATE
        DOTTALKPP_VERSION=\"${DOTTALKPP_VERSION_LABEL}\"
        DOTTALKPP_VERSION_DATE=\"${DOTTALKPP_VERSION_DATE}\"
        DOTTALKPP_GIT_SHA=\"${DOTTALKPP_GIT_SHA}\"
        DOTTALKPP_GIT_DIRTY=${DOTTALKPP_GIT_DIRTY}
    )
endfunction()

function(dottalk_apply_common_settings target_name)
    if (NOT TARGET ${target_name})
        return()
    endif()

    dottalk_apply_version_metadata(${target_name})

    target_compile_definitions(${target_name} PRIVATE
        DOTTALK_PROFILE_${DOTTALK_PROFILE}=1
        DOTTALK_MAX_AREA=${DOTTALK_MAX_AREA}
    )

    if (DOTTALK_EXTRA_DIAGNOSTICS)
        target_compile_definitions(${target_name} PRIVATE DOTTALK_EXTRA_DIAGNOSTICS=1)
    else()
        target_compile_definitions(${target_name} PRIVATE DOTTALK_EXTRA_DIAGNOSTICS=0)
    endif()

    if (DOTTALK_WITH_DEV)
        target_compile_definitions(${target_name} PRIVATE DOTTALK_WITH_DEV=1)
    else()
        target_compile_definitions(${target_name} PRIVATE DOTTALK_WITH_DEV=0)
    endif()

    if (DOTTALK_WITH_RELATIONS)
        target_compile_definitions(${target_name} PRIVATE DOTTALK_WITH_RELATIONS=1)
    else()
        target_compile_definitions(${target_name} PRIVATE DOTTALK_WITH_RELATIONS=0)
    endif()

    # Expression engine. During Phase 1 this is a facade over the existing CLI expression layer.
    if (TARGET xexpr)
        target_link_libraries(${target_name} PRIVATE xexpr)
        target_compile_definitions(${target_name} PRIVATE DOTTALK_XEXPR_AVAILABLE=1)
    else()
        target_compile_definitions(${target_name} PRIVATE DOTTALK_XEXPR_AVAILABLE=0)
    endif()

    if (DOTTALK_HAS_XINDEX)
        target_compile_definitions(${target_name} PRIVATE DOTTALK_HAS_XINDEX=1)
        if (TARGET xindex)
            target_link_libraries(${target_name} PRIVATE xindex)
        endif()
    else()
        target_compile_definitions(${target_name} PRIVATE DOTTALK_HAS_XINDEX=0)
    endif()

    if (_tvision_found)
        target_link_libraries(${target_name} PRIVATE tvision)
        target_compile_definitions(${target_name} PRIVATE DOTTALK_TV_AVAILABLE=1)
    else()
        target_compile_definitions(${target_name} PRIVATE DOTTALK_TV_AVAILABLE=0)
    endif()

    if (_sqlite_found)
        if (SQLite3_FOUND)
            target_link_libraries(${target_name} PRIVATE SQLite::SQLite3)
        else()
            target_link_libraries(${target_name} PRIVATE unofficial::sqlite3::sqlite3)
        endif()
        target_compile_definitions(${target_name} PRIVATE DOTTALK_SQLITE_AVAILABLE=1)
    else()
        target_compile_definitions(${target_name} PRIVATE DOTTALK_SQLITE_AVAILABLE=0)
    endif()

    target_link_libraries(${target_name} PRIVATE nlohmann_json::nlohmann_json)
endfunction()

# ============================================================
# Apply Target Settings
# ============================================================

if (TARGET dottalkpp)
    dottalk_apply_common_settings(dottalkpp)

    if (_tvision_found)
        message(STATUS "Turbo Vision ENABLED for 'dottalkpp' via ${_tvision_origin}.")
    elseif (DOTTALK_WITH_TV)
        message(WARNING "Turbo Vision NOT found; 'dottalkpp' will build WITHOUT TV.")
    else()
        message(STATUS "Turbo Vision explicitly disabled for 'dottalkpp'.")
    endif()

    if (DOTTALK_HAS_XINDEX)
        message(STATUS "Index engine ${DOTTALK_INDEX_MODE} ENABLED for 'dottalkpp'.")
    else()
        message(STATUS "Index engine NONE for 'dottalkpp'.")
    endif()

    if (DOTTALK_WITH_DEV)
        message(STATUS "Developer tools ENABLED for 'dottalkpp'.")
    else()
        message(STATUS "Developer tools DISABLED for 'dottalkpp'.")
    endif()

    if (DOTTALK_WITH_RELATIONS)
        message(STATUS "Relations ENABLED for 'dottalkpp'.")
    else()
        message(STATUS "Relations DISABLED for 'dottalkpp'.")
    endif()
endif()

foreach(_dottalk_gui_target IN ITEMS dottalk_wx dottalk_wx_next)
    dottalk_apply_version_metadata(${_dottalk_gui_target})
endforeach()
unset(_dottalk_gui_target)

if (BUILD_PYDOTTALK)
    if (TARGET pydottalk)
        dottalk_apply_common_settings(pydottalk)

        if (DOTTALK_HAS_XINDEX)
            message(STATUS "Index engine ${DOTTALK_INDEX_MODE} ENABLED for 'pydottalk'.")
        else()
            message(STATUS "Index engine NONE for 'pydottalk'.")
        endif()

        if (DOTTALK_WITH_RELATIONS)
            message(STATUS "Relations ENABLED for 'pydottalk'.")
        else()
            message(STATUS "Relations DISABLED for 'pydottalk'.")
        endif()
    else()
        message(WARNING "BUILD_PYDOTTALK=ON but target 'pydottalk' was not created.")
    endif()
endif()

# ============================================================
# Tests
# ============================================================

if (BUILD_TESTING)
    add_subdirectory(src/tests)
endif()

# ============================================================
# Product Package Allow-list
# ============================================================

# Product packaging is a third filter, separate from .gitignore (never
# version) and PROMOTE.manifest (publish now). It selects only git-tracked
# runtime inputs for this named product and never recursively copies the
# working tree.
string(TOLOWER "${DOTTALK_PRODUCT}" _dottalk_product_lower)
set(DOTTALK_PACKAGE_MANIFEST
    "${CMAKE_SOURCE_DIR}/config/package/${_dottalk_product_lower}.manifest")
if (NOT EXISTS "${DOTTALK_PACKAGE_MANIFEST}")
    message(FATAL_ERROR "Missing product package manifest: ${DOTTALK_PACKAGE_MANIFEST}")
endif()

find_package(Python3 COMPONENTS Interpreter REQUIRED)
set(_dottalk_package_dir "${CMAKE_BINARY_DIR}/package")
set(DOTTALK_PRODUCT_INVENTORY
    "${_dottalk_package_dir}/${_dottalk_product_lower}-product-inventory.json")
set(_dottalk_package_file_list
    "${_dottalk_package_dir}/${_dottalk_product_lower}-package-files.txt")
execute_process(
    COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_SOURCE_DIR}/tools/packaging/build_product_inventory.py"
            --root "${CMAKE_SOURCE_DIR}"
            --manifest "${DOTTALK_PACKAGE_MANIFEST}"
            --product "${DOTTALK_PRODUCT}"
            --output "${DOTTALK_PRODUCT_INVENTORY}"
            --cmake-list-output "${_dottalk_package_file_list}"
    RESULT_VARIABLE _dottalk_inventory_result
    OUTPUT_VARIABLE _dottalk_inventory_output
    ERROR_VARIABLE _dottalk_inventory_error
)
if (NOT _dottalk_inventory_result EQUAL 0)
    message(FATAL_ERROR
        "Product manifest validation failed: ${_dottalk_inventory_error}")
endif()
string(STRIP "${_dottalk_inventory_output}" _dottalk_inventory_output)
message(STATUS "Product package: ${_dottalk_inventory_output}")

file(STRINGS "${_dottalk_package_file_list}" DOTTALK_PACKAGE_FILES)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${DOTTALK_PACKAGE_MANIFEST}"
    "${CMAKE_SOURCE_DIR}/tools/packaging/build_product_inventory.py"
    ${DOTTALK_PACKAGE_FILES}
)

foreach(_dottalk_package_rel IN LISTS DOTTALK_PACKAGE_FILES)
    if (_dottalk_package_rel MATCHES "^dottalkpp/bin/(.+)$")
        get_filename_component(_dottalk_package_subdir
            "${CMAKE_MATCH_1}" DIRECTORY)
        set(_dottalk_package_dest "bin")
        if (NOT _dottalk_package_subdir STREQUAL "")
            string(APPEND _dottalk_package_dest "/${_dottalk_package_subdir}")
        endif()
    elseif (_dottalk_package_rel MATCHES "^dottalkpp/data/(.+)$")
        get_filename_component(_dottalk_package_subdir
            "${CMAKE_MATCH_1}" DIRECTORY)
        set(_dottalk_package_dest "data")
        if (NOT _dottalk_package_subdir STREQUAL "")
            string(APPEND _dottalk_package_dest "/${_dottalk_package_subdir}")
        endif()
    else()
        message(FATAL_ERROR
            "Package entry has no approved install mapping: ${_dottalk_package_rel}")
    endif()
    install(FILES "${CMAKE_SOURCE_DIR}/${_dottalk_package_rel}"
            DESTINATION "${_dottalk_package_dest}")
endforeach()

install(FILES "${CMAKE_SOURCE_DIR}/LICENSE" DESTINATION ".")
install(FILES "${DOTTALK_PACKAGE_MANIFEST}"
        DESTINATION "." RENAME "product.manifest")
install(FILES "${DOTTALK_PRODUCT_INVENTORY}"
        DESTINATION "." RENAME "product-inventory.json")

if (BUILD_TESTING)
    foreach(_dottalk_package_product IN ITEMS
        lean professional educational development)
        add_test(
            NAME "package_manifest_${_dottalk_package_product}"
            COMMAND "${Python3_EXECUTABLE}"
                    "${CMAKE_SOURCE_DIR}/tools/packaging/build_product_inventory.py"
                    --root "${CMAKE_SOURCE_DIR}"
                    --manifest
                    "${CMAKE_SOURCE_DIR}/config/package/${_dottalk_package_product}.manifest"
                    --product "${_dottalk_package_product}"
                    --output
                    "${_dottalk_package_dir}/${_dottalk_package_product}-test-inventory.json"
        )
    endforeach()
endif()

# ============================================================
# Summary
# ============================================================

if (TARGET xexpr)
    set(_xexpr_found ON)
else()
    set(_xexpr_found OFF)
endif()

message(STATUS "==== DotTalk++ / Build summary ====")
message(STATUS "  CMAKE_BUILD_TYPE      : ${CMAKE_BUILD_TYPE}")
message(STATUS "  DOTTALK_PROFILE       : ${DOTTALK_PROFILE}")
message(STATUS "  DOTTALK_MAX_AREA      : ${DOTTALK_MAX_AREA} (legacy/inert; engine uses build-vector areas=${DOTTALK_MAX_AREAS})")
message(STATUS "  DOTTALK_WITH_DEV      : ${DOTTALK_WITH_DEV}")
message(STATUS "  DOTTALK_EXTRA_DIAGN.  : ${DOTTALK_EXTRA_DIAGNOSTICS}")
message(STATUS "  DOTTALK_WITH_INDEX    : ${DOTTALK_WITH_INDEX}")
message(STATUS "  DOTTALK_INDEX_MODE    : ${DOTTALK_INDEX_MODE}")
message(STATUS "  DOTTALK_HAS_XINDEX    : ${DOTTALK_HAS_XINDEX}")
message(STATUS "  DOTTALK_PRODUCT       : ${DOTTALK_PRODUCT}")
message(STATUS "  DOTTALK_WITH_RELATIONS: ${DOTTALK_WITH_RELATIONS}")
message(STATUS "  DOTTALK_WITH_EDUCATION: ${DOTTALK_WITH_EDUCATION}")
message(STATUS "  xexpr found           : ${_xexpr_found}")
message(STATUS "  DOTTALK_WITH_TV       : ${DOTTALK_WITH_TV}")
message(STATUS "  DOTTALK_WITH_GUI      : ${DOTTALK_WITH_GUI}")
message(STATUS "  DOTTALK_WITH_WX       : ${DOTTALK_WITH_WX}")
message(STATUS "  DOTTALK_TV_TESTS      : ${DOTTALK_TV_TESTS}")
message(STATUS "  BUILD_PYDOTTALK       : ${BUILD_PYDOTTALK}")
message(STATUS "  BUILD_TESTING         : ${BUILD_TESTING}")
message(STATUS "  version metadata      : v${DOTTALKPP_VERSION_LABEL} ${DOTTALKPP_VERSION_DATE} ${DOTTALKPP_GIT_SHA} dirty=${DOTTALKPP_GIT_DIRTY}")
message(STATUS "  TVISION_ROOT          : ${TVISION_ROOT}")
message(STATUS "  VCPKG_ROOT            : ${VCPKG_ROOT}")
message(STATUS "  sqlite found          : ${_sqlite_found}")
message(STATUS "  sqlite origin         : ${_sqlite_origin}")
message(STATUS "  tvision found         : ${_tvision_found}")
message(STATUS "  tvision origin        : ${_tvision_origin}")
message(STATUS "===================================")

# BEGIN DOTARCH METACOLLECT CMAKE BUILDWIRE OPTION B V1
# METACOLLECT low-level metadata/reflection skeleton.
# Option B: dt_meta static library plus standalone developer executable.
# Safety boundary: no HELP DATA rebuild, no CMDHELPCHK mutation, no DBF writes.

if(DOTTALK_BUILD_METACOLLECT AND NOT TARGET dt_meta)
    add_library(dt_meta STATIC
        src/cli/expr/date/date_arith.cpp
        src/cli/expr/date/date_utils.cpp
        src/cli/expr/fn_date.cpp
        src/cli/expr/fn_numeric.cpp
        src/cli/expr/fn_string.cpp
        src/cli/expr/function_catalog.cpp
        src/datadict/ddict_read_helpers.cpp
        src/datadict/ddict_dbf_reader.cpp
        src/meta/metacollect.cpp
    )

    target_include_directories(dt_meta PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
    )
    target_include_directories(dt_meta PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src/cli/expr
    )

    target_compile_features(dt_meta PUBLIC cxx_std_17)
endif()

if(DOTTALK_BUILD_METACOLLECT AND NOT TARGET metacollect)
    add_executable(metacollect
        src/tools/metacollect_main.cpp
    )

    target_link_libraries(metacollect PRIVATE dt_meta)
endif()
# END DOTARCH METACOLLECT CMAKE BUILDWIRE OPTION B V1

if(TARGET dottalkpp)
    if (WIN32)
        install(TARGETS dottalkpp RUNTIME DESTINATION bin)
        # CMake sees LMDB as a runtime target. FindSQLite3 exposes SQLite's
        # import library only, while vcpkg app-local deployment copies the DLL
        # beside the executable, so include that file explicitly.
        install(FILES $<TARGET_RUNTIME_DLLS:dottalkpp>
                DESTINATION bin OPTIONAL)
        install(FILES "$<TARGET_FILE_DIR:dottalkpp>/sqlite3.dll"
                DESTINATION bin OPTIONAL)
    else()
        install(TARGETS dottalkpp RUNTIME DESTINATION bin)
    endif()
endif()
