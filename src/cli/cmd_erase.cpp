// src/cli/cmd_erase.cpp
// ERASE — physically deletes a table file and its same-stem sidecars.
//
// Supported syntax:
//   ERASE <table> [CONFIRM]
//   ERASE TABLE <table> [CONFIRM]
//
// Examples:
//   ERASE TABLE clients CONFIRM
//   ERASE students.dbf CONFIRM
//
// Behavior:
//   - Resolves <table> to a .dbf path (adds .dbf if missing).
//   - Resolves relative table names through the active SETPATH DBF slot.
//   - Deletes the DBF plus known sidecars with the same stem in the same directory:
//       .fpt .dbt .inx .cnx .cdx .idx .dtx .dti.json .schema.json
//   - Safety gate: without CONFIRM, it prints what it *would* delete and does nothing.

// @dottalk.usage v1
// owner: DOT|ERASE
// command: ERASE
// category: destructive-file
// status: supported
// noargs: usage
// effect: delete-table-files
// mutates: filesystem
// usage-access: ERASE USAGE
// summary:
//   Physically delete a DBF table file and known same-stem sidecar files.
//
// usage:
//   ERASE USAGE
//   ERASE <table> [CONFIRM]
//   ERASE TABLE <table> [CONFIRM]
//
// examples:
//   ERASE TABLE clients
//   ERASE TABLE clients CONFIRM
//   ERASE students.dbf CONFIRM
//
// notes:
//   ERASE USAGE prints usage and does not inspect or delete files.
//   Without CONFIRM, ERASE performs a dry-run and lists files that would be deleted.
//   CONFIRM physically deletes the DBF and known same-stem sidecars.
//
// risk:
//   deletes_filesystem: ERASE ... CONFIRM
//   dry_run_without_confirm: yes
//   mutates_table_data: filesystem-level delete
//
// related:
//   ZAP
//   PACK
//   COPY
//

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "cli/command_registry.hpp"
#include "cli/path_resolver.hpp"
#include "textio.hpp"
#include "xbase.hpp"

namespace fs = std::filesystem;

static inline std::string s8(const fs::path& p) {
#if defined(_WIN32)
    auto u = p.u8string();
    return std::string(u.begin(), u.end());
#else
    return p.string();
#endif
}

static bool ieq(const std::string& a, const std::string& b) {
    if (a.size() != b.size()) return false;
    for (size_t i = 0; i < a.size(); ++i) {
        if (std::toupper(static_cast<unsigned char>(a[i])) !=
            std::toupper(static_cast<unsigned char>(b[i]))) return false;
    }
    return true;
}

static bool has_ext_ci(const std::string& s, const std::string& ext_with_dot) {
    if (s.size() < ext_with_dot.size()) return false;
    const size_t off = s.size() - ext_with_dot.size();
    return ieq(s.substr(off), ext_with_dot);
}

static fs::path normalize_to_dbf_token(std::string table_arg) {
    // If user passed "clients" -> "clients.dbf".
    // If they passed "clients.dbf" -> keep.
    // If they passed another extension -> keep as-is; ERASE still expects
    // the resolved primary file to exist.
    if (!has_ext_ci(table_arg, ".dbf")) {
        fs::path p(table_arg);
        const auto fn = p.filename().string();
        if (fn.find('.') == std::string::npos) {
            table_arg += ".dbf";
        }
    }
    return fs::path(table_arg);
}

static bool try_resolve_existing(const fs::path& in, fs::path& out) {
    // ERASE must follow the same active-path contract as USE/CREATE/PACK/ZAP:
    // a bare table name is resolved through the current SETPATH DBF slot.
    // Earlier code used cwd-relative guesses such as ./dbf and ./data/dbf;
    // after the SETPATH cleanup those guesses miss active paths like
    // dottalkpp/data/DBF/SANDBOX even though USE can open the table.
    std::error_code ec;

    if (in.is_absolute()) {
        if (fs::exists(in, ec)) { out = in; return true; }
        return false;
    }

    const std::string token = in.string();

    // Primary modern resolver: active Slot::DBF, with DATA-relative behavior
    // for tokens containing path separators (e.g. DBF/SANDBOX/foo.dbf).
    fs::path resolved = dottalk::paths::resolve_dbf(token);
    if (fs::exists(resolved, ec)) { out = resolved; return true; }

    // Compatibility fallback: if the caller already supplied a relative path
    // that exists from the process cwd, still allow it.
    if (fs::exists(in, ec)) { out = in; return true; }

    return false;
}

static std::vector<fs::path> build_sidecar_list(const fs::path& dbf_path) {
    // Same directory, same stem
    const fs::path dir  = dbf_path.parent_path();
    const std::string stem = dbf_path.stem().string(); // "clients" from "clients.dbf"

    std::vector<fs::path> files;
    files.reserve(12);

    // Primary
    files.push_back(dbf_path);

    // Traditional DBF sidecars (optional)
    files.push_back(dir / (stem + ".fpt"));
    files.push_back(dir / (stem + ".dbt"));

    // Index containers / common index files (optional)
    files.push_back(dir / (stem + ".inx"));
    files.push_back(dir / (stem + ".cnx"));
    files.push_back(dir / (stem + ".cdx"));
    files.push_back(dir / (stem + ".idx"));

    // DotTalk++ sidecars (optional)
    files.push_back(dir / (stem + ".dtx"));         // memo sidecar
    files.push_back(dir / (stem + ".dti.json"));    // indexing stub sidecar
    files.push_back(dir / (stem + ".schema.json")); // schema sidecar

    // Dedup
    std::sort(files.begin(), files.end(), [](const fs::path& a, const fs::path& b){
        return s8(a) < s8(b);
    });
    files.erase(std::unique(files.begin(), files.end(), [](const fs::path& a, const fs::path& b){
        return ieq(s8(a), s8(b));
    }), files.end());

    return files;
}

static void print_usage() {
    std::cout
        << "Usage:\n"
        << "  ERASE USAGE\n"
        << "  ERASE <table> [CONFIRM]\n"
        << "  ERASE TABLE <table> [CONFIRM]\n"
        << "Examples:\n"
        << "  ERASE TABLE clients\n"
        << "  ERASE TABLE clients CONFIRM\n"
        << "  ERASE students.dbf CONFIRM\n"
        << "Notes:\n"
        << "  - ERASE USAGE does not inspect or delete files.\n"
        << "  - Physically deletes <table>.dbf and known same-stem sidecars.\n"
        << "  - Without CONFIRM, performs a dry-run and prints what would be deleted.\n"
        << "  - CONFIRM performs deletion.\n";
}

void cmd_ERASE(xbase::DbArea& /*area*/, std::istringstream& iss) {
    std::string tok;
    if (!(iss >> tok)) { print_usage(); return; }
    // ERASE_USAGE_CONTRACT_BRANCH
    {
        const std::string u = textio::up(tok);
        if (u == "USAGE" || u == "HELP" || u == "?") {
            print_usage();
            return;
        }
    }

    std::string table_arg;
    bool confirm = false;

    // Accept optional "TABLE"
    if (textio::up(tok) == "TABLE") {
        if (!(iss >> table_arg) || table_arg.empty()) { print_usage(); return; }
    } else {
        table_arg = tok;
    }

    // Optional trailing CONFIRM
    std::string tail;
    while (iss >> tail) {
        if (textio::up(tail) == "CONFIRM" || tail == "/Y" || tail == "-Y") {
            confirm = true;
        }
        // ignore other tokens for now
    }

    fs::path wanted = normalize_to_dbf_token(table_arg);

    fs::path dbf_path;
    if (!try_resolve_existing(wanted, dbf_path)) {
        std::cout << "ERASE: Table not found: " << s8(wanted) << "\n";
        return;
    }

    auto files = build_sidecar_list(dbf_path);

    // Filter to ones that actually exist
    std::error_code ec;
    std::vector<fs::path> existing;
    existing.reserve(files.size());
    for (const auto& f : files) {
        if (fs::exists(f, ec)) existing.push_back(f);
    }

    if (existing.empty()) {
        std::cout << "ERASE: Nothing to delete for: " << s8(dbf_path) << "\n";
        return;
    }

    // Dry-run unless confirmed
    if (!confirm) {
        std::cout << "ERASE (dry-run): would delete " << existing.size()
                  << " file(s) for table: " << s8(dbf_path.stem()) << "\n";
        for (const auto& f : existing) std::cout << "  " << s8(f.filename()) << "\n";
        std::cout << "Re-run with CONFIRM to perform deletion.\n";
        return;
    }

    int deleted = 0;
    int failed  = 0;

    std::cout << "ERASE: deleting " << existing.size()
              << " file(s) for table: " << s8(dbf_path.stem()) << "\n";

    for (const auto& f : existing) {
        ec.clear();
        fs::remove(f, ec);
        if (ec) {
            ++failed;
            std::cout << "  FAILED: " << s8(f.filename()) << "  (" << ec.message() << ")\n";
        } else {
            ++deleted;
            std::cout << "  Deleted: " << s8(f.filename()) << "\n";
        }
    }

    std::cout << "ERASE complete. Deleted: " << deleted << ", Failed: " << failed << "\n";
}

static bool s_registered = []() {
    dli::registry().add("ERASE", &cmd_ERASE);
    return true;
}();
