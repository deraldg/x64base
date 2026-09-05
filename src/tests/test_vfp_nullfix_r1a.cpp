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
//     INSERT INTO nullfix VALUES (.NULL., "AB",         "0123456789", "RR")   <- R1c
//     INSERT INTO nullfix VALUES (3,      .NULL.,       "0123456789", "SS")   <- R1c
//
// Nothing in this repository wrote a byte of it. The first three `_NullFlags` bytes
// it came back with -- 0x02, 0x0F, 0x08 -- are three of the bytes Arrangement A had
// already computed from the documentation the day before. Rows 4 and 5 were appended
// 2026-09-05 to close R1c; the original three are byte-identical across the
// regeneration, which is itself worth something: the generator is deterministic.
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
// R1c -- WHAT THE FIRST THREE ROWS COULD NOT SEE, AND HOW ROWS 4 AND 5 SEE IT
// ---------------------------------------------------------------------------
//
// This section used to read: "Row 2 nulls ID and VNAME TOGETHER, so bits 0 and 2
// are only ever observed set as a pair. Exchanging them fits this file. Physical-
// field-order allocation says bit 0 is ID's, and that is what assign_null_bits()
// computes, but here that is INFERENCE AND NOT MEASUREMENT."
//
// It was true, and it was a defect in how the fixture was built rather than in any
// code. Rows 4 and 5 fix it, and they are MIRRORS of each other on purpose:
//
//   row 4   ID null, VNAME = "AB" (short, NOT null)   -> 0x03   b0 set, b2 clear
//   row 5   ID = 3 (NOT null), VNAME null             -> 0x06   b0 clear, b2 set
//
// Row 4 is the one that settles it. Its ID field is BLANK and its VNAME field
// holds real content ('AB' + spaces + CHR(2)) -- so the null field and the
// non-null field are distinguishable IN THE DATA, without consulting the bitmap.
// The bit that is set is bit 0. If bit 2 were ID's, row 4 would read 0x06.
//
// A single row would only have told us which of two hypotheses fits. The mirrored
// PAIR additionally forces the two bytes to come back DIFFERENT, which rules out
// any rule that collapses the two null bits into one.
//
// PREDICTED 0x03 and 0x06 in tools/vfp/make_nullfix.prg BEFORE the run; measured
// 0x03 and 0x06. Recorded because the previous prediction block in that same file
// was wrong on all three counts, and a method that only gets written up when it
// succeeds is not a method.
//
// The file is parsed here BY HAND rather than through the loader, on purpose:
// what is under test is the format claim, not our reading of it. The loader's own
// behaviour on real VFP files is graded by dottalkpp_vfp_real_fixture_flags_test.
//
// THE REGENERATION IS BYTE-STABLE. make_nullfix.prg recreates the whole table, so
// adding rows 4 and 5 rewrote rows 1-3 as well. Truncating the new file back to
// three records reproduces the committed R1a blob EXACTLY -- sha256
// 3c43b26e0e9daab883b9cef52bcf20f886618df04869a06163e3d6ed046b34a3 -- so the R1a
// measurement was not quietly re-based by the R1c edit.
//
// A MISSING FIXTURE IS A FAILURE, NOT A SKIP. A test that quietly finds no file
// and reports green is the fifth instrument in one day that could not see what it
// was for.
//
// MUTATION-TESTED against the real file, 2026-09-04 PM, blast radius recorded so a
// later reader knows exactly what this guard can and cannot see:
//
//   M1  swap the pair order in assign_null_bits (null bit lower)   ->  5 red
//   M2  invert the polarity in varlength_value_length              ->  6 red
//   M3  make bit 0 the MSB of byte 0 in bit_is_set                 -> 10 red
//   M4  walk the fields in REVERSE physical order                  ->  5 red
//   M5  exchange the FIRST field's null bit with the SECOND's      ->  6 red
//
// M5 IS THE ONE ROWS 4 AND 5 BOUGHT, and the way it was measured matters more
// than the number. Against the THREE-row fixture, the previous version of this
// test also went red on M5 -- but only through its two
// `check_eq(lay.fields[i].null_bit, N)` lines, which it had itself labelled
// "(INFERRED from field order)". Those assert OUR BELIEF back to us; a mutation
// of the belief reds them by construction. That is not evidence.
//
// Strip exactly those two lines and re-run the old test on the old fixture:
//
//   control                            0 red
//   M5 exchange the two null bits      0 red      <- THE FILE WAS BLIND
//
// Rows 4 and 5 are what make the FILE object, because they tie each null bit to a
// field whose nullness is visible in the record bytes without reading the bitmap.
// Same mutation, same code, five rows instead of three: 6 red.
//
// The lesson is not about VFP. A test can red on a mutation for two reasons -- the
// evidence contradicts it, or the test restates the hypothesis -- and the red looks
// identical from the outside. Labelling the inferred assertions is what made the
// difference visible; deleting them is what proved it.

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
    check_eq((long long)rec_cnt,  5, "record count -- 3 for R1a, plus 2 for R1c");

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
    check_eq(lay.fields[0].null_bit, 0, "ID null bit -- MEASURED by rows 4 and 5 (was INFERRED until R1c)");
    check_eq(lay.fields[1].full_bit, 1, "VNAME varlength bit -- MEASURED by rows 1 and 3");
    check_eq(lay.fields[1].null_bit, 2, "VNAME null bit -- MEASURED by rows 4 and 5 (was INFERRED until R1c)");
    check_eq(lay.fields[2].full_bit, 3, "VFULL varlength bit -- MEASURED by rows 1 and 3");
    check_eq(lay.fields[3].full_bit, -1, "PLAIN contributes nothing");
    check_eq(lay.fields[3].null_bit, -1, "PLAIN contributes nothing");

    // ---- the three bitmap bytes VFP wrote ----------------------------------
    // Bit index 0 is the LSB of byte 0. vfp_null_bits.hpp called that assumption
    // "conventional, unconfirmed". It is now measured: under MSB-first numbering
    // row 1 would read 0x40.
    const std::uint8_t want_flags[5] = { 0x02, 0x0F, 0x08, 0x03, 0x06 };
    const char* row_why[5] = {
        "row 1 -- VNAME short (bit 1), VFULL full, nothing null",
        "row 2 -- ID and VNAME null (bits 0,2) AND both V short (bits 1,3)",
        "row 3 -- VNAME full, VFULL short (bit 3), nothing null",
        "row 4 -- R1c: ID null (bit 0) ALONE, VNAME short and not null, VFULL full",
        "row 5 -- R1c: VNAME null (bit 2) ALONE, ID not null, VFULL full"
    };

    for (std::size_t r = 0; r < 5; ++r) {
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

    // ---- R1c: THE MIRRORED PAIR THAT SEPARATES THE TWO NULL BITS ----------
    //
    // Rows 1-3 can only ever show bits 0 and 2 set TOGETHER (row 2 nulls both
    // nullable fields), so they cannot say which field owns which. Rows 4 and 5
    // null exactly one field each, in opposite directions.
    //
    // The witness is the DATA, not the bitmap: in row 4 the ID field is BLANK and
    // the VNAME field holds real content, so which one is null is visible without
    // consulting _NullFlags at all. The bit that is set is bit 0.
    {
        const std::uint8_t* r4 = &b[hdr_len + 3 * rec_len];
        const std::uint8_t* r5 = &b[hdr_len + 4 * rec_len];
        const std::uint8_t  nf4 = r4[rec_len - 1];
        const std::uint8_t  nf5 = r5[rec_len - 1];

        const int id_null    = lay.fields[0].null_bit;   // 0 under the shipped rule
        const int vname_null = lay.fields[1].null_bit;   // 2 under the shipped rule

        // Record layout: [0] delete, [1..4] ID, [5..14] VNAME, [15..24] VFULL,
        // [25..29] PLAIN, [30] _NullFlags.
        check(r4[1] == ' ' && r4[2] == ' ' && r4[3] == ' ' && r4[4] == ' ',
              "row 4 -- ID is blank, i.e. the null one (data witness, not the bitmap)");
        check(r4[5] == 'A' && r4[6] == 'B' && r4[14] == 2,
              "row 4 -- VNAME holds 'AB' + length byte 2, i.e. NOT null (data witness)");
        check(bit_is_set(&nf4, 1, id_null),
              "row 4 -- the FIRST field's null bit is SET, and the first field is the"
              " one the data shows as null");
        check(!bit_is_set(&nf4, 1, vname_null),
              "row 4 -- the SECOND field's null bit is CLEAR (if these were exchanged,"
              " row 4 would read 0x06)");

        check(r5[4] == '3',
              "row 5 -- ID holds 3, i.e. NOT null (data witness)");
        check(!bit_is_set(&nf5, 1, id_null),
              "row 5 -- the first field's null bit is CLEAR");
        check(bit_is_set(&nf5, 1, vname_null),
              "row 5 -- the second field's null bit is SET");

        // Belt and braces: a rule that collapsed both nulls onto one bit would make
        // these two bytes equal.
        check(nf4 != nf5,
              "row 4 and row 5 differ -- the two null bits are TWO bits, not one");
    }

    if (g_failures) {
        std::printf("R1a FAILED (%d)\n", g_failures);
        return 1;
    }
    std::printf("R1a PASSED -- bit assignment confirmed against a Visual FoxPro-authored file\n");
    return 0;
}
