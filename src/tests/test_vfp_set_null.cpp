// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// status: experimental
//
// AIF-091 -- SET-TO-NULL, GRADED AGAINST BYTES VISUAL FOXPRO WROTE.
//
// THE EXPECTED VALUES ARE NOT IN THIS TEST AND ARE NOT COMPUTED BY IT. They are
// read out of tools/vfp/fixtures/nullfix.DBF, which Visual FoxPro 9 authored, and
// the trick that makes that possible is that the fixture ALREADY CONTAINS ROWS IN
// THE STATES THIS TEST PRODUCES:
//
//   row 1  (1,      "ABC",        "0123456789", "XY")   bitmap 0x02
//   row 4  (.NULL., "AB",         "0123456789", "RR")   bitmap 0x03   <- ID null
//   row 5  (3,      .NULL.,       "0123456789", "SS")   bitmap 0x06   <- VNAME null
//
// So: null row 1's ID with our engine and the bitmap must become the byte VFP
// wrote on row 4. Null row 1's VNAME and it must become the byte VFP wrote on
// row 5 -- AND the ten value bytes must match row 5's ten value bytes exactly,
// which is where the null-Varchar encoding is actually settled (spaces, then a
// trailing length byte of 0x00, with the varlength bit SET even though the field
// is empty).
//
// A create-then-read test of set-to-null would prove our encoder agrees with our
// decoder. This compares our encoder against VFP's, offline, using a file neither
// this test nor this engine wrote.
//
// ARM E (added 2026-09-05) RUNS THE OTHER DIRECTION and is graded the same way:
// write "ABC" over row 5's null VNAME and the row must become, byte for byte,
// what VFP wrote on ROW 1 -- bitmap 0x02 and 41 42 43 20 20 20 20 20 20 03. Both
// expectations are read out of the fixture at run time. It exists because every
// other instrument in this lane pointed ONE WAY, set-then-read, and a value write
// was silently re-committing the stale null bit.
//
// ---------------------------------------------------------------------------
// TWO COPIES, NOT ONE, AND THAT IS NOT FASTIDIOUSNESS
// ---------------------------------------------------------------------------
//
// Each arm starts from a PRISTINE copy of the fixture, because arm B's expected
// bitmap (0x06) is only correct if ID is NOT null. Run both arms against one copy
// and the second inherits the first's null, the expectation silently stops being
// a VFP-written byte, and the test would still pass -- against a number this file
// made up. Separate copies keep every expectation traceable to a row VFP wrote.
//
// The fixture itself is never opened writable: DbArea::open() wants
// ios::in|ios::out and fixtures here are report-only.

#include "xbase.hpp"

#include <algorithm>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <system_error>
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

std::string hexbyte(unsigned v)
{
    char b[8];
    std::snprintf(b, sizeof(b), "0x%02X", v & 0xFFu);
    return std::string(b);
}

// nullfix.DBF geometry, measured and asserted below rather than trusted.
constexpr std::size_t kHdr    = 456;   // 32 + 32*5 + 1 + 263 (VFP backlink)
constexpr std::size_t kRecLen = 31;
constexpr std::size_t kOffId    = 1;    // N(4)
constexpr std::size_t kOffVname = 5;    // V(10)
constexpr std::size_t kOffVfull = 15;   // V(10)
constexpr std::size_t kOffPlain = 25;   // C(5)
constexpr std::size_t kOffBits  = 30;   // _NullFlags

std::size_t rec_off(int r) { return kHdr + static_cast<std::size_t>(r - 1) * kRecLen; }

std::vector<char> slurp(const std::filesystem::path& p)
{
    std::ifstream f(p.string(), std::ios::binary);
    return std::vector<char>((std::istreambuf_iterator<char>(f)),
                              std::istreambuf_iterator<char>());
}

// See test_vfp_null_rowdecode.cpp for the full note. Clear the read-only
// attribute, remove, copy, then make writable -- copy_file PROPAGATES read-only
// and remove() on a read-only file is access-denied on Windows.
bool stage_writable_copy(const std::filesystem::path& src,
                         const std::filesystem::path& dst,
                         std::string& err)
{
    namespace fs = std::filesystem;
    std::error_code ec;
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

void drop(const std::filesystem::path& p)
{
    namespace fs = std::filesystem;
    std::error_code ec;
    fs::permissions(p, fs::perms::owner_write, fs::perm_options::add, ec);
    ec.clear();
    fs::remove(p, ec);
}

} // namespace

int main()
{
    namespace fs = std::filesystem;

    const fs::path src = fs::path(VFP_FIXTURE_ROOT) / "fixtures" / "nullfix.DBF";
    std::printf("AIF-091 -- set-to-null, graded against bytes Visual FoxPro wrote\n");
    std::printf("  fixture: %s\n\n", src.string().c_str());

    if (!fs::exists(src)) {
        std::printf("  FAIL: fixture missing -- a failure, not a skip.\n");
        return 1;
    }

    std::error_code ec;
    const fs::path tmp = fs::temp_directory_path(ec);
    if (ec) { std::printf("  FAIL: no temp directory\n"); return 1; }

    // ---- THE REFERENCE BYTES, taken from the pristine fixture -------------
    // Read once, before anything is written anywhere. These are VFP's answers.
    unsigned vfp_row1_bits = 0, vfp_row4_bits = 0, vfp_row5_bits = 0;
    std::string vfp_row4_id, vfp_row5_vname;
    {
        const std::vector<char> all = slurp(src);
        check(all.size() == 612, "fixture is 612 bytes, got " + std::to_string(all.size()));
        if (all.size() < 612) return 1;

        const auto u8 = [&](std::size_t i) { return static_cast<unsigned char>(all[i]); };

        // Geometry asserted, not assumed.
        const unsigned hdr = u8(8) | (u8(9) << 8);
        const unsigned rl  = u8(10) | (u8(11) << 8);
        check(hdr == kHdr, "fixture header length is 456, got " + std::to_string(hdr));
        check(rl == kRecLen, "fixture record length is 31, got " + std::to_string(rl));

        vfp_row1_bits = u8(rec_off(1) + kOffBits);
        vfp_row4_bits = u8(rec_off(4) + kOffBits);
        vfp_row5_bits = u8(rec_off(5) + kOffBits);

        vfp_row4_id.assign(all.data() + rec_off(4) + kOffId, 4);
        vfp_row5_vname.assign(all.data() + rec_off(5) + kOffVname, 10);

        // If these three are not what the lane recorded, the fixture changed and
        // every expectation below is void -- so say so here rather than let an
        // arm fail further down for a reason that has nothing to do with nulls.
        check(vfp_row1_bits == 0x02, "VFP row 1 bitmap is 0x02, got " + hexbyte(vfp_row1_bits));
        check(vfp_row4_bits == 0x03, "VFP row 4 bitmap is 0x03, got " + hexbyte(vfp_row4_bits));
        check(vfp_row5_bits == 0x06, "VFP row 5 bitmap is 0x06, got " + hexbyte(vfp_row5_bits));
        if (g_failures) {
            std::printf("\nFAIL -- the fixture is not the file this test was written against.\n");
            return 1;
        }
        std::printf("  VFP's own answers: row1 %s   row4(ID null) %s   row5(VNAME null) %s\n\n",
                    hexbyte(vfp_row1_bits).c_str(), hexbyte(vfp_row4_bits).c_str(),
                    hexbyte(vfp_row5_bits).c_str());
    }

    // ===================================================================
    // ARM A -- NULL A NUMERIC. Expect VFP's row-4 bitmap byte.
    // ===================================================================
    {
        const fs::path work = tmp / "x64base_setnull_numeric.DBF";
        std::string cperr;
        if (!stage_writable_copy(src, work, cperr)) {
            check(false, "arm A: could not stage the fixture -- " + cperr);
        } else {
            bool opened = true;
            {
                xbase::DbArea a;
                try { a.open(work.string()); }
                catch (const std::exception& e) {
                    check(false, std::string("arm A open() threw: ") + e.what());
                    opened = false;
                }
                if (opened) {
                check(a.gotoRec(1), "arm A: gotoRec(1)");
                check(!a.fieldIsNull(1), "arm A: ID starts NOT null (staged view)");
                check(!a.fieldIsNullFromBuffer(1), "arm A: ID starts NOT null (buffer)");
                std::string err;
                check(a.replaceFieldNull(1, true, &err),
                      "arm A: replaceFieldNull(ID) succeeded -- " +
                      (err.empty() ? std::string("no error") : err));

                // The staged predicate and the buffer predicate must now AGREE,
                // because the record was written. Before the write they would not,
                // and that difference is the reason both exist.
                check(a.fieldIsNull(1), "arm A: staged view says ID is null");
                check(a.fieldIsNullFromBuffer(1), "arm A: buffer says ID is null");
                check(!a.fieldIsNullFromBuffer(2), "arm A: VNAME is untouched (not null)");
                }
            }

            const std::vector<char> after = slurp(work);
            check(after.size() == 612, "arm A: file is still 612 bytes");
            if (opened && after.size() >= 612) {
                const auto u8 = [&](std::size_t i) { return static_cast<unsigned char>(after[i]); };
                const unsigned got = u8(rec_off(1) + kOffBits);

                // THE LOAD-BEARING COMPARISON OF THIS ARM.
                check(got == vfp_row4_bits,
                      "arm A: our bitmap after nulling ID is " + hexbyte(got) +
                      "; VFP wrote " + hexbyte(vfp_row4_bits) + " for a row in that state");

                // VFP leaves a null numeric's value area as SPACES. Compared to
                // VFP's own row 4, not to a constant typed here.
                const std::string our_id(after.data() + rec_off(1) + kOffId, 4);
                check(our_id == vfp_row4_id,
                      "arm A: our null ID bytes differ from VFP's null ID bytes");

                // The neighbours must not have moved. This is the AIF-110 shape:
                // a write that gets the interesting field right and quietly
                // rewrites the rest passes any test that only reads the field
                // under change.
                const std::string vfull_after(after.data() + rec_off(1) + kOffVfull, 10);
                check(vfull_after == "0123456789",
                      "arm A: VFULL untouched, got [" + vfull_after + "]");
                const std::string plain_after(after.data() + rec_off(1) + kOffPlain, 5);
                check(plain_after == "XY   ",
                      "arm A: PLAIN untouched, got [" + plain_after + "]");

                // And no other ROW moved.
                check(u8(rec_off(4) + kOffBits) == vfp_row4_bits, "arm A: row 4 untouched");
                check(u8(rec_off(5) + kOffBits) == vfp_row5_bits, "arm A: row 5 untouched");
            }
            drop(work);
        }
    }

    // ===================================================================
    // ARM B -- NULL A VARCHAR. Expect VFP's row-5 bitmap AND its value bytes.
    // This is where the null-Varchar encoding is actually settled.
    // ===================================================================
    {
        const fs::path work = tmp / "x64base_setnull_varchar.DBF";
        std::string cperr;
        if (!stage_writable_copy(src, work, cperr)) {
            check(false, "arm B: could not stage the fixture -- " + cperr);
        } else {
            bool opened = true;
            {
                xbase::DbArea a;
                try { a.open(work.string()); }
                catch (const std::exception& e) {
                    check(false, std::string("arm B open() threw: ") + e.what());
                    opened = false;
                }
                if (opened) {
                check(a.gotoRec(1), "arm B: gotoRec(1)");
                check(a.get(2) == "ABC", "arm B: VNAME starts as [ABC]");

                std::string err;
                check(a.replaceFieldNull(2, true, &err),
                      "arm B: replaceFieldNull(VNAME) succeeded -- " +
                      (err.empty() ? std::string("no error") : err));

                check(a.fieldIsNullFromBuffer(2), "arm B: buffer says VNAME is null");
                check(!a.fieldIsNullFromBuffer(1), "arm B: ID is NOT null -- untouched");
                check(a.get(2).empty(),
                      "arm B: a null cell has no value; get() returned [" + a.get(2) + "]");
                }
            }

            const std::vector<char> after = slurp(work);
            if (opened && after.size() >= 612) {
                const auto u8 = [&](std::size_t i) { return static_cast<unsigned char>(after[i]); };
                const unsigned got = u8(rec_off(1) + kOffBits);

                // THE LOAD-BEARING COMPARISON. 0x06 = varlength SET (an empty
                // Varchar is not full) plus null SET. Both, which is the rule
                // measured off this fixture and the one a null-bit-only
                // implementation would get wrong.
                check(got == vfp_row5_bits,
                      "arm B: our bitmap after nulling VNAME is " + hexbyte(got) +
                      "; VFP wrote " + hexbyte(vfp_row5_bits) + " for a row in that state");

                // TEN BYTES, COMPARED TO VFP'S TEN BYTES. Spaces then a trailing
                // length byte of 0x00. A writer that left the old value behind, or
                // left the length byte at 0x20 from the space fill, fails here and
                // nowhere else.
                const std::string our_vname(after.data() + rec_off(1) + kOffVname, 10);
                check(our_vname == vfp_row5_vname,
                      "arm B: our null VNAME bytes differ from VFP's null VNAME bytes");
                check(static_cast<unsigned char>(our_vname[9]) == 0x00,
                      "arm B: trailing length byte is 0x00, got " +
                      hexbyte(static_cast<unsigned char>(our_vname[9])));

                const std::string vfull_after(after.data() + rec_off(1) + kOffVfull, 10);
                check(vfull_after == "0123456789", "arm B: VFULL untouched");
            }
            drop(work);
        }
    }

    // ===================================================================
    // ARM C -- REFUSALS. A false return AND an unchanged file.
    // ===================================================================
    {
        const fs::path work = tmp / "x64base_setnull_refuse.DBF";
        std::string cperr;
        if (!stage_writable_copy(src, work, cperr)) {
            check(false, "arm C: could not stage the fixture -- " + cperr);
        } else {
            const std::vector<char> before = slurp(work);
            bool opened = true;
            {
                xbase::DbArea a;
                try { a.open(work.string()); }
                catch (const std::exception& e) {
                    check(false, std::string("arm C open() threw: ") + e.what());
                    opened = false;
                }
                if (opened) {
                check(a.gotoRec(1), "arm C: gotoRec(1)");

                // VFULL and PLAIN carry descriptor byte 18 = 0x00: not nullable.
                check(!a.setFieldNull(3), "arm C: VFULL is not nullable -- refused");
                check(!a.setFieldNull(4), "arm C: PLAIN is not nullable -- refused");
                check(!a.replaceFieldNull(3), "arm C: replaceFieldNull(VFULL) refused");
                check(!a.setFieldNull(0), "arm C: index 0 refused");
                check(!a.setFieldNull(5), "arm C: the partitioned column refused");
                check(!a.setFieldNull(-1), "arm C: negative index refused");
                check(!a.setFieldNull(999), "arm C: far out-of-range refused");

                // Clearing null is the other direction and must work on a
                // nullable field. Row 2 has ID null; un-null it and re-read.
                check(a.gotoRec(2), "arm C: gotoRec(2)");
                check(a.fieldIsNullFromBuffer(1), "arm C: row 2 ID starts null");
                std::string err;
                check(a.replaceFieldNull(1, false, &err),
                      "arm C: replaceFieldNull(ID, false) succeeded");
                check(!a.fieldIsNullFromBuffer(1), "arm C: row 2 ID is no longer null");
                }
            }
            const std::vector<char> after = slurp(work);
            if (opened && before.size() == after.size() && after.size() >= 612) {
                // Row 1 must be byte-identical: every call against it was refused.
                const bool row1_same =
                    std::equal(before.begin() + static_cast<std::ptrdiff_t>(rec_off(1)),
                               before.begin() + static_cast<std::ptrdiff_t>(rec_off(1) + kRecLen),
                               after.begin() + static_cast<std::ptrdiff_t>(rec_off(1)));
                check(row1_same,
                      "arm C: a refused setFieldNull changed nothing on disk");
            }
            drop(work);
        }
    }

    // ===================================================================
    // ARM E -- CLEARING A NULL BY WRITING A VALUE, GRADED THE SAME WAY.
    //
    // WHY THIS ARM EXISTS. Arms A and B prove we can SET a null and that the
    // bytes are VFP's. Arm C proves the ENGINE can clear one -- by calling
    // replaceFieldNull(f, false) directly, which until 2026-09-05 was the only
    // caller of that spelling anywhere in the tree. NOTHING proved that WRITING
    // A VALUE clears the null, and it did not: DbArea::set() never touched
    // _fd_null, storeFieldsToBuffer() recomputes the bitmap FROM _fd_null, and
    // so a value written over a null cell put the value on disk and re-committed
    // the stale null bit beside it. Found by vfp_null_assertions.dts, not here.
    //
    // A FEATURE PROVEN IN ONE DIRECTION IS NOT PROVEN. Every instrument this lane
    // built pointed the same way -- set a null, read it back, compare to VFP --
    // including the VFP acceptance scripts, which asked whether the cells we
    // nulled are null and never whether a cell we un-nulled is not null.
    //
    // AND IT IS GRADED WITHOUT A HAND-COMPUTED NUMBER, by the same trick the rest
    // of this file uses. Write "ABC" into row 5's null VNAME and the row must
    // become, byte for byte, what VFP wrote on ROW 1:
    //
    //   row 5 before   20 20 20 20 20 20 20 20 20 00   bitmap 0x06  (VNAME null)
    //   row 1 (VFP)    41 42 43 20 20 20 20 20 20 03   bitmap 0x02  (VNAME "ABC")
    //
    // The expected bitmap and the expected ten value bytes are both READ OUT OF
    // THE FIXTURE at run time rather than written here. On the defective code the
    // bitmap comes out 0x06 and this arm is the thing that reds.
    // ===================================================================
    {
        const fs::path work = tmp / "x64base_setnull_clear.DBF";
        std::string cperr;
        if (!stage_writable_copy(src, work, cperr)) {
            check(false, "arm E: could not stage the fixture -- " + cperr);
        } else {
            const std::vector<char> before = slurp(work);

            // The expectations, lifted from rows VFP authored.
            const unsigned char vfp_row1_bits =
                static_cast<unsigned char>(before[rec_off(1) + kOffBits]);
            const std::string vfp_row1_vname(before.data() + rec_off(1) + kOffVname, 10);
            const unsigned char vfp_row5_bits =
                static_cast<unsigned char>(before[rec_off(5) + kOffBits]);

            check(vfp_row5_bits == 0x06,
                  "arm E: fixture row 5 starts at VFP's 0x06, got " +
                  hexbyte(vfp_row5_bits));
            check(vfp_row1_bits == 0x02,
                  "arm E: fixture row 1 carries VFP's 0x02, got " +
                  hexbyte(vfp_row1_bits));

            bool opened = true;
            {
                xbase::DbArea a;
                try { a.open(work.string()); }
                catch (const std::exception& e) {
                    check(false, std::string("arm E open() threw: ") + e.what());
                    opened = false;
                }
                if (opened) {
                    check(a.gotoRec(5), "arm E: gotoRec(5)");
                    check(a.fieldIsNullFromBuffer(2),
                          "arm E: row 5 VNAME starts null -- the guard, without which"
                          " this arm proves nothing");

                    std::string err;
                    check(a.replaceFieldStored(2, "ABC", &err),
                          "arm E: replaceFieldStored(VNAME, \"ABC\") succeeded -- " + err);

                    // The staged view must agree immediately. If this passes and
                    // the byte check below fails, the clear happened in memory and
                    // did not reach storeFieldsToBuffer.
                    check(!a.fieldIsNull(2),
                          "arm E: the staged row no longer calls VNAME null");
                    check(!a.fieldIsNullFromBuffer(2),
                          "arm E: the record buffer no longer calls VNAME null");
                }
            }

            const std::vector<char> after = slurp(work);
            if (opened && before.size() == after.size() && after.size() >= 612) {
                const unsigned char our_bits =
                    static_cast<unsigned char>(after[rec_off(5) + kOffBits]);
                check(our_bits == vfp_row1_bits,
                      "arm E: after clearing, our bitmap is the byte VFP wrote for a"
                      " row with a short non-null VNAME -- expected " +
                      hexbyte(vfp_row1_bits) + ", got " + hexbyte(our_bits));

                const std::string our_vname(after.data() + rec_off(5) + kOffVname, 10);
                check(our_vname == vfp_row1_vname,
                      "arm E: our ten VNAME bytes are VFP's ten VNAME bytes for"
                      " \"ABC\" -- value, padding and trailing length byte");

                // The neighbour field in the same row: ID was not null on row 5
                // and was not written. A clear that widened past its own bit
                // shows up here.
                const bool id_same =
                    std::equal(before.begin() + static_cast<std::ptrdiff_t>(rec_off(5) + kOffId),
                               before.begin() + static_cast<std::ptrdiff_t>(rec_off(5) + kOffId + 4),
                               after.begin()  + static_cast<std::ptrdiff_t>(rec_off(5) + kOffId));
                check(id_same, "arm E: row 5 ID bytes untouched");

                // The neighbour row. Row 4 has ID null (0x03) and must stay that
                // way -- a clear that reached the wrong record is the shape this
                // lane already paid for once (6a10c9353).
                const bool row4_same =
                    std::equal(before.begin() + static_cast<std::ptrdiff_t>(rec_off(4)),
                               before.begin() + static_cast<std::ptrdiff_t>(rec_off(4) + kRecLen),
                               after.begin()  + static_cast<std::ptrdiff_t>(rec_off(4)));
                check(row4_same, "arm E: row 4 is byte-identical -- its ID is still null");
            }

            // AND IT SURVIVES A REOPEN. Everything above reads a buffer this
            // process filled. This asks the file.
            {
                xbase::DbArea a;
                try {
                    a.open(work.string());
                    check(a.gotoRec(5), "arm E: reopen gotoRec(5)");
                    check(!a.fieldIsNullFromBuffer(2),
                          "arm E: reopened, row 5 VNAME is not null");
                    check(a.get(2) == "ABC",
                          "arm E: reopened, row 5 VNAME reads ABC, got '" + a.get(2) + "'");
                } catch (const std::exception& e) {
                    check(false, std::string("arm E reopen threw: ") + e.what());
                }
            }
            drop(work);
        }
    }

    // ===================================================================
    // ARM D -- CONTROL. A table with no bitmap refuses everything and does
    // not crash. Without this, an implementation that dereferenced an empty
    // layout would only be caught the first time a plain table met it.
    // ===================================================================
    {
        const fs::path ctl_src = fs::path(VFP_FIXTURE_ROOT) / "fixtures" / "ACCOUNTS.DBF";
        if (!fs::exists(ctl_src)) {
            check(false, "control fixture ACCOUNTS.DBF is missing");
        } else {
            const fs::path ctl = tmp / "x64base_setnull_control.DBF";
            std::string ctlerr;
            if (!stage_writable_copy(ctl_src, ctl, ctlerr)) {
                check(false, "arm D: could not stage the control -- " + ctlerr);
            } else {
                xbase::DbArea a;
                try {
                    a.open(ctl.string());
                    check(!a.nullFlagsColumn().present,
                          "arm D: control has no _NullFlags column");
                    if (a.recCount64() > 0 && a.gotoRec(1)) {
                        bool any_accepted = false;
                        for (int f = 1; f <= static_cast<int>(a.fields().size()); ++f) {
                            if (a.setFieldNull(f))       any_accepted = true;
                            if (a.replaceFieldNull(f))   any_accepted = true;
                            if (a.fieldIsNull(f))        any_accepted = true;
                        }
                        check(!any_accepted,
                              "arm D: every field on a bitmap-less table refuses,"
                              " and asking did not crash");
                    }
                } catch (const std::exception& e) {
                    check(false, std::string("arm D open() threw: ") + e.what());
                }
                drop(ctl);
            }
        }
    }

    if (g_failures) {
        std::printf("\nFAIL -- %d expectation(s) missed.\n", g_failures);
        return 1;
    }
    std::printf("\nPASS -- our null bytes are the bytes Visual FoxPro wrote for the\n"
                "        same row states, refusals change nothing, and a table with\n"
                "        no bitmap refuses everything.\n");
    return 0;
}
