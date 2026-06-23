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

// @dottalk.usage v1
// owner: DOT|SCHEMAS
// command: SCHEMAS
// category: compatibility
// status: deprecated-compat
// noargs: route
// effect: workspace
// mutates: workspace-through-routed-command
// usage-access: SCHEMAS USAGE
// summary:
//   Deprecated compatibility shim that routes old SCHEMAS commands to WORKSPACE.
//
// usage:
//   SCHEMAS
//   SCHEMAS USAGE
//   SCHEMAS OPEN <arg>
//   SCHEMAS CLOSE
//
// notes:
//   SCHEMAS with no arguments still routes to WORKSPACE list behavior.
//   SCHEMAS OPEN <arg> routes to WORKSPACE OPEN <arg>.
//   SCHEMAS CLOSE routes to WORKSPACE CLOSE.
//   SCHEMAS USAGE prints compatibility guidance and does not route to WORKSPACE.
//   WORKSPACE owns live area/session behavior; DDL owns schema/definition work.
//
// risk:
//   mutates_workspace: SCHEMAS OPEN/CLOSE routed forms
//   mutates_table_data: no direct mutation
//
// related:
//   WORKSPACE
//   DDL
//   WSREPORT
//

#include "xbase.hpp"

#include <iostream>
#include <sstream>
#include <string>
#include <cctype>

void cmd_WORKSPACE(xbase::DbArea& current, std::istringstream& in);

static std::string schemas_trim(std::string s)
{
    while (!s.empty() && (s.front() == ' ' || s.front() == '\t' || s.front() == '\r' || s.front() == '\n')) {
        s.erase(s.begin());
    }
    while (!s.empty() && (s.back() == ' ' || s.back() == '\t' || s.back() == '\r' || s.back() == '\n')) {
        s.pop_back();
    }
    return s;
}

static std::string schemas_upper(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static bool schemas_usage_request(const std::string& raw)
{
    const std::string u = schemas_upper(schemas_trim(raw));
    return u == "USAGE" || u == "HELP" || u == "?";
}

static void print_schemas_usage()
{
    std::cout
        << "Usage:\n"
        << "  SCHEMAS\n"
        << "  SCHEMAS USAGE\n"
        << "  SCHEMAS OPEN <arg>\n"
        << "  SCHEMAS CLOSE\n"
        << "Notes:\n"
        << "  - SCHEMAS is deprecated compatibility. Use WORKSPACE instead.\n"
        << "  - SCHEMAS OPEN <arg> routes to WORKSPACE OPEN <arg>.\n"
        << "  - SCHEMAS CLOSE routes to WORKSPACE CLOSE.\n"
        << "  - DDL owns schema/definition work.\n";
}

void cmd_SCHEMAS(xbase::DbArea& current, std::istringstream& in) {
    std::string arg_line;
    std::getline(in, arg_line);

    if (schemas_usage_request(arg_line)) {
        print_schemas_usage();
        return;
    }

    std::cout
        << "SCHEMAS: deprecated compatibility command. Use WORKSPACE instead.\n"
        << "  SCHEMAS             -> WORKSPACE\n"
        << "  SCHEMAS OPEN <arg>  -> WORKSPACE OPEN <arg>\n"
        << "  SCHEMAS CLOSE       -> WORKSPACE CLOSE\n"
        << "  DDL is the schema/definition command; WORKSPACE is the live area/session command.\n";

    std::istringstream routed(arg_line);
    cmd_WORKSPACE(current, routed);
}
