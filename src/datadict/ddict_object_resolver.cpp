// @dottalk.file v1
// subsystem: datadict
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "datadict/ddict_object_resolver.hpp"
#include "datadict/ddict_read_helpers.hpp"

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

const DDictRow* resolve_object(const std::vector<DDictRow>& objects, const std::string& token) {
    std::string want = upper_copy(token);
    for (const auto& row : objects) {
        if (upper_copy(value_of(row, "OBJID")) == want) {
            return &row;
        }
    }
    for (const auto& row : objects) {
        if (upper_copy(value_of(row, "OBJTYPE")) == "CATALOG_TABLE" &&
            upper_copy(value_of(row, "NAME")) == want) {
            return &row;
        }
    }
    for (const auto& row : objects) {
        if (upper_copy(value_of(row, "NAME")) == want) {
            return &row;
        }
    }
    for (const auto& row : objects) {
        if (upper_copy(value_of(row, "OWNER")) == want) {
            return &row;
        }
    }
    return nullptr;
}

std::unordered_map<std::string, const DDictRow*> object_index(const std::vector<DDictRow>& objects) {
    std::unordered_map<std::string, const DDictRow*> by_id;
    for (const auto& row : objects) {
        std::string objid = value_of(row, "OBJID");
        if (!objid.empty()) {
            by_id[objid] = &row;
        }
    }
    return by_id;
}

} // namespace dottalk::datadict
