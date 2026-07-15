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
