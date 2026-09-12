// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

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

// @dottalk.usage.voluntary v1
// NOT UNDER CONTRACT -- voluntary description, offered not promised.
// Nothing verifies this block and nothing may fail because of it.
// The binding identity for this surface is the @dottalk.subusage
// contract on its ladder arm in src/cli/cmd_set.cpp.
// owner: DOT|SET PATH
// documents: SET PATH
// category: settings
// status: supported
// noargs: report
// effect: configure
// mutates: path-state
// usage-access: SET PATH USAGE
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
#include "cli/command_output.hpp"
#include "cli/cmd_setpath.hpp"
#include "common/path_state.hpp"
#include "workarea_util.hpp"
#include "xbase/workspace_membership.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <vector>
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

    // If cwd IS the data directory (e.g. a test harness sets cwd=.../dottalkpp/data),
    // use it directly. Otherwise the loop below forms `cwd / "data"`, which resolves
    // to a doubled `.../data/data` if any stray `data` child happens to exist.
    // Marker: a real data dir contains a `dbf` subdirectory.
    {
        std::error_code ec;
        if (p.filename() == "data" && fs::is_directory(p / "dbf", ec) && !ec) {
            return norm_abs(p);
        }
    }

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
    cli::cmdout::print_message(dottalk::helpdata::MessageId::SetPathUsageText);
}

static bool is_setpath_usage_request(const std::string& raw)
{
    std::string t = up(raw);
    while (!t.empty() && (t.front() == ' ' || t.front() == '\t')) t.erase(t.begin());
    while (!t.empty() && (t.back() == ' ' || t.back() == '\t' || t.back() == '\r' || t.back() == '\n')) t.pop_back();
    if (t.rfind("SET PATH ", 0) == 0) {
        t = t.substr(9);
        while (!t.empty() && (t.front() == ' ' || t.front() == '\t')) t.erase(t.begin());
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

// ---------------------------------------------------------------------------
// R131 Q1 -- SET PATH <slot> <value> IN <ws-or-handle>
//
// `IN` IS ALREADY THE HOUSE WORD for "target something other than current" --
// SET ORDER TAG <tag> IN <alias> and USE <table> IN <n>. Both of those take
// AREAS. After SET PATH it can only mean a workspace, because a path has no
// per-area meaning, so the keyword is reused with no namespace collision.
//
// WHY AN EXPLICIT CLAUSE RATHER THAN A PROMPT (R131 sec 7): the first form of
// this ruling was a y/n confirmation fired when more than one workspace was
// open. It was withdrawn on measurement -- this engine has NO script-mode
// prompt suppression (g_suppress_prompts is set only on the QUIT path), so a
// prompt inside a .dts blocks or eats the next script line as its answer, and
// open_mcc_and_cascade.dts would have tripped it on the first script written
// against this ruling. One grammar, no mode-dependent behaviour.
//
// AMBIGUITY, DISCLOSED RATHER THAN DISCOVERED: the clause is recognised only
// as the LAST TWO tokens of the value. A directory genuinely ending in
// "... IN <something>" would be misread. That is judged acceptable because the
// alternative -- a separator that cannot occur in a path -- is a new
// punctuation rule for one clause, and because the misread is loud: the slot
// is assigned a shorter path and SETPATH prints the resolved result.
static bool split_trailing_in_clause(std::string& value, std::string& ws_token)
{
    ws_token.clear();
    // Tokenise on whitespace; we need the last two.
    std::vector<std::string> toks;
    {
        std::istringstream ts(value);
        std::string t;
        while (ts >> t) toks.push_back(t);
    }
    if (toks.size() < 3) return false;                 // slot value IN ws needs a value too
    if (up(toks[toks.size() - 2]) != "IN") return false;

    ws_token = toks.back();
    // Rebuild the value from everything before the IN.
    std::string rebuilt;
    for (std::size_t i = 0; i + 2 < toks.size(); ++i) {
        if (!rebuilt.empty()) rebuilt += ' ';
        rebuilt += toks[i];
    }
    if (rebuilt.empty()) { ws_token.clear(); return false; }
    value = rebuilt;
    return true;
}

// Name or handle, the same two forms WORKSPACE SWITCH accepts. 0 = no match.
static std::uint64_t resolve_ws_token(const std::string& tok)
{
    if (tok.empty()) return 0;
    const bool all_digits =
        std::all_of(tok.begin(), tok.end(),
                    [](unsigned char c) { return std::isdigit(c) != 0; });
    if (all_digits) {
        try {
            const std::uint64_t h = std::stoull(tok);
            return xbase::workspace::exists(h) ? h : 0;
        } catch (...) { return 0; }
    }
    return xbase::workspace::find_by_name_ci(tok);
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
        cli::cmdout::print_message(dottalk::helpdata::MessageId::SetPathWarnMissingText);
        return;
    }

    // All current path slots are directory-oriented.
    if (!isDir) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::SetPathWarnExpectedDirectoryText);
        return;
    }
}

} // namespace

void cmd_SETPATH(xbase::DbArea&, std::istringstream& iss)
{
    const std::string raw_args = iss.str();

    std::string a1 = read_word(iss);
    // Test the complete argument string, not the first token alone. HELP is
    // both a usage alias and a writable path-slot name: `SETPATH HELP` asks
    // for usage, while `SETPATH HELP <path>` must assign the HELP slot.
    if (is_setpath_usage_request(raw_args)) {
        print_setpath_usage();
        return;
    }

    if (a1.empty()) {
        cli::cmdout::print_line(dottalk::paths::dump());
        return;
    }

    const std::string u1 = up(a1);

    if (u1 == "RESET") {
        if (dottalk::paths::state().data_root.empty()) {
            dottalk::paths::init_defaults(find_data_root_guess());
        } else {
            dottalk::paths::reset();
        }
        cli::cmdout::print_prefixed_message(
            "SETPATH",
            dottalk::helpdata::MessageId::SetPathResetText);
        cli::cmdout::print_line(dottalk::paths::dump());
        return;
    }

    dottalk::paths::Slot slot{};
    if (!dottalk::paths::slot_from_string(a1, slot)) {
        cli::cmdout::print_prefixed_message(
            "SETPATH",
            dottalk::helpdata::MessageId::SetPathUnknownSlotText,
            {{"slot", a1}});
        print_setpath_usage();
        return;
    }

    skip_optional_tokens(iss);

    std::string path_value = read_rest(iss);
    if (path_value.empty()) {
        print_setpath_usage();
        return;
    }

    // R131 Q1. Peel a trailing IN <ws-or-handle> off the value before the path
    // is resolved, so the clause never reaches the filesystem.
    std::string ws_token;
    const bool has_in = split_trailing_in_clause(path_value, ws_token);

    std::uint64_t target_ws = 0;
    if (has_in) {
        target_ws = resolve_ws_token(ws_token);
        if (target_ws == 0) {
            std::cout << "SETPATH: no such workspace: " << ws_token << "\n"
                      << "  Nothing was assigned. IN takes a workspace name or "
                         "handle, as WORKSPACE SWITCH does.\n";
            return;
        }
    }

    const fs::path finalPath = resolve_setpath_target(slot, fs::path(path_value));

    // THE EXPLICIT FORM DOES NOT MOVE THE SESSION unless it is aimed at the
    // workspace the session is standing in. That is the whole point of the
    // clause: R131 sec 7 records the misordering hazard it exists to answer --
    // NEW then SET PATH then SWITCH binds the OLD workspace, and the remedy is
    // to NAME the target rather than to rely on standing in it.
    const std::uint64_t cur = xbase::workspace::current_handle();
    const bool touches_session = (!has_in || target_ws == cur);

    if (touches_session) dottalk::paths::set_slot(slot, finalPath);

    const fs::path resolved =
        touches_session ? dottalk::paths::get_slot(slot) : finalPath;

    // R131 sec 1: SET PATH RETARGETS THE CURRENT WORKSPACE, NOT THE SESSION.
    // The bare form binds whoever is current -- which also stamps DEFAULT the
    // first time anyone sets a path in a fresh session, so DEFAULT never has
    // to be stamped from a foreign workspace's slots later.
    if (has_in) {
        std::string d, i, l;
        xbase::workspace::roots_of(target_ws, d, i, l);
        if (d.empty() || i.empty() || l.empty()) {
            // Not yet stamped: fill from the session first so the write below
            // sets ONE slot rather than leaving the other two blank. Roots move
            // as a set of three; a half-stamped workspace is the sec 3 defect.
            d = dottalk::paths::get_slot(dottalk::paths::Slot::DBF).string();
            i = dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES).string();
            l = dottalk::paths::get_slot(dottalk::paths::Slot::LMDB).string();
        }
        switch (slot) {
            case dottalk::paths::Slot::DBF:     d = resolved.string(); break;
            case dottalk::paths::Slot::INDEXES: i = resolved.string(); break;
            case dottalk::paths::Slot::LMDB:    l = resolved.string(); break;
            default: break;   // a slot R131 does not govern; nothing to bind
        }
        xbase::workspace::set_roots(target_ws, d, i, l);
    } else {
        cli::workspace_roots_bind_from_slots(cur);
    }

    cli::cmdout::print_prefixed_message(
        "SETPATH",
        dottalk::helpdata::MessageId::SetPathAssignedText,
        {
            {"slot", dottalk::paths::slot_name(slot)},
            {"path", resolved.string()}
        });

    if (has_in) {
        std::cout << "  bound to workspace " << target_ws << " ("
                  << xbase::workspace::name_of(target_ws) << ")";
        if (!touches_session)
            std::cout << "; the session's own slots are unchanged";
        std::cout << ".\n";
    }

    if (touches_session) validate_slot_path(slot, resolved);
}
