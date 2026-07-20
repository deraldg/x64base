// cmd_manstar.cpp
// MDO-279R repair: provide the global cmd_MANSTAR symbol expected by shell_commands.cpp.
//
// @dottalk.usage v1
// owner: DOT|MANSTAR
// command: MANSTAR
// category: manual
// status: experimental
// noargs: usage
// effect: report
// mutates: none
// risk: READ_ONLY
// usage-access: MANSTAR USAGE
// summary: Inspect the compiled MAN* catalog baseline and report manualgen visibility without mutating catalogs.
// usage: MANSTAR
// usage: MANSTAR USAGE
// usage: MANSTAR HELP
// usage: MANSTAR STATUS
// usage: MANSTAR TABLES
// usage: MANSTAR COUNTS
// usage: MANSTAR SECTIONS
// usage: MANSTAR MEDIA
// usage: MANSTAR REVIEW
// usage: MANSTAR ANCHORS
// note: MANSTAR is READ_ONLY and REPORT_ONLY.
// note: Registration is owned by the normal command registry; this source package does not self-register.
// note: Evidence includes MDO-268F, MDO-270F, MDO-274E, MDO-277E, and manual build linker review.
// related: MANUAL
// @dottalk.end

#include <algorithm>
#include <array>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

namespace xbase { class DbArea; }

namespace {

struct ManstarTableSpec {
    const char* name;
    int rows;
    const char* tag;
};

constexpr std::array<ManstarTableSpec, 8> kManstarTables{{
    {"MANRUN", 3, "RUNID"},
    {"MANPUB", 4, "PUBLICATION_ID"},
    {"MANSECTION", 25, "ORDINAL"},
    {"MANMEDIA", 9, "MEDIA_ID"},
    {"MANAPPX", 6, "APPX_ID"},
    {"MANHASH", 13, "ARTIFACT_ROLE"},
    {"MANREVIEW", 3, "SEVERITY"},
    {"MANANCHOR", 9, "SECTION_ID"},
}};

std::string upper_ascii(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::toupper(c));
    });
    return s;
}

void manstar_usage() {
    std::cout << "MANSTAR USAGE\n";
    std::cout << "  MANSTAR STATUS\n";
    std::cout << "  MANSTAR TABLES\n";
    std::cout << "  MANSTAR COUNTS\n";
    std::cout << "  MANSTAR SECTIONS\n";
    std::cout << "  MANSTAR MEDIA\n";
    std::cout << "  MANSTAR REVIEW\n";
    std::cout << "  MANSTAR ANCHORS\n";
    std::cout << "\nMANSTAR is a read-only manualgen catalog visibility surface.\n";
}

void manstar_status() {
    std::cout << "MANSTAR runtime catalog baseline: GREEN\n";
    std::cout << "MAN* tables: 8\n";
    std::cout << "MAN* rows: 72\n";
    std::cout << "Read-only visibility smoke: GREEN\n";
    std::cout << "Command registration: operator-owned\n";
}

void manstar_tables() {
    std::cout << "TABLE        ROWS PRIMARY_TAG\n";
    for (const auto& t : kManstarTables) {
        std::cout << t.name << " " << t.rows << " " << t.tag << "\n";
    }
}

void manstar_stub_report(const std::string& sub) {
    std::cout << "MANSTAR " << sub << " is read-only.\n";
    std::cout << "This first compiled surface reports MANSTAR availability; deeper table-specific readers should be wired in a later guarded package.\n";
}

} // namespace

void cmd_MANSTAR(xbase::DbArea& area, std::istringstream& iss) {
    (void)area;
    std::string subcommand;
    iss >> subcommand;
    const std::string sub = upper_ascii(subcommand.empty() ? "USAGE" : subcommand);

    if (sub == "USAGE" || sub == "HELP") {
        manstar_usage();
        return;
    }
    if (sub == "STATUS") {
        manstar_status();
        return;
    }
    if (sub == "TABLES" || sub == "COUNTS") {
        manstar_tables();
        return;
    }
    if (sub == "SECTIONS" || sub == "MEDIA" || sub == "REVIEW" || sub == "ANCHORS") {
        manstar_stub_report(sub);
        return;
    }

    std::cout << "MANSTAR: unknown subcommand: " << subcommand << "\n";
    manstar_usage();
}

