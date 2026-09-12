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

// AIF-118 shape, removed: STATUS used to print the literal 72 beside an array
// whose eight row counts happen to sum to 72. Two declarations of one number,
// and nothing made them agree. This derives it, so editing the array can no
// longer leave the total lying.
constexpr int manstar_baseline_rows() {
    int total = 0;
    for (const auto& t : kManstarTables) total += t.rows;
    return total;
}

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
    // Every number below is a COMPILE-TIME LITERAL. This command opens no
    // table and reads no catalog, so it cannot report one that is empty,
    // missing, stale, or larger than it was when kManstarTables was written.
    // The old text said "runtime catalog baseline: GREEN" and "Read-only
    // visibility smoke: GREEN" -- two lines that could never say anything
    // else, and one of them contained the word RUNTIME. A status that is the
    // same whether the thing is healthy or absent is not a status, so the
    // output now labels itself as the transcript it is.
    std::cout << "MANSTAR compiled baseline (not a live catalog read)\n";
    std::cout << "  source        : kManstarTables, compiled into this binary\n";
    std::cout << "  MAN* tables   : " << kManstarTables.size() << "  (array length)\n";
    std::cout << "  MAN* rows     : " << manstar_baseline_rows()
              << "  (sum of the array's row counts)\n";
    std::cout << "  baseline state: GREEN as recorded -- this is a constant, "
                 "not a check, and can never report otherwise\n";
    std::cout << "  live catalog  : NOT INSPECTED. MANSTAR has no catalog "
                 "reader; see the contract note in this file.\n";
    std::cout << "  registration  : operator-owned\n";
}

void manstar_tables() {
    std::cout << "MANSTAR TABLES -- compiled baseline, not read from the catalog\n";
    std::cout << "TABLE        ROWS PRIMARY_TAG\n";
    for (const auto& t : kManstarTables) {
        std::cout << t.name << " " << t.rows << " " << t.tag << "\n";
    }
}

void manstar_stub_report(const std::string& sub) {
    // SECTIONS, MEDIA, REVIEW and ANCHORS all arrive here. Echoing `sub` back
    // made each one look like it had done something specific to that name.
    // It had not. The echo stays, because it confirms what was typed, but the
    // text now says plainly that the four are one stub.
    std::cout << "MANSTAR " << sub << ": NOT IMPLEMENTED (stub).\n";
    std::cout << "  SECTIONS, MEDIA, REVIEW and ANCHORS all reach this same "
                 "stub -- none of them reads its table.\n";
    std::cout << "  This first compiled surface reports MANSTAR availability "
                 "only; table-specific readers are not wired.\n";
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

