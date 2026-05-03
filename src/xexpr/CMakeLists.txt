# src/xexpr/CMakeLists.txt
#
# Phase 1 xexpr facade.
#
# This target creates xexpr.lib while the existing expression implementation
# still lives under src/cli/expr.  The facade source files include CLI expr
# headers for now.  That is intentional during Phase 1 and should be removed
# after the expression engine is physically migrated into src/xexpr.

add_library(xexpr STATIC
  expr_value.cpp
  expr_eval.cpp
  function_registry.cpp
)

target_include_directories(xexpr
  PUBLIC
    "${CMAKE_SOURCE_DIR}/include"
  PRIVATE
    "${CMAKE_SOURCE_DIR}/src"
    "${CMAKE_SOURCE_DIR}/src/cli"
    "${CMAKE_CURRENT_SOURCE_DIR}"
)

# xexpr facade accepts DbArea context and may read fields through the existing
# CLI expression glue layer.  Keep this dependency one-way:
#   xexpr -> xbase
# not:
#   xbase -> xexpr
if (TARGET xbase)
  target_link_libraries(xexpr PUBLIC xbase)
endif()

if (MSVC)
  target_compile_options(xexpr PRIVATE /W4 /permissive-)
  target_compile_definitions(xexpr PRIVATE _CRT_SECURE_NO_WARNINGS NOMINMAX)
else()
  target_compile_options(xexpr PRIVATE -Wall -Wextra -Wpedantic)
endif()
