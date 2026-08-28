// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "shell_var_utils.hpp"

#include "cli/command_output.hpp"
#include "textio.hpp"
#include "shell_eval_utils.hpp"  // for VarBangEval, eval_for_varbang, serialize_varbang_value
#include "common/path_state.hpp"  // slot_from_string / get_slot -- the _SLOT authority
#include <algorithm>
#include <cctype>
#include <iomanip>    // for std::setprecision
#include <sstream>
#include <string>
#include <unordered_map>

namespace dottalk {

static std::unordered_map<std::string, std::string>& shell_vars() {
    static std::unordered_map<std::string, std::string> vars;
    return vars;
}

bool is_ident_start(char c) {
    return (std::isalpha(static_cast<unsigned char>(c)) || c == '_');
}

bool is_ident_char(char c) {
    return (std::isalnum(static_cast<unsigned char>(c)) || c == '_');
}

// ---------------------------------------------------------------------------
// ENGINE-OWNED VARIABLES: the leading underscore is reserved.
//
// Convention, 2026-08-28. `_NAME` belongs to the engine; every other name
// belongs to the user. Chosen because it is what xBase already does -- FoxPro
// system memory variables are _TALLY, _SCREEN, _PAGENO, _CLIPTEXT -- so it
// costs a reader of this dialect nothing to learn. It was also measured free:
// no registered command, alias, subcommand or function in this tree begins
// with an underscore, and before this change the engine set NO shell variables
// at all, so the whole namespace was user-owned and `_` was unclaimed.
//
// `_<SLOT>` IS DERIVED ON READ, NEVER STORED. It is deliberately NOT a copy
// kept in sync with the path slots: a synced copy is a second declaration of
// one fact, and a second declaration that can drift is the defect this project
// keeps finding. Resolving from paths::state() at expansion time cannot drift,
// because there is nothing to keep in step.
//
// Every spelling slot_from_string accepts works, so &_WORKSPACES, &_DBF,
// &_TMP and the aliases (&_CURRENT, &_PUBLIC, ...) all resolve. This gives a
// script the sentence it could not previously say: "the slot, wherever it
// currently points."
static bool resolve_engine_var(const std::string& name, std::string& out)
{
    if (name.size() < 2 || name[0] != '_') return false;

    dottalk::paths::Slot slot;
    if (!dottalk::paths::slot_from_string(name.substr(1), slot)) return false;

    out = dottalk::paths::get_slot(slot).string();
    return true;
}

bool expand_macros_outside_quotes(const std::string& in,
                                  std::string& out,
                                  std::string& err_name)
{
    out.clear();
    out.reserve(in.size() + 16);
    bool in_single = false, in_double = false, esc = false;
    for (size_t i = 0; i < in.size(); ++i) {
        const char c = in[i];
        if (esc) { esc = false; out.push_back(c); continue; }
        if (c == '\\') { esc = true; out.push_back(c); continue; }
        if (!in_double && c == '\'') { in_single = !in_single; out.push_back(c); continue; }
        if (!in_single && c == '\"') { in_double = !in_double; out.push_back(c); continue; }
        if (!in_single && !in_double && c == '&') {
            if (i + 1 < in.size() && is_ident_start(in[i + 1])) {
                size_t j = i + 2;
                while (j < in.size() && is_ident_char(in[j])) ++j;
                const std::string name = in.substr(i + 1, j - (i + 1));
                const std::string key = textio::up(name);

                // Engine-owned names are answered FIRST and from the
                // authority, so no user variable can shadow one.
                std::string engine_value;
                if (resolve_engine_var(key, engine_value)) {
                    out.append(engine_value);
                    i = j - 1;
                    continue;
                }

                auto it = shell_vars().find(key);
                if (it == shell_vars().end()) {
                    err_name = name;
                    return false;
                }
                out.append(it->second);
                i = j - 1;
                continue;
            }
        }
        out.push_back(c);
    }
    return true;
}

std::string quote_dottalk_string(const std::string& raw) {
    std::string out;
    out.reserve(raw.size() + 2);
    out.push_back('"');
    for (char c : raw) {
        if (c == '"') out.append("\"\"");
        else out.push_back(c);
    }
    out.push_back('"');
    return out;
}

VarCmdResult try_handle_var_command(xbase::DbArea& area, const std::string& preparedLine)
{
    VarCmdResult r;
    std::istringstream ss(preparedLine);
    std::string cmd;
    ss >> cmd;
    if (cmd.empty()) return r;
    const std::string U = textio::up(cmd);
    std::string sub;
    ss >> sub;
    const std::string subU = textio::up(sub);
    const bool var_bang = (subU == "VAR!");
    if (!(subU == "VAR" || var_bang)) return r;
    r.handled = true;
    std::string rest;
    std::getline(ss, rest);
    rest = textio::trim(rest);
    if (U == "SET") {
        const size_t eq = rest.find('=');
        if (eq == std::string::npos) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetVarUsageLine);
            r.ok = false;
            return r;
        }
        std::string name = textio::trim(rest.substr(0, eq));
        std::string val = textio::trim(rest.substr(eq + 1));
        if (name.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetVarUsageLine);
            r.ok = false;
            return r;
        }
        // The reserved prefix. Without this the convention is a suggestion:
        // a user could SET VAR _WORKSPACES = anything and every script using
        // &_WORKSPACES would then read a value the engine never sanctioned --
        // silently, because expansion would still succeed. Refused at the one
        // place names enter the store. The message says WHY, not just "no",
        // because a bare refusal for a name that looks perfectly legal is the
        // kind of error people file bugs about.
        if (name[0] == '_') {
            cli::cmdout::print_line(
                "SET VAR: '" + name + "' is refused -- a leading underscore is "
                "reserved for engine-owned variables (the xBase convention: "
                "_TALLY, _SCREEN). _<SLOT> names such as &_WORKSPACES are "
                "answered from the path slots themselves and cannot be "
                "assigned. Choose a name that does not start with '_'.");
            r.ok = false;
            return r;
        }
        if (!is_ident_start(name[0])) {
            cli::cmdout::print_prefixed_message(
                "SET VAR",
                dottalk::helpdata::MessageId::VarInvalidName,
                {{"name", name}});
            r.ok = false;
            return r;
        }
        for (char c : name) {
            if (!is_ident_char(c)) {
                cli::cmdout::print_prefixed_message(
                    "SET VAR",
                    dottalk::helpdata::MessageId::VarInvalidName,
                    {{"name", name}});
                r.ok = false;
                return r;
            }
        }
        if (var_bang) {
            VarBangEval ev;
            std::string err;
            if (!eval_for_varbang(area, val, ev, err)) {
                cli::cmdout::print_prefixed_message(
                    "SET VAR!",
                    dottalk::helpdata::MessageId::VarBangEvalError,
                    {{"detail", err}});
                r.ok = false;
                return r;
            }
            shell_vars()[textio::up(name)] = serialize_varbang_value(ev);
            return r;
        }
        shell_vars()[textio::up(name)] = val;
        return r;
    }
    if (U == "SHOW") {
        if (rest.empty()) {
            std::vector<std::string> keys;
            keys.reserve(shell_vars().size());
            for (const auto& kv : shell_vars()) keys.push_back(kv.first);
            std::sort(keys.begin(), keys.end());
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::VarsDefinedCount,
                {{"count", std::to_string(keys.size())}});
            for (const auto& k : keys) {
                cli::cmdout::print_line(" " + k + " = " + shell_vars()[k]);
            }
            return r;
        }
        std::istringstream rs(rest);
        std::string name, extra;
        rs >> name;
        rs >> extra;
        if (name.empty() || !extra.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ShowVarUsageLine);
            r.ok = false;
            return r;
        }
        const std::string key = textio::up(name);
        auto it = shell_vars().find(key);
        if (it == shell_vars().end()) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::VarNotDefined,
                {{"name", name}});
            r.ok = false;
            return r;
        }
        cli::cmdout::print_line(key + " = " + it->second);
        return r;
    }
    if (U == "CLEAR") {
        if (rest.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ClearVarUsageLine);
            r.ok = false;
            return r;
        }
        std::istringstream rs(rest);
        std::string name, extra;
        rs >> name;
        rs >> extra;
        if (name.empty() || !extra.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ClearVarUsageLine);
            r.ok = false;
            return r;
        }
        const std::string key = textio::up(name);
        if (key == "ALL") {
            shell_vars().clear();
            return r;
        }
        auto it = shell_vars().find(key);
        if (it == shell_vars().end()) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::VarNotDefined,
                {{"name", name}});
            r.ok = false;
            return r;
        }
        shell_vars().erase(it);
        return r;
    }
    cli::cmdout::print_message(dottalk::helpdata::MessageId::VarCommandUsageLine);
    r.ok = false;
    return r;
}

} // namespace dottalk
