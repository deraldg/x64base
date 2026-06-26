// SET UNIQUE FIELD <name> ON|OFF
// Lists current unique fields if called without args.

// @dottalk.usage v1
// owner: DOT|SET UNIQUE
// command: SET UNIQUE
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
#include <algorithm>

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/command_output.hpp"
#include "cli/unique_registry.hpp"
#include "help/helpdata_messages.hpp"

using namespace textio;

static inline std::string upcopy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}


static void print_setunique_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::SetUniqueUsageText);
}

void cmd_SET_UNIQUE(xbase::DbArea& A, std::istringstream& in) {
    std::string tok1;
    if (!(in >> tok1)) {
        auto fields = unique_reg::list_unique_fields(A);
        if (fields.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetUniqueNoneText);
            return;
        }

        std::string joined;
        for (size_t i = 0; i < fields.size(); ++i) {
            if (i) joined += ", ";
            joined += fields[i];
        }
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetUniqueFieldsText,
            {{"fields", joined}});
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
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SetUniqueFieldStatusText,
        {
            {"state", Uon == "ON" ? "ON" : "OFF"},
            {"field", upcopy(fname)}
        });
}


