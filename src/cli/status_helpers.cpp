// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "status_helpers.hpp"
#include "cli/order_state.hpp"
#include <sstream>
#include <cctype>
#include <string>

namespace {
inline char upc(char c){ return static_cast<char>(std::toupper(static_cast<unsigned char>(c))); }
inline bool ends_with_3(const std::string& s, const char* ext3) {
    const size_t n = s.size();
    return n >= 4 && s[n-4]=='.' && upc(s[n-3])==ext3[0] && upc(s[n-2])==ext3[1] && upc(s[n-1])==ext3[2];
}
} // anon

namespace status {

std::string format_active_order(const xbase::DbArea& A) {
    std::ostringstream os;
    if (!orderstate::hasOrder(A)) {
        os << "Order       : PHYSICAL";
        return os.str();
    }

    // AIF-148 RESIDUE, 2026-08-29. hasOrder() above answers IS A CONTAINER
    // ATTACHED, which is the right question for "is there a container to
    // describe" and the WRONG one for "which order does the cursor follow". A
    // .cdx attached with NO TAG selected is a table sitting in NATURAL order,
    // and this line called it ASCEND -- a report that disagreed with the
    // navigation verbs operating on the same area. The gate stays on hasOrder
    // so the container filename and tag are still printed; only the ORDER WORD
    // moves to the predicate that answers the question being asked.
    const std::string idxName = orderstate::orderName(A);
    const bool asc = orderstate::isAscending(A);
    os << "Order       : " << (orderstate::isNaturalOrder(A)
                                   ? "PHYSICAL"
                                   : (asc ? "ASCEND" : "DESCEND"));

    if (!idxName.empty()) {
        os << "\n  Index file  : " << idxName;

        // Only CNX carries a tag concept here
        if (ends_with_3(idxName, "CNX")) {
            const std::string tag = orderstate::activeTag(A);
            os << "\n  Active tag  : " << (tag.empty() ? "(none)" : tag);
        } else {
            os << "\n  Active tag  : (none)";
        }
    } else {
        os << "\n  Index file  : (none)"
           << "\n  Active tag  : (none)";
    }

    return os.str();
}

} // namespace status



