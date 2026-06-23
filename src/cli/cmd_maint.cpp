// cmd_maint.cpp
// DotTalk++ native MAINT command
// First-wave maintenance/SDLC inspection surface.
//
// @dottalk.usage v1
// owner: DOT|MAINT
// command: MAINT
// category: maintenance
// status: experimental
// mutates: none
// summary: Inspect DotTalk++ maintenance lanes, cookbooks, status, and protected-system boundaries.
// syntax: MAINT [USAGE|STATUS|LANES|COOKBOOK|BOUNDARY|BBOX]
// usage: MAINT
// usage: MAINT USAGE
// usage: MAINT STATUS
// usage: MAINT LANES
// usage: MAINT COOKBOOK
// usage: MAINT BOUNDARY
// usage: MAINT BBOX
// note: MAINT is read-only first wave.
// note: MAINT does not run maintenance scripts or mutate HELP, CMDHELPCHK, DBFs, source, runtime scripts, or publications.
// note: MAINT explains the maintenance/SDLC control surface; BBOX teaches the Blackbox model.
// related: BBOX
// related: CMDHELP
// related: DDICT
// related: MANUAL
// @dottalk.end

#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

std::string trim_copy(const std::string& value) {
    const auto first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) {
        return std::string();
    }
    const auto last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

std::string upper_copy(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
        return static_cast<char>(std::toupper(ch));
    });
    return value;
}

void print_usage() {
    std::cout
        << "Usage:\n"
        << "  MAINT\n"
        << "  MAINT USAGE\n"
        << "  MAINT STATUS\n"
        << "  MAINT LANES\n"
        << "  MAINT COOKBOOK\n"
        << "  MAINT BOUNDARY\n"
        << "  MAINT BBOX\n"
        << "Notes:\n"
        << "  - MAINT is read-only first wave.\n"
        << "  - MAINT inspects maintenance lanes, cookbooks, status, and boundaries.\n"
        << "  - MAINT does not run scripts or mutate HELP, CMDHELPCHK, DBFs, source, runtime scripts, or publications.\n";
}

void print_status() {
    std::cout
        << "MAINT STATUS\n"
        << "  mode: read-only\n"
        << "  purpose: inspect DotTalk++ maintenance/SDLC lanes and boundaries\n"
        << "  native app: yes, C++ command surface\n"
        << "  executes maintenance scripts: no\n"
        << "  mutates protected systems: no\n"
        << "  related teaching surface: BBOX\n";
}

void print_lanes() {
    std::cout
        << "MAINT LANES\n"
        << "  comments    - source comments and @dottalk.usage evidence\n"
        << "  help        - HELP, CMDHELP, DOTREF, and help-route evidence\n"
        << "  cmdhelpchk  - HELP/registry/source-contract validation\n"
        << "  manualgen   - developer manual generation and MAN* catalog evidence\n"
        << "  datadict    - DD* / DATA_DICTIONARY_* catalog and DDICT evidence\n"
        << "  messaging   - message catalog, language/locale, and output text migration\n"
        << "  blackbox    - data in, processing, information out teaching model\n"
        << "  maintenance - SDLC cookbooks, gates, boundaries, and closeouts\n";
}

void print_cookbook() {
    std::cout
        << "MAINT COOKBOOK\n"
        << "  docs root   : docs\\maintenance\n"
        << "  script root : dottalkpp\\scripts\\maintenance\n"
        << "  runtime scripts stay under dottalkpp\\data\\scripts\n"
        << "  native source support is reserved under src\\maintenance when needed\n"
        << "  PowerShell is temporary MDO scaffolding; permanent app surface is C++.\n"
        << "  Python 3.12 may support portable external helper/report tooling.\n";
}

void print_boundary() {
    std::cout
        << "MAINT BOUNDARY\n"
        << "  first-wave MAINT is inspection-only.\n"
        << "  It must not mutate:\n"
        << "    - source files\n"
        << "    - HELP DATA or raw HELP DBFs\n"
        << "    - CMDHELPCHK expectations\n"
        << "    - metadata catalogs\n"
        << "    - DBF/CDX/LMDB artifacts\n"
        << "    - runtime scripts\n"
        << "    - publications or media\n"
        << "  Mutation lanes require separate guarded packages and explicit authorization.\n";
}

void print_bbox_relation() {
    std::cout
        << "MAINT BBOX\n"
        << "  BBOX teaches the Blackbox model: data in, processing, information out.\n"
        << "  MAINT inspects the SDLC maintenance controls around those transformations.\n"
        << "  Relationship:\n"
        << "    BBOX explains the model.\n"
        << "    MAINT explains the maintenance process, gates, cookbooks, and boundaries.\n";
}

} // namespace

void cmd_MAINT(xbase::DbArea& area, std::istringstream& iss) {
    (void)area;

    std::string rest;
    std::getline(iss, rest);
    const std::string topic = upper_copy(trim_copy(rest));

    if (topic.empty() || topic == "STATUS") {
        print_status();
        return;
    }
    if (topic == "USAGE" || topic == "HELP") {
        print_usage();
        return;
    }
    if (topic == "LANES") {
        print_lanes();
        return;
    }
    if (topic == "COOKBOOK" || topic.rfind("COOKBOOK ", 0) == 0) {
        print_cookbook();
        return;
    }
    if (topic == "BOUNDARY" || topic == "BOUNDARIES") {
        print_boundary();
        return;
    }
    if (topic == "BBOX" || topic == "BLACKBOX") {
        print_bbox_relation();
        return;
    }

    std::cout
        << "MAINT: unknown topic: " << rest << "\n"
        << "Use MAINT USAGE.\n";
}

