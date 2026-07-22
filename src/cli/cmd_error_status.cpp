// src/cli/cmd_ERROR_STATUS.cpp
// Display the last xBase_64 error in a structured, MS-conformal format.

// @dottalk.usage v1
// owner: DOT|ERROR_STATUS
// command: ERROR_STATUS
// category: diagnostics
// status: supported
// noargs: report
// effect: report
// mutates: output-format-state
// usage-access: ERROR_STATUS USAGE
// summary:
//   Display the last xBase_64 error in a structured, HRESULT-style diagnostic format.
//
// usage:
//   ERROR_STATUS
//   ERROR_STATUS USAGE
//
// notes:
//   ERROR_STATUS with no arguments reports the last error.
//   ERROR_STATUS prints severity, facility, number, HRESULT, and message.
//   ERROR_STATUS changes stream formatting while printing diagnostic output.
//   ERROR_STATUS does not mutate table data.
//
// risk:
//   reads_error_state: yes
//   mutates_output_format_state: yes
//   mutates_table_data: no
//
// related:
//   ERROR_CLEAR
//   ERROR_TEST
//

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <sstream>
#include <iomanip>
#include <string>

#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
#include "xbase.hpp"
#include "xbase_error_codes.hpp"
#include "xbase_error_runtime.hpp"
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

std::string facility_hex(code c)
{
    std::ostringstream oss;
    oss << "0x" << std::hex << static_cast<uint16_t>(c.get_facility());
    return oss.str();
}

std::string hresult_hex(code c)
{
    char buf[11] = {};
    std::snprintf(buf, sizeof(buf), "0x%08X", static_cast<unsigned int>(c.value));
    return std::string(buf);
}

} // namespace

// -----------------------------------------------------------------------------
// Corrected to_string() implementation
// -----------------------------------------------------------------------------
inline std::string error_to_string(code c)
{
    // Explicit success handling
    if (c.value == ok().value)
        return "OK";

    switch (c.value)
    {
        // -------------------------
        // GENERAL
        // -------------------------
        case e_unknown().value:
            return "Unknown error";

        case e_invalid_argument().value:
            return "Invalid argument";

        case e_not_implemented().value:
            return "Not implemented";

        // -------------------------
        // DBF64
        // -------------------------
        case e_dbf_header_invalid().value:
            return "DBF_64 header invalid";

        case e_dbf_record_out_of_range().value:
            return "DBF_64 record out of range";

        // -------------------------
        // FPT64
        // -------------------------
        case e_fpt_block_invalid().value:
            return "FPT64 block invalid";

        // -------------------------
        // SECURITY
        // -------------------------
        case e_security_policy_violation().value:
            return "Security policy violation";

        case e_security_elevated_write_forbidden().value:
            return "Security: elevated write forbidden";

        // -------------------------
        // CLI
        // -------------------------
        case e_cli_parse_error().value:
            return "CLI parse error";

        // -------------------------
        // IO
        // -------------------------
        case e_io_write_failed().value:
            return "I/O write failed.";

        // -------------------------
        // FALLBACK
        // -------------------------
        // NOTE: this local map is a partial copy of xbase::error::to_string() and
        // is missing several CLI codes; collapse it into the header mapper in a
        // dedicated follow-up patch (out of scope for the EXPORTFUNCTIONS slice).
        default:
        {
            std::string msg = "Unknown or unmapped xBase_64 error code (";
            msg += to_severity_string(c.get_severity());
            msg += ", facility=";
            msg += to_facility_string(c.get_facility());
            msg += ", number=";
            msg += std::to_string(c.get_number());
            msg += ")";
            return msg;
        }
    }
}

// -----------------------------------------------------------------------------
// CLI Command: ERROR_STATUS
// -----------------------------------------------------------------------------
void cmd_ERROR_STATUS(xbase::DbArea& A, std::istringstream& in)
{
    (void)A;

    if (is_usage_request(in)) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::ErrorStatusUsageText);
        return;
    }

    code c = get_last_error();

    cli::cmdout::print_message(dottalk::helpdata::MessageId::ErrorStatusHeaderText);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ErrorStatusSeverityLineText,
        {{"value", to_severity_string(c.get_severity())}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ErrorStatusFacilityLineText,
        {{"value", to_facility_string(c.get_facility())}, {"hex", facility_hex(c)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ErrorStatusNumberLineText,
        {{"value", std::to_string(c.get_number())}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ErrorStatusHresultLineText,
        {{"value", hresult_hex(c)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ErrorStatusMessageLineText,
        {{"value", error_to_string(c)}});
}
