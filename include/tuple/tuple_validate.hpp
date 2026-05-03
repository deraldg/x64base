#pragma once

#include <string>
#include <vector>

#include "dt/data/row.hpp"
#include "tuple_types.hpp"
#include "xbase.hpp"

namespace dottalk::tupleaugment {

struct TupleValidationIssue {
    int area_slot = -1;
    int recno = 0;
    std::string table;
    std::string field;
    int field_index = -1;
    std::string raw;
    std::string message;
};

struct TupleValidationResult {
    std::size_t rows_checked = 0;
    std::size_t cells_checked = 0;
    std::vector<TupleValidationIssue> issues;

    [[nodiscard]] bool ok() const noexcept { return issues.empty(); }
};

TupleValidationResult validate_tuple_row(
    const dottalk::TupleRow& tuple,
    const xbase::DbArea* fallback_area = nullptr
);

} // namespace dottalk::tupleaugment
