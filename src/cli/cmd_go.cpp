// src/cli/cmd_go.cpp
// FoxPro-style GO router.
//
// Supported forms:
//   GO
//   GO TOP | BOTTOM | FIRST | LAST
//   GO [TO] <recno>
//   GO RECORD <recno>
//   GO +/-<n>

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
