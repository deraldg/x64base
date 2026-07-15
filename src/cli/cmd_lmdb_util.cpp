// File: src/cli/cmd_lmdb_util.cpp
//
// LMDB_UTIL is deprecated.
//
// The project has moved to the OO model:
//   DbArea -> IndexManager -> CdxBackend -> MDB_env*
//
// Use the per-area LMDB command instead:
//   LMDB INFO
//   LMDB OPEN <container.cdx | envdir.cdx.d | stem>
//   LMDB USE  <TAG>
//   LMDB SEEK <key>
//   LMDB DUMP [<max>]
//   LMDB SCAN <low> <high>
//   LMDB CLOSE
//
// This stub intentionally does NOT open any LMDB environments or transactions,
// to avoid cross-area contamination and reader-slot conflicts.
//
// @dottalk.usage v1
// owner: DOT|LMDB_UTIL
// command: LMDB_UTIL
// category: diagnostics
// status: deprecated
// noargs: report
// effect: report
// mutates: none
// usage-access: LMDB_UTIL USAGE
// summary:
//   Deprecated disabled LMDB utility command that points users to the per-area
//   LMDB command.
//
// usage:
//   LMDB_UTIL
//   LMDB_UTIL USAGE
//
// notes:
//   LMDB_UTIL is deprecated and disabled.
//   LMDB_UTIL intentionally does not open LMDB environments or transactions.
//   Use LMDB INFO, LMDB OPEN, LMDB USE, LMDB SEEK, LMDB DUMP, LMDB SCAN, and LMDB CLOSE instead.
//   This avoids cross-area contamination and reader-slot conflicts.
//
// risk:
//   opens_lmdb_env: no
//   reads_index_data: no
//   mutates_table_data: no
//   mutates_index_data: no
//
// related:
//   LMDB
//   LMDBDUMP
//   CDX
//

#include <sstream>
#include <string>
#include <cctype>

#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
#include "xbase.hpp"


namespace {
static std::string lmdb_util_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string lmdb_util_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_lmdb_util_usage_request(const std::string& raw)
{
    std::string t = lmdb_util_upper(lmdb_util_trim(raw));
    if (t.rfind("LMDB_UTIL ", 0) == 0) {
        t = lmdb_util_upper(lmdb_util_trim(t.substr(10)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_lmdb_util_disabled()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::LmdbUtilDisabledText);
}
} // namespace

void cmd_LMDB_UTIL(xbase::DbArea& /*a*/, std::istringstream& iss)
{
    const std::string raw_args = iss.str();
    (void)is_lmdb_util_usage_request(raw_args); // usage/help share the same disabled diagnostic.
    print_lmdb_util_disabled();
}
