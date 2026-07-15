#include "xbase.hpp"
#include "memo/memo_manager.hpp"


namespace xbase {

// Out-of-line defaults keep manager implementation types private (MSVC-safe).
DbArea::DbArea(DbArea&&) = default;
DbArea& DbArea::operator=(DbArea&&) = default;

} // namespace xbase
