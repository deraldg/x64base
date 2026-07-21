# PDLC Foundation Standalone First Build Transcript — Amended Value Contract

**Date:** 2026-07-20  
**Environment:** Linux container, GNU C++ 14.2.0  
**Language mode:** C++17  
**Scope:** Compile-only domain foundation  
**Authority:** Construction smoke only; not the authoritative `D:\code\ccode` build.

## Stewardship amendment

Before this build, the canonical Value packet was amended to add:

```text
ValueKind::UnsignedInteger
std::uint64_t payload
Value::unsigned_integer(uint64_t)
```

This is required because RECNO64 is an unsigned 64-bit domain, not merely signed int64.

## Configure and build

```text
-- The CXX compiler identification is GNU 14.2.0
-- Configuring done
-- Generating done
[ 66%] Built target dottalk_pdlc_foundation
[100%] Built target pdlc_foundation_smoke
```

## CTest

```text
1/1 Test #1: pdlc_foundation_smoke ............ Passed
100% tests passed, 0 tests failed
```

## Smoke output

```text
PDLC foundation smoke passed
  decimal=123.4500
  reference=#2.LNAME
  address=MCC.#2.STUDENTS.RECNO(9007199254740993).LNAME
  recno64_max=18446744073709551615
```

## Proven by this build

- signed `int64_t` and unsigned `uint64_t` are distinct DTV kinds;
- RECNO64 values above the double-safe range remain exact;
- the complete `uint64_t` maximum survives DTV construction;
- `ExactDecimal` preserves declared scale;
- representative qualified references parse;
- malformed and trailing reference text is rejected;
- `DataAddress` preserves exact RECNO64 text;
- the foundation has no CLI-global, DbArea, tuple_builder, or expression dependency.

## Not proven

- MSVC compatibility;
- authoritative local CMake placement;
- real local `MemoRef` compatibility;
- tagged canonical wire round-trip;
- semantic comparison service;
- evaluation, array, or field-codec adapters;
- tuple and reference-host integration.

The next event remains the authoritative build under Claude supervision.
