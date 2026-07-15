// ===============================
// FILE: src/cli/edu_formula.cpp
// FORMULA / "?" <expr>
//
// Phase 1 xexpr migration:
// - FORMULA now routes expression evaluation through xexpr.
// - No direct dependency on cli/expr AST/parser/eval headers.
// - No manual DBF header scanning or disk reads.
// - Table-aware expressions use the current DbArea through xexpr::EvalContext.
// ===============================

// @dottalk.usage v1
// owner: EDU|FORMULA
// command: FORMULA / ?
// category: education-expression
// status: supported
// noargs: usage
// effect: evaluate-expression
// mutates: none
// usage-access: FORMULA USAGE
// summary:
//   Evaluate a scalar expression through xexpr and print the formatted value.
//
// usage:
//   FORMULA USAGE
//   FORMULA <expr>
//   ? <expr>
//
// examples:
//   FORMULA 2 + 2
//   FORMULA UPPER(LNAME)
//   ? GPA + 0
//
// notes:
//   FORMULA USAGE prints usage before expression evaluation.
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

#include <cctype>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

using namespace xbase;

namespace {

static std::string trim_local(std::string s) {
    auto issp = [](unsigned char c) {
        return c == ' ' || c == '\t' || c == '\r' || c == '\n';
    };

    while (!s.empty() && issp(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }

    while (!s.empty() && issp(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }

    return s;
}

static std::string strip_outer_parens(std::string s) {
    s = trim_local(std::move(s));

    for (;;) {
        if (s.size() < 2) {
            return s;
        }

        if (s.front() != '(' || s.back() != ')') {
            return s;
        }

        int depth = 0;
        bool in_single = false;
        bool in_double = false;
        bool outer_pair_wraps_all = true;

        for (std::size_t i = 0; i < s.size(); ++i) {
            const char c = s[i];

            if (c == '"' && !in_single) {
                in_double = !in_double;
                continue;
            }

            if (c == '\'' && !in_double) {
                in_single = !in_single;
                continue;
            }

            if (in_single || in_double) {
                continue;
            }

            if (c == '(') {
                ++depth;
            } else if (c == ')') {
                --depth;
            }

            if (depth == 0 && i != s.size() - 1) {
                outer_pair_wraps_all = false;
                break;
            }
        }

        if (!outer_pair_wraps_all || depth != 0) {
            return s;
        }

        s = trim_local(s.substr(1, s.size() - 2));
    }
}

static std::string format_number(double v) {
    const double iv = std::floor(v);

    if (std::fabs(v - iv) < 1e-9) {
        std::ostringstream o;
        o << static_cast<long long>(iv);
        return o.str();
    }

    std::ostringstream o;
    o << std::fixed << std::setprecision(10) << v;
    std::string s = o.str();

    while (!s.empty() && s.find('.') != std::string::npos && s.back() == '0') {
        s.pop_back();
    }

    if (!s.empty() && s.back() == '.') {
        s.pop_back();
    }

    return s.empty() ? "0" : s;
}

static void print_value(const xexpr::Value& value) {
    switch (value.kind()) {
        case xexpr::ValueKind::Bool:
            std::cout << (value.as_bool() ? ".T." : ".F.") << "\n";
            return;

        case xexpr::ValueKind::Number:
            std::cout << format_number(value.as_number()) << "\n";
            return;

        case xexpr::ValueKind::String:
            std::cout << value.as_string() << "\n";
            return;

        case xexpr::ValueKind::Date:
            std::cout << value.as_date8() << "\n";
            return;

        case xexpr::ValueKind::Error:
            if (!value.error_message().empty()) {
                std::cout << "FORMULA error: " << value.error_message() << "\n";
            } else {
                std::cout << "FORMULA error: evaluation failed.\n";
            }
            return;

        case xexpr::ValueKind::None:
        default:
            std::cout << ".F.\n";
            return;
    }
}

} // namespace

static std::string edu_formula_upper_contract(std::string s) {
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static void print_formula_usage_contract() {
    std::cout
        << "Usage:\n"
        << "  FORMULA USAGE\n"
        << "  FORMULA <expr>\n"
        << "  ? <expr>\n"
        << "Examples:\n"
        << "  FORMULA 2 + 2\n"
        << "  FORMULA UPPER(LNAME)\n"
        << "  ? GPA + 0\n"
        << "Notes:\n"
        << "  - FORMULA USAGE does not evaluate an expression.\n"
        << "  - Field-aware expressions use the current record when a table is open.\n";
}
void edu_FORMULA(DbArea& area, std::istringstream& in) {
    std::string expr;
    std::getline(in, expr);

    expr = cliutil::strip_inline_comments(trim_local(expr));
    expr = strip_outer_parens(expr);

    // FORMULA_USAGE_CONTRACT_BRANCH
    {
        const std::string u = edu_formula_upper_contract(expr);
        if (u == "USAGE" || u == "HELP" || u == "?") {
            print_formula_usage_contract();
            return;
        }
    }
    if (expr.empty()) {
        print_formula_usage_contract();
        return;
    }

    xexpr::EvalContext ctx;
    ctx.area = area.isOpen() ? &area : nullptr;

    const xexpr::Value value = xexpr::evaluate_expression(expr, ctx);
    print_value(value);
}
