// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns:
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: supported

#pragma once

#include <cctype>
#include <string>

#include "xbase.hpp"

namespace cli::fixed_width {

inline void rtrim(std::string& s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
}

inline std::string lpad(const std::string& s, std::size_t width)
{
    if (s.size() >= width) return s.substr(s.size() - width);
    return std::string(width - s.size(), ' ') + s;
}

inline std::string rpad(const std::string& s, std::size_t width)
{
    if (s.size() >= width) return s.substr(0, width);
    return s + std::string(width - s.size(), ' ');
}

inline std::size_t field_width(const xbase::FieldDef& f)
{
    if (f.length > 0) return static_cast<std::size_t>(f.length);
    if (f.type == 'D') return 8u;
    if (f.type == 'L') return 1u;
    return 10u;
}

inline bool right_aligned(char type)
{
    return type == 'N' || type == 'F' || type == 'Y';
}

inline std::string build_schema_aligned_row(xbase::DbArea& area)
{
    const auto& fields = area.fields();
    std::size_t total_len = 0;
    for (const auto& f : fields) {
        total_len += field_width(f);
    }

    std::string out;
    out.reserve(total_len);

    for (std::size_t i = 0; i < fields.size(); ++i) {
        const auto& f = fields[i];
        std::string value = area.get(static_cast<int>(i + 1));
        rtrim(value);

        const std::size_t width = field_width(f);
        out += right_aligned(f.type) ? lpad(value, width) : rpad(value, width);
    }

    return out;
}

} // namespace cli::fixed_width
