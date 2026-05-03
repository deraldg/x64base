#include "tuple/tuple_command_spec.hpp"

#include <algorithm>
#include <cctype>
#include <ios>
#include <istream>
#include <iterator>
#include <sstream>
#include <string>

namespace dottalk::tupleaugment {

std::string tuple_spec_trim(std::string s) {
    auto issp = [](unsigned char c) { return std::isspace(c) != 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [&](unsigned char c) { return !issp(c); }));
    s.erase(std::find_if(s.rbegin(), s.rend(), [&](unsigned char c) { return !issp(c); }).base(), s.end());
    return s;
}

std::string tuple_spec_upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

namespace {

std::string read_tail(std::istream& in) {
    std::string raw{std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>()};
    return tuple_spec_trim(std::move(raw));
}

std::string strip_inline_comments(std::string s) {
    bool in_dquote = false;
    bool in_squote = false;

    for (std::size_t i = 0; i < s.size(); ++i) {
        const char c = s[i];
        if (c == '"' && !in_squote) {
            in_dquote = !in_dquote;
            continue;
        }
        if (c == '\'' && !in_dquote) {
            in_squote = !in_squote;
            continue;
        }
        if (in_dquote || in_squote) continue;

        if (c == '&' && i + 1 < s.size() && s[i + 1] == '&') {
            s.erase(i);
            break;
        }
        if (c == '/' && i + 1 < s.size() && s[i + 1] == '/') {
            const bool left_ok = (i == 0) || std::isspace(static_cast<unsigned char>(s[i - 1]));
            if (left_ok) {
                s.erase(i);
                break;
            }
        }
    }

    return tuple_spec_trim(std::move(s));
}

bool word_boundary(char c) {
    return c == '\0' || std::isspace(static_cast<unsigned char>(c)) || c == ',';
}

std::size_t find_word_outside_quotes(const std::string& s, const std::string& word_upper) {
    bool in_dquote = false;
    bool in_squote = false;
    const std::size_t n = word_upper.size();

    for (std::size_t i = 0; i + n <= s.size(); ++i) {
        const char c = s[i];
        if (c == '"' && !in_squote) {
            in_dquote = !in_dquote;
            continue;
        }
        if (c == '\'' && !in_dquote) {
            in_squote = !in_squote;
            continue;
        }
        if (in_dquote || in_squote) continue;

        if (tuple_spec_upper(s.substr(i, n)) == word_upper) {
            const char left = (i == 0) ? '\0' : s[i - 1];
            const char right = (i + n >= s.size()) ? '\0' : s[i + n];
            if (word_boundary(left) && word_boundary(right)) return i;
        }
    }

    return std::string::npos;
}

struct TokenResult {
    bool ok{false};
    std::string token;
    std::string rest;
};

TokenResult take_token(std::string raw) {
    TokenResult out;
    raw = tuple_spec_trim(std::move(raw));
    if (raw.empty()) return out;

    const char quote = raw.front();
    if (quote == '"' || quote == '\'') {
        std::string token;
        bool escaped = false;
        for (std::size_t i = 1; i < raw.size(); ++i) {
            const char c = raw[i];
            if (escaped) {
                token.push_back(c);
                escaped = false;
                continue;
            }
            if (c == '\\') {
                escaped = true;
                continue;
            }
            if (c == quote) {
                out.ok = true;
                out.token = std::move(token);
                out.rest = tuple_spec_trim(raw.substr(i + 1));
                return out;
            }
            token.push_back(c);
        }
        return out;
    }

    std::istringstream iss(raw);
    iss >> out.token;
    std::string rest;
    std::getline(iss, rest);
    out.rest = tuple_spec_trim(std::move(rest));
    out.ok = !out.token.empty();
    return out;
}

bool consume_trailing_trace(std::string& raw) {
    std::string t = tuple_spec_trim(raw);
    std::string u = tuple_spec_upper(t);

    if (u == "TRACE") {
        raw.clear();
        return true;
    }

    constexpr const char* marker = " TRACE";
    const std::size_t pos = u.rfind(marker);
    if (pos != std::string::npos && pos + 6 == u.size()) {
        raw = tuple_spec_trim(t.substr(0, pos));
        return true;
    }
    return false;
}

void split_for_clause(std::string raw, std::string& before, std::string& for_expr) {
    raw = strip_inline_comments(tuple_spec_trim(std::move(raw)));
    const std::size_t pos = find_word_outside_quotes(raw, "FOR");
    if (pos == std::string::npos) {
        before = raw;
        for_expr.clear();
        return;
    }

    before = tuple_spec_trim(raw.substr(0, pos));
    for_expr = tuple_spec_trim(raw.substr(pos + 3));
}

void normalize_common(TupleCommandSpec& spec) {
    spec.tuple_spec = tuple_spec_trim(std::move(spec.tuple_spec));

    if (tuple_spec_upper(spec.tuple_spec) == "FIELDS") {
        spec.tuple_spec = "*";
    }

    const std::string up = tuple_spec_upper(spec.tuple_spec);
    if (up == "" || up == "*" || up == "ALL") {
        spec.tuple_spec = "*";
        return;
    }

    constexpr const char* fields = "FIELDS ";
    if (up.rfind(fields, 0) == 0) {
        spec.tuple_spec = tuple_spec_trim(spec.tuple_spec.substr(7));
        if (spec.tuple_spec.empty()) spec.tuple_spec = "*";
    }
}

bool is_help(const std::string& raw) {
    const std::string up = tuple_spec_upper(tuple_spec_trim(raw));
    return up.empty() || up == "?" || up == "/?" || up == "HELP" || up == "--HELP";
}

bool consume_validate_options(std::string& raw, TupleCommandSpec& spec) {
    bool changed = false;

    if (consume_trailing_trace(raw)) {
        spec.trace = true;
        changed = true;
    }

    // Small shared parser for MAX <n> at the end of validation/report commands.
    // This is intentionally conservative and does not try to parse MAX inside FOR.
    std::string t = tuple_spec_trim(raw);
    std::string u = tuple_spec_upper(t);
    const std::size_t pos = u.rfind(" MAX ");
    if (pos != std::string::npos) {
        const std::string after = tuple_spec_trim(t.substr(pos + 5));
        if (!after.empty() && std::all_of(after.begin(), after.end(), [](unsigned char c){ return std::isdigit(c) != 0; })) {
            try {
                spec.max_issues = static_cast<std::size_t>(std::stoul(after));
                raw = tuple_spec_trim(t.substr(0, pos));
                changed = true;
            } catch (...) {
            }
        }
    }

    return changed;
}

} // namespace

TupleCommandSpec parse_tuple_export_spec(std::istream& in) {
    TupleCommandSpec spec;
    std::string raw = read_tail(in);
    raw = strip_inline_comments(std::move(raw));

    if (is_help(raw)) {
        spec.help = true;
        return spec;
    }

    TokenResult fmt = take_token(raw);
    if (!fmt.ok) {
        spec.help = true;
        return spec;
    }
    spec.format = tuple_spec_upper(fmt.token);

    TokenResult path = take_token(fmt.rest);
    if (!path.ok) {
        spec.help = true;
        return spec;
    }
    spec.path = path.token;

    std::string before_for;
    split_for_clause(path.rest, before_for, spec.for_expr);
    spec.tuple_spec = before_for;
    normalize_common(spec);

    return spec;
}

TupleCommandSpec parse_tuple_validate_spec(std::istream& in) {
    TupleCommandSpec spec;
    std::string raw = read_tail(in);
    raw = strip_inline_comments(std::move(raw));

    if (!raw.empty() && is_help(raw)) {
        spec.help = true;
        return spec;
    }

    (void)consume_validate_options(raw, spec);

    std::string before_for;
    split_for_clause(raw, before_for, spec.for_expr);
    spec.tuple_spec = before_for;
    normalize_common(spec);

    return spec;
}

} // namespace dottalk::tupleaugment
