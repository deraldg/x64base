#include "predicates.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>

#include "cli/expr/value_eval.hpp"

namespace {

static std::string trim_copy(std::string s) {
    auto not_space = [](unsigned char ch) {
        return !std::isspace(ch);
    };

    auto b = std::find_if(s.begin(), s.end(), [&](char c) {
        return not_space(static_cast<unsigned char>(c));
    });
    auto e = std::find_if(s.rbegin(), s.rend(), [&](char c) {
        return not_space(static_cast<unsigned char>(c));
    }).base();

    if (b >= e) return {};
    return std::string(b, e);
}

static std::string upper_copy(std::string s) {
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static bool looks_numeric_literal(const std::string& s_in) {
    const std::string s = trim_copy(s_in);
    if (s.empty()) return false;

    bool saw_digit = false;
    bool saw_dot = false;
    std::size_t i = 0;

    if (s[i] == '+' || s[i] == '-') ++i;

    for (; i < s.size(); ++i) {
        const unsigned char ch = static_cast<unsigned char>(s[i]);

        if (ch >= '0' && ch <= '9') {
            saw_digit = true;
            continue;
        }

        if (ch == '.' && !saw_dot) {
            saw_dot = true;
            continue;
        }

        return false;
    }

    return saw_digit;
}

static bool is_identifier(const std::string& s_in) {
    const std::string s = trim_copy(s_in);
    if (s.empty()) return false;

    const unsigned char first = static_cast<unsigned char>(s[0]);
    if (!std::isalpha(first) && s[0] != '_') return false;

    for (char c : s) {
        const unsigned char ch = static_cast<unsigned char>(c);
        if (!std::isalnum(ch) && c != '_') return false;
    }

    return true;
}

static bool is_quoted_literal(const std::string& s_in) {
    const std::string s = trim_copy(s_in);
    if (s.size() < 2) return false;

    const char q = s.front();
    if (q != '"' && q != '\'') return false;

    return s.back() == q;
}

static bool is_reserved_literal(const std::string& s_in) {
    const std::string u = upper_copy(trim_copy(s_in));

    return u == "TRUE"  ||
           u == "FALSE" ||
           u == ".T."   ||
           u == ".F."   ||
           u == "NULL";
}

static bool is_known_field_ci(const xbase::DbArea& a, const std::string& name) {
    const std::string want = upper_copy(trim_copy(name));
    if (want.empty()) return false;

    const auto& f = a.fields();
    for (const auto& fld : f) {
        if (upper_copy(trim_copy(fld.name)) == want) return true;
    }

    return false;
}

static bool looks_like_expression(const std::string& s_in) {
    const std::string s = trim_copy(s_in);
    if (s.empty()) return false;

    // Function call or grouped expression.
    if (s.find('(') != std::string::npos || s.find(')') != std::string::npos) {
        return true;
    }

    // Obvious arithmetic or concatenation expression.
    if (s.find('+') != std::string::npos ||
        s.find('*') != std::string::npos ||
        s.find('/') != std::string::npos) {
        return true;
    }

    // A hyphen may be part of a date literal if quoted, but unquoted it is
    // usually arithmetic or unary minus. Numeric negatives are handled earlier.
    if (s.find('-') != std::string::npos && !looks_numeric_literal(s)) {
        return true;
    }

    return false;
}

static std::string escape_string_literal(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 8);

    for (char c : s) {
        if (c == '\\' || c == '"') {
            out.push_back('\\');
        }
        out.push_back(c);
    }

    return out;
}

static std::string quote_string_literal(const std::string& s) {
    return "\"" + escape_string_literal(trim_copy(s)) + "\"";
}

static std::string normalize_rhs_for_expression(const xbase::DbArea& a,
                                                const std::string& rhs_in)
{
    const std::string rhs = trim_copy(rhs_in);

    if (rhs.empty()) return "\"\"";

    // Already valid expression/literal forms.
    if (is_quoted_literal(rhs))      return rhs;
    if (looks_numeric_literal(rhs))  return rhs;
    if (is_reserved_literal(rhs))    return rhs;
    if (is_known_field_ci(a, rhs))   return rhs;
    if (looks_like_expression(rhs))  return rhs;

    // Legacy xBase-ish convenience:
    //   LNAME = WHITE
    // becomes:
    //   LNAME = "WHITE"
    if (is_identifier(rhs)) {
        return quote_string_literal(rhs);
    }

    // Conservative fallback: quote unknown rhs text as a string literal.
    return quote_string_literal(rhs);
}

static std::string build_expr(const xbase::DbArea& a,
                              const std::string& lhs,
                              const std::string& op,
                              const std::string& rhs)
{
    std::ostringstream out;
    out << trim_copy(lhs) << ' '
        << trim_copy(op)  << ' '
        << normalize_rhs_for_expression(a, rhs);

    return out.str();
}

} // namespace

namespace predicates {

int field_index_ci(const xbase::DbArea& a, const std::string& name) {
    const auto& f = a.fields();
    const std::string want = upper_copy(trim_copy(name));

    for (size_t i = 0; i < f.size(); ++i) {
        if (upper_copy(trim_copy(f[i].name)) == want) {
            return static_cast<int>(i + 1); // 1-based
        }
    }

    return 0;
}

bool eval_expr(const xbase::DbArea& a,
               const std::string& expr_text,
               std::string* err_out)
{
    bool out = false;
    std::string err;

    // The evaluator API is non-const because field access is routed through the
    // current DbArea runtime view. This facade does not intentionally mutate the
    // area; const_cast keeps the public predicate interface backward compatible.
    xbase::DbArea& area = const_cast<xbase::DbArea&>(a);

    if (!dottalk::expr::eval_bool(area, expr_text, out, &err)) {
        if (err_out) *err_out = err;
        return false;
    }

    if (err_out) err_out->clear();
    return out;
}

bool eval(const xbase::DbArea& a,
          const std::string& lhs,
          const std::string& op,
          const std::string& rhs)
{
    const std::string expr_text = build_expr(a, lhs, op, rhs);

    std::string ignored;
    return eval_expr(a, expr_text, &ignored);
}

} // namespace predicates
