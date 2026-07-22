# config/build_vectors.cmake
# Generated build-capacity authority (AIF-044, BUILD_VECTORS lane).
#
# CMake owns the selectable build inputs. These cache variables feed
# config/build_vectors.hpp.in via configure_file() to produce the single compiled
# authority (generated/dottalk/build_vectors.hpp).
#
# GATE #1 (non-negotiable): defaults preserve current COMPILED behavior. In particular
# MAX_AREAS = 512, matching the hard-coded xbase::MAX_AREA that the engine actually used
# (the older, inert DOTTALK_MAX_AREA profile value of 256/128 is deliberately NOT adopted
# here — doing so would silently narrow capacity). The old DOTTALK_MAX_AREA cache var is
# left untouched for now and retired in a later milestone.

set(DOTTALK_MAX_AREAS                "512"                 CACHE STRING "Maximum simultaneously addressable work areas")
set(DOTTALK_MAX_FIELDS               "256"                 CACHE STRING "Maximum fields accepted by the compiled engine")
set(DOTTALK_MAX_ROWS                 "9223372036854775807" CACHE STRING "Maximum row count accepted by engine policy")
set(DOTTALK_LEGACY_MAX_INDEX_SLOTS   "5"                   CACHE STRING "Legacy per-area index-slot capacity")
set(DOTTALK_X64_MAX_RECORD_BYTES     "16777216"            CACHE STRING "Hard x64 fixed-record-size ceiling (bytes, 16 MiB)")
set(DOTTALK_X64_RECORD_ADVISORY_BYTES "65536"              CACHE STRING "Advisory move-to-memo point (bytes, 64 KiB)")
set(DOTTALK_X64_TABLE_NAME_DEFAULT   "128"                 CACHE STRING "x64 table-name default length")
set(DOTTALK_X64_TABLE_NAME_MAX       "256"                 CACHE STRING "Greatest x64 table name this build accepts")
set(DOTTALK_X64_FIELD_NAME_DEFAULT   "128"                 CACHE STRING "x64 field-name default length")
set(DOTTALK_X64_FIELD_NAME_MAX       "256"                 CACHE STRING "Greatest x64 field name this build accepts")
set(DOTTALK_TABLE_BUFFER_MAX_CHANGES "10000"               CACHE STRING "Maximum buffered changes per area")
set(DOTTALK_PROMPT_CHAR              "."                   CACHE STRING "Default interactive shell prompt character (single char; runtime-mutable)")

# --- Validation: fail configuration early on invalid combinations. ---
# NOTE: MAX_ROWS is intentionally not range-checked in CMake (its value can exceed
# CMake's integer arithmetic range); the C++ side carries it as a uint64 literal.
if (DOTTALK_MAX_AREAS LESS 1)
  message(FATAL_ERROR "build_vectors: DOTTALK_MAX_AREAS must be >= 1")
endif()
if (DOTTALK_MAX_FIELDS LESS 1)
  message(FATAL_ERROR "build_vectors: DOTTALK_MAX_FIELDS must be >= 1")
endif()
if (DOTTALK_LEGACY_MAX_INDEX_SLOTS LESS 1)
  message(FATAL_ERROR "build_vectors: DOTTALK_LEGACY_MAX_INDEX_SLOTS must be >= 1")
endif()
if (DOTTALK_X64_TABLE_NAME_DEFAULT GREATER DOTTALK_X64_TABLE_NAME_MAX)
  message(FATAL_ERROR "build_vectors: TABLE_NAME_DEFAULT must be <= TABLE_NAME_MAX")
endif()
if (DOTTALK_X64_FIELD_NAME_DEFAULT GREATER DOTTALK_X64_FIELD_NAME_MAX)
  message(FATAL_ERROR "build_vectors: FIELD_NAME_DEFAULT must be <= FIELD_NAME_MAX")
endif()
if (DOTTALK_X64_TABLE_NAME_MAX GREATER 65535)
  message(FATAL_ERROR "build_vectors: TABLE_NAME_MAX must fit uint16 metadata capacity (<= 65535)")
endif()
if (DOTTALK_X64_FIELD_NAME_MAX GREATER 65535)
  message(FATAL_ERROR "build_vectors: FIELD_NAME_MAX must fit uint16 metadata capacity (<= 65535)")
endif()
if (DOTTALK_X64_RECORD_ADVISORY_BYTES GREATER DOTTALK_X64_MAX_RECORD_BYTES)
  message(FATAL_ERROR "build_vectors: RECORD_ADVISORY_BYTES must be <= MAX_RECORD_BYTES")
endif()
string(LENGTH "${DOTTALK_PROMPT_CHAR}" _dottalk_prompt_len)
if (NOT _dottalk_prompt_len EQUAL 1)
  message(FATAL_ERROR "build_vectors: DOTTALK_PROMPT_CHAR must be exactly one character (got '${DOTTALK_PROMPT_CHAR}')")
endif()

message(STATUS "== Build vectors (AIF-044) ==")
message(STATUS "   areas=${DOTTALK_MAX_AREAS} fields=${DOTTALK_MAX_FIELDS} rows=${DOTTALK_MAX_ROWS} index_slots=${DOTTALK_LEGACY_MAX_INDEX_SLOTS}")
message(STATUS "   x64 record hard=${DOTTALK_X64_MAX_RECORD_BYTES} advisory=${DOTTALK_X64_RECORD_ADVISORY_BYTES}")
message(STATUS "   x64 names default=${DOTTALK_X64_TABLE_NAME_DEFAULT}/${DOTTALK_X64_FIELD_NAME_DEFAULT} max=${DOTTALK_X64_TABLE_NAME_MAX}/${DOTTALK_X64_FIELD_NAME_MAX} table-buffer changes=${DOTTALK_TABLE_BUFFER_MAX_CHANGES} prompt='${DOTTALK_PROMPT_CHAR}'")
