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
//   - Nothing about what this build WRITES. kJournalVersionWritten is still 1
//     and nothing in the tree emits a P marker yet; every TBJ2 log here is
//     forged, which is the only way to produce one. The P lane grades the
//     READER, and the reader shipping first is the point.
//   - Nothing about AIF-061's memo record. The U arms forge an 'M'-shaped line
//     to stand for a record from the future, and 'M' is unknown at every
//     version this build reads; what the real record contains is not decided
//     here.
//   - THE D LANE TESTS THE GUARD, NOT ITS CALLERS. It drives
//     journal_note_decided and journal_note_rollback directly, at the layer
//     that owns them. commit_group marks each member after decide_committed
//     and release_sql_transaction walks its enlistments into rollback, and
//     NEITHER OF THOSE PATHS IS EXERCISED HERE -- an edit that stopped
//     commit_group from marking would leave every arm in this file green. That
//     is a real gap and it is named rather than papered over; closing it needs
//     a fixture that can make an APPLY fail after a decision, which is a
//     different instrument.
//   - Nothing about a record this build knows but writes WRONGLY. The U lane
//     asks only whether an unrecognised tag is refused.
//   - Nothing about a real crash. The logs here are forged by hand, which is
//     the only way to produce a version this build cannot write.
//   - Nothing about a pre-header journal. Every log this family has written
//     carries the header; whether one ever existed without it was not swept.
//   - S0/S1 assert the SYS RECOVERY exemption. Its twin -- TABLE BUFFER
//     refusing a SYS table -- lives in table_buffer.cpp behind shell_engine()
//     and is NOT exercised here; this target deliberately links no shell.

#include "cli/group_log.hpp"
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
constexpr int kDeclaredMarkers = 64;   // 44 reader + 12 writer (W0-W3) + 8 teardown (D0-D3)

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

    // ---- P0: the DETECTOR for the prepare lane -----------------------------
    // AIF-160. A TBJ2 log carries `P <group-key> <n>` INSTEAD of a C marker:
    // this member prepared, and whether it committed is recorded in the group
    // log. Here the group IS decided, so the log must replay.
    //
    // Three of the four arms below assert that nothing happened. This one is
    // the reason they mean anything -- same log shape, same key spelling, the
    // only difference being that the decision row exists.
    {
        const fs::path sys_root = root / "sys";
        fs::create_directories(sys_root, ec);
        dottalk::paths::set_slot(dottalk::paths::Slot::SYS, sys_root);

        const std::string key = "testhost:1234:5678#1";
        std::string derr;
        if (!dottalk::group::decide_committed(key, 2, &derr)) {
            std::cerr << "FAIL: P0 fixture could not decide the group (" << derr << ")\n";
            return 1;
        }

        const fs::path dbf = root / "P0.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: P0 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj",
                   std::string("TBJ2 P0\n")
                 + "U 1 1 S 2:" + hex_of("AFTER   ") + "\n"
                 + "P " + key + " 2\n");

        bool present = true;
        const bool replayed = recover(dbf, present);
        check(replayed,                   "JVG_P0_a_decided_group_replays_its_member",
              "a prepared log whose group IS committed did not replay -- every P arm"
              " below is blind");
        check(read_mark(dbf) == "AFTER",  "JVG_P0_the_replay_reached_the_row",
              "MARK is '" + read_mark(dbf) + "', expected 'AFTER'");
        check(!present,                   "JVG_P0_a_replayed_log_is_removed",
              "the log survived a successful replay");
    }

    // ---- P1: presumed abort. No decision row means it did not commit -------
    // The same shape as P0 with a key nobody decided. There is no abort row in
    // the group log by design -- absence IS the answer -- so this discards.
    {
        const fs::path dbf = root / "P1.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: P1 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj",
                   std::string("TBJ2 P1\n")
                 + "U 1 1 S 2:" + hex_of("AFTER   ") + "\n"
                 + "P testhost:1234:5678#99 2\n");

        bool present = true;
        const bool replayed = recover(dbf, present);
        check(!replayed,                  "JVG_P1_an_undecided_group_does_not_replay",
              "a prepared log with NO decision row was replayed -- an aborted group"
              " just landed on disk");
        check(read_mark(dbf) == "BEFORE", "JVG_P1_the_row_was_not_touched",
              "MARK is '" + read_mark(dbf) + "', expected 'BEFORE'");
        check(!present,                   "JVG_P1_a_presumed_abort_is_discarded",
              "the log was PRESERVED -- presumed abort must clear the file");
    }

    // ---- P2: the record set is VERSION-SCOPED ------------------------------
    // A TBJ1 header with a P record inside it. P exists in TBJ2 and not in
    // TBJ1, so this file's own header says it cannot contain one. Accepting it
    // because a LATER version defines the record would spend the version number
    // and then ignore it, which is how the gate above came to be needed.
    {
        const fs::path dbf = root / "P2.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: P2 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj",
                   std::string("TBJ1 P2\n")
                 + "U 1 1 S 2:" + hex_of("AFTER   ") + "\n"
                 + "P testhost:1234:5678#1 2\n");

        bool present = false;
        const bool replayed = recover(dbf, present);
        check(!replayed,                  "JVG_P2_a_P_record_in_TBJ1_is_refused",
              "a TBJ1 log carrying a TBJ2 record was accepted");
        check(read_mark(dbf) == "BEFORE", "JVG_P2_the_row_was_not_touched",
              "MARK is '" + read_mark(dbf) + "', expected 'BEFORE'");
        check(present,                    "JVG_P2_the_refused_log_was_preserved",
              "the log was DELETED -- and its key names a group that IS committed");
    }

    // ---- P3: C and P are alternatives, not a pair --------------------------
    // C says this transaction decided itself; P says a group log decided it.
    // No protocol here writes both, and picking the "most likely" one is the
    // guessing this reader is being taken out of. Note the key is the DECIDED
    // one, so a reader that preferred either marker would replay.
    {
        const fs::path dbf = root / "P3.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: P3 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj",
                   std::string("TBJ2 P3\n")
                 + "U 1 1 S 2:" + hex_of("AFTER   ") + "\n"
                 + "P testhost:1234:5678#1 2\n"
                 + "C 1\n");

        bool present = false;
        const bool replayed = recover(dbf, present);
        check(!replayed,                  "JVG_P3_both_markers_is_refused",
              "a log claiming both C and P was replayed");
        check(read_mark(dbf) == "BEFORE", "JVG_P3_the_row_was_not_touched",
              "MARK is '" + read_mark(dbf) + "', expected 'BEFORE'");
    }

    // ---- P4: a journal belongs to at most one group ------------------------
    // Two P records, the FIRST naming the decided group. A reader that took
    // the first it found would replay; one that took the last would discard.
    // Both are guesses and the fixture does not say which is preferable.
    {
        const fs::path dbf = root / "P4.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: P4 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj",
                   std::string("TBJ2 P4\n")
                 + "U 1 1 S 2:" + hex_of("AFTER   ") + "\n"
                 + "P testhost:1234:5678#1 2\n"
                 + "P testhost:1234:5678#99 2\n");

        bool present = false;
        const bool replayed = recover(dbf, present);
        check(!replayed,                  "JVG_P4_two_prepare_markers_is_refused",
              "a log naming two groups was replayed");
        check(read_mark(dbf) == "BEFORE", "JVG_P4_the_row_was_not_touched",
              "MARK is '" + read_mark(dbf) + "', expected 'BEFORE'");
    }

    // ---- P5: a malformed P names no question -------------------------------
    // The record is `P <group-key> <members>`. With the member count missing
    // there is no reason to trust the key either, and a log we cannot read must
    // never be DISCARDED on the strength of something parsed out of it.
    {
        const fs::path dbf = root / "P5.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: P5 fixture could not be built (" << err << ")\n";
            return 1;
        }
        write_text(dbf.string() + ".tbj",
                   std::string("TBJ2 P5\n")
                 + "U 1 1 S 2:" + hex_of("AFTER   ") + "\n"
                 + "P testhost:1234:5678#1\n");

        bool present = false;
        const bool replayed = recover(dbf, present);
        check(!replayed,                  "JVG_P5_a_malformed_prepare_is_refused",
              "a P record with no member count was accepted");
        check(present,                    "JVG_P5_the_malformed_log_was_preserved",
              "the log was DELETED -- it may name a group that committed");
    }

    // ======================================================================
    // W0-W4: THE WRITER. Everything above hand-wrote its log with write_text
    // and therefore graded the READER. journal_begin_prepare had, until this
    // block, never executed -- it compiled, linked, and was called from
    // nowhere, which a green build reports as success.
    //
    // These arms are the only place the two halves meet. P0 proves the reader
    // accepts a log of the right shape; W0 proves the writer PRODUCES that
    // shape. Either alone is a half-measure that passes.
    // ======================================================================

    // ---- W0: the round trip, and the detector for W1-W4 --------------------
    // A real buffered transaction: open a log, journal one redo record, prepare
    // it into a decided group, and recover. If this does not replay, the writer
    // and the reader disagree about the format and every arm below is blind.
    {
        const fs::path sys_root = root / "sys";
        fs::create_directories(sys_root, ec);
        dottalk::paths::set_slot(dottalk::paths::Slot::SYS, sys_root);

        const int area0 = 0;
        const std::string key = "testhost:1234:5678#W0";
        std::string derr;
        if (!dottalk::group::decide_committed(key, 1, &derr)) {
            std::cerr << "FAIL: W0 fixture could not decide the group (" << derr << ")\n";
            return 1;
        }

        const fs::path dbf = root / "W0.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: W0 fixture could not be built (" << err << ")\n";
            return 1;
        }

        dottalk::table::set_persistence_mode(
            area0, dottalk::table::BufferPersistenceMode::RamJournal);
        if (!dottalk::table::journal_note_buffer_on(area0, dbf.string())) {
            std::cerr << "FAIL: W0 could not open a journal\n";
            return 1;
        }

        dottalk::table::ChangeEntry entry;
        entry.recno       = 1;
        entry.dirty_flags = dottalk::table::CHANGE_UPDATE;
        entry.priority    = 1;
        entry.new_values[2] = "AFTER   ";
        if (!dottalk::table::journal_note_change(area0, entry)) {
            std::cerr << "FAIL: W0 could not journal a redo record\n";
            return 1;
        }

        const bool prepared =
            dottalk::table::journal_begin_prepare(area0, key, 1);
        // Close the handle WITHOUT deleting the log. journal_note_commit and
        // journal_note_rollback both remove the file; clear_journal_state is
        // the only exit that leaves it on disk, which is what recovery needs
        // to find -- and is exactly the state a crash between prepare and
        // apply leaves behind.
        dottalk::table::clear_journal_state(area0);

        check(prepared,                   "JVG_W0_the_writer_prepared",
              "journal_begin_prepare returned false on a well-formed group");

        bool present = true;
        const bool replayed = recover(dbf, present);
        check(replayed,                   "JVG_W0_what_the_writer_wrote_replays",
              "the reader refused a log this build's own writer produced -- the"
              " writer and the reader disagree about TBJ2");
        check(read_mark(dbf) == "AFTER",  "JVG_W0_the_replay_reached_the_row",
              "MARK is '" + read_mark(dbf) + "', expected 'AFTER'");
        check(!present,                   "JVG_W0_a_replayed_log_is_removed",
              "the log survived a successful replay");
    }

    // ---- W1: the header was promoted, and nothing else was trampled --------
    // The promotion is a one-byte overwrite at offset 3 followed by a seek to
    // end. Byte 3 is asserted directly because that seek is the single most
    // fragile line in the writer, and the TABLE NAME is asserted because a
    // wrong offset would silently eat it and still leave a log that parses.
    {
        const int area0 = 0;
        const fs::path dbf = root / "W1.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: W1 fixture could not be built (" << err << ")\n";
            return 1;
        }

        dottalk::table::set_persistence_mode(
            area0, dottalk::table::BufferPersistenceMode::RamJournal);
        dottalk::table::journal_note_buffer_on(area0, dbf.string());
        const bool prepared = dottalk::table::journal_begin_prepare(
            area0, "testhost:1234:5678#W1", 3);
        dottalk::table::clear_journal_state(area0);

        std::ifstream in(dbf.string() + ".tbj", std::ios::binary);
        std::string header, body, line;
        std::getline(in, header);
        while (std::getline(in, line)) body += line + "\n";
        in.close();

        check(prepared && header.rfind("TBJ2 ", 0) == 0,
              "JVG_W1_the_header_was_promoted_to_TBJ2",
              "header is '" + header + "', expected it to start 'TBJ2 '");
        check(header.find(dbf.filename().string()) != std::string::npos,
              "JVG_W1_the_promotion_left_the_table_name_intact",
              "header is '" + header + "' -- the seek overwrote more than the"
              " version digit");
        check(body.find("P testhost:1234:5678#W1 3\n") != std::string::npos,
              "JVG_W1_the_prepare_record_is_well_formed",
              "no 'P <key> <members>' record found; body was:\n" + body);

        fs::remove(dbf.string() + ".tbj", ec);
    }

    // ---- W2: A PLAIN COMMIT STILL WRITES TBJ1 ------------------------------
    // THE NEGATIVE ARM, and the whole argument for promoting per log instead of
    // moving kJournalVersionWritten. If an ordinary single-table commit starts
    // stamping TBJ2, every build that predates this lane refuses a log it could
    // have replayed perfectly, and keeps it forever. Nothing else in this file
    // would notice, because every other arm here is about logs that DO carry a
    // P record.
    {
        const int area0 = 0;
        const fs::path dbf = root / "W2.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: W2 fixture could not be built (" << err << ")\n";
            return 1;
        }

        dottalk::table::set_persistence_mode(
            area0, dottalk::table::BufferPersistenceMode::RamJournal);
        dottalk::table::journal_note_buffer_on(area0, dbf.string());
        dottalk::table::journal_begin_commit(area0);
        dottalk::table::clear_journal_state(area0);

        std::ifstream in(dbf.string() + ".tbj", std::ios::binary);
        std::string header;
        std::getline(in, header);
        in.close();

        check(header.rfind("TBJ1 ", 0) == 0,
              "JVG_W2_an_ungrouped_commit_still_writes_TBJ1",
              "header is '" + header + "' -- a plain commit is stamping a"
              " version older builds refuse, for a record it does not contain");

        fs::remove(dbf.string() + ".tbj", ec);
    }

    // ---- W3: a key with whitespace is refused, and writes NOTHING ----------
    // The reader recovers the key with `is >> prepare_key`, so a key containing
    // a space reads back as its own PREFIX -- a different, almost certainly
    // absent, group -- and presumed abort then discards a committed
    // transaction with nothing to detect it. It is the one field in the record
    // whose corruption is invisible, so the writer refuses rather than encodes.
    //
    // The second arm matters as much as the first: a refusal that had already
    // promoted the header would leave a TBJ2 log with no P record in it.
    {
        const int area0 = 0;
        const fs::path dbf = root / "W3.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: W3 fixture could not be built (" << err << ")\n";
            return 1;
        }

        dottalk::table::set_persistence_mode(
            area0, dottalk::table::BufferPersistenceMode::RamJournal);
        dottalk::table::journal_note_buffer_on(area0, dbf.string());
        const bool refused_space =
            !dottalk::table::journal_begin_prepare(area0, "host:1 2:3#1", 1);
        const bool refused_empty =
            !dottalk::table::journal_begin_prepare(area0, "", 1);
        const bool refused_members =
            !dottalk::table::journal_begin_prepare(area0, "testhost:1:1#W3", 0);
        dottalk::table::clear_journal_state(area0);

        std::ifstream in(dbf.string() + ".tbj", std::ios::binary);
        std::string header, body, line;
        std::getline(in, header);
        while (std::getline(in, line)) body += line + "\n";
        in.close();

        check(refused_space,   "JVG_W3_a_key_with_whitespace_is_refused",
              "a key containing a space was written -- recovery would read its"
              " prefix and discard a committed group");
        check(refused_empty,   "JVG_W3_an_empty_key_is_refused",
              "an empty group key was accepted");
        check(refused_members, "JVG_W3_a_zero_member_count_is_refused",
              "members=0 was accepted; the reader treats it as malformed");
        check(header.rfind("TBJ1 ", 0) == 0 && body.find("P ") == std::string::npos,
              "JVG_W3_a_refused_prepare_wrote_nothing_at_all",
              "header is '" + header + "' and body was:\n" + body
              + "-- a refusal promoted the header or left a partial record");

        fs::remove(dbf.string() + ".tbj", ec);
    }

    dottalk::table::set_persistence_mode(
        0, dottalk::table::BufferPersistenceMode::RamOnly);

    // ======================================================================
    // THE D LANE -- THE JOURNAL THAT MUST SURVIVE ITS OWN TEARDOWN
    //
    // AIF-160, 2026-09-11. Every other arm in this file asks what RECOVERY
    // does. These ask what happens BEFORE recovery ever runs, in the window
    // this lane created and nothing else in the tree had: a group has been
    // DECIDED and a member has not finished APPLYING.
    //
    // That member keeps its journal on purpose. The decision row exists, the P
    // record is on the platter, and the next USE replays it. But every teardown
    // path in the tree -- release_sql_transaction walking its enlistments,
    // commit_group's own abort, cmd_ROLLBACK's shared body -- reaches
    // journal_note_rollback, and journal_note_rollback std::removes that file.
    // A committed transaction, a decision row saying so, and its only copy of
    // the redo deleted by cleanup.
    //
    // BufferJournalInfo::decided is the guard, and until these arms existed
    // NOTHING WOULD HAVE GONE RED IF IT WERE DELETED. Every SQLSEL arm, every
    // ctest target and the whole P and W lane stayed green with the protection
    // in place and would have stayed green with it removed, because no fixture
    // ever asked a decided journal to roll back.
    //
    // D0 IS THE DETECTOR AND IT IS NOT A FORMALITY. D1 and D2 assert that a
    // file SURVIVES. A journal_note_rollback that had quietly stopped deleting
    // anything at all would satisfy both while measuring nothing. D0 is the
    // same sequence with the single difference that the group was never
    // decided, and it REQUIRES the deletion.
    // ======================================================================

    // ---- D0: the detector. Not decided -> rollback deletes, as it always has
    {
        const int area0 = 0;
        const fs::path dbf = root / "D0.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: D0 fixture could not be built (" << err << ")\n";
            return 1;
        }

        dottalk::table::set_persistence_mode(
            area0, dottalk::table::BufferPersistenceMode::RamJournal);
        if (!dottalk::table::journal_note_buffer_on(area0, dbf.string())) {
            std::cerr << "FAIL: D0 could not open a journal\n";
            return 1;
        }
        dottalk::table::ChangeEntry entry;
        entry.recno       = 1;
        entry.dirty_flags = dottalk::table::CHANGE_UPDATE;
        entry.priority    = 1;
        entry.new_values[2] = "AFTER   ";
        dottalk::table::journal_note_change(area0, entry);
        dottalk::table::journal_begin_prepare(area0, "testhost:1234:5678#D0", 1);

        // PREPARED BUT NOT DECIDED. Nothing has told this journal that a group
        // row names it, so it is still this transaction's to discard.
        const bool rolled = dottalk::table::journal_note_rollback(area0);
        const bool gone   = !fs::exists(dbf.string() + ".tbj");

        check(rolled, "JVG_D0_an_undecided_journal_rolls_back",
              "journal_note_rollback refused a journal no group had decided --"
              " the guard is firing on everything and D1/D2 measure nothing");
        check(gone,   "JVG_D0_and_the_log_is_deleted",
              "the log survived a rollback that reported success");
    }

    // ---- D1: decided -> rollback REFUSES, and changes nothing --------------
    {
        const int area0 = 0;
        const fs::path dbf = root / "D1.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: D1 fixture could not be built (" << err << ")\n";
            return 1;
        }

        const std::string key = "testhost:1234:5678#D1";
        std::string derr;
        if (!dottalk::group::decide_committed(key, 1, &derr)) {
            std::cerr << "FAIL: D1 fixture could not decide the group (" << derr << ")\n";
            return 1;
        }

        dottalk::table::set_persistence_mode(
            area0, dottalk::table::BufferPersistenceMode::RamJournal);
        if (!dottalk::table::journal_note_buffer_on(area0, dbf.string())) {
            std::cerr << "FAIL: D1 could not open a journal\n";
            return 1;
        }
        dottalk::table::ChangeEntry entry;
        entry.recno       = 1;
        entry.dirty_flags = dottalk::table::CHANGE_UPDATE;
        entry.priority    = 1;
        entry.new_values[2] = "AFTER   ";
        dottalk::table::journal_note_change(area0, entry);
        dottalk::table::journal_begin_prepare(area0, key, 1);

        // THE DECISION LANDED. From here the journal is not this transaction's
        // to delete -- it belongs to the group row.
        const bool marked = dottalk::table::journal_note_decided(area0);
        const bool rolled = dottalk::table::journal_note_rollback(area0);
        const bool still  = fs::exists(dbf.string() + ".tbj");

        check(marked && !rolled, "JVG_D1_a_decided_journal_refuses_rollback",
              "journal_note_rollback accepted a journal the group had already"
              " decided");
        check(still,             "JVG_D1_the_decided_log_was_preserved",
              "THE LOG WAS DELETED -- a committed transaction's only copy of its"
              " redo was removed by the teardown path");

        // Close the handle without touching the file, the way a process exit
        // would, so D2 can read what a crash would have left.
        dottalk::table::clear_journal_state(area0);
    }

    // ---- D2: and the surviving log REPLAYS -- the point of keeping it ------
    // Preserving a file is worth nothing if recovery cannot finish the
    // transaction from it. D1 proves the teardown did not delete it; this
    // proves what was kept is the thing that makes the member whole.
    {
        const fs::path dbf = root / "D1.dbf";
        bool present = true;
        const bool replayed = recover(dbf, present);

        check(replayed,                  "JVG_D2_the_preserved_log_replays",
              "the journal the guard saved did not replay -- keeping it bought"
              " nothing");
        check(read_mark(dbf) == "AFTER", "JVG_D2_the_replay_completed_the_member",
              "MARK is '" + read_mark(dbf) + "', expected 'AFTER'");
    }

    // ---- D3: one P record per log, refused rather than obeyed --------------
    // A second prepare would write a second P. The reader refuses a log naming
    // two groups -- correctly, since choosing between group keys is guessing --
    // and PRESERVES it, so obeying a second call produces a journal that can
    // never replay and never goes away. A second C marker is harmless; a second
    // P is terminal, which is why the guard is on prepare and not on commit.
    {
        const int area0 = 0;
        const fs::path dbf = root / "D3.dbf";
        std::string err;
        if (!make_table(dbf, err) || !seed_row(dbf)) {
            std::cerr << "FAIL: D3 fixture could not be built (" << err << ")\n";
            return 1;
        }

        dottalk::table::set_persistence_mode(
            area0, dottalk::table::BufferPersistenceMode::RamJournal);
        dottalk::table::journal_note_buffer_on(area0, dbf.string());
        const bool first  =
            dottalk::table::journal_begin_prepare(area0, "testhost:1234:5678#D3a", 1);
        const bool second =
            dottalk::table::journal_begin_prepare(area0, "testhost:1234:5678#D3b", 1);
        dottalk::table::clear_journal_state(area0);

        std::ifstream in(dbf.string() + ".tbj", std::ios::binary);
        std::string body, line;
        std::size_t p_records = 0;
        while (std::getline(in, line)) {
            if (line.rfind("P ", 0) == 0) ++p_records;
            body += line + "\n";
        }
        in.close();

        check(first && !second, "JVG_D3_a_second_prepare_is_refused",
              "journal_begin_prepare accepted a second group for one journal");
        check(p_records == 1,   "JVG_D3_the_log_carries_exactly_one_P",
              "the log holds " + std::to_string(p_records) + " P record(s);"
              " body was:\n" + body);

        fs::remove(dbf.string() + ".tbj", ec);
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
