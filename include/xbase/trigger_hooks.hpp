// @dottalk.file v1
// subsystem: xbase
// layer: header
// owns:
// project: project.x64base.runtime
// lane: triggers-pdlc
// owner: member.derald
// status: experimental
//
// AIF-087: per-DbArea data-trigger callbacks (D2 / C4).
//
// M1, 2026-09-03 -- TWO MECHANISMS, NOT ONE WITH A FLAG.
//
// Decision E as signed 2026-08-04 deferred buffered edits. SQLsel P5 DML is now
// built on TableBuffer + TBJ1 WAL, so that deferral made triggers SILENT FOR
// EVERY SQL WRITE. Re-ruled 2026-09-03.
//
// The WAL COMMIT marker is the instant a change becomes true: before it the
// transaction may vanish, after it recovery replays the write regardless.
// Therefore A TRIGGER CANNOT BOTH FIRE ON COMMITTED TRUTH AND BE ABLE TO REFUSE,
// and the two are separate registrations:
//
//   Before -- fires at commit entry, BEFORE the WAL COMMIT marker.
//             MAY REFUSE the write. MUST NOT mutate (it would re-enter the
//             buffer being committed).
//   After  -- fires once the change is true. CANNOT refuse. May write, in its
//             own transaction, bounded by a depth cap.
//
// On the UNBUFFERED path the two instants coincide, which is why the original
// single-callback spike never had to distinguish them. `fire_field_replace`
// keeps its exact prior behaviour and is now explicitly the AFTER phase.
//
// NOT YET WIRED: the Before phase has a registration slot and a fire entry point
// and NOTHING CALLS IT. Commit-entry wiring is M2 and is not authorized here.
// A registration that can never fire is stated rather than implied, so nobody
// reads this header as evidence that BEFORE triggers work.
//
// Does NOT use cursor_hook (shell/TUI global slot).
#pragma once
#include <cstdint>
namespace xbase {
class DbArea;
namespace trigger_hooks {
// Which side of the WAL COMMIT marker a callback fires on.
enum class Phase { Before, After };

// event_kind values are stable string literals (e.g. "field_replace").
using TriggerFn = void (*)(DbArea& area,
                           const char* event_kind,
                           int field1,
                           std::uint64_t recno,
                           void* user) noexcept;

// A Before callback returns false to REFUSE the write. Its signature is fixed
// here, at M1, so that wiring it in M2 is not an API change to a shipped type.
using BeforeTriggerFn = bool (*)(DbArea& area,
                                 const char* event_kind,
                                 int field1,
                                 std::uint64_t recno,
                                 void* user) noexcept;

// Associate an AFTER callback with a specific DbArea (D2). Null fn clears.
// Retained unchanged: this is the phase that has always existed.
void set_callback(DbArea& area, TriggerFn fn, void* user) noexcept;
void clear_callback(DbArea& area) noexcept;

// Associate a BEFORE callback. Registration works; NOTHING FIRES IT YET (M2).
void set_before_callback(DbArea& area, BeforeTriggerFn fn, void* user) noexcept;
void clear_before_callback(DbArea& area) noexcept;

// Ask the registered Before callback whether a field replace may proceed.
// Returns true when there is no callback, so an unregistered area is unaffected.
// NO CALLER IN M1 -- commit entry wires this in M2.
bool allow_field_replace(DbArea& area, int field1, std::uint64_t recno) noexcept;
// AFTER phase. Invoked by DbArea::replaceFieldStored after successful
// apply_replace. No-op if no callback is set. Nested fires suppressed by Guard.
// Behaviour is byte-for-byte what it was before M1.
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
