// src/cli/cmd_setcnx.cpp
// SET CNX [<name-or-path>]
// Resolve CNX using SET PATH INDEXES slot via cli/path_resolver.

// @dottalk.usage v1
// owner: DOT|SET CNX
// command: SET CNX
// category: index
// status: supported
// noargs: mutate
// effect: attach
// mutates: order-state
// usage-access: SET CNX USAGE
// summary:
//   Attach a CNX index container to the current area order state, using an explicit
//   name/path or the current table default.
//
// usage:
//   SET CNX USAGE
//   SET CNX
//   SET CNX <name-or-path>
//   SETCNX
//   SETCNX USAGE
//   SETCNX <name-or-path>
//
// notes:
//   SET CNX with no arguments resolves the default <table>.cnx container.
//   Relative names resolve through the INDEXES path slot.
//   The target file must exist.
//   Attachment is owned by the order subsystem.
//   This mutates order/session state but not table records.
//
// risk:
//   mutates_order_state: yes
//   reads_filesystem: yes
//   mutates_table_data: no
//
// related:
//   SET INDEX
//   SET ORDER
//   CNX
//

#include "xbase.hpp"
#include "cli/order_state.hpp"
#include "cli/path_resolver.hpp"

#include <cctype>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>

namespace fs = std::filesystem;

static fs::path resolve_cnx_token(const std::string& tok)
{
    // Reuse existing INDEX slot resolver.
    // If no extension was provided, default to .cnx.
    fs::path p = dottalk::paths::resolve_index(tok);
    if (!p.has_extension()) p.replace_extension(".cnx");
    return p;
}

static fs::path default_cnx_for(const xbase::DbArea& A)
{
    // Area-aware default: if a DBF is open, use its basename; otherwise fallback.
    std::string stem;

    // If your DbArea lacks these accessors, replace with what you actually have.
    // Common choices in your tree: logicalName(), name(), dbfBasename(), etc.
    if (A.isOpen()) {
        // name() in your tree prints the open filename/path-ish identifier.
        // Convert to stem safely.
        fs::path n(A.name());
        stem = n.stem().string();
        if (stem.empty()) stem = "table";
    } else {
        stem = "table";
    }

    return resolve_cnx_token(stem);
}


static bool is_setcnx_usage_request(const std::string& raw)
{
    std::string t = raw;
    for (char& ch : t) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    while (!t.empty() && std::isspace(static_cast<unsigned char>(t.front()))) t.erase(t.begin());
    while (!t.empty() && std::isspace(static_cast<unsigned char>(t.back()))) t.pop_back();
    if (t.rfind("SET CNX ", 0) == 0) {
        t = t.substr(8);
        while (!t.empty() && std::isspace(static_cast<unsigned char>(t.front()))) t.erase(t.begin());
        while (!t.empty() && std::isspace(static_cast<unsigned char>(t.back()))) t.pop_back();
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_setcnx_usage()
{
    std::cout
        << "Usage:\n"
        << "  SET CNX USAGE\n"
        << "  SET CNX\n"
        << "  SET CNX <name-or-path>\n"
        << "  SETCNX\n"
        << "  SETCNX USAGE\n"
        << "  SETCNX <name-or-path>\n";
}

void cmd_SETCNX(xbase::DbArea& A, std::istringstream& in)
{
    const std::string raw_args = in.str();

    std::string arg;
    fs::path p;

    if (in >> arg) {
        if (is_setcnx_usage_request(arg) || is_setcnx_usage_request(raw_args)) {
            print_setcnx_usage();
            return;
        }
        p = resolve_cnx_token(arg);
    } else {
        p = default_cnx_for(A);
    }

    if (!fs::exists(p)) {
        std::cout << "SET CNX: file not found: " << p.string() << "\n";
        return;
    }

    try {
        // CNX attachment/state is owned by order subsystem in your architecture.
        orderstate::setOrder(A, p.string());
        std::cout << "SET CNX: attached \"" << p.string() << "\"\n";
    }
    catch (const std::exception& ex) {
        std::cout << "SET CNX failed: " << ex.what() << "\n";
    }
}
