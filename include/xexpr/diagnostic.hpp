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
