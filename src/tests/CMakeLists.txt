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
# relation_parse.cpp is text in, rows out -- so this compiles those translation
# units directly and links nothing. It deliberately does NOT link
# dottalk_gui_core, which would drag in session.cpp, xbase and memo to test a
# pure function.
#
# R124 (2026-08-24) split the unit: the posture round trip moved to
# src/xbase/relation_wire.cpp so the CLI can reach it too, and what stayed here
# is the GUI's own -- merging into the model, and scraping human CLI text. Both
# halves are still standard-library only, and this target is the reason we know
# that: it has been compiling the unit outside dottalk_gui_core since before the
# move, which is what made the move cheap.
# STALE UNTIL 2026-08-24, corrected here. This said "Two arms PIN known defects
# (the unparsed ` TO ` clause, and the tree that flattens below depth 1) and are
# written to go RED when those are fixed." Both defects WERE fixed, and the arms
# were repointed at the time -- the fixture's own transcript now reads "4a: `ON p
# TO c` splits both sides; 4e: the tree nests instead of flattening onto the
# root", which is the FIXED behaviour asserted, not a defect pinned. Only this
# comment was left describing the old world.
#
# It survived because a comment cannot go red. That is the same shape as the
# setting AIF-123 restored, and the same shape as the ~80% cross-file citation
# rot this project has measured and not yet gated -- a claim that decays without
# ever failing. It was caught by READING THE FIXTURE'S TRANSCRIPT rather than by
# trusting a green suite, which is the only thing that could have caught it.
add_executable(dottalkpp_relation_merge_test
  ${CMAKE_CURRENT_SOURCE_DIR}/test_relation_merge.cpp
  ${CMAKE_SOURCE_DIR}/src/gui/core/relation_parse.cpp
  # R124: the posture round trip moved to xbase, so this fixture compiles that
  # TU as well. It still links NOTHING -- relation_wire.cpp is standard-library
  # only and is filed under src/xbase for reach, not for dependencies.
  ${CMAKE_SOURCE_DIR}/src/xbase/relation_wire.cpp
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

# ---- AIF-078: GUI areas are real engine-array areas -------------------------
#
# The discriminator for step 2b. Against the pre-2b code -- where
# Session::Impl::Area held a DbArea BY VALUE and so carried _engine_slot == -1
# for life -- workspace::join(h, -1) matched the free-slot sentinel and claimed
# nothing, so member_count reads the baseline and every area reports the same
# local slot. This fixture reads 2 and two DISTINCT slots, and destroys the
# Session to prove ~Area() releases them again.
#
# Gated on dottalk_gui_core like the counter test above it, which is why both
# need .\build.ps1 -WithGui: src/gui/core is behind DOTTALK_WITH_GUI and a
# plain build does not compile it.
if (TARGET dottalk_gui_core)
  add_executable(dottalkpp_gui_area_membership_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_gui_area_membership.cpp
  )
  target_compile_features(dottalkpp_gui_area_membership_test PRIVATE cxx_std_20)
  target_link_libraries(dottalkpp_gui_area_membership_test PRIVATE dottalk_gui_core)
  target_include_directories(dottalkpp_gui_area_membership_test PRIVATE
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
  )
  add_test(NAME dottalkpp_gui_area_membership_test COMMAND dottalkpp_gui_area_membership_test)
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

# ---- Cooperative lock handshake: table fence vs record writers ------------
# SQLSEL JOIN uses two table locks as its statement read transaction. The
# underlying protocol must therefore close both publication races: a table
# fence refuses an older foreign record lock, and a record writer refuses a
# foreign table fence. The test writes live-owner sidecars deliberately; this
# reaches contention paths a one-process DotScript cannot manufacture.
if(TARGET xbase)
  add_executable(dottalkpp_lock_protocol_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_lock_protocol.cpp
  )
  target_link_libraries(dottalkpp_lock_protocol_test PRIVATE xbase memo)
  target_include_directories(dottalkpp_lock_protocol_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
  add_test(NAME dottalkpp_lock_protocol_test COMMAND dottalkpp_lock_protocol_test)
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

# ---- IN FREE allocator test (AIF-078 slot lane, step 1) ---------------------
# THE FIRST FIXTURE THE FREE-SLOT POLICY HAS EVER HAD. It was a `static` inside
# cmd_use.cpp that fetched shell_engine() and the process-global membership
# table, so nothing could call it; step 1 lifted it into workarea_util and made
# the engine, the table and the handle parameters. The discriminating arm is the
# workspace-SCOPED placement: a naive lowest-free sweep and this policy return
# different slots (2 vs 7), so the arm fails if the scoping is ever lost.
#
# Compiles the three CLI translation units it needs rather than linking the
# shell: workarea_util (the policy), workareas (its array access), and
# workareas_engine_bridge (the real forwarding indirection). The test itself
# supplies the two symbols the shell would -- shell_engine(), deliberately null,
# and an inert cmdout::print_line -- which is why the CLI's output layer
# (OutputRouter/doc/helpdata) is NOT dragged in for a path no arm reaches.
if(TARGET xbase)
  add_executable(dottalkpp_area_alloc_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_area_alloc.cpp
    ${CMAKE_SOURCE_DIR}/src/cli/workarea_util.cpp
    ${CMAKE_SOURCE_DIR}/src/cli/workareas.cpp
    ${CMAKE_SOURCE_DIR}/src/cli/workareas_engine_bridge.cpp
    # R131 (2026-08-29): workarea_util.cpp gained workspace_roots_apply_to_slots,
    # which calls dottalk::paths::get_slot/set_slot -- defined in path_state.cpp.
    # This target compiles workarea_util.cpp directly and links only xbase+memo,
    # so it went to LNK2019 the first time anything built ALL the targets. The
    # GUI closure already pairs these two files (gui/uidef/CMakeLists.txt); this
    # is the one place the pairing was missing. path_state.cpp is self-contained
    # (its own header plus std), so it drags nothing else in.
    ${CMAKE_SOURCE_DIR}/src/common/path_state.cpp
  )
  target_link_libraries(dottalkpp_area_alloc_test PRIVATE xbase memo)
  target_include_directories(dottalkpp_area_alloc_test PRIVATE
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_SOURCE_DIR}/src/cli
  )
  add_test(NAME dottalkpp_area_alloc_test COMMAND dottalkpp_area_alloc_test)
endif()

# ---- VFP _NullFlags bit assignment, the R1 guard (AIF-091 M1) ----------------
# The M1 design named the bit-assignment order as its one open ambiguity and said
# "do not ship M1 on the assumption alone". The assumption was BACKWARDS: Microsoft's
# VFP 9 chapter 9 states that for a field which is both nullable and Varchar/Varbinary
# the LOWER bit is the "full" status and the HIGHER bit is the null status. This test
# is what keeps the corrected order from drifting back.
#
# IT ASSERTS HAND-COMPUTED BYTES, NOT A ROUND TRIP, and that is deliberate: a
# create-then-read proof would only show our encoder and our decoder agreeing with
# each other -- which they do just as happily with the order inverted. Every
# expectation is derived from the documentation so a human can check it against the
# documentation.
#
# This block used to add "there is no VFP fixture with a nullable field anywhere in
# this tree (21 VFP tables measured 2026-09-04)". Both halves were wrong: the sweep
# globbed *.dbf and missed the .SCX/.VCX tables VFP also writes (see 7a46a4a01), and
# a nullable fixture was authored in VFP later the same day. It is graded by
# dottalkpp_vfp_nullfix_r1a_test below, which AGREED with the hand-computed bytes.
#
# Header-only against xbase/vfp_null_bits.hpp: no table, no index, no engine link.
add_executable(dottalkpp_vfp_null_bits_test
  ${CMAKE_CURRENT_SOURCE_DIR}/test_vfp_null_bits.cpp
)
target_include_directories(dottalkpp_vfp_null_bits_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
add_test(NAME dottalkpp_vfp_null_bits_test COMMAND dottalkpp_vfp_null_bits_test)

# ---- VFP/x64 field descriptor flags byte (AIF-091 M1) ------------------------
# `VfpField::flags` sat at byte 23 -- the autoincrement STEP value -- while the
# format puts field flags at byte 18. The struct was a dBASE III descriptor wearing
# a VFP name, so nullable and binary have never been decoded correctly, and nothing
# noticed because every VFP- and x64-flavor table in the tree carries zero at BOTH
# bytes: the wrong byte and the right byte agree on all existing data.
#
# The decoy case is the discriminator -- 0x02 at byte 18 and 0x04 at byte 23 give
# opposite readings under the two layouts. Links xbase for the generated build
# vectors that xbase.hpp pulls in.
if(TARGET xbase)
  add_executable(dottalkpp_vfp_field_descriptor_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_vfp_field_descriptor.cpp
  )
  target_link_libraries(dottalkpp_vfp_field_descriptor_test PRIVATE xbase memo)
  target_include_directories(dottalkpp_vfp_field_descriptor_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
  add_test(NAME dottalkpp_vfp_field_descriptor_test COMMAND dottalkpp_vfp_field_descriptor_test)
endif()

# ---- VFP field flags read from files Visual FoxPro wrote (AIF-091 M1) --------
# Every other test in this lane grades the decoder against byte tables computed by
# hand. Necessary, not sufficient: until 2026-09-04 dbf_create.cpp held its OWN
# declaration of the field subrecord with the SAME wrong layout as the reader, so
# the writer put flags at byte 23 and the reader took them from 23 and agreed
# perfectly. A create-then-read round trip cannot tell that from correct.
#
# These fixtures are .SCX/.VCX -- VFP forms and class libraries, which are
# DBF-format tables authored by Visual FoxPro and NOT named `.dbf`. That naming is
# why the first sweep of this tree missed them and wrongly reported that byte 18
# and byte 23 agree everywhere. OBJCODE carries 0x04 (binary) at byte 18 and 0x00
# at byte 23, so this test goes red under the old layout on a file we did not write.
#
# VFP_FIXTURE_ROOT is passed rather than discovered: a test that hunts for its own
# fixtures can quietly find none and pass. Missing fixture is a FAILURE here.
if(TARGET xbase)
  add_executable(dottalkpp_vfp_real_fixture_flags_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_vfp_real_fixture_flags.cpp
  )
  target_link_libraries(dottalkpp_vfp_real_fixture_flags_test PRIVATE xbase memo)
  target_include_directories(dottalkpp_vfp_real_fixture_flags_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
  target_compile_definitions(dottalkpp_vfp_real_fixture_flags_test
    PRIVATE VFP_FIXTURE_ROOT="${CMAKE_SOURCE_DIR}/tools/vfp")
  add_test(NAME dottalkpp_vfp_real_fixture_flags_test COMMAND dottalkpp_vfp_real_fixture_flags_test)
endif()

# ---- _NullFlags partition and the offset hazard (AIF-091 M1) -----------------
# DbArea::fieldByteOffset_() accumulates field lengths and ignores the descriptor
# `displacement`, so removing a field shifts everything after it. Only a TRAILING
# system field can be partitioned out safely; a system field anywhere else makes
# partitionTrailingSystemField() decline and report, which case (3) proves.
#
# Descriptors are BUILT here rather than read from a file: no tracked table
# carries 0x01 at byte 18, because no writer has ever set it. What is under test
# is our partition arithmetic, not our reading of someone else's format -- the
# real-file evidence lives in dottalkpp_vfp_real_fixture_flags_test.
if(TARGET xbase)
  add_executable(dottalkpp_vfp_null_partition_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_vfp_null_partition.cpp
  )
  target_link_libraries(dottalkpp_vfp_null_partition_test PRIVATE xbase memo)
  target_include_directories(dottalkpp_vfp_null_partition_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
  add_test(NAME dottalkpp_vfp_null_partition_test COMMAND dottalkpp_vfp_null_partition_test)
endif()

# ---- R1a: the bit assignment read out of a VFP-authored file (AIF-091 M1) ----
# dottalkpp_vfp_null_bits_test grades the bit order against bytes computed BY HAND
# from Microsoft's sentence, and its own header says that is not proof against a
# real file. tools/vfp/fixtures/nullfix.DBF is the real file: created inside Visual
# FoxPro 9 on 2026-09-04 by tools/vfp/make_nullfix.prg, with a Varchar field that is
# also nullable -- the only shape where the two-bit order can be observed at all.
#
# It came back 0x02 / 0x0F / 0x08, which are three of the bytes Arrangement A had
# already computed. Row 2 is the load-bearing one: both Varchar fields carry a
# length byte there and both their bits are SET, which is what rules out "the bit
# is set when the field is full".
#
# Header-only. The file is parsed by hand rather than through the loader because
# what is under test is the format claim, not our reading of it.
if(EXISTS "${CMAKE_SOURCE_DIR}/tools/vfp/fixtures/nullfix.DBF")
  add_executable(dottalkpp_vfp_nullfix_r1a_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_vfp_nullfix_r1a.cpp
  )
  target_include_directories(dottalkpp_vfp_nullfix_r1a_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
  target_compile_definitions(dottalkpp_vfp_nullfix_r1a_test
    PRIVATE VFP_FIXTURE_ROOT="${CMAKE_SOURCE_DIR}/tools/vfp")
  add_test(NAME dottalkpp_vfp_nullfix_r1a_test COMMAND dottalkpp_vfp_nullfix_r1a_test)
else()
  message(FATAL_ERROR
    "AIF-091 R1a fixture missing: tools/vfp/fixtures/nullfix.DBF. It is tracked; "
    "rebuild it with tools/vfp/make_nullfix.prg inside Visual FoxPro 9 if it was lost. "
    "This is a configure FAILURE and not a skip on purpose -- a lane whose only "
    "real-file proof can silently vanish has no real-file proof.")
endif()

# ---- per-row null decode through a real open (AIF-091 M1) -------------------
# Everything else in this lane stops at the field descriptors. This goes through
# DbArea::open() -> gotoRec() -> fieldIsNullFromBuffer(), which is the path a
# consumer takes, and is the "getters" half of the section-6 accept gate.
#
# IT OPENS A COPY. DbArea::open() uses ios::in|ios::out and fixtures here are
# report-only; a test that opened nullfix.DBF writable would leave the lane's only
# real-file evidence one stray write from being evidence of nothing, silently.
#
# Its expectations are transcribed from make_nullfix.prg -- the statements that
# told VFP which cells to null -- and NOT derived from the _NullFlags bytes.
# Deriving them from the bytes would make the test agree with the decoder by
# construction, which is the closed loop this whole lane exists to correct.
if(TARGET xbase)
  add_executable(dottalkpp_vfp_null_rowdecode_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_vfp_null_rowdecode.cpp
  )
  target_link_libraries(dottalkpp_vfp_null_rowdecode_test PRIVATE xbase memo)
  target_include_directories(dottalkpp_vfp_null_rowdecode_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
  target_compile_definitions(dottalkpp_vfp_null_rowdecode_test
    PRIVATE VFP_FIXTURE_ROOT="${CMAKE_SOURCE_DIR}/tools/vfp")
  add_test(NAME dottalkpp_vfp_null_rowdecode_test COMMAND dottalkpp_vfp_null_rowdecode_test)
endif()

# ---- does a write preserve the row's null bitmap? (AIF-091 M1) --------------
# storeFieldsToBuffer() space-fills the whole record and then re-encodes one field
# per entry in `_fields`. Since fbd7e5ee5 the `_NullFlags` column is NOT in
# `_fields` -- the partition removed it -- and nothing writes its bytes back, so a
# write leaves the bitmap as 0x20: every null becomes not-null and every short
# Varchar claims to be full.
#
# The record keeps its length, its field values and its deleted flag. Only the
# nulls are gone. That is the AIF-110 shape exactly, whose spec says it in one
# line: a test that asserts SHAPE passes green on a blanked table.
#
# No existing write test could see this, because every write test in this project
# runs on tables THIS ENGINE created and this engine cannot yet create a nullable
# table. The fixture is the only nullable table in the tree.
#
# It writes to a COPY. The fixture is never opened writable.
if(TARGET xbase)
  add_executable(dottalkpp_vfp_null_write_guard_test
    ${CMAKE_CURRENT_SOURCE_DIR}/test_vfp_null_write_preserves_bitmap.cpp
  )
  target_link_libraries(dottalkpp_vfp_null_write_guard_test PRIVATE xbase memo)
  target_include_directories(dottalkpp_vfp_null_write_guard_test PRIVATE ${CMAKE_SOURCE_DIR}/include)
  target_compile_definitions(dottalkpp_vfp_null_write_guard_test
    PRIVATE VFP_FIXTURE_ROOT="${CMAKE_SOURCE_DIR}/tools/vfp")
  add_test(NAME dottalkpp_vfp_null_write_guard_test COMMAND dottalkpp_vfp_null_write_guard_test)
endif()
