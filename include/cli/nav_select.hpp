// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// ============================================================
// nav_select.hpp
//
// Target path:
//   include/cli/nav_select.hpp
//
// Purpose:
//   Shared cursor-selection helper used by SKIP / TOP / BOTTOM to
//   choose the next record number from either the active logical
//   view or the active physical/index order.
//
//   NOT GO. R121 (2026-08-24) draws the line this file sits on:
//   ADDRESSING IS ABSOLUTE, TRAVERSAL IS FILTERED. GO names a
//   record and must land on it; SKIP/TOP/BOTTOM name a position in
//   a set and must walk the visible one. cmd_goto.cpp deliberately
//   does not include this header and must not start.
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
    // RENAMED FROM AutoByFilter BY R121. The old name was accurate about what
    // the code did and wrong about what the code is for: it chose the logical
    // view by asking whether a SET FILTER was active, which is only one of the
    // two things that make the visible set differ from the raw order. Fixing
    // the predicate without fixing the name would have left a label describing
    // the bug.
    AutoByVisibility
};

enum class Step {
    First,
    Last,
    Next,
    Prior
};

inline Mode resolve_mode(xbase::DbArea& A, Mode mode)
{
    if (mode == Mode::AutoByVisibility) {
        // R121: ONE QUESTION, ASKED ONCE, IN THE PLACE THAT OWNS IT.
        // Was `filter::has_active_filter(&A)`, which silently meant "SET
        // DELETED is not a reason to filter" -- and everything downstream of
        // Mode::LogicalView already honoured SET DELETED, so the setting was
        // wired end to end except for the branch that decides to use it.
        return filter::view_is_filtered(&A) ? Mode::LogicalView
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

    case Mode::AutoByVisibility:
        break;
    }

    return 0;
}

} // namespace cli::navsel
