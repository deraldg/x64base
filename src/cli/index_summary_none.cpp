#include "cli/index_summary.hpp"
#include "xbase.hpp"

namespace dottalk {

IndexSummary summarize_index(xbase::DbArea& area)
{
    IndexSummary summary;
    summary.kind = IndexSummary::OrderKind::Physical;
    summary.record_count = area.recCount();
    return summary;
}

} // namespace dottalk
