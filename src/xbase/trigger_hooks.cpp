// @dottalk.file v1
// subsystem: xbase
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: triggers-pdlc
// owner: member.derald
// status: experimental
//
// AIF-087 Phase-1: per-area trigger callback table. GLOB'd into xbase STATIC.
//
// M2a, 2026-09-04: ONE After table and ONE Before table, both keyed by DbArea*
// and both under the SAME mutex, so register/fire ordering is total across the
// two phases.
//
// The After entry holds BOTH callback shapes. A per-write callback wins when
// both are set; otherwise a per-field callback is fanned out once per changed
// field. That fan-out is the compatibility path for
// DbArea::replaceFieldStored, where the set always has one element -- it is
// NOT a claim that N calls faithfully represent one physical write. See the
// header for why the write, not the field, is the unit.
//
// The Before table is read only by allow_record_write, WHICH HAS NO CALLER YET.
// Wiring it at commit entry is M2b.
#include "xbase/trigger_hooks.hpp"
#include <mutex>
#include <unordered_map>
namespace xbase::trigger_hooks {
namespace {
struct AfterEntry {
    AfterWriteFn write_fn   = nullptr;  // general form; wins when both are set
    void*        write_user = nullptr;
    TriggerFn    field_fn   = nullptr;  // degenerate per-field form
    void*        field_user = nullptr;
};
struct BeforeEntry {
    BeforeWriteFn fn   = nullptr;
    void*         user = nullptr;
};
std::mutex& table_mu() noexcept
{
    static std::mutex mu;
    return mu;
}
std::unordered_map<DbArea*, AfterEntry>& table() noexcept
{
    static std::unordered_map<DbArea*, AfterEntry> t;
    return t;
}
std::unordered_map<DbArea*, BeforeEntry>& before_table() noexcept
{
    static std::unordered_map<DbArea*, BeforeEntry> t;
    return t;
}
thread_local int g_suppress_depth = 0;
// Erase the After row once neither shape is registered, so an area that set and
// then cleared both leaves no entry behind.
void prune_after(DbArea& area) noexcept
{
    const auto it = table().find(&area);
    if (it == table().end()) return;
    if (!it->second.write_fn && !it->second.field_fn) table().erase(it);
}
} // namespace
void set_callback(DbArea& area, TriggerFn fn, void* user) noexcept
{
    std::lock_guard<std::mutex> lock(table_mu());
    auto& e = table()[&area];
    e.field_fn   = fn;
    e.field_user = fn ? user : nullptr;
    prune_after(area);
}
void clear_callback(DbArea& area) noexcept
{
    set_callback(area, nullptr, nullptr);
}
void set_after_callback(DbArea& area, AfterWriteFn fn, void* user) noexcept
{
    std::lock_guard<std::mutex> lock(table_mu());
    auto& e = table()[&area];
    e.write_fn   = fn;
    e.write_user = fn ? user : nullptr;
    prune_after(area);
}
void clear_after_callback(DbArea& area) noexcept
{
    set_after_callback(area, nullptr, nullptr);
}
void set_before_callback(DbArea& area, BeforeWriteFn fn, void* user) noexcept
{
    std::lock_guard<std::mutex> lock(table_mu());
    if (!fn) {
        before_table().erase(&area);
        return;
    }
    before_table()[&area] = BeforeEntry{fn, user};
}
void clear_before_callback(DbArea& area) noexcept
{
    set_before_callback(area, nullptr, nullptr);
}
bool allow_record_write(DbArea& area, const WriteEvent& ev, RefusalCode* reason) noexcept
{
    if (reason) *reason = kNoReason;
    // No Before callback registered -> the write proceeds. An area that never
    // asked for a veto must behave exactly as it did before triggers existed.
    if (g_suppress_depth > 0) return true;
    BeforeWriteFn fn = nullptr;
    void* user = nullptr;
    {
        std::lock_guard<std::mutex> lock(table_mu());
        const auto it = before_table().find(&area);
        if (it == before_table().end() || !it->second.fn) return true;
        fn = it->second.fn;
        user = it->second.user;
    }
    // A Before callback MUST NOT mutate -- it would re-enter the buffer being
    // committed. The Guard makes any write it attempts fire no further trigger,
    // which CONTAINS the damage but does not license the mutation.
    RefusalCode local = kNoReason;
    Guard nested;
    return fn(area, ev, reason ? reason : &local, user);
}
bool allow_field_replace(DbArea& area, int field1, std::uint64_t recno,
                         RefusalCode* reason) noexcept
{
    const int fields[1] = { field1 };
    WriteEvent ev;
    ev.event_kind  = "field_replace";
    ev.recno       = recno;
    ev.fields      = fields;
    ev.field_count = 1;
    return allow_record_write(area, ev, reason);
}
void detach(DbArea& area) noexcept
{
    clear_callback(area);
    clear_after_callback(area);
    clear_before_callback(area);
}
void fire_record_write(DbArea& area, const WriteEvent& ev) noexcept
{
    if (g_suppress_depth > 0) return;
    AfterEntry e;
    {
        std::lock_guard<std::mutex> lock(table_mu());
        const auto it = table().find(&area);
        if (it == table().end()) return;
        e = it->second;
    }
    if (!e.write_fn && !e.field_fn) return;
    // Suppress nested fire while the callback runs.
    Guard nested;
    if (e.write_fn) {
        e.write_fn(area, ev, e.write_user);
        return;
    }
    // Degenerate form: one call per changed field. Correct for the one-field
    // writes this shape exists to serve; see the header before reusing it.
    for (std::size_t i = 0; i < ev.field_count; ++i) {
        e.field_fn(area, ev.event_kind, ev.fields[i], ev.recno, e.field_user);
    }
}
void fire_field_replace(DbArea& area, int field1, std::uint64_t recno) noexcept
{
    const int fields[1] = { field1 };
    WriteEvent ev;
    ev.event_kind  = "field_replace";
    ev.recno       = recno;
    ev.fields      = fields;
    ev.field_count = 1;
    fire_record_write(area, ev);
}
Guard::Guard() noexcept  { ++g_suppress_depth; }
Guard::~Guard() noexcept { --g_suppress_depth; }
} // namespace xbase::trigger_hooks
