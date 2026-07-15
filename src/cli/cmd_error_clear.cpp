// src/cli/cmd_ERROR_CLEAR.cpp
// Clear the last xBase_64 error and report success.

// @dottalk.usage v1
// owner: DOT|ERROR_CLEAR
// command: ERROR_CLEAR
// category: diagnostics
// status: supported
// noargs: mutate
// effect: clear
// mutates: error-state
// usage-access: ERROR_CLEAR USAGE
// summary:
//   Clear the last xBase_64 error context.
//
// usage:
//   ERROR_CLEAR
//   ERROR_CLEAR USAGE
//
// notes:
//   ERROR_CLEAR with no arguments clears the last error.
//   ERROR_CLEAR USAGE prints usage and does not clear the error state.
//   ERROR_CLEAR mutates diagnostic error state only, not table data.
//
// risk:
//   clears_error_state: yes
//   mutates_table_data: no
//
// related:
//   ERROR_STATUS
//   ERROR_TEST
//

#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>

#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
#include "xbase.hpp"
#include "xbase_error_codes.hpp"
#include "xbase_error_context.hpp"

using namespace xbase::error;

namespace {

std::string trim_copy(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

std::string upper_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

bool is_usage_request(std::istringstream& in)
{
    const std::streampos start = in.tellg();
    std::string tok;
    if (!(in >> tok)) {
        in.clear();
        if (start != std::streampos(-1)) in.seekg(start);
        return false;
    }
    in.clear();
    if (start != std::streampos(-1)) in.seekg(start);
    const std::string u = upper_copy(trim_copy(tok));
    return u == "USAGE" || u == "HELP" || u == "?";
}

} // namespace

void cmd_ERROR_CLEAR(xbase::DbArea& A, std::istringstream& in)
{
    (void)A;

    if (is_usage_request(in)) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::ErrorClearUsageText);
        return;
    }

    clear_last_error();
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ErrorClearStatusText);
}
