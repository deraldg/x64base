// @dottalk.usage v1
// owner: DOT|VAR
// command: VAR
// category: scripting
// status: supported
// noargs: usage
// effect: parse
// mutates: none-currently
// usage-access: VAR USAGE
// summary:
//   Validate and accept DotScript variable assignment syntax.
//
// usage:
//   VAR USAGE
//   VAR <name> = <expression>
//
// examples:
//   VAR threshold = 3.0
//   VAR label = UPPER(LNAME)
//   VAR today = DATE()
//
// notes:
//   VAR with no arguments prints usage.
//   VAR USAGE prints usage and does not validate/accept an assignment.
//   Current implementation validates the variable name and expression presence,
//   then reports the accepted assignment.
//
// risk:
//   mutates_table_data: no
//
// related:
//   DOTSCRIPT
//   CALC
//

#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "dotscript_var_name.hpp"
#include <algorithm>
#include <cctype>

using dottalk::dotscript::VarNameCheck;
using dottalk::dotscript::validate_var_name;


static std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static void print_var_usage() {
    std::cout
        << "Usage:\n"
        << "  VAR USAGE\n"
        << "  VAR <name> = <expression>\n"
        << "Examples:\n"
        << "  VAR threshold = 3.0\n"
        << "  VAR label = UPPER(LNAME)\n"
        << "  VAR today = DATE()\n";
}

static std::string ltrim_copy(std::string s) {
    std::size_t i = 0;
    while (i < s.size() && static_cast<unsigned char>(s[i]) <= ' ') {
        ++i;
    }
    return s.substr(i);
}

void cmd_VAR(xbase::DbArea& current, std::istringstream& iss) {
    (void)current;

    std::string var_name;
    if (!(iss >> var_name)) {
        print_var_usage();
        return;
    }

    const std::string varU = upper_copy(var_name);
    if (varU == "USAGE" || varU == "HELP" || varU == "?") {
        print_var_usage();
        return;
    }

    const VarNameCheck check = validate_var_name(var_name);
    if (!check.ok) {
        std::cout << check.message << "\n";
        return;
    }

    std::string eq;
    if (!(iss >> eq) || eq != "=") {
        print_var_usage();
        return;
    }

    std::string expr;
    std::getline(iss, expr);
    expr = ltrim_copy(expr);
    if (expr.empty()) {
        print_var_usage();
        return;
    }

    // TODO: replace with your real variable storage/evaluation path.
    std::cout << "VAR accepted: name='" << var_name << "' expr='" << expr << "'\n";
}
