// @dottalk.file v1
// subsystem: datadict
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "datadict/ddict_read_helpers.hpp"

#include <algorithm>
#include <cctype>

// DD-089C extraction provenance. This file was extracted from
// src/cli/cmd_ddict.cpp by DD-089C.
//
// CORRECTED 2026-08-24. This banner used to read "extraction preview only /
// This generated candidate is not installed or wired by DD-089C" -- and that
// stopped being true when the file was wired, which nothing updated. It is
// COMPILED THREE SEPARATE WAYS today:
//   1. src/CMakeLists.txt GLOB_RECURSE over src/**/*.cpp sweeps src/datadict/
//   2. the DD-089H block re-adds four of these files by name via target_sources
//   3. root CMakeLists.txt links ddict_read_helpers + ddict_dbf_reader into the
//      dt_meta static library that metacollect uses
//
// A reader trusting the old banner concluded this code was inert. A comment
// cannot go red, so it drifted silently from the day the wiring landed --
// the same shape as a severed setting whose default survives it.

namespace dottalk::datadict {

std::string lower_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return s;
}

std::string trim_copy(std::string s) {
    auto not_space = [](unsigned char ch) {
        return !std::isspace(ch) && ch != '\0';
    };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
}

std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) {
        return static_cast<char>(std::toupper(ch));
    });
    return s;
}

std::string short_text(const std::string& s, std::size_t n) {
    return s.size() <= n ? s : s.substr(0, n);
}

std::string value_of(const DDictRow& row, const std::string& key) {
    auto it = row.find(key);
    return it == row.end() ? std::string{} : it->second;
}

} // namespace dottalk::datadict
