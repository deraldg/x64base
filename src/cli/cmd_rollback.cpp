// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_rollback.cpp
// @dottalk.usage v1
// owner: DOT|ROLLBACK
// command: ROLLBACK
// category: table-buffer
// status: supported
// noargs: rollback-current-area
// effect: discard-buffered-changes
// mutates: buffer-state dirty-stale-flags journal
// usage-access: ROLLBACK USAGE
// summary:
//   Discard buffered/uncommitted table changes for the current area or all areas.
//
// usage:
//   ROLLBACK USAGE
//   ROLLBACK
//   ROLLBACK ALL
//
// examples:
//   ROLLBACK
//   ROLLBACK ALL
//
// notes:
//   ROLLBACK USAGE returns before modifying buffer state.
//   ROLLBACK without arguments clears buffered state for the current area.
//   ROLLBACK ALL clears buffered state across all areas.
//   ROLLBACK best-effort notes a ROLLBACK marker in the durable journal for the area.
//
// risk:
//   discards_uncommitted_changes: yes except usage
//   mutates_buffer_state: yes except usage
//   mutates_table_data: no
//
// related:
//   COMMIT
//   TABLE BUFFER
//

#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "cli/table_state.hpp"
#include "cli/command_output.hpp"

#include "workarea_util.hpp"
#include "cli/table_buffer.hpp"     // AIF-159 s7.6: the shared body this file fills in
#include "sqlsel_statement.hpp"      // AIF-159 s7.6: sqlsel::transaction_active()
extern "C" xbase::XBaseEngine* shell_engine();

namespace {

static inline std::string up_copy(std::string s) {
    for (auto& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

} // namespace

// File-local, but OUTSIDE the anonymous namespace so both the ALL branch and
// cli::rollback::rollback_area below name the same helper. Renamed from
// rollback_area to rollback_area_impl so it cannot be confused with the public
// entry point that now shares this file (AIF-159 s7.6).
static void rollback_area_impl(int area0, size_t& total_changes, int& areas_touched) {
    // We consider an area "touched" if it had buffered changes OR flags set.
    bool touched = false;

    auto& tb = dottalk::table::get_tb(area0);
    if (!tb.empty()) {
        total_changes += tb.changes.size();

        // Persistent TABLE BUFFER stub hook. Future implementation should
        // append/mark ROLLBACK or delete the uncommitted journal here.
        (void)dottalk::table::journal_note_rollback(area0);

        tb.clear();
        touched = true;
    }

    // If TABLE is enabled, clear state flags (even if buffer was empty).
    // Contract: rollback means clean/fresh.
    if (dottalk::table::is_enabled(area0)) {
        if (dottalk::table::is_dirty(area0) || dottalk::table::is_stale(area0)) touched = true;

        dottalk::table::set_dirty(area0, false);
        dottalk::table::set_stale(area0, false);   // should clear stale bitset internally if implemented that way
        dottalk::table::clear_stale_fields(area0); // explicit/defensive
    }

    if (touched) ++areas_touched;
}

// ---------------------------------------------------------------------------
// AIF-159 s7.6 -- the single-area body, lifted so the SQL path can call it.
//
// rollback_sql_transaction used to reach cmd_ROLLBACK directly. It now calls
// this instead, which is what lets the command below carry a guard the SQL path
// does not trip over. Everything observable is unchanged: slot_of_area first,
// the same CannotDetermine message, the same rollback_area, the same discarded
// count in the same catalog message.
// ---------------------------------------------------------------------------
namespace cli { namespace rollback {

void rollback_area(xbase::DbArea& A, Outcome& out)
{
    out = Outcome{};

    const int area0 = cli::slot_of_area(&A);
    if (area0 < 0) {
        cli::cmdout::print_prefixed_message(
            "ROLLBACK", dottalk::helpdata::MessageId::RollbackCannotDetermineCurrentAreaText);
        return;
    }

    ::rollback_area_impl(area0, out.discarded_changes, out.areas_touched);

    cli::cmdout::print_prefixed_message(
        "ROLLBACK",
        dottalk::helpdata::MessageId::RollbackDiscardedText,
        {{"changes", std::to_string(out.discarded_changes)}});
}

}} // namespace cli::rollback


static void print_rollback_usage_contract()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::RollbackUsageText);
}
void cmd_ROLLBACK(xbase::DbArea& A, std::istringstream& in) {
    // ROLLBACK_USAGE_CONTRACT_BRANCH
    {
        const std::streampos usage_pos = in.tellg();
        std::string usage_tok;
        if (in >> usage_tok) {
            in.clear();
            if (usage_pos != std::streampos(-1)) {
                in.seekg(usage_pos);
            }

            const std::string u = up_copy(usage_tok);
            if (u == "USAGE" || u == "HELP" || u == "?") {
                print_rollback_usage_contract();
                return;
            }
        } else {
            in.clear();
            if (usage_pos != std::streampos(-1)) {
                in.seekg(usage_pos);
            }
        }
    }


    // AIF-159 s7.6 -- REFUSE A NATIVE ROLLBACK INSIDE A SQL TRANSACTION.
    //
    // Same hazard as the COMMIT half and the same owner ruling: refuse, because
    // SET MODE already refuses it (src/cli/cmd_set.cpp:730). The difference is
    // what the leak costs. A native COMMIT at least wrote the data before
    // leaving the scope open; a native ROLLBACK DISCARDS the staged work and
    // still leaves the user inside a transaction they never opened, so the next
    // autocommit DML stages instead of committing.
    //
    // After the USAGE branch, so ROLLBACK USAGE still prints. Before ALL and
    // before the single-area path, because ALL would otherwise reach the
    // enlisted area from the side and throw its buffer away.
    if (sqlsel::transaction_active()) {
        std::cout << "ROLLBACK: a SQL transaction is active; end it with COMMIT or "
                     "ROLLBACK in SQL mode (SET MODE SQL). A native ROLLBACK would "
                     "discard the buffered changes and leave the transaction open.\n";
        return;
    }

    std::string tok;
    if (in >> tok) {
        const std::string up = up_copy(tok);
        if (up == "ALL") {
            auto* eng = shell_engine();
            if (!eng) {
                cli::cmdout::print_prefixed_message(
                    "ROLLBACK", dottalk::helpdata::MessageId::RollbackEngineUnavailableText);
                return;
            }

            size_t total_changes = 0;
            int areas_touched = 0;

            for (int i = 0; i < xbase::MAX_AREA; ++i) {
                rollback_area_impl(i, total_changes, areas_touched);
            }

            cli::cmdout::print_prefixed_message(
                "ROLLBACK ALL",
                dottalk::helpdata::MessageId::RollbackAllDiscardedText,
                {{"changes", std::to_string(total_changes)},
                 {"areas", std::to_string(areas_touched)}});
            return;
        }

        print_rollback_usage_contract();
        return;
    }

    // AIF-159 s7.6: same work, same output; the counts are simply available now.
    cli::rollback::Outcome outcome;
    cli::rollback::rollback_area(A, outcome);
}
