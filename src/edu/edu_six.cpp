#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "xindex/local_index_stub.hpp"

void cmd_SIX(xbase::DbArea& area, std::istringstream& in)
{
    std::string sub;
    if (!(in >> sub)) {
        std::cout << "SIX CREATE <file> TAG <name> FIELD <n>\n";
        std::cout << "SIX BUILD <file>\n";
        std::cout << "SIX INFO <file>\n";
        return;
    }

    const std::string U = xindex::upper_ascii_copy(sub);
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
