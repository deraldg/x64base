// src/cli/cmd_browse.cpp — thin forwarder to the refactored BROWSE module

// @dottalk.usage v1
// owner: DOT|BROWSE
// command: BROWSE
// category: ui
// status: supported
// noargs: interactive
// effect: interactive
// mutates: delegates browse module commands
// usage-access: BROWSE USAGE
// summary:
//   Enter the refactored BROWSE module through the legacy global command
//   symbol, preserving existing callers while delegating implementation.
//
// usage:
//   BROWSE USAGE
//   BROWSE
//   BROWSE EDIT
//
// notes:
//   BROWSE is a thin forwarder to the browse module.
//   BROWSE with no arguments enters interactive browse mode.
//   BROWSE EDIT requests edit-capable browse behavior where supported by the module.
//   Side effects depend on browse actions and delegated commands.
//
// risk:
//   interactive: yes
//   mutates_data: possible through edit actions
//   delegates_to_browse_module: yes
//
// related:
//   BROWSER
//   BROWSETUI
//   LIST
//   DISPLAY
//   REPLACE
//

#include <sstream>
#include <iostream>
#include <string>
#include <algorithm>
#include <cctype>
#include "xbase.hpp"

// Public entrypoint from the new module
#include "browse/browse_cmd.hpp"


namespace {
static std::string browse_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}
static std::string browse_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}
static bool is_browse_usage_request(std::string raw)
{
    std::string t = browse_upper(browse_trim(std::move(raw)));
    if (t.rfind("BROWSE ", 0) == 0) t = browse_trim(t.substr(7));
    return t == "USAGE" || t == "HELP" || t == "?";
}
static void print_browse_usage()
{
    std::cout
        << "Usage:\n"
        << "  BROWSE USAGE\n"
        << "  BROWSE\n"
        << "  BROWSE EDIT\n"
        << "Notes:\n"
        << "  - Enters the refactored interactive browse module.\n";
}
} // namespace

// Keep the original global symbol so existing callers don't change.
void cmd_BROWSE(::xbase::DbArea& area, std::istringstream& in) {
    const std::string raw_args = in.str();
    if (is_browse_usage_request(raw_args)) {
        print_browse_usage();
        return;
    }

    dottalk::browse::cmd_BROWSE(area, in);
}
