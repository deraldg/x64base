// src/cli/cmd_idx.cpp
//
// IDX is the EDU IDX command surface: a memory-only educational index lab.
// It is intentionally orthogonal to persistent index families.
//
// Supported Phase 1 commands:
//   IDX ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]
//   IDX LIST
//   IDX DROP <tag>
//   IDX DROP ALL
//   IDX HELP
//
// IDX does not write .inx files and does not participate in SET ORDER,
// REINDEX, WORKSPACE restore, IndexManager, or IIndexBackend.

// @dottalk.usage v1
// owner: DOT|IDX
// command: IDX
// category: education
// status: supported
// noargs: report
// effect: mixed
// mutates: edu-idx-memory
// usage-access: IDX USAGE
// summary:
//   Memory-only educational index lab for teaching sorting and index concepts
//   without writing persistent INX/CNX/CDX files.
//
// usage:
//   IDX
//   IDX USAGE
//   IDX ON <field|#n> TAG <name>
//   IDX ON <field|#n> TAG <name> SORT <algo>
//   IDX ON <field|#n> TAG <name> <algo>
//   IDX ON <field|#n> TAG <name> ASC
//   IDX ON <field|#n> TAG <name> DESC
//   IDX LIST
//   IDX DROP <tag>
//   IDX DROP ALL
//
// examples:
//   IDX ON LNAME TAG lname_std
//   IDX ON LNAME TAG lname_bubble BUBBLE
//   IDX ON LNAME TAG lname_bubble2 SORT BUBBLE DESC
//
// notes:
//   IDX with no arguments prints help/usage.
//   IDX is memory-only and does not write .inx files.
//   IDX does not participate in SET ORDER, REINDEX, WORKSPACE restore, IndexManager, or IIndexBackend.
//   Use INDEX for persistent index files.
//   SORT algorithms currently include STD and BUBBLE.
//
// risk:
//   mutates_edu_idx_memory: build/drop/drop all
//   writes_index_files: no
//   mutates_table_data: no
//
// related:
//   INDEX
//   SET ORDER
//   REINDEX
//

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "cli/edu_idx.hpp"
#include "help/helpdata_messages.hpp"
#include "textio.hpp"

#include <cctype>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

using xbase::DbArea;

namespace {

std::string upper_copy(std::string s) {
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

std::string elapsed_text(uint64_t us) {
    std::ostringstream out;
    if (us >= 1000) {
        out << (us / 1000) << " ms";
    } else {
        out << us << " us";
    }
    return out.str();
}

void print_help() {
    cli::cmdout::print_message(dottalk::helpdata::MessageId::IdxUsageText);
}

bool parse_build_args(const std::string& first,
                      std::istringstream& in,
                      dottalk::edu_idx::BuildRequest& request,
                      std::string& error) {
    if (upper_copy(first) != "ON") {
        error = cli::cmdout::message_text(dottalk::helpdata::MessageId::IdxExpectedOnText);
        return false;
    }

    if (!(in >> request.field_token) || request.field_token.empty()) {
        error = cli::cmdout::message_text(dottalk::helpdata::MessageId::IdxMissingFieldTokenText);
        return false;
    }

    std::string tagTok;
    if (!(in >> tagTok) || upper_copy(tagTok) != "TAG") {
        error = cli::cmdout::message_text(dottalk::helpdata::MessageId::IdxExpectedTagText);
        return false;
    }

    if (!(in >> request.tag) || request.tag.empty()) {
        error = cli::cmdout::message_text(dottalk::helpdata::MessageId::IdxMissingTagNameText);
        return false;
    }

    bool saw_sort = false;
    bool saw_direction = false;

    std::string tok;
    while (in >> tok) {
        const std::string up = upper_copy(tok);

        if (up == "SORT") {
            if (saw_sort) {
                error = cli::cmdout::message_text(dottalk::helpdata::MessageId::IdxDuplicateSortOptionText);
                return false;
            }

            std::string algoTok;
            if (!(in >> algoTok)) {
                error = cli::cmdout::message_text(dottalk::helpdata::MessageId::IdxSortRequiresAlgorithmText);
                return false;
            }

            dottalk::edu_idx::SortAlgo algo{};
            if (!dottalk::edu_idx::parse_sort_algo(algoTok, algo)) {
                error = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::IdxUnknownSortAlgorithmText,
                    {{"algorithm", algoTok}});
                return false;
            }

            request.sort_algo = algo;
            saw_sort = true;
            continue;
        }

        dottalk::edu_idx::SortDirection dir{};
        if (dottalk::edu_idx::parse_direction(tok, dir)) {
            if (saw_direction) {
                error = cli::cmdout::message_text(dottalk::helpdata::MessageId::IdxDuplicateDirectionOptionText);
                return false;
            }
            request.direction = dir;
            saw_direction = true;
            continue;
        }

        dottalk::edu_idx::SortAlgo algo{};
        if (!saw_sort && dottalk::edu_idx::parse_sort_algo(tok, algo)) {
            request.sort_algo = algo;
            saw_sort = true;
            continue;
        }

        error = cli::cmdout::message_text(
            dottalk::helpdata::MessageId::IdxUnexpectedTokenText,
            {{"token", tok}});
        return false;
    }

    return true;
}

void print_build_result(const dottalk::edu_idx::BuildRequest& request,
                        const dottalk::edu_idx::BuildResult& result) {
    const char* verb = result.replaced ? "replaced" : "created";

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::IdxBuildCreatedText,
        {{"verb", verb}, {"tag", result.tag}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::IdxExprLineText,
        {{"value", request.field_token}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::IdxSortLineText,
        {{"value", dottalk::edu_idx::to_string(request.sort_algo)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::IdxDirectionLineText,
        {{"value", dottalk::edu_idx::to_string(request.direction)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::IdxRecordsLineText,
        {{"indexed", std::to_string(result.build.records_indexed)},
         {"scanned", std::to_string(result.build.records_scanned)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::IdxDeletedLineText,
        {{"count", std::to_string(result.build.deleted_skipped)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::IdxBuildElapsedLineText,
        {{"value", elapsed_text(result.build.elapsed_us)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::IdxSortElapsedLineText,
        {{"value", elapsed_text(result.build.sort.elapsed_us)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::IdxComparisonsLineText,
        {{"value", std::to_string(result.build.sort.comparisons)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::IdxSwapsLineText,
        {{"value", std::to_string(result.build.sort.swaps)}});
}

void print_list() {
    const auto rows = dottalk::edu_idx::list_indexes();
    if (rows.empty()) {
        cli::cmdout::print_prefixed_message("IDX", dottalk::helpdata::MessageId::IdxNoMemoryIndexesText);
        return;
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::IdxMemoryIndexesTitle);
    cli::cmdout::print_line("");
    cli::cmdout::print_message(dottalk::helpdata::MessageId::IdxListHeaderLineText);
    std::cout << std::left
              << std::setw(18) << "TAG"
              << std::setw(12) << "EXPR"
              << std::setw(10) << "SORT"
              << std::setw(6)  << "DIR"
              << std::setw(10) << "ENTRIES"
              << "BUILD"
              << "\n";

    for (const auto& r : rows) {
        std::cout << std::left
                  << std::setw(18) << r.tag
                  << std::setw(12) << r.expr
                  << std::setw(10) << r.sort_algo
                  << std::setw(6)  << r.direction
                  << std::setw(10) << r.entries
                  << elapsed_text(r.build_us)
                  << "\n";
    }
}

void run_drop(std::istringstream& in) {
    std::string tag;
    if (!(in >> tag) || tag.empty()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::IdxDropUsageText);
        return;
    }

    if (upper_copy(tag) == "ALL") {
        const auto before = dottalk::edu_idx::list_indexes().size();
        dottalk::edu_idx::drop_all_indexes();
        if (before == 0) {
            cli::cmdout::print_prefixed_message("IDX", dottalk::helpdata::MessageId::IdxNoMemoryIndexesToDropText);
        } else {
            cli::cmdout::print_prefixed_message("IDX", dottalk::helpdata::MessageId::IdxDroppedAllText);
        }
        return;
    }

    if (dottalk::edu_idx::drop_index(tag)) {
        cli::cmdout::print_prefixed_message(
            "IDX", dottalk::helpdata::MessageId::IdxDroppedMemoryIndexText,
            {{"tag", tag}});
    } else {
        cli::cmdout::print_prefixed_message(
            "IDX", dottalk::helpdata::MessageId::IdxMemoryIndexNotFoundText,
            {{"tag", tag}});
    }
}

} // namespace

void cmd_IDX(DbArea& A, std::istringstream& in) {
    std::string first;
    if (!(in >> first)) {
        print_help();
        return;
    }

    const std::string cmd = upper_copy(first);

    if (cmd == "USAGE" || cmd == "HELP" || cmd == "?" || cmd == "/?" || cmd == "-H" || cmd == "--HELP") {
        print_help();
        return;
    }

    if (cmd == "LIST") {
        print_list();
        return;
    }

    if (cmd == "DROP") {
        run_drop(in);
        return;
    }

    if (cmd == "ON") {
        dottalk::edu_idx::BuildRequest request{};
        std::string error;

        if (!parse_build_args(first, in, request, error)) {
            cli::cmdout::print_info("IDX", error);
            cli::cmdout::print_message(dottalk::helpdata::MessageId::IdxBuildUsageText);
            return;
        }

        auto result = dottalk::edu_idx::build_and_store(A, request);
        if (!result.ok) {
            cli::cmdout::print_info("IDX", result.message);
            return;
        }

        print_build_result(request, result);
        return;
    }

    cli::cmdout::print_prefixed_message(
        "IDX", dottalk::helpdata::MessageId::IdxUnknownCommandText,
        {{"command", first}});
    print_help();
}

// Shell registry entrypoint.
// The shell registers command name IDX to edu_IDX. Keep cmd_IDX as the
// implementation name for older call sites, and export edu_IDX for the
// current education-command registry contract.
void edu_IDX(DbArea& A, std::istringstream& in) {
    cmd_IDX(A, in);
}
