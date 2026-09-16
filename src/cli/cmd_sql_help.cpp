// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// cmd_sql_help.cpp
// @dottalk.usage v1
// owner: DOT|SQLHELP
// command: SQLHELP
// category: reference
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: SQLHELP USAGE
// summary:
//   Display or search the SQL helper/reference catalog.
//
// usage:
//   SQLHELP
//   SQLHELP USAGE
//   SQLHELP SQLSEL
//   SQLHELP LIST-CATEGORIES
//   SQLHELP <category>
//   SQLHELP <term>
//
// examples:
//   SQLHELP
//   SQLHELP SQLSEL
//   SQLHELP INDEXING
//   SQLHELP CREATE-INDEX
//   SQLHELP LIST-CATEGORIES
//
// notes:
//   SQLHELP with no arguments displays the grouped SQL reference.
//   SQLHELP USAGE prints command usage without searching the catalog.
//   SQLHELP is read-only and does not execute SQL.
//   THE CATALOG IS A PORTABLE SQLite/MSSQL REFERENCE AND RUNS NOTHING HERE.
//     This engine's own SELECT is SQLSEL. SQLHELP SQLSEL DELEGATES to
//     sqlsel::print_statement_usage() -- the ONE runtime description of the
//     statement grammar -- rather than keeping a second copy. Three
//     authorities for one command's help is how the text drifts from the
//     code, which AIF-074 caught twice in one day.
//
// risk:
//   mutates_table_data: no
//   executes_sql: no
//
// related:
//   SQL
//   SQLSEL
//   SQLITE
//   SHOW
//   PSHELL
//

#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <string>

#include "sql_ref.hpp"
#include "sqlsel_statement.hpp"   // the ONE statement-grammar description; delegated to, never copied

#if __has_include("dli/registry.hpp")
  #include "dli/registry.hpp"
  #define DT_HAVE_DLI_REGISTRY 1
#else
  #define DT_HAVE_DLI_REGISTRY 0
#endif

namespace {
std::string to_upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}


void print_sqlhelp_usage()
{
    std::cout
        << "Usage:\n"
        << "  SQLHELP\n"
        << "  SQLHELP USAGE\n"
        << "  SQLHELP LIST-CATEGORIES\n"
        << "  SQLHELP <category>\n"
        << "  SQLHELP <term>\n"
        << "Examples:\n"
        << "  SQLHELP INDEXING\n"
        << "  SQLHELP CREATE-INDEX\n"
        << "  SQLHELP LIST-CATEGORIES\n"
        << "Notes:\n"
        << "  - SQLHELP is a read-only reference command; it does not execute SQL.\n";
}

bool sqlhelp_usage_request(const std::string& raw)
{
    const std::string u = to_upper(raw);
    return u == "USAGE" || u == "HELP" || u == "?";
}

// Greedy word wrap. Local because nothing in scope wraps a std::string --
// OutputRouter::set_wrap is the router's own behaviour, not a text utility.
void print_wrapped(const char* text, const char* indent, std::size_t width) {
    std::istringstream in(text);
    std::string word, line;
    while (in >> word) {
        if (!line.empty() && line.size() + 1 + word.size() > width) {
            std::cout << indent << line << "\n";
            line.clear();
        }
        if (!line.empty()) line += ' ';
        line += word;
    }
    if (!line.empty()) std::cout << indent << line << "\n";
}

void print_item(const sqlref::Item& it, bool verbose = true) {
    std::cout << it.name << "\n";
    std::cout << "  " << it.syntax << "\n";
    std::cout << "  " << it.summary << "\n";
    if (!it.portable) {
        std::cout << "  (SQLite/MSSQL differences apply)\n";
    }

    // THE x64 MAPPING NOTE HAD NO READER UNTIL 2026-09-09, and this is the line
    // that gives it one. Item::x64 answers the question the catalog exists for
    // -- its own declaration comment says so: "I know this SQL construct -- does
    // x64base do it, and by what command?" -- and this function emitted name,
    // syntax, summary and the portability line and STOPPED. Seventeen entries
    // carried a mapping note that only sql_conformance_gate.py and the website
    // (which quotes the header verbatim) could see. A reference that ships the
    // answer and cannot print it is not a reference. Found 2026-09-09 while
    // verifying a correction to the CREATE-TABLE entry: the corrected text was
    // provably in the binary and provably unreachable from the prompt.
    //
    // DETAIL VIEW ONLY, deliberately. These notes run past a thousand
    // characters, so the partial-search path (verbose=false) still prints one
    // block per hit -- flooding a result list would trade one unusable output
    // for another.
    if (verbose && it.x64 && *it.x64) {
        std::cout << "\n  x64base mapping:\n";
        print_wrapped(it.x64, "    ", 76);
    }

    if (verbose) std::cout << "\n";
}
} // namespace

void show_sql_help(const std::string& arg) {
    std::string term = to_upper(arg);

    if (term.empty()) {
        std::cout << "SQL REFERENCE (SQLite + MSSQL)\n\n"
                  // A reader who types HELP SQL in THIS engine wants this
                  // engine's SELECT first. The catalog below is portable
                  // reference material and executes nothing here.
                  << "This engine's own SELECT is SQLSEL -- typed, set-oriented,\n"
                  << "over open x64base work areas:\n\n"
                  << "  SQLSEL * FROM STUDENTS WHERE GPA > 3\n"
                  << "  SQL SQLSEL                 -> the full SQLSEL grammar\n\n"
                  << "The catalog below is a portable SQLite/MSSQL reference. It\n"
                  << "documents those dialects; it does not run here.\n\n"
                  << "Common commands for database work (grouped)\n\n";

        std::map<std::string, std::vector<const sqlref::Item*>> grouped;
        for (const auto& item : sqlref::catalog()) {
            std::string cat = item.category ? item.category : "Uncategorized";
            grouped[cat].push_back(&item);
        }

        for (const auto& [cat, items] : grouped) {
            std::cout << "=== " << cat << " ===\n";
            for (const auto* it : items) {
                std::cout << std::left << std::setw(28) << it->name << it->summary << "\n";
            }
            std::cout << "\n";
        }

        std::cout << "Usage:\n"
                  << "  SQL                        -> this grouped list\n"
                  << "  SQL INDEXING               -> only indexing commands\n"
                  << "  SQL CREATE-INDEX           -> show details\n"
                  << "  SQL LIST-CATEGORIES        -> show category names\n"
                  << "  SQL SQLSEL                 -> this engine's own SELECT grammar\n"
                  << "  HELP SQL <term>            -> same as SQL <term>\n\n"
                  << "Tip: Use EXPLAIN QUERY PLAN (SQLite) or SET SHOWPLAN_ALL ON (MSSQL) to verify indexes.\n";
        return;
    }

    // SQLSEL is not in the portable catalog and must not be added to it: the
    // catalog describes SQLite and MSSQL, and SQLSEL is neither. Delegate to the
    // statement surface's own printer so this help can never drift from the
    // grammar it describes.
    if (term == "SQLSEL") {
        std::cout << "SQLSEL -- this engine's SELECT statement surface.\n\n";
        sqlsel::print_statement_usage();
        std::cout << "\nSee also: SQLSEL USAGE (same text, from the verb itself),\n"
                  << "          SQL (the reserved verb and the family boundary),\n"
                  << "          SQLITE (the bridge to an actual SQLite database).\n";
        return;
    }

    if (term == "LIST" || term == "LIST-CATEGORIES") {
        std::cout << "SQL Categories:\n\n";
        auto cats = sqlref::categories();
        for (const auto& cat : cats) {
            std::cout << "  " << cat << "\n";
        }
        std::cout << "\nExample: HELP SQL INDEXING\n";
        return;
    }

    // Group filter (e.g. HELP SQL INDEXING)
    bool is_group = false;
    std::string group_upper = term;
    for (const auto& item : sqlref::catalog()) {
        if (item.category && to_upper(item.category).find(group_upper) != std::string::npos) {
            if (!is_group) {
                std::cout << "=== " << item.category << " ===\n\n";
                is_group = true;
            }
            std::cout << std::left << std::setw(28) << item.name << item.summary << "\n";
            if (!item.portable) {
                std::cout << "  (SQLite/MSSQL differences apply)\n";
            }
        }
    }
    if (is_group) return;

    // Exact match
    if (const auto* item = sqlref::find(term)) {
        print_item(*item, true);
        return;
    }

    // Partial / contains search
    auto matches = sqlref::search(term);
    if (!matches.empty()) {
        std::cout << "Matching SQL helpers:\n\n";
        for (const auto* m : matches) {
            print_item(*m, false);
            std::cout << "\n";
        }
        return;
    }

    std::cout << "No match for: " << term << "\n"
              << "Try: SQL, HELP SQL LIST-CATEGORIES, or HELP SQL <category>\n";
}

// ────────────────────────────────────────────────
// Command handler + optional registration
// ────────────────────────────────────────────────

// IMPORTANT: Do NOT define cmd_SQL here; cmd_sql.cpp already defines it.
void cmd_SQLHELP(xbase::DbArea& /*area*/, std::istringstream& iss) {
    std::string args;
    std::getline(iss >> std::ws, args);
    if (sqlhelp_usage_request(args)) {
        print_sqlhelp_usage();
        return;
    }
    show_sql_help(args);
}

#if DT_HAVE_DLI_REGISTRY
// Register only SQLHELP to avoid LNK2005 with cmd_sql.obj.
static bool s_sqlhelp_reg = []() {
    dli::registry().add("SQLHELP", &cmd_SQLHELP);
    return true;
}();
#endif
