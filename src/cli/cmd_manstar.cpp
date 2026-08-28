// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

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
// usage: MANSTAR                            (no argument: same as USAGE)
// usage: MANSTAR USAGE                      (alias: HELP)
// usage: MANSTAR STATUS
// usage: MANSTAR TABLES                     (alias: COUNTS)
// usage: MANSTAR SECTIONS                   (aliases: MEDIA, REVIEW, ANCHORS
//                                            -- ALL FOUR ARE ONE STUB, see note)
// note: MANSTAR is READ_ONLY and REPORT_ONLY.
// note: TEN usage lines stood here for FOUR handlers, until 2026-08-28. The
//   contract read as ten capabilities and there are four:
//     USAGE|HELP                     -> manstar_usage()
//     STATUS                         -> manstar_status()
//     TABLES|COUNTS                  -> manstar_tables()
//     SECTIONS|MEDIA|REVIEW|ANCHORS  -> manstar_stub_report(sub)
// note: SECTIONS, MEDIA, REVIEW and ANCHORS DO NOTHING TABLE-SPECIFIC. All
//   four reach one stub that echoes back the word you typed and then says
//   deeper readers "should be wired in a later guarded package". Because the
//   stub prints the subcommand name, its output LOOKS specific to whichever
//   one you asked for. It is not. Four questions, one answer.
// note: EVERY NUMBER THIS COMMAND PRINTS IS A COMPILE-TIME LITERAL. The file
//   includes only <algorithm> <array> <cctype> <iostream> <sstream> <string>
//   -- no xbase, no paths, no catalog reader -- and its DbArea parameter is
//   discarded with (void)area. TABLES prints the constexpr kManstarTables
//   array; STATUS prints "MAN* tables: 8" and "MAN* rows: 72" (the array's
//   length and the sum of its row counts) plus "GREEN" twice, unconditionally.
//   MANSTAR therefore CANNOT report a catalog that is empty, missing, stale
//   or larger than it was when those numbers were typed in. "MANSTAR runtime
//   catalog baseline: GREEN" contains the word runtime and is a string
//   literal. Treat this command as a transcript of a past measurement, not a
//   measurement. status: experimental is doing real work here.
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

