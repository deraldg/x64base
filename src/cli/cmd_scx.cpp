#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "xindex/local_index_stub.hpp"

void cmd_SCX(xbase::DbArea& area, std::istringstream& in)
{
    std::string sub;
    if (!(in >> sub)) {
        std::cout << "SCX CREATE <file>\n";
        std::cout << "SCX ADDTAG <file> <name> FIELD <n> [DESC]\n";
        std::cout << "SCX BUILD <file>\n";
        std::cout << "SCX TAGS <file>\n";
        std::cout << "SCX INFO <file>\n";
        return;
    }

    const std::string U = xindex::upper_ascii_copy(sub);
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
