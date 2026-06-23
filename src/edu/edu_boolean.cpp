// src/cli/edu_boolean.cpp
// DotTalk++ BOOLEAN
//
// xexpr migration note:
//   This command now calls the xexpr facade instead of reaching directly into
//   cli/expr/api.hpp, cli/expr/ast.hpp, and cli/expr/glue_xbase.hpp.
//   The command syntax and output remain unchanged.

// @dottalk.usage v1
// owner: EDU|BOOLEAN
// command: BOOLEAN
// category: education-expression
// status: supported
// noargs: usage
// effect: evaluate-expression
// mutates: none
// usage-access: BOOLEAN USAGE
// summary:
//   Evaluate a boolean expression through xexpr and print .T. or .F.
//
// usage:
//   BOOLEAN USAGE
//   BOOLEAN <expr>
//
// examples:
//   BOOLEAN 1 = 1
//   BOOLEAN GPA >= 3.0
//
// notes:
//   BOOLEAN USAGE prints usage before expression evaluation.
//   When a table is open, field-aware expressions use the current record.
//   This command does not mutate table data.
//
// risk:
//   evaluates_expression: yes except usage
//   mutates_table_data: no
//

#include "xbase.hpp"
#include "cli/cli_comment.hpp"
#include "xexpr.hpp"

#include <exception>
#include <iostream>
#include <sstream>
#include <string>
#include <cctype>

using namespace xbase;

namespace {

static std::string trim_local(std::string s) {
    auto issp = [](unsigned char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; };
    while (!s.empty() && issp((unsigned char)s.front())) s.erase(s.begin());
    while (!s.empty() && issp((unsigned char)s.back())) s.pop_back();
    return s;
}

} // namespace

static std::string edu_boolean_upper_contract(std::string s) {
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static void print_boolean_usage_contract() {
    std::cout
        << "Usage:\n"
        << "  BOOLEAN USAGE\n"
        << "  BOOLEAN <expr>\n"
        << "Examples:\n"
        << "  BOOLEAN 1 = 1\n"
        << "  BOOLEAN GPA >= 3.0\n"
        << "Notes:\n"
        << "  - BOOLEAN USAGE does not evaluate an expression.\n"
        << "  - Field-aware expressions use the current record when a table is open.\n";
}
void edu_BOOLEAN(DbArea& area, std::istringstream& in) {
    std::string expr;
    std::getline(in, expr);
    expr = cliutil::strip_inline_comments(trim_local(expr));

    // BOOLEAN_USAGE_CONTRACT_BRANCH
    {
        const std::string u = edu_boolean_upper_contract(expr);
        if (u == "USAGE" || u == "HELP" || u == "?") {
            print_boolean_usage_contract();
            return;
        }
    }
    if (expr.empty()) {
        print_boolean_usage_contract();
        return;
    }

    try {
        xexpr::EvalContext ctx;
        ctx.area = area.isOpen() ? &area : nullptr;

        bool result = false;
        std::string err;
        if (!xexpr::evaluate_predicate(expr, ctx, result, &err)) {
            std::cout << "BOOLEAN error: "
                      << (err.empty() ? "evaluation failed." : err)
                      << "\n";
            return;
        }

        std::cout << (result ? ".T." : ".F.") << "\n";
    } catch (const std::exception& e) {
        std::cout << "BOOLEAN error: " << e.what() << "\n";
    } catch (...) {
        std::cout << "BOOLEAN error: evaluation failed.\n";
    }
}
