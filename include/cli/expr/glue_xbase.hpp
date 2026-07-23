
// include/cli/expr/glue_xbase.hpp
#pragma once
#include <optional>
#include <string>
#include <string_view>
#include "cli/expr/ast.hpp"   // RecordView
#include "xbase.hpp"

namespace dottalk { namespace expr { namespace glue {

// Create a RecordView over the current record of an xbase::DbArea.
// Numeric accessor coerces DBF fields using standard normalization:
//   - N: thousands/decimals allowed (e.g., "1,234.50" -> 1234.50)
//   - D: YYYYMMDD as number (e.g., "20250131" -> 20250131)
//   - L: T/.T./Y/1 => 1.0, F/.F./N/0 => 0.0
//   - C/M: returns nullopt for numeric accessor
RecordView make_record_view(xbase::DbArea& area);

// Selective-decode variant (scan-evaluator lane M2). Same accessor semantics,
// but decodes each field on demand from the current record buffer instead of
// the eager per-field _fd cache. Use with DbArea::readCurrentRaw() so a scan
// decodes only the fields the predicate reads (N/F numerics with no alloc).
RecordView make_record_view_raw(xbase::DbArea& area);

}}} // namespace dottalk::expr::glue




