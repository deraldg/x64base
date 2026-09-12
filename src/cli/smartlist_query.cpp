// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

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
        default:
            // AIF-123. `all` IS THE ROW-LIMIT FLAG. It means "no 20-row cap"
            // (QuerySpec::limit), and it was ALSO deciding deleted visibility --
            // one flag answering two questions, so `LIST ALL` typed to see past
            // twenty rows silently turned deleted rows on as well, and SET
            // DELETED appeared nowhere in the decision.
            //
            // With no explicit clause the answer now comes from the session
            // setting, applied once in filter::visible(). Returning true here is
            // not "show everything" -- it is "no clause in force, the gate
            // decides", which is what DelFilter::Any has always meant.
            (void)all;
            return true;
    }
}

bool pass_all_filters(xbase::DbArea& a, const QuerySpec& spec) {
    if (!pass_deleted_filter(a, spec.del, spec.all)) return false;

    // An explicit OnlyDeleted / OnlyAlive clause has already spoken above, and
    // in xBase a clause beats the session default -- so the gate must not then
    // filter those rows back out. Any means no clause: let it apply SET DELETED.
    const auto policy = (spec.del == DelFilter::Any)
                            ? filter::DeletedPolicy::SessionDefault
                            : filter::DeletedPolicy::CallerHandles;
    if (!filter::visible(&a, spec.expr_prog, policy)) return false;

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
