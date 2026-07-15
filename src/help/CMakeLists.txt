# ============================================================================
# File: src/help/CMakeLists.txt
# Purpose: HELP DATA v2 production library target.
# ============================================================================

add_library(dottalk_helpdata STATIC
    helpdata_model.cpp
    helpdata_messages.cpp
    message_catalog.cpp
    locale_spine_catalog.cpp
    helpdata_artifacts.cpp
    helpdata_source_miner.cpp
    helpdata_export_dbf.cpp
)

target_include_directories(dottalk_helpdata
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
)

target_compile_features(dottalk_helpdata PUBLIC cxx_std_20)
