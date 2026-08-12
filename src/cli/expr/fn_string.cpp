// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/expr/fn_string.cpp
// FoxPro-style string builtins for DotTalk++
//
// Notes:
// - Functions operate on string-based argument/return model (current engine).
// - EMPTY() implements practical FoxPro semantics over string inputs.
// - TRANSFORM() is currently a pass-through placeholder.

#include "cli/expr/fn_string.hpp"
#include "cli/path_resolver.hpp"
#include "cli/text_match.hpp"
#include "common/path_state.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <filesystem>
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
// FILE() -- filesystem existence probe (FoxPro-compatible name)
// --------------------------------------------------
// Added 2026-08-12 for the WORKSPACE WRITEBACK refusal arms (WB_T5/WB_T6):
// "the aborted target does not exist afterward" needs a by-value read of the
// filesystem, and the catalog had no such probe. Deliberately broader than
// VFP (which is files-only): returns .T. for ANY filesystem entry, directory
// included, because an absence proof wants the widest possible detector --
// "nothing means nothing" fails on a leftover empty directory too.
// Relative paths resolve through paths::resolve_in_slot, the same rule every
// other path token in the engine uses: absolute stays absolute, a token with
// separators is DATA-root-relative, a bare name sits in the DBF slot.
//
// Corrected 2026-08-12, same day it was added. The first cut resolved against
// the process CWD and this comment claimed that "matched" WORKSPACE WRITEBACK
// and ERASE. It did -- all three were wrong together, and being wrong in
// unison is not a specification. SET PATH resolved the same spelling against
// DATA, so a marker of the form FILE("DBF/wbabort/STUDENTS.dbf") probed a
// different directory than the writeback it was auditing. It agreed only
// because datarun.ps1 runs with cwd = DATA. An absence proof that reads the
// wrong directory always reports absence.
//
// Registered here AND in function_catalog.cpp in the same commit, per the
// kDateFns rule (execution table and documentation table must not drift).

static std::string dt_file(const std::vector<std::string>& args) {
    if (args.empty()) return ".F.";

    std::string s = args[0];

    // Strip quotes if present (same convention as dt_empty)
    if (s.size() >= 2) {
        if ((s.front() == '"' && s.back() == '"') ||
            (s.front() == '\'' && s.back() == '\'')) {
            s = s.substr(1, s.size() - 2);
        }
    }

    // Trim surrounding whitespace; a blank path is not a path
    const auto b = s.find_first_not_of(" \t\r\n");
    if (b == std::string::npos) return ".F.";
    const auto e = s.find_last_not_of(" \t\r\n");
    s = s.substr(b, e - b + 1);

    // Cross-OS: scripts spell paths either way; POSIX does not treat '\' as
    // a separator (house pattern, see shell.cpp / cmd_setorder.cpp).
    std::replace(s.begin(), s.end(), '\\', '/');

    std::error_code ec;
    const std::filesystem::path probe = dottalk::paths::resolve_in_slot(
        dottalk::paths::get_slot(dottalk::paths::Slot::DBF), s);
    const bool present = std::filesystem::exists(probe, ec) && !ec;
    return present ? ".T." : ".F.";
}

// --------------------------------------------------
// SOUNDEX() — classic 4-character phonetic code
// --------------------------------------------------

static std::string dt_soundex(const std::vector<std::string>& args) {
    if (args.empty()) return {};
    // Canonical Soundex lives in cli/text_match.hpp (shared with HELP did-you-mean).
    // Preserves classic examples (ASHCRAFT -> A261, TYMCZAK -> T522, PFISTER -> P236).
    return dottalk::text::soundex(args[0]);
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

// STUFF(cExpr, nStart, nLen, cRepl): replace nLen chars of cExpr at 1-based nStart
// with cRepl (nLen 0 inserts).
static std::string dt_stuff(const std::vector<std::string>& args) {
    if (args.size() < 4) return args.empty() ? "" : args[0];
    std::string s = args[0];
    int start = 0, len = 0;
    try { start = std::stoi(args[1]); len = std::stoi(args[2]); }
    catch (...) { return s; }
    const std::string& repl = args[3];
    if (start < 1) start = 1;
    std::size_t pos = static_cast<std::size_t>(start - 1);
    if (pos > s.size()) pos = s.size();
    if (len < 0) len = 0;
    std::size_t n = static_cast<std::size_t>(len);
    if (pos + n > s.size()) n = s.size() - pos;
    s.replace(pos, n, repl);
    return s;
}

// Pad helpers: cExpr to nLen with cFill (default space); truncate to nLen if longer.
static std::string dt_padl(const std::vector<std::string>& args) {
    if (args.size() < 2) return args.empty() ? "" : args[0];
    std::string s = args[0];
    int len = 0;
    try { len = std::stoi(args[1]); } catch (...) { return s; }
    char fill = (args.size() >= 3 && !args[2].empty()) ? args[2][0] : ' ';
    if (len < 0) len = 0;
    std::size_t L = static_cast<std::size_t>(len);
    if (s.size() >= L) return s.substr(0, L);
    return std::string(L - s.size(), fill) + s;
}

static std::string dt_padr(const std::vector<std::string>& args) {
    if (args.size() < 2) return args.empty() ? "" : args[0];
    std::string s = args[0];
    int len = 0;
    try { len = std::stoi(args[1]); } catch (...) { return s; }
    char fill = (args.size() >= 3 && !args[2].empty()) ? args[2][0] : ' ';
    if (len < 0) len = 0;
    std::size_t L = static_cast<std::size_t>(len);
    if (s.size() >= L) return s.substr(0, L);
    return s + std::string(L - s.size(), fill);
}

static std::string dt_padc(const std::vector<std::string>& args) {
    if (args.size() < 2) return args.empty() ? "" : args[0];
    std::string s = args[0];
    int len = 0;
    try { len = std::stoi(args[1]); } catch (...) { return s; }
    char fill = (args.size() >= 3 && !args[2].empty()) ? args[2][0] : ' ';
    if (len < 0) len = 0;
    std::size_t L = static_cast<std::size_t>(len);
    if (s.size() >= L) return s.substr(0, L);
    std::size_t total = L - s.size();
    std::size_t left = total / 2;
    return std::string(left, fill) + s + std::string(total - left, fill);
}

// PROPER(cExpr): title-case -- first letter of each word up, rest down.
static std::string dt_proper(const std::vector<std::string>& args) {
    if (args.empty()) return {};
    std::string s = args[0];
    bool at_start = true;
    for (char& c : s) {
        unsigned char u = static_cast<unsigned char>(c);
        if (std::isalpha(u)) {
            c = at_start ? static_cast<char>(std::toupper(u))
                         : static_cast<char>(std::tolower(u));
            at_start = false;
        } else {
            at_start = true;
        }
    }
    return s;
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
    { "FILE",1,1,&dt_file },
    { "SOUNDEX",1,1,&dt_soundex },
    { "AT",2,2,&dt_at },
    { "RAT",2,2,&dt_rat },
    { "STRTRAN",3,3,&dt_strtran },
    { "CHRTRAN",3,3,&dt_chrtran },
    { "STUFF",4,4,&dt_stuff },
    { "PADL",2,3,&dt_padl },
    { "PADR",2,3,&dt_padr },
    { "PADC",2,3,&dt_padc },
    { "PROPER",1,1,&dt_proper },
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
