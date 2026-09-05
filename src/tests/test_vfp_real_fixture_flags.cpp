// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// status: experimental
//
// AIF-091 M1 -- THE ONLY EVIDENCE THAT COUNTS: FILES VISUAL FOXPRO WROTE.
//
// Every other test in this lane proves the decoder against byte tables computed by
// hand from the format document. That is necessary and it is not sufficient, and
// the reason is the defect this lane found: `src/xbase/dbf_create.cpp` used to hold
// its OWN declaration of the field subrecord with the SAME wrong layout as the
// reader, so the writer put field flags at byte 23 and the reader took them from
// byte 23 and the two agreed perfectly. A create-then-read round trip -- which is
// what every test that makes its own table does -- CANNOT DISTINGUISH THAT FROM
// CORRECT. A closed loop ratifies an inverted bit order, a shifted offset and a
// swapped endianness with equal enthusiasm.
//
// So this test reads tables THIS PROJECT DID NOT WRITE.
//
// An .SCX is a VFP form, a .VCX a VFP class library. Both are DBF-format tables
// authored by Visual FoxPro itself, and neither is named `.dbf` -- which is exactly
// why the first sweep of this repository missed them: it globbed `*.dbf` and
// reported that byte 18 and byte 23 agree on every table we own. THAT WAS FALSE,
// and it was false in the direction that made the old code look harmless. Measured
// over `git ls-files` by MAGIC BYTE rather than extension: 59 tracked DBF-format
// files, and 7 of them disagree between the two bytes.
//
// All seven disagree in the same place. `OBJCODE` is the memo holding compiled
// object code, and VFP marks it BINARY (0x04 at byte 18) on purpose, so that no
// codepage translation is ever applied to compiled code. Byte 23 on those same
// files is 0x00.
//
//     OLD code: flags = byte 23 = 0x00  ->  binary = FALSE   WRONG
//     NEW code: flags = byte 18 = 0x04  ->  binary = TRUE    RIGHT
//
// This test goes RED under the old layout on a file we did not author. That is the
// discriminator the hand-computed tables cannot be.
//
// SCOPE. This began by proving the BINARY bit only: no tracked file carried 0x02 at
// byte 18, so nullability and the `_NullFlags` column were hand-computed-table
// evidence and the paragraph here said "that half of R1a is still owed and still
// wants a nullable table authored in VFP."
//
// IT ARRIVED. `fixtures/nullfix.DBF` was created inside Visual FoxPro 9 on
// 2026-09-04 -- a nullable N, a nullable Varchar, a plain Varchar, a plain C, and
// therefore the `_NullFlags` system column this engine had never seen on real
// output. nullfix_fixture() below reads it THROUGH THE LOADER and grades what the
// loader does with it: the null bit, the system partition, the recovered offset.
// The BIT LAYOUT inside the bitmap is graded separately and by hand in
// dottalkpp_vfp_nullfix_r1a_test; this is the decode PATH, that is the format.
//
// READ-ONLY BY CONSTRUCTION: fixtures are report-only. This opens each file with a
// bare std::ifstream in binary mode and never constructs a writable area over one.
//
// A MISSING FIXTURE IS A FAILURE, NOT A SKIP. A test that quietly passes when its
// evidence is absent is the exact shape this whole lane exists to correct.

#include "xbase.hpp"
#include "xbase_vfp.hpp"

#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

#ifndef VFP_FIXTURE_ROOT
#error "VFP_FIXTURE_ROOT must be defined by the build -- the test cannot guess where the tree is"
#endif

namespace {

int g_failures = 0;

void check(bool ok, const std::string& what)
{
    if (ok) return;
    std::printf("  FAIL: %s\n", what.c_str());
    ++g_failures;
}

// Parse one real table's field descriptors THROUGH THE ENGINE'S OWN LOADER, not
// through a reimplementation of it in the test. `vfp_loader::readFields` is the
// function that had the defect; a test that walked the descriptors itself would be
// grading a copy.
bool load_into(const std::string& path,
               xbase::DbArea& area,
               std::vector<xbase::VfpFieldExtras>& extras_out,
               std::uint8_t& version_out)
{
    std::ifstream fp(path, std::ios::binary);
    if (!fp) return false;

    version_out = xbase::vfp_loader::peekVersion(fp);
    area.setVersionByte(version_out);

    fp.clear();
    fp.seekg(static_cast<std::streamoff>(sizeof(xbase::HeaderRec)), std::ios::beg);

    extras_out.clear();
    xbase::vfp_loader::readFields(area, fp, extras_out);
    return true;
}

// The area is a local here on purpose: DbArea is not copied out, it is filled in
// place. Callers that need to interrogate the AREA (and not just its field vector)
// use load_into directly.
bool load_extras(const std::string& path,
                 std::vector<xbase::FieldDef>& fields_out,
                 std::vector<xbase::VfpFieldExtras>& extras_out,
                 std::uint8_t& version_out)
{
    xbase::DbArea area;
    if (!load_into(path, area, extras_out, version_out)) return false;
    fields_out = area.fields();
    return true;
}

// One 32-bit little-endian field read straight out of the file, for the places
// where the test must not ask the loader what the loader wrote.
bool raw_bytes_at(const std::string& path, std::size_t off, std::size_t n,
                  std::vector<std::uint8_t>& out)
{
    std::ifstream fp(path, std::ios::binary);
    if (!fp) return false;
    out.assign(n, 0);
    fp.seekg(static_cast<std::streamoff>(off), std::ios::beg);
    fp.read(reinterpret_cast<char*>(out.data()), static_cast<std::streamsize>(n));
    return fp.good() || fp.gcount() == static_cast<std::streamsize>(n);
}

int index_of_field(const std::vector<xbase::FieldDef>& fields, const char* name)
{
    for (std::size_t i = 0; i < fields.size(); ++i)
        if (fields[i].name == name) return static_cast<int>(i);
    return -1;
}

// ---------------------------------------------------------------------------
// The seven files that disagree, and the one that does not.
//
// `expect_binary_field` is the field VFP marked binary, or nullptr for a table
// this engine wrote -- the negative control, which must report NO binary field at
// all. Without the control a decoder that answered "binary" unconditionally would
// pass every positive case here.
// ---------------------------------------------------------------------------
struct Fixture {
    const char* rel_path;
    const char* expect_binary_field;   // nullptr => expect none
    const char* what_it_is;
};

const Fixture FIXTURES[] = {
    { "fixtures/ACCOUNTS.SCX",         "OBJCODE", "VFP form (screen table)"    },
    { "fixtures/STUDENTS.SCX",         "OBJCODE", "VFP form (screen table)"    },
    { "fixtures/TEST_APP.VCX",         "OBJCODE", "VFP class library"          },
    { "fixtures/X64FORM_SAMEDIR.SCX",  "OBJCODE", "VFP form (screen table)"    },
    { "fixtures/X64FORM_VFPSAVED.SCX", "OBJCODE", "VFP form (screen table)"    },
    { "fixtures/form1.scx",            "OBJCODE", "VFP form (screen table)"    },
    { "generated/x64form.scx",         "OBJCODE", "VFP form (screen table)"    },
    { "fixtures/ACCOUNTS.DBF",         nullptr,   "table THIS ENGINE wrote -- control" },
};

void one_fixture(const Fixture& fx)
{
    const std::string path = std::string(VFP_FIXTURE_ROOT) + "/" + fx.rel_path;

    std::vector<xbase::FieldDef>        fields;
    std::vector<xbase::VfpFieldExtras>  extras;
    std::uint8_t ver = 0;

    if (!load_extras(path, fields, extras, ver)) {
        check(false, "fixture is MISSING or unreadable: " + path +
                     "  -- this is a failure, not a skip; the evidence is the test");
        return;
    }

    std::printf("  %-34s ver=0x%02X fields=%2d  (%s)\n",
                fx.rel_path, ver, static_cast<int>(fields.size()), fx.what_it_is);

    check(fields.size() == extras.size(),
          std::string(fx.rel_path) + ": extras is parallel to fields");
    if (fields.size() != extras.size()) return;

    check(!fields.empty(), std::string(fx.rel_path) + ": has at least one field");

    // Count what the decoder claims, so an unconditional answer cannot hide.
    int binary_count = 0;
    for (std::size_t i = 0; i < extras.size(); ++i)
        if (extras[i].binary) ++binary_count;

    if (fx.expect_binary_field == nullptr) {
        check(binary_count == 0,
              std::string(fx.rel_path) +
              ": a table this engine wrote must report NO binary field"
              " (control -- if this reds, the decoder is answering unconditionally)");
        return;
    }

    const int idx = index_of_field(fields, fx.expect_binary_field);
    check(idx >= 0, std::string(fx.rel_path) + ": has a field named " +
                    fx.expect_binary_field);
    if (idx < 0) return;

    const xbase::VfpFieldExtras& ex = extras[static_cast<std::size_t>(idx)];

    // THE DISCRIMINATOR. Under the old layout this reads byte 23 == 0x00 and the
    // field decodes as NOT binary.
    check(ex.binary,
          std::string(fx.rel_path) + ": " + fx.expect_binary_field +
          " is BINARY -- 0x04 at byte 18, written by Visual FoxPro"
          " (under the old byte-23 layout this reads 0x00 and goes false)");

    check(fields[static_cast<std::size_t>(idx)].type == 'M',
          std::string(fx.rel_path) + ": " + fx.expect_binary_field + " is a memo field");

    // The same byte says these are all clear, so a decoder that simply returned
    // true everywhere would fail here.
    check(!ex.nullable,
          std::string(fx.rel_path) + ": " + fx.expect_binary_field + " is NOT nullable");
    check(!ex.system,
          std::string(fx.rel_path) + ": " + fx.expect_binary_field + " is NOT a system field");
    check(!ex.autoincrement,
          std::string(fx.rel_path) + ": " + fx.expect_binary_field + " is NOT autoincrementing");

    check(binary_count == 1,
          std::string(fx.rel_path) + ": EXACTLY ONE binary field, not a blanket yes");
}

// ---------------------------------------------------------------------------
// nullfix.DBF -- THE OTHER HALF OF R1a, READ THROUGH THE LOADER.
//
// Everything above grades one bit (binary) on tables that happen to be VFP forms.
// This grades the shape the lane is actually for: a table with NULLABLE fields and
// the hidden `_NullFlags` system column, authored by Visual FoxPro, decoded by
// vfp_loader::readFields and partitioned by DbArea::partitionTrailingSystemField.
//
// Read the file with a hex dump beside this list; every number here came out of it:
//
//   ver 0x32   hdrlen 456   reclen 31   3 records
//   ID          N   4   byte18 0x02   nullable
//   VNAME       V  10   byte18 0x02   nullable          <- also varlength: TWO bits
//   VFULL       V  10   byte18 0x00
//   PLAIN       C   5   byte18 0x00
//   _NullFlags  0   1   byte18 0x05   system AND BINARY
// ---------------------------------------------------------------------------
void nullfix_fixture()
{
    const char* rel = "fixtures/nullfix.DBF";
    const std::string path = std::string(VFP_FIXTURE_ROOT) + "/" + rel;

    xbase::DbArea area;
    std::vector<xbase::VfpFieldExtras> extras;
    std::uint8_t ver = 0;

    if (!load_into(path, area, extras, ver)) {
        check(false, std::string(rel) + ": MISSING or unreadable -- this is a failure,"
                     " not a skip. Rebuild with tools/vfp/make_nullfix.prg inside VFP 9.");
        return;
    }

    const std::vector<xbase::FieldDef>& fields = area.fields();
    std::printf("  %-34s ver=0x%02X fields=%2d  (%s)\n",
                rel, ver, static_cast<int>(fields.size()),
                "VFP table with nullable fields -- authored in VFP 9");

    // 0x32 is the varchar-capable flavor. A V field cannot exist below it.
    check(ver == 0x32, std::string(rel) + ": version byte 0x32 (Varchar-capable VFP)");

    // THE PARTITION. Five descriptors are on disk; the user must see FOUR.
    check(fields.size() == 4,
          std::string(rel) + ": _NullFlags is partitioned OUT -- fields() has 4, not 5");
    check(extras.size() == fields.size(),
          std::string(rel) + ": extras stays parallel after the pop");
    check(index_of_field(fields, "_NullFlags") < 0,
          std::string(rel) + ": no field named _NullFlags survives into fields()"
          " (it is a system column, not a junk 1-byte binary column)");
    if (fields.size() != 4 || extras.size() != 4) return;

    struct Want { const char* name; char type; int len; bool nullable; };
    const Want wanted[4] = {
        { "ID",    'N',  4, true  },
        { "VNAME", 'V', 10, true  },
        { "VFULL", 'V', 10, false },
        { "PLAIN", 'C',  5, false }
    };
    int nullable_count = 0;
    for (int i = 0; i < 4; ++i) {
        const std::string tag = std::string(rel) + ": field " + wanted[i].name;
        check(fields[i].name == wanted[i].name, tag + " is at physical position " +
              std::to_string(i) + " (order is load-bearing for the bitmap)");
        check(fields[i].type == wanted[i].type, tag + " type");
        check(static_cast<int>(fields[i].length) == wanted[i].len, tag + " length");
        check(extras[i].nullable == wanted[i].nullable,
              tag + (wanted[i].nullable ? " IS nullable (0x02 at byte 18)"
                                        : " is NOT nullable"));
        check(!extras[i].system, tag + " is not a system field");
        if (extras[i].nullable) ++nullable_count;
    }
    // Two, not four: a decoder answering "nullable" unconditionally fails here.
    check(nullable_count == 2,
          std::string(rel) + ": EXACTLY TWO nullable fields, not a blanket yes");

    // THE HIDDEN COLUMN, and where the engine thinks it sits.
    const xbase::NullFlagsColumn& nf = area.nullFlagsColumn();
    check(nf.present, std::string(rel) + ": nullFlagsColumn() reports present");
    check(nf.name == "_NullFlags",
          std::string(rel) + ": the column is named as the descriptor spelled it");
    check(nf.length == 1,
          std::string(rel) + ": bitmap is 1 byte -- 4 bits (ID null, VNAME full,"
          " VNAME null, VFULL full) round up to one");
    check(!area.systemFieldNotLast(),
          std::string(rel) + ": the system field IS last, so the partition was taken"
          " rather than declined");

    // THE OFFSET, CHECKED AGAINST VFP AND NOT AGAINST OURSELVES.
    //
    // partitionTrailingSystemField() computes the offset by ACCUMULATING FIELD
    // LENGTHS from 1 -- the same arithmetic fieldByteOffset_() uses, and it ignores
    // the `displacement` VFP wrote into descriptor bytes 12-15. If those two ever
    // disagree, every field offset in the record is wrong and no hand-computed test
    // in this lane can see it. So read the displacement out of the file and compare.
    std::vector<std::uint8_t> disp;
    const std::size_t nullflags_desc = 32 + 4 * 32;      // 5th descriptor
    if (raw_bytes_at(path, nullflags_desc + 12, 4, disp) && disp.size() == 4) {
        const std::size_t vfp_disp =
            (std::size_t)disp[0] | ((std::size_t)disp[1] << 8) |
            ((std::size_t)disp[2] << 16) | ((std::size_t)disp[3] << 24);
        check(nf.offset == vfp_disp,
              std::string(rel) + ": our accumulated offset (" + std::to_string(nf.offset) +
              ") equals the displacement VISUAL FOXPRO wrote (" + std::to_string(vfp_disp) +
              ") -- these are computed by different means and must agree");
        check(nf.offset == 30,
              std::string(rel) + ": offset 30 = 1 delete flag + 4 + 10 + 10 + 5");
    } else {
        check(false, std::string(rel) + ": could not read the _NullFlags displacement");
    }

    // WHAT THE LOADER DELIBERATELY DROPS, read raw so the fact is on the record:
    // the flags byte of the partitioned column. VFP marks its own hidden column
    // 0x05 -- SYSTEM (0x01) *and* BINARY (0x04). The M1 design doc told the CREATE
    // path to write 0x01. Reading is unaffected; writing 0x01 would produce a column
    // VFP does not mark the way VFP marks its own.
    std::vector<std::uint8_t> fl;
    if (raw_bytes_at(path, nullflags_desc + 18, 1, fl) && fl.size() == 1) {
        check(fl[0] == 0x05,
              std::string(rel) + ": _NullFlags byte 18 is 0x05 (system|binary), NOT 0x01"
              " -- what CREATE must write");
    } else {
        check(false, std::string(rel) + ": could not read the _NullFlags flags byte");
    }
}

} // namespace

int main()
{
    std::printf("AIF-091 M1 -- field flags decoded from files Visual FoxPro wrote\n");
    std::printf("  OBJCODE carries 0x04 (binary) at byte 18 and 0x00 at byte 23.\n");
    std::printf("  Reading byte 23 -- what this engine did until 2026-09-04 -- gets it backwards.\n");
    std::printf("  fixture root: %s\n\n", VFP_FIXTURE_ROOT);

    for (const Fixture& fx : FIXTURES)
        one_fixture(fx);

    std::printf("\n  -- nullable fixture (R1a), decoded through the loader --\n");
    nullfix_fixture();

    if (g_failures == 0) {
        std::printf("\nPASS -- real VFP output agrees with byte 18 and disagrees with byte 23.\n");
        return 0;
    }
    std::printf("\nFAIL -- %d expectation(s) missed.\n", g_failures);
    return 1;
}
