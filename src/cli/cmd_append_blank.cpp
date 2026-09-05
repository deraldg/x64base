// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_append_blank.cpp -- APPEND BLANK
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
//   APPEND BLANK is rewritten to APPEND_BLANK by cli::preprocess_for_dispatch in
//     src/cli/shell_api_extras.cpp, which is the only thing that makes the
//     two-word spelling work. UNTIL 2026-09-05 THIS LINE READ "the friendly
//     command spelling when routed by the dispatcher" AND NOTHING ROUTED IT:
//     the claim was conditional, the condition was false, and a reader who
//     checked here before typing the command got a wrong answer from the most
//     authoritative-looking place available. Name the mechanism, or do not
//     make the claim.
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
    cli::cmdout::print_message(dottalk::helpdata::MessageId::AppendBlankUsageText);
}
} // namespace

void cmd_APPEND_BLANK(xbase::DbArea& A, std::istringstream& iss)
{
    const std::string raw_args = iss.str();
    if (is_append_blank_usage_request(raw_args)) {
        print_append_blank_usage();
        return;
    }

    // AN UNRECOGNIZED TRAILING WORD IS REFUSED, NOT IGNORED.
    //
    // Credit where it is due: this arm exists because a second reviewer
    // (Grok, reviewing the public snapshot on 2026-09-05) specified
    // "extra words after BLANK still print usage", and the version of this
    // repair that did not have it was measured and found wanting --
    // dottalk_append_blank_core takes its istringstream UNNAMED and reads
    // nothing from it, so `APPEND BLANK GARBAGE` would have appended a record
    // and dropped GARBAGE without a word.
    //
    // That is the SAME DEFECT SHAPE this whole file is being repaired for:
    // BLANK itself was a word cmd_APPEND did not recognize, and the cost of
    // ignoring it quietly was a silently empty table. A repair that fixes one
    // silently-swallowed token by introducing another has not learned anything.
    std::string extra;
    if (iss >> extra) {
        print_append_blank_usage();
        return;
    }

    (void)dottalk_append_blank_core(A, iss);
}
