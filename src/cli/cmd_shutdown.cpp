// src/cli/cmd_shutdown.cpp
// Runs optional shutdown script from bin/shutdown.ini

// @dottalk.usage v1
// owner: DOT|SHUTDOWN
// command: SHUTDOWN
// category: script
// status: supported
// noargs: execute
// effect: execute
// mutates: delegates-command-effects session filesystem
// usage-access: SHUTDOWN USAGE
// summary:
//   Run the optional shutdown.ini script from the executable directory.
//
// usage:
//   SHUTDOWN
//   SHUTDOWN USAGE
//
// notes:
//   SHUTDOWN with no arguments looks for shutdown.ini beside the executable and executes it when present.
//   SHUTDOWN USAGE prints usage and does not execute shutdown.ini.
//   Each non-empty shutdown.ini line is executed through the shell command executor.
//   UTF-8 BOM and trailing carriage returns are handled.
//   SHUTDOWN may indirectly mutate data, session state, or files depending on script contents.
//
// risk:
//   reads_files: shutdown.ini when present
//   executes_commands: yes
//   mutates_table_data: depends on script contents
//   mutates_session: depends on script contents
//   writes_files: depends on script contents
//
// related:
//   INIT
//   TEST
//   DOTSCRIPT
//

#include <cctype>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#if defined(_WIN32)
#  include <windows.h>
#elif defined(__APPLE__)
#  include <mach-o/dyld.h>
#elif defined(__linux__)
#  include <unistd.h>
#endif

#include "xbase.hpp"

namespace fs = std::filesystem;


namespace {
static std::string shutdown_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string shutdown_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_shutdown_usage_request(const std::string& raw)
{
    std::string t = shutdown_upper(shutdown_trim(raw));
    if (t.rfind("SHUTDOWN ", 0) == 0) {
        t = shutdown_upper(shutdown_trim(t.substr(9)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_shutdown_usage()
{
    std::cout
        << "Usage:\n"
        << "  SHUTDOWN\n"
        << "  SHUTDOWN USAGE\n"
        << "Notes:\n"
        << "  - SHUTDOWN with no arguments executes shutdown.ini when present.\n"
        << "  - SHUTDOWN USAGE prints this usage and does not execute shutdown.ini.\n";
}
} // namespace

// Match the real signature that already exists in your program.
bool shell_execute_line(xbase::DbArea& current, const std::string& line);

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

static void strip_utf8_bom(std::string& s) {
    if (s.size() >= 3 &&
        static_cast<unsigned char>(s[0]) == 0xEF &&
        static_cast<unsigned char>(s[1]) == 0xBB &&
        static_cast<unsigned char>(s[2]) == 0xBF) {
        s.erase(0, 3);
    }
}

static void trim_trailing_cr(std::string& s) {
    if (!s.empty() && s.back() == '\r') {
        s.pop_back();
    }
}

static void run_shutdown_script(xbase::DbArea& current, const fs::path& ini_path) {
    std::ifstream in(ini_path, std::ios::binary);
    if (!in) {
        std::cout << "SHUTDOWN: unable to open " << ini_path.string() << "\n";
        return;
    }

    std::cout << "SHUTDOWN: processing " << ini_path.string() << "\n";

    std::string line;
    std::size_t line_no = 0;

    while (std::getline(in, line)) {
        ++line_no;
        trim_trailing_cr(line);
        if (line_no == 1) {
            strip_utf8_bom(line);
        }

        if (line.empty()) {
            continue;
        }

        try {
            (void)shell_execute_line(current, line);
        } catch (const std::exception& ex) {
            std::cout << "SHUTDOWN: " << ini_path.filename().string()
                      << ":" << line_no << ": " << ex.what() << "\n";
        } catch (...) {
            std::cout << "SHUTDOWN: " << ini_path.filename().string()
                      << ":" << line_no << ": unknown error\n";
        }
    }
}

void cmd_SHUTDOWN(xbase::DbArea& current, std::istringstream& in) {
    const std::string raw_args = in.str();
    if (is_shutdown_usage_request(raw_args)) {
        print_shutdown_usage();
        return;
    }

    try {
        const fs::path ini_path = get_executable_dir() / "shutdown.ini";
        if (fs::exists(ini_path) && fs::is_regular_file(ini_path)) {
            run_shutdown_script(current, ini_path);
        } else {
            std::cout << "SHUTDOWN: no shutdown.ini found in "
                      << get_executable_dir().string() << "\n";
        }
    } catch (const std::exception& ex) {
        std::cout << "SHUTDOWN: ini processing failed: " << ex.what() << "\n";
    } catch (...) {
        std::cout << "SHUTDOWN: ini processing failed (unknown error)\n";
    }
}