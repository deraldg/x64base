#include "datadict/ddict_object_resolver.hpp"
#include "datadict/ddict_read_helpers.hpp"

// DD-089C extraction preview only.
// This generated candidate is not installed or wired by DD-089C.

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
