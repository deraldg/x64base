// src/cli/cmd_go.cpp
// FoxPro-style GO router.
//
// Supported forms:
//   GO
//   GO TOP | BOTTOM | FIRST | LAST
//   GO [TO] <recno>
//   GO RECORD <recno>
//   GO +/-<n>

// @dottalk.usage v1
// owner: DOT|GO
// command: GO
// category: navigation
// status: supported
// noargs: navigate
// effect: navigate
// mutates: cursor
// usage-access: GO USAGE
// summary:
//   Refresh the current record, move to table/order endpoints, move to an
//   absolute record number, or skip relative to the current record.
//
// usage:
//   GO
//   GO USAGE
//   GO TOP
//   GO BOTTOM
//   GO FIRST
//   GO LAST
//   GO TO <recno>
//   GO RECORD <recno>
//   GO <recno>
//   GO +<n>
//   GO -<n>
//
// notes:
//   GO with no arguments refreshes/re-reads the current record through the navigation layer.
//   GO TOP/BOTTOM/FIRST/LAST move to logical endpoints.
//   GO <recno>, GO TO <recno>, and GO RECORD <recno> navigate absolutely.
//   GO +/-<n> delegates to relative skip.
//   GO USAGE prints usage before navigation.
//
// risk:
//   mutates_cursor: yes except usage
//   mutates_table_data: no
//
// related:
//   GOTO
//   TOP
//   BOTTOM
//   SKIP
//

#include <sstream>
#include <string>

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "cli/nav_move.hpp"
#include "help/helpdata_messages.hpp"

namespace {

void print_go_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GoUsageText);
}

} // namespace

void cmd_GO(xbase::DbArea& A, std::istringstream& in)
{
    std::string tok;
    if (!(in >> tok)) {
        // Placeholder for relationship refresh; for now, just re-read current.
        cli::nav::refresh_current(A, "GO");
        return;
    }

    const std::string u = cli::nav::upper_copy(tok);

    if (u == "USAGE" || u == "HELP" || u == "?") {
        print_go_usage();
        return;
    }

    if (u == "TOP") {
        cli::nav::go_endpoint(A, cli::nav::Endpoint::Top, "GO");
        return;
    }
    if (u == "BOTTOM") {
        cli::nav::go_endpoint(A, cli::nav::Endpoint::Bottom, "GO");
        return;
    }
    if (u == "FIRST") {
        cli::nav::go_endpoint(A, cli::nav::Endpoint::First, "GO");
        return;
    }
    if (u == "LAST") {
        cli::nav::go_endpoint(A, cli::nav::Endpoint::Last, "GO");
        return;
    }

    if (u == "TO" || u == "RECORD") {
        std::string nTok;
        int n = 0;
        if (!(in >> nTok) || !cli::nav::try_parse_int_token(nTok, n) || n <= 0) {
            cli::cmdout::print_prefixed_message("GO", dottalk::helpdata::MessageId::GoExpectedPositiveRecordNumberText);
            cli::cmdout::show_command_syntax("GO");
            return;
        }
        cli::nav::go_absolute(A, n, "GO");
        return;
    }

    if (u == "IN") {
        cli::cmdout::print_prefixed_message("GO", dottalk::helpdata::MessageId::GoAreaQualifierNotSupportedYetText);
        return;
    }

    int n = 0;
    if (cli::nav::try_parse_int_token(tok, n)) {
        if (!tok.empty() && (tok[0] == '+' || tok[0] == '-')) {
            cli::nav::skip_relative(A, n, "GO");
        } else {
            cli::nav::go_absolute(A, n, "GO");
        }
        return;
    }

    cli::cmdout::print_prefixed_message("GO", dottalk::helpdata::MessageId::GoUnrecognizedCommandFormText);
    cli::cmdout::show_command_syntax("GO");
}
