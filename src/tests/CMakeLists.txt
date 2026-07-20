# ---- LMDB backend smoke test -----------------------------------------------

if(DOTTALK_WITH_INDEX AND TARGET xindex)
  add_executable(dottalkpp_lmdb_backend_smoke
    ${CMAKE_CURRENT_SOURCE_DIR}/test_lmdb_backend.cpp
  )
  target_link_libraries(dottalkpp_lmdb_backend_smoke PRIVATE xindex)
  target_include_directories(dottalkpp_lmdb_backend_smoke PRIVATE ${CMAKE_SOURCE_DIR}/include)
  add_test(NAME dottalkpp_lmdb_backend_smoke COMMAND dottalkpp_lmdb_backend_smoke)
endif()

add_executable(dottalkpp_security_policy_test
  ${CMAKE_CURRENT_SOURCE_DIR}/test_security_policy.cpp
)
target_include_directories(dottalkpp_security_policy_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
add_test(NAME dottalkpp_security_policy_test COMMAND dottalkpp_security_policy_test)

# ---- X64 record-size hard-guard test (16 MiB ceiling via create_dbf) --------
# If the linker reports unresolved memo/xindex symbols pulled in by create_dbf,
# add those libs here (e.g. PRIVATE xbase memo). The over-ceiling path returns
# before any sidecar/index work, so xbase alone is expected to suffice.
if(TARGET xbase)
  add_executable(dottalkpp_x64_record_limit_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_x64_record_limit.cpp
  )
  target_link_libraries(dottalkpp_x64_record_limit_test PRIVATE xbase)
  target_include_directories(dottalkpp_x64_record_limit_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
  add_test(NAME dottalkpp_x64_record_limit_test COMMAND dottalkpp_x64_record_limit_test)
endif()

# ---- RECNO64 boundary test (M4-5: accessors past 2^31) ----------------------
# Fabricates 64-bit cursor/count/length state via DbArea's public setters (no
# giant table) and asserts recno64/recCount64/recLength64 resolve distinct values
# past 2^31 while the legacy recno()/recCount()/recLength() return -1 at overflow.
# DbArea's ctor pulls the memo context, so link memo alongside xbase.
if(TARGET xbase)
  add_executable(dottalkpp_recno64_boundary_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_recno64_boundary.cpp
  )
  target_link_libraries(dottalkpp_recno64_boundary_test PRIVATE xbase memo)
  target_include_directories(dottalkpp_recno64_boundary_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
  add_test(NAME dottalkpp_recno64_boundary_test COMMAND dottalkpp_recno64_boundary_test)
endif()

# ---- RECNO64 sparse-file end-to-end test (M4-5: real record past 2^31) -------
# Builds a real x64 table whose record_count is set past 2^31, writes records at
# recno 1 / 2^31+1 / 2^31+2 into a SPARSE file (the ~19 GB gap is a filesystem
# hole), reopens through the engine, and asserts gotoRec64 reads them distinctly.
# Uses create_dbf + full DbArea open/read, so link xbase + memo (add xindex here
# if the linker reports unresolved index symbols from the open path).
if(TARGET xbase)
  add_executable(dottalkpp_recno64_sparse_e2e_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_recno64_sparse_e2e.cpp
  )
  target_link_libraries(dottalkpp_recno64_sparse_e2e_test PRIVATE xbase memo)
  target_include_directories(dottalkpp_recno64_sparse_e2e_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
  add_test(NAME dottalkpp_recno64_sparse_e2e_test COMMAND dottalkpp_recno64_sparse_e2e_test)
endif()

# ---- FIELDTYPE M2 codec boundary test (I/B/Y/T binary encode/decode) --------
# Exercises the field-type codec registry directly (no DBF): encodes text into a
# field-width byte region and decodes it back, asserting round-trips and exact
# on-disk encoding at boundaries. Codecs live in xbase.lib; no memo/index needed.
if(TARGET xbase)
  add_executable(dottalkpp_field_codec_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_field_codec.cpp
  )
  target_link_libraries(dottalkpp_field_codec_test PRIVATE xbase)
  target_include_directories(dottalkpp_field_codec_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
  add_test(NAME dottalkpp_field_codec_test COMMAND dottalkpp_field_codec_test)
endif()

find_package(Python3 COMPONENTS Interpreter REQUIRED)
if (TARGET dottalkpp)
  add_test(
    NAME dottalkpp_profile_smoke
    COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/profile_smoke.py"
            --exe "$<TARGET_FILE:dottalkpp>"
            --root "${CMAKE_SOURCE_DIR}"
            --index-mode "${DOTTALK_INDEX_MODE}"
            --product "${DOTTALK_PRODUCT}"
  )
  set_tests_properties(dottalkpp_profile_smoke PROPERTIES
    LABELS "profile;runtime;xbase"
  )
endif()
