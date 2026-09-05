// @dottalk.file v1
// subsystem: xbase
// layer: header
// owns: VFP _NullFlags bit assignment
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// owner: member.derald
// status: experimental

// vfp_null_bits.hpp -- WHERE EACH FIELD'S BITS LIVE IN THE VFP `_NullFlags` COLUMN.
//
// AIF-091 M1. THIS IS THE ONE PLACE THAT ANSWERS THE QUESTION, on purpose: the M1
// design says the bit-assignment order is "the one ambiguity across implementations"
// and instructs that it be encoded "as a single documented function so a flip is one
// edit". This is that function. Nothing else in the engine may derive a bit index.
//
// ---------------------------------------------------------------------------
// THE RULE, FROM THE FORMAT'S AUTHOR
// ---------------------------------------------------------------------------
//
// Microsoft, "What's New in Visual FoxPro 9.0", chapter 9 (New Data and Index Types):
//
//     "If a field is both nullable and Varchar or Varbinary, two bits are used to
//      represent a field. The LOWER bit represents the 'full' status and the HIGHER
//      bit represents the null status."
//
//     "If a bit contains 0, the length of the value in a field equals the field size
//      (the field is full). If the bit contains 1, the length of the value is less
//      than the field size, in which case the field is padded with spaces as
//      necessary and the last byte contains [the length of the value]."
//
// Hentzen et al., "The Hacker's Guide to Visual FoxPro", section 1 chapter 2:
//
//     "_NullFlags is a bitmap, one bit for each nullable field in the table, IN THE
//      PHYSICAL ORDER OF THE FIELDS IN THE TABLE. If a field is to be null, the
//      associated bit is set on (to 1)."
//
// So: walk the user fields in PHYSICAL ORDER; each field contributes a `full` bit if
// it is variable-length (V/Q) and a `null` bit if it is nullable; when it contributes
// both, THE FULL BIT COMES FIRST (lower index).
//
// ---------------------------------------------------------------------------
// THIS CORRECTS THE M1 SPEC, WHICH HAD IT BACKWARDS
// ---------------------------------------------------------------------------
//
// AI_ENGINE_VFP_M1_NULLFLAGS_DECODE_DESIGN_V1.md section 3 said: "assign the next
// bitmap bit index to each field's null bit (if nullable) THEN its varlength bit (if
// V/Q)". That is the opposite of the sentence quoted above, and the spec itself said
// "Do not ship M1 on the assumption alone." It was an assumption, and it was wrong.
// Measured 2026-09-04 by reading the primary source the spec had already cited.
//
// ---------------------------------------------------------------------------
// SUPERSEDED 2026-09-04 PM -- THE FIXTURE ARRIVED. Original text kept verbatim
// because it is the record of what was known when the rule was written:
// ---------------------------------------------------------------------------
//
//   | WHAT IS STILL NOT PROVEN, AND WHY IT MATTERS MORE THAN USUAL
//   |
//   | THERE IS NO VFP FIXTURE WITH A NULLABLE FIELD ANYWHERE IN THIS REPOSITORY.
//   | Measured the same day: 21 VFP-flavor tables (13 tracked, 8 untracked), every
//   | one version 0x30, every one with ZERO nullable fields and ZERO system fields.
//   | So the M1 accept gate's "decode proof against a real VFP fixture" CANNOT BE
//   | RUN TODAY.
//   |
//   | That is why this header exists separately from any encoder, and why its test
//   | asserts HAND-COMPUTED BYTES rather than a round trip. [...] It is not proof
//   | against a real file; it is the strongest thing available without one, and it
//   | is honest about which it is.
//   |
//   | ONE ASSUMPTION REMAINS AND IS NOT DOCUMENTED BY ANY SOURCE READ: that bit
//   | index 0 is the LEAST SIGNIFICANT bit of byte 0. Conventional, unconfirmed.
//
// TWO OF THOSE SENTENCES WERE ALREADY WRONG WHEN WRITTEN. The "21 VFP-flavor
// tables" sweep globbed `*.dbf`; VFP also writes DBF-format tables named .SCX and
// .VCX. Re-measured by MAGIC BYTE the same day: 59 tracked DBF-format files, seven
// of which disagree with the reassuring claim. See commit 7a46a4a01.
//
// ---------------------------------------------------------------------------
// WHAT IS PROVEN NOW, AND BY WHAT
// ---------------------------------------------------------------------------
//
// tools/vfp/fixtures/nullfix.DBF was created INSIDE Visual FoxPro 9 on 2026-09-04
// by tools/vfp/make_nullfix.prg -- version 0x32, a nullable N, a field that is both
// nullable and Varchar, a plain Varchar, and a plain C. Nothing here wrote a byte
// of it. Its three `_NullFlags` bytes came back 0x02, 0x0F, 0x08, which are three of
// the bytes the hand-computed test had already asserted. dottalkpp_vfp_nullfix_r1a_test
// is that measurement; read its header for the derivation.
//
//   PROVEN: the varlength bit is set when the field is NOT full -- when the trailing
//           length byte is in use. Row 2 of the fixture settles it: both Varchar
//           fields carry a length byte and both bits are SET.
//   PROVEN: bit index 0 IS the least significant bit of byte 0. Under MSB-first
//           numbering row 1 would have read 0x40. The assumption above is retired.
//   PROVEN: the varlength bits land at the indices this function computes -- VNAME's
//           at 1 and VFULL's at 3, which is physical field order with the full bit
//           lower.
//
// ONE THING IS STILL NOT MEASURED. The fixture's row 2 nulls BOTH nullable fields at
// once, so bits 0 and 2 are only ever observed set as a pair; exchanging them fits
// the file. That bit 0 belongs to the FIRST field is inference from field order, not
// measurement. R1c is the missing row -- ID null with VNAME short and NOT null --
// which reads 0x03 if this function is right and 0x06 if it is not. The fixture's
// load-bearing row was built wrong; that is recorded rather than glossed.
//
// If a fixture ever contradicts the LSB convention after all, the fix is in
// bit_is_set/set_bit below and nowhere else -- which is why those two exist.

#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace xbase {
namespace vfp {

// What a single user field contributes to the bitmap. Both false -> no bits.
struct FieldNullSpec {
    bool varlength {false};   // V (Varchar) or Q (Varbinary): contributes a "full" bit
    bool nullable  {false};   // field-descriptor flag 0x02: contributes a null bit
};

// Where one field's bits landed. -1 means "this field has no such bit".
struct FieldBitIndex {
    int full_bit {-1};
    int null_bit {-1};
};

struct NullBitLayout {
    std::vector<FieldBitIndex> fields;      // parallel to the user field vector
    std::size_t bit_count  {0};
    std::size_t byte_count {0};             // ceil(bit_count / 8) -- the _NullFlags length
};

// THE ASSIGNMENT. Physical field order; full bit before null bit within a field.
inline NullBitLayout assign_null_bits(const std::vector<FieldNullSpec>& specs)
{
    NullBitLayout out;
    out.fields.reserve(specs.size());

    int next = 0;
    for (const FieldNullSpec& s : specs) {
        FieldBitIndex fb;
        // ORDER IS LOAD-BEARING: the "full" bit is the LOWER of the two.
        if (s.varlength) fb.full_bit = next++;
        if (s.nullable)  fb.null_bit = next++;
        out.fields.push_back(fb);
    }

    out.bit_count  = static_cast<std::size_t>(next);
    out.byte_count = (out.bit_count + 7) / 8;
    return out;
}

// Bit index 0 is the LSB of byte 0. See the assumption note in the header comment.
inline bool bit_is_set(const std::uint8_t* bitmap, std::size_t bytes, int bit_index) noexcept
{
    if (!bitmap || bit_index < 0) return false;
    const std::size_t byte = static_cast<std::size_t>(bit_index) / 8;
    if (byte >= bytes) return false;
    return (bitmap[byte] & (1u << (static_cast<unsigned>(bit_index) % 8))) != 0;
}

inline void set_bit(std::uint8_t* bitmap, std::size_t bytes, int bit_index, bool on) noexcept
{
    if (!bitmap || bit_index < 0) return;
    const std::size_t byte = static_cast<std::size_t>(bit_index) / 8;
    if (byte >= bytes) return;
    const std::uint8_t mask = static_cast<std::uint8_t>(1u << (static_cast<unsigned>(bit_index) % 8));
    if (on) bitmap[byte] = static_cast<std::uint8_t>(bitmap[byte] | mask);
    else    bitmap[byte] = static_cast<std::uint8_t>(bitmap[byte] & static_cast<std::uint8_t>(~mask));
}

// A value's true length, given its "full" bit and the field's bytes.
// full bit CLEAR -> the value fills the field. full bit SET -> the LAST BYTE of the
// field carries the value length (MS example: a 10-byte Varchar holding "AB" stores
// 'AB' + seven spaces + CHR(2)).
inline std::size_t varlength_value_length(const std::uint8_t* field_bytes,
                                          std::size_t field_length,
                                          bool full_bit_set) noexcept
{
    if (!field_bytes || field_length == 0) return 0;
    if (!full_bit_set) return field_length;
    const std::size_t len = static_cast<std::size_t>(field_bytes[field_length - 1]);
    return (len <= field_length) ? len : field_length;   // fail closed on a bad byte
}

} // namespace vfp
} // namespace xbase
