// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// status: experimental
//
// AIF-091 M1 -- R1a: THE BIT ASSIGNMENT, READ OUT OF A FILE VISUAL FOXPRO WROTE.
//
// dottalkpp_vfp_null_bits_test asserts bytes computed BY HAND from Microsoft's
// sentence, and says so in its own header: "IT IS NOT PROOF AGAINST A REAL FILE.
// It is the strongest thing available without one. When a real fixture arrives,
// this test stays and the fixture proof is added beside it."
//
// THIS IS THAT PROOF. tools/vfp/fixtures/nullfix.DBF was created inside Visual
// FoxPro 9 by tools/vfp/make_nullfix.prg on 2026-09-04:
//
//     CREATE TABLE nullfix (id N(4) NULL, vname V(10) NULL, vfull V(10), plain C(5))
//     INSERT INTO nullfix VALUES (1,      "ABC",        "0123456789", "XY")
//     INSERT INTO nullfix VALUES (.NULL., .NULL.,       "AB",         "ZZ")
//     INSERT INTO nullfix VALUES (2,      "0123456789", "C",          "QQ")
//
// Nothing in this repository wrote a byte of it. The three `_NullFlags` bytes it
// came back with -- 0x02, 0x0F, 0x08 -- are three of the bytes Arrangement A had
// already computed from the documentation the day before.
//
// ---------------------------------------------------------------------------
// WHAT ROW 2 IS FOR, AND WHY ROWS 1 AND 3 ARE NOT ENOUGH
// ---------------------------------------------------------------------------
//
// Row 1 (VNAME short, VFULL full) reads 0x02 and row 3 (VNAME full, VFULL short)
// reads 0x08. Those two are AMBIGUOUS on their own: "bit set = the field is FULL"
// with the two varlength bits exchanged fits both rows exactly as well as the
// rule we ship. Row 2 is the discriminator -- BOTH Varchar fields carry a length
// byte there, and BOTH their bits are SET. Under "set = full" both would have to
// be clear. So the bit is set when the field is NOT full, which is to say when
// the trailing length byte is in use, which is what varlength_value_length()
// already implements. That is asserted below twice: once as the literal byte, and
// once by deriving each Varchar value under both rules and showing the inverted
// rule produces bytes that cannot be a value.
//
// ---------------------------------------------------------------------------
// WHAT THIS FIXTURE DOES *NOT* PROVE -- READ BEFORE TRUSTING IT FURTHER
// ---------------------------------------------------------------------------
//
// Row 2 nulls ID and VNAME TOGETHER, so bits 0 and 2 are only ever observed set
// as a pair. Exchanging them fits this file. Physical-field-order allocation says
// bit 0 is ID's, and that is what assign_null_bits() computes, but here that is
// INFERENCE AND NOT MEASUREMENT. The missing row is R1c: ID null with VNAME short
// and NOT null, which reads 0x03 if the shipped rule holds and 0x06 if it does
// not. The fixture's load-bearing row nulls both nullable fields at once; that is
// a defect in how it was built, and it is recorded here rather than papered over.
//
// The file is parsed here BY HAND rather than through the loader, on purpose:
// what is under test is the format claim, not our reading of it. The loader's own
// behaviour on real VFP files is graded by dottalkpp_vfp_real_fixture_flags_test.
//
// A MISSING FIXTURE IS A FAILURE, NOT A SKIP. A test that quietly finds no file
// and reports green is the fifth instrument in one day that could not see what it
// was for.
//
// MUTATION-TESTED against the real file, 2026-09-04 PM, blast radius recorded so a
// later reader knows exactly what this guard can and cannot see:
//
//   swap the pair order in assign_null_bits (null bit lower)  -> 3 red
//   invert the polarity in varlength_value_length             -> 4 red
//   make bit 0 the MSB of byte 0 in bit_is_set                -> 6 red
//   exchange ID's null bit with VNAME's null bit              -> GREEN. That is
//     R1c, and it is why R1c is still open: THE FILE CANNOT SEE IT.

#include "xbase/vfp_null_bits.hpp"

#include <cstdio>
#include <cstdint>
#include <cstring>
#include <string>
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
    std::printf("  FAIL: %s -- got %lld (0x%llX), want %lld (0x%llX)\n",
                what, got, (unsigned long long)got, want, (unsigned long long)want);
    ++g_failures;
}

using xbase::vfp::FieldNullSpec;
using xbase::vfp::assign_null_bits;
using xbase::vfp::bit_is_set;
using xbase::vfp::varlength_value_length;

struct Desc {
    std::string   name;
    char          type   {0};
    std::uint8_t  length {0};
    std::uint8_t  flags  {0};
};

std::uint16_t le16(const std::uint8_t* p) { return (std::uint16_t)(p[0] | (p[1] << 8)); }
std::uint32_t le32(const std::uint8_t* p)
{
    return (std::uint32_t)p[0] | ((std::uint32_t)p[1] << 8)
         | ((std::uint32_t)p[2] << 16) | ((std::uint32_t)p[3] << 24);
}

// Could these bytes be a Varchar value of `vlen` characters in a `len`-byte field,
// with `len - 1` holding the length when the length byte is in use? Printable data,
// spaces to the pad, nothing else. This is the independent witness: it looks at the
// DATA, not at the bitmap, so it can contradict the bitmap.
bool plausible_varchar(const std::uint8_t* f, std::size_t len,
                       std::size_t vlen, bool length_byte_in_use)
{
    const std::size_t usable = length_byte_in_use ? (len - 1) : len;
    if (vlen > usable) return false;
    for (std::size_t i = 0; i < vlen; ++i)
        if (f[i] < 0x20 || f[i] > 0x7E) return false;
    for (std::size_t i = vlen; i < usable; ++i)
        if (f[i] != ' ') return false;
    return true;
}

} // namespace

int main()
{
    const std::string path = std::string(VFP_FIXTURE_ROOT) + "/fixtures/nullfix.DBF";
    std::printf("R1a -- VFP-authored nullable fixture: %s\n", path.c_str());

    std::FILE* fp = std::fopen(path.c_str(), "rb");
    if (!fp) {
        std::printf("  FAIL: fixture not found. This is a FAILURE, not a skip --\n"
                    "        R1a is the only measurement in this lane taken from a\n"
                    "        file Visual FoxPro wrote. Rebuild it with\n"
                    "        tools/vfp/make_nullfix.prg inside VFP 9.\n");
        return 1;
    }
    std::vector<std::uint8_t> b;
    {
        std::uint8_t buf[4096];
        std::size_t n;
        while ((n = std::fread(buf, 1, sizeof buf, fp)) > 0) b.insert(b.end(), buf, buf + n);
    }
    std::fclose(fp);
    check(b.size() > 64, "fixture is not empty");
    if (b.size() <= 64) return 1;

    // ---- header ------------------------------------------------------------
    // 0x32 is the varchar-capable VFP flavor. A V field cannot exist below it.
    check_eq(b[0], 0x32, "version byte -- VFP 9 with Varchar support");
    const std::size_t hdr_len = le16(&b[8]);
    const std::size_t rec_len = le16(&b[10]);
    const std::size_t rec_cnt = le32(&b[4]);
    check_eq((long long)rec_len, 31, "record length");
    check_eq((long long)rec_cnt,  3, "record count");

    // ---- field descriptors -------------------------------------------------
    std::vector<Desc> flds;
    for (std::size_t off = 32; off + 32 <= b.size() && b[off] != 0x0D; off += 32) {
        Desc d;
        for (std::size_t i = 0; i < 11 && b[off + i]; ++i) d.name.push_back((char)b[off + i]);
        d.type   = (char)b[off + 11];
        d.length = b[off + 16];
        d.flags  = b[off + 18];          // BYTE 18. Not 23. That was the first bug.
        flds.push_back(d);
    }
    check_eq((long long)flds.size(), 5, "five descriptors -- four user fields plus _NullFlags");
    if (flds.size() != 5) return 1;

    struct Want { const char* name; char type; int len; int flags; const char* why; };
    const Want wanted[5] = {
        { "ID",         'N',  4, 0x02, "N nullable"                                   },
        { "VNAME",      'V', 10, 0x02, "V nullable -- the field that gets TWO bits"    },
        { "VFULL",      'V', 10, 0x00, "V not nullable -- one varlength bit"           },
        { "PLAIN",      'C',  5, 0x00, "C plain -- contributes no bit at all"          },
        // 0x05, NOT 0x01. VFP marks its own hidden column system AND BINARY. The M1
        // design doc says "set flags 0x01 on it"; a CREATE that follows the doc
        // writes a column VFP would not have written. Measured 2026-09-04.
        { "_NullFlags", '0',  1, 0x05, "system AND binary -- the design doc says 0x01" }
    };
    for (int i = 0; i < 5; ++i) {
        char what[128];
        std::snprintf(what, sizeof what, "field %d name (%s)", i, wanted[i].why);
        check(flds[i].name == wanted[i].name, what);
        std::snprintf(what, sizeof what, "field %d type", i);
        check_eq(flds[i].type, wanted[i].type, what);
        std::snprintf(what, sizeof what, "field %d length", i);
        check_eq(flds[i].length, wanted[i].len, what);
        std::snprintf(what, sizeof what, "field %d flags byte 18 (%s)", i, wanted[i].why);
        check_eq(flds[i].flags, wanted[i].flags, what);
    }

    // ---- the layout our shipped rule computes for THIS table ---------------
    std::vector<FieldNullSpec> specs;
    for (int i = 0; i < 4; ++i) {                      // user fields only
        FieldNullSpec s;
        s.varlength = (flds[i].type == 'V' || flds[i].type == 'Q');
        s.nullable  = (flds[i].flags & 0x02) != 0;
        specs.push_back(s);
    }
    const auto lay = assign_null_bits(specs);
    check_eq((long long)lay.bit_count,  4, "four bits");
    check_eq((long long)lay.byte_count, 1, "one byte");
    check_eq((long long)lay.byte_count, flds[4].length,
             "computed bitmap width equals the _NullFlags width VFP wrote");
    check_eq(lay.fields[0].null_bit, 0, "ID null bit  (INFERRED from field order -- see R1c note)");
    check_eq(lay.fields[1].full_bit, 1, "VNAME varlength bit -- MEASURED by rows 1 and 3");
    check_eq(lay.fields[1].null_bit, 2, "VNAME null bit  (INFERRED -- see R1c note)");
    check_eq(lay.fields[2].full_bit, 3, "VFULL varlength bit -- MEASURED by rows 1 and 3");
    check_eq(lay.fields[3].full_bit, -1, "PLAIN contributes nothing");
    check_eq(lay.fields[3].null_bit, -1, "PLAIN contributes nothing");

    // ---- the three bitmap bytes VFP wrote ----------------------------------
    // Bit index 0 is the LSB of byte 0. vfp_null_bits.hpp called that assumption
    // "conventional, unconfirmed". It is now measured: under MSB-first numbering
    // row 1 would read 0x40.
    const std::uint8_t want_flags[3] = { 0x02, 0x0F, 0x08 };
    const char* row_why[3] = {
        "row 1 -- VNAME short (bit 1), VFULL full, nothing null",
        "row 2 -- ID and VNAME null (bits 0,2) AND both V short (bits 1,3)",
        "row 3 -- VNAME full, VFULL short (bit 3), nothing null"
    };

    for (std::size_t r = 0; r < 3; ++r) {
        const std::uint8_t* row = &b[hdr_len + r * rec_len];
        check_eq(row[0], ' ', "record is not deleted");

        std::size_t off = 1;
        const std::uint8_t* fld[5];
        for (int i = 0; i < 5; ++i) { fld[i] = row + off; off += flds[i].length; }
        check_eq((long long)off, (long long)rec_len, "fields fill the record exactly");

        const std::uint8_t nf = fld[4][0];
        check_eq(nf, want_flags[r], row_why[r]);

        // The independent witness. For each Varchar field, derive the value under
        // the SHIPPED rule and under the INVERTED one, and require that the shipped
        // rule yields something that can be a value while -- on at least one field
        // per row -- the inverted rule does not. If both survive everywhere, this
        // fixture is not discriminating and must not be reported as proof.
        bool inverted_died = false;
        for (int i = 1; i <= 2; ++i) {
            const int bit = lay.fields[i].full_bit;
            const bool set = bit_is_set(&nf, 1, bit);
            const std::size_t len = flds[i].length;

            const std::size_t v_ship = varlength_value_length(fld[i], len, set);
            char what[160];
            std::snprintf(what, sizeof what, "row %zu %s reads as a value under the shipped rule",
                          r + 1, flds[i].name.c_str());
            check(plausible_varchar(fld[i], len, v_ship, set), what);

            const std::size_t v_inv = varlength_value_length(fld[i], len, !set);
            if (!plausible_varchar(fld[i], len, v_inv, !set)) inverted_died = true;
        }
        char what[128];
        std::snprintf(what, sizeof what,
                      "row %zu discriminates -- the inverted polarity produces a value it cannot",
                      r + 1);
        check(inverted_died, what);
    }

    // Row 2 is the one that kills "set = full" outright: both varlength bits set
    // while both fields carry a length byte.
    {
        const std::uint8_t* row = &b[hdr_len + 1 * rec_len];
        const std::uint8_t nf = row[rec_len - 1];
        check(bit_is_set(&nf, 1, lay.fields[1].full_bit) &&
              bit_is_set(&nf, 1, lay.fields[2].full_bit),
              "row 2 -- BOTH varlength bits set while BOTH fields hold a length byte");
        check(row[1] == ' ' && row[2] == ' ' && row[3] == ' ' && row[4] == ' ',
              "row 2 -- the null N field is stored blank");
    }

    if (g_failures) {
        std::printf("R1a FAILED (%d)\n", g_failures);
        return 1;
    }
    std::printf("R1a PASSED -- bit assignment confirmed against a Visual FoxPro-authored file\n");
    return 0;
}
