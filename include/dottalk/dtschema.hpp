// @dottalk.file v1
// subsystem: dottalk
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

#pragma once

#include <cctype>
#include <cstddef>
#include <string_view>

// AIF-120. DTSHEMA writes the literal word "none" to mean "this AREA line has
// no index" or "no active tag". The sentinel is the format, not a typo:
// src/cli/cmd_workspace.cpp:1569-1575 substitutes it whenever the underlying
// value is empty --
//
//     << " | index="     << (idxOut.empty() ? "none" : idxOut)
//     << " | indextype=" << (indexType.empty() ? "NONE" : indexType)
//     << " | tag="       << (tag.empty() ? "none" : tag);
//
// -- so a reader that tests only for emptiness accepts "none" as data. That is
// what made a tool-written schema ask the CDX backend for a tag literally named
// NONE, which it correctly refused (src/xindex/cdx_backend.cpp:592).
//
// Note the case is NOT uniform: `indextype` is written uppercase NONE while
// `index` and `tag` are written lowercase none. Compare case-insensitively or
// you will fix half of it.
//
// This predicate lives in a shared header rather than beside either reader
// because the format has two independent parsers -- the CLI in
// src/cli/cmd_workspace.cpp and the GUI in src/gui/core/session.cpp
// (load_dtschema2_areas). The CLI already honors the sentinel in six places,
// two of them purpose-built helpers (setActiveTagSafe, infer_index_type_from_path).
// Retire those onto this predicate rather than adding a seventh copy.

namespace dottalk::dtschema {

// True when a DTSHEMA field carries no value: empty, whitespace-only, or the
// writer's "none" sentinel in any casing.
//
// There is deliberately NO std::filesystem::path overload. path converts
// implicitly to its native string_type, which is std::string on POSIX and
// std::wstring on Windows, so a path overload would either be ambiguous with
// this one or silently change behaviour between platforms. Callers holding a
// path pass value.string() and the asymmetry stays visible at the call site.
inline bool is_absent(std::string_view value) noexcept {
    auto is_space = [](char c) noexcept {
        return std::isspace(static_cast<unsigned char>(c)) != 0;
    };

    std::size_t begin = 0;
    std::size_t end = value.size();
    while (begin < end && is_space(value[begin])) {
        ++begin;
    }
    while (end > begin && is_space(value[end - 1])) {
        --end;
    }

    const std::string_view trimmed = value.substr(begin, end - begin);
    if (trimmed.empty()) {
        return true;
    }

    constexpr std::string_view kNone = "none";
    if (trimmed.size() != kNone.size()) {
        return false;
    }
    for (std::size_t i = 0; i < kNone.size(); ++i) {
        if (std::tolower(static_cast<unsigned char>(trimmed[i])) != kNone[i]) {
            return false;
        }
    }
    return true;
}

} // namespace dottalk::dtschema
