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
  memo_browser_frame.cpp
)

# AIF-120 R91. The application icon. On MSW it is a LINKED RESOURCE -- the .rc
# names the .ico, CMake hands it to the resource compiler, and Explorer takes
# the executable icon from the same resource wxIconBundle reads at run time.
# Everywhere else the icon is compiled in as XPM by res/app_icon.hpp and there
# is nothing to add to the source list.
if (WIN32)
  list(APPEND DOTTALK_WX_SOURCES res/x64base.rc)
endif()

add_executable(dottalk_wb WIN32 ${DOTTALK_WX_SOURCES})
add_executable(dottalk_wb_next WIN32 ${DOTTALK_WX_SOURCES})

if (wxWidgets_USE_FILE AND NOT TARGET wx::core)
  include("${wxWidgets_USE_FILE}")
endif()

target_include_directories(dottalk_wb
  PRIVATE
    "${CMAKE_SOURCE_DIR}/include"
    ${wxWidgets_INCLUDE_DIRS}
)
target_include_directories(dottalk_wb_next
  PRIVATE
    "${CMAKE_SOURCE_DIR}/include"
    ${wxWidgets_INCLUDE_DIRS}
)

target_compile_features(dottalk_wb PRIVATE cxx_std_20)
target_compile_features(dottalk_wb_next PRIVATE cxx_std_20)

target_link_libraries(dottalk_wb
  PRIVATE
    dottalk_gui_core
    ${wxWidgets_LIBRARIES}
)
target_link_libraries(dottalk_wb_next
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
    add_custom_command(TARGET dottalk_wb POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${_dottalk_wx_runtime_dlls}
        $<TARGET_FILE_DIR:dottalk_wb>
      COMMAND_EXPAND_LISTS
      COMMENT "Copying wxWidgets runtime DLLs for dottalk_wb"
    )
    add_custom_command(TARGET dottalk_wb_next POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${_dottalk_wx_runtime_dlls}
        $<TARGET_FILE_DIR:dottalk_wb_next>
      COMMAND_EXPAND_LISTS
      COMMENT "Copying wxWidgets runtime DLLs for dottalk_wb_next"
    )
  endif()

  unset(_dottalk_prefix_runtime_dlls)
  unset(_dottalk_prefix_wx_required_dlls)
  # NOT `unset(_dottalk_wx_runtime_dlls)` here. The staging block near the end of
  # this file guards on that variable, and CMake's `if()` does not open a scope --
  # so unsetting it inside this block left the guard permanently false and the
  # staged DLL copy never ran. The symptom was silent: the build printed the
  # "Copying ... for dottalk_wb" comment from the build-dir copy above and simply
  # never printed "Staging wxWidgets runtime DLLs into dottalkpp/bin", so the log
  # looked healthy. Measured 2026-08-21 in a full Release build. It is unset at
  # the bottom of this file instead, after its last use.
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
  target_compile_options(dottalk_wb PRIVATE /W4 /permissive-)
  target_compile_options(dottalk_wb_next PRIVATE /W4 /permissive-)
else()
  target_compile_options(dottalk_wb PRIVATE -Wall -Wextra -Wpedantic)
  target_compile_options(dottalk_wb_next PRIVATE -Wall -Wextra -Wpedantic)
endif()

# -----------------------------------------------------------------------------
# Stage the built GUI where the runtime looks for it. AIF-120.
#
# `APPGUI` resolves the GUI executable through the GUI path slot, which is
# root-relative and beside the product: <repo>/dottalkpp/bin (path_state.cpp,
# `s.gui_root = s.root / "bin"`, and cmd_setpath.cpp init_defaults). A launcher
# that has to guess where a build put its output is a launcher that can be wrong;
# staging here means the product DECLARES the location and APPGUI only reports it.
#
# copy_if_different, matching the wx DLL step above -- a rebuild that changed
# nothing should not touch the staged file.
set(DOTTALK_GUI_STAGE_DIR "${CMAKE_SOURCE_DIR}/dottalkpp/bin")

foreach(_dottalk_gui_target dottalk_wb dottalk_wb_next)
  add_custom_command(TARGET ${_dottalk_gui_target} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "${DOTTALK_GUI_STAGE_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
      "$<TARGET_FILE:${_dottalk_gui_target}>"
      "${DOTTALK_GUI_STAGE_DIR}"
    COMMENT "Staging ${_dottalk_gui_target} into dottalkpp/bin (the GUI path slot)"
  )
endforeach()

# The executable alone is not runnable on Windows. The DLL list was gathered
# above for the build directory; the staged copy needs the same set beside it.
if (WIN32 AND _dottalk_wx_runtime_dlls)
  add_custom_command(TARGET dottalk_wb POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
      ${_dottalk_wx_runtime_dlls}
      "${DOTTALK_GUI_STAGE_DIR}"
    COMMAND_EXPAND_LISTS
    COMMENT "Staging wxWidgets runtime DLLs into dottalkpp/bin"
  )
elseif (WIN32)
  # Reaching here means the DLL search above found nothing. Say so at configure
  # time: the staged exe will not run, and a silent skip is what hid this for as
  # long as it did.
  message(WARNING
    "No wxWidgets runtime DLLs were located, so ${DOTTALK_GUI_STAGE_DIR} will "
    "hold dottalk_wb.exe without the DLLs it needs. APPGUI will launch it and "
    "Windows will fail to start the process."
  )
endif()

unset(_dottalk_wx_runtime_dlls)
unset(_dottalk_gui_target)
