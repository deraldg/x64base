// @dottalk.usage v1
// owner: DOT|UNLOCK
// command: UNLOCK
// category: locking
// status: supported
// noargs: unlock-current-record
// effect: release-lock
// mutates: lock-state
// usage-access: UNLOCK USAGE
// summary:
//   Release the current record lock, a specified record lock, or the table lock.
//
// usage:
//   UNLOCK USAGE
//   UNLOCK
//   UNLOCK <recno>
//   UNLOCK ALL
//   UNLOCK TABLE
//
// examples:
//   UNLOCK
//   UNLOCK 10
//   UNLOCK ALL
//   UNLOCK TABLE
//
// notes:
//   UNLOCK USAGE returns before open-table checks.
//   UNLOCK with no arguments unlocks the current record.
//   UNLOCK ALL and UNLOCK TABLE release the table lock.
//
// risk:
//   requires_open_table: yes except usage
//   mutates_lock_state: yes
//   mutates_table_data: no
//
// related:
//   LOCK
//   RLOCK
//   FLOCK
//

#include <iostream>
#include <sstream>
#include <string>
#include <cctype>

#include "xbase.hpp"
#include "xbase_locks.hpp"
#include "textio.hpp"

static std::string read_rest(std::istringstream& iss) {
    std::string s; std::getline(iss >> std::ws, s); return textio::trim(s);
}
static std::string up(std::string s) { for (auto& c: s) c = (char)std::toupper((unsigned char)c); return s; }

static void print_unlock_usage_contract()
{
    std::cout
        << "Usage:\n"
        << "  UNLOCK USAGE\n"
        << "  UNLOCK\n"
        << "  UNLOCK <recno>\n"
        << "  UNLOCK ALL\n"
        << "  UNLOCK TABLE\n"
        << "Examples:\n"
        << "  UNLOCK\n"
        << "  UNLOCK 10\n"
        << "  UNLOCK ALL\n"
        << "  UNLOCK TABLE\n"
        << "Notes:\n"
        << "  - UNLOCK USAGE does not require an open table.\n"
        << "  - UNLOCK with no arguments unlocks the current record.\n";
}
void cmd_UNLOCK(xbase::DbArea& a, std::istringstream& iss) {
    // UNLOCK_USAGE_CONTRACT_BRANCH
    {
        const std::streampos usage_pos = iss.tellg();
        std::string usage_tok;
        if (iss >> usage_tok) {
            iss.clear();
            if (usage_pos != std::streampos(-1)) {
                iss.seekg(usage_pos);
            }

            const std::string u = up(usage_tok);
            if (u == "USAGE" || u == "HELP" || u == "?") {
                print_unlock_usage_contract();
                return;
            }
        } else {
            iss.clear();
            if (usage_pos != std::streampos(-1)) {
                iss.seekg(usage_pos);
            }
        }
    }

    if (!a.isOpen()) { std::cout << "UNLOCK: no table open.\n"; return; }

    std::string rest = up(read_rest(iss));
    if (rest.empty()) {
        // UNLOCK current record
        const auto rn = static_cast<uint32_t>(a.recno());
        if (rn == 0) { std::cout << "UNLOCK: no current record.\n"; return; }
        xbase::locks::unlock_record(a, rn);
        std::cout << "UNLOCK: record " << rn << " unlocked.\n";
        return;
    }

    if (rest == "ALL" || rest == "TABLE") {
        xbase::locks::unlock_table(a);
        std::cout << "UNLOCK: table unlocked.\n";
        return;
    }

    // UNLOCK <n>
    try {
        uint32_t n = static_cast<uint32_t>(std::stoul(rest));
        xbase::locks::unlock_record(a, n);
        std::cout << "UNLOCK: record " << n << " unlocked.\n";
    } catch (...) {
        print_unlock_usage_contract();
    }
}



