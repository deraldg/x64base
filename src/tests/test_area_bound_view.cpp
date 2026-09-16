// @dottalk.file v1
// subsystem: tests
// layer: test
// owns: 
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

// R146 -- a schema panel is bound to the AREA, and an area can change under it.
//
// WHY THIS IS A ctest AND NOT A .dts. SMARTBROWSER is an interactive pager and,
// under a script, paints the first page and exits on the failed getline --
// measured and recorded in the probe's own header
// (dottalkpp/data/scripts/buffer_visibility_probe_v3_smartbrowser.dts). So no
// script in this tree can reach OPEN CHILD, and the defect R146 names is
// unreachable from the .dts suite in both directions: a script can neither
// provoke it nor prove it fixed. A spec that cannot fail is the INDEX_X64 v2
// shape the suite reported as PASS on 2026-09-13.
//
// The resolvers here are counters, not the real ones. This test asserts the
// BINDING RULE -- when a derivation happens -- and never touches a table, an
// index or the filesystem, which is what lets it run on any build.
//
// EACH ARM RETURNS ITS OWN CODE so a failure names itself in ctest output.

#include "area_bound_view.hpp"

#include <string>

int main()
{
    int schema_calls  = 0;
    int sidecar_calls = 0;

    dottalk::AreaBoundView<std::string, std::string> view(
        [&](const std::string& a) { ++schema_calls;  return "schema-of:"  + a; },
        [&](const std::string& a) { ++sidecar_calls; return "sidecar-of:" + a; });

    // A1. Nothing is derived before the first sync, and primed() says so rather
    //     than handing back a payload no resolver produced.
    if (view.primed())          return 1;
    if (view.derivations() != 0) return 2;

    // A2. The first sync derives.
    view.sync("CUSTOMER");
    if (!view.primed())                        return 3;
    if (view.derivations() != 1)               return 4;
    if (view.area()    != "CUSTOMER")          return 5;
    if (view.schema()  != "schema-of:CUSTOMER")  return 6;
    if (view.sidecar() != "sidecar-of:CUSTOMER") return 7;

    // A3. THE CONTROL, and the half a naive fix gets wrong. Repainting the same
    //     area -- every page turn, every SKIP, every TOP -- must NOT re-derive.
    //     If this arm goes red the pager resolves a schema per page.
    for (int i = 0; i < 5; ++i) view.sync("CUSTOMER");
    if (view.derivations() != 1) return 8;
    if (schema_calls  != 1)      return 9;
    if (sidecar_calls != 1)      return 10;

    // A4. THE DISCRIMINATOR. This is OPEN CHILD: the area changes under a live
    //     view. Before R146 the pager held CUSTOMER's schema here and printed it
    //     above ORDERS' rows.
    view.sync("ORDERS");
    if (view.derivations() != 2)             return 11;
    if (view.area()   != "ORDERS")           return 12;
    if (view.schema() != "schema-of:ORDERS") return 13;

    // A5. BACK. Returning to an area already visited derives AGAIN -- the view
    //     holds one area, not a cache. Asserted so a later "optimisation" that
    //     memoises per area has to change this line deliberately and say why.
    view.sync("CUSTOMER");
    if (view.derivations() != 3)                return 14;
    if (view.schema() != "schema-of:CUSTOMER")  return 15;

    // A6. The empty name is a real area state, not a sentinel to skip. An
    //     unopened or closed stream must show what the resolver says about
    //     nothing, and it must count as a derivation like any other change.
    view.sync("");
    if (view.derivations() != 4)          return 16;
    if (view.area()   != "")              return 17;
    if (view.schema() != "schema-of:")    return 18;

    // A7. ...and the empty name is idempotent too, so a closed stream repainting
    //     does not resolve on every pass.
    view.sync("");
    if (view.derivations() != 4) return 19;

    // A8. Both resolvers ran the same number of times. A view whose schema and
    //     sidecar could drift apart would be two bindings wearing one name.
    if (schema_calls != sidecar_calls) return 20;
    if (schema_calls != 4)             return 21;

    return 0;
}
