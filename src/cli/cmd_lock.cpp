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

#include <sstream>
#include <string>
#include <cctype>

#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
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
    cli::cmdout::print_message(dottalk::helpdata::MessageId::LockUsageText);
}

static std::string lock_state_text(bool locked) {
    return cli::cmdout::message_text(
        locked
            ? dottalk::helpdata::MessageId::LockStateLockedText
            : dottalk::helpdata::MessageId::LockStateUnlockedText);
}

static std::string lock_owner_clause(const std::string& owner) {
    if (owner.empty()) {
        return std::string();
    }
    return cli::cmdout::message_text(
        dottalk::helpdata::MessageId::LockOwnerClauseText,
        {{"owner", owner}});
}

static void show_status(xbase::DbArea& a) {
    if (!a.isOpen()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::LockStatusNoTableOpenText);
        return;
    }
    std::string tab;
    bool tlocked = xbase::locks::is_table_locked(a, &tab);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::LockStatusTableLineText,
        {
            {"state", lock_state_text(tlocked)},
            {"owner_clause", tlocked ? lock_owner_clause(tab) : std::string()}
        });

    const auto rn = static_cast<uint32_t>(a.recno());
    if (rn > 0) {
        std::string row;
        bool rlocked = xbase::locks::is_record_locked(a, rn, &row);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::LockStatusRecordLineText,
            {
                {"recno", std::to_string(rn)},
                {"state", lock_state_text(rlocked)},
                {"owner_clause", rlocked ? lock_owner_clause(row) : std::string()}
            });
    }
}

static void show_who(xbase::DbArea& a, uint32_t n) {
    std::string owner;
    if (!xbase::locks::is_record_locked(a, n, &owner)) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::LockWhoNoneText,
            {{"recno", std::to_string(n)}});
        return;
    }
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::LockWhoOwnedText,
        {{"recno", std::to_string(n)}, {"owner", owner}});
}

void cmd_LOCK(xbase::DbArea& a, std::istringstream& iss) {
    std::string rest = up(read_rest(iss));
    if (rest.rfind("LOCK ", 0) == 0) {
        rest = textio::trim(rest.substr(5));
    } else if (rest == "LOCK") {
        rest.clear();
    }
    if (rest == "USAGE" || rest == "HELP" || rest == "?" ||
        rest == "LOCK USAGE" || rest == "LOCK HELP" || rest == "LOCK ?") {
        print_usage();
        return;
    }

    if (rest == "STATUS") { show_status(a); return; }

    if (!a.isOpen()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::LockNoTableOpenText);
        return;
    }
    const auto& me = xbase::locks::current_owner();

    if (rest.empty()) {
        const auto rn = static_cast<uint32_t>(a.recno());
        if (rn == 0) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::LockNoCurrentRecordText);
            return;
        }
        std::string err;
        if (xbase::locks::try_lock_record(a, rn, me, &err)) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::LockRecordLockedText,
                {{"recno", std::to_string(rn)}});
        } else {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::LockFailedText,
                {{"detail", err}});
        }
        return;
    }

    if (rest == "ALL" || rest == "TABLE") {
        std::string err;
        if (xbase::locks::try_lock_table(a, me, &err)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::LockTableLockedText);
        } else {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::LockFailedText,
                {{"detail", err}});
        }
        return;
    }

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
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::LockRecordLockedText,
                {{"recno", std::to_string(n)}});
        } else {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::LockFailedText,
                {{"detail", err}});
        }
    } catch (...) {
        print_usage();
    }
}
