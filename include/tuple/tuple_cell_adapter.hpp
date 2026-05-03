#pragma once

#include <string>

#include "dt/data/row.hpp"
#include "tuple_types.hpp"
#include "xbase.hpp"

namespace dottalk::tupleaugment {

struct TupleCellAdapterOptions {
    bool validate_cells = true;
};

struct TupleCellAdapterResult {
    bool ok = true;
    std::string error;
    dt::data::Row row;
};

// Convert a TupleRow into typed cells using resolved runtime field metadata.
// This does not open files, read raw DBF bytes, or inspect x64 metadata.
// It consumes the tuple layer and DbArea/FieldDef runtime truth only.
TupleCellAdapterResult cells_from_tuple_row(
    const dottalk::TupleRow& tuple,
    const xbase::DbArea* fallback_area = nullptr,
    const TupleCellAdapterOptions& options = {}
);

} // namespace dottalk::tupleaugment
