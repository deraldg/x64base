#include "tuple/tuple_validate.hpp"

#include "tuple/tuple_cell_adapter.hpp"

namespace dottalk::tupleaugment {

TupleValidationResult validate_tuple_row(
    const dottalk::TupleRow& tuple,
    const xbase::DbArea* fallback_area
) {
    TupleValidationResult out;
    out.rows_checked = 1;

    TupleCellAdapterOptions opt;
    opt.validate_cells = true;

    auto conv = cells_from_tuple_row(tuple, fallback_area, opt);
    if (!conv.ok) {
        TupleValidationIssue issue;
        issue.message = conv.error;
        out.issues.push_back(std::move(issue));
        return out;
    }

    out.cells_checked = conv.row.cells.size();

    for (const auto& cell : conv.row.cells) {
        if (cell.valid) continue;

        TupleValidationIssue issue;
        issue.area_slot = cell.area_slot;
        issue.recno = cell.recno;
        issue.table = cell.table_name;
        issue.field = cell.field_name;
        issue.field_index = cell.field_index;
        issue.raw = cell.raw;
        issue.message = cell.error;
        out.issues.push_back(std::move(issue));
    }

    return out;
}

} // namespace dottalk::tupleaugment
