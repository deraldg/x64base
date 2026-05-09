// @dottalk.usage v1
// owner: DOT|BELL
// command: BELL
// category: ui
// status: supported
// noargs: execute
// effect: configure
// mutates: bell-setting audible-notification
// usage-access: BELL USAGE
// summary:
//   Ring the bell when enabled, or turn the shell bell setting on or off.
//
// usage:
//   BELL
//   BELL USAGE
//   BELL ON
//   BELL OFF
//
// notes:
//   BELL with no arguments rings the bell when bell is ON; otherwise reports that bell is OFF.
//   BELL ON enables the bell and rings it once.
//   BELL OFF disables the bell.
//   BELL mutates only the shell bell setting and audible notification state.
//
// risk:
//   mutates_setting: bell_on
//   audible_effect: yes when ringing
//   mutates_table_data: no
//
// related:
//   SET
//   COLOR
//

#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

#include "cli/output_router.hpp"
#include "cli/settings.hpp"

#ifdef _WIN32
#include <windows.h>
#endif

namespace {

static inline std::string up_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static inline bool parse_on_off(const std::string& tok, bool& out)
{
    const std::string u = up_copy(tok);
    if (u == "ON")  { out = true;  return true; }
    if (u == "OFF") { out = false; return true; }
    return false;
}

static void ring_bell()
{
#ifdef _WIN32
    ::MessageBeep(MB_OK);
#else
    std::cout << '\a' << std::flush;
#endif
}

} // namespace

void cmd_BELL(xbase::DbArea&, std::istringstream& in)
{
    auto& S   = cli::Settings::instance();
    auto& out = cli::OutputRouter::instance().out();

    std::string tok;
    if (!(in >> tok)) {
        if (S.bell_on.load()) {
            ring_bell();
            out << "Bell rung.\n";
        } else {
            out << "Bell is OFF.\n";
        }
        return;
    }

    bool on = S.bell_on.load();
    if (!parse_on_off(tok, on)) {
        out << "Usage: BELL [ON|OFF]\n";
        return;
    }

    S.bell_on.store(on);
    out << "Bell is " << (on ? "ON" : "OFF") << "\n";

    if (on) {
        ring_bell();
    }
}