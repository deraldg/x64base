#include "smartlist_query.hpp"

#include "predicates.hpp"
#include "filters/filter_registry.hpp"
#include "../xbase/cursor_hook.hpp"

#include <cstdint>

namespace cli::smartlist {

bool pass_deleted_filter(const xbase::DbArea& a, DelFilter del, bool all) {
    const bool isDel = a.isDeleted();
    switch (del) {
        case DelFilter::OnlyDeleted: return isDel;
        case DelFilter::OnlyAlive:   return !isDel;
        case DelFilter::Any:
        default:                     return all ? true : !isDel;
    }
}

bool pass_all_filters(xbase::DbArea& a, const QuerySpec& spec) {
    if (!pass_deleted_filter(a, spec.del, spec.all)) return false;

    if (!filter::visible(&a, spec.expr_prog)) return false;

    if (spec.haveFieldFilter &&
        !predicates::eval(a, spec.fld, spec.op, spec.val)) {
        return false;
    }

    return true;
}

QueryStats execute_query(
    xbase::DbArea& a,
    const QuerySpec& spec,
    const RecordConsumer& consumer)
{
    QueryStats stats{};
    const int32_t total = a.recCount();

    auto process_record = [&](int32_t rn) -> bool {
        if (!a.gotoRec(rn) || !a.readCurrent()) return false;
        if (!pass_all_filters(a, spec)) return true;

        if (!consumer(a, rn, stats.printed)) return false;

        ++stats.printed;
        if (!spec.all && spec.limit > 0 && stats.printed >= spec.limit) {
            return false;
        }
        return true;
    };

    // Explicit DELETED output must use a physical scan.
    // Ordered/index-backed iteration usually omits deleted rows, so running
    // OnlyDeleted through an active order returns a false zero-row result.
    const bool force_physical_for_deleted = (spec.del == DelFilter::OnlyDeleted);

    if (!force_physical_for_deleted) {
        xbase::cursor_hook::Guard suppress_cursor;

        const bool iter_ok = cli::order_iterate_recnos(
            a,
            [&](uint64_t rn64) -> bool {
                if (rn64 == 0 || rn64 > static_cast<uint64_t>(a.recCount64())) return true;
                return process_record(static_cast<int32_t>(rn64));
            },
            &stats.iter_spec,
            &stats.iter_err);

        if (iter_ok) {
            stats.iter_used = true;
            return stats;
        }
    }

    {
        xbase::cursor_hook::Guard suppress_cursor;
        for (int32_t rn = 1; rn <= total; ++rn) {
            if (!process_record(rn)) break;
        }
    }

    return stats;
    }
} // namespace cli::smartlist
