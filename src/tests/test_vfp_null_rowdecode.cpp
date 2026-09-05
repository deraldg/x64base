// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// status: experimental
//
// AIF-091 M1 -- THE PER-ROW NULL DECODE, THROUGH A REAL OPEN.
//
// The other tests in this lane stop at the field descriptors. This one goes the
// rest of the way: DbArea::open() -> gotoRec() -> fieldIsNullFromBuffer(), which
// is the path a consumer will actually take. Design doc section 6 asks for the
// fixture read "through the loader AND the getters"; the loader half landed in
// dottalkpp_vfp_real_fixture_flags_test, and this is the getter half.
//
// ---------------------------------------------------------------------------
// IT OPENS A COPY, AND THAT IS NOT FASTIDIOUSNESS
// ---------------------------------------------------------------------------
//
// DbArea::open() opens with `std::ios::in | std::ios::out`. Fixtures in this
// repository are REPORT-ONLY -- dottalkpp_vfp_real_fixture_flags_test says so in
// its own header and uses a bare ifstream to honour it. A test that opened
// nullfix.DBF writable would put the lane's only real-file evidence one stray
// write away from being evidence of nothing, and the failure would be silent: the
// file would still parse, still pass, and no longer be what Visual FoxPro wrote.
//
// So the fixture is copied to a scratch path and the COPY is opened. The copy is
// removed at the end; if this test crashes, a stale copy in the temp directory is
// the harmless outcome.
//
// ---------------------------------------------------------------------------
// THE TRUTH TABLE COMES FROM THE GENERATOR, NOT FROM THE BITMAP
// ---------------------------------------------------------------------------
//
// tools/vfp/make_nullfix.prg is what told Visual FoxPro which cells to null:
//
//   row 1  (1,      "ABC",        "0123456789", "XY")
//   row 2  (.NULL., .NULL.,       "AB",         "ZZ")
//   row 3  (2,      "0123456789", "C",          "QQ")
//   row 4  (.NULL., "AB",         "0123456789", "RR")
//   row 5  (3,      .NULL.,       "0123456789", "SS")
//
// The expectations below are transcribed from THOSE lines. They are not derived
// from the `_NullFlags` bytes, because deriving them from the bytes would make
// this test agree with the decoder by construction -- the same closed loop that
// let a writer and a reader share a wrong byte offset for the life of this
// project. Two independent statements of the same fact, and they have to match.
//
// VFULL and PLAIN are the controls: neither is nullable, so a decoder that
// answered "null" whenever the bitmap was non-zero would fail on rows 1-5, every
// one of which has at least one bit set.

#include "xbase.hpp"

#include <cstdio>
#include <filesystem>
#include <string>
#include <system_error>

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

// row (1-based) x field (1-based ID,VNAME,VFULL,PLAIN) -> is that cell .NULL.
// Transcribed from make_nullfix.prg. See the header note.
const bool EXPECT_NULL[5][4] = {
    /* row 1 */ { false, false, false, false },
    /* row 2 */ { true,  true,  false, false },
    /* row 3 */ { false, false, false, false },
    /* row 4 */ { true,  false, false, false },
    /* row 5 */ { false, true,  false, false }
};

const char* FIELD_NAME[4] = { "ID", "VNAME", "VFULL", "PLAIN" };

std::string row_tag(int r) { return "row " + std::to_string(r); }

// Copy a fixture to a scratch path and make the COPY writable.
//
// MEASURED THE HARD WAY 2026-09-05: the first version of this test copied
// ACCOUNTS.DBF and then failed to open it, errno=13 / GetLastError=5. The fixture
// carries the read-only attribute on disk -- which is the report-only policy doing
// exactly its job -- and std::filesystem::copy_file PROPAGATES that attribute, so
// the copy inherits the protection and DbArea::open() (ios::in|ios::out) is denied.
//
// The fix belongs here and not on the fixture. A test that needed a fixture to be
// writable in order to run would be one `git checkout` away from quietly changing
// what the evidence is. The destination is removed first because overwrite_existing
// onto a read-only file fails the same way.
bool stage_writable_copy(const std::filesystem::path& src,
                         const std::filesystem::path& dst,
                         std::string& err)
{
    namespace fs = std::filesystem;
    std::error_code ec;

    // ORDER MATTERS. On Windows, remove() on a read-only file is ALSO access-denied,
    // and the first run of this test left exactly such a file behind. So clear the
    // attribute first, then remove. Both steps ignore errors: the usual case is that
    // the file simply is not there.
    fs::permissions(dst, fs::perms::owner_write, fs::perm_options::add, ec);
    ec.clear();
    fs::remove(dst, ec);
    ec.clear();

    fs::copy_file(src, dst, fs::copy_options::overwrite_existing, ec);
    if (ec) { err = "copy_file: " + ec.message(); return false; }

    fs::permissions(dst, fs::perms::owner_write, fs::perm_options::add, ec);
    if (ec) { err = "could not make the copy writable: " + ec.message(); return false; }

    return true;
}

} // namespace

int main()
{
    namespace fs = std::filesystem;

    const fs::path src = fs::path(VFP_FIXTURE_ROOT) / "fixtures" / "nullfix.DBF";
    std::printf("AIF-091 M1 -- per-row null decode through DbArea::open()\n");
    std::printf("  fixture: %s\n", src.string().c_str());

    if (!fs::exists(src)) {
        std::printf("  FAIL: fixture missing -- this is a failure, not a skip.\n"
                    "        Rebuild with tools/vfp/make_nullfix.prg inside VFP 9.\n");
        return 1;
    }

    // THE COPY. See the header: the fixture itself is never opened writable.
    std::error_code ec;
    const fs::path work =
        fs::temp_directory_path(ec) / "x64base_nullfix_rowdecode.DBF";
    if (ec) { std::printf("  FAIL: no temp directory: %s\n", ec.message().c_str()); return 1; }

    std::string cperr;
    if (!stage_writable_copy(src, work, cperr)) {
        std::printf("  FAIL: could not stage the fixture at %s -- %s\n",
                    work.string().c_str(), cperr.c_str());
        return 1;
    }
    std::printf("  working copy: %s\n\n", work.string().c_str());

    {
        xbase::DbArea area;
        try {
            area.open(work.string());
        } catch (const std::exception& e) {
            std::printf("  FAIL: open() threw: %s\n", e.what());
            fs::remove(work, ec);
            return 1;
        }

        // ---- table-level facts -------------------------------------------
        check(area.versionByte() == 0x32, "version byte 0x32");
        check(area.fields().size() == 4,
              "four user fields -- _NullFlags partitioned out by the open path too,"
              " not only by the loader test's hand-rolled call");
        check(area.nullFlagsColumn().present, "nullFlagsColumn() present after open()");
        check(!area.systemFieldNotLast(), "the partition was taken, not declined");
        check(area.recCount64() == 5, "five records (recCount64 -- the authoritative count)");
        if (area.fields().size() != 4) { fs::remove(work, ec); return 1; }

        // NULLABILITY IS A TABLE PROPERTY. Asserted separately from nullness so a
        // predicate that confuses the two cannot pass both halves.
        check(area.fieldIsNullable(1),  "ID is nullable");
        check(area.fieldIsNullable(2),  "VNAME is nullable");
        check(!area.fieldIsNullable(3), "VFULL is NOT nullable");
        check(!area.fieldIsNullable(4), "PLAIN is NOT nullable");
        check(!area.fieldIsNullable(0), "index 0 is out of range and answers false");
        check(!area.fieldIsNullable(5), "index 5 is out of range and answers false");

        const auto& lay = area.nullBitLayout();
        check(lay.fields.size() == 4, "layout is parallel to the USER field vector");
        check(lay.byte_count == area.nullFlagsColumn().length,
              "computed bitmap width matches the width VFP wrote");

        // ---- the rows ----------------------------------------------------
        int nulls_seen = 0;
        for (int r = 1; r <= 5; ++r) {
            check(area.gotoRec(r), row_tag(r) + " -- gotoRec()");
            for (int f = 1; f <= 4; ++f) {
                const bool want = EXPECT_NULL[r - 1][f - 1];
                const bool got  = area.fieldIsNullFromBuffer(f);
                if (got) ++nulls_seen;
                check(got == want,
                      row_tag(r) + " " + FIELD_NAME[f - 1] + " -- expected " +
                      (want ? "NULL" : "not null") + ", decoder said " +
                      (got ? "NULL" : "not null"));
            }
        }

        // Four .NULL. cells across the five rows, per the generator. A decoder
        // stuck on "true" would report 20; one stuck on "false" would report 0,
        // and would pass 16 of the 20 checks above on its way there.
        check(nulls_seen == 4,
              "exactly FOUR null cells in the table -- not a decoder stuck on one answer");

        // Out-of-range must be inert rather than reading past the buffer.
        check(area.gotoRec(1), "back to row 1");
        check(!area.fieldIsNullFromBuffer(0),   "field index 0 answers false");
        check(!area.fieldIsNullFromBuffer(5),   "field index 5 (the partitioned column) answers false");
        check(!area.fieldIsNullFromBuffer(-1),  "negative field index answers false");
        check(!area.fieldIsNullFromBuffer(999), "far out-of-range answers false");
    }

    // ---- negative control: a table with no bitmap at all ------------------
    //
    // ACCOUNTS.DBF was written by this engine and has no nullable field and no
    // `_NullFlags` column. Every answer must be false, and nothing may crash.
    // Without this, a predicate that dereferenced an empty layout would only be
    // caught the first time a plain table met it in the field.
    {
        const fs::path ctl_src = fs::path(VFP_FIXTURE_ROOT) / "fixtures" / "ACCOUNTS.DBF";
        if (!fs::exists(ctl_src)) {
            check(false, "control fixture ACCOUNTS.DBF is missing");
        } else {
            const fs::path ctl = fs::temp_directory_path(ec) / "x64base_accounts_rowdecode.DBF";
            std::string ctlerr;
            if (!stage_writable_copy(ctl_src, ctl, ctlerr)) {
                check(false, "could not stage the control fixture: " + ctlerr);
            } else {
                xbase::DbArea a2;
                try {
                    a2.open(ctl.string());
                    check(!a2.nullFlagsColumn().present,
                          "control -- a table this engine wrote has NO _NullFlags column");
                    check(a2.nullBitLayout().fields.empty(),
                          "control -- no bitmap means no layout, not a layout of zeros");
                    if (a2.recCount64() > 0 && a2.gotoRec(1)) {
                        bool any = false;
                        for (int f = 1; f <= static_cast<int>(a2.fields().size()); ++f) {
                            if (a2.fieldIsNullable(f)) any = true;
                            if (a2.fieldIsNullFromBuffer(f)) any = true;
                        }
                        check(!any,
                              "control -- nothing is nullable and nothing is null,"
                              " and asking did not crash");
                    }
                } catch (const std::exception& e) {
                    check(false, std::string("control open() threw: ") + e.what());
                }
                fs::permissions(ctl, fs::perms::owner_write, fs::perm_options::add, ec);
                ec.clear();
                fs::remove(ctl, ec);
            }
        }
    }

    // Leave nothing read-only behind for the next run to trip over.
    fs::permissions(work, fs::perms::owner_write, fs::perm_options::add, ec);
    ec.clear();
    fs::remove(work, ec);   // best effort; a stale temp copy is harmless

    if (g_failures) {
        std::printf("\nFAIL -- %d expectation(s) missed.\n", g_failures);
        return 1;
    }
    std::printf("\nPASS -- every row's null map matches what make_nullfix.prg told VFP to write.\n");
    return 0;
}
