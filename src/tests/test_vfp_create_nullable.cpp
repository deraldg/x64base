// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// status: experimental
//
// AIF-091 M2 -- OUR CREATE, GRADED AGAINST VISUAL FOXPRO'S OWN OUTPUT.
//
// THIS IS DELIBERATELY NOT A ROUND TRIP. Every other lane in this project
// proves a writer by reading its output back, and this lane exists because that
// proves nothing: dbf_create.cpp and the reader shared a wrong field-flags
// offset for the life of the project, each ratifying the other, and a
// create-then-read test was green throughout.
//
// So the expected bytes here are not hand-computed and not read back through
// our loader. THEY ARE TAKEN FROM tools/vfp/fixtures/nullfix.DBF, which Visual
// FoxPro 9 wrote. This test builds the SAME SCHEMA through create_dbf() and
// compares the two files field by field. VFP is the authority; where we differ,
// we are wrong.
//
//     nullfix.DBF   CREATE TABLE nullfix (id N(4) NULL, vname V(10) NULL,
//                                         vfull V(10), plain C(5))   <- VFP wrote this
//     this test     the identical schema through xbase::dbf_create::create_dbf
//
// WHAT IS DELIBERATELY NOT COMPARED, and why each one is legitimately allowed
// to differ rather than being an excuse:
//
//   the date stamp   bytes 1-3 are the day the file was written.
//   record count     VFP's fixture has five rows; ours is empty by construction.
//   the codepage     VFP wrote what its session was set to; CREATE writes
//                    CP_WINDOWS_ANSI. A real difference, out of scope here, and
//                    named so it is not mistaken for agreement.
//   field-name CASE  VFP uppercases; CREATE preserves what the caller typed.
//                    Compared case-insensitively, and flagged as a genuine open
//                    question rather than quietly normalized away.
//
// EVERYTHING STRUCTURAL IS COMPARED EXACTLY: version byte, header length,
// record length, field count, and per field the type, width, decimals, flags
// byte and displacement.
//
// A MISSING FIXTURE IS A FAILURE, NOT A SKIP.

#include "xbase/dbf_create.hpp"

#include <cstdio>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#ifndef VFP_FIXTURE_ROOT
#error "VFP_FIXTURE_ROOT must be defined by the build"
#endif

namespace {

int g_failures = 0;

void check(bool ok, const std::string& what)
{
    if (ok) return;
    std::printf("  FAIL: %s\n", what.c_str());
    ++g_failures;
}

void check_eq(long long got, long long want, const std::string& what)
{
    if (got == want) return;
    std::printf("  FAIL: %s -- got %lld (0x%llX), want %lld (0x%llX)\n",
                what.c_str(), got, (unsigned long long)got,
                want, (unsigned long long)want);
    ++g_failures;
}

struct Desc {
    std::string  name;
    char         type {0};
    std::uint32_t disp {0};
    std::uint8_t len {0};
    std::uint8_t dec {0};
    std::uint8_t flags {0};
};

struct Table {
    std::uint8_t  version {0};
    std::size_t   hdr_len {0};
    std::size_t   rec_len {0};
    std::vector<Desc> fields;
};

std::string upper(std::string s)
{
    for (char& c : s) if (c >= 'a' && c <= 'z') c = (char)(c - 'a' + 'A');
    return s;
}

// Parse a DBF header BY HAND. Not through our loader -- the loader is the thing
// the writer must be independent of.
bool parse(const std::filesystem::path& p, Table& t, std::string& err)
{
    std::ifstream f(p, std::ios::binary);
    if (!f) { err = "cannot open " + p.string(); return false; }
    std::vector<std::uint8_t> b((std::istreambuf_iterator<char>(f)),
                                 std::istreambuf_iterator<char>());
    if (b.size() < 66) { err = "too small: " + p.string(); return false; }

    t.version = b[0];
    t.hdr_len = (std::size_t)b[8]  | ((std::size_t)b[9]  << 8);
    t.rec_len = (std::size_t)b[10] | ((std::size_t)b[11] << 8);

    for (std::size_t off = 32; off + 32 <= b.size() && b[off] != 0x0D; off += 32) {
        Desc d;
        for (std::size_t i = 0; i < 11 && b[off + i]; ++i)
            d.name.push_back((char)b[off + i]);
        d.type  = (char)b[off + 11];
        d.disp  = (std::uint32_t)b[off+12] | ((std::uint32_t)b[off+13] << 8)
                | ((std::uint32_t)b[off+14] << 16) | ((std::uint32_t)b[off+15] << 24);
        d.len   = b[off + 16];
        d.dec   = b[off + 17];
        d.flags = b[off + 18];
        t.fields.push_back(d);
    }
    return true;
}

} // namespace

int main()
{
    namespace fs = std::filesystem;
    using xbase::dbf_create::FieldSpec;
    using xbase::dbf_create::Flavor;

    std::printf("AIF-091 M2 -- our CREATE compared with Visual FoxPro's own output\n");

    // ---- the authority --------------------------------------------------
    const fs::path ref = fs::path(VFP_FIXTURE_ROOT) / "fixtures" / "nullfix.DBF";
    if (!fs::exists(ref)) {
        std::printf("  FAIL: fixture missing -- a failure, not a skip. This test has\n"
                    "        no expected values of its own; the fixture IS them.\n");
        return 1;
    }
    Table vfp;
    std::string err;
    if (!parse(ref, vfp, err)) { std::printf("  FAIL: %s\n", err.c_str()); return 1; }
    std::printf("  reference : %s  (VFP 9 wrote this)\n", ref.string().c_str());

    // ---- V is now an accepted CREATE type for VFP, and only for VFP ------
    check(xbase::dbf_create::supports_type_now('V', Flavor::VFP),
          "V is accepted for CREATE VFP");
    check(!xbase::dbf_create::supports_type_now('V', Flavor::X64),
          "V is still REFUSED for CREATE X64 -- whether x64 wants VFP's hidden-bitmap"
          " mechanism is an open design question, not a side effect of a shared switch");
    check(!xbase::dbf_create::supports_type_now('V', Flavor::MSDOS),
          "V is still refused for MSDOS");

    // ---- build the same schema ------------------------------------------
    std::vector<FieldSpec> spec;
    { FieldSpec f; f.name="ID";    f.type='N'; f.len=4;  f.dec=0; f.nullable=true;  spec.push_back(f); }
    { FieldSpec f; f.name="VNAME"; f.type='V'; f.len=10; f.dec=0; f.nullable=true;  spec.push_back(f); }
    { FieldSpec f; f.name="VFULL"; f.type='V'; f.len=10; f.dec=0; f.nullable=false; spec.push_back(f); }
    { FieldSpec f; f.name="PLAIN"; f.type='C'; f.len=5;  f.dec=0; f.nullable=false; spec.push_back(f); }

    std::error_code ec;
    const fs::path out = fs::temp_directory_path(ec) / "x64base_create_nullable.dbf";
    fs::permissions(out, fs::perms::owner_write, fs::perm_options::add, ec); ec.clear();
    fs::remove(out, ec); ec.clear();

    std::string cerr_;
    if (!xbase::dbf_create::create_dbf(out.string(), spec, Flavor::VFP, cerr_)) {
        std::printf("  FAIL: create_dbf refused: %s\n", cerr_.c_str());
        return 1;
    }
    Table ours;
    if (!parse(out, ours, err)) { std::printf("  FAIL: %s\n", err.c_str()); return 1; }
    std::printf("  ours      : %s\n\n", out.string().c_str());

    // ---- the comparison --------------------------------------------------
    check_eq(ours.version, vfp.version,
             "version byte matches VFP (0x32 -- the varchar-capable flavor; a V field"
             " cannot exist below it, and VER_VFP_VARCHAR had no caller until now)");
    check_eq((long long)ours.rec_len, (long long)vfp.rec_len,
             "record length matches VFP -- the hidden column's byte is IN it");
    check_eq((long long)ours.hdr_len, (long long)vfp.hdr_len,
             "header length matches VFP (32 + 32n + 1 + 263 backlink)");
    check_eq((long long)ours.fields.size(), (long long)vfp.fields.size(),
             "field count matches VFP -- FIVE descriptors for four declared columns");

    if (ours.fields.size() != vfp.fields.size()) {
        std::printf("\nFAIL -- field counts differ; per-field comparison skipped.\n");
        fs::remove(out, ec);
        return 1;
    }

    for (std::size_t i = 0; i < vfp.fields.size(); ++i) {
        const Desc& a = ours.fields[i];
        const Desc& b = vfp.fields[i];
        const std::string tag = "field " + std::to_string(i) + " (" + b.name + ") ";

        // Case-insensitive: VFP uppercases, CREATE preserves. A real difference,
        // named rather than normalized away -- see the header note.
        check(upper(a.name) == upper(b.name), tag + "name");
        check_eq(a.type,  b.type,  tag + "type");
        check_eq(a.len,   b.len,   tag + "width");
        check_eq(a.dec,   b.dec,   tag + "decimals");
        check_eq(a.disp,  b.disp,  tag + "displacement -- computed by our loop,"
                                          " compared against VFP's");
        check_eq(a.flags, b.flags, tag + "FLAGS BYTE 18");
    }

    // Said separately because it is the claim the design doc got wrong.
    const Desc& hid = ours.fields.back();
    check(hid.name == "_NullFlags", "the hidden column is named _NullFlags");
    check_eq(hid.type, '0', "the hidden column's type is the DIGIT ZERO");
    check_eq(hid.len, 1, "one byte holds this table's four bits");
    check_eq(hid.flags, 0x05,
             "hidden column flags are 0x05 (system|binary) -- the M1 design doc said"
             " 0x01, and VFP's own file says otherwise");

    // A table with nothing nullable and nothing variable must gain NO column,
    // and must NOT be bumped to 0x32. Without this the writer could append a
    // zero-bit bitmap to every table it makes and every check above would pass.
    {
        std::vector<FieldSpec> plain;
        { FieldSpec f; f.name="A"; f.type='C'; f.len=5; plain.push_back(f); }
        { FieldSpec f; f.name="B"; f.type='N'; f.len=4; plain.push_back(f); }
        const fs::path p2 = fs::temp_directory_path(ec) / "x64base_create_plain.dbf";
        fs::permissions(p2, fs::perms::owner_write, fs::perm_options::add, ec); ec.clear();
        fs::remove(p2, ec); ec.clear();
        std::string e2;
        if (xbase::dbf_create::create_dbf(p2.string(), plain, Flavor::VFP, e2)) {
            Table t2;
            if (parse(p2, t2, err)) {
                check_eq((long long)t2.fields.size(), 2,
                         "control -- a table with no nullable and no V field gains NO hidden column");
                check_eq(t2.version, 0x30,
                         "control -- and is NOT bumped to 0x32; only a V/Q table moves");
                check_eq((long long)t2.rec_len, 10,
                         "control -- record length is 1 + 5 + 4, with nothing extra");
            } else check(false, "control table unreadable: " + err);
        } else check(false, "control create_dbf refused: " + e2);
        fs::permissions(p2, fs::perms::owner_write, fs::perm_options::add, ec); ec.clear();
        fs::remove(p2, ec);
    }

    fs::permissions(out, fs::perms::owner_write, fs::perm_options::add, ec); ec.clear();
    fs::remove(out, ec);

    if (g_failures) {
        std::printf("\nFAIL -- %d expectation(s) missed against VFP's own output.\n", g_failures);
        return 1;
    }
    std::printf("\nPASS -- our CREATE emits the same structure Visual FoxPro emits.\n");
    return 0;
}
