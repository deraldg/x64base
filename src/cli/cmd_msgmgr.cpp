// src/cli/cmd_msgmgr.cpp
// @dottalk.usage v1
// owner: DOT|MSGMGR
// command: MSGMGR
// category: messaging
// status: supported
// noargs: usage
// effect: report|maintenance
// mutates: yes (SEED PRIORITYA APPLY only)
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
//   MSGMGR SEED PRIORITYA CHECK
//   MSGMGR SEED PRIORITYA APPLY
//   MSGMGR SEED PRIORITYB CHECK
//   MSGMGR SEED PRIORITYB APPLY
//   MSGMGR SEED PRIORITYC CHECK
//   MSGMGR SEED PRIORITYC APPLY
//
// notes:
//   MSGMGR is the command house for Messaging manager surfaces.
//   STATUS and top-level CHECK remain report-only surfaces.
//   SEED PRIORITYA CHECK inspects the active runtime Messaging rows.
//   SEED PRIORITYA APPLY upserts Priority A runtime Messaging rows into
//   SYSTEM_MESSAGES / SYSTEM_MESSAGE_TEXT and rebuilds the matching
//   Messaging LMDB backends from existing CDX containers.
//   MSGMGR does not mutate HELP DATA, CMDHELPCHK, manualgen, Data Dictionary,
//   SelfDoc, or source-derived catalogs.
//
// related:
//   SET MESSAGE CATALOG CHECK
//   SET MESSAGE CATALOG GET
//   SET LANGUAGE
//   SET MESSAGE EMIT
//   DDICT
//

#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>

#include "cli/command_output.hpp"
#include "cli/settings.hpp"
#include "help/message_catalog.hpp"
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
    cli::cmdout::print_line("Usage:");
    cli::cmdout::print_line("  MSGMGR");
    cli::cmdout::print_line("  MSGMGR USAGE");
    cli::cmdout::print_line("  MSGMGR STATUS");
    cli::cmdout::print_line("  MSGMGR CHECK");
    cli::cmdout::print_line("  MSGMGR SEED PRIORITYA CHECK");
    cli::cmdout::print_line("  MSGMGR SEED PRIORITYA APPLY");
    cli::cmdout::print_line("  MSGMGR SEED PRIORITYB CHECK");
    cli::cmdout::print_line("  MSGMGR SEED PRIORITYB APPLY");
    cli::cmdout::print_line("  MSGMGR SEED PRIORITYC CHECK");
    cli::cmdout::print_line("  MSGMGR SEED PRIORITYC APPLY");
    cli::cmdout::print_line("Notes:");
    cli::cmdout::print_line("  - STATUS and CHECK remain read/report surfaces.");
    cli::cmdout::print_line("  - SEED PRIORITYA CHECK/APPLY maintains SET MESSAGE / MSGMGR rows.");
    cli::cmdout::print_line("  - SEED PRIORITYB CHECK/APPLY maintains the demoed command-surface rows.");
    cli::cmdout::print_line("  - SEED PRIORITYC CHECK/APPLY maintains USE / DISPLAY / navigation runtime lines.");
}

static void print_msgmgr_status()
{
    const std::string locale = cli::Settings::instance().message_locale;
    cli::cmdout::print_line(
        dottalk::helpdata::format_message_catalog(locale, "MSGMGR_STATUS_TITLE"));
    cli::cmdout::print_line(
        dottalk::helpdata::format_message_catalog(locale, "MSGMGR_STATUS_BODY_TEXT"));
}

static bool is_priority_a_token(const std::string& s)
{
    return s == "PRIORITYA" || s == "PRIORITY_A" || s == "PRIORITY-A";
}

static bool is_priority_b_token(const std::string& s)
{
    return s == "PRIORITYB" || s == "PRIORITY_B" || s == "PRIORITY-B";
}

static bool is_priority_c_token(const std::string& s)
{
    return s == "PRIORITYC" || s == "PRIORITY_C" || s == "PRIORITY-C";
}

static void print_seed_report(const char* bundle,
                              const char* action,
                              const dottalk::helpdata::MessageCatalogSeedReport& report)
{
    cli::cmdout::print_line(std::string("MSGMGR SEED ") + bundle + " " + action);
    cli::cmdout::print_line(std::string("  success             : ") + (report.success ? "yes" : "no"));
    cli::cmdout::print_line(std::string("  seed complete       : ") + (report.seed_complete ? "yes" : "no"));
    cli::cmdout::print_line(std::string("  active catalog      : ") + (report.active_catalog_present ? "yes" : "no"));
    cli::cmdout::print_line(std::string("  active rows loaded  : ") + (report.active_catalog_loaded ? "yes" : "no"));
    cli::cmdout::print_line("  dbf root            : " + report.active_dbf_dir);
    cli::cmdout::print_line("  indexes root        : " + report.active_indexes_dir);
    cli::cmdout::print_line("  lmdb root           : " + report.active_lmdb_dir);
    cli::cmdout::print_line("  expected messages   : " + std::to_string(report.expected_message_rows));
    cli::cmdout::print_line("  present messages    : " + std::to_string(report.present_message_rows));
    cli::cmdout::print_line("  expected text rows  : " + std::to_string(report.expected_text_rows));
    cli::cmdout::print_line("  present text rows   : " + std::to_string(report.present_text_rows));
    cli::cmdout::print_line("  messages before     : " + std::to_string(report.message_rows_before));
    cli::cmdout::print_line("  messages after      : " + std::to_string(report.message_rows_after));
    cli::cmdout::print_line("  text rows before    : " + std::to_string(report.text_rows_before));
    cli::cmdout::print_line("  text rows after     : " + std::to_string(report.text_rows_after));
    cli::cmdout::print_line("  message inserted    : " + std::to_string(report.message_rows_inserted));
    cli::cmdout::print_line("  message updated     : " + std::to_string(report.message_rows_updated));
    cli::cmdout::print_line("  message unchanged   : " + std::to_string(report.message_rows_unchanged));
    cli::cmdout::print_line("  text inserted       : " + std::to_string(report.text_rows_inserted));
    cli::cmdout::print_line("  text updated        : " + std::to_string(report.text_rows_updated));
    cli::cmdout::print_line("  text unchanged      : " + std::to_string(report.text_rows_unchanged));
    cli::cmdout::print_line("  detail              : " + report.detail);

    if (!report.rebuilt_containers.empty()) {
        cli::cmdout::print_line("  rebuilt containers  : " + std::to_string(report.rebuilt_containers.size()));
        for (const auto& path : report.rebuilt_containers) {
            cli::cmdout::print_line("    " + path);
        }
    }

    if (!report.errors.empty()) {
        cli::cmdout::print_line("  errors              : " + std::to_string(report.errors.size()));
        for (const auto& error : report.errors) {
            cli::cmdout::print_line("    " + error);
        }
    }
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

    if (sub == "SEED") {
        std::string target;
        std::string action;
        args >> target >> action;
        target = msgmgr_upper(msgmgr_trim(target));
        action = msgmgr_upper(msgmgr_trim(action));

        if (action.empty()) {
            print_msgmgr_usage();
            return;
        }

        if (is_priority_a_token(target)) {
            if (action == "CHECK") {
                print_seed_report("PRIORITYA", "CHECK", dottalk::helpdata::check_priority_a_seed());
                return;
            }

            if (action == "APPLY") {
                print_seed_report("PRIORITYA", "APPLY", dottalk::helpdata::apply_priority_a_seed());
                return;
            }
        }

        if (is_priority_b_token(target)) {
            if (action == "CHECK") {
                print_seed_report("PRIORITYB", "CHECK", dottalk::helpdata::check_priority_b_seed());
                return;
            }

            if (action == "APPLY") {
                print_seed_report("PRIORITYB", "APPLY", dottalk::helpdata::apply_priority_b_seed());
                return;
            }
        }

        if (is_priority_c_token(target)) {
            if (action == "CHECK") {
                print_seed_report("PRIORITYC", "CHECK", dottalk::helpdata::check_priority_c_seed());
                return;
            }

            if (action == "APPLY") {
                print_seed_report("PRIORITYC", "APPLY", dottalk::helpdata::apply_priority_c_seed());
                return;
            }
        }

        print_msgmgr_usage();
        return;
    }

    cli::cmdout::print_prefixed_message(
        "MSGMGR",
        dottalk::helpdata::MessageId::MsgMgrUnknownSubcommand,
        {{"command", sub}});
    print_msgmgr_usage();
}
