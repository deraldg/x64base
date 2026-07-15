// src/cli/cmd_validate.cpp -- VALIDATE router
// Forwards subcommands like "VALIDATE UNIQUE ..." to their handlers.

// @dottalk.usage v1
// owner: DOT|VALIDATE
// command: VALIDATE
// category: validation
// status: supported
// noargs: usage
// effect: validate
// mutates: delegated-subcommand
// usage-access: VALIDATE USAGE
// summary:
//   Route validation subcommands such as VALIDATE UNIQUE to their handlers.
//
// usage:
//   VALIDATE USAGE
//   VALIDATE UNIQUE USAGE
//   VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]
//
// examples:
//   VALIDATE UNIQUE FIELD SID
//   VALIDATE UNIQUE FIELD EMAIL IGNORE DELETED
//   VALIDATE UNIQUE FIELD SID REPAIR
//   VALIDATE UNIQUE FIELD SID REPORT TO tmp\sid_dupes.txt
//
// notes:
//   VALIDATE with no arguments prints usage.
//   VALIDATE USAGE prints usage and does not scan or repair records.
//   VALIDATE UNIQUE is delegated to the UNIQUE validator.
//   REPAIR may mutate field values; use it intentionally.
//
// risk:
//   scans_records: VALIDATE UNIQUE FIELD
//   writes_files: REPORT TO <path>
//   mutates_table_data: VALIDATE UNIQUE ... REPAIR
//
// related:
//   RULE
//   WHERE
//

#include <sstream>
#include <string>
#include <iostream>
#include <algorithm>

#include "xbase.hpp"
#include <cctype>
#include "cli/command_output.hpp"

void cmd_VALIDATE_UNIQUE(xbase::DbArea&, std::istringstream&);


static void print_validate_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ValidateUsageText);
}

static inline std::string upcopy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(static_cast<unsigned char>(c))); });
    return s;
}

void cmd_VALIDATE(xbase::DbArea& A, std::istringstream& in)
{
    std::streampos pos = in.tellg();
    std::string tok;
    if (!(in >> tok)) {
        print_validate_usage();
        return;
    }
    const std::string U = upcopy(tok);

    if (U == "USAGE" || U == "HELP" || U == "?") {
        print_validate_usage();
        return;
    }

    in.clear();
    in.seekg(pos);

    if (U == "UNIQUE") {
        cmd_VALIDATE_UNIQUE(A, in);
        return;
    }

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ValidateUnknownSubcommandText,
        {{"command", tok}});
    print_validate_usage();
}
