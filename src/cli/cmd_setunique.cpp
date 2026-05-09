// SET UNIQUE FIELD <name> ON|OFF
// Lists current unique fields if called without args.

// @dottalk.usage v1
// owner: DOT|SET_UNIQUE
// command: SET_UNIQUE
// category: constraints
// status: supported
// noargs: report
// effect: configure
// mutates: unique-field-registry
// usage-access: SET UNIQUE USAGE
// summary:
//   Report or configure per-table unique-field registry entries.
//
// usage:
//   SET_UNIQUE
//   SET_UNIQUE USAGE
//   SET_UNIQUE FIELD <name> ON
//   SET_UNIQUE FIELD <name> OFF
//   SET UNIQUE
//   SET UNIQUE USAGE
//   SET UNIQUE FIELD <name> ON
//   SET UNIQUE FIELD <name> OFF
//
// notes:
//   SET UNIQUE with no arguments lists current unique fields.
//   FIELD <name> ON marks a field as unique in the registry.
//   FIELD <name> OFF clears the unique marker.
//   This mutates uniqueness metadata only; it does not rewrite table records.
//
// risk:
//   mutates_unique_registry: yes
//   mutates_table_data: no
//
// related:
//   SET
//   FIELDMGR
//   CREATE
//

#include <sstream>
#include <string>
#include <iostream>
#include <algorithm>

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/unique_registry.hpp"

using namespace textio;

static inline std::string upcopy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}


static void print_setunique_usage()
{
    std::cout
        << "Usage:\n"
        << "  SET UNIQUE\n"
        << "  SET UNIQUE USAGE\n"
        << "  SET UNIQUE FIELD <name> ON\n"
        << "  SET UNIQUE FIELD <name> OFF\n";
}

void cmd_SET_UNIQUE(xbase::DbArea& A, std::istringstream& in) {
    const std::string raw_args = in.str();

    std::string tok1;
    if (!(in >> tok1)) {
        auto fields = unique_reg::list_unique_fields(A);
        if (fields.empty()) { std::cout << "UNIQUE: (none)\n"; return; }
        std::cout << "UNIQUE fields: ";
        for (size_t i=0;i<fields.size();++i) {
            if (i) std::cout << ", ";
            std::cout << fields[i];
        }
        std::cout << "\n";
        return;
    }

    const std::string U1 = upcopy(tok1);
    if (U1 == "USAGE" || U1 == "HELP" || U1 == "?") {
        print_setunique_usage();
        return;
    }
    if (U1 != "FIELD") {
        print_setunique_usage();
        return;
    }

    std::string fname, onoff;
    if (!(in >> fname >> onoff)) {
        print_setunique_usage();
        return;
    }

    const std::string Uon = upcopy(onoff);
    if (Uon != "ON" && Uon != "OFF") {
        print_setunique_usage();
        return;
    }

    unique_reg::set_unique_field(A, fname, Uon == "ON");
    std::cout << "UNIQUE " << (Uon == "ON" ? "ON" : "OFF")
              << " for FIELD " << upcopy(fname) << ".\n";
}



