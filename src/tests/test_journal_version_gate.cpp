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
//     still writes TBJ1 deliberately. The U arms forge an 'M'-shaped line to
//     stand for a record from the future; they say nothing about what AIF-061's
//     memo record will actually contain.
//   - Nothing about a record this build knows but writes WRONGLY. The U lane
//     asks only whether an unrecognised tag is refused.
//   - Nothing about a real crash. The logs here are forged by hand, which is
//     the only way to produce a version this build cannot write.
//   - Nothing about a pre-header journal. Every log this family has written
//     carries the header; whether one ever existed without it was not swept.
//   - S0/S1 assert the SYS RECOVERY exemption. Its twin -- TABLE BUFFER
//     refusing a SYS table -- lives in table_buffer.cpp behind shell_engine()
//     and is NOT exercised here; this target deliberately links no shell.

#include "cli/table_state.hpp"
#include "common/path_state.hpp"
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
int g_checks   = 0;

// THE DECLARED TOTAL, hand-written on purpose.
//
// Every other number this file prints is derived from what ran, which is
// exactly why none of them can contradict what ran. This one is written down
// separately so it CAN disagree, and a disagreement is red.
//
// It catches the arm that stops running without failing: a guard that turned
// false, a block that returned early, a section someone commented out while
// chasing something else. Those do not print .F. -- they print nothing, and a
// count derived from what happened would happily report the smaller number as
// a pass. Marker-count discipline says count first and read verdicts second;
// this makes the binary do it.
//
// IT DOES NOT DETECT A STALE BINARY. A binary built from older source carries
// the older markers AND the older total, and the two agree. Nothing inside a
// program can tell that it is the wrong program -- that is the build's job,
// and build.ps1 now derives its test-target list from src/tests for it.
//
// Adding a marker means editing this number. That cost is paid in the file
// being edited, and forgetting it fails loudly rather than quietly.
constexpr int kDeclaredMarkers = 29;

void check(bool condition, const std::string& marker, const std::string& detail) {
    ++g_checks;
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

    // ---- U1: a record this build does not know, in a version it does -------
    // The version gate cannot see this one. The header says TBJ1, which this
    // build reads; the unknown record sits INSIDE the log. It is placed after a
    // valid U and before the C deliberately: a reader that validated lazily
    // would already have written the row by the time it met the record it
    // cannot read, and would then refuse a log it had half applied.
    {
        const fs::path dbf = root / "U1.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: U1 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj",
                   std::string("TBJ1 U1\n")
                 + "U 1 1 S 2:" + hex_of("AFTER   ") + "\n"
                 + "M 1 objid:7f devnull\n"
                 + "C 1\n");

        bool present = false;
        const bool replayed = recover(dbf, present);
        check(!replayed,                  "JVG_U1_an_unknown_record_is_refused",
              "a log carrying an unknown record was replayed");
        check(read_mark(dbf) == "BEFORE", "JVG_U1_not_even_the_known_records_ran",
              "MARK is '" + read_mark(dbf) + "', expected 'BEFORE' -- the log was"
              " half applied before it was refused");
        check(present,                    "JVG_U1_the_refused_log_was_preserved",
              "the log was DELETED -- a commit a newer build could replay is now gone");
    }

    // ---- U2: a tag is a TOKEN, and this is the arm that costs something -----
    // `UPD` is not a record. Against the one-byte match this reader shipped
    // with -- `ln[0] == 'I' || ln[0] == 'U'` -- it was not dropped, it was READ
    // AS AN UPDATE: the token became the tag, the next integer a recno, and the
    // `<n>:<hex>` pair a field to set. So the old reader writes WRONG into the
    // row. That is not a record ignored; it is a record misread, and it is the
    // reason the tag rule had to move out of the C test and into one place.
    {
        const fs::path dbf = root / "U2.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: U2 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj",
                   std::string("TBJ1 U2\n")
                 + "UPD 1 1 S 2:" + hex_of("WRONG   ") + "\n"
                 + "C 1\n");

        bool present = false;
        const bool replayed = recover(dbf, present);
        check(!replayed,                  "JVG_U2_a_prefix_collision_is_refused",
              "'UPD' was accepted as a record by a build that knows only 'U'");
        check(read_mark(dbf) == "BEFORE", "JVG_U2_the_row_was_not_written",
              "MARK is '" + read_mark(dbf) + "', expected 'BEFORE' -- 'UPD' was"
              " misread as an update and wrote a field");
        check(present,                    "JVG_U2_the_refused_log_was_preserved",
              "the log was DELETED");
    }

    // ---- U3: a blank line is not a record ----------------------------------
    // The control for U1 and U2. If the refusal fired on anything that is not
    // a known tag, an empty line would refuse too, and every arm above would be
    // green for the wrong reason.
    {
        const fs::path dbf = root / "U3.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: U3 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj",
                   std::string("TBJ1 U3\n")
                 + "\n"
                 + "U 1 1 S 2:" + hex_of("AFTER   ") + "\n"
                 + "\n"
                 + "C 1\n");

        bool present = true;
        const bool replayed = recover(dbf, present);
        check(replayed,                   "JVG_U3_blank_lines_do_not_refuse",
              "a blank line was treated as an unknown record");
        check(read_mark(dbf) == "AFTER",  "JVG_U3_the_replay_reached_the_row",
              "MARK is '" + read_mark(dbf) + "', expected 'AFTER'");
    }

    // ---- U4: an UNCOMMITTED log with an unknown record is still DISCARDED ---
    // This pins the PLACEMENT, which is the part of the design that could
    // silently drift. The validation pass runs only for committed logs, because
    // this WAL fsyncs exactly once -- in journal_begin_commit, after the C
    // marker -- so a torn tail can only exist in a log with no C. Validating
    // those would convert every interrupted transaction into a permanent
    // warning about a file that is correctly deletable.
    {
        const fs::path dbf = root / "U4.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: U4 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj",
                   std::string("TBJ1 U4\n")
                 + "U 1 1 S 2:" + hex_of("AFTER   ") + "\n"
                 + "M 1 objid:7f devnull\n");   // no C marker

        bool present = true;
        const bool replayed = recover(dbf, present);
        check(!replayed,                  "JVG_U4_an_uncommitted_log_replays_nothing",
              "an uncommitted log reported a replay");
        check(read_mark(dbf) == "BEFORE", "JVG_U4_the_row_was_not_touched",
              "MARK is '" + read_mark(dbf) + "', expected 'BEFORE'");
        check(!present,                   "JVG_U4_an_uncommitted_log_is_still_discarded",
              "an uncommitted log was PRESERVED -- it would warn on every USE forever");
    }

    // ---- S0: the SYS predicate itself ---------------------------------------
    // AIF-160. Tables under the SYS slot are engine state: written directly,
    // never buffered, never recovered. The rule is LOCATION, so the predicate is
    // what everything else leans on and it is asserted before it is trusted.
    {
        const fs::path sys_root = root / "sys";
        fs::create_directories(sys_root, ec);
        fs::create_directories(root / "sysx", ec);
        dottalk::paths::set_slot(dottalk::paths::Slot::SYS, sys_root);

        check(dottalk::table::is_engine_state_file((sys_root / "GROUPS.dbf").string()),
              "JVG_S0_a_file_under_sys_is_engine_state",
              "a file directly under the SYS slot was not recognised");
        // The discriminator: a STRING prefix test passes this and must not.
        check(!dottalk::table::is_engine_state_file((root / "sysx" / "T.dbf").string()),
              "JVG_S0_a_sys_prefixed_sibling_is_not",
              "'sysx' matched the SYS slot -- the check is a string prefix, not "
              "component-wise, and any directory starting with the slot name is "
              "now silently exempt from recovery");
        check(!dottalk::table::is_engine_state_file((root / "G0.dbf").string()),
              "JVG_S0_an_ordinary_table_is_not",
              "an ordinary table outside SYS was treated as engine state -- "
              "recovery is now disabled for it");
    }

    // ---- S1: recovery SKIPS a SYS table, and leaves its log alone -----------
    // The fixture is G0's exactly -- a valid, committed TBJ1 log that WOULD
    // replay. Only the table's location differs, so a green here is the guard
    // and nothing else.
    {
        const fs::path sys_root = root / "sys";
        const fs::path dbf = sys_root / "S1.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: S1 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj", forged_log("TBJ1 S1"));

        bool present = false;
        const bool replayed = recover(dbf, present);
        check(!replayed,                  "JVG_S1_recovery_skips_a_sys_table",
              "a committed journal under SYS was replayed -- engine state can now "
              "be recovered, and the group log could be asked to recover itself");
        check(read_mark(dbf) == "BEFORE", "JVG_S1_the_sys_row_was_not_touched",
              "MARK is '" + read_mark(dbf) + "', expected 'BEFORE'");
        check(present,                    "JVG_S1_the_sys_log_was_left_alone",
              "the log was DELETED. A .tbj under SYS is a BUG TO BE FOUND, not a "
              "file to be quietly consumed -- recovery must neither replay it nor "
              "remove it");
    }

    fs::remove_all(root, ec);

    if (g_checks != kDeclaredMarkers) {
        std::cerr << "FAIL: JVG_MARKER_COUNT -- ran " << g_checks
                  << " marker(s), this file declares " << kDeclaredMarkers
                  << ". An arm stopped running, or the declared total was not "
                     "updated when one was added.\n";
        ++g_failures;
    }

    std::cout << "JOURNAL VERSION GATE: " << (g_failures == 0 ? "PASS" : "FAIL")
              << " -- " << g_checks << " of " << kDeclaredMarkers
              << " marker(s), " << g_failures << " red.\n";
    return g_failures == 0 ? 0 : 1;
}
