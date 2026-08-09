// @dottalk.file v1
// subsystem: xbase
// layer: header
// owns:
// project: project.x64base.runtime
// lane: triggers-pdlc
// owner: member.derald
// status: experimental
//
// AIF-087 Phase-1 spike: per-DbArea data-trigger callback (D2 / C4).
// Fire path is replaceFieldStored after successful index_hooks.apply_replace (B1).
// Does NOT use cursor_hook (shell/TUI global slot).
#pragma once
#include <cstdint>
namespace xbase {
class DbArea;
namespace trigger_hooks {
// event_kind values are stable string literals (e.g. "field_replace").
using TriggerFn = void (*)(DbArea& area,
                           const char* event_kind,
                           int field1,
                           std::uint64_t recno,
                           void* user) noexcept;
// Associate a callback with a specific DbArea (D2). Null fn clears.
void set_callback(DbArea& area, TriggerFn fn, void* user) noexcept;
void clear_callback(DbArea& area) noexcept;
// Invoked by DbArea::replaceFieldStored after successful apply_replace.
// No-op if no callback is set for this area. Nested fires suppressed by Guard.
void fire_field_replace(DbArea& area, int field1, std::uint64_t recno) noexcept;
// Optional: drop registration when an area is destroyed/closed by higher layers.
void detach(DbArea& area) noexcept;
// Suppress nested trigger fire within a scope (same idea as cursor_hook::Guard).
class Guard {
public:
    Guard() noexcept;
    ~Guard() noexcept;
    Guard(const Guard&)            = delete;
    Guard& operator=(const Guard&) = delete;
    Guard(Guard&&)                 = delete;
    Guard& operator=(Guard&&)      = delete;
};
} // namespace trigger_hooks
} // namespace xbase
