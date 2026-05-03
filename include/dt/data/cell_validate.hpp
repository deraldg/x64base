#pragma once

#include <cstddef>
#include <string>

#include "dt/data/cell.hpp"
#include "dt/data/row.hpp"

namespace dt::data {

struct RowErrorSummary {
    bool        ok              { true };
    std::size_t invalid_cells   { 0 };
    std::string first_error;
};

bool validate_cell(Cell& cell, std::string* error_out = nullptr);
bool validate_row(Row& row, RowErrorSummary& summary);
RowErrorSummary summarize_row_errors(const Row& row);

} // namespace dt::data
