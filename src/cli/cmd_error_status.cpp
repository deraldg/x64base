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

#include <iostream>
#include <sstream>
#include <iomanip>

#include "xbase.hpp"
#include "xbase_error_codes.hpp"
#include "xbase_error_runtime.hpp"
#include "xbase_error_context.hpp"

using namespace xbase::error;

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
        // FALLBACK
        // -------------------------
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
    (void)in;

    code c = get_last_error();

    std::cout << "Last Error:\n";

    std::cout << "  Severity : " << to_severity_string(c.get_severity()) << "\n";
    std::cout << "  Facility : " << to_facility_string(c.get_facility())
              << " (0x" << std::hex << static_cast<uint16_t>(c.get_facility()) << std::dec << ")\n";
    std::cout << "  Number   : " << c.get_number() << "\n";

    std::cout << "  HRESULT  : 0x"
              << std::hex << std::uppercase << std::setw(8) << std::setfill('0')
              << c.value << std::dec << "\n";

    std::cout << "  Message  : " << error_to_string(c) << "\n";
}