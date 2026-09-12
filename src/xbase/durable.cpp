// @dottalk.file v1
// subsystem: xbase
// layer: implementation
// owns:
// project: project.x64base.runtime
// lane: AIF-078
// owner: member.derald
// status: supported
#include "xbase/durable.hpp"
#include "xbase/ramfs.hpp"

#include <string>

#ifdef _WIN32
  #ifndef WIN32_LEAN_AND_MEAN
    #define WIN32_LEAN_AND_MEAN
  #endif
  #ifndef NOMINMAX
    #define NOMINMAX
  #endif
  #include <windows.h>
  #include <filesystem>
#else
  #include <fcntl.h>
  #include <unistd.h>
  #include <cerrno>
  #include <cstring>
#endif

namespace xbase {

bool durable_sync(const std::string& path, std::string* err) noexcept
{
    try {
        // A RAM table has no durable medium. Success, and nothing done.
        if (xbase::ramfs::is_virtual(path)) return true;
    } catch (...) {
        // is_virtual must not decide durability by throwing; fall through and
        // treat the path as a real file, which is the conservative answer.
    }

#ifdef _WIN32
    // FlushFileBuffers REQUIRES GENERIC_WRITE on the handle -- a read handle
    // returns ERROR_ACCESS_DENIED. Share flags match dbf_file.cpp's existing
    // CreateFileW idiom so this cannot fail merely because the table is open.
    try {
        const std::filesystem::path winp(path);
        HANDLE h = ::CreateFileW(
            winp.c_str(),
            GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            nullptr,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            nullptr);
        if (h == INVALID_HANDLE_VALUE) {
            if (err) *err = "durable_sync: CreateFileW gle=" +
                            std::to_string(::GetLastError());
            return false;
        }
        const BOOL ok = ::FlushFileBuffers(h);
        const DWORD gle = ok ? 0u : ::GetLastError();
        ::CloseHandle(h);
        if (!ok && err) *err = "durable_sync: FlushFileBuffers gle=" +
                               std::to_string(gle);
        return ok != FALSE;
    } catch (...) {
        if (err) *err = "durable_sync: unexpected failure";
        return false;
    }
#else
    // POSIX permits fsync on a read-only descriptor and it is the portable
    // idiom (git does the same), so O_RDONLY is used deliberately: a table the
    // caller may only be able to read still gets its contents synced.
    const int fd = ::open(path.c_str(), O_RDONLY);
    if (fd < 0) {
        if (err) *err = std::string("durable_sync: open failed: ") + std::strerror(errno);
        return false;
    }
    const int rc = ::fsync(fd);
    const int e  = errno;
    ::close(fd);
    if (rc != 0) {
        if (err) *err = std::string("durable_sync: fsync failed: ") + std::strerror(e);
        return false;
    }
    return true;
#endif
}

} // namespace xbase
