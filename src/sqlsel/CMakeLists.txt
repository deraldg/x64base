# SQLsel is a consumer library over the typed tuple, expression, table, lock,
# and optional index seams. The command shell only routes text into this target.
add_library(sqlsel STATIC
  mode.cpp
  ../cli/sqlsel_statement.cpp
)

target_compile_features(sqlsel PUBLIC cxx_std_20)
target_include_directories(sqlsel
  PUBLIC "${CMAKE_SOURCE_DIR}/include"
  PRIVATE
    "${CMAKE_SOURCE_DIR}/src"
    "${CMAKE_SOURCE_DIR}/src/cli"
)

if (TARGET xbase)
  target_link_libraries(sqlsel PUBLIC xbase)
endif()
if (TARGET xexpr)
  target_link_libraries(sqlsel PUBLIC xexpr)
endif()
if (TARGET xindex)
  target_link_libraries(sqlsel PUBLIC xindex)
endif()
if (TARGET memo)
  target_link_libraries(sqlsel PUBLIC memo)
endif()

if (MSVC)
  target_compile_options(sqlsel PRIVATE /W4 /permissive-)
else()
  target_compile_options(sqlsel PRIVATE -Wall -Wextra -Wpedantic)
endif()
