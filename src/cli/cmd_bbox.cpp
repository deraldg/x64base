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
// usage: BBOX CONTRACTS
// note: BBOX is read-only and educational.
// note: BBOX explains SelfDoc maintenance lanes as data -> process -> information systems.
// note: BBOX does not mutate DBFs, HELP, META, CMDHELPCHK, source files, runtime scripts, or publication artifacts.

#include "xbase.hpp"
#include "cli/command_output.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>

namespace {

using dottalk::helpdata::MessageId;

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
    cli::cmdout::print_message(MessageId::BBoxUsageText);
}

void print_bbox_model() {
    cli::cmdout::print_message(MessageId::BBoxModelText);
}

void print_bbox_lanes() {
    cli::cmdout::print_message(MessageId::BBoxLanesText);
}

void print_comments_lane() {
    cli::cmdout::print_message(MessageId::BBoxCommentsLaneText);
}

void print_help_lane() {
    cli::cmdout::print_message(MessageId::BBoxHelpLaneText);
}

void print_manualgen_lane() {
    cli::cmdout::print_message(MessageId::BBoxManualgenLaneText);
}

void print_datadict_lane() {
    cli::cmdout::print_message(MessageId::BBoxDatadictLaneText);
}

void print_messaging_lane() {
    cli::cmdout::print_message(MessageId::BBoxMessagingLaneText);
}

void print_maint_lane() {
    cli::cmdout::print_message(MessageId::BBoxMaintLaneText);
}

void print_contracts_lane() {
    cli::cmdout::print_line("Contracts lane");
    cli::cmdout::print_line("  Data in:");
    cli::cmdout::print_line("    chat decisions, source USAGE blocks, @dottalk.contract annotations, HELP/CMDHELP evidence, governance docs, database/UI/build/safety contracts");
    cli::cmdout::print_line("  Process:");
    cli::cmdout::print_line("    intake -> classify -> register -> cross-link -> validate -> promote -> supersede");
    cli::cmdout::print_line("  Information out:");
    cli::cmdout::print_line("    contract registry, lifecycle state, intake queue, scan reports, drift reports, promotion tasks");
    cli::cmdout::print_line("  Manager mode:");
    cli::cmdout::print_line("    MAINT CONTRACTS is the read-only manager/inspector; BBOX CONTRACTS explains the model.");
}

} // namespace

void cmd_BBOX(xbase::DbArea& /*area*/, std::istringstream& iss) {
    const std::string arg = upper_copy(remaining_args(iss));

    if (arg.empty() || arg == "MODEL") {
        print_bbox_model();
        if (arg.empty()) {
            cli::cmdout::print_line("");
            print_bbox_lanes();
        }
        return;
    }

    if (arg == "USAGE") {
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

    if (arg == "CONTRACTS" || arg == "CONTRACT") {
        print_contracts_lane();
        return;
    }

    cli::cmdout::print_prefixed_message(
        "BBOX",
        MessageId::BBoxUnknownTopic,
        {{"topic", arg}});
    print_bbox_usage();
}
