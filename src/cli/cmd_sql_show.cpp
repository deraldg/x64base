// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported


// src/cli/cmd_sql_show.cpp
// SHOW family: SHOW TABLE | SHOW COLUMNS | SHOW INDEX
//
// - SHOW TABLE   : one-screen summary of current work area
// - SHOW COLUMNS : column layout (similar to FIELDS/STRUCT but compact)
// - SHOW INDEX   : order/index summary (graceful on non-order builds)

// @dottalk.usage v1
// owner: DOT|SHOW
// command: SHOW
// category: diagnostics
// status: supported
// noargs: report
// effect: report
// mutates: cursor-temporary
// usage-access: SHOW USAGE
// summary:
//   Show table, column, or active order/index information for the current work
//   area.
//
// usage:
//   SHOW
//   SHOW USAGE
//   SHOW COLUMNS
//   SHOW TABLE
//   SHOW INDEX
//
// examples:
//   SHOW
//   SHOW COLUMNS
//   SHOW TABLE
//   SHOW INDEX
//
// notes:
//   SHOW with no arguments displays columns.
//   SHOW TABLE scans records to count deleted rows and restores cursor best-effort.
//   SHOW INDEX reports physical/order/tag state when available.
//   SHOW USAGE prints usage before open-table checks or cursor movement.
//
// risk:
//   reads_current_area: yes except usage
//   mutates_cursor: SHOW TABLE temporarily, restored best-effort
//   mutates_table_data: no
//
// related:
//   STRUCT
//   DISPLAY
//   SET ORDER
//

#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <iomanip>
#include <filesystem>

#include "xbase.hpp"
#include "xbase_field_getters.hpp"
#include "textio.hpp"
#include "cli/order_state.hpp"
#include "filters/filter_registry.hpp"

using xbase::DbArea;
namespace fs = std::filesystem;


static void print_show_usage()
{
    std::cout
        << "Usage:\n"
        << "  SHOW\n"
        << "  SHOW USAGE\n"
        << "  SHOW COLUMNS\n"
        << "  SHOW TABLE\n"
        << "  SHOW INDEX\n"
        << "Examples:\n"
        << "  SHOW COLUMNS\n"
        << "  SHOW TABLE\n"
        << "  SHOW INDEX\n";
}

static inline std::string basename_only(std::string p) {
    // normalize slashes and pull basename
    for (auto &c : p) if (c == '\\') c = '/';
    auto pos = p.find_last_of('/');
    if (pos != std::string::npos) p.erase(0, pos + 1);
    return p;
}

static void show_table(DbArea& A)
{
    if (!A.isOpen()) { std::cout << "No file open\n"; return; }

    // THE AREA KNOWS ITS OWN PATH. ASK IT.
    //
    // This line used to read A.name() and hand it to fs::absolute(). name() is
    // the LOGICAL ALIAS -- "STUDENTS" -- not a path, and fs::absolute resolves
    // a bare token against the PROCESS CWD, which is the DATA root. So SHOW
    // TABLE printed
    //     Path : ...\dottalkpp\data\STUDENTS
    // for a table living at ...\data\dbf\x64\STUDENTS.dbf -- the
    // subdirectory and the extension both gone. Measured 2026-08-30. That is
    // worse than printing nothing: the output is well formed, plausible, and
    // names a file that does not exist, so a reader who copies it gets a
    // "not found" from somewhere else entirely.
    //
    // THIS EXACT DEFECT WAS FOUND AND FIXED ONCE ALREADY, at a different site.
    // cmd_workspace.cpp's notes on `TO <root>`: "resolves like every other
    // path token (paths::resolve_in_slot) ... Corrected 2026-08-12; it
    // previously followed the process CWD while SET PATH followed DATA."
    // Same mistake, same cause, fifteen days apart, in a file nobody thought
    // to check when the first one was fixed.
    //
    // No resolver is needed here and using one would be the same error in a
    // politer form. DbArea CARRIES the absolute path it opened
    // (_dbf_abs_path, set in dbarea.cpp on open and cleared on close) and
    // hands it over as filename(). The AREA command has always done this --
    // cmd_area.cpp reads A.filename() and prints "(unknown)" when it is empty,
    // rather than reconstructing -- and this now matches it.
    //
    // The Table: line below deliberately keeps A.name(): that line reports the
    // ALIAS, which is what name() is for. Two lines, two different questions,
    // two different accessors.
    const std::string& abs = A.filename();
    const std::string path = abs.empty() ? std::string("(unknown)") : abs;

    // Deleted count (quick scan, position-preserving)
    int64_t deleted = 0;
    long save_rec = A.recno();
    bool have = false;
    try {
        if (A.top() && A.readCurrent()) {
            do {
                if (A.isDeleted()) ++deleted;
            } while (A.skip(+1) && A.readCurrent());
        }
        have = true;
    } catch (...) {
        // ignore
    }
    // restore position if we moved
    if (have) {
        try { if (save_rec > 0) { A.gotoRec(save_rec); A.readCurrent(); } } catch (...) {}
    }

    std::cout << "Table: " << basename_only(A.name()) << "\n";
    std::cout << "Path : "  << path << "\n";

    // We don't have the engine here to print Area #; RECNO/RECS is enough.
    std::cout << "Recs : " << A.recCount()
              << "   Recno: " << A.recno() << "\n";
    std::cout << "Del  : " << deleted << "\n";

    try {
        if (!orderstate::hasOrder(A)) {
            std::cout << "Order: PHYSICAL\n";
            std::cout << "Index: (none)\n";
            std::cout << "Tag  : (none)\n";
        } else {
            const bool asc = orderstate::isAscending(A);
            const std::string idx = orderstate::orderName(A);
            const std::string tag = orderstate::activeTag(A);
            // AIF-148 residue.  The gate above is hasOrder() and is RIGHT --
            // it asks IS A CONTAINER ATTACHED, and an attached container has
            // an Index and Tag line worth printing.  What was wrong is that
            // reaching this branch was then treated as proof that an order
            // was IN FORCE, so a .cdx attached with no tag selected printed
            // ASCEND while TOP, BOTTOM and SKIP traversed the table
            // physically.  The gate stays; the order WORD moves.
            //
            // PHYSICAL, not NATURAL, because that is the word this function
            // already uses three lines up for the unattached case.  Each site
            // keeps its own vocabulary and only the predicate moves.
            std::cout << "Order: " << (orderstate::isNaturalOrder(A)
                                           ? "PHYSICAL"
                                           : (asc ? "ASCEND" : "DESCEND")) << "\n";
            std::cout << "Index: " << (idx.empty() ? std::string("(unknown)") : idx) << "\n";
            std::cout << "Tag  : " << (tag.empty() ? std::string("(none)") : tag) << "\n";
        }
    } catch (...) {
        std::cout << "Order: (unavailable)\n";
        std::cout << "Index: (unavailable)\n";
        std::cout << "Tag  : (unavailable)\n";
    }

    // SHOW TABLE must report the same active filter state used by COUNT/LIST.
    try {
        std::cout << "Filter: " << (filter::has_active_filter(&A) ? "ON" : "OFF") << "\n";
    } catch (...) {
        std::cout << "Filter: (unavailable)\n";
    }
}

static void show_columns(DbArea& A)
{
    if (!A.isOpen()) { std::cout << "No file open\n"; return; }

    const int n = (int)A.fields().size();
    std::cout << "Field  " << std::left << std::setw(14) << "Name"
              << "Type " << "Len " << "Dec" << "\n";

    for (int i = 0; i < n; ++i) {
        const auto& f = A.fields()[size_t(i)];
        std::cout << std::right << std::setw(5) << (i+1) << "  "
                  << std::left  << std::setw(14) << f.name
                  << f.type << "    "
                  << std::right << std::setw(0) << f.length << "   "
                  << f.decimals << "\n";
    }
}

static void show_index(DbArea& A)
{
    std::cout << "INDEX INFO:\n";
    try {
        if (!A.isOpen()) { std::cout << "  (No file open)\n"; return; }
        if (!orderstate::hasOrder(A)) {
            std::cout << "  Order      : PHYSICAL\n";
            std::cout << "  Index file : (none)\n";
            std::cout << "  Active tag : (none)\n";
            return;
        }
        const bool asc = orderstate::isAscending(A);
        const std::string idx = orderstate::orderName(A);
        const std::string tag = orderstate::activeTag(A);
        // AIF-148 residue, the same shape as show_table() above and worth
        // fixing in both rather than factoring: SHOW INDEX is the command a
        // person runs to ASK what order is in force, so it is the worst place
        // in the file to answer with the direction flag.  Under a .cdx with
        // no tag it said `Order: ASCEND` beside `Active tag : (none)` -- the
        // report holding both halves of its own contradiction.
        std::cout << "  Order      : " << (orderstate::isNaturalOrder(A)
                                               ? "PHYSICAL"
                                               : (asc ? "ASCEND" : "DESCEND")) << "\n";
        std::cout << "  Index file : " << (idx.empty() ? std::string("(unknown)") : idx) << "\n";
        std::cout << "  Active tag : " << (tag.empty() ? std::string("(none)") : tag) << "\n";
    } catch (...) {
        std::cout << "  (Order API not wired in this build target)\n";
    }
}

void cmd_SQL_SHOW(DbArea& A, std::istringstream& S)
{
    std::string what;
    std::getline(S, what);
    what = textio::trim(what);
    const std::string U = textio::up(what);

    if (U == "USAGE" || U == "HELP" || U == "?") { print_show_usage(); return; }

    if (U == "TABLE") { show_table(A); return; }
    if (U == "COLUMNS" || U.empty()) { show_columns(A); return; }
    if (U == "INDEX") { show_index(A); return; }

    print_show_usage();
}



