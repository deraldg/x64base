// @dottalk.file v1
// subsystem: cli
// layer: helper
// project: project.x64base.runtime
// lane: AIF-174
// owner: member.derald
// status: supported

#pragma once
#include <cstdio>
#include <memory>
#include <ostream>
#include <string>

namespace cli {
// Caller must perform host-command authorization before invoking this helper.
// Shell children share one pipe for stdout/stderr, preserving their merged order.
// Blocks until the child exits; returns the platform close status, or -1 on
// launch/read failure. The output stream is caller-owned. No authorization is
// granted here, and no interpretation of the child's exit status is performed.
inline int stream_shell_output(const std::string& command, std::ostream& output) {
    const auto redirected = "(" + command + ") 2>&1";
#ifdef _WIN32
    auto close = &_pclose;
    FILE* raw = _popen(redirected.c_str(), "r");
#else
    auto close = &pclose;
    FILE* raw = popen(redirected.c_str(), "r");
#endif
    if (!raw) return -1;
    std::unique_ptr<FILE, decltype(close)> pipe(raw, close);
    char buffer[4096];
    while (const auto count = std::fread(buffer, 1, sizeof(buffer), pipe.get()))
        output.write(buffer, static_cast<std::streamsize>(count));
    const bool read_failed = std::ferror(pipe.get()) != 0;
    const int status = close(pipe.release());
    return read_failed ? -1 : status;
}
} // namespace cli
