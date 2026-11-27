# Shim package for DOTTALK_SYSTEM_DEPS=ON. The target is created, GLOBAL, by
# cmake/sysdeps/DotTalkSystemDeps.cmake; this file only reports whether it exists.
if (TARGET nlohmann_json::nlohmann_json)
    set(nlohmann_json_FOUND TRUE)
else()
    set(nlohmann_json_FOUND FALSE)
    set(nlohmann_json_NOT_FOUND_MESSAGE "nlohmann_json::nlohmann_json was not created; include cmake/sysdeps/DotTalkSystemDeps.cmake with DOTTALK_SYSTEM_DEPS=ON first.")
endif()
