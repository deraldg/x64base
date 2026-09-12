// @dottalk.file v1
// subsystem: xindex
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported


// cli_bridge.cpp  (updated)
#include "cli/order_state.hpp"
#include "cli/cli_bridge.hpp"

namespace xindex_cli {

bool db_index_attached(const xbase::DbArea& A) {
    return orderstate::hasOrder(A);
}

std::string db_index_path(const xbase::DbArea& A) {
    return orderstate::orderName(A);
}

std::string db_active_cnx_tag(const xbase::DbArea& A) {
    if (!orderstate::isCnx(A)) return std::string();
    return orderstate::activeTag(A);
}

bool db_order_asc(const xbase::DbArea& A) {
    return orderstate::isAscending(A);
}

// AIF-148.  Deliberately NOT !db_index_attached(): an attached tag container
// with no tag selected is natural order, and that is precisely the case the
// attachment predicate cannot see.
bool db_order_is_natural(const xbase::DbArea& A) {
    return orderstate::isNaturalOrder(A);
}

} // namespace xindex_cli

namespace xindex_cli_internal {
void set_active(const xbase::DbArea& /*A*/, const std::string& /*key*/) {
    // no-op for now
}
} // namespace xindex_cli_internal



