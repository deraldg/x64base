#pragma once
#include <string>
#include <vector>

namespace dottalk {

struct TupleDeltaField {
    int area0 = -1;        // owning work area
    int recno = 0;         // record number
    int field1 = 0;        // 1-based field index (preferred)
    std::string table;     // fallback / debug
    std::string field;     // fallback / debug
    std::string old_value; // optional (for rollback/validation)
    std::string new_value; // staged value
};

struct TupleDelta {
    std::vector<TupleDeltaField> fields;

    bool empty() const { return fields.empty(); }

    bool valid() const {
        for (const auto& f : fields) {
            if (f.area0 < 0 || f.recno <= 0) return false;
            if (f.field1 <= 0 && f.field.empty()) return false;
        }
        return true;
    }
};

} // namespace dottalk