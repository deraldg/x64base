// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: AIF-160
// owner: member.derald
// status: experimental
//
// THE GROUP LOG, STEP 1 -- the catalog, the decision, and the lookup.
//
// One row in this catalog is the instant a multi-table group becomes true.
// Everything else in multi-area commit is arrangement around that fact, so it is
// graded before anything depends on it.
//
// WHAT THE ARMS ARE ACTUALLY FOR. Three of the properties here are the kind that
// look like formalities and are not:
//
//   PRESUMED ABORT. An unknown key must read NOT COMMITTED. That is not a
//   convenience -- it is the entire abort mechanism. There is no abort row, so
//   "absent" IS "did not commit", and a lookup that ever guessed otherwise would
//   replay a group that never happened.
//
//   A LOOKUP MUST NOT CREATE ITS OWN AUTHORITY. is_committed() is asked during
//   recovery, at USE, on a machine that may have just crashed. If asking the
//   question MINTED an empty catalog, then every later lookup would consult a
//   file created by the asking rather than by any decision -- and an empty
//   catalog answers "not committed" to everything, confidently. T1B is that arm.
//
//   THE CATALOG IS ENGINE STATE. It must sit under the SYS slot and be
//   recognised as such, because that is what makes it refuse the table buffer
//   and skip journal recovery -- which is what stops the group log from having
//   to be recovered by consulting itself.
//
// NOT CLAIMED:
//   - Nothing about durability under a crash. durable_sync is called and its
//     failure is reported; no arm here pulls power.
//   - Nothing about concurrency. One process, in sequence.
//   - Nothing about the LINEAR SCAN's cost. is_committed walks the catalog, the
//     design says an index is owed, and no arm here measures the growth.

#include "cli/group_log.hpp"
#include "cli/table_state.hpp"
#include "common/path_state.hpp"

#include <filesystem>
#include <iostream>
#include <string>

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
constexpr int kDeclaredMarkers = 27;

void check(bool condition, const std::string& marker, const std::string& detail) {
    ++g_checks;
    std::cout << marker << ":" << (condition ? ".T." : ".F.") << "\n";
    if (!condition) {
        std::cerr << "FAIL: " << marker << " -- " << detail << "\n";
        ++g_failures;
    }
}

} // namespace

int main() {
    namespace fs = std::filesystem;
    std::error_code ec;

    const fs::path root = fs::temp_directory_path(ec) / "dottalkpp_grouplog";
    fs::remove_all(root, ec);
    fs::create_directories(root, ec);
    const fs::path sys_root = root / "sys";
    dottalk::paths::set_slot(dottalk::paths::Slot::SYS, sys_root);

    const std::string catalog = dottalk::group::catalog_path();

    // ---- G0: the catalog is addressed under SYS and does not exist yet ------
    check(!catalog.empty(), "GRP_G0_catalog_has_a_path",
          "catalog_path() is empty -- the SYS slot did not take");
    check(!fs::exists(catalog, ec), "GRP_G0_catalog_absent_before_any_decision",
          "a group log existed before anything decided");

    // ---- T1: presumed abort, with NO catalog at all -------------------------
    {
        const bool committed = dottalk::group::is_committed("nobody:0:0#1");
        check(!committed, "GRP_T1_unknown_key_is_not_committed",
              "an unknown key read as COMMITTED -- presumed abort is broken and a "
              "group that never happened would replay");

        // T1B: and asking must not have MINTED the authority.
        check(!fs::exists(catalog, ec), "GRP_T1B_a_lookup_did_not_create_the_catalog",
              "is_committed() CREATED the group log. Every later lookup now "
              "consults a file made by the asking rather than by a decision, and "
              "an empty catalog answers 'not committed' to everything");
    }

    // ---- G1: keys are distinct, and reuse the process owner token -----------
    const std::string k1 = dottalk::group::mint_group_key();
    const std::string k2 = dottalk::group::mint_group_key();
    check(!k1.empty() && k1 != k2, "GRP_G1_minted_keys_are_distinct",
          "mint_group_key() returned '" + k1 + "' and '" + k2 + "'");

    // ---- T2: the decision lands, and only for the key decided ---------------
    {
        std::string err;
        const bool decided = dottalk::group::decide_committed(k1, 4, &err);
        check(decided, "GRP_T2_the_decision_was_written_and_synced",
              "decide_committed failed: " + err);
        check(fs::exists(catalog, ec), "GRP_T2_the_catalog_now_exists",
              "a decision reported success and created no catalog");
        check(dottalk::group::is_committed(k1), "GRP_T2_the_decided_key_reads_committed",
              "the key just decided does not read as committed");
        check(!dottalk::group::is_committed(k2), "GRP_T2_an_undecided_key_still_is_not",
              "a key that was never decided reads as COMMITTED -- the lookup is "
              "answering about the catalog rather than about the key");
    }

    // ---- G2: the catalog is ENGINE STATE, which is what guards it -----------
    check(dottalk::table::is_engine_state_file(catalog),
          "GRP_G2_the_catalog_is_engine_state",
          "the group log is not recognised as engine state, so it can be table-"
          "buffered and journal-recovered -- and recovering it would mean asking "
          "the group log whether the group log committed");

    // ---- T3: a second decision coexists; neither displaces the other --------
    {
        std::string err;
        check(dottalk::group::decide_committed(k2, 2, &err),
              "GRP_T3_a_second_decision_landed", "decide_committed failed: " + err);
        check(dottalk::group::is_committed(k1) && dottalk::group::is_committed(k2),
              "GRP_T3_both_decisions_survive",
              "a second decision displaced the first -- the catalog is append-only "
              "and a save must never overwrite");
        check(dottalk::group::decision_count() == 2, "GRP_T3_two_rows_are_on_disk",
              "decision_count() is " + std::to_string(dottalk::group::decision_count())
              + ", expected 2");
    }

    // ---- T4: an empty key is refused and writes nothing ---------------------
    {
        const long long before = dottalk::group::decision_count();
        std::string err;
        check(!dottalk::group::decide_committed("", 1, &err),
              "GRP_T4_an_empty_key_is_refused", "an empty group key was accepted");
        check(dottalk::group::decision_count() == before,
              "GRP_T4_the_refusal_wrote_no_row",
              "a refused decision still appended a row");
        check(!dottalk::group::is_committed(""),
              "GRP_T4_an_empty_key_is_never_committed",
              "an empty key read as committed");
    }

    // ---- M: the members table, which is what lets a row ever be retired ----
    // A group row is needed only while some member carries a P span, so
    // retirement needs to know the members. These arms cover the two readings
    // that must never be confused: "this group had no members recorded" and
    // "this group had members and they are these".
    {
        const std::string mk1 = dottalk::group::mint_group_key();
        const std::string mk2 = dottalk::group::mint_group_key();
        const std::string mpath = dottalk::group::members_path();

        check(!mpath.empty() && !fs::exists(mpath, ec),
              "GRP_M0_members_table_absent_before_any_prepare",
              "a members table existed before anything recorded members");

        // The read path must not mint the table it is asking -- same rule as
        // is_committed, and here it fails safe only by accident of retirement
        // reading "empty" as KEEP. Assert it so that stays deliberate.
        check(dottalk::group::members_of(mk1).empty(),
              "GRP_M1_unknown_group_has_no_members",
              "an unrecorded group reported members");
        check(!fs::exists(mpath, ec),
              "GRP_M1B_a_members_lookup_did_not_create_the_table",
              "members_of() CREATED the members table. A table minted by the "
              "asking answers 'no members' to everything, and retirement reads "
              "'no members' as KEEP -- safe today, a silent trap the moment that "
              "reading changes");

        std::string err;
        const std::vector<std::string> want = {
            "D:\\data\\dbf\\ALPHA.dbf",
            "D:\\data\\dbf\\BETA.dbf",
            "D:\\data\\dbf\\GAMMA.dbf",
        };
        check(dottalk::group::record_members(mk1, want, &err),
              "GRP_M2_members_recorded", "record_members failed: " + err);

        const std::vector<std::string> got = dottalk::group::members_of(mk1);
        check(got == want, "GRP_M2_members_read_back_in_order",
              "got " + std::to_string(got.size()) + " member(s), expected "
              + std::to_string(want.size()));

        // The discriminator: a second group must not inherit the first's
        // members. Retirement acting on the wrong member set would retire a
        // decision whose real members are still carrying P spans.
        check(dottalk::group::members_of(mk2).empty(),
              "GRP_M3_a_different_group_has_none_of_them",
              "a group that recorded nothing inherited another group's members");

        check(dottalk::group::record_members(mk2, {"D:\\data\\dbf\\DELTA.dbf"}, &err),
              "GRP_M3_second_group_recorded", "record_members failed: " + err);
        check(dottalk::group::members_of(mk1) == want &&
              dottalk::group::members_of(mk2).size() == 1,
              "GRP_M3_both_member_sets_survive",
              "recording a second group disturbed the first");

        // An empty list is not an error and writes nothing: a group that spans
        // no tables is degenerate, not broken.
        check(dottalk::group::record_members(mk1, {}, &err),
              "GRP_M4_an_empty_member_list_is_not_an_error",
              "recording zero members was refused: " + err);
        check(dottalk::group::members_of(mk1) == want,
              "GRP_M4_and_it_wrote_nothing",
              "an empty member list disturbed the recorded rows");
        check(!dottalk::group::record_members("", {"X"}, &err),
              "GRP_M4_an_empty_key_is_refused",
              "an empty group key accepted members");
    }

    fs::remove_all(root, ec);

    if (g_checks != kDeclaredMarkers) {
        std::cerr << "FAIL: GRP_MARKER_COUNT -- ran " << g_checks
                  << " marker(s), this file declares " << kDeclaredMarkers
                  << ". An arm stopped running, or the declared total was not "
                     "updated when one was added.\n";
        ++g_failures;
    }

    std::cout << "GROUP LOG: " << (g_failures == 0 ? "PASS" : "FAIL")
              << " -- " << g_checks << " of " << kDeclaredMarkers
              << " marker(s), " << g_failures << " red.\n";
    return g_failures == 0 ? 0 : 1;
}
