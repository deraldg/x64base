#pragma once

#include <cstdint>

namespace xbase { class DbArea; }

namespace cli::logical_nav {

// True if the given record is visible in the current logical view
// (active order + SET FILTER + SET DELETED policy as enforced by filter::visible()).
// Record numbers are 64-bit (RECNO64 lane); 0 is the "no record" sentinel.
bool is_visible(xbase::DbArea& area, std::uint64_t recno);

// First / last visible record in the current logical order.
// Returns 0 if no visible record exists.
std::uint64_t first_recno(xbase::DbArea& area);
std::uint64_t last_recno(xbase::DbArea& area);

// Next / previous visible record in the current logical order.
// from_recno == 0 means "start from endpoint":
//   next_recno(..., 0) -> first visible
//   prev_recno(..., 0) -> last visible
//
// Returns 0 if no matching next/previous visible record exists.
std::uint64_t next_recno(xbase::DbArea& area, std::uint64_t from_recno);
std::uint64_t prev_recno(xbase::DbArea& area, std::uint64_t from_recno);

} // namespace cli::logical_nav
