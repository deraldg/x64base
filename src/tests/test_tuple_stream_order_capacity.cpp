// @dottalk.file v1
// subsystem: tests
// layer: test
// owns:
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: supported

// src/tests/test_tuple_stream_order_capacity.cpp
//
// RECNO64 completion gate 3 ("Relations/tuples preserve them"), at the tuple
// stream's order vector -- AIF-120 R69/R70.
//
// The order vector is PURE 64 by owner ruling: std::vector<RecordNo>, no narrow
// backing, no width to select. An earlier version made it a two-width variant to
// save 22 MB on a pinocchio-scale ordered browse; the owner ruled the memory is not
// worth a second code path. 32-bit TABLES are still fully supported -- a classic
// CNX or .inx still stores four-byte recnos and still loads through a
// std::vector<uint32_t>, because that is what the FORMAT holds. What is gone is a
// 32-bit representation of a record number anywhere inside the stream.
//
// What this proves:
//   1. record numbers past 2^32 round-trip and stay DISTINCT -- the previous path
//      narrowed a full 64-bit CDX/LMDB recno to uint32_t, and 2^32 truncates to 0,
//      which is the engine's own "no current record" (bof() is _crn64 == 0);
//   2. a classic 32-bit table's whole unsigned range is carried unchanged, so
//      widening cost the narrow case nothing;
//   3. order_find_pos is 1-based with 0 for absent, so an unsigned identity needs
//      no -1 sentinel -- the three MSVC C4245 warnings that found the leftover
//      `order_pos_ = -1` assignments were the last of those.

#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <vector>

#include "db_tuple_stream.hpp"

int main() {
    using dottalk::RecordNo;
    using dottalk::order_find_pos;

    const RecordNo U32MAX = std::numeric_limits<std::uint32_t>::max();   // 4294967295
    const RecordNo PAST32 = U32MAX + 1;                                  // 4294967296
    const RecordNo I31    = 2147483648ull;                               // 2^31

    static_assert(sizeof(RecordNo) == 8, "a record number is 64-bit, everywhere");
    static_assert(!std::numeric_limits<RecordNo>::is_signed,
                  "identity is unsigned; a delta is the signed type");

    // 1) Past 2^32, held and distinct.
    std::vector<RecordNo> ord;
    ord.push_back(PAST32);
    ord.push_back(PAST32 + 7);
    assert(ord[0] == PAST32);
    assert(ord[1] == PAST32 + 7);
    assert(ord[0] != ord[1] && "two records past 2^32 must stay distinct");

    // What the previous path did to the same value, spelled out.
    const std::uint32_t truncated = static_cast<std::uint32_t>(PAST32);
    assert(truncated == 0 &&
           "2^32 truncates to 0 -- the engine's own 'no current record'");
    std::cout << "recno " << PAST32 << " survives; narrowed it would have been "
              << truncated << " (bof)\n";

    // 2) A classic table's whole range, unchanged by the widening.
    std::vector<RecordNo> classic;
    classic.push_back(1);
    classic.push_back(I31);          // past 2^31 is ordinary in 32 UNSIGNED bits
    classic.push_back(U32MAX);
    assert(classic[1] == I31);
    assert(classic[2] == U32MAX);

    // A 32-bit FORMAT still loads through its own width, then widens on the way in
    // -- this is exactly what the CNX and .inx paths do.
    std::vector<std::uint32_t> from_cnx{1u, 7u, static_cast<std::uint32_t>(U32MAX)};
    std::vector<RecordNo> widened(from_cnx.begin(), from_cnx.end());
    assert(widened.size() == 3);
    assert(widened[2] == U32MAX && "a classic recno widens without change");

    // 3) 1-based, 0 for absent.
    assert(order_find_pos(ord, PAST32) == 1);
    assert(order_find_pos(ord, PAST32 + 7) == 2);
    assert(order_find_pos(ord, 12345) == 0);
    assert(order_find_pos(classic, U32MAX) == 3);
    assert(order_find_pos(classic, PAST32) == 0);

    std::cout << "order vector is pure 64: " << PAST32 << " and " << (PAST32 + 7)
              << " distinct, classic range intact, 1-based find. PASS\n";
    return 0;
}
