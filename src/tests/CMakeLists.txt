# ---- PDLC / DTV foundation smoke test --------------------------------------
# Canonical DotTalk Value + qualified reference + DataAddress (tuple/PDLC Phase-0).
# Links the isolated dottalk_value lib; proves signed/unsigned exact integers
# (incl. RECNO64 UINT64_MAX), ExactDecimal, reference parse/reject, and address text.
if(TARGET dottalk_value)
  add_executable(dottalkpp_pdlc_foundation_smoke
    ${CMAKE_CURRENT_SOURCE_DIR}/test_pdlc_foundation_smoke.cpp
  )
  target_link_libraries(dottalkpp_pdlc_foundation_smoke PRIVATE dottalk_value)
  target_include_directories(dottalkpp_pdlc_foundation_smoke PRIVATE ${CMAKE_SOURCE_DIR}/include)
  add_test(NAME dottalkpp_pdlc_foundation_smoke COMMAND dottalkpp_pdlc_foundation_smoke)
endif()

# ---- LMDB backend smoke test -----------------------------------------------

if(DOTTALK_WITH_INDEX AND TARGET xindex)
  add_executable(dottalkpp_lmdb_backend_smoke
    ${CMAKE_CURRENT_SOURCE_DIR}/test_lmdb_backend.cpp
  )
  target_link_libraries(dottalkpp_lmdb_backend_smoke PRIVATE xindex)
  target_include_directories(dottalkpp_lmdb_backend_smoke PRIVATE ${CMAKE_SOURCE_DIR}/include)
  add_test(NAME dottalkpp_lmdb_backend_smoke COMMAND dottalkpp_lmdb_backend_smoke)
endif()

# ---- Workspace membership: R6, absent is not a value -----------------------
# Header-only (include/xbase/workspace_membership.hpp is all inline), so this
# links nothing and touches no filesystem. Proves join()/leave() refuse a
# NEGATIVE engine slot -- the value that used to mean both "this area has no
# slot" and "this member entry is free". See ruling D10 sec 2a.
add_executable(dottalkpp_workspace_membership_test
  ${CMAKE_CURRENT_SOURCE_DIR}/test_workspace_membership.cpp
)
target_include_directories(dottalkpp_workspace_membership_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
add_test(NAME dottalkpp_workspace_membership_test COMMAND dottalkpp_workspace_membership_test)

# ---- Relation merge and parse: AIF-078 decision-owed #6 --------------------
# relation_parse.cpp is text in, rows out -- it includes only model.hpp, which
# is standard-library only -- so this compiles that ONE translation unit
# directly and links nothing. It deliberately does NOT link dottalk_gui_core,
# which would drag in session.cpp, xbase and memo to test a pure function.
# Two arms PIN known defects (the unparsed ` TO ` clause, and the tree that
# flattens below depth 1) and are written to go RED when those are fixed.
add_executable(dottalkpp_relation_merge_test
  ${CMAKE_CURRENT_SOURCE_DIR}/test_relation_merge.cpp
  ${CMAKE_SOURCE_DIR}/src/gui/core/relation_parse.cpp
)
target_compile_features(dottalkpp_relation_merge_test PRIVATE cxx_std_20)
target_include_directories(dottalkpp_relation_merge_test PRIVATE
  ${CMAKE_SOURCE_DIR}/include
  ${CMAKE_SOURCE_DIR}/src
)
add_test(NAME dottalkpp_relation_merge_test COMMAND dottalkpp_relation_merge_test)

# ---- GUI match counter: the fixture the two-counters fix was owed ----------
# Unlike the relation-merge test this one LINKS dottalk_gui_core, because the
# counter under test needs a live Session with real open tables -- which is
# exactly why it drifted from the engine's counter unnoticed. Guarded on the
# target existing, since gui/core is only added under DOTTALK_WITH_GUI or
# DOTTALK_WITH_WX.
#
# It builds its own tables and does NOT skip when data is absent: everything it
# reads, it wrote.
if (TARGET dottalk_gui_core)
  add_executable(dottalkpp_gui_match_count_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_gui_match_count.cpp
  )
  target_compile_features(dottalkpp_gui_match_count_test PRIVATE cxx_std_20)
  target_link_libraries(dottalkpp_gui_match_count_test PRIVATE dottalk_gui_core)
  target_include_directories(dottalkpp_gui_match_count_test PRIVATE
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
  )
  add_test(NAME dottalkpp_gui_match_count_test COMMAND dottalkpp_gui_match_count_test)
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

# ---- Trigger hooks smoke (AIF-087 Phase-1 spike: per-DbArea trigger fire) ----
# Fires a C++ callback after a successful index_hooks::apply_replace in
# replaceFieldStored, via a dedicated per-DbArea trigger hook (NOT cursor_hook).
# DbArea's ctor pulls the memo context, so link memo alongside xbase. If the
# linker reports unresolved index_hooks/xindex symbols, add xindex here too.
if(TARGET xbase)
  add_executable(dottalkpp_trigger_hooks_smoke
    ${CMAKE_CURRENT_SOURCE_DIR}/test_trigger_hooks_smoke.cpp
  )
  target_link_libraries(dottalkpp_trigger_hooks_smoke PRIVATE xbase memo)
  target_include_directories(dottalkpp_trigger_hooks_smoke PRIVATE ${CMAKE_SOURCE_DIR}/include)
  add_test(NAME dottalkpp_trigger_hooks_smoke COMMAND dottalkpp_trigger_hooks_smoke)
endif()

# ---- Tracking schema-lint smoke (AIF-086 M1: DBF-native tracking layer) --------
# Header-only lint over portal/tracking_schema.hpp (SYSLANE/SYSRUN/SYSRUNLANE/
# SYSPROOF/SYSTASK): asserts physical names <=10, no duplicate fields, and every
# 64-bit id/epoch field is N(20). No engine or DBF -- needs only the include path.
add_executable(dottalkpp_tracking_schema_test
  ${CMAKE_CURRENT_SOURCE_DIR}/test_tracking_schema.cpp
)
target_include_directories(dottalkpp_tracking_schema_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
add_test(NAME dottalkpp_tracking_schema_test COMMAND dottalkpp_tracking_schema_test)

# ---- RECNO64 gate 3: tuple-stream order-vector capacity (AIF-120 R69) -------
# The order vector is the one place in DbTupleStream where widening has a real
# memory cost, so its width is a DECLARED CAPACITY chosen once -- IIndexBackend's
# shape from RECNO64 M4-4, one layer up. This asserts the narrow backing holds a
# classic table's whole unsigned range, REFUSES a value past its ceiling instead of
# truncating it (the previous path narrowed a 64-bit CDX/LMDB recno to uint32_t
# silently, and 2^32 truncates to 0 -- the engine's own "no current record"), and
# that the wide backing keeps two record numbers past 2^32 distinct.
# Header-only against db_tuple_stream.hpp: no table, no index, no engine link.
add_executable(dottalkpp_tuple_order_capacity_test
  ${CMAKE_CURRENT_SOURCE_DIR}/test_tuple_stream_order_capacity.cpp
)
target_include_directories(dottalkpp_tuple_order_capacity_test PRIVATE
  ${CMAKE_SOURCE_DIR}/include
  ${CMAKE_SOURCE_DIR}/src
  ${CMAKE_SOURCE_DIR}/src/cli
)
add_test(NAME dottalkpp_tuple_order_capacity_test
         COMMAND dottalkpp_tuple_order_capacity_test)
