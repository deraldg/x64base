// src/cli/cmd_drawio.cpp
//
// DRAWIO command
//
// Launches diagrams.net / draw.io and can list/open project diagram files.
//
// Usage:
//   DRAWIO
//   DRAWIO PATHS
//   DRAWIO LIST [SYSTEM|USER|ALL]
//   DRAWIO OPEN
//   DRAWIO OPEN <url-or-path>
//   DRAWIO OPEN [SYSTEM|USER|ALL] <n|filename>

// @dottalk.usage v1
// owner: DOT|DRAWIO
// command: DRAWIO
// category: integration
// status: supported
// noargs: execute
// effect: launch
// mutates: external-browser
// usage-access: DRAWIO USAGE
// summary:
//   Launch diagrams.net, or list/open draw.io files from configured diagram paths.
//
// usage:
//   DRAWIO USAGE
//   DRAWIO
//   DRAWIO PATHS
//   DRAWIO LIST
//   DRAWIO LIST SYSTEM
//   DRAWIO LIST USER
//   DRAWIO LIST ALL
//   DRAWIO OPEN
//   DRAWIO OPEN <url-or-path>
//   DRAWIO OPEN SYSTEM <n|filename>
//   DRAWIO OPEN USER <n|filename>
//   DRAWIO OPEN ALL <n|filename>
//
// notes:
//   DRAWIO with no arguments launches the default diagrams.net URL.
//   DRAWIO OPEN with no target also launches the default diagrams.net URL.
//   DRAWIO LIST defaults to SYSTEM.
//   SYSTEM diagrams come from SETPATH SYSTEM_DIAGRAMS / DIAGRAMS.
//   USER diagrams come from SETPATH USER_DIAGRAMS.
//   DRAWIO does not mutate table data or workspace state.
//
// risk:
//   launches_external_browser: yes
//   opens_url: yes
//   reads_filesystem: yes
//   mutates_table_data: no
//   writes_files: no
//
// related:
//   HELP
//   EXPORT
//   SETPATH
//

#include "xbase.hpp"
#include "textio.hpp"
#include "common/path_state.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <system_error>
#include <vector>

#if defined(_WIN32)
    #include <windows.h>
    #include <shellapi.h>
#endif

namespace fs = std::filesystem;

namespace {

constexpr const char* kDefaultUrl = "https://app.diagrams.net";

struct DiagramEntry {
    std::string scope;
    fs::path root;
    fs::path path;
};

static std::string trim_copy(std::string s) {
    return textio::trim(std::move(s));
}

static std::string up_copy(std::string s) {
    for (auto& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static bool is_number(const std::string& s) {
    return !s.empty() &&
           std::all_of(s.begin(), s.end(), [](unsigned char c) { return std::isdigit(c) != 0; });
}

static bool is_url(const std::string& s) {
    const std::string u = up_copy(s);
    return u.rfind("HTTP://", 0) == 0 ||
           u.rfind("HTTPS://", 0) == 0 ||
           u.rfind("FILE://", 0) == 0;
}

static bool has_drawio_extension(const fs::path& p) {
    const std::string ext = up_copy(p.extension().string());
    return ext == ".DRAWIO";
}

static void print_usage() {
    std::cout
        << "Usage:\n"
        << "  DRAWIO USAGE\n"
        << "  DRAWIO\n"
        << "  DRAWIO PATHS\n"
        << "  DRAWIO LIST [SYSTEM|USER|ALL]\n"
        << "  DRAWIO OPEN\n"
        << "  DRAWIO OPEN <url-or-path>\n"
        << "  DRAWIO OPEN SYSTEM <n|filename>\n"
        << "  DRAWIO OPEN USER <n|filename>\n"
        << "  DRAWIO OPEN ALL <n|filename>\n"
        << "\n"
        << "Paths:\n"
        << "  SYSTEM = SETPATH SYSTEM_DIAGRAMS / DIAGRAMS\n"
        << "  USER   = SETPATH USER_DIAGRAMS\n"
        << "\n"
        << "Default:\n"
        << "  " << kDefaultUrl << "\n";
}

static bool launch_target(const std::string& target) {
#if defined(_WIN32)
    HINSTANCE rc = ShellExecuteA(
        nullptr,
        "open",
        target.c_str(),
        nullptr,
        nullptr,
        SW_SHOWNORMAL
    );
    return reinterpret_cast<intptr_t>(rc) > 32;
#elif defined(__APPLE__)
    std::string cmd = "open \"" + target + "\"";
    return std::system(cmd.c_str()) == 0;
#else
    std::string cmd = "xdg-open \"" + target + "\" >/dev/null 2>&1";
    return std::system(cmd.c_str()) == 0;
#endif
}

static fs::path root_for_scope(const std::string& scope) {
    const std::string S = up_copy(scope);
    if (S == "USER") {
        return dottalk::paths::get_slot(dottalk::paths::Slot::USER_DIAGRAMS);
    }
    return dottalk::paths::get_slot(dottalk::paths::Slot::SYSTEM_DIAGRAMS);
}

static void print_paths() {
    std::cout << "DRAWIO PATHS\n";
    std::cout << "----------------------------------------\n";
    std::cout << "  SYSTEM_DIAGRAMS = "
              << dottalk::paths::get_slot(dottalk::paths::Slot::SYSTEM_DIAGRAMS).string() << "\n";
    std::cout << "  USER_DIAGRAMS   = "
              << dottalk::paths::get_slot(dottalk::paths::Slot::USER_DIAGRAMS).string() << "\n";
}

static void append_scope_files(std::vector<DiagramEntry>& out, const std::string& scope) {
    const fs::path root = root_for_scope(scope);
    if (root.empty()) {
        return;
    }

    std::error_code ec;
    if (!fs::exists(root, ec) || ec || !fs::is_directory(root, ec) || ec) {
        return;
    }

    for (const auto& de : fs::directory_iterator(root, fs::directory_options::skip_permission_denied, ec)) {
        if (ec) {
            ec.clear();
            continue;
        }
        if (!de.is_regular_file(ec) || ec) {
            ec.clear();
            continue;
        }
        const fs::path p = de.path();
        if (has_drawio_extension(p)) {
            out.push_back(DiagramEntry{scope, root, p});
        }
    }
}

static std::vector<DiagramEntry> list_entries(const std::string& scope) {
    std::vector<DiagramEntry> entries;
    const std::string S = up_copy(scope.empty() ? "SYSTEM" : scope);

    if (S == "ALL") {
        append_scope_files(entries, "SYSTEM");
        append_scope_files(entries, "USER");
    } else if (S == "USER") {
        append_scope_files(entries, "USER");
    } else {
        append_scope_files(entries, "SYSTEM");
    }

    std::sort(entries.begin(), entries.end(), [](const DiagramEntry& a, const DiagramEntry& b) {
        const std::string as = up_copy(a.scope + ":" + a.path.filename().string());
        const std::string bs = up_copy(b.scope + ":" + b.path.filename().string());
        return as < bs;
    });
    return entries;
}

static void print_list(const std::string& scope) {
    const std::string S = up_copy(scope.empty() ? "SYSTEM" : scope);
    const auto entries = list_entries(S);

    std::cout << "DRAWIO LIST " << S << "\n";
    std::cout << "----------------------------------------\n";

    if (entries.empty()) {
        std::cout << "  no .drawio files found\n";
        if (S == "SYSTEM" || S == "ALL") {
            std::cout << "  SYSTEM_DIAGRAMS = " << root_for_scope("SYSTEM").string() << "\n";
        }
        if (S == "USER" || S == "ALL") {
            std::cout << "  USER_DIAGRAMS   = " << root_for_scope("USER").string() << "\n";
        }
        return;
    }

    for (size_t i = 0; i < entries.size(); ++i) {
        std::cout << "  " << (i + 1) << ". [" << entries[i].scope << "] "
                  << entries[i].path.filename().string() << "\n";
    }
}

static std::optional<fs::path> resolve_named_in_entries(const std::vector<DiagramEntry>& entries,
                                                        const std::string& token) {
    if (token.empty()) {
        return std::nullopt;
    }

    if (is_number(token)) {
        const unsigned long long n = std::stoull(token);
        if (n >= 1 && n <= entries.size()) {
            return entries[static_cast<size_t>(n - 1)].path;
        }
        return std::nullopt;
    }

    const std::string wanted = up_copy(token);
    const std::string wanted_drawio = up_copy(token + ".drawio");

    for (const auto& e : entries) {
        const std::string base = up_copy(e.path.filename().string());
        if (base == wanted || base == wanted_drawio) {
            return e.path;
        }
    }

    return std::nullopt;
}

static std::optional<fs::path> resolve_local_file_or_diagram(const std::string& target,
                                                             const std::string& scope) {
    const fs::path raw(target);

    std::error_code ec;
    if ((raw.is_absolute() || raw.has_parent_path()) && fs::exists(raw, ec) && !ec) {
        return fs::absolute(raw, ec).lexically_normal();
    }

    if (!raw.has_parent_path() && fs::exists(raw, ec) && !ec) {
        return fs::absolute(raw, ec).lexically_normal();
    }

    return resolve_named_in_entries(list_entries(scope), target);
}

static void open_target_report(const std::string& target, const std::string& label) {
    if (launch_target(target)) {
        std::cout << "DRAWIO: launched " << label << "\n";
    } else {
        std::cout << "DRAWIO: failed to launch " << label << "\n";
    }
}

} // namespace

void cmd_DRAWIO(xbase::DbArea& area, std::istringstream& iss) {
    (void)area;

    std::string sub;
    iss >> sub;

    if (sub.empty()) {
        open_target_report(kDefaultUrl, kDefaultUrl);
        return;
    }

    const std::string SUB = up_copy(sub);

    if (SUB == "USAGE" || SUB == "HELP" || SUB == "?" || SUB == "/?" || SUB == "-H" || SUB == "--HELP") {
        print_usage();
        return;
    }

    if (SUB == "PATHS") {
        print_paths();
        return;
    }

    if (SUB == "LIST" || SUB == "LS" || SUB == "DIR") {
        std::string scope;
        iss >> scope;
        scope = scope.empty() ? "SYSTEM" : up_copy(scope);
        if (scope != "SYSTEM" && scope != "USER" && scope != "ALL") {
            std::cout << "DRAWIO: unknown list scope: " << scope << "\n";
            print_usage();
            return;
        }
        print_list(scope);
        return;
    }

    if (SUB == "OPEN") {
        std::string first;
        iss >> first;

        if (first.empty()) {
            open_target_report(kDefaultUrl, kDefaultUrl);
            return;
        }

        const std::string FIRST = up_copy(first);
        if (FIRST == "SYSTEM" || FIRST == "USER" || FIRST == "ALL") {
            std::string selector;
            std::getline(iss >> std::ws, selector);
            selector = trim_copy(selector);
            if (selector.empty()) {
                print_list(FIRST);
                return;
            }
            auto found = resolve_named_in_entries(list_entries(FIRST), selector);
            if (!found.has_value()) {
                std::cout << "DRAWIO: no diagram matched " << selector << " in " << FIRST << "\n";
                return;
            }
            open_target_report(found->string(), found->filename().string());
            return;
        }

        std::string rest;
        std::getline(iss >> std::ws, rest);
        const std::string target = trim_copy(rest.empty() ? first : (first + " " + rest));

        if (is_url(target)) {
            open_target_report(target, target);
            return;
        }

        auto found = resolve_local_file_or_diagram(target, "ALL");
        if (found.has_value()) {
            open_target_report(found->string(), found->filename().string());
            return;
        }

        // Preserve the old permissive behavior: if it is not a known local diagram,
        // pass the supplied target through to the platform opener.
        open_target_report(target, target);
        return;
    }

    print_usage();
}
