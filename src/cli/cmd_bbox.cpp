// cmd_bbox.cpp
// DotTalk++ native Blackbox educational command surface.
//
// @dottalk.usage v1
// owner: DOT|BBOX
// command: BBOX
// category: education
// status: experimental
// effect: report
// mutates: none
// usage-access: no-open-table
// summary: Teach and inspect the Blackbox model: data enters a processing system and information comes out.
// usage: BBOX
// usage: BBOX USAGE
// usage: BBOX MODEL
// usage: BBOX LANES
// usage: BBOX COMMENTS
// usage: BBOX HELP
// usage: BBOX MANUALGEN
// usage: BBOX DATADICT
// usage: BBOX MESSAGING
// usage: BBOX MAINT
// note: BBOX is read-only and educational.
// note: BBOX explains SelfDoc maintenance lanes as data -> process -> information systems.
// note: BBOX does not mutate DBFs, HELP, META, CMDHELPCHK, source files, runtime scripts, or publication artifacts.

#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

std::string trim_copy(std::string s) {
    auto not_space = [](unsigned char ch) { return !std::isspace(ch); };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
}

std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) {
        return static_cast<char>(std::toupper(ch));
    });
    return s;
}

std::string remaining_args(std::istringstream& iss) {
    std::string rest;
    std::getline(iss, rest);
    return trim_copy(rest);
}

void print_bbox_usage() {
    std::cout
        << "Usage:\n"
        << "  BBOX\n"
        << "  BBOX USAGE\n"
        << "  BBOX MODEL\n"
        << "  BBOX LANES\n"
        << "  BBOX COMMENTS\n"
        << "  BBOX HELP\n"
        << "  BBOX MANUALGEN\n"
        << "  BBOX DATADICT\n"
        << "  BBOX MESSAGING\n"
        << "  BBOX MAINT\n"
        << "Notes:\n"
        << "  - BBOX is read-only and educational.\n"
        << "  - BBOX teaches the Blackbox model: data in, processing, information out.\n"
        << "  - BBOX does not mutate DBFs, HELP, META, CMDHELPCHK, source, scripts, or publications.\n";
}

void print_bbox_model() {
    std::cout
        << "BLACKBOX MODEL\n"
        << "  DATA IN\n"
        << "    source comments, usage contracts, DBFs, scripts, Markdown, media, source code, catalogs\n"
        << "\n"
        << "  PROCESSING\n"
        << "    scan, harvest, classify, import, build, validate, publish, smoke test\n"
        << "\n"
        << "  INFORMATION OUT\n"
        << "    HELP, CMDHELP, manuals, data dictionary, comments workspace, MAN*/DD*/SRC* catalogs, reports, diagrams\n"
        << "\n"
        << "  CONTROL\n"
        << "    backup, rollback, boundary ledger, runtime smoke, savepoint, next gate\n";
}

void print_bbox_lanes() {
    std::cout
        << "BBOX LANES\n"
        << "  COMMENTS   source comments and @dottalk.usage -> SRC* evidence catalogs\n"
        << "  HELP       registry, DOTREF, usage contracts -> HELP DATA and CMDHELP\n"
        << "  MANUALGEN  manual sections/media/manifests -> MAN* catalog and published manuals\n"
        << "  DATADICT   repo/schema/help evidence -> DD* catalog and DDICT runtime view\n"
        << "  MESSAGING  hard-coded text/message IDs/locales -> typed localized runtime messages\n"
        << "  CMDHELPCHK command/help contracts -> validation evidence\n"
        << "  MAINT      maintenance lanes, cookbooks, gates, and read-only status\n";
}

void print_comments_lane() {
    std::cout
        << "COMMENTS BLACKBOX\n"
        << "  DATA IN: source files, header comments, @dottalk.usage v1 blocks\n"
        << "  PROCESS: harvest, classify, import, validate, review disposition\n"
        << "  OUT: SRCFILE, SRCBLOCK, SRCLINE, SRCUSAGE, SRCCLASS, SRCDISP, SRCALIAS, MEMO_LINES\n"
        << "  CURRENT WORKSPACE: dottalkpp/data/workspaces/comments.dtschema\n";
}

void print_help_lane() {
    std::cout
        << "HELP BLACKBOX\n"
        << "  DATA IN: command registry, dotref.hpp, foxref.hpp, usage contracts, curated rows, source-mined facts\n"
        << "  PROCESS: CMDHELP BUILD, HELP DATA generation, validation, runtime smoke\n"
        << "  OUT: help_line.dbf, help_topic.dbf, help_artifacts.dbf, commands.dbf, cmd_args.dbf, HELP/CMDHELP output\n"
        << "  NOTE: CMDHELP and HELP /DOT are related consumers but not identical proof surfaces.\n";
}

void print_manualgen_lane() {
    std::cout
        << "MANUALGEN BLACKBOX\n"
        << "  DATA IN: section files, appendices, media anchors, review queues, manifests\n"
        << "  PROCESS: assemble, normalize, validate, publish, catalog, runtime smoke\n"
        << "  OUT: published manual, MAN* catalog, MANUAL runtime command, regeneration evidence\n";
}

void print_datadict_lane() {
    std::cout
        << "DATADICT BLACKBOX\n"
        << "  DATA IN: data dictionary manifests, DD* candidate rows, x64 DATA_DICTIONARY_* physical tables\n"
        << "  PROCESS: stage, import, validate, CDX/LMDB build, runtime smoke\n"
        << "  OUT: DD* catalog, DDICT STATUS/TABLES/OBJECTS/FIELDS/TAGS/REL/EVIDENCE\n"
        << "  RULE: use bridge policy; report metadata owner and physical artifact.\n";
}

void print_messaging_lane() {
    std::cout
        << "MESSAGING BLACKBOX\n"
        << "  DATA IN: hard-coded text, message IDs, message arguments, locale/language rows\n"
        << "  PROCESS: extract, catalog, localize, validate placeholders, replace source strings gradually\n"
        << "  OUT: x64base message catalog, localized runtime text, typed warnings/errors/status/help messages\n"
        << "  CONTROL: SET LANGUAGE / SET LOCALE selects message-rendering locale where supported.\n";
}

void print_maint_lane() {
    std::cout
        << "MAINT BLACKBOX\n"
        << "  PURPOSE: developer/SDLC maintenance inspection over documented lanes and cookbooks\n"
        << "  PRIMARY APP: native C++ MAINT surface, planned separately\n"
        << "  EXTERNAL TOOLS: Python 3.12 for portable report tooling; PowerShell only for temporary scaffolding\n"
        << "  RULE: MAINT starts read-only; mutation lanes require explicit guarded packages.\n";
}

} // namespace

void cmd_BBOX(xbase::DbArea& /*area*/, std::istringstream& iss) {
    const std::string arg = upper_copy(remaining_args(iss));

    if (arg.empty() || arg == "MODEL") {
        print_bbox_model();
        if (arg.empty()) {
            std::cout << "\n";
            print_bbox_lanes();
        }
        return;
    }

    if (arg == "USAGE" || arg == "HELP") {
        print_bbox_usage();
        return;
    }

    if (arg == "LANES") {
        print_bbox_lanes();
        return;
    }

    if (arg == "COMMENTS") {
        print_comments_lane();
        return;
    }

    if (arg == "HELPDATA" || arg == "HELP" || arg == "CMDHELP" || arg == "DOTREF") {
        print_help_lane();
        return;
    }

    if (arg == "MANUAL" || arg == "MANUALGEN") {
        print_manualgen_lane();
        return;
    }

    if (arg == "DDICT" || arg == "DATADICT" || arg == "DATA DICTIONARY") {
        print_datadict_lane();
        return;
    }

    if (arg == "MESSAGING" || arg == "MSG") {
        print_messaging_lane();
        return;
    }

    if (arg == "MAINT" || arg == "MAINTENANCE") {
        print_maint_lane();
        return;
    }

    std::cout << "BBOX: unknown topic: " << arg << "\n";
    print_bbox_usage();
}
