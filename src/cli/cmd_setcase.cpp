// src/cli/cmd_setcase.cpp
// @dottalk.usage v1
// owner: DOT|SETCASE
// command: SETCASE
// category: settings
// status: supported
// noargs: report
// effect: configure
// mutates: case-sensitivity-setting
// usage-access: SET CASE USAGE
// summary:
//   Report or set predicate/expression case-sensitivity behavior.
//
// usage:
//   SET CASE
//   SET CASE USAGE
//   SET CASE ON
//   SET CASE OFF
//   SETCASE
//   SETCASE USAGE
//   SETCASE ON
//   SETCASE OFF
//
// notes:
//   SET CASE with no arguments reports current case sensitivity.
//   SETCASE with no arguments reports current case sensitivity.
//   ON, TRUE, and 1 enable case-sensitive predicate behavior.
//   OFF, FALSE, and 0 disable case-sensitive predicate behavior.
//
// risk:
//   mutates_session_settings: ON OFF
//   mutates_table_data: no
//
// related:
//   SET
//   SET NEAR
//   LOCATE
//   FIND
//

#include <iostream>
#include <sstream>
#include <string>

#include "predicate_eval.hpp"
#include "textio.hpp"
#include "xbase.hpp"

static void print_setcase_usage()
{
    std::cout
        << "Usage:\n"
        << "  SET CASE\n"
        << "  SET CASE USAGE\n"
        << "  SET CASE ON\n"
        << "  SET CASE OFF\n"
        << "  SETCASE\n"
        << "  SETCASE USAGE\n"
        << "  SETCASE ON\n"
        << "  SETCASE OFF\n";
}

void cmd_SETCASE(xbase::DbArea&, std::istringstream& iss) {
    std::string tok;
    if (!(iss >> tok)) {
        std::cout << (predx::get_case_sensitive()
            ? "CASE SENSITIVE: ON\n"
            : "CASE SENSITIVE: OFF\n");
        return;
    }

    if (textio::ieq(tok, "USAGE") || textio::ieq(tok, "HELP") || tok == "?") {
        print_setcase_usage();
        return;
    }

    if (textio::ieq(tok, "ON") || textio::ieq(tok, "TRUE") || textio::ieq(tok, "1")) {
        predx::set_case_sensitive(true);
        std::cout << "CASE SENSITIVE: ON\n";
        return;
    }

    if (textio::ieq(tok, "OFF") || textio::ieq(tok, "FALSE") || textio::ieq(tok, "0")) {
        predx::set_case_sensitive(false);
        std::cout << "CASE SENSITIVE: OFF\n";
        return;
    }

    print_setcase_usage();
}