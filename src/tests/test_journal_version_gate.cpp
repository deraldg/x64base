// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: multi-area-commit
// status: experimental
//
// AIF-160 / AIF-061 -- THE JOURNAL VERSION GATE, AND ITS CONTROL.
//
// WHAT IS UNDER TEST. recover_table_buffer_journal() used to replay a .tbj log
// without ever reading the "TBJ<n>" header it has always written. It scanned
// for a line beginning 'C', replayed 'I'/'U'/'D', and skipped everything else
// with no default branch. A log from a NEWER build would therefore be half
// replayed: its 'C' honoured, its unknown records dropped in silence. For the
// memo records AIF-061 designed, that means recovered rows referencing memo
// objects the memo store was never told to write -- a table that opens clean
// with the damage one field deep.
//
// The gate refuses a version it does not understand, and PRESERVES the log
// rather than deleting it, because an unreadable log may be a committed
// transaction a newer build can still replay.
//
// WHY G0 EXISTS AND WHY IT IS NOT A FORMALITY. Three of the four arms below
// assert that NOTHING HAPPENED. A fixture that could never have produced a
// replay in the first place satisfies all three while measuring nothing -- the
// house rule from the L3 arm, "never credit G1 without D1", in a new place. G0
// is the detector: the SAME forged log shape, the only difference being the
// version token, and it MUST replay. If G0 fails, T1 and T2 mean nothing and
// this test says so rather than reporting three greens.
//
// WHAT THIS TEST DOES NOT CLAIM.
//   - Nothing about TBJ2. No M record and no P marker exists yet; this build
//     still writes TBJ1 deliberately.
//   - Nothing about a real crash. The logs here are forged by hand, which is
//     the only way to produce a version this build cannot write.
//   - Nothing about a pre-header journal. Every log this family has written
//     carries the header; whether one ever existed without it was not swept.

#include "cli/table_state.hpp"
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"

#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {

int g_failures = 0;

void check(bool condition, const std::string& marker, const std::string& detail) {
    std::cout << marker << ":" << (condition ? ".T." : ".F.") << "\n";
    if (!condition) {
        std::cerr << "FAIL: " << marker << " -- " << detail << "\n";
        ++g_failures;
    }
}

std::string hex_of(const std::string& raw) {
    static const char* const H = "0123456789ABCDEF";
    std::string out;
    for (unsigned char c : raw) {
        out.push_back(H[(c >> 4) & 0xF]);
        out.push_back(H[c & 0xF]);
    }
    return out;
}

bool make_table(const std::filesystem::path& path, std::string& err) {
    xbase::dbf_create::FieldSpec id;
    id.name = "ID";   id.type = 'N'; id.len = 6; id.dec = 0;
    xbase::dbf_create::FieldSpec mark;
    mark.name = "MARK"; mark.type = 'C'; mark.len = 8; mark.dec = 0;
    return xbase::dbf_create::create_dbf(
        path.string(), std::vector<xbase::dbf_create::FieldSpec>{id, mark},
        xbase::dbf_create::Flavor::X64, err);
}

void write_text(const std::filesystem::path& path, const std::string& text) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    out.write(text.data(), static_cast<std::streamsize>(text.size()));
    out.flush();
}

// One row, MARK = "BEFORE".
bool open_area(xbase::DbArea& a, const std::filesystem::path& dbf) {
    try {
        a.open(dbf.string());
    } catch (...) {
        return false;
    }
    return a.isOpen();
}

bool seed_row(const std::filesystem::path& dbf) {
    xbase::DbArea a;
    if (!open_area(a, dbf)) return false;
    if (!a.appendBlank() || !a.readCurrent()) { a.close(); return false; }
    const bool ok = a.set(1, "1") && a.set(2, "BEFORE") && a.writeCurrent();
    a.close();
    return ok;
}

std::string read_mark(const std::filesystem::path& dbf) {
    xbase::DbArea a;
    if (!open_area(a, dbf)) return "<unopened>";
    std::string value = "<unread>";
    if (a.gotoRec64(1) && a.readCurrent()) value = a.get(2);
    a.close();
    return value;
}

// A log whose only variable is its first line. Everything after it is a valid,
// committed TBJ1 body that WOULD replay -- which is what makes the version the
// single thing each arm changes.
std::string forged_log(const std::string& header_line) {
    return header_line + "\n"
         + "U 1 1 S 2:" + hex_of("AFTER   ") + "\n"
         + "C 1\n";
}

// Returns true iff recovery replayed. `present_after` reports whether the log
// survived, which is the half that separates refuse-and-preserve from discard.
bool recover(const std::filesystem::path& dbf, bool& present_after) {
    xbase::DbArea a;
    const bool replayed =
        open_area(a, dbf) && dottalk::table::recover_table_buffer_journal(a);
    if (a.isOpen()) a.close();
    present_after = std::filesystem::exists(dbf.string() + ".tbj");
    return replayed;
}

} // namespace

int main() {
    namespace fs = std::filesystem;
    std::error_code ec;
    const fs::path root = fs::temp_directory_path(ec) / "dottalkpp_tbjver";
    fs::remove_all(root, ec);
    fs::create_directories(root, ec);

    // ---- G0: the detector. A TBJ1 log of this exact shape MUST replay. ------
    {
        const fs::path dbf = root / "G0.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: G0 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj", forged_log("TBJ1 G0"));

        bool present = true;
        const bool replayed = recover(dbf, present);
        check(replayed,                       "JVG_G0_a_current_version_log_replays",
              "a TBJ1 log with a C marker did not replay -- every arm below is blind");
        check(read_mark(dbf) == "AFTER",      "JVG_G0_the_replay_reached_the_row",
              "MARK is '" + read_mark(dbf) + "', expected 'AFTER'");
        check(!present,                       "JVG_G0_a_replayed_log_is_removed",
              "the log survived a successful replay");
    }

    // ---- T1: a version from the future. Refuse, and KEEP. -------------------
    {
        const fs::path dbf = root / "T1.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: T1 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj", forged_log("TBJ9 T1"));

        bool present = false;
        const bool replayed = recover(dbf, present);
        check(!replayed,                      "JVG_T1_a_newer_version_is_refused",
              "a TBJ9 log was replayed by a build that reads TBJ1");
        check(read_mark(dbf) == "BEFORE",     "JVG_T1_the_row_was_not_touched",
              "MARK is '" + read_mark(dbf) + "', expected 'BEFORE'");
        check(present,                        "JVG_T1_the_refused_log_was_preserved",
              "the log was DELETED -- a commit a newer build could replay is now gone");
    }

    // ---- T2: a header this family never wrote. Refuse, and KEEP. ------------
    {
        const fs::path dbf = root / "T2.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: T2 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj", forged_log("NOTAHEADER"));

        bool present = false;
        const bool replayed = recover(dbf, present);
        check(!replayed,                      "JVG_T2_an_unreadable_header_is_refused",
              "a log with no TBJ header was replayed");
        check(read_mark(dbf) == "BEFORE",     "JVG_T2_the_row_was_not_touched",
              "MARK is '" + read_mark(dbf) + "', expected 'BEFORE'");
        check(present,                        "JVG_T2_the_refused_log_was_preserved",
              "the log was deleted rather than kept");
    }

    // ---- T3: an empty log is an aborted transaction, NOT a version problem. -
    // This arm guards against the gate's own regression: routing a zero-byte
    // .tbj through the refusal would warn on every USE, forever, about a file
    // that holds nothing and can never be recovered by anyone.
    {
        const fs::path dbf = root / "T3.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: T3 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj", "");

        bool present = true;
        const bool replayed = recover(dbf, present);
        check(!replayed,                      "JVG_T3_an_empty_log_replays_nothing",
              "an empty log reported a replay");
        check(read_mark(dbf) == "BEFORE",     "JVG_T3_the_row_was_not_touched",
              "MARK is '" + read_mark(dbf) + "', expected 'BEFORE'");
        check(!present,                       "JVG_T3_an_empty_log_is_discarded",
              "an empty log was PRESERVED -- it would warn on every USE forever");
    }

    fs::remove_all(root, ec);

    std::cout << "JOURNAL VERSION GATE: " << (g_failures == 0 ? "PASS" : "FAIL")
              << " -- 12 marker(s), " << g_failures << " red.\n";
    return g_failures == 0 ? 0 : 1;
}
