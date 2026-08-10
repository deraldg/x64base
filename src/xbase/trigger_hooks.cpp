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
#include "xbase/trigger_hooks.hpp"
#include <mutex>
#include <unordered_map>
namespace xbase::trigger_hooks {
namespace {
struct Entry {
    TriggerFn fn = nullptr;
    void*     user = nullptr;
};
std::mutex& table_mu() noexcept
{
    static std::mutex mu;
    return mu;
}
std::unordered_map<DbArea*, Entry>& table() noexcept
{
    static std::unordered_map<DbArea*, Entry> t;
    return t;
}
thread_local int g_suppress_depth = 0;
} // namespace
void set_callback(DbArea& area, TriggerFn fn, void* user) noexcept
{
    std::lock_guard<std::mutex> lock(table_mu());
    if (!fn) {
        table().erase(&area);
        return;
    }
    table()[&area] = Entry{fn, user};
}
void clear_callback(DbArea& area) noexcept
{
    set_callback(area, nullptr, nullptr);
}
void detach(DbArea& area) noexcept
{
    clear_callback(area);
}
void fire_field_replace(DbArea& area, int field1, std::uint64_t recno) noexcept
{
    if (g_suppress_depth > 0) return;
    TriggerFn fn = nullptr;
    void* user = nullptr;
    {
        std::lock_guard<std::mutex> lock(table_mu());
        const auto it = table().find(&area);
        if (it == table().end() || !it->second.fn) return;
        fn = it->second.fn;
        user = it->second.user;
    }
    // Suppress nested fire while the callback runs.
    Guard nested;
    fn(area, "field_replace", field1, recno, user);
}
Guard::Guard() noexcept  { ++g_suppress_depth; }
Guard::~Guard() noexcept { --g_suppress_depth; }
} // namespace xbase::trigger_hooks
