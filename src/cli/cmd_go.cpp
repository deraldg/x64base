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
#include "cli/nav_move.hpp"
#include "cli/command_catalog.hpp"
#include "cli/message_catalog.hpp"
#include "cli/output_router.hpp"

namespace {

void print_line(const std::string& s)
{
    auto& out = cli::OutputRouter::instance().out();
    out << s << '\n';
}

void print_go_usage()
{
    print_line("Usage:");
    print_line("  GO");
    print_line("  GO USAGE");
    print_line("  GO TOP");
    print_line("  GO BOTTOM");
    print_line("  GO FIRST");
    print_line("  GO LAST");
    print_line("  GO TO <recno>");
    print_line("  GO RECORD <recno>");
    print_line("  GO <recno>");
    print_line("  GO +<n>");
    print_line("  GO -<n>");
}

void show_command_syntax(const std::string& cmd)
{
    const auto* doc = dottalk::doc::get(cmd);
    if (!doc) {
        return;
    }

    for (const auto& line : doc->syntax) {
        print_line(line);
    }
}

void show_prefixed_message(const std::string& cmd, const std::string& text)
{
    print_line(cmd + ": " + text);
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
            show_prefixed_message("GO", dottalk::msg::text(dottalk::msg::Code::ExpectedPositiveRecordNumber));
            show_command_syntax("GO");
            return;
        }
        cli::nav::go_absolute(A, n, "GO");
        return;
    }

    if (u == "IN") {
        show_prefixed_message("GO", dottalk::msg::text(dottalk::msg::Code::AreaQualifierNotSupportedYet));
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

    show_prefixed_message("GO", dottalk::msg::text(dottalk::msg::Code::UnrecognizedCommandForm));
    show_command_syntax("GO");
}
