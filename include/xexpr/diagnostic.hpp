// @dottalk.file v1
// subsystem: xexpr
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <cstddef>
#include <string>

namespace xexpr {

struct Diagnostic {
    std::string code;
    std::string message;
    std::size_t position = 0;
    std::string token;

    explicit operator bool() const noexcept {
        return !code.empty() || !message.empty();
    }
};

} // namespace xexpr
