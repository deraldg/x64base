// src/cli/edu_boolean.cpp
// DotTalk++ BOOLEAN
//
// xexpr migration note:
//   This command now calls the xexpr facade instead of reaching directly into
//   cli/expr/api.hpp, cli/expr/ast.hpp, and cli/expr/glue_xbase.hpp.
//   The command syntax and output remain unchanged.

#include "xbase.hpp"
#include "cli/cli_comment.hpp"
#include "xexpr.hpp"

#include <exception>
#include <iostream>
#include <sstream>
#include <string>

using namespace xbase;

namespace {

static std::string trim_local(std::string s) {
    auto issp = [](unsigned char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; };
    while (!s.empty() && issp((unsigned char)s.front())) s.erase(s.begin());
    while (!s.empty() && issp((unsigned char)s.back())) s.pop_back();
    return s;
}

} // namespace

void edu_BOOLEAN(DbArea& area, std::istringstream& in) {
    std::string expr;
    std::getline(in, expr);
    expr = cliutil::strip_inline_comments(trim_local(expr));

    if (expr.empty()) {
        std::cout << "Usage: BOOLEAN <expr>\n";
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
