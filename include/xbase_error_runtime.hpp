#pragma once
// xbase_error_runtime.hpp
// Lightweight runtime helpers for xbase::error::code.

#include "xbase_error_codes.hpp"

#include <sstream>
#include <string>

namespace xbase {
namespace error {

inline std::string describe(code ec)
{
    std::ostringstream oss;
    oss << to_string(ec)
        << " [severity=" << to_severity_string(ec.get_severity())
        << ", facility=" << to_facility_string(ec.get_facility())
        << ", number=" << ec.get_number()
        << ", value=0x" << std::hex << static_cast<unsigned long>(ec.value) << std::dec
        << "]";
    return oss.str();
}

inline bool failed(code ec) noexcept
{
    return ec.failed();
}

} // namespace error
} // namespace xbase
