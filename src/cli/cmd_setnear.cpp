// src/cli/cmd_setnear.cpp
// @dottalk.usage v1
// owner: DOT|SET NEAR
// command: SET NEAR
// category: settings
// status: supported
// noargs: report
// effect: configure
// mutates: near-search-setting
// usage-access: SET NEAR USAGE
// summary:
//   Report or set SEEK/FIND near-match behavior.
//
// usage:
//   SET NEAR
//   SET NEAR USAGE
//   SET NEAR ON
//   SET NEAR OFF
//   SETNEAR
//   SETNEAR USAGE
//   SETNEAR ON
//   SETNEAR OFF
//
// notes:
//   SET NEAR with no arguments reports current NEAR state.
//   ON, TRUE, and 1 enable nearest greater-or-equal match behavior.
//   OFF, FALSE, and 0 require exact matches.
//   This mutates search behavior settings only.
//
// risk:
//   mutates_session_settings: yes
//   mutates_table_data: no
//
// related:
//   SEEK
//   FIND
//   SET CASE
//

#include <atomic>
#include <iostream>
#include <sstream>
#include <string>

#include "textio.hpp"
#include "xbase.hpp"

// -----------------------------------------------------------------------------
// SET NEAR state
//
// Contract:
//   SET NEAR OFF  -> SEEK requires an exact key match.
//   SET NEAR ON   -> SEEK may move to the nearest greater/equal key when no
//                    exact key exists. SEEK/FIND must still report the
//                    difference between exact Found and Near match.
//
// This state is deliberately small and global, matching the current SETCASE
// command style. SEEK/FIND can later consume dottalk::near::get_near().
// -----------------------------------------------------------------------------
namespace dottalk::near {

namespace {
std::atomic_bool g_near_on{false};
}

bool get_near() noexcept {
    return g_near_on.load();
}

void set_near(bool on) noexcept {
    g_near_on.store(on);
}

} // namespace dottalk::near

static void print_setnear_usage()
{
    std::cout
        << "Usage:\n"
        << "  SET NEAR\n"
        << "  SET NEAR USAGE\n"
        << "  SET NEAR ON\n"
        << "  SET NEAR OFF\n"
        << "  SETNEAR\n"
        << "  SETNEAR USAGE\n"
        << "  SETNEAR ON\n"
        << "  SETNEAR OFF\n";
}

void cmd_SETNEAR(xbase::DbArea&, std::istringstream& iss) {
    std::string tok;

    if (!(iss >> tok)) {
        std::cout << (dottalk::near::get_near()
            ? "NEAR: ON\n"
            : "NEAR: OFF\n");
        return;
    }

    if (textio::ieq(tok, "USAGE") || textio::ieq(tok, "HELP") || tok == "?") {
        print_setnear_usage();
        return;
    }

    if (textio::ieq(tok, "ON") || textio::ieq(tok, "TRUE") || textio::ieq(tok, "1")) {
        dottalk::near::set_near(true);
        std::cout << "NEAR: ON\n";
        return;
    }

    if (textio::ieq(tok, "OFF") || textio::ieq(tok, "FALSE") || textio::ieq(tok, "0")) {
        dottalk::near::set_near(false);
        std::cout << "NEAR: OFF\n";
        return;
    }

    print_setnear_usage();
}
