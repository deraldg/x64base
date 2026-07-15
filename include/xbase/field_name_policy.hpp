#pragma once

#include <algorithm>
#include <cctype>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>
#include <unordered_set>
#include <vector>

namespace xbase::field_name_policy {

constexpr std::size_t DBF_DESCRIPTOR_TOKEN_BYTES = 10;

struct FieldNamePlan {
    std::string logical_name;     // authoritative name
    std::string descriptor_name;  // physical DBF/VFP descriptor token
    bool truncated = false;       // logical name exceeded descriptor width
    bool mangled = false;         // descriptor was changed to avoid collision
    bool sanitized = false;       // descriptor contains DBF-safe normalized chars
};

inline std::string descriptor_key(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

inline bool dbf_safe_char(unsigned char c) noexcept
{
    return std::isalnum(c) || c == '_';
}

inline std::string normalize_descriptor_base(const std::string& logical)
{
    std::string out;
    out.reserve(logical.size());

    for (unsigned char c : logical) {
        if (dbf_safe_char(c)) {
            out.push_back(static_cast<char>(std::toupper(c)));
        } else {
            out.push_back('_');
        }
    }

    if (out.empty()) out = "FIELD";
    return out;
}

inline std::string first_n(const std::string& s, std::size_t n)
{
    if (s.size() <= n) return s;
    return s.substr(0, n);
}

inline std::string make_mangled_token(const std::string& base,
                                      std::uint64_t ordinal,
                                      std::size_t width = DBF_DESCRIPTOR_TOKEN_BYTES)
{
    std::string suffix = "~" + std::to_string(ordinal);
    if (suffix.size() >= width) {
        return first_n(suffix, width);
    }

    const std::size_t prefix_len = width - suffix.size();
    std::string prefix = first_n(base, prefix_len);
    if (prefix.empty()) prefix = "F";
    return first_n(prefix + suffix, width);
}

inline std::string base36(std::uint64_t v)
{
    static constexpr char chars[] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    if (v == 0) return "0";

    std::string out;
    while (v > 0) {
        out.push_back(chars[v % 36]);
        v /= 36;
    }
    std::reverse(out.begin(), out.end());
    return out;
}

inline std::string make_hash_token(const std::string& base,
                                   std::size_t width = DBF_DESCRIPTOR_TOKEN_BYTES)
{
    const std::uint64_t h = static_cast<std::uint64_t>(std::hash<std::string>{}(base));
    std::string suffix = "~" + first_n(base36(h), 4);
    if (suffix.size() >= width) return first_n(suffix, width);
    return first_n(first_n(base, width - suffix.size()) + suffix, width);
}

// X64 policy:
// - logical_name remains authoritative and is not modified.
// - descriptor_name is a unique 10-byte DBF/VFP fallback token.
// - first field gets the obvious 10-byte truncation when available.
// - later collisions get DOS/Windows-style ~n aliases.
inline std::vector<FieldNamePlan> plan_x64_unique_fallback(const std::vector<std::string>& logical_names)
{
    std::vector<FieldNamePlan> plans;
    plans.reserve(logical_names.size());

    std::unordered_set<std::string> used;

    for (const auto& logical : logical_names) {
        FieldNamePlan p;
        p.logical_name = logical;

        const std::string base = normalize_descriptor_base(logical);
        p.sanitized = (base != logical);
        p.truncated = (base.size() > DBF_DESCRIPTOR_TOKEN_BYTES);

        std::string token = first_n(base, DBF_DESCRIPTOR_TOKEN_BYTES);
        std::string key = descriptor_key(token);

        if (used.find(key) != used.end()) {
            p.mangled = true;

            bool found = false;
            for (std::uint64_t n = 1; n <= 999999; ++n) {
                token = make_mangled_token(base, n);
                key = descriptor_key(token);
                if (used.find(key) == used.end()) {
                    found = true;
                    break;
                }
            }

            if (!found) {
                token = make_hash_token(base);
                key = descriptor_key(token);
            }
        }

        used.insert(key);
        p.descriptor_name = token;
        plans.push_back(std::move(p));
    }

    return plans;
}

// Strict classic/free-table policy:
// - descriptor token is the real exported field name.
// - collisions are destructive, so callers should fail by default.
inline std::vector<FieldNamePlan> plan_classic_strict(const std::vector<std::string>& logical_names)
{
    std::vector<FieldNamePlan> plans;
    plans.reserve(logical_names.size());

    for (const auto& logical : logical_names) {
        FieldNamePlan p;
        p.logical_name = logical;
        const std::string base = normalize_descriptor_base(logical);
        p.sanitized = (base != logical);
        p.truncated = (base.size() > DBF_DESCRIPTOR_TOKEN_BYTES);
        p.descriptor_name = first_n(base, DBF_DESCRIPTOR_TOKEN_BYTES);
        plans.push_back(std::move(p));
    }

    return plans;
}

} // namespace xbase::field_name_policy
