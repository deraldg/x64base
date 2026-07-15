#pragma once

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <ios>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace textio {

// ============================================================================
// textio.hpp
//
// DotTalk command-surface string utilities.
//
// Doctrine:
//   - textio owns reusable string behavior for command parsing/reporting.
//   - textio does not own database, workarea, relation, workspace, memo,
//     tuple, or x64 storage policy.
//   - Keep helpers small, predictable, ASCII-oriented, and cross-platform.
//   - Prefer additive helpers over changing existing semantics.
//
// Compatibility:
//   Existing public helpers are preserved:
//     cls, ltrim, rtrim, trim, up, upper, lower, proper,
//     ieq, ends_with_ci, unescape_basic, unquote, tokenize.
// ============================================================================

// ---------------- console helpers ----------------

inline void cls() {
#if defined(_WIN32)
    std::system("cls");
#else
    std::system("clear");
#endif
}

// ---------------- character helpers ----------------

inline bool is_space(unsigned char c) noexcept {
    return std::isspace(c) != 0;
}

inline bool is_digit(unsigned char c) noexcept {
    return std::isdigit(c) != 0;
}

inline bool is_alnum(unsigned char c) noexcept {
    return std::isalnum(c) != 0;
}

inline char to_upper_char(char c) noexcept {
    return static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
}

inline char to_lower_char(char c) noexcept {
    return static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
}

// ---------------- basic trimming & case helpers ----------------

inline std::string ltrim(std::string s) {
    s.erase(s.begin(), std::find_if(s.begin(), s.end(),
        [](unsigned char c) { return !is_space(c); }));
    return s;
}

inline std::string rtrim(std::string s) {
    while (!s.empty() && is_space(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

inline std::string trim(std::string s) {
    return rtrim(ltrim(std::move(s)));
}

// legacy alias kept for compatibility
inline std::string up(std::string s) {
    for (auto& ch : s) ch = to_upper_char(ch);
    return s;
}

inline std::string upper(std::string s) {
    for (auto& ch : s) ch = to_upper_char(ch);
    return s;
}

inline std::string lower(std::string s) {
    for (auto& ch : s) ch = to_lower_char(ch);
    return s;
}

// Title/Proper case: first letter of each word uppercased, others lowercased.
// Word boundaries are any non-alphanumeric character.
inline std::string proper(std::string s) {
    bool new_word = true;
    for (auto& ch : s) {
        const unsigned char u = static_cast<unsigned char>(ch);
        if (is_alnum(u)) {
            ch = static_cast<char>(new_word ? std::toupper(u) : std::tolower(u));
            new_word = false;
        } else {
            new_word = true;
        }
    }
    return s;
}

// Normalized case helpers.
// These intentionally compose existing behavior so command docs can describe
// one string policy instead of command-local trim/up variations.
inline std::string trim_upper(std::string s) {
    return upper(trim(std::move(s)));
}

inline std::string trim_lower(std::string s) {
    return lower(trim(std::move(s)));
}

inline bool empty_after_trim(const std::string& s) {
    return trim(s).empty();
}

// ---------------- comparisons ----------------

inline bool ieq(const std::string& a, const std::string& b) {
    if (a.size() != b.size()) return false;
    for (std::size_t i = 0; i < a.size(); ++i) {
        if (to_lower_char(a[i]) != to_lower_char(b[i])) return false;
    }
    return true;
}

inline bool ieq_trimmed(const std::string& a, const std::string& b) {
    return ieq(trim(a), trim(b));
}

inline bool starts_with_ci(const std::string& s, const std::string& prefix) {
    if (s.size() < prefix.size()) return false;
    for (std::size_t i = 0; i < prefix.size(); ++i) {
        if (to_lower_char(s[i]) != to_lower_char(prefix[i])) return false;
    }
    return true;
}

inline bool starts_with_ci_trimmed(const std::string& s, const std::string& prefix) {
    return starts_with_ci(trim(s), prefix);
}

inline bool ends_with_ci(const std::string& s, const std::string& suf) {
    if (s.size() < suf.size()) return false;
    const std::size_t off = s.size() - suf.size();
    for (std::size_t i = 0; i < suf.size(); ++i) {
        if (to_lower_char(s[off + i]) != to_lower_char(suf[i])) return false;
    }
    return true;
}

inline bool token_is_ci(const std::string& token, const char* keyword_upper_or_mixed) {
    return ieq(trim(token), std::string(keyword_upper_or_mixed ? keyword_upper_or_mixed : ""));
}

// ---------------- quoting / escaping helpers ----------------

/* Unescape a few common sequences: \n \t \r \\ \" \'
   Unknown escapes keep the escaped character literally.
   A trailing backslash is preserved as a literal backslash. */
inline std::string unescape_basic(std::string s) {
    std::string out;
    out.reserve(s.size());

    bool esc = false;
    for (char c : s) {
        if (!esc) {
            if (c == '\\') {
                esc = true;
                continue;
            }
            out.push_back(c);
            continue;
        }

        switch (c) {
            case 'n':  out.push_back('\n'); break;
            case 't':  out.push_back('\t'); break;
            case 'r':  out.push_back('\r'); break;
            case '\\': out.push_back('\\'); break;
            case '"':  out.push_back('"'); break;
            case '\'': out.push_back('\''); break;
            default:   out.push_back(c); break;
        }
        esc = false;
    }

    if (esc) out.push_back('\\');
    return out;
}

inline std::string unquote(const std::string& s) {
    std::string t = trim(s);
    if (t.size() >= 2) {
        const char q0 = t.front();
        const char q1 = t.back();
        if ((q0 == '"' && q1 == '"') || (q0 == '\'' && q1 == '\'')) {
            return unescape_basic(t.substr(1, t.size() - 2));
        }
    }
    return t;
}

inline std::string quote_double_for_expr(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 2);
    out.push_back('"');
    for (char c : s) {
        switch (c) {
            case '\\': out += "\\\\"; break;
            case '"':  out += "\\\""; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:   out.push_back(c); break;
        }
    }
    out.push_back('"');
    return out;
}

// Minimal JSON string escaping for command-generated sidecar/debug files.
// This is intentionally not a JSON parser or serializer.
inline std::string escape_json_basic(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 16);
    for (char c : s) {
        switch (c) {
            case '\\': out += "\\\\"; break;
            case '"':  out += "\\\""; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:   out.push_back(c); break;
        }
    }
    return out;
}

// ---------------- stream helpers ----------------

// Return the remainder of an istringstream from its current position.
// This consumes the remaining current line when possible, matching the old
// tokenize(istringstream&) behavior closely enough for command-tail parsing.
inline std::string rest_of_stream(std::istringstream& iss) {
    std::string rest;

    if (iss.rdbuf() && iss.rdbuf()->in_avail() > 0) {
        std::getline(iss, rest);
        return rest;
    }

    const std::ios::iostate old_state = iss.rdstate();
    iss.clear();

    const std::streampos pos = iss.tellg();
    if (pos != std::istringstream::pos_type(-1)) {
        const std::string s = iss.str();
        const auto idx = static_cast<std::size_t>(pos);
        if (idx < s.size()) rest = s.substr(idx);
    }

    iss.setstate(old_state & std::ios::eofbit);
    return rest;
}

// Peek at the remainder without intentionally consuming it.
// For istringstream command parsers only.
inline std::string peek_rest(std::istringstream& iss) {
    const std::ios::iostate old_state = iss.rdstate();
    iss.clear();

    std::string rest;
    const std::streampos pos = iss.tellg();
    if (pos != std::istringstream::pos_type(-1)) {
        const std::string s = iss.str();
        const auto idx = static_cast<std::size_t>(pos);
        if (idx < s.size()) rest = s.substr(idx);
    }

    iss.clear(old_state);
    if (pos != std::istringstream::pos_type(-1)) {
        iss.seekg(pos);
    }
    return rest;
}

inline bool consume_keyword_ci(std::istringstream& iss, const char* keyword) {
    const std::ios::iostate old_state = iss.rdstate();
    iss.clear();

    const std::streampos pos = iss.tellg();

    std::string tok;
    if ((iss >> tok) && ieq(tok, std::string(keyword ? keyword : ""))) {
        return true;
    }

    iss.clear(old_state);
    if (pos != std::istringstream::pos_type(-1)) {
        iss.seekg(pos);
    }
    return false;
}

// ---------------- tokenization helpers ----------------

// Tokenize respecting quotes ('...' / "...") and backslash escapes inside quotes.
// Whitespace separates tokens only when not inside quotes.
// Quote characters are not included in the returned token.
inline std::vector<std::string> tokenize(const std::string& line) {
    std::vector<std::string> toks;
    std::string cur;
    cur.reserve(line.size());

    bool in_quote = false;
    char quote_ch = '\0';
    bool esc = false;

    auto flush = [&]() {
        if (!cur.empty()) {
            toks.emplace_back(std::move(cur));
            cur.clear();
        }
    };

    for (char c : line) {
        if (in_quote) {
            if (esc) {
                switch (c) {
                    case 'n':  cur.push_back('\n'); break;
                    case 't':  cur.push_back('\t'); break;
                    case 'r':  cur.push_back('\r'); break;
                    case '\\': cur.push_back('\\'); break;
                    case '"':  cur.push_back('"'); break;
                    case '\'': cur.push_back('\''); break;
                    default:   cur.push_back(c); break;
                }
                esc = false;
                continue;
            }

            if (c == '\\') {
                esc = true;
                continue;
            }

            if (c == quote_ch) {
                in_quote = false;
                quote_ch = '\0';
                continue;
            }

            cur.push_back(c);
            continue;
        }

        if (c == '"' || c == '\'') {
            in_quote = true;
            quote_ch = c;
            continue;
        }

        if (is_space(static_cast<unsigned char>(c))) {
            flush();
            continue;
        }

        cur.push_back(c);
    }

    if (esc) cur.push_back('\\');
    flush();
    return toks;
}

// Convenience overload: tokenize the remainder of an istringstream's current line.
inline std::vector<std::string> tokenize(std::istringstream& iss) {
    return tokenize(rest_of_stream(iss));
}

inline std::vector<std::string> tokenize_rest(std::istringstream& iss) {
    return tokenize(rest_of_stream(iss));
}

// ---------------- split helpers ----------------

inline std::vector<std::string> split_csv_simple(const std::string& csv) {
    std::vector<std::string> out;
    std::string cur;

    for (char c : csv) {
        if (c == ',') {
            std::string t = trim(std::move(cur));
            if (!t.empty()) out.push_back(std::move(t));
            cur.clear();
            continue;
        }
        cur.push_back(c);
    }

    std::string t = trim(std::move(cur));
    if (!t.empty()) out.push_back(std::move(t));
    return out;
}

// Split a comma expression list while respecting quoted strings and
// parenthesis depth. Quote characters are preserved in output.
inline std::vector<std::string> split_csv_expr(const std::string& s) {
    std::vector<std::string> out;
    std::string cur;

    int paren_depth = 0;
    bool in_quote = false;
    char quote_ch = '\0';
    bool esc = false;

    auto flush = [&]() {
        std::string t = trim(std::move(cur));
        if (!t.empty()) out.push_back(std::move(t));
        cur.clear();
    };

    for (char c : s) {
        if (in_quote) {
            cur.push_back(c);

            if (esc) {
                esc = false;
                continue;
            }

            if (c == '\\') {
                esc = true;
                continue;
            }

            if (c == quote_ch) {
                in_quote = false;
                quote_ch = '\0';
            }

            continue;
        }

        if (c == '"' || c == '\'') {
            in_quote = true;
            quote_ch = c;
            cur.push_back(c);
            continue;
        }

        if (c == '(') {
            ++paren_depth;
            cur.push_back(c);
            continue;
        }

        if (c == ')' && paren_depth > 0) {
            --paren_depth;
            cur.push_back(c);
            continue;
        }

        if (c == ',' && paren_depth == 0) {
            flush();
            continue;
        }

        cur.push_back(c);
    }

    flush();
    return out;
}

// Browser/relation path tokens commonly use:
//   enroll -> classes -> teachers
// or:
//   enroll, classes, teachers
inline std::vector<std::string> split_path_tokens(const std::string& raw) {
    std::string normalized;
    normalized.reserve(raw.size());

    for (std::size_t i = 0; i < raw.size(); ++i) {
        if (raw[i] == '-' && i + 1 < raw.size() && raw[i + 1] == '>') {
            normalized.push_back(',');
            ++i;
        } else {
            normalized.push_back(raw[i]);
        }
    }

    return split_csv_simple(normalized);
}

inline std::vector<std::string> split_pipe_simple(const std::string& line) {
    std::vector<std::string> out;
    std::string cur;

    for (char c : line) {
        if (c == '|') {
            out.push_back(trim(std::move(cur)));
            cur.clear();
            continue;
        }
        cur.push_back(c);
    }

    out.push_back(trim(std::move(cur)));
    return out;
}

inline std::string join(const std::vector<std::string>& parts, const std::string& sep) {
    std::string out;
    for (std::size_t i = 0; i < parts.size(); ++i) {
        if (i) out += sep;
        out += parts[i];
    }
    return out;
}

// ---------------- syntax-only command references ----------------

struct FieldRefText {
    std::string area;
    std::string field;
};

inline bool has_operatorish_char(char c) noexcept {
    switch (c) {
        case '(':
        case ')':
        case '"':
        case '\'':
        case '+':
        case '-':
        case '*':
        case '/':
        case '%':
        case '<':
        case '>':
        case '=':
        case '&':
        case '|':
        case '!':
            return true;
        default:
            return false;
    }
}

// Syntax-only parser for FIELD or AREA.FIELD.
//
// This does not resolve an area name to a workarea and does not resolve
// a field name against a DbArea. It deliberately mirrors the older relation
// command helper: reject expression/operator-looking terms, then split on dot.
inline bool parse_field_ref_text(const std::string& term, FieldRefText& out) {
    out = FieldRefText{};

    std::string t = trim(term);
    if (t.empty()) return false;

    for (char c : t) {
        if (has_operatorish_char(c)) return false;
    }

    const std::size_t dot = t.find('.');
    if (dot == std::string::npos) {
        out.field = trim(std::move(t));
        return !out.field.empty();
    }

    out.area = trim(t.substr(0, dot));
    out.field = trim(t.substr(dot + 1));
    return !out.area.empty() && !out.field.empty();
}

inline bool parse_field_ref_text(const std::string& term,
                                 std::string& area_out,
                                 std::string& field_out) {
    FieldRefText ref;
    if (!parse_field_ref_text(term, ref)) {
        area_out.clear();
        field_out.clear();
        return false;
    }

    area_out = std::move(ref.area);
    field_out = std::move(ref.field);
    return true;
}

inline std::string naked_field(std::string s) {
    const std::size_t dot = s.find('.');
    if (dot != std::string::npos) s = s.substr(dot + 1);
    return trim(std::move(s));
}

inline bool is_plain_identifier_ref(const std::string& s) {
    FieldRefText ref;
    return parse_field_ref_text(s, ref);
}

// ---------------- literal helpers ----------------

inline bool is_integer_literal(const std::string& s) {
    const std::string t = trim(s);
    if (t.empty()) return false;

    std::size_t i = 0;
    if (t[i] == '+' || t[i] == '-') ++i;
    if (i >= t.size()) return false;

    bool any_digit = false;
    for (; i < t.size(); ++i) {
        if (!is_digit(static_cast<unsigned char>(t[i]))) return false;
        any_digit = true;
    }

    return any_digit;
}

// Simple historical numeric literal test:
//   optional sign, digits, optional one decimal point.
// No exponent notation here; callers needing modern numeric grammar should
// use their owning expression/parser subsystem.
inline bool is_numeric_literal(const std::string& s) {
    const std::string t = trim(s);
    if (t.empty()) return false;

    std::size_t i = 0;
    if (t[i] == '+' || t[i] == '-') ++i;
    if (i >= t.size()) return false;

    bool any_digit = false;
    bool any_dot = false;

    for (; i < t.size(); ++i) {
        const unsigned char ch = static_cast<unsigned char>(t[i]);

        if (is_digit(ch)) {
            any_digit = true;
            continue;
        }

        if (t[i] == '.' && !any_dot) {
            any_dot = true;
            continue;
        }

        return false;
    }

    return any_digit;
}

} // namespace textio
