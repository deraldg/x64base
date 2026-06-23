// src/cli/cmd_setcdx.cpp
// SET CDX [<name-or-path>]
// Resolve CDX using SET PATH INDEXES slot via cli/path_resolver.

// @dottalk.usage v1
// owner: DOT|SET CDX
// command: SET CDX
// category: index
// status: supported
// noargs: mutate
// effect: attach
// mutates: order-state
// usage-access: SET CDX USAGE
// summary:
//   Attach a CDX index container to the current area order state, using an explicit
//   name/path or the current table default.
//
// usage:
//   SET CDX USAGE
//   SET CDX
//   SET CDX <name-or-path>
//   SETCDX
//   SETCDX USAGE
//   SETCDX <name-or-path>
//
// notes:
//   SET CDX with no arguments resolves the default <table>.cdx container.
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
//   CDX
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

static fs::path resolve_cdx_token(const std::string& tok)
{
    // Reuse existing INDEX slot resolver.
    // If no extension was provided, default to .cdx.
    fs::path p = dottalk::paths::resolve_index(tok);
    if (!p.has_extension()) p.replace_extension(".cdx");
    return p;
}

static fs::path default_cdx_for(const xbase::DbArea& A)
{
    // Area-aware default: if a DBF is open, use its basename; otherwise fallback.
    std::string stem;

    if (A.isOpen()) {
        fs::path n(A.name());
        stem = n.stem().string();
        if (stem.empty()) stem = "table";
    } else {
        stem = "table";
    }

    return resolve_cdx_token(stem);
}


static bool is_setcdx_usage_request(const std::string& raw)
{
    std::string t = raw;
    for (char& ch : t) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    while (!t.empty() && std::isspace(static_cast<unsigned char>(t.front()))) t.erase(t.begin());
    while (!t.empty() && std::isspace(static_cast<unsigned char>(t.back()))) t.pop_back();
    if (t.rfind("SET CDX ", 0) == 0) {
        t = t.substr(8);
        while (!t.empty() && std::isspace(static_cast<unsigned char>(t.front()))) t.erase(t.begin());
        while (!t.empty() && std::isspace(static_cast<unsigned char>(t.back()))) t.pop_back();
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_setcdx_usage()
{
    std::cout
        << "Usage:\n"
        << "  SET CDX USAGE\n"
        << "  SET CDX\n"
        << "  SET CDX <name-or-path>\n"
        << "  SETCDX\n"
        << "  SETCDX USAGE\n"
        << "  SETCDX <name-or-path>\n";
}

void cmd_SETCDX(xbase::DbArea& A, std::istringstream& in)
{
    const std::string raw_args = in.str();

    std::string arg;
    fs::path p;

    if (in >> arg) {
        if (is_setcdx_usage_request(arg) || is_setcdx_usage_request(raw_args)) {
            print_setcdx_usage();
            return;
        }
        p = resolve_cdx_token(arg);
    } else {
        p = default_cdx_for(A);
    }

    if (!fs::exists(p)) {
        std::cout << "SET CDX: file not found: " << p.string() << "\n";
        return;
    }

    try {
        // CDX attachment/state is owned by order subsystem in your architecture.
        orderstate::setOrder(A, p.string());
        std::cout << "SET CDX: attached \"" << p.string() << "\"\n";
    }
    catch (const std::exception& ex) {
        std::cout << "SET CDX failed: " << ex.what() << "\n";
    }
}