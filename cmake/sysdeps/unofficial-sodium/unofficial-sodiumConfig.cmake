# Shim package for DOTTALK_SYSTEM_DEPS=ON. The target is created, GLOBAL, by
# cmake/sysdeps/DotTalkSystemDeps.cmake; this file only reports whether it exists.
if (TARGET unofficial-sodium::sodium)
    set(unofficial-sodium_FOUND TRUE)
else()
    set(unofficial-sodium_FOUND FALSE)
    set(unofficial-sodium_NOT_FOUND_MESSAGE "unofficial-sodium::sodium was not created; include cmake/sysdeps/DotTalkSystemDeps.cmake with DOTTALK_SYSTEM_DEPS=ON first.")
endif()
