#include "xindex/index_format_detect.hpp"

namespace xindex::fmt {

std::string upper_copy_ascii(std::string s) {
    for (char& ch : s) {
        if (ch >= 'a' && ch <= 'z') {
            ch = static_cast<char>(ch - ('a' - 'A'));
        }
    }
    return s;
}

static bool has_ext_eq(const std::filesystem::path& p, const char* want_upper) {
    std::string ext = upper_copy_ascii(p.extension().string());
    return ext == want_upper;
}

bool has_ext_inx(const std::filesystem::path& p) { return has_ext_eq(p, ".INX"); }
bool has_ext_cnx(const std::filesystem::path& p) { return has_ext_eq(p, ".CNX"); }
bool has_ext_cdx(const std::filesystem::path& p) { return has_ext_eq(p, ".CDX"); }
bool has_ext_six(const std::filesystem::path& p) { return has_ext_eq(p, ".SIX"); }
bool has_ext_scx(const std::filesystem::path& p) { return has_ext_eq(p, ".SCX"); }

bool is_inx(const std::filesystem::path& p) { return has_ext_inx(p); }
bool is_cnx(const std::filesystem::path& p) { return has_ext_cnx(p); }
bool is_cdx(const std::filesystem::path& p) { return has_ext_cdx(p); }
bool is_six(const std::filesystem::path& p) { return has_ext_six(p); }
bool is_scx(const std::filesystem::path& p) { return has_ext_scx(p); }

IndexFormat detect(const std::filesystem::path& p) {
    if (is_inx(p)) return IndexFormat::INX;
    if (is_cnx(p)) return IndexFormat::CNX;
    if (is_cdx(p)) return IndexFormat::CDX;
    if (is_six(p)) return IndexFormat::SIX;
    if (is_scx(p)) return IndexFormat::SCX;
    return IndexFormat::Unknown;
}

const char* to_string(IndexFormat f) noexcept {
    switch (f) {
    case IndexFormat::INX:     return "INX";
    case IndexFormat::CNX:     return "CNX";
    case IndexFormat::CDX:     return "CDX";
    case IndexFormat::SIX:     return "SIX";
    case IndexFormat::SCX:     return "SCX";
    default:                   return "UNKNOWN";
    }
}

} // namespace xindex::fmt