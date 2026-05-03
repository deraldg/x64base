// src/cli/cmd_schemas.cpp
//
// SCHEMAS is now a legacy compatibility command.
//
// Canonical command ownership:
//   WORKSPACE / WS : live work-area/session open/close/list/save/load
//   DDL            : schema/definition work
//   WSREPORT       : workspace diagnostics/reporting
//
// This file intentionally contains only a shim so old DTS scripts keep
// working while new scripts move to WORKSPACE.

#include "xbase.hpp"

#include <iostream>
#include <sstream>
#include <string>

void cmd_WORKSPACE(xbase::DbArea& current, std::istringstream& in);

void cmd_SCHEMAS(xbase::DbArea& current, std::istringstream& in) {
    std::string arg_line;
    std::getline(in, arg_line);

    std::cout
        << "SCHEMAS: deprecated compatibility command. Use WORKSPACE instead.\n"
        << "  SCHEMAS             -> WORKSPACE\n"
        << "  SCHEMAS OPEN <arg>  -> WORKSPACE OPEN <arg>\n"
        << "  SCHEMAS CLOSE       -> WORKSPACE CLOSE\n"
        << "  DDL is the schema/definition command; WORKSPACE is the live area/session command.\n";

    std::istringstream routed(arg_line);
    cmd_WORKSPACE(current, routed);
}
