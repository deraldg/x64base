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
               const xbase::trigger_hooks::WriteEvent& ev,
               xbase::trigger_hooks::RefusalCode* reason,
               void* user) noexcept
{
    auto* p = static_cast<Probe*>(user);
    if (p) {
        p->fires += 1;
        p->last_recno = ev.recno;
        p->last_field1 = (ev.field_count > 0) ? ev.fields[0] : 0;
    }
    // Refuse any write that touches field 4, so the veto is distinguishable
    // from a no-op AND is a decision about the WRITE, not about one field.
    for (std::size_t i = 0; i < ev.field_count; ++i) {
        if (ev.fields[i] == 4) {
            if (reason) *reason = 4242;
            return false;
        }
    }
    return true;
}
struct WriteProbe {
    int fires = 0;
    std::size_t last_count = 0;
    int last_first = 0;
    std::uint64_t last_recno = 0;
};
void on_after_write(xbase::DbArea& /*area*/,
                    const xbase::trigger_hooks::WriteEvent& ev,
                    void* user) noexcept
{
    auto* p = static_cast<WriteProbe*>(user);
    if (!p) return;
    p->fires += 1;
    p->last_count = ev.field_count;
    p->last_first = (ev.field_count > 0) ? ev.fields[0] : 0;
    p->last_recno = ev.recno;
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
    // --- M2a: BEFORE registration slot. NOT WIRED INTO THE ENGINE (M2b).
    // These call allow_* directly; nothing in dbarea.cpp or cmd_commit.cpp does.
    {
        Probe bp;
        namespace th = xbase::trigger_hooks;
        th::RefusalCode why = 99;
        // Unregistered area must be unaffected: allow, and clear the code.
        if (!th::allow_field_replace(area, 4, 1, &why)) {
            return fail("unregistered before-callback did not allow");
        }
        if (why != th::kNoReason) return fail("reason not reset when allowed");
        if (bp.fires != 0) return fail("unregistered before-callback fired");

        th::set_before_callback(area, &on_before, &bp);
        if (!th::allow_field_replace(area, 3, 1, &why)) {
            return fail("before-callback refused a permitted field");
        }
        if (bp.fires != 1) return fail("before-callback did not fire");
        if (why != th::kNoReason) return fail("reason set on an allowed write");
        if (th::allow_field_replace(area, 4, 1, &why)) {
            return fail("before-callback veto not honoured");
        }
        if (why != 4242) return fail("refusal code not carried out");
        if (bp.fires != 2) return fail("before-callback fire count");

        // A MULTI-FIELD write is ONE decision, not one per field. Four fields,
        // one of them vetoed => exactly ONE callback call, and a refusal.
        bp.fires = 0;
        const int many[4] = {1, 2, 4, 3};
        th::WriteEvent mev;
        mev.event_kind = "field_replace";
        mev.recno = 7;
        mev.fields = many;
        mev.field_count = 4;
        if (th::allow_record_write(area, mev, &why)) {
            return fail("multi-field veto not honoured");
        }
        if (bp.fires != 1) return fail("multi-field write asked more than once");
        if (bp.last_recno != 7) return fail("multi-field recno mismatch");

        // The reason argument is optional.
        if (th::allow_record_write(area, mev)) {
            return fail("veto not honoured without a reason argument");
        }

        // Before and After registrations are independent.
        probe.fires = 0;
        th::set_callback(area, &on_trigger, &probe);
        th::fire_field_replace(area, 4, 1);
        if (probe.fires != 1) return fail("after fire disturbed by before slot");
        if (bp.fires != 2) return fail("after fire invoked before-callback");

        th::clear_callback(area);
        th::clear_before_callback(area);
        if (!th::allow_field_replace(area, 4, 1)) {
            return fail("cleared before-callback still refusing");
        }
        if (bp.fires != 2) return fail("cleared before-callback still fired");
    }
    // --- M2a: per-write AFTER callback. ONE call for one physical write.
    {
        namespace th = xbase::trigger_hooks;
        WriteProbe wp;
        const int many[3] = {5, 6, 7};
        th::WriteEvent ev;
        ev.event_kind = "record_write";
        ev.recno = 12;
        ev.fields = many;
        ev.field_count = 3;

        th::set_after_callback(area, &on_after_write, &wp);
        th::fire_record_write(area, ev);
        if (wp.fires != 1) return fail("per-write after did not fire exactly once");
        if (wp.last_count != 3) return fail("changed-field count not carried");
        if (wp.last_first != 5) return fail("changed-field set not carried");
        if (wp.last_recno != 12) return fail("per-write recno mismatch");

        // Per-write wins over per-field when both are registered.
        probe.fires = 0;
        th::set_callback(area, &on_trigger, &probe);
        th::fire_record_write(area, ev);
        if (wp.fires != 2) return fail("per-write callback not preferred");
        if (probe.fires != 0) return fail("per-field fired while per-write set");

        // With only the per-field shape, a 3-field write fans out to 3 calls --
        // the documented degenerate path, asserted so a change to it is visible.
        th::clear_after_callback(area);
        probe.fires = 0;
        th::fire_record_write(area, ev);
        if (probe.fires != 3) return fail("per-field fan-out count");

        th::clear_callback(area);
        wp.fires = 0;
        probe.fires = 0;
        th::fire_record_write(area, ev);
        if (wp.fires != 0 || probe.fires != 0) return fail("cleared after still fired");
    }
    std::printf("PASS test_trigger_hooks_smoke\n");
    return 0;
}
