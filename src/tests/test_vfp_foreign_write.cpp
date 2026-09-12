// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// status: experimental
//
// AIF-091 M2 -- THE THIRD DIRECTION: VISUAL FOXPRO WROTE INTO A TABLE WE MADE.
//
// Every other test in this lane runs in one of two directions, and BOTH of them
// can be satisfied by a self-consistent mistake:
//
//   we write -> we read      dottalkpp_vfp_varchar_roundtrip_test, and every
//                            create-then-read test in this repository. It proves
//                            our encoder and our decoder agree. dbf_create.cpp and
//                            the reader shared a WRONG field-flags offset for years
//                            while exactly that test stayed green.
//
//   VFP writes -> we read    dottalkpp_vfp_nullfix_r1a_test and
//                            dottalkpp_vfp_null_rowdecode_test, against
//                            nullfix.DBF. Real evidence -- but of a table VISUAL
//                            FOXPRO designed. It says nothing about a schema WE
//                            laid out.
//
// This one is the direction neither covers: OUR CREATE built the table, and then
// VISUAL FOXPRO 9 APPENDED A ROW INTO IT. If our `_NullFlags` column were at the
// wrong displacement, or the wrong width, or carried the wrong descriptor flags,
// or if `assign_null_bits()` handed out bit positions in an order VFP does not
// use, VFP would have written that row somewhere we do not look -- and no test in
// either of the two directions above could tell.
//
// ---------------------------------------------------------------------------
// PROVENANCE OF THE FIXTURE -- READ THIS BEFORE REGENERATING IT
// ---------------------------------------------------------------------------
//
// tools/vfp/fixtures/nullwrote.DBF, 550 bytes,
// sha256 bfe72f6806f23fe0fee477b61edc8ebf4a29ada40853eefc44526f7cfde69e16
//
//   1. Our CREATE wrote the file, on 2026-09-05, from the DotTalk++ shell:
//        CREATE VFP nullnew (id N(4) NULL, vname V(10) NULL,
//                            vfull V(10), plain C(5))
//   2. Our engine appended records 1 and 2 (APPEND + REPLACE).
//   3. VISUAL FOXPRO 9 opened it and appended record 3, via
//      tools/vfp/read_created.prg section S4:
//        APPEND BLANK
//        REPLACE id    WITH .NULL.
//        REPLACE vname WITH "VFPW"
//        REPLACE vfull WITH "0123456789"
//        REPLACE plain WITH "VF"
//      VFP raised no errors and its own LIST printed record 3 as
//        3   .NULL.   VFPW   0123456789   VF
//   4. The result was copied to this name. `nullnew.dbf` remains the
//      REGENERABLE scratch path that read_created.prg opens; THIS file is the
//      EVIDENCE and is report-only, like every other fixture here.
//
// RECORDS 1 AND 2 ARE OURS AND THEREFORE PROVE NOTHING BY THEMSELVES. They are
// asserted below only as context -- a decoder that read every row correctly for
// the wrong reason would still pass on them. RECORD 3 IS THE ONLY LOAD-BEARING
// ROW IN THIS FILE, and the header comment on each arm says which kind it is.
//
// ---------------------------------------------------------------------------
// THE TRUTH TABLE COMES FROM read_created.prg, NOT FROM THE BITMAP
// ---------------------------------------------------------------------------
//
// The expectations for record 3 are transcribed from the five REPLACE lines
// above and from what VFP printed. They are NOT derived from the `_NullFlags`
// byte, because deriving them from the byte would make this test agree with the
// decoder by construction -- the closed loop this whole file exists to break.
//
// The raw-byte arm at the end reads the file with an ifstream and never touches
// DbArea, so the FORMAT is graded independently of anything our loader believes.

#include "xbase.hpp"

#include <cstdint>
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

// Print a byte the way a byte should be printed. MEASURED THE HARD WAY on
// 2026-09-05: a diagnostic in this lane built its text as
// "0x" + std::to_string(value) and reported a byte of 0x20 as "0x32", which is a
// plausible-looking version byte. A test whose failure message lies is worse than
// no message.
std::string hexbyte(unsigned v)
{
    char b[8];
    std::snprintf(b, sizeof(b), "0x%02X", v & 0xFFu);
    return std::string(b);
}

// See test_vfp_null_rowdecode.cpp for why this exists in full. Short version:
// DbArea::open() wants ios::in|ios::out, fixtures are report-only, copy_file
// PROPAGATES the read-only attribute, and remove() on a read-only file is also
// access-denied on Windows -- so clear, remove, copy, then make writable.
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

} // namespace

int main()
{
    namespace fs = std::filesystem;

    const fs::path src = fs::path(VFP_FIXTURE_ROOT) / "fixtures" / "nullwrote.DBF";
    std::printf("AIF-091 M2 -- Visual FoxPro wrote a row into a table OUR CREATE made\n");
    std::printf("  fixture: %s\n", src.string().c_str());

    if (!fs::exists(src)) {
        std::printf("  FAIL: fixture missing -- this is a failure, not a skip.\n"
                    "        See the provenance note in this file's header; it is\n"
                    "        NOT regenerated by rerunning read_created.prg alone.\n");
        return 1;
    }

    std::error_code ec;
    const fs::path work =
        fs::temp_directory_path(ec) / "x64base_nullwrote_foreign.DBF";
    if (ec) { std::printf("  FAIL: no temp directory: %s\n", ec.message().c_str()); return 1; }

    std::string cperr;
    if (!stage_writable_copy(src, work, cperr)) {
        std::printf("  FAIL: could not stage the fixture at %s -- %s\n",
                    work.string().c_str(), cperr.c_str());
        return 1;
    }
    std::printf("  working copy: %s\n\n", work.string().c_str());

    // =====================================================================
    // ARM 1 -- THE RAW FORMAT, WITHOUT THE LOADER
    // =====================================================================
    //
    // Read the bytes with an ifstream and grade them by hand. Nothing here goes
    // through DbArea, so this arm stays true even if the loader is wrong -- which
    // is the point: it is what tells a FORMAT failure apart from a DECODE failure
    // when the arm below goes red at the same time.
    {
        std::ifstream f(src.string(), std::ios::binary);
        check(static_cast<bool>(f), "raw -- fixture opens for reading");

        std::vector<char> all((std::istreambuf_iterator<char>(f)),
                               std::istreambuf_iterator<char>());
        check(all.size() == 550, "raw -- file is 550 bytes, got " +
                                 std::to_string(all.size()));
        if (all.size() < 550) { fs::remove(work, ec); return 1; }

        const auto u8 = [&all](std::size_t i) -> unsigned {
            return static_cast<unsigned char>(all[i]);
        };

        // The header VFP left behind. VFP REWROTE THE RECORD COUNT AND THE DATE
        // AND CHANGED NOTHING ELSE -- it accepted our header rather than
        // rebuilding it, which is itself the finding.
        check(u8(0) == 0x32, "raw -- version byte still " + hexbyte(0x32) +
                             " after VFP wrote to the file, got " + hexbyte(u8(0)));
        const unsigned recs = u8(4) | (u8(5) << 8) | (u8(6) << 16) | (u8(7) << 24);
        check(recs == 3, "raw -- record count is 3, got " + std::to_string(recs));
        const unsigned hdr = u8(8) | (u8(9) << 8);
        check(hdr == 456, "raw -- header length still 456 (32 + 32*5 + 1 + 263),"
                          " got " + std::to_string(hdr));
        const unsigned rl = u8(10) | (u8(11) << 8);
        check(rl == 31, "raw -- record length still 31, got " + std::to_string(rl));

        // Record 3: the one Visual FoxPro wrote.
        //   [0]      deleted flag
        //   [1..4]   id     N(4)
        //   [5..14]  vname  V(10), value bytes then a trailing length byte
        //   [15..24] vfull  V(10)
        //   [25..29] plain  C(5)
        //   [30]     _NullFlags
        const std::size_t r3 = 456 + 2 * 31;

        check(u8(r3 + 0) == 0x20, "raw -- record 3 is not deleted");

        // WHAT VFP DOES WITH A NULL NUMERIC: it leaves the value area as spaces.
        // The bitmap carries the nullness; the bytes carry nothing.
        bool id_spaces = true;
        for (std::size_t i = 1; i <= 4; ++i) if (u8(r3 + i) != 0x20) id_spaces = false;
        check(id_spaces, "raw -- VFP left the null ID field as spaces");

        check(all[r3 + 5] == 'V' && all[r3 + 6] == 'F' &&
              all[r3 + 7] == 'P' && all[r3 + 8] == 'W',
              "raw -- VNAME value bytes are VFPW");
        check(u8(r3 + 14) == 0x04,
              "raw -- VNAME trailing length byte is " + hexbyte(0x04) +
              " (4 characters), got " + hexbyte(u8(r3 + 14)));

        bool vfull_ok = true;
        for (std::size_t i = 0; i < 10; ++i)
            if (all[r3 + 15 + i] != static_cast<char>('0' + i)) vfull_ok = false;
        check(vfull_ok, "raw -- VFULL holds all ten characters and no length byte");

        // THE LOAD-BEARING BYTE OF THIS ENTIRE TEST.
        //
        // Predicted from include/xbase/vfp_null_bits.hpp BEFORE the file was read:
        //   bit 0  ID null            SET   -- VFP wrote .NULL.
        //   bit 1  VNAME varlength    SET   -- "VFPW" is 4 of 10, so not full
        //   bit 2  VNAME null         clear -- VFP wrote a value
        //   bit 3  VFULL varlength    clear -- 10 of 10, so full
        // => 0x03
        //
        // Visual FoxPro had no access to that header. It was given a file, and it
        // chose these bits from the descriptors OUR CREATE wrote.
        check(u8(r3 + 30) == 0x03,
              "raw -- record 3 _NullFlags is " + hexbyte(0x03) +
              " (bit0 ID null, bit1 VNAME varlength), got " + hexbyte(u8(r3 + 30)));
    }

    // =====================================================================
    // ARM 2 -- THE SAME ROW THROUGH OUR DECODER
    // =====================================================================
    {
        xbase::DbArea area;
        try {
            area.open(work.string());
        } catch (const std::exception& e) {
            std::printf("  FAIL: open() threw: %s\n", e.what());
            fs::remove(work, ec);
            return 1;
        }

        check(area.versionByte() == 0x32, "open -- version byte 0x32");
        check(area.fields().size() == 4,
              "open -- four user fields; _NullFlags partitioned out");
        check(area.nullFlagsColumn().present, "open -- _NullFlags column present");
        check(area.recCount64() == 3, "open -- three records");
        if (area.fields().size() != 4) { fs::remove(work, ec); return 1; }

        // Nullability is a property of the TABLE OUR CREATE WROTE, read back after
        // VFP has had the file. If VFP had rebuilt the descriptors these would move.
        check(area.fieldIsNullable(1),  "open -- id is nullable");
        check(area.fieldIsNullable(2),  "open -- vname is nullable");
        check(!area.fieldIsNullable(3), "open -- vfull is NOT nullable");
        check(!area.fieldIsNullable(4), "open -- plain is NOT nullable");

        // ---- RECORD 3: THE LOAD-BEARING ROW ------------------------------
        check(area.gotoRec(3), "gotoRec(3) -- the row VFP wrote");

        check(area.fieldIsNullFromBuffer(1),
              "rec3 id -- VFP wrote .NULL. and our decoder must see NULL");
        check(!area.fieldIsNullFromBuffer(2), "rec3 vname -- not null");
        check(!area.fieldIsNullFromBuffer(3), "rec3 vfull -- not null");
        check(!area.fieldIsNullFromBuffer(4), "rec3 plain -- not null");

        // The Varchar VALUE, un-rtrimmed and with no stray length byte. A decoder
        // that ignored the trailing length byte would return "VFPW" plus five
        // spaces plus a 0x04, which is not a string anyone wants.
        const std::string vname3 = area.get(2);
        check(vname3 == "VFPW",
              "rec3 vname -- expected [VFPW], decoder returned [" + vname3 + "]"
              " (length " + std::to_string(vname3.size()) + ")");

        const std::string vfull3 = area.get(3);
        check(vfull3 == "0123456789",
              "rec3 vfull -- expected the full ten characters, got [" + vfull3 + "]");

        // ---- RECORDS 1 AND 2: OURS, THEREFORE CONTEXT ONLY ---------------
        //
        // These went through our own writer. They cannot fail for a reason record
        // 3 would not also catch, and they are here so a reader of the output can
        // see the whole table rather than one row of it. Do not mistake them for
        // evidence.
        check(area.gotoRec(1), "gotoRec(1) -- our own row, context only");
        check(!area.fieldIsNullFromBuffer(1), "rec1 id -- not null (ours)");
        check(area.get(2) == "AB", "rec1 vname -- [AB] (ours)");

        check(area.gotoRec(2), "gotoRec(2) -- our own row, context only");
        check(area.get(2) == "0123456789",
              "rec2 vname -- full width, no length byte (ours)");

        // A decoder stuck on one answer. Exactly ONE null cell exists in this
        // table and VFP put it there.
        int nulls_seen = 0;
        for (int r = 1; r <= 3; ++r) {
            if (!area.gotoRec(r)) continue;
            for (int f = 1; f <= 4; ++f)
                if (area.fieldIsNullFromBuffer(f)) ++nulls_seen;
        }
        check(nulls_seen == 1,
              "exactly ONE null cell in the table, and Visual FoxPro wrote it --"
              " got " + std::to_string(nulls_seen));
    }

    fs::permissions(work, fs::perms::owner_write, fs::perm_options::add, ec);
    ec.clear();
    fs::remove(work, ec);   // best effort; a stale temp copy is harmless

    if (g_failures) {
        std::printf("\nFAIL -- %d expectation(s) missed.\n", g_failures);
        return 1;
    }
    std::printf("\nPASS -- Visual FoxPro chose the same bits our header says it would,\n"
                "        in a table it did not design, and our decoder read them back.\n");
    return 0;
}
