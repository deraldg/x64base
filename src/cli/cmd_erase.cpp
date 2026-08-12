// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_erase.cpp
// ERASE -- physically deletes a table file and its same-stem sidecars.
//
// Supported syntax:
//   ERASE <table> [CONFIRM]
//   ERASE TABLE <table> [CONFIRM]
//   ERASE DIR <path> [CONFIRM]
//
// Examples:
//   ERASE TABLE clients CONFIRM
//   ERASE students.dbf CONFIRM
//   ERASE DIR DBF\wbregress CONFIRM
//
// Behavior:
//   - Resolves <table> to a .dbf path (adds .dbf if missing).
//   - Resolves relative table names through the active SETPATH DBF slot.
//   - Deletes the DBF plus known DBF-sidecars in the same directory:
//       .fpt .dbt .dtx .dti.json .schema.json
//   - Also deletes matching public index files through the active INDEXES slot:
//       .inx .cnx .cdx .idx
//   - Also deletes the matching LMDB backend directory for the public .cdx
//     through the active LMDB slot:
//       <stem>.cdx.d
//   - Safety gate: without CONFIRM, it prints what it *would* delete and does nothing.
//   - ERASE DIR (owner-ruled 2026-08-12): explicit directory teardown. A landed
//     writeback target has no table token -- the .dbf normalization would mangle
//     it -- and the WORKSPACE WRITEBACK regression needs clean-slate reruns
//     (a leftover target makes the writeback refuse on collision while the
//     markers read the PREVIOUS run's files: a stale false green). No .dbf
//     normalization, no sidecar sweep, no SETPATH resolution: the named
//     directory (cwd-relative or absolute) and its contents, nothing else.
//     Same CONFIRM contract: dry-run without it.

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
//   Physically delete a DBF table file plus known same-stem sidecars across DBF, INDEXES, and LMDB roots.
//
// usage:
//   ERASE USAGE
//   ERASE <table> [CONFIRM]
//   ERASE TABLE <table> [CONFIRM]
//   ERASE DIR <path> [CONFIRM]
//
// examples:
//   ERASE TABLE clients
//   ERASE TABLE clients CONFIRM
//   ERASE students.dbf CONFIRM
//   ERASE DIR DBF\wbregress CONFIRM
//
// notes:
//   ERASE USAGE prints usage and does not inspect or delete files.
//   Without CONFIRM, ERASE performs a dry-run and lists files that would be deleted.
//   CONFIRM physically deletes the DBF, matching index containers/files, and matching LMDB backend directory when present.
//   ERASE DIR deletes the named directory and everything under it; cwd-relative or absolute path, no SETPATH resolution, no sidecar sweep. Dry-run without CONFIRM.
//
// risk:
//   deletes_filesystem: ERASE ... CONFIRM
//   deletes_directory_recursive: ERASE DIR ... CONFIRM
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
#include <sstream>
#include <string>
#include <vector>

#include "cli/command_output.hpp"
#include "cli/command_registry.hpp"
#include "cli/path_resolver.hpp"
#include "common/path_state.hpp"
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

static bool istarts_with(const std::string& s, const std::string& prefix) {
    if (prefix.size() > s.size()) return false;
    for (size_t i = 0; i < prefix.size(); ++i) {
        if (std::toupper(static_cast<unsigned char>(s[i])) !=
            std::toupper(static_cast<unsigned char>(prefix[i]))) return false;
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
    // Same logical table stem across DBF, INDEXES, and LMDB roots.
    const fs::path dir = dbf_path.parent_path();
    const std::string stem = dbf_path.stem().string(); // "clients" from "clients.dbf"

    std::vector<fs::path> files;
    files.reserve(16);

    // Primary
    files.push_back(dbf_path);

    // Traditional DBF sidecars (optional, same DBF directory)
    files.push_back(dir / (stem + ".fpt"));
    files.push_back(dir / (stem + ".dbt"));
    files.push_back(dir / (stem + ".dtx"));         // memo sidecar
    files.push_back(dir / (stem + ".dti.json"));    // indexing stub sidecar
    files.push_back(dir / (stem + ".schema.json")); // schema sidecar

    // Public index containers/files (optional, active INDEXES root)
    const fs::path inx = dottalk::paths::resolve_index(stem + ".inx");
    const fs::path cnx = dottalk::paths::resolve_index(stem + ".cnx");
    const fs::path cdx = dottalk::paths::resolve_index(stem + ".cdx");
    const fs::path idx = dottalk::paths::resolve_index(stem + ".idx");
    files.push_back(inx);
    files.push_back(cnx);
    files.push_back(cdx);
    files.push_back(idx);

    // LMDB backend env for the public CDX container (optional, active LMDB root)
    files.push_back(dottalk::paths::resolve_lmdb_env_for_cdx(cdx));

    // Single-index families often include tag suffixes, for example:
    //   students_lname.inx
    //   students_gpa.idx
    // When ERASE targets the table, treat these as belonging to the same
    // table and remove them too from the active INDEXES root.
    const fs::path index_dir = cdx.parent_path();
    std::error_code walk_ec;
    if (!index_dir.empty() && fs::exists(index_dir, walk_ec) && !walk_ec) {
        for (const auto& entry : fs::directory_iterator(index_dir, walk_ec)) {
            if (walk_ec) break;
            if (!entry.is_regular_file()) continue;
            const fs::path candidate = entry.path();
            const std::string ext = candidate.extension().string();
            if (!ieq(ext, ".inx") && !ieq(ext, ".idx")) continue;
            const std::string candidate_stem = candidate.stem().string();
            if (istarts_with(candidate_stem, stem)) {
                files.push_back(candidate);
            }
        }
    }

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
    cli::cmdout::print_message(dottalk::helpdata::MessageId::EraseUsageText);
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

    // ERASE DIR <path> [CONFIRM] -- explicit directory teardown (owner-ruled
    // 2026-08-12; charter in the file header). Handled before the table path
    // so a directory token never reaches the .dbf normalization below.
    if (textio::up(tok) == "DIR") {
        std::string dir_arg;
        if (!(iss >> dir_arg) || dir_arg.empty()) { print_usage(); return; }

        // Cross-OS: scripts spell paths either way; POSIX does not treat
        // '\' as a separator (house pattern, see shell.cpp).
        std::replace(dir_arg.begin(), dir_arg.end(), '\\', '/');

        bool dir_confirm = false;
        std::string t2;
        while (iss >> t2) {
            if (textio::up(t2) == "CONFIRM" || t2 == "/Y" || t2 == "-Y") {
                dir_confirm = true;
            }
        }

        std::error_code ec;
        // Same resolution as every other path token in the engine, and the
        // same one WORKSPACE WRITEBACK's TO target uses: absolute stays
        // absolute, separators mean DATA-root-relative, a bare name sits in
        // the DBF slot. A teardown that resolved differently from the write
        // it is tearing down would delete the wrong directory or miss the
        // right one -- which is exactly what happened while this took the
        // raw token and followed the process CWD (measured 2026-08-12).
        const fs::path dir = dottalk::paths::resolve_in_slot(
            dottalk::paths::get_slot(dottalk::paths::Slot::DBF), dir_arg);
        if (!fs::exists(dir, ec) || ec) {
            // Absence is the desired end state of a teardown, not an error --
            // a bootstrap pre-clean on a fresh tree lands here by design.
            cli::cmdout::print_line("ERASE DIR: '" + dir_arg +
                                    "' does not exist -- nothing to delete.");
            return;
        }
        ec.clear();
        if (!fs::is_directory(dir, ec) || ec) {
            cli::cmdout::print_line("ERASE DIR: '" + dir_arg +
                                    "' is not a directory -- use ERASE <table|file> for files.");
            return;
        }

        if (!dir_confirm) {
            ec.clear();
            std::size_t entries = 0;
            for (auto it = fs::recursive_directory_iterator(dir, ec);
                 !ec && it != fs::recursive_directory_iterator(); it.increment(ec)) {
                ++entries;
            }
            cli::cmdout::print_line("ERASE DIR (dry-run): would remove '" + dir_arg +
                                    "' and " + std::to_string(entries) +
                                    " entrie(s) under it. Re-run with CONFIRM.");
            return;
        }

        ec.clear();
        const std::uintmax_t removed = fs::remove_all(dir, ec);
        if (ec) {
            cli::cmdout::print_line("ERASE DIR: failed on '" + dir_arg + "': " +
                                    ec.message());
        } else {
            cli::cmdout::print_line("ERASE DIR: removed '" + dir_arg + "' (" +
                                    std::to_string(removed) + " entrie(s)).");
        }
        return;
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
        cli::cmdout::print_prefixed_message(
            "ERASE", dottalk::helpdata::MessageId::EraseTableNotFoundText,
            {{"table", s8(wanted)}});
        return;
    }

    auto files = build_sidecar_list(dbf_path);

    // Filter to ones that actually exist
    std::error_code ec;
    std::vector<fs::path> existing;
    existing.reserve(files.size());
    for (const auto& f : files) {
        ec.clear();
        if (fs::exists(f, ec) && !ec) existing.push_back(f);
    }

    if (existing.empty()) {
        cli::cmdout::print_prefixed_message(
            "ERASE", dottalk::helpdata::MessageId::EraseNothingToDeleteText,
            {{"path", s8(dbf_path)}});
        return;
    }

    // Dry-run unless confirmed
    if (!confirm) {
        cli::cmdout::print_prefixed_message(
            "ERASE (dry-run)", dottalk::helpdata::MessageId::EraseDryRunHeaderText,
            {{"count", std::to_string(existing.size())},
             {"table", s8(dbf_path.stem())}});
        for (const auto& f : existing) cli::cmdout::print_line("  " + s8(f.filename()));
        cli::cmdout::print_message(dottalk::helpdata::MessageId::EraseReRunConfirmText);
        return;
    }

    int deleted = 0;
    int failed  = 0;

    cli::cmdout::print_prefixed_message(
        "ERASE", dottalk::helpdata::MessageId::EraseDeletingHeaderText,
        {{"count", std::to_string(existing.size())},
         {"table", s8(dbf_path.stem())}});

    for (const auto& f : existing) {
        ec.clear();
        std::uintmax_t removed = 0;
        if (fs::is_directory(f, ec)) {
            ec.clear();
            removed = fs::remove_all(f, ec);
        } else {
            fs::remove(f, ec);
            removed = ec ? 0u : 1u;
        }
        if (ec) {
            ++failed;
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::EraseFailedLineText,
                {{"file", s8(f.filename())}, {"error", ec.message()}});
        } else {
            ++deleted;
            if (removed > 1) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::EraseDeletedEntriesLineText,
                    {{"file", s8(f.filename())}, {"entries", std::to_string(removed)}});
            } else {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::EraseDeletedLineText,
                    {{"file", s8(f.filename())}});
            }
        }
    }

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::EraseCompleteText,
        {{"deleted", std::to_string(deleted)}, {"failed", std::to_string(failed)}});
}

static bool s_registered = []() {
    dli::registry().add("ERASE", &cmd_ERASE);
    return true;
}();
