// src/cli/cmd_sqlver.cpp
// @dottalk.usage v1
// owner: DOT|SQLVER
// command: SQLVER
// category: sql
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: SQLVER USAGE
// summary:
//   Report whether SQLite support is available and print the linked SQLite
//   library version when available.
//
// usage:
//   SQLVER
//   SQLVER USAGE
//
// notes:
//   SQLVER with no arguments reports SQLite availability/version.
//   SQLVER is read-only and does not open SQLite databases.
//
// risk:
//   mutates_table_data: no
//   opens_sqlite_db: no
//
// related:
//   SQLITE
//

#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
#include "xbase.hpp"


namespace {
static std::string sqlver_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string sqlver_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_sqlver_usage_request(const std::string& raw)
{
    std::string t = sqlver_upper(sqlver_trim(raw));
    if (t.rfind("SQLVER ", 0) == 0) {
        t = sqlver_upper(sqlver_trim(t.substr(7)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_sqlver_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::SqlverUsageText);
}
} // namespace

#if DOTTALK_SQLITE_AVAILABLE
  #include <sqlite3.h>
#endif

// Shell entry point: SQLVER
// Usage: . SQLVER
void cmd_SQLVER(xbase::DbArea& /*area*/, std::istringstream& is)
{
    const std::string raw_args = is.str();
    if (is_sqlver_usage_request(raw_args)) {
        print_sqlver_usage();
        return;
    }

#if DOTTALK_SQLITE_AVAILABLE
    const char* ver = sqlite3_libversion();
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SqlverAvailableLineText,
        {{"version", ver ? ver : "unknown"}});
#else
    cli::cmdout::print_message(dottalk::helpdata::MessageId::SqlverUnavailableLineText);
#endif
}
