// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: triggers-pdlc
// status: experimental
//
// AIF-087 G1 smoke: trigger_hooks set/clear/fire/nested-suppress without
// requiring an open DBF. Links xbase.
#include "xbase.hpp"
#include "xbase/trigger_hooks.hpp"
#include <cstdio>
#include <cstdint>
namespace {
struct Probe {
    int fires = 0;
    int last_field1 = 0;
    std::uint64_t last_recno = 0;
    const char* last_kind = nullptr;
    xbase::DbArea* last_area = nullptr;
};
void on_trigger(xbase::DbArea& area,
                const char* event_kind,
                int field1,
                std::uint64_t recno,
                void* user) noexcept
{
    auto* p = static_cast<Probe*>(user);
    if (!p) return;
    p->fires += 1;
    p->last_field1 = field1;
    p->last_recno = recno;
    p->last_kind = event_kind;
    p->last_area = &area;
}
void on_nested(xbase::DbArea& area,
               const char* /*event_kind*/,
               int field1,
               std::uint64_t recno,
               void* user) noexcept
{
    auto* p = static_cast<Probe*>(user);
    if (!p) return;
    p->fires += 1;
    // Attempt re-entrant fire; Guard inside fire_field_replace must suppress.
    xbase::trigger_hooks::fire_field_replace(area, field1, recno);
}
bool on_before(xbase::DbArea& /*area*/,
               const char* /*event_kind*/,
               int field1,
               std::uint64_t /*recno*/,
               void* user) noexcept
{
    auto* p = static_cast<Probe*>(user);
    if (p) p->fires += 1;
    // Refuse exactly one field so the veto is distinguishable from a no-op.
    return field1 != 4;
}
int fail(const char* msg)
{
    std::fprintf(stderr, "FAIL: %s\n", msg);
    return 1;
}
} // namespace
int main()
{
    xbase::DbArea area;
    Probe probe;
    // Null callback: no-op
    xbase::trigger_hooks::fire_field_replace(area, 3, 42);
    if (probe.fires != 0) return fail("null callback fired");
    // Install and fire once
    xbase::trigger_hooks::set_callback(area, &on_trigger, &probe);
    xbase::trigger_hooks::fire_field_replace(area, 7, 99);
    if (probe.fires != 1) return fail("expected one fire");
    if (probe.last_field1 != 7) return fail("field1 mismatch");
    if (probe.last_recno != 99) return fail("recno mismatch");
    if (probe.last_area != &area) return fail("area pointer mismatch");
    {
        const char* k = probe.last_kind;
        const char* expect = "field_replace";
        if (!k) return fail("event_kind null");
        for (int i = 0; expect[i]; ++i) {
            if (k[i] != expect[i]) return fail("event_kind mismatch");
        }
        if (k[13] != '\0') return fail("event_kind mismatch");
    }
    // Clear: no more fires
    xbase::trigger_hooks::clear_callback(area);
    xbase::trigger_hooks::fire_field_replace(area, 1, 1);
    if (probe.fires != 1) return fail("cleared callback still fired");
    // Nested suppress
    probe.fires = 0;
    xbase::trigger_hooks::set_callback(area, &on_nested, &probe);
    xbase::trigger_hooks::fire_field_replace(area, 2, 5);
    if (probe.fires != 1) return fail("nested fire not suppressed");
    xbase::trigger_hooks::clear_callback(area);
    // --- M1: BEFORE registration slot. NOT WIRED INTO THE ENGINE (M2).
    // These call allow_field_replace directly; nothing in dbarea.cpp does.
    {
        Probe bp;
        // Unregistered area must be unaffected: allow.
        if (!xbase::trigger_hooks::allow_field_replace(area, 4, 1)) {
            return fail("unregistered before-callback did not allow");
        }
        if (bp.fires != 0) return fail("unregistered before-callback fired");
        xbase::trigger_hooks::set_before_callback(area, &on_before, &bp);
        if (!xbase::trigger_hooks::allow_field_replace(area, 3, 1)) {
            return fail("before-callback refused a permitted field");
        }
        if (bp.fires != 1) return fail("before-callback did not fire");
        if (xbase::trigger_hooks::allow_field_replace(area, 4, 1)) {
            return fail("before-callback veto not honoured");
        }
        if (bp.fires != 2) return fail("before-callback fire count");
        // Before and After registrations are independent: firing After must
        // not consult the Before table.
        probe.fires = 0;
        xbase::trigger_hooks::set_callback(area, &on_trigger, &probe);
        xbase::trigger_hooks::fire_field_replace(area, 4, 1);
        if (probe.fires != 1) return fail("after fire disturbed by before slot");
        if (bp.fires != 2) return fail("after fire invoked before-callback");
        xbase::trigger_hooks::clear_callback(area);
        xbase::trigger_hooks::clear_before_callback(area);
        if (!xbase::trigger_hooks::allow_field_replace(area, 4, 1)) {
            return fail("cleared before-callback still refusing");
        }
        if (bp.fires != 2) return fail("cleared before-callback still fired");
    }
    std::printf("PASS test_trigger_hooks_smoke\n");
    return 0;
}
