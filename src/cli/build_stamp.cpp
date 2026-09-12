// @dottalk.file v1
// subsystem: cli
// layer: support
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// The implementation of dottalk/build_stamp.hpp. It lives in a .cpp rather than
// in the header for one reason: <windows.h> defines min, max and a few hundred
// other things, and a header included by two command TUs has no business
// dragging that into them.
//
// It was LIFTED from cmd_version.cpp rather than copied. The two statics there
// (version_executable_path and version_build_stamp) are now gone from that file
// and it calls these, so there is exactly one answer to "which build" in the
// tree and VERSION and a regression log cannot disagree about it.

#include "dottalk/build_stamp.hpp"

#include "dottalk/version.hpp"

#include <chrono>
#include <ctime>
#include <filesystem>
#include <iomanip>
#include <sstream>
#include <system_error>
#include <vector>

#if defined(_WIN32)
#  include <windows.h>
#elif defined(__APPLE__)
#  include <mach-o/dyld.h>
#elif defined(__linux__)
#  include <unistd.h>
#endif

namespace dottalk {
namespace {

std::filesystem::path executable_path_impl()
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

} // namespace

std::string executable_path()
{
    return executable_path_impl().string();
}

std::string version_identity()
{
    return version::display_version();
}

std::string build_stamp()
{
    namespace fs = std::filesystem;
    std::error_code ec;
    const fs::path exe = executable_path_impl();
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

    // Weaker, and preserved deliberately -- see the header.
    return std::string(__DATE__) + " " + __TIME__;
}

} // namespace dottalk
