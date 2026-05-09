// src/cli/cmd_clear.cpp
// DotTalk++ ? CLEAR (and CLS alias via registry)
// Cross-platform default: Windows -> cls; others -> ANSI escape.
// We keep it minimal and non-invasive (no engine touches).

// @dottalk.usage v1
// owner: DOT|CLEAR
// command: CLEAR
// category: ui
// status: supported
// noargs: screen
// effect: screen
// mutates: console
// usage-access: CLEAR USAGE
// summary:
//   Clear the terminal screen using the platform console command or ANSI
//   escape sequence without touching the database engine.
//
// usage:
//   CLEAR USAGE
//   CLEAR
//   CLS
//
// notes:
//   CLEAR with no arguments clears the console screen.
//   CLS is the registry alias where configured.
//   CLEAR is UI-only and does not mutate table data or session state.
//
// risk:
//   clears_console: yes
//   mutates_table_data: no
//   mutates_session: no
//
// related:
//   COLOR
//   HELP
//

#include <iostream>
#include <sstream>
#include <cstdlib>
#include <string>
#include <cctype>

#include "xbase.hpp"


namespace {
static std::string clear_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}
static std::string clear_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}
static bool is_clear_usage_request(std::string raw)
{
    std::string t = clear_upper(clear_trim(std::move(raw)));
    if (t.rfind("CLEAR ", 0) == 0) t = clear_trim(t.substr(6));
    if (t.rfind("CLS ", 0) == 0) t = clear_trim(t.substr(4));
    return t == "USAGE" || t == "HELP" || t == "?";
}
static void print_clear_usage()
{
    std::cout
        << "Usage:\n"
        << "  CLEAR USAGE\n"
        << "  CLEAR\n"
        << "  CLS\n"
        << "Notes:\n"
        << "  - Clears the console screen only.\n";
}
} // namespace

void cmd_CLEAR(xbase::DbArea& /*a*/, std::istringstream& iss) {
    const std::string raw_args = iss.str();
    if (is_clear_usage_request(raw_args)) {
        print_clear_usage();
        return;
    }

#ifdef _WIN32
    // Windows console: use built-in cls for predictable behavior in CMD/PowerShell.
    std::system("cls");
#else
    // ANSI-capable terminals (Linux/macOS/Windows 10+): clear + home.
    std::cout << "\x1b[2J\x1b[H";
    std::cout.flush();
#endif
}



