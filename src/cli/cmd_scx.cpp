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
#include "cli/command_output.hpp"
#include "xindex/local_index_stub.hpp"

static void print_scx_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ScxUsageText);
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
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ScxCreateUsageText);
            return;
        }
        if (!xindex::write_scx_create(file, &err)) {
            cli::cmdout::print_prefixed_message("SCX CREATE", dottalk::helpdata::MessageId::ScxDetailText, {{"detail", err}});
            return;
        }
        cli::cmdout::print_prefixed_message("SCX CREATE", dottalk::helpdata::MessageId::ScxCreateWroteText, {{"file", file}});
        return;
    }

    if (U == "ADDTAG") {
        std::string file, name, tok;
        unsigned field = 0;
        bool desc = false;
        if (!(in >> file >> name >> tok) || xindex::upper_ascii_copy(tok) != "FIELD" || !(in >> field)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ScxAddtagUsageText);
            return;
        }
        if ((in >> tok)) desc = (xindex::upper_ascii_copy(tok) == "DESC");
        if (!xindex::scx_add_tag(file, xindex::upper_ascii_copy(name), field, desc, &err)) {
            cli::cmdout::print_prefixed_message("SCX ADDTAG", dottalk::helpdata::MessageId::ScxDetailText, {{"detail", err}});
            return;
        }
        cli::cmdout::print_prefixed_message("SCX ADDTAG", dottalk::helpdata::MessageId::ScxAddtagAddedText, {{"name", xindex::upper_ascii_copy(name)}});
        return;
    }

    if (U == "BUILD") {
        std::string file;
        if (!(in >> file)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ScxBuildUsageText);
            return;
        }
        if (!xindex::scx_build_from_area(file, area, &err)) {
            cli::cmdout::print_prefixed_message("SCX BUILD", dottalk::helpdata::MessageId::ScxDetailText, {{"detail", err}});
            return;
        }
        cli::cmdout::print_prefixed_message("SCX BUILD", dottalk::helpdata::MessageId::ScxBuildDoneText, {{"file", file}});
        return;
    }

    if (U == "TAGS") {
        std::string file;
        if (!(in >> file)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ScxTagsUsageText);
            return;
        }
        if (!xindex::scx_tags(file, std::cout, &err)) {
            cli::cmdout::print_prefixed_message("SCX TAGS", dottalk::helpdata::MessageId::ScxDetailText, {{"detail", err}});
        }
        return;
    }

    if (U == "INFO") {
        std::string file;
        if (!(in >> file)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ScxInfoUsageText);
            return;
        }
        if (!xindex::scx_info(file, std::cout, &err)) {
            cli::cmdout::print_prefixed_message("SCX INFO", dottalk::helpdata::MessageId::ScxDetailText, {{"detail", err}});
        }
        return;
    }

    cli::cmdout::print_prefixed_message("SCX", dottalk::helpdata::MessageId::ScxUnknownSubText, {{"sub", sub}});
}
