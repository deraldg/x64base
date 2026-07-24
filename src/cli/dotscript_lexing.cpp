// src/cli/dotscript_lexing.cpp
// Canonical implementation of the DotScript comment vocabulary. See the header
// for the rules; this is the single source of truth (AIF-037, Rule of Three).

#include "cli/dotscript_lexing.hpp"

#include <cctype>
#include <cstddef>

namespace dottalk::lexing {

namespace {

// "REM" as the first token at position i: case-insensitive, then whitespace/EOL.
bool matches_rem(const std::string& s, std::size_t i)
{
    return i + 2 < s.size()
        && (s[i]     == 'R' || s[i]     == 'r')
        && (s[i + 1] == 'E' || s[i + 1] == 'e')
        && (s[i + 2] == 'M' || s[i + 2] == 'm')
        && (i + 3 == s.size() || std::isspace(static_cast<unsigned char>(s[i + 3])));
}

std::size_t first_nonspace(const std::string& s)
{
    std::size_t i = 0;
    while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) ++i;
    return i;
}

} // namespace

std::string strip_inline_comment(const std::string& s)
{
    bool in_single = false;
    bool in_double = false;
    bool esc = false;

    for (std::size_t i = 0; i < s.size(); ++i) {
        const char c = s[i];

        if (esc) { esc = false; continue; }
        if (c == '\\') { esc = true; continue; }
        if (!in_double && c == '\'') { in_single = !in_single; continue; }
        if (!in_single && c == '"')  { in_double = !in_double; continue; }

        const bool outside_quotes = !in_single && !in_double;
        const bool starts_hash = (c == '#');
        const bool starts_amp2 = (c == '&' && i + 1 < s.size() && s[i + 1] == '&');

        if (outside_quotes && (starts_hash || starts_amp2)) {
            std::size_t j = i;
            while (j > 0 && (s[j - 1] == ' ' || s[j - 1] == '\t')) --j;
            return s.substr(0, j);
        }
    }
    return s;
}

bool is_comment_line(const std::string& s)
{
    const std::size_t i = first_nonspace(s);
    if (i >= s.size()) return false;                                  // blank
    if (s[i] == '*' || s[i] == '#') return true;                      // * canonical, # tolerated
    if (s[i] == '/' && i + 1 < s.size() && s[i + 1] == '/') return true;  // // tolerated
    if (s[i] == '&' && i + 1 < s.size() && s[i + 1] == '&') return true;  // && line-leading
    if (matches_rem(s, i)) return true;                               // REM canonical
    return false;
}

bool is_comment_or_blank(const std::string& s)
{
    const std::size_t i = first_nonspace(s);
    if (i >= s.size()) return true;      // blank
    if (s[i] == ';') return true;        // bare continuation marker
    return is_comment_line(s);
}

} // namespace dottalk::lexing
