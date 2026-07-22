// src/cli/logical_nav.cpp
//
// Logical navigation helpers:
//   raw order stream
//     + active order direction
//     + SET FILTER visibility
//   => logical visible record stream
//
// This layer is intentionally above order_iterator/order_nav.
// It does not change backend order semantics; it only filters them
// into the user-visible logical view.

#include "cli/logical_nav.hpp"

#include <algorithm>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "cli/order_iterator.hpp"
#include "filters/filter_registry.hpp"

namespace cli::logical_nav {
namespace {

struct CursorRestore {
    xbase::DbArea& area;
    std::uint64_t saved{0};
    bool had_open{false};

    explicit CursorRestore(xbase::DbArea& a)
        : area(a), saved(a.isOpen() ? a.recno64() : 0), had_open(a.isOpen()) {}

    ~CursorRestore() {
        if (!had_open) return;
        if (saved > 0) {
            (void)area.gotoRec64(saved);
            (void)area.readCurrent();
        }
    }
};

} // namespace

bool is_visible(xbase::DbArea& area, std::uint64_t recno)
{
    if (!area.isOpen() || recno == 0 || recno > area.recCount64()) {
        return false;
    }

    CursorRestore restore(area);

    if (!area.gotoRec64(recno) || !area.readCurrent()) {
        return false;
    }

    // Canonical logical visibility gate already used by LIST/COUNT/SMARTLIST/LOCATE.
    return filter::visible(&area, std::shared_ptr<dottalk::expr::Expr>{});
}

std::uint64_t first_recno(xbase::DbArea& area)
{
    if (!area.isOpen()) return 0;

    // Stream the display order and stop at the first visible record.
    std::uint64_t found = 0;
    cli::order_stream_display(area, /*reverse=*/false,
        [&](uint64_t rn) -> bool {
            if (is_visible(area, rn)) { found = rn; return false; }
            return true;
        });
    return found;
}

std::uint64_t last_recno(xbase::DbArea& area)
{
    if (!area.isOpen()) return 0;

    // Stream in reverse display order and stop at the first visible record,
    // which is the last visible record in display order.
    std::uint64_t found = 0;
    cli::order_stream_display(area, /*reverse=*/true,
        [&](uint64_t rn) -> bool {
            if (is_visible(area, rn)) { found = rn; return false; }
            return true;
        });
    return found;
}

std::uint64_t next_recno(xbase::DbArea& area, std::uint64_t from_recno)
{
    if (!area.isOpen()) return 0;
    if (from_recno == 0) return first_recno(area);

    // Stream forward, skip until we pass from_recno, then return the next
    // visible record. Stops as soon as it is found.
    bool seen = false;
    std::uint64_t found = 0;
    cli::order_stream_display(area, /*reverse=*/false,
        [&](uint64_t rn) -> bool {
            if (!seen) {
                if (rn == from_recno) seen = true;
                return true;
            }
            if (is_visible(area, rn)) { found = rn; return false; }
            return true;
        });
    return found;
}

std::uint64_t prev_recno(xbase::DbArea& area, std::uint64_t from_recno)
{
    if (!area.isOpen()) return 0;
    if (from_recno == 0) return last_recno(area);

    // Stream in reverse display order, skip until we pass from_recno, then
    // return the next visible record (the previous record in display order).
    bool seen = false;
    std::uint64_t found = 0;
    cli::order_stream_display(area, /*reverse=*/true,
        [&](uint64_t rn) -> bool {
            if (!seen) {
                if (rn == from_recno) seen = true;
                return true;
            }
            if (is_visible(area, rn)) { found = rn; return false; }
            return true;
        });
    return found;
}

} // namespace cli::logical_nav
