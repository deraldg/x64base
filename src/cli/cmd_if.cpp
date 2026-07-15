// @dottalk.usage v1
// owner: DOT|IF
// command: IF
// category: script
// status: supported
// noargs: error
// effect: control-flow
// mutates: if-stack
// usage-access: IF USAGE
// summary:
//   Start an IF/ELSE/ENDIF conditional block using the shell's shared boolean
//   expression evaluator and control-flow stack.
//
// usage:
//   IF USAGE
//   IF <bool-expr>
//   ELSE
//   ELSE USAGE
//   ENDIF
//   ENDIF USAGE
//
// examples:
//   IF GPA >= 3.0
//       ECHO HONORS
//   ELSE
//       ECHO REGULAR
//   ENDIF
//
// notes:
//   IF USAGE prints usage and does not modify the IF stack.
//   IF evaluates only when the outer IF stack allows execution.
//   ELSE flips the active branch for the current IF frame.
//   ENDIF exits the current IF frame.
//   Effects of commands inside the active branch are owned by those commands.
//
// risk:
//   mutates_if_stack: yes except usage
//   executes_body_commands: indirectly through shell control flow
//   mutates_table_data: no direct mutation
//
// related:
//   WHILE
//   UNTIL
//   SCAN
//

// src/cli/cmd_if.cpp
// IF / ELSE / ENDIF
//
// Thin command layer. Control logic is owned by shell_control_utils,
// which must be the same stack consulted by shell_execute_line(...).

#include "xbase.hpp"
#include "cli/cli_comment.hpp"
#include "shell.hpp"
#include "shell_control_utils.hpp"

#include <iostream>
#include <sstream>
#include <string>
#include <cctype>

static std::string trim_local(std::string s)
{
    auto issp = [](unsigned char c) {
        return c == ' ' || c == '\t' || c == '\r' || c == '\n';
    };
    while (!s.empty() && issp((unsigned char)s.front())) s.erase(s.begin());
    while (!s.empty() && issp((unsigned char)s.back())) s.pop_back();
    return s;
}

static std::string upper_local(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static bool usage_word_local(const std::string& raw)
{
    const std::string u = upper_local(trim_local(raw));
    return u == "USAGE" || u == "HELP" || u == "?";
}

static void print_if_usage()
{
    std::cout
        << "Usage:\n"
        << "  IF USAGE\n"
        << "  IF <bool-expr>\n"
        << "  ELSE\n"
        << "  ELSE USAGE\n"
        << "  ENDIF\n"
        << "  ENDIF USAGE\n"
        << "Examples:\n"
        << "  IF GPA >= 3.0\n"
        << "      ECHO HONORS\n"
        << "  ELSE\n"
        << "      ECHO REGULAR\n"
        << "  ENDIF\n"
        << "Notes:\n"
        << "  - IF USAGE, ELSE USAGE, and ENDIF USAGE do not modify the IF stack.\n";
}

void cmd_IF(xbase::DbArea& area, std::istringstream& in)
{
    std::string expr;
    std::getline(in, expr);
    expr = cliutil::strip_inline_comments(trim_local(expr));

    if (usage_word_local(expr)) {
        print_if_usage();
        return;
    }

    // Already suppressed by outer IF -> do not evaluate.
    if (!dottalk::shell_if_can_eval()) {
        dottalk::shell_if_enter(false, /*evaluated=*/false);
        return;
    }

    if (expr.empty()) {
        std::cout << "IF error: missing expression\n";
        dottalk::shell_if_enter(false, /*evaluated=*/false);
        return;
    }

    bool cond = false;
    std::string err;
    const bool ok = shell_eval_bool_expr(area, expr, &cond, &err);
    if (!ok) {
        std::cout << "IF error: "
                  << (err.empty() ? "invalid boolean expression" : err) << "\n";
        dottalk::shell_if_enter(false, /*evaluated=*/false);
        return;
    }

    dottalk::shell_if_enter(cond, /*evaluated=*/true);
}

void cmd_ELSE(xbase::DbArea&, std::istringstream& in)
{
    std::string arg;
    std::getline(in, arg);
    if (usage_word_local(arg)) {
        print_if_usage();
        return;
    }
    dottalk::shell_if_else();
}

// @dottalk.usage v1
// owner: DOT|ENDIF
// command: ENDIF
// category: syntax-command
// status: active
// noargs: closes-control-block
// effect: control-flow
// mutates: none
// usage-access: ENDIF USAGE
// summary:
//   Close an IF control block.
//
// usage:
//   ENDIF
//
// notes:
//   Syntax command paired with IF and ELSE. It does not mutate table data by itself.
//
// related:
//   IF, ELSE, CASE
//
void cmd_ENDIF(xbase::DbArea&, std::istringstream& in)
{
    std::string arg;
    std::getline(in, arg);
    if (usage_word_local(arg)) {
        print_if_usage();
        return;
    }
    dottalk::shell_if_exit();
}
