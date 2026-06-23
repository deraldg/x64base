// src/cli/cmd_msgmgr.cpp
// @dottalk.usage v1
// owner: DOT|MSGMGR
// command: MSGMGR
// category: messaging
// status: supported
// noargs: usage
// effect: report
// mutates: no
// usage-access: MSGMGR USAGE
// summary:
//   Message Manager command house for runtime messaging and locale-spine
//   inspection surfaces.
//
// usage:
//   MSGMGR
//   MSGMGR USAGE
//   MSGMGR STATUS
//   MSGMGR CHECK
//
// notes:
//   MSGMGR is the command house for Messaging manager surfaces.
//   This first house registration is intentionally read-only.
//   STATUS and CHECK report that the command house is registered and that
//   runtime Messaging catalog checks remain owned by SET MESSAGE CATALOG
//   until later guarded wiring phases.
//   MSGMGR does not mutate DBF, CDX, LMDB, HELP DATA, CMDHELPCHK, manualgen,
//   Data Dictionary, SelfDoc, or source-derived catalogs.
//
// related:
//   SET MESSAGE CATALOG CHECK
//   SET MESSAGE CATALOG GET
//   SET LANGUAGE
//   DDICT
//

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"

namespace {

static std::string msgmgr_upper(std::string s)
{
    std::transform(
        s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); }
    );
    return s;
}

static std::string msgmgr_trim(std::string s)
{
    auto is_space = [](unsigned char ch) { return std::isspace(ch) != 0; };

    s.erase(
        s.begin(),
        std::find_if(s.begin(), s.end(), [&](unsigned char c) { return !is_space(c); })
    );

    s.erase(
        std::find_if(s.rbegin(), s.rend(), [&](unsigned char c) { return !is_space(c); }).base(),
        s.end()
    );

    return s;
}

static void print_msgmgr_usage()
{
    std::cout
        << "Usage:\n"
        << "  MSGMGR                 (Show this usage)\n"
        << "  MSGMGR USAGE           (Show this usage)\n"
        << "  MSGMGR STATUS          (Report Message Manager command-house status)\n"
        << "  MSGMGR CHECK           (Read-only command-house check)\n"
        << "Notes:\n"
        << "  - MSGMGR is read-only in this phase.\n"
        << "  - Runtime message catalog proof remains available through SET MESSAGE CATALOG CHECK.\n"
        << "  - Locale-spine runtime wiring remains guarded for a later phase.\n";
}

static void print_msgmgr_status()
{
    std::cout
        << "MSGMGR STATUS\n"
        << "  command house        : registered\n"
        << "  read mode            : read-only\n"
        << "  active message check : SET MESSAGE CATALOG CHECK\n"
        << "  active message get   : SET MESSAGE CATALOG GET\n"
        << "  provider mode        : active_dbf\n"
        << "  message DBF root     : dottalkpp/data/messaging\n"
        << "  message index root   : dottalkpp/data/indexes/messaging\n"
        << "  message LMDB root    : dottalkpp/data/lmdb/messaging\n"
        << "  locale spine         : scaffold present; runtime status wiring held\n"
        << "  schema root          : dottalkpp/data/schemas\n"
        << "  locale schema        : dottalkpp/data/schemas/locale/locale_spine.dtschema\n"
        << "  messaging schema     : dottalkpp/data/schemas/messaging/message_catalog.dtschema\n"
        << "  boundary             : no DBF/CDX/LMDB mutation; no runtime writeback\n";
}

} // anonymous namespace

void cmd_MSGMGR(xbase::DbArea& area, std::istringstream& args)
{
    (void)area;

    std::string sub;
    args >> sub;
    sub = msgmgr_upper(msgmgr_trim(sub));

    if (sub.empty() || sub == "USAGE" || sub == "HELP" || sub == "?" ||
        sub == "/?" || sub == "-H" || sub == "--HELP") {
        print_msgmgr_usage();
        return;
    }

    if (sub == "STATUS" || sub == "CHECK") {
        print_msgmgr_status();
        return;
    }

    std::cout << "MSGMGR: unknown subcommand '" << sub << "'.\n";
    print_msgmgr_usage();
}
