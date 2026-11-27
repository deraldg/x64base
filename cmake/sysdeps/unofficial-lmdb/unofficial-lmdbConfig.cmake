# Shim package for DOTTALK_SYSTEM_DEPS=ON. The target is created, GLOBAL, by
# cmake/sysdeps/DotTalkSystemDeps.cmake; this file only reports whether it exists.
if (TARGET unofficial::lmdb::lmdb)
    set(unofficial-lmdb_FOUND TRUE)
else()
    set(unofficial-lmdb_FOUND FALSE)
    set(unofficial-lmdb_NOT_FOUND_MESSAGE "unofficial::lmdb::lmdb was not created; include cmake/sysdeps/DotTalkSystemDeps.cmake with DOTTALK_SYSTEM_DEPS=ON first.")
endif()
