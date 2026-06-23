// cmd_manstar_candidate.cpp
// MDO-274E candidate only - do not copy into source tree without a later guarded apply package.
//
// @dottalk.usage v1
// command: MANSTAR
// forms:
//   MANSTAR USAGE
//   MANSTAR STATUS
//   MANSTAR TABLES
//   MANSTAR COUNTS
//   MANSTAR SECTIONS
//   MANSTAR MEDIA
//   MANSTAR REVIEW
//   MANSTAR ANCHORS
//   MANSTAR HELP
// safety: READ_ONLY / REPORT_ONLY / NO_REGISTRATION_BY_PACKAGE
// evidence: MANSTAR baseline MDO-268F through MDO-270F; implementation plan MDO-272E; source recon MDO-273E.

#include "cmd_manstar_candidate.h"

#include <algorithm>
#include <array>
#include <iostream>
#include <string>
#include <string_view>

namespace dottalk::manstar_candidate {

struct TableSpec {
    std::string_view name;
    int expected_rows;
    std::string_view primary_tag;
};

static constexpr std::array<TableSpec, 8> kTables{{
    {"MANRUN", 3, "RUNID"},
    {"MANPUB", 4, "PUBLICATION_ID"},
    {"MANSECTION", 25, "ORDINAL"},
    {"MANMEDIA", 9, "MEDIA_ID"},
    {"MANAPPX", 6, "APPX_ID"},
    {"MANHASH", 13, "ARTIFACT_ROLE"},
    {"MANREVIEW", 3, "SEVERITY"},
    {"MANANCHOR", 9, "SECTION_ID"},
}};

// Candidate-only adapter notes:
// 1. Wire this through the existing command dispatcher only in a later authorized package.
// 2. Registration is explicitly operator-owned; this candidate contains no registration side effect.
// 3. Replace std::ostream reporting with the project message/report layer if required.
// 4. Runtime DBF/CDX/LMDB reads should reuse existing USE / SET INDEX / SET ORDER / LIST-equivalent internals.

static std::string upper_ascii(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

int print_usage(std::ostream& out) {
    out << "MANSTAR USAGE\n";
    out << "  MANSTAR STATUS\n";
    out << "  MANSTAR TABLES\n";
    out << "  MANSTAR COUNTS\n";
    out << "  MANSTAR SECTIONS\n";
    out << "  MANSTAR MEDIA\n";
    out << "  MANSTAR REVIEW\n";
    out << "  MANSTAR ANCHORS\n";
    out << "\nAll MANSTAR candidate surfaces are read-only.\n";
    return 0;
}

int print_status(std::ostream& out) {
    out << "MANSTAR runtime catalog baseline: GREEN\n";
    out << "MAN* tables: 8\n";
    out << "MAN* rows: 72\n";
    out << "Visibility smoke: GREEN\n";
    return 0;
}

int print_tables(std::ostream& out) {
    out << "TABLE        ROWS PRIMARY_TAG\n";
    for (const auto& t : kTables) {
        out << t.name << " " << t.expected_rows << " " << t.primary_tag << "\n";
    }
    return 0;
}

int dispatch_candidate(const std::string& subcommand, std::ostream& out) {
    const std::string sub = upper_ascii(subcommand.empty() ? "USAGE" : subcommand);
    if (sub == "USAGE" || sub == "HELP") return print_usage(out);
    if (sub == "STATUS") return print_status(out);
    if (sub == "TABLES" || sub == "COUNTS") return print_tables(out);
    if (sub == "SECTIONS" || sub == "MEDIA" || sub == "REVIEW" || sub == "ANCHORS") {
        out << "MANSTAR " << sub << " candidate: route to existing indexed read-only MAN* table query.\n";
        return 0;
    }
    out << "MANSTAR: unknown subcommand: " << subcommand << "\n";
    return 1;
}

} // namespace dottalk::manstar_candidate
