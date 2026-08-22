// @dottalk.file v1
// subsystem: gui
// layer: registry
// owns: uidef_register / uidef_after_init
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: supported
// summary:
//   R60 -- contention and ROLLBACK between two typed frontends
//
// notes:
//   Contract added 2026-08-22. This directory was promoted from lane to
//   project in 898a37b62 without them, so 14 of its 15 C++ files were
//   INVISIBLE to the doc pass -- not undocumented, invisible: the pass
//   completed and reported success while covering less than it claimed.

// AIF-120 R60 -- contention and ROLLBACK between two typed frontends.
//
// Build (needs wx AND the engine archives), then run TWO processes:
//
//   B=build/wsl-core-vcpkg
//   cp dottalkpp/data/dbf/vfp/STUDENTS.dbf /tmp/c_STUDENTS.dbf
//   cp dottalkpp/data/dbf/vfp/ENROLL.dbf   /tmp/c_ENROLL.dbf
//   python3 gui/uidef/uidef_wx.py DOMAIN.DBF /tmp/dom.cpp --dispatch
//   g++ -std=c++17 -Wall -Wextra -Iinclude -I$B/generated -Igui/uidef \
//       /tmp/dom.cpp gui/uidef/wx_contend_registry.cpp \
//       $B/src/xbase/libxbase.a $B/src/memo/libmemo.a $B/src/xexpr/libxexpr.a \
//       $B/src/libdottalk_value.a $B/src/libdottalk_inx_payload.a \
//       -o /tmp/con $(wx-config --cxxflags --libs) -pthread
//   ( xvfb-run -a /tmp/con hold & ) ; sleep 4 ; xvfb-run -a /tmp/con try
//
// The holder holds for 12s deliberately. An earlier version held for 3s while the
// runner slept 3s, so the contender arrived as the lock was released, the handler
// RAN, and the run proved nothing while looking like a pass.
//
// R59 left both: "No contention" and "the typed provider's rollback path has not
// executed: it needs an acquisition that fails partway, which needs a second
// process." This is that second process.
//
//   ./con hold    -- takes ONLY `students`, the SECOND alias in the provider's
//                    sorted order, and holds it. So a contender acquires `enroll`
//                    first, is refused `students`, and MUST give `enroll` back.
//   ./con try     -- a full typed frontend: fires a handler on the domain and
//                    reports whether it ran, plus what it left behind.
#include "uidef_rt.h"
#include "uidef_xbase_locks.h"
#include "xbase.hpp"

#include <cstdio>
#include <string>
#include <vector>

extern uidef::Runtime* g_rt;
extern std::shared_ptr<uidef::Scope> g_scope;

static xbase::DbArea g_students, g_enroll;
static std::vector<std::string> g_log;
static std::mutex g_lm;
static bool g_ran = false;
static std::string g_state = "(no completion)";
static void say(const std::string& s) { std::lock_guard<std::mutex> g(g_lm); g_log.push_back(s); }

static const char* st(xbase::DbArea& a) {
    return xbase::locks::is_table_locked(a) ? "LOCKED" : "free";
}

void uidef_register(uidef::Runtime& rt) {
    rt.reg("Touch", [](uidef::Scope&) {
        g_ran = true;
        say("  handler RAN -- students=" + std::string(st(g_students)) +
            " enroll=" + std::string(st(g_enroll)));
        return std::string("touched");
    });
    rt.comp("Done", [](uidef::Scope&, const std::string& r, const std::string& s2) {
        g_state = s2 + " (" + r + ")";
    });
}

void uidef_after_init(wxWindow* frame) {
    (void)frame;
    const std::string mode = wxTheApp->argc > 1
        ? std::string(wxTheApp->argv[1].mb_str()) : std::string("try");
    g_students.open("/tmp/c_STUDENTS.dbf");
    g_enroll.open("/tmp/c_ENROLL.dbf");
    if (!g_students.isOpen() || !g_enroll.isOpen()) {
        std::printf("open FAILED\n"); wxTheApp->ExitMainLoop(); return;
    }

    if (mode == "hold") {
        std::string err;
        const bool ok = xbase::locks::try_lock_table(
            g_students, xbase::locks::current_owner(), &err);
        std::printf("HOLDER  owner=%s  students=%s%s\n",
                    xbase::locks::current_owner().id.c_str(),
                    ok ? "LOCKED" : "FAILED ", err.c_str());
        std::fflush(stdout);
        static wxTimer* t = new wxTimer();
        t->Bind(wxEVT_TIMER, [](wxTimerEvent&) {
            std::string e2;
            xbase::locks::unlock_table(g_students, xbase::locks::current_owner(), &e2);
            std::printf("HOLDER  released\n");
            std::fflush(stdout);
            wxTheApp->ExitMainLoop();
        });
        t->StartOnce(12000);   // hold long enough that the contender cannot arrive late
        return;
    }

    g_rt->set_lock_provider(uidef::xbase_lock_provider(
        [](const std::string& a) -> xbase::DbArea* {
            say("  resolve: " + a);
            if (a == "students") return &g_students;
            if (a == "enroll")   return &g_enroll;
            return nullptr;
        },
        false,
        [](const std::string& m) { say("  provider: " + m); }));

    // R52's C0 lesson: "enroll is free at the end" is also satisfied by "enroll was
    // never locked". Watch it from a timer DURING the acquisition instead.
    static wxTimer* peek = new wxTimer();
    peek->Bind(wxEVT_TIMER, [](wxTimerEvent&) {
        say(std::string("  mid-acquire peek : enroll=") + st(g_enroll));
    });
    peek->Start(1);

    std::printf("CONTENDER owner=%s\n", xbase::locks::current_owner().id.c_str());
    std::printf("  before : students=%s enroll=%s\n", st(g_students), st(g_enroll));
    g_rt->fire("Touch", "worker", g_scope, "students", "Done");

    static wxTimer* t = new wxTimer();
    t->Bind(wxEVT_TIMER, [](wxTimerEvent&) {
        { std::lock_guard<std::mutex> g(g_lm);
          for (auto& l : g_log) std::printf("%s\n", l.c_str()); }
        std::printf("  handler ran      : %s\n", g_ran ? "YES" : "no -- refused");
        std::printf("  completion state : %s\n", g_state.c_str());
        std::printf("  after  : students=%s enroll=%s\n", st(g_students), st(g_enroll));
        peek->Stop();
        int enroll_touched = 0;
        { std::lock_guard<std::mutex> g(g_lm);
          for (auto& l : g_log) if (l == "  resolve: enroll") ++enroll_touched; }
        const bool ever = enroll_touched >= 2;   // once to acquire, once to release
        std::printf("\n  C0  enroll acquired then released (resolved %dx)  : %s\n",
                    enroll_touched,
                    ever ? "yes" : "NO -- the rollback test is vacuous");
        std::printf("  ROLLBACK: enroll released after the partial acquisition : %s\n",
                    xbase::locks::is_table_locked(g_enroll) ? "NO -- LEAKED" : "yes");
        std::fflush(stdout);
        wxTheApp->ExitMainLoop();
    });
    t->StartOnce(900);
}
