// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// status: experimental
//
// AIF-091 M1 -- DOES A WRITE DESTROY THE ROW'S NULL BITMAP?
//
// This test was written to FAIL, and the defect it names is one THIS LANE
// INTRODUCED. Read that part first.
//
// ---------------------------------------------------------------------------
// THE DEFECT
// ---------------------------------------------------------------------------
//
// DbArea::storeFieldsToBuffer() begins:
//
//     std::fill(_recbuf.begin(), _recbuf.end(), ' ');
//     _recbuf[0] = _del;
//
// -- the ENTIRE record becomes 0x20 -- and then re-encodes one field per entry
// in `_fields`. Since fbd7e5ee5, `_NullFlags` IS NOT IN `_fields`: the partition
// removed it so it would stop surfacing as a junk one-byte binary column. Its
// bytes are still in the record. Nothing writes them back.
//
// So any writeCurrent() on a nullable VFP table leaves the bitmap as 0x20.
// For this fixture's four-bit layout that reads as bits 0-3 ALL CLEAR:
//
//     every NULL becomes NOT NULL, and every short Varchar claims to be FULL --
//     which also makes its trailing length byte read back as data.
//
// The row still has the right length, the right field values, and the right
// deleted flag. Only the nulls are gone. THAT SHAPE HAS BITTEN THIS PROJECT
// BEFORE: the AIF-110 spec in cmd_regression.cpp records a rewrite that blanked
// every value to 0x20 while "record count, schema, field descriptors, and deleted
// flags all read CORRECT", and draws the doctrine this test follows -- A TEST
// THAT ASSERTS SHAPE PASSES GREEN ON A BLANKED TABLE, so assert the values.
//
// ---------------------------------------------------------------------------
// IT WAS ALREADY BROKEN, AND THIS LANE MADE IT WORSE. BOTH HALVES ARE TRUE.
// ---------------------------------------------------------------------------
//
// Before the partition, `_NullFlags` was a visible field, so `_fd` held its byte
// as decoded TEXT and storeFieldsToBuffer re-encoded it through the fixed-width
// text codec -- which rtrims. A bitmap byte of 0x20 would have decoded to the
// empty string and written back as a space; other values would have survived by
// luck. That is an unreliable round trip.
//
// After the partition it is not unreliable. It is deterministic destruction.
// Turning a coin flip into a certainty is a regression even when the coin was
// already bad, and no test in this tree could see either version -- because
// every write test in this project runs against tables THIS ENGINE created, and
// this engine cannot yet create a nullable table.
//
// ---------------------------------------------------------------------------
// WHAT THIS TEST DOES
// ---------------------------------------------------------------------------
//
// It performs the most harmless write available: it re-sets PLAIN on row 4 to
// the value PLAIN already holds, and calls writeCurrent(). No user-visible cell
// changes. Then it closes, reopens, and asks whether row 4's ID is still null.
//
// If a no-op write can silently discard a null, every write can.
//
// It then checks the SECOND site: appendBlank() writes its own all-spaces record
// directly to disk and never goes through storeFieldsToBuffer(), so it shipped
// 0x20 in the bitmap as well. That is not data loss -- the row is new -- but 0x20
// sets bit 5, which belongs to no field in this table's four-bit map.
//
// The bitmap byte is ALSO read raw from the reopened file, because asking the
// decoder whether the decoder's input survived is not independent evidence.

#include "xbase.hpp"

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

// See test_vfp_null_rowdecode.cpp: fixtures can carry the read-only attribute,
// copy_file propagates it, and remove() on a read-only file is access-denied.
bool stage_writable_copy(const std::filesystem::path& src,
                         const std::filesystem::path& dst,
                         std::string& err)
{
    namespace fs = std::filesystem;
    std::error_code ec;
    fs::permissions(dst, fs::perms::owner_write, fs::perm_options::add, ec); ec.clear();
    fs::remove(dst, ec);                                                     ec.clear();
    fs::copy_file(src, dst, fs::copy_options::overwrite_existing, ec);
    if (ec) { err = "copy_file: " + ec.message(); return false; }
    fs::permissions(dst, fs::perms::owner_write, fs::perm_options::add, ec);
    if (ec) { err = "chmod: " + ec.message(); return false; }
    return true;
}

// Read one record's _NullFlags byte straight out of the file. Independent of the
// decoder on purpose.
bool raw_bitmap_byte(const std::filesystem::path& p, int recno1, std::uint8_t& out)
{
    std::ifstream f(p, std::ios::binary);
    if (!f) return false;
    std::vector<std::uint8_t> b((std::istreambuf_iterator<char>(f)),
                                 std::istreambuf_iterator<char>());
    if (b.size() < 64) return false;
    const std::size_t hdr = (std::size_t)b[8]  | ((std::size_t)b[9]  << 8);
    const std::size_t rec = (std::size_t)b[10] | ((std::size_t)b[11] << 8);
    if (rec == 0) return false;
    const std::size_t at = hdr + (std::size_t)(recno1 - 1) * rec + (rec - 1);
    if (at >= b.size()) return false;
    out = b[at];
    return true;
}

} // namespace

int main()
{
    namespace fs = std::filesystem;
    std::error_code ec;

    const fs::path src = fs::path(VFP_FIXTURE_ROOT) / "fixtures" / "nullfix.DBF";
    const fs::path work = fs::temp_directory_path(ec) / "x64base_nullfix_writeguard.DBF";

    std::printf("AIF-091 M1 -- does writeCurrent() preserve the _NullFlags bitmap?\n");
    if (!fs::exists(src)) {
        std::printf("  FAIL: fixture missing -- a failure, not a skip.\n");
        return 1;
    }
    std::string err;
    if (!stage_writable_copy(src, work, err)) {
        std::printf("  FAIL: could not stage a writable copy -- %s\n", err.c_str());
        return 1;
    }
    std::printf("  working copy: %s\n\n", work.string().c_str());

    // ---- before ----------------------------------------------------------
    std::uint8_t before = 0;
    check(raw_bitmap_byte(work, 4, before), "read row 4's bitmap byte before the write");
    std::printf("  row 4 bitmap BEFORE the write: 0x%02X (expect 0x03)\n", before);
    check(before == 0x03, "row 4 starts at 0x03 -- first field null, second field short");

    // ---- the most harmless write available -------------------------------
    try {
        xbase::DbArea area;
        area.open(work.string());
        check(area.gotoRec(4), "gotoRec(4)");
        check(area.fieldIsNullFromBuffer(1), "row 4 ID reads NULL before the write");

        const std::string plain_before = area.get(4);
        std::printf("  PLAIN before: '%s'\n", plain_before.c_str());

        // Set it to what it already is. Nothing a user could see changes.
        check(area.set(4, plain_before), "set PLAIN to the value it already holds");
        check(area.writeCurrent(), "writeCurrent()");
    } catch (const std::exception& e) {
        check(false, std::string("open/write threw: ") + e.what());
        fs::remove(work, ec);
        return 1;
    }

    // ---- after -----------------------------------------------------------
    std::uint8_t after = 0;
    check(raw_bitmap_byte(work, 4, after), "read row 4's bitmap byte after the write");
    std::printf("  row 4 bitmap AFTER  the write: 0x%02X\n", after);

    check(after != 0x20,
          "THE DEFECT: the bitmap byte is 0x20 -- storeFieldsToBuffer() space-filled"
          " the whole record and never wrote the partitioned _NullFlags column back");
    check(after == before,
          "a no-op write must leave the bitmap byte EXACTLY as it was"
          " (before 0x" + std::to_string(before) + ")");

    // And through the decoder, which is what a consumer would notice.
    try {
        xbase::DbArea area;
        area.open(work.string());
        check(area.gotoRec(4), "reopen and gotoRec(4)");
        check(area.fieldIsNullFromBuffer(1),
              "row 4 ID is STILL NULL after a no-op write -- if this reds, a write"
              " silently converted a null into a value");
        check(!area.fieldIsNullFromBuffer(2), "row 4 VNAME is still not null");

        // The other rows must be untouched: only record 4 was written.
        check(area.gotoRec(2), "gotoRec(2)");
        check(area.fieldIsNullFromBuffer(1) && area.fieldIsNullFromBuffer(2),
              "row 2's two nulls are untouched by a write to row 4");
        check(area.gotoRec(5), "gotoRec(5)");
        check(area.fieldIsNullFromBuffer(2) && !area.fieldIsNullFromBuffer(1),
              "row 5's single null is untouched");
    } catch (const std::exception& e) {
        check(false, std::string("reopen threw: ") + e.what());
    }

    // ---- APPEND BLANK is a SECOND site, and it does not go through -------
    //      storeFieldsToBuffer() at all: appendBlank() writes its own all-spaces
    //      record straight to disk, so the bitmap shipped as 0x20 there too. That
    //      one is not data LOSS -- the row is new -- but 0x20 sets bit 5, which
    //      belongs to no field in this table's four-bit map. Zero asserts nothing.
    //
    //      What Visual FoxPro's own APPEND BLANK writes here is NOT MEASURED. This
    //      asserts our choice, not VFP's behaviour, and says so.
    {
        std::uint8_t r2_before = 0, r4_before = 0;
        check(raw_bitmap_byte(work, 2, r2_before), "row 2 bitmap before the append");
        check(raw_bitmap_byte(work, 4, r4_before), "row 4 bitmap before the append");

        try {
            xbase::DbArea area;
            area.open(work.string());
            const std::uint64_t before_count = area.recCount64();
            check(area.appendBlank(), "appendBlank()");
            check(area.recCount64() == before_count + 1, "record count went up by one");
        } catch (const std::exception& e) {
            check(false, std::string("appendBlank threw: ") + e.what());
        }

        std::uint8_t appended = 0xFF;
        if (raw_bitmap_byte(work, 6, appended)) {
            std::printf("  appended row 6 bitmap: 0x%02X\n", appended);
            check(appended != 0x20,
                  "an appended row's bitmap is not 0x20 -- bit 5 belongs to no field here");
            check(appended == 0x00,
                  "an appended row's bitmap is zero: nothing null, and an all-spaces"
                  " Varchar is full (OUR choice; VFP's APPEND BLANK is unmeasured)");
        } else {
            check(false, "could not read the appended row's bitmap");
        }

        // The append must not have disturbed anything already on disk.
        std::uint8_t r2_after = 0, r4_after = 0;
        check(raw_bitmap_byte(work, 2, r2_after), "row 2 bitmap after the append");
        check(raw_bitmap_byte(work, 4, r4_after), "row 4 bitmap after the append");
        check(r2_after == r2_before, "the append left row 2's bitmap alone");
        check(r4_after == r4_before, "the append left row 4's bitmap alone");
    }

    fs::permissions(work, fs::perms::owner_write, fs::perm_options::add, ec); ec.clear();
    fs::remove(work, ec);

    if (g_failures) {
        std::printf("\nFAIL -- %d expectation(s) missed.\n", g_failures);
        return 1;
    }
    std::printf("\nPASS -- a write preserves the row's null bitmap.\n");
    return 0;
}
