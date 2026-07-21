// @dottalk.usage v1
// owner: DOT|VAR
// command: VAR
// category: scripting
// status: supported
// noargs: usage
// effect: evaluate-and-store
// mutates: session-variables
// usage-access: VAR USAGE
// summary:
//   Evaluate an expression and store it as a scoped DotScript memory variable,
//   referenced later as $name.
//
// usage:
//   VAR USAGE
//   VAR <name> = <expression>
//
// examples:
//   VAR threshold = 3.0
//   VAR label = UPPER(LNAME)
//   VAR today = DATE()
//   VAR nums = {10, 20, 30}
//   ? $threshold * 2          && reference a stored variable as $name
//
// notes:
//   VAR with no arguments prints usage.
//   VAR USAGE prints usage and does not evaluate or store.
//   VAR evaluates the right-hand side through the array-preserving expression
//   path and stores the result in the scoped session memory-variable store,
//   keyed by the sigil-stripped, case-insensitive name; the value may be a
//   scalar or an array. The stored variable is read back in later expressions
//   as $name. Distinct from SET VAR (&macro) variables, which do textual
//   substitution rather than value storage.
//
// risk:
//   mutates_table_data: no
//
// related:
//   DOTSCRIPT
//   CALC
//   SET VAR
//

#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "dotscript_var_name.hpp"
#include "cli/expr/rhs_eval.hpp"     // eval_rhs -> dottalk::expr::EvalValue
#include "cli/expr/value_eval.hpp"   // EvalValue definition
#include "xexpr/var_store.hpp"       // dottalk::dotscript::session_vars() (AIF-038)
#include <algorithm>
#include <cctype>
#include <utility>

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

    // Evaluate the right-hand side through the array-preserving expression path (so
    // field references, functions, arithmetic AND array literals/subscripts all work)
    // and store the result directly. Using eval_rhs_avalue rather than eval_rhs is
    // essential: eval_rhs returns an EvalValue, which has no array kind and would
    // flatten `{1,2,3}` to the string "{array:3}" — the variable must keep its real
    // ArrayRef so `$x[n]` subscripting works. Names are stored under the sigil-stripped
    // bare form, so `VAR x = ...` and a later `$x` reference agree.
    std::string err;
    dottalk::array::Value value;   // defaults to NIL
    if (!dottalk::expr::eval_rhs_avalue(&current, expr, value, &err)) {
        std::cout << "VAR error: " << (err.empty() ? "evaluation failed" : err) << "\n";
        return;
    }

    std::string store_name = var_name;
    if (!store_name.empty() && store_name[0] == '$') store_name.erase(0, 1);

    dottalk::dotscript::session_vars().assign(store_name, std::move(value));
    std::cout << "VAR stored: " << store_name << "\n";
}
