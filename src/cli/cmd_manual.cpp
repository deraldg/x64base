// @dottalk.usage v1
// owner: DOT|MANUAL
// command: MANUAL
// category: manualgen
// status: experimental
// noargs: status
// effect: report
// mutates: none
// usage-access: MANUAL USAGE
// summary:
//   Inspect the accepted MAN* manualgen catalog from inside DotTalk++.
//
// usage:
//   MANUAL
//   MANUAL USAGE
//   MANUAL STATUS
//   MANUAL TABLES
//   MANUAL COUNTS
//   MANUAL RESOLVE <token>
//   MANUAL CATALOG STATUS
//   MANUAL CATALOG TABLES
//   MANUAL CATALOG COUNTS
//   MANUAL CATALOG RESOLVE <token>
//   MANUAL SECTIONS
//   MANUAL MEDIA
//   MANUAL REVIEW
//
// notes:
//   MANUAL is read-only.
//   MANUAL reports manualgen catalog status, resolver behavior, and accepted MAN* evidence.
//   MANUAL does not mutate DBFs, HELP, META, CMDHELPCHK, source files, or publication artifacts.
//   MANUAL is intentionally self-contained in src/cli so the existing src/cli glob can pick it up.
//   Resolver/reader/formatter support modules are not registered commands.
//
// risk:
//   launches_external_process: no
//   executes_host_command: no
//   mutates_table_data: no
//   mutates_filesystem: no
//
// related:
//   HELP
//   DDICT
//   MANSECTION
//

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "cli/output_router.hpp"
#include "textio.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <system_error>
#include <vector>

namespace {

inline std::ostream& out()
{
    return cli::OutputRouter::instance().out();
}

struct ManualTableSpec {
    const char* compact;
    const char* alias;
    int expected_records;
    const char* purpose;
};

static const ManualTableSpec kManualTables[] = {
    {"MANRUN",     "MANUAL_RUNS",         3,  "manualgen run records"},
    {"MANSECTION", "MANUAL_SECTIONS",    25,  "published manual section records"},
    {"MANMEDIA",   "MANUAL_MEDIA",        9,  "media inventory records"},
    {"MANANCHOR",  "MANUAL_ANCHORS",      9,  "media/manual anchor records"},
    {"MANHASH",    "MANUAL_HASHES",      13,  "hash/provenance records"},
    {"MANREVIEW",  "MANUAL_REVIEW",       3,  "review/drift records"},
    {"MANPUB",     "MANUAL_PUBLICATIONS", 4,  "publication records"},
    {"MANAPPX",    "MANUAL_APPENDICES",   6,  "appendix records"},
};

static std::string manual_trim(std::string s)
{
    const auto not_space = [](unsigned char c) { return !std::isspace(c); };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
}

static std::string manual_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static std::vector<std::string> manual_split_upper(std::string raw)
{
    std::vector<std::string> out;
    std::istringstream in(std::move(raw));
    std::string tok;
    while (in >> tok) {
        out.push_back(manual_upper(std::move(tok)));
    }
    return out;
}

static bool manual_exists(const std::filesystem::path& p)
{
    std::error_code ec;
    return std::filesystem::exists(p, ec);
}

static std::filesystem::path manual_catalog_dbf_dir_from_repo(const std::filesystem::path& repo)
{
    return repo / "docs" / "manuals" / "developer" / "manualgen" /
           "accepted_catalogs" / "man_catalog_v1" / "dbf";
}

static std::filesystem::path manual_find_repo_root()
{
    std::error_code ec;
    std::filesystem::path p = std::filesystem::current_path(ec);
    if (ec) {
        return std::filesystem::path{"."};
    }

    for (int i = 0; i < 10; ++i) {
        const auto dbf_dir = manual_catalog_dbf_dir_from_repo(p);
        if (manual_exists(dbf_dir)) {
            return p;
        }

        const auto manual_schema = p / "dottalkpp" / "data" / "workspaces" / "manual.dtschema";
        if (manual_exists(manual_schema)) {
            return p;
        }

        if (!p.has_parent_path() || p.parent_path() == p) {
            break;
        }
        p = p.parent_path();
    }

    return std::filesystem::current_path(ec);
}

static const ManualTableSpec* manual_resolve_table(const std::string& token)
{
    const std::string u = manual_upper(token);
    for (const auto& t : kManualTables) {
        if (u == t.compact || u == t.alias) {
            return &t;
        }
    }
    return nullptr;
}

static std::filesystem::path manual_table_path(const std::filesystem::path& dbf_dir,
                                               const ManualTableSpec& table)
{
    return dbf_dir / (std::string(table.compact) + ".dbf");
}

static void print_manual_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ManualUsageTitle);
    out()
        << "  MANUAL\n"
        << "  MANUAL USAGE\n"
        << "  MANUAL STATUS\n"
        << "  MANUAL TABLES\n"
        << "  MANUAL COUNTS\n"
        << "  MANUAL RESOLVE <token>\n"
        << "  MANUAL CATALOG STATUS\n"
        << "  MANUAL CATALOG TABLES\n"
        << "  MANUAL CATALOG COUNTS\n"
        << "  MANUAL CATALOG RESOLVE <token>\n"
        << "  MANUAL SECTIONS\n"
        << "  MANUAL MEDIA\n"
        << "  MANUAL REVIEW\n";
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ManualNotesTitle);
    out() << "  - "
          << cli::cmdout::message_text(dottalk::helpdata::MessageId::ManualReadOnlyNote)
          << "\n";
    out() << "  - "
          << cli::cmdout::message_text(dottalk::helpdata::MessageId::ManualReportsEvidenceNote)
          << "\n";
    out() << "  - "
          << cli::cmdout::message_text(dottalk::helpdata::MessageId::ManualDoesNotMutateNote)
          << "\n";
}

static void print_manual_catalog_status()
{
    const auto repo = manual_find_repo_root();
    const auto dbf_dir = manual_catalog_dbf_dir_from_repo(repo);
    int present = 0;
    for (const auto& t : kManualTables) {
        if (manual_exists(manual_table_path(dbf_dir, t))) {
            ++present;
        }
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::ManualCatalogStatusTitle);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ManualStatusModeLine);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualStatusRepoRootLine,
        {{"value", repo.string()}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualStatusAcceptedDbfDirLine,
        {{"value", dbf_dir.string()}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualStatusAcceptedDbfDirExistsLine,
        {{"value", std::to_string(manual_exists(dbf_dir) ? 1 : 0)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualStatusExpectedTablesLine,
        {{"value", std::to_string(static_cast<int>(sizeof(kManualTables) / sizeof(kManualTables[0])))}} );
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualStatusPresentTablesLine,
        {{"value", std::to_string(present)}});
}

static void print_manual_catalog_tables()
{
    const auto repo = manual_find_repo_root();
    const auto dbf_dir = manual_catalog_dbf_dir_from_repo(repo);

    cli::cmdout::print_message(dottalk::helpdata::MessageId::ManualCatalogTablesTitle);
    for (const auto& t : kManualTables) {
        const auto path = manual_table_path(dbf_dir, t);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::ManualTableLine,
            {
                {"compact", t.compact},
                {"alias", t.alias},
                {"expected", std::to_string(t.expected_records)},
                {"exists", std::to_string(manual_exists(path) ? 1 : 0)},
                {"purpose", t.purpose}
            });
    }
}

static void print_manual_catalog_counts()
{
    const auto repo = manual_find_repo_root();
    const auto dbf_dir = manual_catalog_dbf_dir_from_repo(repo);

    cli::cmdout::print_message(dottalk::helpdata::MessageId::ManualCatalogCountsTitle);
    out() << "  "
          << cli::cmdout::message_text(dottalk::helpdata::MessageId::ManualCatalogCountsNote)
          << "\n";
    for (const auto& t : kManualTables) {
        const auto path = manual_table_path(dbf_dir, t);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::ManualCountLine,
            {
                {"compact", t.compact},
                {"expected", std::to_string(t.expected_records)},
                {"exists", std::to_string(manual_exists(path) ? 1 : 0)}
            });
    }
}

static void print_manual_resolve(const std::string& token)
{
    const auto* table = manual_resolve_table(token);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ManualCatalogResolveTitle);
    if (!table) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::ManualResolveRequestedTokenLine,
            {{"value", token}});
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::ManualResolveResolvedLine,
            {{"value", "0"}});
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::ManualResolveMessageLine,
            {{"value", cli::cmdout::message_text(dottalk::helpdata::MessageId::ManualResolveUnknownToken)}});
        return;
    }

    const auto repo = manual_find_repo_root();
    const auto dbf_dir = manual_catalog_dbf_dir_from_repo(repo);
    const auto path = manual_table_path(dbf_dir, *table);

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualResolveRequestedTokenLine,
        {{"value", token}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualResolveResolvedLine,
        {{"value", "1"}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualResolveCompactNameLine,
        {{"value", table->compact}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualResolveAliasCandidateLine,
        {{"value", table->alias}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualResolvePhysicalTableLine,
        {{"value", path.string()}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualResolveDbfExistsLine,
        {{"value", std::to_string(manual_exists(path) ? 1 : 0)}});
}

static void print_manual_table_focus(const std::string& title, const char* table_name)
{
    const auto* table = manual_resolve_table(table_name);
    out() << title << "\n";
    if (!table) {
        out() << "  "
              << cli::cmdout::message_text(dottalk::helpdata::MessageId::ManualInternalTableSpecMissing)
              << "\n";
        return;
    }

    const auto repo = manual_find_repo_root();
    const auto dbf_dir = manual_catalog_dbf_dir_from_repo(repo);
    const auto path = manual_table_path(dbf_dir, *table);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualFocusCompactNameLine,
        {{"value", table->compact}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualFocusAliasCandidateLine,
        {{"value", table->alias}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualFocusExpectedRecordsLine,
        {{"value", std::to_string(table->expected_records)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualFocusDbfExistsLine,
        {{"value", std::to_string(manual_exists(path) ? 1 : 0)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ManualFocusPhysicalTableLine,
        {{"value", path.string()}});
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ManualFocusDetailFutureNoteLine);
}

static bool is_usage_request(const std::vector<std::string>& args)
{
    if (args.empty()) {
        return false;
    }
    return args[0] == "USAGE" || args[0] == "HELP" || args[0] == "?";
}

} // namespace

void cmd_MANUAL(xbase::DbArea&, std::istringstream& iss)
{
    std::string rest;
    std::getline(iss, rest);
    rest = manual_trim(std::move(rest));

    auto args = manual_split_upper(rest);
    if (!args.empty() && args[0] == "MANUAL") {
        args.erase(args.begin());
    }

    if (is_usage_request(args)) {
        print_manual_usage();
        return;
    }

    if (args.empty()) {
        print_manual_catalog_status();
        return;
    }

    if (args[0] == "CATALOG" && args.size() == 1) {
        print_manual_catalog_status();
        return;
    }

    if (args[0] == "STATUS") {
        print_manual_catalog_status();
        return;
    }
    if (args[0] == "TABLES") {
        print_manual_catalog_tables();
        return;
    }
    if (args[0] == "COUNTS") {
        print_manual_catalog_counts();
        return;
    }
    if (args.size() >= 2 && args[0] == "RESOLVE") {
        print_manual_resolve(args[1]);
        return;
    }

    if (args.size() >= 2 && args[0] == "CATALOG" && args[1] == "STATUS") {
        print_manual_catalog_status();
        return;
    }
    if (args.size() >= 2 && args[0] == "CATALOG" && args[1] == "TABLES") {
        print_manual_catalog_tables();
        return;
    }
    if (args.size() >= 2 && args[0] == "CATALOG" && args[1] == "COUNTS") {
        print_manual_catalog_counts();
        return;
    }
    if (args.size() >= 3 && args[0] == "CATALOG" && args[1] == "RESOLVE") {
        print_manual_resolve(args[2]);
        return;
    }

    if (args[0] == "SECTIONS") {
        print_manual_table_focus(
            cli::cmdout::message_text(dottalk::helpdata::MessageId::ManualSectionsTitle),
            "MANSECTION");
        return;
    }
    if (args[0] == "MEDIA") {
        print_manual_table_focus(
            cli::cmdout::message_text(dottalk::helpdata::MessageId::ManualMediaTitle),
            "MANMEDIA");
        print_manual_table_focus(
            cli::cmdout::message_text(dottalk::helpdata::MessageId::ManualMediaAnchorsTitle),
            "MANANCHOR");
        return;
    }
    if (args[0] == "REVIEW") {
        print_manual_table_focus(
            cli::cmdout::message_text(dottalk::helpdata::MessageId::ManualReviewTitle),
            "MANREVIEW");
        return;
    }

    cli::cmdout::print_prefixed_message(
        "MANUAL",
        dottalk::helpdata::MessageId::ManualUnsupportedSubcommand);
}
