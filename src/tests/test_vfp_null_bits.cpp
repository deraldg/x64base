// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// status: experimental
//
// AIF-091 M1 -- THE R1 GUARD.
//
// R1 in the M1 design is the bit-assignment order in the VFP `_NullFlags` column,
// and the design says in as many words: "Do not ship M1 on the assumption alone."
// The assumption in that document was NULL-BIT-THEN-VARLENGTH-BIT and it was
// BACKWARDS. Microsoft's own VFP 9 chapter 9 says the opposite:
//
//     "If a field is both nullable and Varchar or Varbinary, two bits are used to
//      represent a field. The LOWER bit represents the 'full' status and the HIGHER
//      bit represents the null status."
//
// WHY THIS TEST ASSERTS BYTES RATHER THAN A ROUND TRIP, and it is the whole design:
// there is NO VFP fixture with a nullable field anywhere in this repository -- 21
// VFP-flavor tables measured 2026-09-04, all 0x30, all with zero nullable and zero
// system fields. So M1's real accept gate cannot be run. A create-then-read round
// trip would prove only that OUR ENCODER AND OUR DECODER AGREE WITH EACH OTHER,
// which they would do just as happily with the order inverted -- a closed loop
// reporting green on a file VFP could not open. Every expectation below is computed
// BY HAND from the sentence quoted above, so a reader can check it against the
// documentation instead of against us.
//
// IT IS NOT PROOF AGAINST A REAL FILE. It is the strongest thing available without
// one. When a real fixture arrives, this test stays and the fixture proof is added
// beside it; if they disagree, the fixture wins and the flip is one edit in
// include/xbase/vfp_null_bits.hpp.
//
// -------------------------------------------------------------------------
// THE FIXTURE ARRIVED THE SAME DAY, AND THEY AGREED. 2026-09-04 PM.
// -------------------------------------------------------------------------
//
// tools/vfp/fixtures/nullfix.DBF was created inside Visual FoxPro 9 -- a nullable
// N, a nullable Varchar, a plain Varchar, a plain C. Its three `_NullFlags` bytes
// are 0x02, 0x0F and 0x08: three of the bytes Arrangement A below asserts, on a
// file nothing here wrote. The promise above is kept -- THIS TEST STAYS, and the
// fixture proof sits beside it as dottalkpp_vfp_nullfix_r1a_test.
//
// TWO CORRECTIONS TO THE PARAGRAPH ABOVE, both measured, both left standing rather
// than edited away:
//
//   The "21 VFP-flavor tables, all 0x30" sweep globbed `*.dbf` and so could not see
//   the .SCX and .VCX tables VFP also writes. Re-measured by magic byte: 59 tracked
//   DBF-format files, seven of which disagree (commit 7a46a4a01).
//
//   "M1's real accept gate cannot be run" was true for about eighteen hours.
//
// STILL NOT MEASURED, and Arrangement A cannot see it either: the fixture's row 2
// nulls both nullable fields at once, so bits 0 and 2 are only ever observed as a
// pair. Which of them belongs to the first field is inference from field order.
// R1c -- first field null, second short and not null -- is the row that would say.

#include "xbase/vfp_null_bits.hpp"

#include <cstdio>
#include <cstdint>
#include <vector>

namespace {

int g_failures = 0;

void check(bool ok, const char* what)
{
    if (ok) return;
    std::printf("  FAIL: %s\n", what);
    ++g_failures;
}

void check_eq(long long got, long long want, const char* what)
{
    if (got == want) return;
    std::printf("  FAIL: %s -- got %lld, want %lld\n", what, got, want);
    ++g_failures;
}

using xbase::vfp::FieldNullSpec;
using xbase::vfp::assign_null_bits;
using xbase::vfp::set_bit;
using xbase::vfp::bit_is_set;
using xbase::vfp::varlength_value_length;

// -------------------------------------------------------------------------
// ARRANGEMENT A -- the M1 accept gate's own shape, plus a field that
// contributes nothing.
//
//   f1  N  nullable            -> null bit only        -> null = 0
//   f2  V  nullable            -> BOTH, full is lower  -> full = 1, null = 2
//   f3  V  not nullable        -> full bit only        -> full = 3
//   f4  C  plain               -> no bits at all
//
//   4 bits -> 1 byte.
// -------------------------------------------------------------------------
void arrangement_a()
{
    std::printf("Arrangement A: N-nullable, V-nullable, V-plain, C-plain\n");

    const std::vector<FieldNullSpec> specs = {
        { false, true  },   // f1
        { true,  true  },   // f2
        { true,  false },   // f3
        { false, false }    // f4
    };
    const auto lay = assign_null_bits(specs);

    check_eq(static_cast<long long>(lay.bit_count),  4, "A bit_count");
    check_eq(static_cast<long long>(lay.byte_count), 1, "A byte_count");

    check_eq(lay.fields[0].full_bit, -1, "A f1 has no full bit");
    check_eq(lay.fields[0].null_bit,  0, "A f1 null bit");
    check_eq(lay.fields[1].full_bit,  1, "A f2 FULL bit is the LOWER of its pair");
    check_eq(lay.fields[1].null_bit,  2, "A f2 NULL bit is the HIGHER of its pair");
    check_eq(lay.fields[2].full_bit,  3, "A f3 full bit");
    check_eq(lay.fields[2].null_bit, -1, "A f3 has no null bit");
    check_eq(lay.fields[3].full_bit, -1, "A f4 contributes nothing (full)");
    check_eq(lay.fields[3].null_bit, -1, "A f4 contributes nothing (null)");

    // ---- byte expectations, each computed by hand from the rule ----
    std::uint8_t b[1];

    b[0] = 0;
    check_eq(b[0], 0x00, "A nothing set");

    b[0] = 0;
    set_bit(b, 1, lay.fields[0].null_bit, true);          // bit 0
    check_eq(b[0], 0x01, "A f1 null -> bit 0 -> 0x01");

    b[0] = 0;
    set_bit(b, 1, lay.fields[1].full_bit, true);          // bit 1
    check_eq(b[0], 0x02, "A f2 short value -> full bit 1 -> 0x02");

    // THE DISCRIMINATOR. Under the M1 spec's original (inverted) order f2's null
    // bit would be index 1 and this byte would read 0x02. It must read 0x04.
    b[0] = 0;
    set_bit(b, 1, lay.fields[1].null_bit, true);          // bit 2
    check_eq(b[0], 0x04, "A f2 NULL -> bit 2 -> 0x04  (0x02 here means the order flipped)");

    b[0] = 0;
    set_bit(b, 1, lay.fields[1].full_bit, true);
    set_bit(b, 1, lay.fields[1].null_bit, true);
    check_eq(b[0], 0x06, "A f2 short AND null -> bits 1+2 -> 0x06");

    b[0] = 0;
    set_bit(b, 1, lay.fields[2].full_bit, true);          // bit 3
    check_eq(b[0], 0x08, "A f3 short value -> bit 3 -> 0x08");

    b[0] = 0;
    for (const auto& fb : lay.fields) {
        set_bit(b, 1, fb.full_bit, true);
        set_bit(b, 1, fb.null_bit, true);
    }
    check_eq(b[0], 0x0F, "A every bit this layout owns -> 0x0F (and no bit above it)");

    // Reading back what we set, and NOT reading what we did not.
    b[0] = 0;
    set_bit(b, 1, lay.fields[1].null_bit, true);
    check(bit_is_set(b, 1, lay.fields[1].null_bit),  "A f2 null reads back set");
    check(!bit_is_set(b, 1, lay.fields[1].full_bit), "A f2 full stays clear");
    check(!bit_is_set(b, 1, lay.fields[0].null_bit), "A f1 null stays clear");
}

// -------------------------------------------------------------------------
// ARRANGEMENT B -- five fields that are BOTH, so the bitmap crosses a byte
// boundary. Ten bits -> two bytes.
//
//   f1 full=0 null=1 | f2 full=2 null=3 | f3 full=4 null=5
//   f4 full=6 null=7 | f5 full=8 null=9
// -------------------------------------------------------------------------
void arrangement_b()
{
    std::printf("Arrangement B: five nullable Varchar fields (crosses a byte)\n");

    const std::vector<FieldNullSpec> specs(5, FieldNullSpec{ true, true });
    const auto lay = assign_null_bits(specs);

    check_eq(static_cast<long long>(lay.bit_count),  10, "B bit_count");
    check_eq(static_cast<long long>(lay.byte_count),  2, "B byte_count = ceil(10/8)");

    check_eq(lay.fields[0].full_bit, 0, "B f1 full");
    check_eq(lay.fields[0].null_bit, 1, "B f1 null");
    check_eq(lay.fields[4].full_bit, 8, "B f5 full");
    check_eq(lay.fields[4].null_bit, 9, "B f5 null");

    std::uint8_t b[2];

    b[0] = 0; b[1] = 0;
    set_bit(b, 2, lay.fields[3].null_bit, true);          // bit 7, top of byte 0
    check_eq(b[0], 0x80, "B f4 null -> bit 7 -> byte0 0x80");
    check_eq(b[1], 0x00, "B f4 null leaves byte1 clear");

    b[0] = 0; b[1] = 0;
    set_bit(b, 2, lay.fields[4].null_bit, true);          // bit 9, byte 1 bit 1
    check_eq(b[0], 0x00, "B f5 null leaves byte0 clear");
    check_eq(b[1], 0x02, "B f5 null -> bit 9 -> byte1 0x02");

    // Out-of-range must be inert rather than corrupting a neighbour.
    b[0] = 0; b[1] = 0;
    set_bit(b, 2, 16, true);
    check_eq(b[0], 0x00, "B out-of-range write does not touch byte0");
    check_eq(b[1], 0x00, "B out-of-range write does not touch byte1");
    check(!bit_is_set(b, 2, 16), "B out-of-range read is false, not a crash");
}

// -------------------------------------------------------------------------
// VALUE LENGTH -- MS worked example: a 10-byte Varchar holding "AB" stores
// 'AB' + seven spaces + CHR(2), and 2 is the length of the VALUE.
// -------------------------------------------------------------------------
void value_length()
{
    std::printf("Varchar true length from the last field byte\n");

    std::uint8_t f[10] = { 'A','B',' ',' ',' ',' ',' ',' ',' ', 2 };

    check_eq(static_cast<long long>(varlength_value_length(f, 10, true)), 2,
             "full bit SET -> last byte is the value length");
    check_eq(static_cast<long long>(varlength_value_length(f, 10, false)), 10,
             "full bit CLEAR -> the value fills the field");

    // Fail closed: a last byte longer than the field must not hand back an
    // out-of-bounds length. This is the shape that turns a bad file into a read
    // past the end of a record.
    std::uint8_t bad[10] = { 'A','B',' ',' ',' ',' ',' ',' ',' ', 99 };
    check_eq(static_cast<long long>(varlength_value_length(bad, 10, true)), 10,
             "a length byte larger than the field clamps to the field");
}

} // namespace

int main()
{
    std::printf("AIF-091 M1 -- VFP _NullFlags bit assignment (R1 guard)\n");
    std::printf("  Rule: physical field order; a field that is BOTH nullable and\n");
    std::printf("  Varchar/Varbinary gets TWO bits, FULL lower and NULL higher.\n");
    std::printf("  Source: Microsoft, What's New in VFP 9, chapter 9.\n\n");

    arrangement_a();
    arrangement_b();
    value_length();

    if (g_failures == 0) {
        std::printf("\nPASS -- every bit index and every byte matches the documented rule.\n");
        std::printf("NOT a proof against a real VFP file: none exists in this tree.\n");
        return 0;
    }
    std::printf("\nFAIL -- %d expectation(s) missed.\n", g_failures);
    return 1;
}
