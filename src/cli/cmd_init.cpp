// src/cli/cmd_init.cpp
// Initializes runtime environment before the REPL (paths, locks, init scripts)

// @dottalk.usage v1
// owner: DOT|INIT
// command: INIT
// category: script
// status: supported
// noargs: execute
// effect: initialize
// mutates: path-state lock-state delegates-command-effects
// usage-access: INIT USAGE
// summary:
//   Initialize runtime paths, cleanup stale locks, and run system/user init
//   scripts from the executable directory.
//
// usage:
//   INIT
//   INIT USAGE
//
// notes:
//   INIT with no arguments initializes default paths when needed and reports path slots.
//   INIT cleans stale DBF locks best-effort.
//   INIT runs dottalkpp.ini and init.ini from the executable directory when present.
//   INIT USAGE prints usage and does not initialize paths, cleanup locks, or run scripts.
//   Script commands run through the shell command executor and may have their own side effects.
//
// risk:
//   mutates_path_state: yes
//   cleans_lock_files: yes
//   reads_ini_files: yes
//   executes_commands: yes
//   mutates_table_data: depends on init script contents
//
// related:
//   SHUTDOWN
//   SETPATH
//   DOTSCRIPT
//

#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <cctype>

#if defined(_WIN32)
#  include <windows.h>
#elif defined(__APPLE__)
#  include <mach-o/dyld.h>
#elif defined(__linux__)
#  include <unistd.h>
#endif

#include "xbase.hpp"
#include "cli/cmd_setpath.hpp"     // uses dottalk::paths API
#include "cli/path_resolver.hpp"
#include "cli/script_reader.hpp"
#include "lock_cleanup.hpp"

namespace fs = std::filesystem;

// Match the real signature that already exists in your program.
bool shell_execute_line(xbase::DbArea& current, const std::string& line);


static std::string init_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string init_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_init_usage_request(const std::string& raw)
{
    std::string t = init_upper(init_trim(raw));
    if (t.rfind("INIT ", 0) == 0) {
        t = init_upper(init_trim(t.substr(5)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_init_usage()
{
    std::cout
        << "Usage:\n"
        << "  INIT\n"
        << "  INIT USAGE\n";
}

static fs::path get_executable_dir() {
#if defined(_WIN32)
    std::wstring buf(MAX_PATH, L'\0');
    DWORD len = ::GetModuleFileNameW(nullptr, buf.data(), static_cast<DWORD>(buf.size()));
    while (len == buf.size()) {
        buf.resize(buf.size() * 2);
        len = ::GetModuleFileNameW(nullptr, buf.data(), static_cast<DWORD>(buf.size()));
    }
    if (len > 0) {
        buf.resize(len);
        return fs::path(buf).parent_path();
    }
#elif defined(__APPLE__)
    uint32_t size = 0;
    _NSGetExecutablePath(nullptr, &size);
    std::vector<char> buf(size + 1, '\0');
    if (_NSGetExecutablePath(buf.data(), &size) == 0) {
        return fs::weakly_canonical(fs::path(buf.data())).parent_path();
    }
#elif defined(__linux__)
    std::vector<char> buf(4096, '\0');
    const ssize_t len = ::readlink("/proc/self/exe", buf.data(), buf.size() - 1);
    if (len > 0) {
        buf[static_cast<std::size_t>(len)] = '\0';
        return fs::weakly_canonical(fs::path(buf.data())).parent_path();
    }
#endif
    return fs::current_path();
}

static fs::path find_data_root_guess() {
    // Prefer data relative to the executable folder first.
    fs::path p = get_executable_dir();
    for (int i = 0; i < 14; ++i) {
        const fs::path cand = p / "data";
        if (fs::exists(cand) && fs::is_directory(cand)) {
            return fs::absolute(cand);
        }
        if (!p.has_parent_path() || p.parent_path() == p) {
            break;
        }
        p = p.parent_path();
    }

    // Fallback to current working directory search.
    p = fs::current_path();
    for (int i = 0; i < 14; ++i) {
        const fs::path cand = p / "data";
        if (fs::exists(cand) && fs::is_directory(cand)) {
            return fs::absolute(cand);
        }
        if (!p.has_parent_path() || p.parent_path() == p) {
            break;
        }
        p = p.parent_path();
    }

    return fs::absolute(get_executable_dir());
}

static std::string exe_stem_lower() {
    fs::path exe = get_executable_dir();
#if defined(_WIN32)
    std::wstring buf(MAX_PATH, L'\0');
    DWORD len = ::GetModuleFileNameW(nullptr, buf.data(), static_cast<DWORD>(buf.size()));
    while (len == buf.size()) {
        buf.resize(buf.size() * 2);
        len = ::GetModuleFileNameW(nullptr, buf.data(), static_cast<DWORD>(buf.size()));
    }
    if (len > 0) {
        buf.resize(len);
        exe = fs::path(buf);
    }
#elif defined(__APPLE__)
    uint32_t size = 0;
    _NSGetExecutablePath(nullptr, &size);
    std::vector<char> buf(size + 1, '\0');
    if (_NSGetExecutablePath(buf.data(), &size) == 0) {
        exe = fs::weakly_canonical(fs::path(buf.data()));
    }
#elif defined(__linux__)
    std::vector<char> buf(4096, '\0');
    const ssize_t len = ::readlink("/proc/self/exe", buf.data(), buf.size() - 1);
    if (len > 0) {
        buf[static_cast<std::size_t>(len)] = '\0';
        exe = fs::weakly_canonical(fs::path(buf.data()));
    }
#endif

    std::string stem = exe.stem().string();
    for (char& c : stem) {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }
    return stem;
}

static fs::path find_system_ini_in_bin() {
    const fs::path bin = get_executable_dir();
    const std::string stem = exe_stem_lower();

    if (!stem.empty()) {
        const fs::path exact = bin / (stem + ".ini");
        if (fs::exists(exact) && fs::is_regular_file(exact)) {
            return exact;
        }
    }

    return {};
}

static fs::path find_user_ini_in_bin() {
    const fs::path bin = get_executable_dir();
    const fs::path user_ini = bin / "init.ini";

    if (fs::exists(user_ini) && fs::is_regular_file(user_ini)) {
        return user_ini;
    }

    return {};
}

static bool begins_with_comment(const std::string& s) {
    std::size_t i = 0;
    while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) {
        ++i;
    }
    if (i >= s.size()) {
        return false;
    }
    if (s[i] == '#') {
        return true;
    }
    if (s[i] == '*') {
        return true;
    }
    return (s[i] == '/' && i + 1 < s.size() && s[i + 1] == '/');
}

static void run_init_script(xbase::DbArea& current, const fs::path& ini_path, const char* label) {
    std::ifstream in(ini_path, std::ios::binary);
    if (!in) {
        std::cout << "INIT: unable to open " << ini_path.string() << "\n";
        return;
    }

    std::cout << "INIT: processing " << label << " " << ini_path.string() << "\n";

    std::string line;
    std::size_t line_no = 0;

    while (read_script_command(in, line)) {
        ++line_no;

        if (line.empty()) {
            continue;
        }

        if (begins_with_comment(line)) {
            continue;
        }

        try {
            (void)shell_execute_line(current, line);
        } catch (const std::exception& ex) {
            std::cout << "INIT: " << ini_path.filename().string()
                      << ":" << line_no << ": " << ex.what() << "\n";
        } catch (...) {
            std::cout << "INIT: " << ini_path.filename().string()
                      << ":" << line_no << ": unknown error\n";
        }
    }
}

void cmd_INIT(xbase::DbArea& current, std::istringstream& in) {
    if (is_init_usage_request(in.str())) {
        print_init_usage();
        return;
    }

    using namespace dottalk::paths;

    if (state().data_root.empty()
        || get_slot(Slot::DBF).empty()
        || get_slot(Slot::INDEXES).empty()
        || get_slot(Slot::LMDB).empty()) {
        const fs::path root = find_data_root_guess();
        init_defaults(root);
    }

    std::cout << "INIT: Paths\n";
    std::cout << "  BIN        : " << get_executable_dir().string() << "\n";
    std::cout << "  DATA       : " << state().data_root.string() << "\n";
    std::cout << "  DBF        : " << get_slot(Slot::DBF).string() << "\n";
    std::cout << "  INDEXES    : " << get_slot(Slot::INDEXES).string() << "\n";
    std::cout << "  LMDB       : " << get_slot(Slot::LMDB).string() << "\n";
    std::cout << "  WORKSPACES : " << get_slot(Slot::WORKSPACES).string() << "\n";
    std::cout << "  SCHEMAS    : " << get_slot(Slot::SCHEMAS).string() << "\n";
    std::cout << "  PROJECTS   : " << get_slot(Slot::PROJECTS).string() << "\n";
    std::cout << "  SCRIPTS    : " << get_slot(Slot::SCRIPTS).string() << "\n";
    std::cout << "  TESTS      : " << get_slot(Slot::TESTS).string() << "\n";
    std::cout << "  HELP       : " << get_slot(Slot::HELP).string() << "\n";
    std::cout << "  LOGS       : " << get_slot(Slot::LOGS).string() << "\n";
    std::cout << "  TMP        : " << get_slot(Slot::TMP).string() << "\n";

    try {
        dottalk::locks::cleanup_stale_locks(get_slot(Slot::DBF));
    } catch (...) {
        std::cout << "INIT: lock cleanup failed (ignored)\n";
    }

    try {
        const fs::path system_ini = find_system_ini_in_bin();
        const fs::path user_ini   = find_user_ini_in_bin();

        bool ran_any = false;

        if (!system_ini.empty()) {
            run_init_script(current, system_ini, "system .ini");
            ran_any = true;
        }

        if (!user_ini.empty()) {
            bool same_file = false;
            try {
                same_file = fs::equivalent(system_ini, user_ini);
            } catch (...) {
                same_file = (!system_ini.empty() && system_ini == user_ini);
            }

            if (!same_file) {
                run_init_script(current, user_ini, "user .ini");
                ran_any = true;
            }
        }

        if (!ran_any) {
            std::cout << "INIT: no .ini file found in " << get_executable_dir().string() << "\n";
        }
    } catch (const std::exception& ex) {
        std::cout << "INIT: ini processing failed: " << ex.what() << "\n";
    } catch (...) {
        std::cout << "INIT: ini processing failed (unknown error)\n";
    }
}