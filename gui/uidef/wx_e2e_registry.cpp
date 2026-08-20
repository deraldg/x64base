// AIF-120 R58 -- a generated wx frontend driving the REAL engine, end to end.
//
// Build and run (needs BOTH wx and the engine archives -- the Cowork container has
// both; the device VM has neither wx nor a matching libstdc++):
//
//   B=build/wsl-core-vcpkg
//   cp dottalkpp/data/dbf/vfp/STUDENTS.dbf /tmp/e2e_STUDENTS.dbf
//   python3 gui/uidef/uidef_wx.py E2E.DBF /tmp/e2e.cpp --dispatch
//   g++ -std=c++17 -Wall -Wextra -Iinclude -I$B/generated -Igui/uidef \
//       /tmp/e2e.cpp gui/uidef/wx_e2e_registry.cpp \
//       $B/src/xbase/libxbase.a $B/src/memo/libmemo.a $B/src/xexpr/libxexpr.a \
//       $B/src/libdottalk_value.a $B/src/libdottalk_inx_payload.a \
//       -o /tmp/e2e $(wx-config --cxxflags --libs) -pthread
//   xvfb-run -a /tmp/e2e
//
// Chain under test, all of it at once:
//   UIDEF table -> uidef_wx.py --dispatch -> generated wx C++
//                -> uidef::Runtime (R37/R41 dispatch, R47 refusal semantics)
//                -> uidef::xbase_lock_provider (R57.1, typed)
//                -> xbase::locks + xbase::DbArea (the engine)
//
// R53.4 is honoured literally: every alias in SOURCE is opened into its own work
// area BEFORE any handler fires, and the provider is installed against a resolver
// that can only answer for areas that are already open.
#include "uidef_rt.h"
#include "uidef_xbase_locks.h"
#include "xbase.hpp"

#include <cstdio>
#include <string>
#include <vector>

extern uidef::Runtime* g_rt;
extern std::shared_ptr<uidef::Scope> g_scope;

static xbase::DbArea g_students;
static std::vector<std::string> g_log;
static std::mutex g_lm;
static void say(const std::string& s) { std::lock_guard<std::mutex> g(g_lm); g_log.push_back(s); }

void uidef_register(uidef::Runtime& rt) {
    rt.reg("CountRows", [](uidef::Scope&) {
        // Runs on a worker, under the domain lock the provider took from the engine.
        const std::uint64_t n = g_students.recCount64();
        std::string who;
        const bool mine = xbase::locks::is_table_locked(g_students, &who);
        say("handler saw recCount64=" + std::to_string(n) +
            ", table locked=" + (mine ? "yes" : "NO") + " (" + who + ")");
        return std::to_string(n);
    });
    rt.comp("Done", [](uidef::Scope&, const std::string& r, const std::string& st) {
        say("completion: " + st + " result=" + r);
    });
}

void uidef_after_init(wxWindow* frame) {
    (void)frame;   // the areas are named by SOURCE, not found through the window
    // ---- R53.4: open every SOURCE alias FIRST -------------------------------
    g_students.open("/tmp/e2e_STUDENTS.dbf");
    std::printf("open students        : %s\n", g_students.isOpen() ? "ok" : "FAILED");
    if (!g_students.isOpen()) { wxTheApp->ExitMainLoop(); return; }

    // ---- R57.1: the TYPED provider, not console text ------------------------
    g_rt->set_lock_provider(uidef::xbase_lock_provider(
        [](const std::string& alias) -> xbase::DbArea* {
            return alias == "students" ? &g_students : nullptr;
        },
        /*record_granularity=*/false,
        [](const std::string& m) { say("provider: " + m); }));

    std::printf("provider             : typed (xbase::locks), table granularity\n");

    // Fire the generated binding's handler.
    g_rt->fire("CountRows", "worker", g_scope, "students", "Done");

    static wxTimer* t = new wxTimer();
    t->Bind(wxEVT_TIMER, [](wxTimerEvent&) {
        std::string who;
        const bool held = xbase::locks::is_table_locked(g_students, &who);
        { std::lock_guard<std::mutex> g(g_lm);
          for (auto& l : g_log) std::printf("   %s\n", l.c_str()); }
        std::printf("after the handler    : table locked = %s (%s)\n",
                    held ? "yes -- LEAKED" : "no -- released", who.c_str());
        std::printf("\n  end to end: generated wx -> runtime -> typed provider -> engine : %s\n",
                    held ? "LOCK LEAKED" : "OK");
        std::fflush(stdout);
        wxTheApp->ExitMainLoop();
    });
    t->StartOnce(900);
}
