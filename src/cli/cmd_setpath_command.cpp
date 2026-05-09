// src/cli/cmd_setpath_command.cpp
// DotTalk++: SETPATH command implementation (CLI)
//
// Usage:
//   SETPATH                       -> show current roots
//   SETPATH RESET                 -> restore defaults (based on current DATA root)
//   SETPATH <SLOT> [TO|=] <path>  -> set slot path
//
// Accepted forms:
//   SET PATH DBF xdbf
//   SET PATH DBF = xdbf
//   SET PATH DBF TO xdbf
//   SET PATH DBF TO = xdbf
//   SET PATH DBF = TO xdbf
//
// Relative path behavior:
//   - DATA resolves relative to the application root (parent of current DATA),
//     not the process working directory.
//   - All other top-level slots resolve relative to the current DATA root.
//   - Validation is non-blocking: missing/wrong-kind paths warn, but assignment
//     still succeeds.
//
// Slots:
//   DATA DBF XDBF INDEXES LMDB WORKSPACES SCHEMAS PROJECTS SCRIPTS TESTS HELP LOGS TMP

// @dottalk.usage v1
// owner: DOT|SETPATH
// command: SETPATH
// category: settings
// status: supported
// noargs: report
// effect: configure
// mutates: path-state
// usage-access: SETPATH USAGE
// summary:
//   Report, reset, or configure DotTalk++ path slots.
//
// usage:
//   SETPATH
//   SETPATH USAGE
//   SETPATH RESET
//   SETPATH DATA <path>
//   SETPATH DBF <path>
//   SETPATH XDBF <path>
//   SETPATH INDEXES <path>
//   SETPATH LMDB <path>
//   SETPATH WORKSPACES <path>
//   SETPATH SCHEMAS <path>
//   SETPATH PROJECTS <path>
//   SETPATH SCRIPTS <path>
//   SETPATH TESTS <path>
//   SETPATH HELP <path>
//   SETPATH LOGS <path>
//   SETPATH TMP <path>
//   SET PATH <slot> <path>
//   SET PATH <slot> TO <path>
//   SET PATH <slot> = <path>
//
// notes:
//   SETPATH with no arguments reports all path slots.
//   RESET restores defaults based on the current DATA root.
//   SET PATH forms route through SETPATH.
//   DATA resolves relative to the application root.
//   Other top-level slots resolve relative to the current DATA root.
//   Validation is non-blocking; missing or wrong-kind paths warn but assignment still succeeds.
//
// risk:
//   mutates_path_state: yes
//   reads_filesystem: validation only
//   mutates_table_data: no
//
// related:
//   SET
//   DDL
//   USE
//   WORKSPACE
//

#include "xbase.hpp"
#include "cli/cmd_setpath.hpp"
#include "common/path_state.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <system_error>

namespace fs = std::filesystem;

namespace {

static fs::path norm_abs(const fs::path& p)
{
    try {
        return fs::absolute(p).lexically_normal();
    } catch (...) {
        return p;
    }
}

static fs::path find_data_root_guess()
{
    fs::path p = fs::current_path();
    for (int i = 0; i < 14; ++i) {
        fs::path cand = p / "data";
        std::error_code ec;
        if (fs::exists(cand, ec) && !ec && fs::is_directory(cand, ec) && !ec) {
            return norm_abs(cand);
        }
        if (!p.has_parent_path()) break;
        fs::path parent = p.parent_path();
        if (parent == p) break;
        p = parent;
    }
    return norm_abs(fs::current_path());
}

static std::string read_word(std::istringstream& iss)
{
    std::string w;
    iss >> w;
    return w;
}

static std::string read_rest(std::istringstream& iss)
{
    std::string s;
    std::getline(iss >> std::ws, s);

    while (!s.empty() &&
           (s.back() == '\r' || s.back() == '\n' ||
            s.back() == ' '  || s.back() == '\t')) {
        s.pop_back();
    }

    size_t i = 0;
    while (i < s.size() && (s[i] == ' ' || s[i] == '\t')) ++i;
    return s.substr(i);
}

static std::string up(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

// Skip optional SET PATH noise tokens: TO and =

static void print_setpath_usage()
{
    std::cout
        << "Usage:\n"
        << "  SETPATH\n"
        << "  SETPATH USAGE\n"
        << "  SETPATH RESET\n"
        << "  SETPATH <slot> [TO|=] <path>\n"
        << "  SET PATH <slot> [TO|=] <path>\n"
        << "Slots:\n"
        << "  DATA DBF XDBF INDEXES LMDB WORKSPACES SCHEMAS PROJECTS SCRIPTS TESTS HELP LOGS TMP\n";
}

static bool is_setpath_usage_request(const std::string& raw)
{
    std::string t = up(raw);
    while (!t.empty() && (t.front() == ' ' || t.front() == '\\t')) t.erase(t.begin());
    while (!t.empty() && (t.back() == ' ' || t.back() == '\\t' || t.back() == '\\r' || t.back() == '\\n')) t.pop_back();
    if (t.rfind("SET PATH ", 0) == 0) {
        t = t.substr(9);
        while (!t.empty() && (t.front() == ' ' || t.front() == '\\t')) t.erase(t.begin());
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void skip_optional_tokens(std::istringstream& iss)
{
    while (true) {
        std::streampos pos = iss.tellg();

        std::string tok;
        if (!(iss >> tok)) {
            return;
        }

        const std::string u = up(tok);
        if (u == "TO" || u == "=") {
            continue;
        }

        iss.clear();
        iss.seekg(pos);
        return;
    }
}

static fs::path resolve_setpath_target(dottalk::paths::Slot slot, const fs::path& input)
{
    using dottalk::paths::Slot;

    if (input.empty()) {
        return input;
    }

    if (input.is_absolute()) {
        return norm_abs(input);
    }

    const auto& st = dottalk::paths::state();

    // DATA is the logical root authority. A relative DATA assignment should be
    // interpreted relative to the current application root (parent of DATA),
    // not the process working directory.
    if (slot == Slot::DATA) {
        fs::path base;
        if (!st.root.empty()) {
            base = st.root;
        } else if (!st.data_root.empty()) {
            base = st.data_root.parent_path();
        } else {
            fs::path guessed = find_data_root_guess();
            base = guessed.empty() ? fs::current_path() : guessed.parent_path();
        }
        return norm_abs(base / input);
    }

    // All top-level logical slots resolve relative to the current DATA root.
    fs::path dataRoot = dottalk::paths::get_slot(Slot::DATA);
    if (dataRoot.empty()) {
        dataRoot = find_data_root_guess();
    }
    return norm_abs(dataRoot / input);
}

// Non-blocking validation: warn, but do not reject assignment.
static void validate_slot_path(dottalk::paths::Slot /*slot*/, const fs::path& p)
{
    std::error_code ec;

    const bool exists = fs::exists(p, ec) && !ec;
    const bool isDir  = exists && fs::is_directory(p, ec) && !ec;

    if (!exists) {
        std::cout << "  warning: path does not exist\n";
        return;
    }

    // All current path slots are directory-oriented.
    if (!isDir) {
        std::cout << "  warning: expected directory, found file\n";
        return;
    }
}

} // namespace

void cmd_SETPATH(xbase::DbArea&, std::istringstream& iss)
{
    const std::string raw_args = iss.str();

    std::string a1 = read_word(iss);
    if (is_setpath_usage_request(raw_args) || is_setpath_usage_request(a1)) {
        print_setpath_usage();
        return;
    }

    if (a1.empty()) {
        std::cout << dottalk::paths::dump();
        return;
    }

    const std::string u1 = up(a1);

    if (u1 == "RESET") {
        if (dottalk::paths::state().data_root.empty()) {
            dottalk::paths::init_defaults(find_data_root_guess());
        } else {
            dottalk::paths::reset();
        }
        std::cout << "SETPATH: reset to defaults.\n";
        std::cout << dottalk::paths::dump();
        return;
    }

    dottalk::paths::Slot slot{};
    if (!dottalk::paths::slot_from_string(a1, slot)) {
        std::cout << "SETPATH: unknown slot: " << a1 << "\n";
        print_setpath_usage();
        return;
    }

    skip_optional_tokens(iss);

    const std::string path_value = read_rest(iss);
    if (path_value.empty()) {
        print_setpath_usage();
        return;
    }

    const fs::path finalPath = resolve_setpath_target(slot, fs::path(path_value));
    dottalk::paths::set_slot(slot, finalPath);

    const fs::path resolved = dottalk::paths::get_slot(slot);

    std::cout << "SETPATH: "
              << dottalk::paths::slot_name(slot)
              << " = "
              << resolved.string()
              << "\n";

    validate_slot_path(slot, resolved);
}
