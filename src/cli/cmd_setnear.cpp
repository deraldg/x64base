// src/cli/cmd_setnear.cpp
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

void cmd_SETNEAR(xbase::DbArea&, std::istringstream& iss) {
    std::string tok;

    if (!(iss >> tok)) {
        std::cout << (dottalk::near::get_near()
            ? "NEAR: ON\n"
            : "NEAR: OFF\n");
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

    std::cout << "Usage: SET NEAR [ON|OFF]\n";
}
