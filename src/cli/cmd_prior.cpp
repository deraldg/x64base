// src/cli/cmd_prior.cpp
// PRIOR = previous visible record in current logical view
// (active order + filter visibility).

// @dottalk.usage v1
// owner: DOT|PRIOR
// command: PRIOR
// category: navigation
// status: supported
// noargs: navigate
// effect: navigate
// mutates: cursor
// usage-access: PRIOR USAGE
// summary:
//   Move to the previous visible record in the current logical view.
//
// usage:
//   PRIOR
//   PRIOR USAGE
//
// notes:
//   PRIOR with no arguments moves to the previous visible record.
//   Active order and filter visibility are honored through logical_nav.
//   PRIOR USAGE prints usage before open-table checks or cursor movement.
//
// risk:
//   mutates_cursor: yes except usage
//   mutates_table_data: no
//   requires_open_table: yes except usage
//
// related:
//   NEXT
//   TOP
//   BOTTOM
//

#include <sstream>
#include <cstdint>
#include <cctype>
#include <string>

#include "cli/command_output.hpp"
#include "xbase.hpp"
#include "cli/logical_nav.hpp"
#include "cli/settings.hpp"
#include "help/helpdata_messages.hpp"

static std::string prior_upper(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static bool prior_usage_request(std::istringstream& in)
{
    std::string tok;
    if (!(in >> tok)) {
        in.clear();
        in.seekg(0);
        return false;
    }
    const std::string u = prior_upper(tok);
    if (u == "USAGE" || u == "HELP" || u == "?") {
        return true;
    }
    in.clear();
    in.seekg(0);
    return false;
}

static void print_prior_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::PriorUsageText);
}

void cmd_PRIOR(xbase::DbArea& A, std::istringstream& in)
{
    if (prior_usage_request(in)) {
        print_prior_usage();
        return;
    }
    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message("PRIOR", dottalk::helpdata::MessageId::NavNoFileOpenText);
        return;
    }

    const int32_t rn = cli::logical_nav::prev_recno(A, A.recno());
    if (rn <= 0) {
        cli::cmdout::print_prefixed_message("PRIOR", dottalk::helpdata::MessageId::NavAtTopText);
        return;
    }

    if (!A.gotoRec(rn) || !A.readCurrent()) {
        cli::cmdout::print_prefixed_message("PRIOR", dottalk::helpdata::MessageId::NavFailedText);
        return;
    }

    if (cli::Settings::instance().talk_on.load()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::NavRecnoLine,
            {{"recno", std::to_string(A.recno())}});
    }
}
