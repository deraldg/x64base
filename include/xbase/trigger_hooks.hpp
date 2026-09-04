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
// M2a, 2026-09-04 -- THE FIRE UNIT IS THE PHYSICAL WRITE, NOT THE FIELD.
//
// M1 modelled a fire as one field. Measuring the three write paths showed that
// is the special case, not the general one:
//
//   DbArea::replaceFieldStored -- 1 field, 1 write. The two coincide, which is
//                                 why the original spike never had to choose.
//   MULTIREP                   -- N fields, ONE record lock, ONE physical write.
//   COMMIT's apply_one_recno   -- N fields folded by aggregate_for_recno, then
//                                 one set() loop and ONE writeCurrent().
//
// Firing N times for one physical write misreports what happened, and for the
// Before phase it is incoherent: N independent vetoes over one indivisible
// write, when YOU CANNOT HALF-WRITE A RECORD. A veto is a veto of the write.
//
// So the general callback takes a WriteEvent carrying the changed-field set,
// and the per-field form is retained as the degenerate one-element case that
// `replaceFieldStored` still uses. `fire_field_replace` keeps its exact prior
// behaviour and is now explicitly the After phase.
//
// NOT YET WIRED: the Before phase has registration and a fire entry point and
// NOTHING CALLS IT. Commit-entry wiring is M2b and is not authorized here.
// A registration that can never fire is stated rather than implied, so nobody
// reads this header as evidence that BEFORE triggers work.
//
// Does NOT use cursor_hook (shell/TUI global slot).
#pragma once
#include <cstddef>
#include <cstdint>
namespace xbase {
class DbArea;
namespace trigger_hooks {
// Which side of the WAL COMMIT marker a callback fires on.
enum class Phase { Before, After };

// Why a Before callback refused. OPAQUE TO THIS LAYER BY DESIGN: the message
// catalog (dottalk::helpdata::MessageId) lives in the CLI, and src/xbase must
// not depend on it. The CLI maps this back to a catalog id so STOP_ON_ERROR
// governs the refusal per AIF-036. Zero means "no reason supplied".
using RefusalCode = std::uint32_t;
inline constexpr RefusalCode kNoReason = 0;

// One physical record write, and the fields it changed. `fields` points at
// `field_count` 1-based field numbers owned by the CALLER and valid only for
// the duration of the call -- a callback that needs them longer must copy.
// field_count may be 0 for a write that changes no field (a delete).
struct WriteEvent {
    const char*   event_kind   = nullptr;  // stable literal, e.g. "field_replace"
    std::uint64_t recno        = 0;
    const int*    fields       = nullptr;
    std::size_t   field_count  = 0;
};

// Per-field After callback. THE DEGENERATE CASE, kept because
// DbArea::replaceFieldStored is genuinely one field per write. Unchanged since
// the 2026-08-04 spike.
using TriggerFn = void (*)(DbArea& area,
                           const char* event_kind,
                           int field1,
                           std::uint64_t recno,
                           void* user) noexcept;

// Per-write After callback. The general form.
using AfterWriteFn = void (*)(DbArea& area,
                              const WriteEvent& ev,
                              void* user) noexcept;

// Per-write Before callback. Returns false to REFUSE, and may set *reason.
using BeforeWriteFn = bool (*)(DbArea& area,
                               const WriteEvent& ev,
                               RefusalCode* reason,
                               void* user) noexcept;

// -- After registration (D2). At most one shape per area; the last set wins for
// its own shape, and a per-write callback takes precedence over a per-field one.
void set_callback(DbArea& area, TriggerFn fn, void* user) noexcept;
void clear_callback(DbArea& area) noexcept;
void set_after_callback(DbArea& area, AfterWriteFn fn, void* user) noexcept;
void clear_after_callback(DbArea& area) noexcept;

// -- Before registration. Registration works; NOTHING FIRES IT YET (M2b).
void set_before_callback(DbArea& area, BeforeWriteFn fn, void* user) noexcept;
void clear_before_callback(DbArea& area) noexcept;

// Ask the registered Before callback whether a write may proceed. Returns true
// when there is no callback, so an unregistered area is unaffected. On refusal,
// *reason receives the callback's code (kNoReason if it set none).
// NO CALLER IN M2a -- commit entry wires this in M2b.
bool allow_record_write(DbArea& area,
                        const WriteEvent& ev,
                        RefusalCode* reason = nullptr) noexcept;
// One-field convenience over allow_record_write.
bool allow_field_replace(DbArea& area,
                         int field1,
                         std::uint64_t recno,
                         RefusalCode* reason = nullptr) noexcept;

// -- After fire. No-op if nothing is registered. Nested fires suppressed by Guard.
void fire_record_write(DbArea& area, const WriteEvent& ev) noexcept;
// Invoked by DbArea::replaceFieldStored after successful apply_replace.
// Behaviour is what it was before M1: one call, event_kind "field_replace".
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
