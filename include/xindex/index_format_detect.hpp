#pragma once

#include <filesystem>
#include <string>

namespace xindex::fmt {

enum class IndexFormat {
    Unknown = 0,
    INX,
    CNX,
    CDX,
    SIX,
    SCX
};

inline std::string upper_copy_ascii(std::string s) {
    for (char& ch : s) {
        if (ch >= 'a' && ch <= 'z') {
            ch = static_cast<char>(ch - ('a' - 'A'));
        }
    }
    return s;
}

inline bool has_ext_eq(const std::filesystem::path& p, const char* want_upper) {
    const std::string ext = upper_copy_ascii(p.extension().string());
    return ext == want_upper;
}

inline bool has_ext_inx(const std::filesystem::path& p) { return has_ext_eq(p, ".INX"); }
inline bool has_ext_cnx(const std::filesystem::path& p) { return has_ext_eq(p, ".CNX"); }
inline bool has_ext_cdx(const std::filesystem::path& p) { return has_ext_eq(p, ".CDX"); }
inline bool has_ext_six(const std::filesystem::path& p) { return has_ext_eq(p, ".SIX"); }
inline bool has_ext_scx(const std::filesystem::path& p) { return has_ext_eq(p, ".SCX"); }

inline bool is_inx(const std::filesystem::path& p) { return has_ext_inx(p); }
inline bool is_cnx(const std::filesystem::path& p) { return has_ext_cnx(p); }
inline bool is_cdx(const std::filesystem::path& p) { return has_ext_cdx(p); }
inline bool is_six(const std::filesystem::path& p) { return has_ext_six(p); }
inline bool is_scx(const std::filesystem::path& p) { return has_ext_scx(p); }

inline IndexFormat detect(const std::filesystem::path& p) {
    if (is_inx(p)) return IndexFormat::INX;
    if (is_cnx(p)) return IndexFormat::CNX;
    if (is_cdx(p)) return IndexFormat::CDX;
    if (is_six(p)) return IndexFormat::SIX;
    if (is_scx(p)) return IndexFormat::SCX;
    return IndexFormat::Unknown;
}

inline const char* to_string(IndexFormat f) noexcept {
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