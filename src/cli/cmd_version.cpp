// @dottalk.usage v1
// owner: DOT|VERSION
// command: VERSION
// category: report
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: VERSION USAGE
// summary:
//   Report the DotTalk++ version label and build date/time.
//
// usage:
//   VERSION
//   VERSION USAGE
//
// notes:
//   VERSION with no arguments reports version and build information.
//   VERSION USAGE prints usage.
//   VERSION is read-only and does not mutate table data or session state.
//
// risk:
//   mutates_table_data: no
//   mutates_session: no
//
// related:
//   ABOUT
//   SQLVER
//

#include "cmd_version.hpp"
#include <algorithm>
#include <chrono>
#include <cctype>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

#if defined(_WIN32)
#  include <windows.h>
#elif defined(__APPLE__)
#  include <mach-o/dyld.h>
#elif defined(__linux__)
#  include <unistd.h>
#endif

#ifndef DOTTALKPP_VERSION
// #define DOTTALKPP_VERSION "alpha-v15.0"
#define DOTTALKPP_VERSION "beta-0"
#endif


namespace {
static std::string version_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string version_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_version_usage_request(const std::string& raw)
{
    std::string t = version_upper(version_trim(raw));
    if (t.rfind("VERSION ", 0) == 0) {
        t = version_upper(version_trim(t.substr(8)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_version_usage()
{
    std::cout << "Usage:\n"
              << "  VERSION\n"
              << "  VERSION USAGE\n";
}

static std::filesystem::path version_executable_path()
{
#if defined(_WIN32)
    std::wstring buf(MAX_PATH, L'\0');
    DWORD len = ::GetModuleFileNameW(nullptr, buf.data(), static_cast<DWORD>(buf.size()));
    while (len == buf.size()) {
        buf.resize(buf.size() * 2);
        len = ::GetModuleFileNameW(nullptr, buf.data(), static_cast<DWORD>(buf.size()));
    }
    if (len > 0) {
        buf.resize(len);
        return std::filesystem::path(buf);
    }
#elif defined(__APPLE__)
    uint32_t size = 0;
    _NSGetExecutablePath(nullptr, &size);
    std::vector<char> buf(size + 1, '\0');
    if (_NSGetExecutablePath(buf.data(), &size) == 0) {
        return std::filesystem::weakly_canonical(std::filesystem::path(buf.data()));
    }
#elif defined(__linux__)
    std::vector<char> buf(4096, '\0');
    const ssize_t len = ::readlink("/proc/self/exe", buf.data(), buf.size() - 1);
    if (len > 0) {
        buf[static_cast<std::size_t>(len)] = '\0';
        return std::filesystem::weakly_canonical(std::filesystem::path(buf.data()));
    }
#endif
    return {};
}

static std::string version_build_stamp()
{
    namespace fs = std::filesystem;
    std::error_code ec;
    const fs::path exe = version_executable_path();
    if (!exe.empty()) {
        const auto ftime = fs::last_write_time(exe, ec);
        if (!ec) {
            const auto sctp = std::chrono::system_clock::now() +
                              (ftime - fs::file_time_type::clock::now());
            const std::time_t tt = std::chrono::system_clock::to_time_t(sctp);
            std::tm tm_buf{};
#if defined(_WIN32)
            if (localtime_s(&tm_buf, &tt) == 0) {
#else
            if (localtime_r(&tt, &tm_buf) != nullptr) {
#endif
                std::ostringstream oss;
                oss << std::put_time(&tm_buf, "%b %d %Y %H:%M:%S");
                return oss.str();
            }
        }
    }

    return std::string(__DATE__) + " " + __TIME__;
}
} // namespace

void cmd_VERSION(xbase::DbArea& area, std::istringstream& args) {
    (void)area;
    if (is_version_usage_request(args.str())) {
        print_version_usage();
        return;
    }

    const std::string stamp = version_build_stamp();
    std::cout << "dottalk++ " << DOTTALKPP_VERSION
              << "  (" << stamp << ")\n";
    std::cout << "DotTalk++ build " << stamp << "\n";

}
 


