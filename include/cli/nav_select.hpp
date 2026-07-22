// ============================================================
// nav_select.hpp
//
// Target path:
//   include/cli/nav_select.hpp
//
// Purpose:
//   Shared cursor-selection helper used by SKIP / GO-style
//   navigation to choose the next record number from either the
//   active logical/filter view or the active physical/index order.
//
// Fix in this version:
//   Prevent ordered SKIP boundary leakage.
//
//   Previous behavior:
//     order_skip(A, +1/-1) || A.skip(+1/-1)
//
//   That allowed TOP + SKIP -1 and BOTTOM + SKIP +1 under an
//   active CDX/LMDB order to fall through into physical record
//   movement. The cursor could leave the ordered boundary and move
//   to a neighboring physical record.
//
//   Correct behavior:
//     When an order is active, order_skip() owns traversal and a
//     failed ordered move means boundary/no movement. Do not fall
//     back to physical A.skip().
//
// Notes:
//   - This is a surgical navigation fix.
//   - No command names, public syntax, or index attach behavior are
//     changed here.
//   - Existing physical-order behavior remains routed through
//     order_skip(), which already handles the no-active-order case.
// ============================================================
#pragma once

#include <cstdint>

#include "xbase.hpp"
#include "cli/logical_nav.hpp"
#include "cli/order_nav.hpp"
#include "filters/filter_registry.hpp"

namespace cli::navsel {

enum class Mode {
    RawOrder,
    LogicalView,
    AutoByFilter
};

enum class Step {
    First,
    Last,
    Next,
    Prior
};

inline Mode resolve_mode(xbase::DbArea& A, Mode mode)
{
    if (mode == Mode::AutoByFilter) {
        return filter::has_active_filter(&A) ? Mode::LogicalView
                                             : Mode::RawOrder;
    }
    return mode;
}

inline std::int64_t pick_recno(xbase::DbArea& A,
                          Mode mode,
                          Step step,
                          std::int64_t from_recno = 0)
{
    if (!A.isOpen()) return 0;

    mode = resolve_mode(A, mode);

    switch (mode) {
    case Mode::LogicalView:
        // RECNO64 M5: pick_recno now returns 64-bit; logical_nav is already 64-bit.
        switch (step) {
        case Step::First:
            return static_cast<std::int64_t>(cli::logical_nav::first_recno(A));
        case Step::Last:
            return static_cast<std::int64_t>(cli::logical_nav::last_recno(A));
        case Step::Next:
            return static_cast<std::int64_t>(cli::logical_nav::next_recno(
                A, from_recno > 0 ? static_cast<std::uint64_t>(from_recno)
                                  : A.recno64()));
        case Step::Prior:
            return static_cast<std::int64_t>(cli::logical_nav::prev_recno(
                A, from_recno > 0 ? static_cast<std::uint64_t>(from_recno)
                                  : A.recno64()));
        }
        break;

    case Mode::RawOrder:
        {
            std::int64_t rn = 0;

            switch (step) {
            case Step::First:
                if (order_first_recno(A, rn)) return rn;
                return (A.recCount64() > 0 ? 1 : 0);

            case Step::Last:
                if (order_last_recno(A, rn)) return rn;
                return (A.recCount64() > 0 ? static_cast<std::int64_t>(A.recCount64()) : 0);

            case Step::Next:
            {
                const std::int64_t save = static_cast<std::int64_t>(A.recno64());
                const std::int64_t start = (from_recno > 0 ? from_recno : save);

                if (start <= 0) return 0;
                if (start != save) {
                    if (!A.gotoRec64(static_cast<std::uint64_t>(start)) || !A.readCurrent()) return 0;
                }

                const bool ok = order_skip(A, +1);
                rn = ok ? static_cast<std::int64_t>(A.recno64()) : 0;

                if (save > 0) {
                    (void)A.gotoRec64(static_cast<std::uint64_t>(save));
                    (void)A.readCurrent();
                }
                return rn;
            }

            case Step::Prior:
            {
                const std::int64_t save = static_cast<std::int64_t>(A.recno64());
                const std::int64_t start = (from_recno > 0 ? from_recno : save);

                if (start <= 0) return 0;
                if (start != save) {
                    if (!A.gotoRec64(static_cast<std::uint64_t>(start)) || !A.readCurrent()) return 0;
                }

                const bool ok = order_skip(A, -1);
                rn = ok ? static_cast<std::int64_t>(A.recno64()) : 0;

                if (save > 0) {
                    (void)A.gotoRec64(static_cast<std::uint64_t>(save));
                    (void)A.readCurrent();
                }
                return rn;
            }
            }

        }
        break;

    case Mode::AutoByFilter:
        break;
    }

    return 0;
}

} // namespace cli::navsel
