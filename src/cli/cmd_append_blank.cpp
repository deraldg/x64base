// src/cli/cmd_append_blank.cpp — APPEND BLANK
//
// Delegates to shared append support so APPEND and APPEND BLANK stay aligned.

// @dottalk.usage v1
// owner: DOT|APPEND_BLANK
// command: APPEND_BLANK
// category: data
// status: supported
// noargs: mutate
// effect: mutate
// mutates: table-data index memo record-pointer
// usage-access: APPEND_BLANK USAGE
// summary:
//   Append one blank record using the shared append support path so APPEND
//   and APPEND BLANK behavior stay aligned.
//
// usage:
//   APPEND_BLANK USAGE
//   APPEND_BLANK
//   APPEND BLANK
//
// notes:
//   APPEND_BLANK with no arguments appends one blank record.
//   APPEND BLANK is the friendly command spelling when routed by the dispatcher.
//   The implementation delegates to dottalk_append_blank_core.
//   APPEND_BLANK is a table-data mutation command; do not classify it as read-only.
//
// risk:
//   writes_dbf_records: yes
//   appends_records: yes
//   updates_indexes: shared append support path
//   requires_open_table: yes
//
// related:
//   APPEND
//   REPLACE
//   TABLE
//   COMMIT
//

#include <sstream>
#include <string>
#include <cctype>

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "cli/append_support.hpp"


namespace {
static std::string append_blank_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static std::string append_blank_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static bool is_append_blank_usage_request(std::string raw)
{
    std::string t = append_blank_upper(append_blank_trim(std::move(raw)));
    if (t.rfind("APPEND_BLANK ", 0) == 0) t = append_blank_trim(t.substr(13));
    if (t.rfind("APPEND BLANK ", 0) == 0) t = append_blank_trim(t.substr(13));
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_append_blank_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalUsageTitle);
    cli::cmdout::print_line("  APPEND_BLANK USAGE");
    cli::cmdout::print_line("  APPEND_BLANK");
    cli::cmdout::print_line("  APPEND BLANK");
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalNotesTitle);
    cli::cmdout::print_line(
        "  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AppendBlankUsageSharedNote));
}
} // namespace

void cmd_APPEND_BLANK(xbase::DbArea& A, std::istringstream& iss)
{
    const std::string raw_args = iss.str();
    if (is_append_blank_usage_request(raw_args)) {
        print_append_blank_usage();
        return;
    }

    (void)dottalk_append_blank_core(A, iss);
}
