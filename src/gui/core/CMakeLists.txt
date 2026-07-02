add_library(dottalk_gui_core STATIC
  async_session.cpp
  gui_command_catalog.cpp
  gui_runtime_adapter.cpp
  gui_shell_runtime.cpp
  gui_workspace_format.cpp
  localization.cpp
  gui_cli_bridge.cpp
  session.cpp
)

target_include_directories(dottalk_gui_core
  PUBLIC
    "${CMAKE_SOURCE_DIR}/include"
  PRIVATE
    "${CMAKE_SOURCE_DIR}/src"
)

target_compile_features(dottalk_gui_core PUBLIC cxx_std_20)

target_compile_definitions(dottalk_gui_core PRIVATE
  DOTTALK_GUI_SOURCE_ROOT="${CMAKE_SOURCE_DIR}"
  DOTTALK_GUI_BINARY_DIR="${CMAKE_BINARY_DIR}"
)

if (TARGET xbase)
  target_link_libraries(dottalk_gui_core PUBLIC xbase)
else()
  message(FATAL_ERROR "dottalk_gui_core requires target xbase")
endif()

if (TARGET memo)
  target_link_libraries(dottalk_gui_core PUBLIC memo)
endif()

target_sources(dottalk_gui_core PRIVATE
  "${CMAKE_SOURCE_DIR}/src/common/path_state.cpp"
  "${CMAKE_SOURCE_DIR}/src/common/path_resolver.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/order_iterator.cpp"
  "${CMAKE_SOURCE_DIR}/src/cli/order_state.cpp"
)

if (MSVC)
  target_compile_options(dottalk_gui_core PRIVATE /W4 /permissive-)
else()
  target_compile_options(dottalk_gui_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

if (BUILD_TESTING)
  add_executable(dottalk_gui_core_async_smoke
    gui_test_async_session.cpp
  )

  target_link_libraries(dottalk_gui_core_async_smoke
    PRIVATE
      dottalk_gui_core
  )

  target_compile_features(dottalk_gui_core_async_smoke PRIVATE cxx_std_20)

  if (MSVC)
    target_compile_options(dottalk_gui_core_async_smoke PRIVATE /W4 /permissive-)
  else()
    target_compile_options(dottalk_gui_core_async_smoke PRIVATE -Wall -Wextra -Wpedantic)
  endif()

  add_test(NAME dottalk_gui_core_async_smoke COMMAND dottalk_gui_core_async_smoke)
endif()
