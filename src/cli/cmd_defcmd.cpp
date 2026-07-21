// @dottalk.usage v1
// owner: DOT|DEFCMD
// command: DEFCMD
// category: diagnostics
// status: experimental
// noargs: usage
// effect: mutates-command-registry
// mutates: none
// usage-access: DEFCMD USAGE
// summary:
//   Define an ephemeral, session-only scratch command at runtime, without a
//   rebuild or source edit. Intended as an AI/developer testbed for verifying
//   token parsing and command routing.
//
// usage:
//   DEFCMD USAGE
//   DEFCMD LIST
//   DEFCMD <NAME> = <body-text>
//   DEFCMD <NAME> <body-text>
//
// examples:
//   DEFCMD PING = pong
//   DEFCMD GREET = hello there
//
// notes:
//   Scratch commands live only for the current session and are never written
//   to disk; they vanish on EXIT.
//   Invoking a scratch command prints its stored body, followed by any trailing
//   arguments (useful for routing/parse checks).
//   DEFCMD refuses to shadow a protected built-in and refuses to overwrite any
//   pre-existing non-scratch command. Redefining your own scratch command is OK.
//   Registered as a non-protected Extension-origin command in the live registry.
//   Remove with UNDEFCMD.
//
// risk:
//   mutates_table_data: no
//   mutates_command_registry: session-only, non-protected names
//
// related:
//   UNDEFCMD
//   EXAMPLE
//

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/command_registry.hpp"

#include <iostream>
#include <map>
#include <sstream>
#include <string>

namespace {

// Session-scoped registry of scratch command names -> body text.
// Doubles as the "is this one of ours?" set so UNDEFCMD/redefine only touch
// commands DEFCMD created (never built-ins or other extensions).
std::map<std::string, std::string>& scratch_store()
{
    static std::map<std::string, std::string> store;
    return store;
}

void print_defcmd_usage()
{
    std::cout
        << "Usage:\n"
        << "  DEFCMD USAGE\n"
        << "  DEFCMD LIST\n"
        << "  DEFCMD <NAME> = <body-text>\n"
        << "  DEFCMD <NAME> <body-text>\n"
        << "Notes:\n"
        << "  - Session-only; scratch commands vanish on EXIT.\n"
        << "  - Cannot shadow built-ins; remove with UNDEFCMD.\n";
}

void print_scratch_list()
{
    const auto& store = scratch_store();
    if (store.empty()) {
        std::cout << "DEFCMD: no scratch commands defined.\n";
        return;
    }
    std::cout << "Scratch commands (" << store.size() << "):\n";
    for (const auto& kv : store) {
        std::cout << "  " << kv.first << " = " << kv.second << "\n";
    }
}

} // namespace

void cmd_DEFCMD(xbase::DbArea&, std::istringstream& iss)
{
    std::string rest;
    std::getline(iss, rest);
    rest = textio::trim(rest);

    if (rest.empty()) {
        print_defcmd_usage();
        return;
    }

    {
        const std::string u = textio::upper(rest);
        if (u == "USAGE" || u == "HELP" || u == "?") {
            print_defcmd_usage();
            return;
        }
        if (u == "LIST") {
            print_scratch_list();
            return;
        }
    }

    // Parse "<NAME> [=] <body>".
    std::istringstream ps(rest);
    std::string rawName;
    ps >> rawName;

    std::string body;
    std::getline(ps, body);
    body = textio::trim(body);
    if (!body.empty() && body.front() == '=') {
        body.erase(body.begin());
        body = textio::trim(body);
    }

    const std::string key = textio::upper(textio::trim(rawName));
    if (key.empty()) {
        print_defcmd_usage();
        return;
    }

    // Guard 1: never shadow a protected built-in.
    if (dli::registry().is_protected(key)) {
        std::cout << "DEFCMD: '" << key
                  << "' is a protected built-in; cannot redefine.\n";
        return;
    }

    // Guard 2: never clobber a pre-existing command that we did not create.
    const bool ours = scratch_store().count(key) != 0;
    if (!ours && dli::registry().registration_info(key).has_value()) {
        std::cout << "DEFCMD: '" << key
                  << "' already exists as a non-scratch command; refusing to overwrite.\n";
        return;
    }

    // Register (or redefine) as a session-scoped Extension command whose body
    // is captured by value. The live dispatcher (CommandRegistry::try_run) will
    // find it on the very next command.
    scratch_store()[key] = body;
    dli::registry().add_extension(
        key,
        [key, body](xbase::DbArea&, std::istringstream& in) {
            std::string tail;
            std::getline(in, tail);
            tail = textio::trim(tail);

            std::cout << body;
            if (!tail.empty()) {
                std::cout << " " << tail;
            }
            std::cout << "\n";
        },
        "runtime:DEFCMD");

    std::cout << "DEFCMD: defined " << key;
    if (body.empty()) {
        std::cout << " (empty body)";
    }
    std::cout << "\n";
}

// @dottalk.usage v1
// owner: DOT|UNDEFCMD
// command: UNDEFCMD
// category: diagnostics
// status: experimental
// noargs: usage
// effect: mutates-command-registry
// mutates: none
// usage-access: UNDEFCMD USAGE
// summary:
//   Remove a scratch command previously defined with DEFCMD.
//
// usage:
//   UNDEFCMD USAGE
//   UNDEFCMD <NAME>
//
// notes:
//   Only removes session scratch commands created by DEFCMD.
//   Never removes protected built-ins or other extensions.
//
// risk:
//   mutates_table_data: no
//
// related:
//   DEFCMD
//

void cmd_UNDEFCMD(xbase::DbArea&, std::istringstream& iss)
{
    std::string rawName;
    iss >> rawName;
    const std::string key = textio::upper(textio::trim(rawName));

    if (key.empty() || key == "USAGE" || key == "HELP" || key == "?") {
        std::cout << "Usage:\n  UNDEFCMD <NAME>\n";
        return;
    }

    auto& store = scratch_store();
    const auto it = store.find(key);
    if (it == store.end()) {
        std::cout << "UNDEFCMD: no scratch command named '" << key << "'.\n";
        return;
    }

    dli::registry().remove(key);
    store.erase(it);
    std::cout << "UNDEFCMD: removed " << key << "\n";
}
