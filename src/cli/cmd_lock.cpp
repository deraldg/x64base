// cmd_lock.cpp — owner-aware UI (works with the back-compat shims too)
// @dottalk.usage v1
// owner: DOT|LOCK
// command: LOCK
// category: concurrency
// status: supported
// noargs: mutate
// effect: lock
// mutates: lock-state
// usage-access: LOCK USAGE
// summary:
//   Acquire record or table locks for the current table and inspect lock status
//   or lock ownership.
//
// usage:
//   LOCK USAGE
//   LOCK
//   LOCK <n>
//   LOCK ALL
//   LOCK TABLE
//   LOCK STATUS
//   LOCK WHO <n>
//
// notes:
//   LOCK requires an open table except for LOCK USAGE.
//   LOCK with no arguments locks the current record.
//   LOCK <n> locks record n.
//   LOCK ALL and LOCK TABLE lock the entire table.
//   LOCK STATUS reports table and current-record lock state.
//   LOCK WHO <n> reports the owner of record n when a lock is recorded.
//   LOCK mutates lock state but does not mutate table data.
//
// risk:
//   mutates_lock_state: yes
//   mutates_table_data: no
//   requires_open_table: yes except usage
//   uses_current_owner: yes
//
// related:
//   UNLOCK
//   DELETE
//   COMMIT
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
static std::string up(std::string s) {
    for (auto& c: s) c = (char)std::toupper((unsigned char)c);
    return s;
}

static void print_usage() {
    std::cout << "Usage:\n"
                 "  LOCK USAGE           - show this usage\n"
                 "  LOCK                 - lock current record\n"
                 "  LOCK <n>             - lock record <n>\n"
                 "  LOCK ALL             - lock entire table\n"
                 "  LOCK TABLE           - lock entire table\n"
                 "  LOCK STATUS          - show lock status\n"
                 "  LOCK WHO <n>         - show owner of record <n>\n";
}

static void show_status(xbase::DbArea& a) {
    if (!a.isOpen()) { std::cout << "LOCK STATUS: no table open.\n"; return; }
    std::string tab;
    bool tlocked = xbase::locks::is_table_locked(a, &tab);
    std::cout << "Table: " << (tlocked ? "LOCKED" : "unlocked");
    if (tlocked) std::cout << " (owner " << tab << ")";
    std::cout << "\n";

    const auto rn = static_cast<uint32_t>(a.recno());
    if (rn > 0) {
        std::string row;
        bool rlocked = xbase::locks::is_record_locked(a, rn, &row);
        std::cout << "Record " << rn << ": " << (rlocked ? "LOCKED" : "unlocked");
        if (rlocked) std::cout << " (owner " << row << ")";
        std::cout << "\n";
    }
}

static void show_who(xbase::DbArea& a, uint32_t n) {
    std::string owner;
    if (!xbase::locks::is_record_locked(a, n, &owner)) {
        std::cout << "LOCK WHO: no lock recorded for " << n << ".\n";
        return;
    }
    std::cout << "LOCK WHO: record " << n << " owned by " << owner << "\n";
}

void cmd_LOCK(xbase::DbArea& a, std::istringstream& iss) {
    std::string rest = up(read_rest(iss));
    if (rest == "USAGE" || rest == "HELP" || rest == "?" ||
        rest == "LOCK USAGE" || rest == "LOCK HELP" || rest == "LOCK ?") {
        print_usage();
        return;
    }

    if (!a.isOpen()) { std::cout << "LOCK: no table open.\n"; return; }
    const auto& me = xbase::locks::current_owner();

    if (rest.empty()) {
        const auto rn = static_cast<uint32_t>(a.recno());
        if (rn == 0) { std::cout << "LOCK: no current record.\n"; return; }
        std::string err;
        if (xbase::locks::try_lock_record(a, rn, me, &err)) {
            std::cout << "LOCK: record " << rn << " locked.\n";
        } else {
            std::cout << "LOCK: failed (" << err << ").\n";
        }
        return;
    }

    if (rest == "ALL" || rest == "TABLE") {
        std::string err;
        if (xbase::locks::try_lock_table(a, me, &err)) {
            std::cout << "LOCK: table locked.\n";
        } else {
            std::cout << "LOCK: failed (" << err << ").\n";
        }
        return;
    }

    if (rest == "STATUS") { show_status(a); return; }

    if (rest.rfind("WHO", 0) == 0) {
        std::istringstream tmp(rest);
        std::string who; tmp >> who; // WHO
        std::string nstr; std::getline(tmp >> std::ws, nstr);
        if (nstr.empty()) { print_usage(); return; }
        try { show_who(a, static_cast<uint32_t>(std::stoul(nstr))); }
        catch (...) { print_usage(); }
        return;
    }

    // LOCK <n>
    try {
        uint32_t n = static_cast<uint32_t>(std::stoul(rest));
        std::string err;
        if (xbase::locks::try_lock_record(a, n, me, &err)) {
            std::cout << "LOCK: record " << n << " locked.\n";
        } else {
            std::cout << "LOCK: failed (" << err << ").\n";
        }
    } catch (...) {
        print_usage();
    }
}
