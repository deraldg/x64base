// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// @dottalk.usage v1
// owner: DOT|HELP_GROUPED_IMPL
// command: HELP
// category: help-helper
// status: implementation-helper
// noargs: n/a
// effect: report
// mutates: none
// usage-access: owned-by HELP
// summary:
//   Helper implementation for grouped HELP/reflection output.
//
// usage:
//   This file does not export a standalone shell command.
//   User-visible usage is owned by HELP, CMDHELP, and related HELP reflection commands.
//
// notes:
//   Keep this file focused on grouped presentation/reporting support.
//   Do not register a separate HELP_GROUPED command from here.
//
// risk:
//   mutates_table_data: no
//

// src/cli/cmd_help_grouped.cpp
#include "cmd_help.hpp"
#include "cli/output_router.hpp"
#include "cli/expr/function_catalog.hpp"

#include <algorithm>
#include <cctype>
#include <iomanip>
#include <map>
#include <ostream>
#include <string>
#include <vector>

namespace {

inline std::ostream& out()
{
    return cli::OutputRouter::instance().out();
}

inline std::string uptrim(std::string s)
{
    auto notspace = [](unsigned char c) { return !std::isspace(c); };
    s.erase(std::begin(s), std::find_if(std::begin(s), std::end(s), notspace));
    s.erase(std::find_if(std::rbegin(s), std::rend(s), notspace).base(), std::end(s));
    std::transform(std::begin(s), std::end(s), std::begin(s),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

inline std::vector<dottalk::expr::FunctionCategory> function_category_order()
{
    using dottalk::expr::FunctionCategory;
    return {
        FunctionCategory::Numeric,
        FunctionCategory::Date,
        FunctionCategory::String,
        FunctionCategory::Search,
        FunctionCategory::Logical,
        FunctionCategory::Construction,
        FunctionCategory::Conversion,
        // NOTE: this list is DUPLICATED verbatim in cmd_export_functions.cpp and
        // cmd_help_grouped.cpp. Add a category to one and not the other and
        // EXPORTFUNCTIONS and HELP silently disagree about what exists -- the
        // omission is invisible because a missing category prints nothing rather
        // than erroring. Both were updated together for Cursor.
        FunctionCategory::Cursor,
        FunctionCategory::Misc
    };
}

inline std::map<dottalk::expr::FunctionCategory, std::vector<const dottalk::expr::FunctionDoc*>>
group_function_docs()
{
    std::map<dottalk::expr::FunctionCategory, std::vector<const dottalk::expr::FunctionDoc*>> groups;
    const auto docs = dottalk::expr::all_function_docs();

    for (const auto* doc : docs) {
        if (!doc) continue;
        groups[doc->category].push_back(doc);
    }

    for (auto& [cat, vec] : groups) {
        (void)cat;
        std::sort(vec.begin(), vec.end(),
                  [](const dottalk::expr::FunctionDoc* a, const dottalk::expr::FunctionDoc* b) {
                      return a->name < b->name;
                  });
    }

    return groups;
}

inline bool parse_function_category_token_local(const std::string& token,
                                                dottalk::expr::FunctionCategory& out_cat)
{
    using dottalk::expr::FunctionCategory;

    const std::string t = uptrim(token);

    struct Entry {
        const char* token;
        FunctionCategory category;
    };

    static const Entry entries[] = {
        {"NUMERIC",       FunctionCategory::Numeric},
        {"NUMERICS",      FunctionCategory::Numeric},
        {"DATE",          FunctionCategory::Date},
        {"DATES",         FunctionCategory::Date},
        {"STRING",        FunctionCategory::String},
        {"STRINGS",       FunctionCategory::String},
        {"SEARCH",        FunctionCategory::Search},
        {"SEARCHES",      FunctionCategory::Search},
        {"LOGICAL",       FunctionCategory::Logical},
        {"LOGICALS",      FunctionCategory::Logical},
        {"CONSTRUCTION",  FunctionCategory::Construction},
        {"CONSTRUCTIONS", FunctionCategory::Construction},
        {"CONVERSION",    FunctionCategory::Conversion},
        {"CONVERSIONS",   FunctionCategory::Conversion},
        {"CURSOR",        FunctionCategory::Cursor},
        {"CURSORS",       FunctionCategory::Cursor},
        {"ROW",           FunctionCategory::Cursor},
        {"MISC",          FunctionCategory::Misc}
    };

    for (const auto& e : entries) {
        if (t == e.token) {
            out_cat = e.category;
            return true;
        }
    }

    return false;
}

inline bool show_function_category_impl(dottalk::expr::FunctionCategory category)
{
    const auto groups = group_function_docs();
    const auto it = groups.find(category);
    if (it == groups.end() || it->second.empty()) return false;

    std::string heading = dottalk::expr::to_string(category);
    std::transform(heading.begin(), heading.end(), heading.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });

    out() << heading << " FUNCTIONS\n";
    out() << std::string(heading.size() + 10, '=') << "\n\n";

    for (const auto* doc : it->second) {
        out() << std::left << std::setw(12) << doc->name << " " << doc->summary << "\n";
    }

    out() << "\nUsage:\n";
    out() << "  HELP FUNCTION <name>\n";
    out() << "  HELP FUNCTIONS\n";
    return true;
}

} // anonymous namespace

namespace dottalk::help_grouped {

void show_function_index_grouped()
{
    const auto groups = group_function_docs();
    const auto order = function_category_order();

    out() << "FUNCTIONS\n";
    out() << "=========\n\n";

    for (const auto cat : order) {
        const auto it = groups.find(cat);
        if (it == groups.end() || it->second.empty()) continue;

        std::string heading = dottalk::expr::to_string(cat);
        std::transform(heading.begin(), heading.end(), heading.begin(),
                       [](unsigned char c) { return static_cast<char>(std::toupper(c)); });

        out() << heading << " (" << it->second.size() << ")\n";
        out() << std::string(heading.size() + 4 + std::to_string(it->second.size()).size(), '-') << "\n";

        int col = 0;
        for (const auto* doc : it->second) {
            out() << std::left << std::setw(12) << doc->name;
            if (++col % 5 == 0) out() << "\n";
        }
        if (col % 5 != 0) out() << "\n";
        out() << "\n";
    }

    out() << "Usage:\n";
    out() << "  HELP FUNCTIONS\n";
    out() << "  HELP FUNCTION <name>\n";
    // DERIVED, NOT TYPED. This line used to be a hand-written list of the eight
    // categories, and adding a ninth (Cursor, 2026-09-05) left it naming eight --
    // help text advertising a set that no longer matched the set. It was caught by
    // reading HELP's own output rather than by any gate, which is exactly how long
    // it would have survived otherwise.
    //
    // Building it from function_category_order() means the next category cannot
    // introduce the same drift: the sentence and the enum have one source.
    out() << "  HELP <category>      (";
    {
        bool first = true;
        for (const auto cat : function_category_order()) {
            if (!first) out() << ", ";
            first = false;
            std::string label = dottalk::expr::to_string(cat);
            for (char& ch : label) {
                ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
            }
            out() << label;
        }
    }
    out() << ")\n";
    out() << "  HELP <name>          (falls through to function help if no command owns the name)\n";
}

bool try_show_function_category(const std::string& token)
{
    dottalk::expr::FunctionCategory category{};
    if (!parse_function_category_token_local(token, category)) {
        return false;
    }
    return show_function_category_impl(category);
}

} // namespace dottalk::help_grouped
