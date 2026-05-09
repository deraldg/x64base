// @dottalk.usage v1
// owner: DOT|SCX
// command: SCX
// category: index
// status: supported
// noargs: usage
// effect: mixed
// mutates: scx-index-file
// usage-access: SCX USAGE
// summary:
//   Student/local SCX index-file lab command for creating, tagging, building,
//   listing, and inspecting SCX index files.
//
// usage:
//   SCX USAGE
//   SCX CREATE <file>
//   SCX ADDTAG <file> <name> FIELD <n>
//   SCX ADDTAG <file> <name> FIELD <n> DESC
//   SCX BUILD <file>
//   SCX TAGS <file>
//   SCX INFO <file>
//
// notes:
//   SCX with no arguments prints usage.
//   CREATE writes a new SCX container/file.
//   ADDTAG mutates SCX tag metadata.
//   BUILD builds SCX contents from the current area.
//   TAGS and INFO inspect SCX metadata.
//   SCX is separate from the ordinary command-surface CNX/CDX/LMDB abstractions.
//
// risk:
//   writes_index_file: CREATE ADDTAG BUILD
//   reads_current_area: BUILD
//   mutates_table_data: no
//
// related:
//   IDX
//   INDEX
//   REINDEX
//

#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "xindex/local_index_stub.hpp"

static void print_scx_usage()
{
    std::cout
        << "Usage:\n"
        << "  SCX USAGE\n"
        << "  SCX CREATE <file>\n"
        << "  SCX ADDTAG <file> <name> FIELD <n> [DESC]\n"
        << "  SCX BUILD <file>\n"
        << "  SCX TAGS <file>\n"
        << "  SCX INFO <file>\n";
}

void cmd_SCX(xbase::DbArea& area, std::istringstream& in)
{
    std::string sub;
    if (!(in >> sub)) {
        print_scx_usage();
        return;
    }

    const std::string U = xindex::upper_ascii_copy(sub);

    if (U == "USAGE" || U == "HELP" || U == "?") {
        print_scx_usage();
        return;
    }
    std::string err;

    if (U == "CREATE") {
        std::string file;
        if (!(in >> file)) {
            std::cout << "Usage: SCX CREATE <file>\n";
            return;
        }
        if (!xindex::write_scx_create(file, &err)) {
            std::cout << "SCX CREATE: " << err << "\n";
            return;
        }
        std::cout << "SCX CREATE: wrote " << file << "\n";
        return;
    }

    if (U == "ADDTAG") {
        std::string file, name, tok;
        unsigned field = 0;
        bool desc = false;
        if (!(in >> file >> name >> tok) || xindex::upper_ascii_copy(tok) != "FIELD" || !(in >> field)) {
            std::cout << "Usage: SCX ADDTAG <file> <name> FIELD <n> [DESC]\n";
            return;
        }
        if ((in >> tok)) desc = (xindex::upper_ascii_copy(tok) == "DESC");
        if (!xindex::scx_add_tag(file, xindex::upper_ascii_copy(name), field, desc, &err)) {
            std::cout << "SCX ADDTAG: " << err << "\n";
            return;
        }
        std::cout << "SCX ADDTAG: added '" << xindex::upper_ascii_copy(name) << "'\n";
        return;
    }

    if (U == "BUILD") {
        std::string file;
        if (!(in >> file)) {
            std::cout << "Usage: SCX BUILD <file>\n";
            return;
        }
        if (!xindex::scx_build_from_area(file, area, &err)) {
            std::cout << "SCX BUILD: " << err << "\n";
            return;
        }
        std::cout << "SCX BUILD: done " << file << "\n";
        return;
    }

    if (U == "TAGS") {
        std::string file;
        if (!(in >> file)) {
            std::cout << "Usage: SCX TAGS <file>\n";
            return;
        }
        if (!xindex::scx_tags(file, std::cout, &err)) {
            std::cout << "SCX TAGS: " << err << "\n";
        }
        return;
    }

    if (U == "INFO") {
        std::string file;
        if (!(in >> file)) {
            std::cout << "Usage: SCX INFO <file>\n";
            return;
        }
        if (!xindex::scx_info(file, std::cout, &err)) {
            std::cout << "SCX INFO: " << err << "\n";
        }
        return;
    }

    std::cout << "SCX: unknown subcommand: " << sub << "\n";
}
