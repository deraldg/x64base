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
#include "cli/edu_idx.hpp"
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
    std::cout
        << "IDX is a memory-only educational index lab.\n"
        << "It teaches sorting and index concepts without writing .inx files.\n"
        << "Use INDEX for persistent INX files.\n"
        << "\n"
        << "Usage:\n"
        << "  IDX\n"
        << "  IDX USAGE\n"
        << "  IDX ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]\n"
        << "  IDX LIST\n"
        << "  IDX DROP <tag>\n"
        << "  IDX DROP ALL\n"
        << "  IDX HELP\n"
        << "\n"
        << "Sort algorithms, Phase 1:\n"
        << "  STD       C++ std::sort baseline\n"
        << "  BUBBLE    classroom bubble sort\n"
        << "\n"
        << "Examples:\n"
        << "  IDX ON LNAME TAG lname_std\n"
        << "  IDX ON LNAME TAG lname_bubble BUBBLE\n"
        << "  IDX ON LNAME TAG lname_bubble2 SORT BUBBLE DESC\n";
}

bool parse_build_args(const std::string& first,
                      std::istringstream& in,
                      dottalk::edu_idx::BuildRequest& request,
                      std::string& error) {
    if (upper_copy(first) != "ON") {
        error = "IDX: expected ON.";
        return false;
    }

    if (!(in >> request.field_token) || request.field_token.empty()) {
        error = "IDX: missing field token.";
        return false;
    }

    std::string tagTok;
    if (!(in >> tagTok) || upper_copy(tagTok) != "TAG") {
        error = "IDX: expected TAG.";
        return false;
    }

    if (!(in >> request.tag) || request.tag.empty()) {
        error = "IDX: missing TAG name.";
        return false;
    }

    bool saw_sort = false;
    bool saw_direction = false;

    std::string tok;
    while (in >> tok) {
        const std::string up = upper_copy(tok);

        if (up == "SORT") {
            if (saw_sort) {
                error = "IDX: duplicate SORT option.";
                return false;
            }

            std::string algoTok;
            if (!(in >> algoTok)) {
                error = "IDX: SORT requires an algorithm name.";
                return false;
            }

            dottalk::edu_idx::SortAlgo algo{};
            if (!dottalk::edu_idx::parse_sort_algo(algoTok, algo)) {
                error = "IDX: unknown SORT algorithm '" + algoTok + "'. Supported: STD, BUBBLE.";
                return false;
            }

            request.sort_algo = algo;
            saw_sort = true;
            continue;
        }

        dottalk::edu_idx::SortDirection dir{};
        if (dottalk::edu_idx::parse_direction(tok, dir)) {
            if (saw_direction) {
                error = "IDX: duplicate direction option.";
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

        error = "IDX: unexpected token '" + tok + "'.";
        return false;
    }

    return true;
}

void print_build_result(const dottalk::edu_idx::BuildRequest& request,
                        const dottalk::edu_idx::BuildResult& result) {
    const char* verb = result.replaced ? "replaced" : "created";

    std::cout << "Memory index " << verb << ": " << result.tag << "\n";
    std::cout << "  expr       : " << request.field_token << "\n";
    std::cout << "  sort       : " << dottalk::edu_idx::to_string(request.sort_algo) << "\n";
    std::cout << "  direction  : " << dottalk::edu_idx::to_string(request.direction) << "\n";
    std::cout << "  records    : " << result.build.records_indexed
              << " indexed / " << result.build.records_scanned << " scanned\n";
    std::cout << "  deleted    : " << result.build.deleted_skipped << " skipped\n";
    std::cout << "  build      : " << elapsed_text(result.build.elapsed_us) << "\n";
    std::cout << "  sort       : " << elapsed_text(result.build.sort.elapsed_us) << "\n";
    std::cout << "  compares   : " << result.build.sort.comparisons << "\n";
    std::cout << "  swaps      : " << result.build.sort.swaps << "\n";
}

void print_list() {
    const auto rows = dottalk::edu_idx::list_indexes();
    if (rows.empty()) {
        std::cout << "IDX: no memory indexes.\n";
        return;
    }

    std::cout << "IDX memory indexes:\n\n";
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
        std::cout << "Usage: IDX DROP <tag>|ALL\n";
        return;
    }

    if (upper_copy(tag) == "ALL") {
        const auto before = dottalk::edu_idx::list_indexes().size();
        dottalk::edu_idx::drop_all_indexes();
        if (before == 0) {
            std::cout << "IDX: no memory indexes to drop.\n";
        } else {
            std::cout << "IDX: dropped all memory indexes.\n";
        }
        return;
    }

    if (dottalk::edu_idx::drop_index(tag)) {
        std::cout << "IDX: dropped memory index " << tag << ".\n";
    } else {
        std::cout << "IDX: memory index not found: " << tag << "\n";
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
            std::cout << error << "\n";
            std::cout << "Usage: IDX ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]\n";
            return;
        }

        auto result = dottalk::edu_idx::build_and_store(A, request);
        if (!result.ok) {
            std::cout << result.message << "\n";
            return;
        }

        print_build_result(request, result);
        return;
    }

    std::cout << "IDX: unknown command '" << first << "'.\n";
    print_help();
}

// Shell registry entrypoint.
// The shell registers command name IDX to edu_IDX. Keep cmd_IDX as the
// implementation name for older call sites, and export edu_IDX for the
// current education-command registry contract.
void edu_IDX(DbArea& A, std::istringstream& in) {
    cmd_IDX(A, in);
}

