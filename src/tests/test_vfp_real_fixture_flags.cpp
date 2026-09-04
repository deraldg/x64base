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
// SCOPE, STATED SO IT IS NOT OVERSOLD: this proves the BINARY bit against real VFP
// output. It proves nothing about the NULL bit -- no tracked file carries 0x02 at
// byte 18 -- so nullability and the `_NullFlags` bitmap remain hand-computed-table
// evidence only. That half of R1a is still owed and still wants a nullable table
// authored in VFP.
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
bool load_extras(const std::string& path,
                 std::vector<xbase::FieldDef>& fields_out,
                 std::vector<xbase::VfpFieldExtras>& extras_out,
                 std::uint8_t& version_out)
{
    std::ifstream fp(path, std::ios::binary);
    if (!fp) return false;

    version_out = xbase::vfp_loader::peekVersion(fp);

    xbase::DbArea area;
    area.setVersionByte(version_out);

    fp.clear();
    fp.seekg(static_cast<std::streamoff>(sizeof(xbase::HeaderRec)), std::ios::beg);

    extras_out.clear();
    xbase::vfp_loader::readFields(area, fp, extras_out);

    fields_out = area.fields();
    return true;
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

} // namespace

int main()
{
    std::printf("AIF-091 M1 -- field flags decoded from files Visual FoxPro wrote\n");
    std::printf("  OBJCODE carries 0x04 (binary) at byte 18 and 0x00 at byte 23.\n");
    std::printf("  Reading byte 23 -- what this engine did until 2026-09-04 -- gets it backwards.\n");
    std::printf("  fixture root: %s\n\n", VFP_FIXTURE_ROOT);

    for (const Fixture& fx : FIXTURES)
        one_fixture(fx);

    if (g_failures == 0) {
        std::printf("\nPASS -- real VFP output agrees with byte 18 and disagrees with byte 23.\n");
        return 0;
    }
    std::printf("\nFAIL -- %d expectation(s) missed.\n", g_failures);
    return 1;
}
