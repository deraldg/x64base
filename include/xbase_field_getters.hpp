// @dottalk.file v1
// subsystem: include
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <cctype>
#include <cstdint>
#include <functional>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include "xbase.hpp"
#include "textio.hpp"
#include "xbase/field_name_policy.hpp"

// Tiny namespace to avoid collisions with local helpers.
namespace xfg {

// -----------------------------------------------------------------------------
// Basic helpers
// -----------------------------------------------------------------------------
inline std::string rtrim_copy(std::string s) {
    while (!s.empty() &&
           std::isspace(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

inline std::string ltrim_copy(std::string s) {
    std::size_t i = 0;
    while (i < s.size() &&
           std::isspace(static_cast<unsigned char>(s[i]))) {
        ++i;
    }
    if (i) s.erase(0, i);
    return s;
}

inline std::string trim_copy(std::string s) {
    return rtrim_copy(ltrim_copy(std::move(s)));
}

inline char up_char(char c) noexcept {
    return static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
}

inline std::string up_copy(std::string s) {
    for (char& c : s) c = up_char(c);
    return s;
}

// -----------------------------------------------------------------------------
// Type helpers
//
// These helpers classify field kinds for retrieval/display purposes.
// They do not imply that full binary decoding is implemented yet.
// -----------------------------------------------------------------------------
inline bool is_textual_type(char t) noexcept {
    switch (up_char(t)) {
    case 'C':   // Character
    case 'V':   // VFP VarChar
        return true;
    case 'M':   // Memo field: DBF slot currently holds a token/reference
        return true;
    default:
        return false;
    }
}

inline bool is_numeric_ascii_type(char t) noexcept {
    switch (up_char(t)) {
    case 'N':   // Numeric (ASCII in row)
    case 'F':   // Float   (ASCII in row)
        return true;
    default:
        return false;
    }
}

inline bool is_binary_numeric_type(char t) noexcept {
    switch (up_char(t)) {
    case 'I':   // VFP Integer
    case 'Y':   // VFP Currency
    case 'B':   // VFP Double
        return true;
    default:
        return false;
    }
}

inline bool is_date_type(char t) noexcept {
    return up_char(t) == 'D';
}

inline bool is_datetime_type(char t) noexcept {
    return up_char(t) == 'T';
}

inline bool is_logical_type(char t) noexcept {
    return up_char(t) == 'L';
}

inline bool is_memo_type(char t) noexcept {
    return up_char(t) == 'M';
}

// -----------------------------------------------------------------------------
// Field resolution
//
// Resolution policy:
//   1. Authoritative/logical field names always win.
//   2. For x64 tables only, if no authoritative match is found, allow the
//      generated DBF/VFP descriptor fallback token as a compatibility alias.
//      This mirrors the write-time policy used by CREATE X64 and
//      COPY AS X64 VECTOR.
//   3. Fallback aliases are accepted only when they map uniquely.
//
// CORRECTED 2026-09-06: RULE 3 NAMES THE WRONG COMPONENT. Read as written it
// says THIS FUNCTION decides uniqueness. It does not. xbase::field_name_policy::
// plan_x64_unique_fallback decides it, at WRITE time, by inserting
// descriptor_key(token) into a `used` set and re-mangling until the key is free
// -- which is why CREATE X64 announces "token was mangled to avoid a fallback
// collision". Tokens are therefore DISTINCT BY CONSTRUCTION before this
// function ever sees one.
//
// SO THE `ambiguous` CHECK BELOW CANNOT FIRE, and that is worth stating rather
// than leaving for someone to rediscover as a bug. For a GENERATED token
// field_name_core_ and descriptor_key agree exactly: a token leaves
// normalize_descriptor_base as [A-Z0-9_] plus a possible '~', so there is never
// whitespace to trim and never a NUL to truncate. At most one plan can match.
//
// IT IS KEPT ANYWAY AND IS NOT DEAD WEIGHT. It is the only thing standing if a
// future planner stops guaranteeing uniqueness, and it fails CLOSED -- -1, no
// match -- rather than silently picking the first of two. A guard that cannot
// fire under today's caller is different from a guard that is wrong; this one
// is cheap, correct, and one edit away from being load-bearing.
//
// PROVEN BY: the TAGFIELD spec (index_field_name_resolution.dts, section 3)
// covers rules 1 and 2 against a real collision -- STUDENT_LAST_NAME takes the
// plain token STUDENT_LA, STUDENT_LABEL and STUDENT_LA are mangled to
// STUDENT_~1 and STUDENT_~2, and `STUDENT_LA` as a tag must resolve to the
// FIELD OF THAT NAME, not to the field holding it as a token. Rule 3 is the one
// arm no fixture can reach, for the reason above.
//
// This keeps x64 metadata names canonical while making non-destructive
// 10-byte descriptor tokens useful as aliases.
// -----------------------------------------------------------------------------
// AIF-157: truncate a stored field name at the first NUL before comparing.
//
// The DBF field descriptor carries an 11-byte NUL-padded name, so a stored name
// can arrive as "SID\0\0\0\0" depending on the reader. trim_copy only strips
// isspace, and NUL is not isspace, so an untruncated name never equals its own
// trimmed spelling.
//
// This is not a new opinion -- it is the ONE capability the hand-rolled matchers
// in cdx_native_backend.cpp and cnx_backend.cpp had that this resolver lacked.
// Those two were retired onto this function, so absorbing their NUL handling
// here is what makes the consolidation lossless rather than a quiet downgrade.
// A name with no NUL is completely unaffected.
inline std::string field_name_core_(std::string s) {
    const auto nul = s.find('\0');
    if (nul != std::string::npos) s.resize(nul);
    return up_copy(trim_copy(std::move(s)));
}

inline int resolve_field_index_std(const xbase::DbArea& db, const std::string& nameIn) {
    const std::string want = field_name_core_(nameIn);
    const auto& F = db.fields();

    // 1. Authoritative/logical field names always win.
    for (int i = 0; i < static_cast<int>(F.size()); ++i) {
        if (field_name_core_(F[static_cast<std::size_t>(i)].name) == want) {
            return i;
        }
    }

    // 2. x64 descriptor fallback-token aliases.
    if (db.versionByte() == 0x64) {
        std::vector<std::string> logical_names;
        logical_names.reserve(F.size());

        for (const auto& fd : F) {
            logical_names.push_back(fd.name);
        }

        const auto plans =
            xbase::field_name_policy::plan_x64_unique_fallback(logical_names);

        int found = -1;
        bool ambiguous = false;

        for (int i = 0; i < static_cast<int>(plans.size()); ++i) {
            const std::string token =
                field_name_core_(plans[static_cast<std::size_t>(i)].descriptor_name);

            if (token == want) {
                if (found >= 0 && found != i) {
                    ambiguous = true;
                    break;
                }
                found = i;
            }
        }

        if (!ambiguous && found >= 0) {
            return found;
        }
    }

    return -1;
}

inline int resolve_field_index_std(xbase::DbArea& db, const std::string& nameIn) {
    return resolve_field_index_std(static_cast<const xbase::DbArea&>(db), nameIn);
}

inline char getFieldType(xbase::DbArea& db, const std::string& name) {
    const int idx0 = resolve_field_index_std(db, name);
    if (idx0 < 0) return '\0';
    const auto& F = db.fields();
    return (idx0 < static_cast<int>(F.size())) ? F[static_cast<std::size_t>(idx0)].type : '\0';
}

inline char getFieldType(const xbase::DbArea& db, const std::string& name) {
    const int idx0 = resolve_field_index_std(db, name);
    if (idx0 < 0) return '\0';
    const auto& F = db.fields();
    return (idx0 < static_cast<int>(F.size())) ? F[static_cast<std::size_t>(idx0)].type : '\0';
}

// -----------------------------------------------------------------------------
// Raw field access
//
// These functions return DBF slot contents only.
// For M fields, that means the raw memo token/reference stored in the row,
// not the resolved memo payload.
// -----------------------------------------------------------------------------
inline std::string getFieldRawString(xbase::DbArea& db, const std::string& name) {
    const int idx0 = resolve_field_index_std(db, name);
    if (idx0 < 0) return std::string{};
    return db.get(idx0 + 1); // API is 1-based
}

inline std::string getFieldAsString(xbase::DbArea& db, const std::string& name) {
    return rtrim_copy(getFieldRawString(db, name));
}

// -----------------------------------------------------------------------------
// Memo-aware resolved getter hook
//
// The callback receives the raw DBF slot contents for an M field
// (typically a token/reference), and may return resolved memo text.
// If no resolver is provided, or resolution does not return a value,
// the raw slot contents are returned unchanged.
//
// This keeps the header backend-neutral: actual DTX/FPT retrieval belongs
// in the supplied resolver, not in this header.
// -----------------------------------------------------------------------------
using MemoResolver = std::function<std::optional<std::string>(xbase::DbArea&, const std::string& rawToken)>;

inline std::string getFieldAsResolvedString(xbase::DbArea& db,
                                            const std::string& name,
                                            const MemoResolver& memoResolver = {}) {
    const int idx0 = resolve_field_index_std(db, name);
    if (idx0 < 0) return std::string{};

    const auto& F = db.fields();
    if (idx0 >= static_cast<int>(F.size())) return std::string{};

    const char t = up_char(F[static_cast<std::size_t>(idx0)].type);
    std::string raw = rtrim_copy(db.get(idx0 + 1));

    if (t == 'M' && memoResolver) {
        if (auto resolved = memoResolver(db, raw)) {
            return *resolved;
        }
    }

    return raw;
}

// -----------------------------------------------------------------------------
// Numeric access
//
// Current practical stance:
//   - N/F are parsed from ASCII storage now.
//   - I/Y/B are recognized as VFP binary numeric families.
//   - Until DbArea::get() or lower-level row decoding becomes binary-aware for
//     those types, this helper still parses whatever string representation
//     DbArea::get() returns.
//
// This makes the helper safe to use now without overstating binary VFP support.
// -----------------------------------------------------------------------------
inline double parse_trimmed_double(std::string s) {
    s = trim_copy(std::move(s));
    if (s.empty()) throw std::runtime_error("empty numeric");
    std::size_t pos = 0;
    const double v = std::stod(s, &pos);
    if (pos != s.size()) throw std::runtime_error("trailing numeric data");
    return v;
}

inline double getFieldAsNumber(xbase::DbArea& db, const std::string& name) {
    const int idx0 = resolve_field_index_std(db, name);
    if (idx0 < 0) throw std::runtime_error("field not found");

    const auto& F = db.fields();
    if (idx0 >= static_cast<int>(F.size())) throw std::runtime_error("field index out of range");

    const char t = up_char(F[static_cast<std::size_t>(idx0)].type);
    const std::string raw = getFieldRawString(db, name);

    if (is_numeric_ascii_type(t) || is_binary_numeric_type(t)) {
        return parse_trimmed_double(raw);
    }

    throw std::runtime_error("field is not numeric");
}

inline std::optional<double> tryGetFieldAsNumber(xbase::DbArea& db, const std::string& name) {
    try {
        return getFieldAsNumber(db, name);
    } catch (...) {
        return std::nullopt;
    }
}

// -----------------------------------------------------------------------------
// Integer-oriented convenience
// -----------------------------------------------------------------------------
inline std::optional<std::int64_t> tryGetFieldAsInt64(xbase::DbArea& db, const std::string& name) {
    try {
        std::string s = trim_copy(getFieldRawString(db, name));
        if (s.empty()) return std::nullopt;

        std::size_t pos = 0;
        const long long v = std::stoll(s, &pos, 10);
        if (pos != s.size()) return std::nullopt;

        return static_cast<std::int64_t>(v);
    } catch (...) {
        return std::nullopt;
    }
}

// -----------------------------------------------------------------------------
// Logical access
// -----------------------------------------------------------------------------
inline std::optional<bool> tryGetFieldAsBool(xbase::DbArea& db, const std::string& name) {
    const int idx0 = resolve_field_index_std(db, name);
    if (idx0 < 0) return std::nullopt;

    const auto& F = db.fields();
    if (idx0 >= static_cast<int>(F.size())) return std::nullopt;
    if (!is_logical_type(F[static_cast<std::size_t>(idx0)].type)) return std::nullopt;

    std::string s = trim_copy(getFieldRawString(db, name));
    if (s.empty()) return std::nullopt;

    const char c = up_char(s.front());
    if (c == 'T' || c == 'Y') return true;
    if (c == 'F' || c == 'N') return false;
    return std::nullopt;
}

// -----------------------------------------------------------------------------
// Date / datetime access
//
// These remain string-oriented for now.
// For 'T' fields, this returns the raw string representation currently exposed
// by DbArea::get(); it is not yet a full native VFP datetime decoder.
// -----------------------------------------------------------------------------
inline std::string getFieldAsDateString(xbase::DbArea& db, const std::string& name) {
    const int idx0 = resolve_field_index_std(db, name);
    if (idx0 < 0) return std::string{};

    const auto& F = db.fields();
    if (idx0 >= static_cast<int>(F.size())) return std::string{};

    const char t = up_char(F[static_cast<std::size_t>(idx0)].type);
    if (!(t == 'D' || t == 'T')) return std::string{};

    return rtrim_copy(getFieldRawString(db, name));
}

// -----------------------------------------------------------------------------
// Generic display helper
//
// For memo fields:
//   - returns resolved memo text if a resolver is supplied and succeeds
//   - otherwise returns the raw token/reference stored in the DBF slot
//
// For non-memo fields:
//   - returns trimmed display text
// -----------------------------------------------------------------------------
inline std::string getFieldForDisplay(xbase::DbArea& db,
                                      const std::string& name,
                                      const MemoResolver& memoResolver = {}) {
    const int idx0 = resolve_field_index_std(db, name);
    if (idx0 < 0) return std::string{};

    const auto& F = db.fields();
    if (idx0 >= static_cast<int>(F.size())) return std::string{};

    if (is_memo_type(F[static_cast<std::size_t>(idx0)].type)) {
        return getFieldAsResolvedString(db, name, memoResolver);
    }

    return getFieldAsString(db, name);
}

} // namespace xfg
