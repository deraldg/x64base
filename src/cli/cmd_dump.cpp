// src/cli/cmd_dump.cpp
// DotTalk++ — DUMP
// Legacy, path-blind record dumper.
// Operates ONLY on the current work area.
// No path resolution, no file opens, no side effects.

// @dottalk.usage v1
// owner: DOT|DUMP
// command: DUMP
// category: report
// status: supported
// noargs: report
// effect: report
// mutates: cursor
// usage-access: DUMP USAGE
// summary:
//   Dump every record from the current work area in legacy pipe-delimited form.
//
// usage:
//   DUMP
//   DUMP USAGE
//
// notes:
//   DUMP requires an open table except for DUMP USAGE.
//   DUMP operates only on the current work area.
//   DUMP does not resolve paths and does not open files.
//   Deleted records are prefixed with an asterisk marker.
//   DUMP iterates by record number and reads each record.
//   DUMP is read-only for table data but moves the current cursor during output.
//
// risk:
//   reads_table_records: yes
//   mutates_table_data: no
//   cursor_movement: yes
//   opens_files: no
//
// related:
//   LIST
//   DISPLAY
//   BROWSE
//   COUNT
//

#include "xbase.hpp"
#include <iostream>
#include <cctype>
#include <sstream>
#include <string>
#include <cstdint>
#include <limits>

using namespace xbase;


namespace {
static std::string dump_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string dump_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_dump_usage_request(const std::string& raw)
{
    std::string t = dump_upper(dump_trim(raw));

    // Some dispatch paths pass the whole raw line ("DUMP USAGE")
    // instead of only the command tail ("USAGE"). Accept both.
    if (t.rfind("DUMP ", 0) == 0) {
        t = dump_upper(dump_trim(t.substr(5)));
    }

    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_dump_usage()
{
    std::cout
        << "Usage:\n"
        << "  DUMP\n"
        << "  DUMP USAGE\n"
        << "Notes:\n"
        << "  - Dumps all records from the current work area.\n"
        << "  - Deleted records are prefixed with an asterisk marker.\n"
        << "  - DUMP is read-only for table data but moves through records while printing.\n";
}
} // namespace

void cmd_DUMP(DbArea& a, std::istringstream& args)
{
    const std::string raw_args = args.str();
    if (is_dump_usage_request(raw_args)) {
        print_dump_usage();
        return;
    }

    // Must have an open table
    if (!a.isOpen()) {
        std::cout << "No table open.\n";
        return;
    }

    const auto& fields = a.fields();
    const size_t nrecs = a.recCount();

	// DbArea::gotoRec() is 32-bit in this codebase. Guard the cast.
	if (nrecs > static_cast<size_t>(std::numeric_limits<std::int32_t>::max())) {
	    std::cout << "DUMP: record count too large for 32-bit recno (" << nrecs << ").\n";
	    return;
	}

	// Record-number–based iteration (DbArea has no eof())
	for (std::int32_t r = 1; r <= static_cast<std::int32_t>(nrecs); ++r) {
	    a.gotoRec(r);
        a.readCurrent();   // loads internal record buffer

        // Deleted marker (legacy style)
        if (a.isDeleted())
            std::cout << "* ";
        else
            std::cout << "  ";

        // Dump fields, pipe-delimited
        for (size_t i = 0; i < fields.size(); ++i) {
            std::string val;
            try {
                // DbArea uses 1-based field indexing
                val = a.get((int)i + 1);
            } catch (...) {
                val.clear();
            }

            std::cout << val;
            if (i + 1 < fields.size())
                std::cout << " | ";
        }

        std::cout << "\n";
    }
}
