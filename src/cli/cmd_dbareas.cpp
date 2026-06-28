// src/cli/cmd_dbareas.cpp
//
// DBAREAS - Convenience wrapper around DBAREA.
//
// Key rule (matches cmd_schemas.cpp): filename() is the source of truth for
// whether a slot is "open". DbArea::isOpen() is not reliable during refactors.

// @dottalk.usage v1
// owner: DOT|DBAREAS
// command: DBAREAS
// category: workspace
// status: supported
// noargs: report
// effect: report
// mutates: no
// usage-access: DBAREAS USAGE
// summary:
//   Report current, selected, or all open DbArea/work-area state.
//
// usage:
//   DBAREAS
//   DBAREAS USAGE
//   DBAREAS <n>
//   DBAREAS ALL
//   DBAREAS REL
//
// notes:
//   DBAREAS with no arguments reports the current area by delegating to DBAREA.
//   DBAREAS <n> reports slot n when that slot is open.
//   DBAREAS ALL reports all open slots using filename() as the open-area truth.
//   DBAREAS REL reports the current area and appends relation summary/tree context.
//   DBAREAS is read-only; it reports session/work-area state and does not mutate table data.
//
// related:
//   DBAREA
//   WORKSPACE
//   REL
//   STATUS
//

#include <algorithm>
#include <cstdlib>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "cmd_dbarea.hpp"
#include "workareas.hpp"

#if __has_include("set_relations.hpp")
  #include "set_relations.hpp"
  #define HAVE_RELATIONS 1
#else
  #define HAVE_RELATIONS 0
#endif

namespace {

// ---- small helpers ---------------------------------------------------------

static inline std::string trim_copy(std::string s) {
    auto is_space = [](unsigned char ch) { return std::isspace(ch) != 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(),
        [&](unsigned char c){ return !is_space(c); }));
    s.erase(std::find_if(s.rbegin(), s.rend(),
        [&](unsigned char c){ return !is_space(c); }).base(), s.end());
    return s;
}

static inline std::string up_copy(std::string s) {
    for (auto& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

static inline bool try_parse_int(const std::string& s, int& out) {
    if (s.empty()) return false;
    char* end = nullptr;
    long v = std::strtol(s.c_str(), &end, 10);
    if (end == s.c_str() || *end != '\0') return false;
    out = static_cast<int>(v);
    return true;
}

// "Open truth" (matches cmd_schemas.cpp):
// A slot is open if (and only if) filename() is non-empty.
static inline bool open_truth(const xbase::DbArea& a) {
    try {
        return !a.filename().empty();
    } catch (...) {
        return false;
    }
}

static std::string infer_parent_from_area(const xbase::DbArea& a) {
    try {
        const std::string ln = a.logicalName();
        if (!ln.empty()) return up_copy(ln);
        return up_copy(a.name());
    } catch (...) {
        return {};
    }
}

#if HAVE_RELATIONS
static void print_relations_for_current_area(xbase::DbArea& current) {
    // Parent anchor inferred from *current* area identity (logicalName preferred).
    const std::string parent = infer_parent_from_area(current);

    // Wire parent + refresh counts for this anchor.
    try { relations_api::set_current_parent_name(parent); } catch (...) {}
    try { relations_api::refresh_for_current_parent(); } catch (...) {}

    std::cout << "\n";
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareasRelationsTitleText);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareasRelationsDividerText);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::DbareasParentAnchorLineText,
        {{"value", parent.empty() ? std::string("(unknown)") : parent}});

    // Direct children + match counts (current parent row context).
    std::vector<std::string> kids;
    try { kids = relations_api::child_areas_for_current_parent(); } catch (...) { kids.clear(); }

    if (kids.empty()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareasChildrenNoneText);
    } else {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareasChildrenDirectTitleText);
        for (const auto& child : kids) {
            int mc = 0;
            try { mc = relations_api::match_count_for_child(child); } catch (...) { mc = 0; }
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::DbareasChildMatchLineText,
                {{"child", child}, {"count", std::to_string(mc)}});
        }
    }

    // Tree view (REL LIST ALL style)
    std::cout << "\n";
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareasRelationTreeTitleText);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareasRelationTreeDividerText);

    std::vector<relations_api::PreviewRow> rows;
    try { rows = relations_api::list_tree_for_current_parent(/*recursive=*/true, /*max_depth=*/64); }
    catch (...) { rows.clear(); }

    if (rows.empty()) {
        std::cout << (parent.empty() ? "(none)" : parent) << "\n";
        return;
    }

    for (const auto& row : rows) {
        // IMPORTANT: PreviewRow field is `line` (not `text`).
        std::cout << row.line << "\n";
    }
}
#endif

} // namespace

// ---- Command ---------------------------------------------------------------

void cmd_DBAREAS(xbase::DbArea& current, std::istringstream& in)
{
    // Consume the remainder as a simple token stream.
    std::string tok;
    if (!(in >> tok)) {
        // No args: behave like DBAREA (current slot only)
        std::istringstream empty;
        cmd_DBAREA(current, empty);
        return;
    }

    const std::string up = up_copy(tok);

    if (up == "USAGE" || up == "HELP" || up == "?") {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareasUsageText);
        return;
    }

    if (up == "ALL") {
        // Print ONLY open slots (filename() truth), using DBAREA for canonical formatting.
        bool any = false;

        for (int i = 0; i < xbase::MAX_AREA; ++i) {
            xbase::DbArea* a = nullptr;
            try { a = workareas::db(i); } catch (...) { a = nullptr; }
            if (!a) continue;
            if (!open_truth(*a)) continue;

            any = true;
            std::istringstream empty;
            cmd_DBAREA(*a, empty);
        }

        if (!any) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareasNoOpenWorkAreasText);
        }
        return;
    }

    if (up == "REL") {
        // Current area summary + relations block (optional)
        std::istringstream empty;
        cmd_DBAREA(current, empty);

#if HAVE_RELATIONS
        print_relations_for_current_area(current);
#else
        std::cout << "\n";
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareasRelationsModuleMissingText);
#endif
        return;
    }

    // Numeric slot? (0-based)
    int slot = -1;
    if (try_parse_int(tok, slot)) {
        if (slot < 0 || slot >= xbase::MAX_AREA) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::DbareasSlotOutOfRangeText,
                {
                    {"slot", std::to_string(slot)},
                    {"max", std::to_string(xbase::MAX_AREA - 1)},
                });
            return;
        }

        xbase::DbArea* a = nullptr;
        try { a = workareas::db(slot); } catch (...) { a = nullptr; }

        if (!a || !open_truth(*a)) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::DbareasAreaNotOpenText,
                {{"slot", std::to_string(slot)}});
            return;
        }

        std::istringstream empty;
        cmd_DBAREA(*a, empty);
        return;
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareasUsageText);
}

