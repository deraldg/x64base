// @dottalk.file v1
// subsystem: xbase
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "xbase.hpp"
#include "memo/memo_manager.hpp"


namespace xbase {

// Out-of-line defaults keep manager implementation types private (MSVC-safe).
DbArea::DbArea(DbArea&&) = default;
DbArea& DbArea::operator=(DbArea&&) = default;

} // namespace xbase
