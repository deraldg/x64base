// @dottalk.usage v1
// owner: EDU|SIX
// command: SIX
// category: education-index
// status: implementation-present
// noargs: usage
// effect: create-build-inspect-index-stub
// mutates: filesystem index-stub
// usage-access: SIX USAGE
// summary:
//   Educational SIX/local-index stub command for create/build/info operations.
//
// usage:
//   SIX USAGE
//   SIX CREATE <file> TAG <name> FIELD <n>
//   SIX BUILD <file>
//   SIX INFO <file>
//
// examples:
//   SIX CREATE students.six TAG LNAME FIELD 2
//   SIX BUILD students.six
//   SIX INFO students.six
//
// notes:
//   SIX USAGE/HELP/? returns before creating, building, or reading index files.
//   This file defines cmd_SIX but does not itself register the command.
//
// risk:
//   writes_filesystem: SIX CREATE/BUILD
//   reads_current_table: SIX BUILD
//   mutates_table_data: no
//

#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "xindex/local_index_stub.hpp"

static void print_six_usage_contract()
{
    std::cout
        << "Usage:\n"
        << "  SIX USAGE\n"
        << "  SIX CREATE <file> TAG <name> FIELD <n>\n"
        << "  SIX BUILD <file>\n"
        << "  SIX INFO <file>\n"
        << "Examples:\n"
        << "  SIX CREATE students.six TAG LNAME FIELD 2\n"
        << "  SIX BUILD students.six\n"
        << "  SIX INFO students.six\n"
        << "Notes:\n"
        << "  - SIX USAGE does not create, build, or inspect index files.\n";
}
void cmd_SIX(xbase::DbArea& area, std::istringstream& in)
{
    std::string sub;
    if (!(in >> sub)) {
        print_six_usage_contract();
        return;
    }

    const std::string U = xindex::upper_ascii_copy(sub);
    // SIX_USAGE_CONTRACT_BRANCH
    if (U == "USAGE" || U == "HELP" || U == "?") {
        print_six_usage_contract();
        return;
    }
    std::string err;

    if (U == "CREATE") {
        std::string file, tok, tag;
        unsigned field = 0;
        if (!(in >> file >> tok) || xindex::upper_ascii_copy(tok) != "TAG" ||
            !(in >> tag >> tok) || xindex::upper_ascii_copy(tok) != "FIELD" ||
            !(in >> field)) {
            std::cout << "Usage: SIX CREATE <file> TAG <name> FIELD <n>\n";
            return;
        }
        if (!xindex::write_six_create(file, xindex::upper_ascii_copy(tag), field, &err)) {
            std::cout << "SIX CREATE: " << err << "\n";
            return;
        }
        std::cout << "SIX CREATE: wrote " << file << "\n";
        return;
    }

    if (U == "BUILD") {
        std::string file;
        if (!(in >> file)) {
            std::cout << "Usage: SIX BUILD <file>\n";
            return;
        }
        if (!xindex::six_build_from_area(file, area, &err)) {
            std::cout << "SIX BUILD: " << err << "\n";
            return;
        }
        std::cout << "SIX BUILD: done " << file << "\n";
        return;
    }

    if (U == "INFO") {
        std::string file;
        if (!(in >> file)) {
            std::cout << "Usage: SIX INFO <file>\n";
            return;
        }
        if (!xindex::six_info(file, std::cout, &err)) {
            std::cout << "SIX INFO: " << err << "\n";
        }
        return;
    }

    std::cout << "SIX: unknown subcommand: " << sub << "\n";
}
