// @dottalk.usage v1
// owner: DOT|DEFFN
// command: DEFFN
// category: diagnostics
// status: experimental
// noargs: usage
// effect: mutates-function-registry
// mutates: none
// usage-access: DEFFN USAGE
// summary:
//   Define an ephemeral, session-only expression function at runtime, without a rebuild
//   or source edit. The function resolves inside ? / CALC / WHERE via the fn_custom seam.
//   Part of the RUNTIME_DEF_FAMILY lane (sibling to DEFCMD).
//
// usage:
//   DEFFN USAGE
//   DEFFN LIST
//   DEFFN <NAME> = <body-text>
//   DEFFN <NAME> <body-text>
//
// examples:
//   DEFFN GREET = hello
//   ? GREET()            && -> hello
//
// notes:
//   Session-only; custom functions vanish on EXIT and are never written to disk.
//   MVP body returns the stored text (arguments are accepted but ignored).
//   DEFFN refuses to shadow a compiled-in builtin function; redefining your own custom
//   function is OK. Remove with UNDEFFN.
//
// risk:
//   mutates_table_data: no
//   mutates_function_registry: session-only, non-builtin names
//
// related:
//   UNDEFFN
//   DEFCMD
//

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/expr/fn_custom.hpp"

#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

// MVP: a custom function accepts up to this many args (all ignored by the text body).
constexpr int kCustomFnMaxArgs = 16;

void print_deffn_usage()
{
    std::cout
        << "Usage:\n"
        << "  DEFFN USAGE\n"
        << "  DEFFN LIST\n"
        << "  DEFFN <NAME> = <body-text>\n"
        << "  DEFFN <NAME> <body-text>\n"
        << "Notes:\n"
        << "  - Session-only; custom functions vanish on EXIT.\n"
        << "  - Resolves in ? / CALC / WHERE; cannot shadow builtins; remove with UNDEFFN.\n";
}

void print_deffn_list()
{
    const std::vector<std::string> names = dottalk::expr::custom_fn_names();
    if (names.empty()) {
        std::cout << "DEFFN: no custom functions defined.\n";
        return;
    }
    std::cout << "Custom functions (" << names.size() << "):\n";
    for (const std::string& n : names) {
        std::cout << "  " << n << "\n";
    }
}

} // namespace

void cmd_DEFFN(xbase::DbArea&, std::istringstream& iss)
{
    std::string rest;
    std::getline(iss, rest);
    rest = textio::trim(rest);

    if (rest.empty()) {
        print_deffn_usage();
        return;
    }

    {
        const std::string u = textio::upper(rest);
        if (u == "USAGE" || u == "HELP" || u == "?") {
            print_deffn_usage();
            return;
        }
        if (u == "LIST") {
            print_deffn_list();
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
        print_deffn_usage();
        return;
    }

    // Guard: never shadow a compiled-in builtin function.
    if (dottalk::expr::is_builtin_fn(key)) {
        std::cout << "DEFFN: '" << key
                  << "' is a builtin function; cannot redefine.\n";
        return;
    }

    // Register (or redefine) a session custom function. MVP body returns the stored text
    // and ignores its arguments. Captured by value so the entry is self-contained.
    const bool ok = dottalk::expr::register_custom_fn(
        key, 0, kCustomFnMaxArgs,
        [body](const std::vector<std::string>&) -> std::string {
            return body;
        });

    if (!ok) {
        std::cout << "DEFFN: could not define '" << key << "'.\n";
        return;
    }

    std::cout << "DEFFN: defined " << key;
    if (body.empty()) {
        std::cout << " (empty body)";
    }
    std::cout << "\n";
}

// @dottalk.usage v1
// owner: DOT|UNDEFFN
// command: UNDEFFN
// category: diagnostics
// status: experimental
// noargs: usage
// effect: mutates-function-registry
// mutates: none
// usage-access: UNDEFFN USAGE
// summary:
//   Remove a session custom function previously defined with DEFFN.
//
// usage:
//   UNDEFFN USAGE
//   UNDEFFN <NAME>
//
// notes:
//   Only removes session custom functions created by DEFFN.
//   Never removes compiled-in builtins.
//
// risk:
//   mutates_table_data: no
//
// related:
//   DEFFN
//

void cmd_UNDEFFN(xbase::DbArea&, std::istringstream& iss)
{
    std::string rawName;
    iss >> rawName;
    const std::string key = textio::upper(textio::trim(rawName));

    if (key.empty() || key == "USAGE" || key == "HELP" || key == "?") {
        std::cout << "Usage:\n  UNDEFFN <NAME>\n";
        return;
    }

    if (!dottalk::expr::find_custom_fn(key)) {
        std::cout << "UNDEFFN: no custom function named '" << key << "'.\n";
        return;
    }

    dottalk::expr::unregister_custom_fn(key);
    std::cout << "UNDEFFN: removed " << key << "\n";
}
