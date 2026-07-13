// @dottalk.usage v1
// owner: DOT|CONCAT
// command: CONCAT
// aliases: STRCAT
// category: string
// status: supported
// noargs: usage
// effect: output
// mutates: none
// usage-access: CONCAT USAGE
// summary:
//   Concatenate one or more expressions into a single string and print the result.
//
// usage:
//   CONCAT USAGE
//   CONCAT <expr1>[, <expr2> ...]
//   STRCAT <expr1>[, <expr2> ...]
//
// examples:
//   CONCAT "hello", " ", "world"
//   CONCAT FNAME, " ", LNAME
//   STRCAT("A", "B", "C")
//
// notes:
//   CONCAT accepts between 1 and 32 arguments.
//   Bare identifiers resolve through the expression engine:
//   fields read from the current table when open; otherwise they remain plain text.
//   Parenthesized call form is also accepted for command-line convenience.
//
// related:
//   CALC
//   REPLACE
//   MULTIREP
//

#include "shell_commands.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

#include "cli/expr/value_eval.hpp"

namespace {

std::string trim_copy(std::string s) {
    auto not_space = [](unsigned char ch) { return !std::isspace(ch); };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
}

std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

void print_concat_usage() {
    std::cout
        << "Usage:\n"
        << "  CONCAT USAGE\n"
        << "  CONCAT <expr1>[, <expr2> ...]\n"
        << "  STRCAT <expr1>[, <expr2> ...]\n"
        << "Examples:\n"
        << "  CONCAT \"hello\", \" \", \"world\"\n"
        << "  CONCAT FNAME, \" \", LNAME\n"
        << "  STRCAT(\"A\", \"B\", \"C\")\n"
        << "Notes:\n"
        << "  - CONCAT accepts between 1 and 32 arguments.\n"
        << "  - Bare identifiers resolve as fields when a table is open; otherwise they remain literal text.\n";
}

} // namespace

void cmd_CONCAT(xbase::DbArea& area, std::istringstream& iss) {
    std::string raw;
    std::getline(iss, raw);
    raw = trim_copy(raw);

    if (raw.empty()) {
        print_concat_usage();
        return;
    }

    const std::string raw_upper = upper_copy(raw);
    if (raw_upper == "USAGE" || raw_upper == "HELP" || raw_upper == "?") {
        print_concat_usage();
        return;
    }

    const std::string expr =
        (!raw.empty() && raw.front() == '(') ? ("CONCAT" + raw) : ("CONCAT(" + raw + ")");

    std::string out;
    if (!dottalk::expr::eval_string_value_expr(area, expr, out)) {
        std::cout << "CONCAT: unable to evaluate arguments.\n";
        return;
    }

    std::cout << out << "\n";
}
