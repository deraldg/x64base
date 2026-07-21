// include/cli/expr/dotscript_predicate_bridge.hpp
//
// One shared bridge that lets a predicate referencing DotScript state — a `$name` memory
// variable, a `$a[n]` subscript, or a `{...}` array literal — be evaluated by the single
// house expression evaluator (`dottalk::expr::eval_rhs_avalue`, the same session_vars()-backed,
// field-aware ValueParser the display path uses), against the current record.
//
// This is the "centralize on the house expr system" convergence (AIF-041). It is reused by
// BOTH predicate entry points that need it, so the detector and truthiness live in exactly
// one place (AIF-037, Rule of Three):
//   - shell_eval_bool_expr        (IF / WHILE / UNTIL — the boolean adapter)
//   - predx::eval_expr            (LOCATE / COUNT / SCAN / LIST FOR + SET FILTER — the scan path)
//
// The compiled WHERE engine and the predx triplet evaluator cannot represent `$name`/`$a[n]`/
// `{...}` (and predx uses `$` as the substring-containment operator), so those predicates are
// routed here instead. Field-only predicates never match the detector and are left untouched.

#pragma once

#include <cctype>
#include <cmath>
#include <string>
#include <variant>

#include "xbase.hpp"
#include "cli/expr/rhs_eval.hpp"   // dottalk::expr::eval_rhs_avalue + dottalk::array::Value

namespace dottalk::dotscript {

// A predicate references DotScript state if it contains a `{` (array literal) or a `$`
// that STARTS an operand (a memvar sigil `$name`), as opposed to the xBase substring
// containment operator `a $ b` which sits BETWEEN operands. `$` is a memvar sigil only
// when it is immediately followed by an identifier char AND is at the start, or the
// previous non-space character is not an operand terminator (alnum / `_` / `)` / quote).
inline bool looks_like_dotscript_predicate(const std::string& s)
{
    for (std::size_t i = 0; i < s.size(); ++i) {
        if (s[i] == '{') return true;                 // {...} array literal
        if (s[i] != '$') continue;

        const char nxt = (i + 1 < s.size()) ? s[i + 1] : '\0';
        if (!(std::isalpha(static_cast<unsigned char>(nxt)) || nxt == '_')) continue;

        std::size_t j = i;
        while (j > 0 && (s[j - 1] == ' ' || s[j - 1] == '\t')) --j;
        if (j == 0) return true;                       // `$name ...` at start of operand
        const char prev = s[j - 1];
        const bool prev_is_operand_end =
            std::isalnum(static_cast<unsigned char>(prev)) ||
            prev == '_' || prev == ')' || prev == '"' || prev == '\'';
        if (!prev_is_operand_end) return true;         // preceded by operator/`(`/`,` → memvar
        // else `operand $ name` → containment operator; not a memvar.
    }
    return false;
}

// Truthiness of a house-evaluated value used as a boolean predicate result. A comparison
// yields a bool leaf; the other arms are defensive so a stray non-boolean never asserts.
inline bool avalue_truthy(const dottalk::array::Value& v)
{
    if (std::holds_alternative<bool>(v)) return std::get<bool>(v);
    if (std::holds_alternative<double>(v)) {
        const double d = std::get<double>(v);
        return std::isfinite(d) && d != 0.0;
    }
    if (std::holds_alternative<std::string>(v)) {
        std::string t = std::get<std::string>(v);
        const std::size_t a = t.find_first_not_of(" \t");
        if (a == std::string::npos) return false;
        const std::size_t b = t.find_last_not_of(" \t");
        t = t.substr(a, b - a + 1);
        for (char& c : t) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        return t == ".T." || t == "T" || t == "TRUE" || t == "Y" || t == "1";
    }
    return false; // NilValue, or a bare array reference, is not a satisfied condition
}

// Try to evaluate `expr` as a DotScript-referencing predicate against the current record of
// `A`, via the house evaluator. Returns true (and sets `out`) if the predicate references
// DotScript state AND the house evaluator succeeded; false otherwise — in which case the
// caller keeps its normal path (no regression for field-only / containment predicates, and
// a graceful fall-through if the house evaluator cannot handle a given DotScript predicate).
inline bool try_eval_dotscript_predicate(xbase::DbArea& A, const std::string& expr, bool& out)
{
    if (!looks_like_dotscript_predicate(expr)) return false;
    dottalk::array::Value v;
    std::string err;
    if (dottalk::expr::eval_rhs_avalue(&A, expr, v, &err)) {
        out = avalue_truthy(v);
        return true;
    }
    return false;
}

} // namespace dottalk::dotscript
