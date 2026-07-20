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
static std::string up(std::string s) { for (auto& c: s) c = (char)std::toupper((unsigned char)c); return s; }

static void print_unlock_usage_contract()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::UnlockUsageText);
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

    if (!a.isOpen()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::UnlockNoTableOpenText);
        return;
    }

    std::string rest = up(read_rest(iss));
    if (rest.empty()) {
        // UNLOCK current record
        const std::uint64_t rn = a.recno64();
        if (rn == 0) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::UnlockNoCurrentRecordText);
            return;
        }
        xbase::locks::unlock_record(a, rn);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::UnlockRecordUnlockedText,
            {{"recno", std::to_string(rn)}});
        return;
    }

    if (rest == "ALL" || rest == "TABLE") {
        xbase::locks::unlock_table(a);
        cli::cmdout::print_message(dottalk::helpdata::MessageId::UnlockTableUnlockedText);
        return;
    }

    // UNLOCK <n>
    try {
        std::uint64_t n = std::stoull(rest);
        xbase::locks::unlock_record(a, n);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::UnlockRecordUnlockedText,
            {{"recno", std::to_string(n)}});
    } catch (...) {
        print_unlock_usage_contract();
    }
}
