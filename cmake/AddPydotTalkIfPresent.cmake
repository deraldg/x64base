# AddPydotTalkIfPresent.cmake
# Drop-in helper for the root CMakeLists.txt line:
#   include(cmake/AddPydotTalkIfPresent.cmake OPTIONAL)
#
# Purpose:
#   Keep pydottalk out of broad source globs, while allowing
#   -DBUILD_PYDOTTALK=ON to opt into the Python binding target.
#
# Assumptions:
#   - root CMakeLists.txt defines option(BUILD_PYDOTTALK ...)
#   - bindings/pydottalk/CMakeLists.txt owns pybind11_add_module(pydottalk ...)

if(NOT DEFINED BUILD_PYDOTTALK)
  set(BUILD_PYDOTTALK OFF)
endif()

if(BUILD_PYDOTTALK)
  set(_pydottalk_dir "${CMAKE_SOURCE_DIR}/bindings/pydottalk")
  set(_pydottalk_cmake "${_pydottalk_dir}/CMakeLists.txt")

  if(EXISTS "${_pydottalk_cmake}")
    message(STATUS "pydottalk: enabling bindings from ${_pydottalk_dir}")
    add_subdirectory("${_pydottalk_dir}" "${CMAKE_BINARY_DIR}/bindings/pydottalk")
  else()
    message(WARNING
      "BUILD_PYDOTTALK=ON, but ${_pydottalk_cmake} was not found. "
      "Skipping pydottalk target."
    )
  endif()
endif()
