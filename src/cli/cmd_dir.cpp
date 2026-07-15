// src/cli/cmd_dir.cpp
// @dottalk.usage v1
// owner: DOT|DIR
// command: DIR
// category: filesystem
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: DIR USAGE
// summary:
//   List a directory or show a single file entry through DotTalk++ path
//   resolution.
//
// usage:
//   DIR
//   DIR USAGE
//   DIR <path>
//   DIR <slot>
//   DIR <slot>:<path>
//
// notes:
//   DIR with no arguments lists the configured DBF path.
//   DIR <path> lists a directory or prints a single file entry.
//   Slot-style paths resolve through the common path resolver.
//   DIR is read-only and does not mutate table data or filesystem contents.
//
// risk:
//   reads_filesystem: yes
//   writes_filesystem: no
//   mutates_table_data: no
//
// related:
//   SETPATH
//   SHOWINI
//

#include "xbase.hpp"
#include "textio.hpp"

#include "common/path_resolver.hpp"
#include "common/path_state.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <ctime>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

namespace fs = std::filesystem;

static void print_dir_usage()
{
    std::cout
        << "Usage:\n"
        << "  DIR\n"
        << "  DIR USAGE\n"
        << "  DIR <path>\n"
        << "  DIR <slot>\n"
        << "  DIR <slot>:<path>\n";
}

static bool has_ext_ci(const fs::path& p, const char* ext) {
    auto e = textio::up(p.extension().string());
    return e == textio::up(std::string(ext));
}

static std::time_t to_time_t(fs::file_time_type ft) {
    using namespace std::chrono;
    auto sctp = time_point_cast<system_clock::duration>(
        ft - fs::file_time_type::clock::now() + system_clock::now()
    );
    return system_clock::to_time_t(sctp);
}

static std::tm to_local_tm(std::time_t tt) {
    std::tm tm{};
#ifdef _WIN32
    localtime_s(&tm, &tt);
#else
    localtime_r(&tt, &tm);
#endif
    return tm;
}

static std::string format_commas(std::uint64_t v) {
    std::string s = std::to_string(v);
    std::string out;
    out.reserve(s.size() + s.size() / 3);

    int n = 0;
    for (auto it = s.rbegin(); it != s.rend(); ++it) {
        if (n == 3) {
            out.push_back(',');
            n = 0;
        }
        out.push_back(*it);
        ++n;
    }

    std::reverse(out.begin(), out.end());
    return out;
}

static fs::path normalize_slashes(std::string s) {
    for (char& ch : s) {
        if (ch == '/' || ch == '\\') {
            ch = fs::path::preferred_separator;
        }
    }
    return fs::path(s);
}

static std::string normalize_slot_token(std::string s) {
    s = textio::trim(s);

    for (char& ch : s) {
        if (ch == '-') {
            ch = '_';
        }
    }

    return textio::up(s);
}

static std::string portable_path_key(std::string s) {
    s = textio::trim(std::move(s));
    for (char& ch : s) {
        if (ch == '\\') {
            ch = '/';
        }
    }

    while (!s.empty() && s.front() == '/') {
        s.erase(s.begin());
    }

    if (s.size() >= 2 && s[0] == '.' && s[1] == '/') {
        s.erase(0, 2);
    }

    return textio::up(s);
}

static bool looks_project_data_relative(const std::string& raw_arg) {
    const std::string key = portable_path_key(raw_arg);

    // Project-root relative path.  This is distinct from the historical
    // DATA-relative DIR contract.  Without this guard,
    //     DIR dottalkpp\data\tmp
    // incorrectly becomes:
    //     <DATA>\dottalkpp\data\tmp
    return key == "DOTTALKPP/DATA" ||
           key.rfind("DOTTALKPP/DATA/", 0) == 0;
}

static fs::path resolve_dir_target(const std::string& raw_arg) {
    const std::string arg = textio::trim(raw_arg);

    if (arg.empty()) {
        return dottalk::paths::get_slot(dottalk::paths::Slot::DATA);
    }

    fs::path p = normalize_slashes(arg);

    if (p.is_absolute()) {
        return p;
    }

    // Explicit project-root relative paths should be resolved from the
    // process current directory, not from the DATA slot.  This preserves
    // shell-created files such as:
    //     ! cmd /c "echo x>dottalkpp\data\tmp\file.txt"
    //     DIR dottalkpp\data\tmp\file.txt
    if (looks_project_data_relative(arg)) {
        return fs::absolute(p).lexically_normal();
    }

    // Allow DIR DBF, DIR INDEXES, DIR LMDB, DIR WORKSPACES, etc.
    //
    // Also allow nested slot-style aliases:
    //   DIR DBF/X32       -> DBF_X32
    //   DIR DBF/X64       -> DBF_X64
    //   DIR INDEXES/X32   -> INDEXES_X32
    //   DIR INDEXES/X64   -> INDEXES_X64
    //
    // If the whole token is not a known slot, fall back to DATA-relative.
    std::string slot_key = normalize_slot_token(arg);
    std::replace(slot_key.begin(), slot_key.end(), '/', '_');
    std::replace(slot_key.begin(), slot_key.end(), '\\', '_');

    dottalk::paths::Slot slot{};
    if (dottalk::paths::slot_from_string(slot_key, slot)) {
        return dottalk::paths::get_slot(slot);
    }

    // Historical contract:
    //   DIR DBF/X32 means DATA-relative path if not recognized as a slot.
    return dottalk::paths::resolve_in_slot(
        dottalk::paths::get_slot(dottalk::paths::Slot::DATA),
        p.string()
    );
}

static bool print_regular_file(const fs::path& target) {
    std::error_code ec;

    auto fsz = fs::file_size(target, ec);
    if (ec) {
        std::cout << "Unable to read file size: " << target.string() << "\n";
        return false;
    }

    auto ftime = fs::last_write_time(target, ec);
    if (ec) {
        std::cout << "Unable to read file time: " << target.string() << "\n";
        return false;
    }

    std::tm tm = to_local_tm(to_time_t(ftime));

    std::cout << std::put_time(&tm, "%Y-%m-%d %H:%M")
              << "       " << std::setw(12)
              << format_commas(static_cast<std::uint64_t>(fsz))
              << " " << target.filename().string() << "\n";

    return true;
}

void cmd_DIR(xbase::DbArea&, std::istringstream& iss) {
    std::string arg;
    std::getline(iss, arg);
    arg = textio::trim(arg);

    const std::string argU = textio::up(arg);
    if (argU == "USAGE" || argU == "HELP" || argU == "?") {
        print_dir_usage();
        return;
    }

    fs::path target = resolve_dir_target(arg);

    std::error_code ec;

    if (!fs::exists(target, ec)) {
        std::cout << "Path not found: "
                  << (arg.empty() ? target.string() : arg)
                  << "\n";
        std::cout << "Resolved to: " << target.string() << "\n";
        return;
    }

    ec.clear();

    if (fs::is_regular_file(target, ec)) {
        print_regular_file(target);
        return;
    }

    ec.clear();

    if (!fs::is_directory(target, ec)) {
        std::cout << "Not a directory: " << target.string() << "\n";
        return;
    }

    fs::path shown = fs::absolute(target, ec);
    if (ec) {
        ec.clear();
        shown = target;
    }

    std::cout << "\n Directory of " << shown.string() << "\n\n";

    std::size_t dirs = 0;
    std::size_t files = 0;
    std::uint64_t bytes = 0;

    fs::directory_iterator it(target, ec);
    const fs::directory_iterator end;

    if (ec) {
        std::cout << "Unable to read directory: " << target.string() << "\n";
        return;
    }

    for (; it != end; it.increment(ec)) {
        if (ec) {
            // Keep DIR useful even when one entry cannot be advanced/read.
            // In ordinary cases increment() advances or reaches end; clear and
            // allow the loop condition to decide.  This avoids aborting the
            // whole listing because of a single filesystem hiccup.
            ec.clear();
            continue;
        }

        const auto& entry = *it;
        const auto& p = entry.path();

        auto ftime = entry.last_write_time(ec);
        if (ec) {
            ec.clear();
            continue;
        }

        std::tm tm = to_local_tm(to_time_t(ftime));

        if (entry.is_directory(ec)) {
            if (ec) {
                ec.clear();
                continue;
            }

            ++dirs;

            std::cout << std::put_time(&tm, "%Y-%m-%d %H:%M")
                      << "    <DIR>          "
                      << p.filename().string() << "\n";
        } else if (entry.is_regular_file(ec)) {
            if (ec) {
                ec.clear();
                continue;
            }

            ++files;

            auto sz = entry.file_size(ec);
            if (ec) {
                ec.clear();
                sz = 0;
            }

            bytes += static_cast<std::uint64_t>(sz);

            const bool is_dbf = has_ext_ci(p, ".dbf");

            std::cout << std::put_time(&tm, "%Y-%m-%d %H:%M")
                      << "         " << std::setw(12)
                      << format_commas(static_cast<std::uint64_t>(sz)) << " "
                      << (is_dbf ? "[DBF] " : "")
                      << p.filename().string() << "\n";
        } else {
            ec.clear();
        }

        ec.clear();
    }

    std::cout << "             " << dirs << " Dir(s)\n";
    std::cout << "             " << files << " File(s)  "
              << format_commas(bytes) << " bytes\n";
}
