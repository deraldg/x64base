// src/cli/expr/fn_string.cpp
// FoxPro-style string builtins for DotTalk++
//
// Notes:
// - Functions operate on string-based argument/return model (current engine).
// - EMPTY() implements practical FoxPro semantics over string inputs.
// - TRANSFORM() is currently a pass-through placeholder.

#include "cli/expr/fn_string.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <iomanip>
#include <locale>
#include <sstream>
#include <string>
#include <vector>

namespace dottalk::expr {

// --------------------------------------------------
// Core helpers
// --------------------------------------------------

static std::string dt_upper(const std::vector<std::string>& args) {
    if (args.empty()) return {};
    std::string s = args[0];
    for (char& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

static std::string dt_lower(const std::vector<std::string>& args) {
    if (args.empty()) return {};
    std::string s = args[0];
    for (char& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return s;
}

static std::string dt_alltrim(const std::vector<std::string>& args) {
    if (args.empty()) return {};
    const std::string& s = args[0];
    auto start = s.find_first_not_of(" \t");
    if (start == std::string::npos) return {};
    auto end = s.find_last_not_of(" \t");
    return s.substr(start, end - start + 1);
}

static std::string dt_ltrim(const std::vector<std::string>& args) {
    if (args.empty()) return {};
    const std::string& s = args[0];
    auto start = s.find_first_not_of(" \t");
    return (start == std::string::npos) ? std::string{} : s.substr(start);
}

static std::string dt_rtrim(const std::vector<std::string>& args) {
    if (args.empty()) return {};
    const std::string& s = args[0];
    auto end = s.find_last_not_of(" \t");
    return (end == std::string::npos) ? std::string{} : s.substr(0, end + 1);
}

static std::string dt_left(const std::vector<std::string>& args) {
    if (args.size() < 2) return {};
    const std::string& s = args[0];
    int n = std::stoi(args[1]);
    if (n <= 0) return {};
    return s.substr(0, std::min<std::size_t>(n, s.size()));
}

static std::string dt_right(const std::vector<std::string>& args) {
    if (args.size() < 2) return {};
    const std::string& s = args[0];
    int n = std::stoi(args[1]);
    if (n <= 0) return {};
    return (n >= static_cast<int>(s.size())) ? s : s.substr(s.size() - n);
}

static std::string dt_substr(const std::vector<std::string>& args) {
    if (args.size() < 2) return {};
    const std::string& s = args[0];
    int start = std::stoi(args[1]);
    if (start <= 0) start = 1;
    std::size_t pos = static_cast<std::size_t>(start - 1);
    if (pos >= s.size()) return {};
    std::size_t len = s.size() - pos;
    if (args.size() >= 3) len = std::stoi(args[2]);
    return s.substr(pos, len);
}

static std::string dt_len(const std::vector<std::string>& args) {
    return args.empty() ? "0" : std::to_string(args[0].size());
}

static std::string dt_concat(const std::vector<std::string>& args) {
    std::string out;
    std::size_t total = 0;
    for (const auto& arg : args) total += arg.size();
    out.reserve(total);
    for (const auto& arg : args) out += arg;
    return out;
}

// --------------------------------------------------
// EMPTY() — corrected implementation
// --------------------------------------------------

static std::string dt_empty(const std::vector<std::string>& args) {
    if (args.empty()) return ".T.";

    std::string s = args[0];

    // Strip quotes if present
    if (s.size() >= 2) {
        if ((s.front() == '"' && s.back() == '"') ||
            (s.front() == '\'' && s.back() == '\'')) {
            s = s.substr(1, s.size() - 2);
        }
    }

    // Blank / whitespace
    if (s.find_first_not_of(" \t\r\n") == std::string::npos)
        return ".T.";

    // Logical false
    if (s == ".F." || s == "F" || s == "false" || s == "FALSE")
        return ".T.";

    // Numeric zero
    try {
        double v = std::stod(s);
        if (v == 0.0) return ".T.";
    } catch (...) {}

    return ".F.";
}

// --------------------------------------------------
// SOUNDEX() — classic 4-character phonetic code
// --------------------------------------------------

static std::string dt_soundex(const std::vector<std::string>& args) {
    if (args.empty()) return {};

    std::string letters;
    for (char ch : args[0]) {
        unsigned char uch = static_cast<unsigned char>(ch);
        if (std::isalpha(uch)) {
            letters.push_back(static_cast<char>(std::toupper(uch)));
        }
    }

    if (letters.empty()) return {};

    auto code_for = [](char c) -> char {
        switch (c) {
            case 'B': case 'F': case 'P': case 'V': return '1';
            case 'C': case 'G': case 'J': case 'K': case 'Q':
            case 'S': case 'X': case 'Z': return '2';
            case 'D': case 'T': return '3';
            case 'L': return '4';
            case 'M': case 'N': return '5';
            case 'R': return '6';
            default: return '0';
        }
    };

    std::string out;
    out.reserve(4);
    out.push_back(letters[0]);

    // Standard Soundex rule:
    // - Keep first letter.
    // - Vowels/Y reset duplicate-code suppression.
    // - H/W do not reset duplicate-code suppression.
    // This preserves classic examples such as ASHCRAFT -> A261,
    // TYMCZAK -> T522, and PFISTER -> P236.
    char prev = code_for(letters[0]);

    for (std::size_t i = 1; i < letters.size() && out.size() < 4; ++i) {
        char c = letters[i];
        char code = code_for(c);

        if (c == 'H' || c == 'W') {
            continue;
        }

        if (code == '0') {
            prev = '0';
            continue;
        }

        if (code != prev) {
            out.push_back(code);
        }

        prev = code;
    }

    while (out.size() < 4) {
        out.push_back('0');
    }

    return out.substr(0, 4);
}

// --------------------------------------------------
// Search functions
// --------------------------------------------------

static std::string dt_at(const std::vector<std::string>& args) {
    if (args.size() < 2) return "0";
    auto pos = args[1].find(args[0]);
    return (pos == std::string::npos) ? "0" : std::to_string(pos + 1);
}

static std::string dt_rat(const std::vector<std::string>& args) {
    if (args.size() < 2) return "0";
    auto pos = args[1].rfind(args[0]);
    return (pos == std::string::npos) ? "0" : std::to_string(pos + 1);
}

// --------------------------------------------------
// Replace / transform
// --------------------------------------------------

static std::string dt_strtran(const std::vector<std::string>& args) {
    if (args.size() < 3) return args.empty() ? "" : args[0];

    std::string out = args[0];
    const std::string& find = args[1];
    const std::string& repl = args[2];

    std::size_t pos = 0;
    while ((pos = out.find(find, pos)) != std::string::npos) {
        out.replace(pos, find.length(), repl);
        pos += repl.length();
    }
    return out;
}

static std::string dt_chrtran(const std::vector<std::string>& args) {
    if (args.size() < 3) return args.empty() ? "" : args[0];

    std::string out = args[0];
    const std::string& from = args[1];
    const std::string& to = args[2];

    for (char& c : out) {
        auto pos = from.find(c);
        if (pos != std::string::npos) {
            if (pos < to.size())
                c = to[pos];
            else
                c = '\0';
        }
    }

    out.erase(std::remove(out.begin(), out.end(), '\0'), out.end());
    return out;
}

// --------------------------------------------------
// Other utilities
// --------------------------------------------------

static std::string dt_chr(const std::vector<std::string>& args) {
    return args.empty() ? "" : std::string(1, static_cast<char>(std::stoi(args[0])));
}

static std::string dt_asc(const std::vector<std::string>& args) {
    return args.empty() ? "0" : std::to_string(static_cast<unsigned char>(args[0][0]));
}

static std::string dt_space(const std::vector<std::string>& args) {
    return args.empty() ? "" : std::string(std::stoi(args[0]), ' ');
}

static std::string dt_replicate(const std::vector<std::string>& args) {
    if (args.size() < 2) return "";
    std::string out;
    for (int i = 0; i < std::stoi(args[1]); ++i)
        out += args[0];
    return out;
}

static std::string dt_val(const std::vector<std::string>& args) {
    if (args.empty()) return "0";
    try { return std::to_string(std::stod(args[0])); }
    catch (...) { return "0"; }
}

static std::string dt_str(const std::vector<std::string>& args) {
    if (args.empty()) return "";

    double value = 0.0;
    try {
        value = std::stod(args[0]);
    } catch (...) {
        return "";
    }

    int width = 10;
    int decimals = 0;
    try {
        if (args.size() >= 2) width = std::stoi(args[1]);
        if (args.size() >= 3) decimals = std::stoi(args[2]);
    } catch (...) {
        return "";
    }

    if (width <= 0) return "";
    if (decimals < 0) decimals = 0;

    std::ostringstream oss;
    oss.imbue(std::locale::classic());   // AIF-031: no thousands grouping in STR() output
    oss << std::fixed << std::setprecision(decimals) << value;
    const std::string rendered = oss.str();

    if (static_cast<int>(rendered.size()) > width) {
        return std::string(static_cast<std::size_t>(width), '*');
    }

    return std::string(static_cast<std::size_t>(width - static_cast<int>(rendered.size())), ' ')
         + rendered;
}

static std::string dt_transform(const std::vector<std::string>& args) {
    return args.empty() ? "" : args[0];
}

// --------------------------------------------------
// Registry
// --------------------------------------------------

static const BuiltinFnSpec kStringFns[] = {
    { "UPPER",1,1,&dt_upper },
    { "LOWER",1,1,&dt_lower },
    { "ALLTRIM",1,1,&dt_alltrim },
    { "LTRIM",1,1,&dt_ltrim },
    { "RTRIM",1,1,&dt_rtrim },
    { "TRIM",1,1,&dt_rtrim },
    { "LEFT",2,2,&dt_left },
    { "RIGHT",2,2,&dt_right },
    { "SUBSTR",2,3,&dt_substr },
    { "LEN",1,1,&dt_len },
    { "CONCAT",1,32,&dt_concat },
    { "STRCAT",1,32,&dt_concat },
    { "EMPTY",1,1,&dt_empty },
    { "SOUNDEX",1,1,&dt_soundex },
    { "AT",2,2,&dt_at },
    { "RAT",2,2,&dt_rat },
    { "STRTRAN",3,3,&dt_strtran },
    { "CHRTRAN",3,3,&dt_chrtran },
    { "CHR",1,1,&dt_chr },
    { "ASC",1,1,&dt_asc },
    { "SPACE",1,1,&dt_space },
    { "REPLICATE",2,2,&dt_replicate },
    { "VAL",1,1,&dt_val },
    { "STR",1,3,&dt_str },
    { "TRANSFORM",1,2,&dt_transform }
};

const BuiltinFnSpec* string_fn_specs() { return kStringFns; }
std::size_t string_fn_specs_count() { return sizeof(kStringFns)/sizeof(kStringFns[0]); }

} // namespace
