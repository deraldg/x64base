// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// status: experimental
//
// AIF-091 M1/M2 -- WHAT DOES THIS ENGINE ALREADY DO TO A VARCHAR?
//
// WHY THIS TEST EXISTS BEFORE ANY VARCHAR READ SUPPORT DOES.
//
// The finding from 6a10c9353 was that read-without-create format features are
// invisible to every write test, because every write test runs against tables the
// engine itself created -- and `V` is next in line for exactly that hole. The
// mitigation named there was: WHEN A LANE ADDS READ SUPPORT FOR A FORMAT FEATURE,
// ASK WHAT THE WRITE PATH DOES WITH THAT FEATURE FIRST, even though no test can
// fail yet. This is that question, asked before the answer is convenient.
//
// It is expected to go RED. Every expectation below is a FORMAT CONTRACT, not a
// description of current behaviour, so the reds name defects rather than pinning
// them in place.
//
// ---------------------------------------------------------------------------
// THE FORMAT CONTRACT BEING ASSERTED
// ---------------------------------------------------------------------------
//
// A VFP Varchar field of width W stores, per row:
//   - the varlength bit CLEAR  -> the value fills the field; all W bytes are data
//   - the varlength bit SET    -> the LAST byte holds the value length L (L < W),
//                                bytes 0..L-1 are the value, L..W-2 are padding
//
// Two consequences a caller must be able to rely on:
//   1. Reading a Varchar gives the value, NOT the value plus its length byte.
//   2. Writing a Varchar leaves the length byte and the varlength bit AGREEING
//      with what was written. A file where they disagree is one VFP may reject.
//
// ---------------------------------------------------------------------------
// WHAT I EXPECT TO SEE, WRITTEN DOWN BEFORE THE RUN
// ---------------------------------------------------------------------------
//
// READ:  decodeFieldFromBuffer() dispatches on f.type through a codec that gets
//        only the field's own bytes and its full width. Nothing consults the
//        varlength bit, so a short Varchar should come back INCLUDING its length
//        byte -- row 1's VNAME as 'ABC' + six spaces + CHR(3). The default text
//        codec rtrims TRAILING SPACES, and CHR(3) is not a space, so the rtrim
//        will not hide it.
//
// WRITE: storeFieldsToBuffer() re-encodes from `_fd`, and `_fd` was filled by the
//        same unaware read. So the length byte may ROUND-TRIP BY ACCIDENT for
//        these rows -- the value read back includes the length byte, and writing
//        that same string back reproduces it. If so, a no-op write is byte-clean
//        TODAY and would BREAK THE MOMENT READ TRIMMING LANDS, because `_fd` would
//        then hold 'AB' and the encoder would write 'AB' + eight spaces, losing
//        the length byte while the varlength bit still claims one is there.
//
//        THAT IS THE WHOLE REASON THIS TEST IS WRITTEN FIRST. If it is true, the
//        read fix and the write fix MUST LAND TOGETHER, and landing the read fix
//        alone would introduce a corruption that today does not exist.
//
// SET:   setting VNAME to "XY" should store 'XY' + seven spaces + CHR(2) with the
//        varlength bit SET. I expect it to store 'XY' + eight spaces instead --
//        making the last byte 0x20, which reads back as a claimed length of 32 in
//        a 10-byte field, while the bit still says a length byte is present.
//
// Writes go to a COPY. The fixture is never opened writable.

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

bool stage_writable_copy(const std::filesystem::path& src,
                         const std::filesystem::path& dst, std::string& err)
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

std::vector<std::uint8_t> slurp(const std::filesystem::path& p)
{
    std::ifstream f(p, std::ios::binary);
    return std::vector<std::uint8_t>((std::istreambuf_iterator<char>(f)),
                                      std::istreambuf_iterator<char>());
}

struct Geom { std::size_t hdr, rec; };

Geom geom(const std::vector<std::uint8_t>& b)
{
    Geom g{};
    g.hdr = (std::size_t)b[8]  | ((std::size_t)b[9]  << 8);
    g.rec = (std::size_t)b[10] | ((std::size_t)b[11] << 8);
    return g;
}

// Record layout: [0] delete, [1..4] ID, [5..14] VNAME, [15..24] VFULL,
// [25..29] PLAIN, [30] _NullFlags.
const std::size_t VNAME_OFF = 5, VNAME_LEN = 10;

std::string show(const std::uint8_t* p, std::size_t n)
{
    std::string s;
    char buf[8];
    for (std::size_t i = 0; i < n; ++i) {
        if (p[i] >= 0x20 && p[i] <= 0x7E) { s.push_back((char)p[i]); }
        else { std::snprintf(buf, sizeof buf, "\\x%02X", p[i]); s += buf; }
    }
    return s;
}

} // namespace

int main()
{
    namespace fs = std::filesystem;
    std::error_code ec;

    const fs::path src  = fs::path(VFP_FIXTURE_ROOT) / "fixtures" / "nullfix.DBF";
    const fs::path work = fs::temp_directory_path(ec) / "x64base_nullfix_varchar.DBF";

    std::printf("AIF-091 -- Varchar read/write behaviour, measured before it is changed\n");
    if (!fs::exists(src)) { std::printf("  FAIL: fixture missing -- a failure, not a skip.\n"); return 1; }
    std::string err;
    if (!stage_writable_copy(src, work, err)) {
        std::printf("  FAIL: could not stage a writable copy -- %s\n", err.c_str());
        return 1;
    }

    // ---- 1. WHAT DOES READING A VARCHAR GIVE BACK? ------------------------
    std::printf("\n  -- read --\n");
    try {
        xbase::DbArea area;
        area.open(work.string());

        struct Want { int row; const char* want; const char* why; };
        const Want wanted[] = {
            { 1, "ABC",        "short, length byte 3"      },
            { 2, "",           "null, stored length 0"     },
            { 3, "0123456789", "exactly full, no length byte" },
            { 4, "AB",         "short, length byte 2"      },
            { 5, "",           "null, stored length 0"     }
        };
        for (const Want& w : wanted) {
            check(area.gotoRec(w.row), "gotoRec");
            const std::string got = area.get(2);
            std::printf("    row %d VNAME -> '%s'  (want '%s' -- %s)\n",
                        w.row, show((const std::uint8_t*)got.data(), got.size()).c_str(),
                        w.want, w.why);
            check(got == w.want,
                  "row " + std::to_string(w.row) +
                  " VNAME reads as the VALUE, without its trailing length byte");
        }
    } catch (const std::exception& e) {
        check(false, std::string("read pass threw: ") + e.what());
    }

    // ---- 2. IS A NO-OP WRITE BYTE-CLEAN TODAY? ----------------------------
    //
    // This is the load-bearing question. If it is clean today only because the
    // unaware read and the unaware write cancel out, then landing read trimming
    // ALONE breaks it.
    std::printf("\n  -- no-op write --\n");
    const std::vector<std::uint8_t> before = slurp(work);
    const Geom g = geom(before);
    try {
        xbase::DbArea area;
        area.open(work.string());
        check(area.gotoRec(4), "gotoRec(4)");
        check(area.set(4, area.get(4)), "set PLAIN to the value it already holds");
        check(area.writeCurrent(), "writeCurrent()");
    } catch (const std::exception& e) {
        check(false, std::string("no-op write threw: ") + e.what());
    }
    {
        const std::vector<std::uint8_t> after = slurp(work);
        const std::size_t at = g.hdr + 3 * g.rec;
        std::printf("    row 4 before: %s\n", show(&before[at], g.rec).c_str());
        std::printf("    row 4 after : %s\n", show(&after[at],  g.rec).c_str());
        check(before.size() == after.size(), "a no-op write does not change the file size");
        bool same = before.size() == after.size();
        if (same) for (std::size_t i = 0; i < g.rec; ++i)
            if (before[at + i] != after[at + i]) { same = false; break; }
        check(same, "A NO-OP WRITE IS BYTE-IDENTICAL -- every byte of row 4 survives");
    }

    // ---- 3. WHAT DOES SETTING A VARCHAR ACTUALLY STORE? -------------------
    std::printf("\n  -- set VNAME = \"XY\" on row 4 --\n");
    try {
        xbase::DbArea area;
        area.open(work.string());
        check(area.gotoRec(4), "gotoRec(4)");
        check(area.set(2, "XY"), "set VNAME");
        check(area.writeCurrent(), "writeCurrent()");
    } catch (const std::exception& e) {
        check(false, std::string("varchar write threw: ") + e.what());
    }
    {
        const std::vector<std::uint8_t> b = slurp(work);
        const std::size_t at = g.hdr + 3 * g.rec;
        const std::uint8_t* v = &b[at + VNAME_OFF];
        const std::uint8_t  nf = b[at + g.rec - 1];
        std::printf("    VNAME bytes : %s\n", show(v, VNAME_LEN).c_str());
        std::printf("    _NullFlags  : 0x%02X   (bit1 = VNAME varlength)\n", nf);

        const bool varlen_bit = (nf & 0x02) != 0;
        check(varlen_bit,
              "VNAME is 2 chars in a 10-byte field, so the varlength bit must be SET");
        // Formatted as hex ON PURPOSE, and it was wrong once: this message used to
        // read "0x" + std::to_string(decimal), so a byte of 0x20 was reported as
        // "0x32". A diagnostic that misstates the value it found is the same class
        // of fault as everything else this lane has been chasing -- an instrument
        // that cannot be trusted about what it saw.
        {
            char got[16];
            std::snprintf(got, sizeof got, "0x%02X", (unsigned)v[VNAME_LEN - 1]);
            check(v[VNAME_LEN - 1] == 2,
                  std::string("the stored length byte must be 2 -- it is ") + got +
                  "; a length byte that disagrees with the value is a file VFP may reject");
        }
        check(v[0] == 'X' && v[1] == 'Y', "the value bytes are 'XY'");
    }

    // ---- 4. AND A VALUE THAT EXACTLY FILLS THE FIELD ----------------------
    std::printf("\n  -- set VNAME = \"0123456789\" (exactly full) on row 4 --\n");
    try {
        xbase::DbArea area;
        area.open(work.string());
        check(area.gotoRec(4), "gotoRec(4)");
        check(area.set(2, "0123456789"), "set VNAME to exactly the field width");
        check(area.writeCurrent(), "writeCurrent()");
    } catch (const std::exception& e) {
        check(false, std::string("full varchar write threw: ") + e.what());
    }
    {
        const std::vector<std::uint8_t> b = slurp(work);
        const std::size_t at = g.hdr + 3 * g.rec;
        const std::uint8_t* v = &b[at + VNAME_OFF];
        const std::uint8_t  nf = b[at + g.rec - 1];
        std::printf("    VNAME bytes : %s\n", show(v, VNAME_LEN).c_str());
        std::printf("    _NullFlags  : 0x%02X\n", nf);
        check((nf & 0x02) == 0,
              "a value that FILLS the field must CLEAR the varlength bit -- there is"
              " no room for a length byte");
        check(v[VNAME_LEN - 1] == '9', "the last byte is data, not a length");
    }

    fs::permissions(work, fs::perms::owner_write, fs::perm_options::add, ec); ec.clear();
    fs::remove(work, ec);

    if (g_failures) {
        std::printf("\nFAIL -- %d expectation(s) missed. Each is a format contract.\n", g_failures);
        return 1;
    }
    std::printf("\nPASS -- Varchar reads and writes agree with the format.\n");
    return 0;
}
