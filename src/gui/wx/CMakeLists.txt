find_package(wxWidgets CONFIG QUIET COMPONENTS core base)

if (NOT wxWidgets_FOUND)
  set(_dottalk_wxrc_hints)
  if (VCPKG_ROOT)
    list(APPEND _dottalk_wxrc_hints
      "${VCPKG_ROOT}/installed/x64-windows/tools/wxwidgets/wxrc.exe"
      "${VCPKG_ROOT}/installed/x64-windows-static/tools/wxwidgets/wxrc.exe"
    )
  endif()
  if (CMAKE_PREFIX_PATH)
    foreach(_dottalk_prefix IN LISTS CMAKE_PREFIX_PATH)
      list(APPEND _dottalk_wxrc_hints
        "${_dottalk_prefix}/tools/wxwidgets/wxrc.exe"
      )
    endforeach()
  endif()
  foreach(_dottalk_wxrc IN LISTS _dottalk_wxrc_hints)
    if (EXISTS "${_dottalk_wxrc}")
      set(wxWidgets_wxrc_EXECUTABLE "${_dottalk_wxrc}" CACHE FILEPATH "wxWidgets resource compiler" FORCE)
      break()
    endif()
  endforeach()
  unset(_dottalk_wxrc)
  unset(_dottalk_prefix)
  unset(_dottalk_wxrc_hints)

  find_package(wxWidgets QUIET COMPONENTS core base)
endif()

if (NOT wxWidgets_FOUND)
  message(FATAL_ERROR
    "DOTTALK_WITH_WX=ON requires wxWidgets with the core and base components. "
    "Install wxWidgets for this toolchain, or configure with DOTTALK_WITH_WX=OFF "
    "to build only the GUI-neutral dottalk_gui_core target."
  )
endif()

set(DOTTALK_WX_SOURCES
  main.cpp
  main_frame.cpp
)

add_executable(dottalk_wx WIN32 ${DOTTALK_WX_SOURCES})
add_executable(dottalk_wx_next WIN32 ${DOTTALK_WX_SOURCES})

if (wxWidgets_USE_FILE AND NOT TARGET wx::core)
  include("${wxWidgets_USE_FILE}")
endif()

target_include_directories(dottalk_wx
  PRIVATE
    "${CMAKE_SOURCE_DIR}/include"
    ${wxWidgets_INCLUDE_DIRS}
)
target_include_directories(dottalk_wx_next
  PRIVATE
    "${CMAKE_SOURCE_DIR}/include"
    ${wxWidgets_INCLUDE_DIRS}
)

target_compile_features(dottalk_wx PRIVATE cxx_std_20)
target_compile_features(dottalk_wx_next PRIVATE cxx_std_20)

target_link_libraries(dottalk_wx
  PRIVATE
    dottalk_gui_core
    ${wxWidgets_LIBRARIES}
)
target_link_libraries(dottalk_wx_next
  PRIVATE
    dottalk_gui_core
    ${wxWidgets_LIBRARIES}
)

if (WIN32)
  set(_dottalk_wx_runtime_prefixes)

  foreach(_dottalk_prefix IN LISTS CMAKE_PREFIX_PATH)
    file(TO_CMAKE_PATH "${_dottalk_prefix}" _dottalk_normal_prefix)
    if (IS_DIRECTORY "${_dottalk_normal_prefix}")
      list(APPEND _dottalk_wx_runtime_prefixes "${_dottalk_normal_prefix}")
    endif()
  endforeach()

  if (VCPKG_ROOT)
    file(TO_CMAKE_PATH "${VCPKG_ROOT}" _dottalk_vcpkg_root)
    foreach(_dottalk_triplet x64-windows)
      if (IS_DIRECTORY "${_dottalk_vcpkg_root}/installed/${_dottalk_triplet}")
        list(APPEND _dottalk_wx_runtime_prefixes "${_dottalk_vcpkg_root}/installed/${_dottalk_triplet}")
      endif()
    endforeach()
  endif()

  if (wxWidgets_DIR)
    file(TO_CMAKE_PATH "${wxWidgets_DIR}" _dottalk_wx_dir)
    get_filename_component(_dottalk_wx_share_dir "${_dottalk_wx_dir}" DIRECTORY)
    get_filename_component(_dottalk_wx_prefix "${_dottalk_wx_share_dir}" DIRECTORY)
    if (IS_DIRECTORY "${_dottalk_wx_prefix}")
      list(APPEND _dottalk_wx_runtime_prefixes "${_dottalk_wx_prefix}")
    endif()
  endif()

  if (_dottalk_wx_runtime_prefixes)
    list(REMOVE_DUPLICATES _dottalk_wx_runtime_prefixes)
  endif()

  set(_dottalk_wx_runtime_dlls)
  foreach(_dottalk_prefix IN LISTS _dottalk_wx_runtime_prefixes)
    if (IS_DIRECTORY "${_dottalk_prefix}/bin")
      file(GLOB _dottalk_prefix_runtime_dlls CONFIGURE_DEPENDS
        "${_dottalk_prefix}/bin/wx*.dll"
        "${_dottalk_prefix}/bin/zlib*.dll"
        "${_dottalk_prefix}/bin/pcre2-16.dll"
        "${_dottalk_prefix}/bin/jpeg*.dll"
        "${_dottalk_prefix}/bin/libpng*.dll"
        "${_dottalk_prefix}/bin/tiff*.dll"
        "${_dottalk_prefix}/bin/liblzma*.dll"
        "${_dottalk_prefix}/bin/libwebp*.dll"
        "${_dottalk_prefix}/bin/libsharpyuv*.dll"
      )
      file(GLOB _dottalk_prefix_wx_required_dlls CONFIGURE_DEPENDS
        "${_dottalk_prefix}/bin/wxbase*_vc_*_custom.dll"
        "${_dottalk_prefix}/bin/wxmsw*_core_vc_*_custom.dll"
      )
      list(APPEND _dottalk_prefix_runtime_dlls ${_dottalk_prefix_wx_required_dlls})
      list(APPEND _dottalk_wx_runtime_dlls ${_dottalk_prefix_runtime_dlls})
    endif()
  endforeach()

  if (_dottalk_wx_runtime_dlls)
    list(REMOVE_DUPLICATES _dottalk_wx_runtime_dlls)
    add_custom_command(TARGET dottalk_wx POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${_dottalk_wx_runtime_dlls}
        $<TARGET_FILE_DIR:dottalk_wx>
      COMMAND_EXPAND_LISTS
      COMMENT "Copying wxWidgets runtime DLLs for dottalk_wx"
    )
    add_custom_command(TARGET dottalk_wx_next POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${_dottalk_wx_runtime_dlls}
        $<TARGET_FILE_DIR:dottalk_wx_next>
      COMMAND_EXPAND_LISTS
      COMMENT "Copying wxWidgets runtime DLLs for dottalk_wx_next"
    )
  endif()

  unset(_dottalk_prefix_runtime_dlls)
  unset(_dottalk_prefix_wx_required_dlls)
  unset(_dottalk_wx_runtime_dlls)
  unset(_dottalk_wx_prefix)
  unset(_dottalk_wx_share_dir)
  unset(_dottalk_wx_dir)
  unset(_dottalk_triplet)
  unset(_dottalk_vcpkg_root)
  unset(_dottalk_normal_prefix)
  unset(_dottalk_prefix)
  unset(_dottalk_wx_runtime_prefixes)
endif()

if (MSVC)
  target_compile_options(dottalk_wx PRIVATE /W4 /permissive-)
  target_compile_options(dottalk_wx_next PRIVATE /W4 /permissive-)
else()
  target_compile_options(dottalk_wx PRIVATE -Wall -Wextra -Wpedantic)
  target_compile_options(dottalk_wx_next PRIVATE -Wall -Wextra -Wpedantic)
endif()
