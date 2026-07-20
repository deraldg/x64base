// src/tests/test_recno64_boundary.cpp
//
// RECNO64 M4-5 boundary proof.
//
// This is the decisive test the capacity docs call "not yet measured": that the
// 64-bit accessors resolve DISTINCT record numbers past 2^31, and that the legacy
// 32-bit accessors now return -1 ("out of 32-bit range") at overflow instead of
// silently clamping to INT_MAX (the old saturating behavior collapsed two different
// records past 2.1 B onto the same 2147483647).
//
// No 2.1-billion-row / ~85 GB table is written: the 64-bit cursor/count/length state
// is fabricated directly with the public setters, so the accessor arithmetic is
// exercised at INT32_MAX, INT32_MAX+1/+2, UINT32_MAX, and UINT32_MAX+1.

#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>

#include "xbase.hpp"

int main() {
    const std::int32_t  I32MAX = std::numeric_limits<std::int32_t>::max();   // 2147483647
    const std::uint64_t I32MAXu = static_cast<std::uint64_t>(I32MAX);
    const std::uint64_t U32MAX = std::numeric_limits<std::uint32_t>::max();  // 4294967295
    const int           IMAX   = std::numeric_limits<int>::max();

    xbase::DbArea a;

    // ---- recno(): exactly INT32_MAX still fits ----
    a.setRecno64(I32MAXu);
    assert(a.recno64() == I32MAXu);
    assert(a.recno() == I32MAX && "INT32_MAX must still round-trip through recno()");

    // ---- recno(): first value past 2^31 signals overflow, not a clamp ----
    a.setRecno64(I32MAXu + 1);
    assert(a.recno64() == I32MAXu + 1);
    assert(a.recno() == -1 && "recno() must return -1 past INT32_MAX, not INT_MAX");

    // ---- decisive: two DISTINCT records past 2^31 are distinguishable ----
    a.setRecno64(I32MAXu + 2);
    assert(a.recno64() == I32MAXu + 2);
    assert(a.recno64() != (I32MAXu + 1) &&
           "records past 2^31 must be distinct via recno64() (old recno() collapsed them)");
    assert(a.recno() == -1);

    // ---- recno(): 32-bit-unsigned boundary and just beyond ----
    a.setRecno64(U32MAX);
    assert(a.recno64() == U32MAX);
    assert(a.recno() == -1);

    a.setRecno64(U32MAX + 1);
    assert(a.recno64() == U32MAX + 1);
    assert(a.recno() == -1);

    // ---- recCount(): same boundary contract ----
    a.setRecordCount64(I32MAXu);
    assert(a.recCount64() == I32MAXu);
    assert(a.recCount() == I32MAX);

    a.setRecordCount64(I32MAXu + 1);
    assert(a.recCount64() == I32MAXu + 1);
    assert(a.recCount() == -1);

    a.setRecordCount64(U32MAX + 1);
    assert(a.recCount64() == U32MAX + 1);
    assert(a.recCount() == -1);

    // ---- recLength()/cpr(): INT_MAX fits, past it returns -1 ----
    a.setRecordLength(static_cast<std::uint64_t>(IMAX));
    assert(a.recLength64() == static_cast<std::uint64_t>(IMAX));
    assert(a.recLength() == IMAX);
    assert(a.cpr() == IMAX);

    a.setRecordLength(static_cast<std::uint64_t>(IMAX) + 1);
    assert(a.recLength64() == static_cast<std::uint64_t>(IMAX) + 1);
    assert(a.recLength() == -1 && "recLength() must return -1 past INT_MAX, not clamp");
    assert(a.cpr() == -1);

    std::cout << "recno64_boundary: recno64/recCount64/recLength64 resolve distinct "
                 "values past 2^31; legacy accessors return -1 at overflow. PASS\n";
    return 0;
}
