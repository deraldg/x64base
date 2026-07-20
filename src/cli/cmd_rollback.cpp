// src/cli/cmd_rollback.cpp
// @dottalk.usage v1
// owner: DOT|ROLLBACK
// command: ROLLBACK
// category: table-buffer
// status: supported
// noargs: rollback-current-area
// effect: discard-buffered-changes
// mutates: buffer-state dirty-stale-flags
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
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "cli/table_state.hpp"
#include "cli/command_output.hpp"

extern "C" xbase::XBaseEngine* shell_engine();

namespace {

static inline std::string up_copy(std::string s) {
    for (auto& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static int resolve_current_index(xbase::DbArea& A) {
    xbase::XBaseEngine* eng = shell_engine();
    if (!eng) return -1;

    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (&eng->area(i) == &A) return i;
    }
    return -1;
}

static void rollback_area(int area0, size_t& total_changes, int& areas_touched) {
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

} // namespace

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
                rollback_area(i, total_changes, areas_touched);
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

    const int area0 = resolve_current_index(A);
    if (area0 < 0) {
        cli::cmdout::print_prefixed_message(
            "ROLLBACK", dottalk::helpdata::MessageId::RollbackCannotDetermineCurrentAreaText);
        return;
    }

    size_t total_changes = 0;
    int areas_touched = 0;

    rollback_area(area0, total_changes, areas_touched);

    // For single-area rollback, keep the classic wording.
    cli::cmdout::print_prefixed_message(
        "ROLLBACK",
        dottalk::helpdata::MessageId::RollbackDiscardedText,
        {{"changes", std::to_string(total_changes)}});
}
