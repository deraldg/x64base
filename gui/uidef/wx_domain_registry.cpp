// @dottalk.file v1
// subsystem: gui
// layer: registry
// owns: uidef_register / uidef_after_init
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: supported
// summary:
//   R59 -- a RELATION-SET domain acquired through the engine
//
// notes:
//   Contract added 2026-08-22. This directory was promoted from lane to
//   project in 898a37b62 without them, so 14 of its 15 C++ files were
//   INVISIBLE to the doc pass -- not undocumented, invisible: the pass
//   completed and reported success while covering less than it claimed.

// AIF-120 R59 -- a RELATION-SET domain acquired through the engine, and a handler
// that WRITES under the lock it holds.
//
// Build and run (needs wx AND the engine archives):
//
//   B=build/wsl-core-vcpkg
//   cp dottalkpp/data/dbf/vfp/STUDENTS.dbf /tmp/d_STUDENTS.dbf
//   cp dottalkpp/data/dbf/vfp/ENROLL.dbf   /tmp/d_ENROLL.dbf
//   python3 gui/uidef/uidef_wx.py DOMAIN.DBF /tmp/dom.cpp --dispatch
//   g++ -std=c++17 -Wall -Wextra -Iinclude -I$B/generated -Igui/uidef \
//       /tmp/dom.cpp gui/uidef/wx_domain_registry.cpp \
//       $B/src/xbase/libxbase.a $B/src/memo/libmemo.a $B/src/xexpr/libxexpr.a \
//       $B/src/libdottalk_value.a $B/src/libdottalk_inx_payload.a \
//       -o /tmp/dom $(wx-config --cxxflags --libs) -pthread
//   xvfb-run -a /tmp/dom
//
// It WRITES to d_STUDENTS.dbf, so both tables are copies.
//
// R58 proved the chain with one area and a read. The two cases that were left are
// the ones R26 and R57.2 are actually about:
//   A. the domain is the transitive closure -- acquiring it must lock BOTH areas
//   B. a handler writing under a TABLE lock must still hold it afterwards
//      (R57.2 proved the record case is destroyed by DbArea's own unlock; the
//       table case was proven in a probe, never through a generated frontend)
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
static void say(const std::string& s) { std::lock_guard<std::mutex> g(g_lm); g_log.push_back(s); }

static std::string lockstate(const char* nm, xbase::DbArea& a) {
    std::string who;
    const bool held = xbase::locks::is_table_locked(a, &who);
    return std::string(nm) + "=" + (held ? "LOCKED" : "free");
}

void uidef_register(uidef::Runtime& rt) {
    // A -- what does the handler actually hold?
    rt.reg("ReadBoth", [](uidef::Scope&) {
        say("  during ReadBoth : " + lockstate("students", g_students) +
            "  " + lockstate("enroll", g_enroll));
        return std::to_string(g_students.recCount64()) + "/" +
               std::to_string(g_enroll.recCount64());
    });
    // B -- write under the domain lock, then look again.
    rt.reg("WriteOne", [](uidef::Scope&) {
        g_students.gotoRec64(1);
        std::string werr;
        const bool ok = g_students.replaceFieldStored(1, std::string("Z"), &werr);
        say("  WriteOne write  : " + std::string(ok ? "ok" : "FAILED " + werr));
        say("  after the write : " + lockstate("students", g_students) +
            "  " + lockstate("enroll", g_enroll));
        return std::string(ok ? "wrote" : "failed");
    });
    rt.comp("Done", [](uidef::Scope&, const std::string& r, const std::string& st) {
        say("  completion      : " + st + " result=" + r);
    });
}

void uidef_after_init(wxWindow* frame) {
    (void)frame;
    g_students.open("/tmp/d_STUDENTS.dbf");
    g_enroll.open("/tmp/d_ENROLL.dbf");
    std::printf("open             : students=%s enroll=%s\n",
                g_students.isOpen() ? "ok" : "FAILED",
                g_enroll.isOpen() ? "ok" : "FAILED");
    if (!g_students.isOpen() || !g_enroll.isOpen()) { wxTheApp->ExitMainLoop(); return; }

    g_rt->set_lock_provider(uidef::xbase_lock_provider(
        [](const std::string& alias) -> xbase::DbArea* {
            if (alias == "students") return &g_students;
            if (alias == "enroll")   return &g_enroll;
            return nullptr;
        },
        false,
        [](const std::string& m) { say("  provider        : " + m); }));

    std::printf("before any handler: %s  %s\n",
                lockstate("students", g_students).c_str(),
                lockstate("enroll", g_enroll).c_str());

    g_rt->fire("ReadBoth", "worker", g_scope, "students", "Done");

    static wxTimer* t2 = new wxTimer();
    t2->Bind(wxEVT_TIMER, [](wxTimerEvent&) {
        say("--- second handler, on the OTHER alias of the same domain ---");
        g_rt->fire("WriteOne", "worker", g_scope, "enroll", "Done");
    });
    t2->StartOnce(500);

    static wxTimer* t3 = new wxTimer();
    t3->Bind(wxEVT_TIMER, [](wxTimerEvent&) {
        { std::lock_guard<std::mutex> g(g_lm);
          for (auto& l : g_log) std::printf("%s\n", l.c_str()); }
        std::printf("after everything  : %s  %s\n",
                    lockstate("students", g_students).c_str(),
                    lockstate("enroll", g_enroll).c_str());
        std::fflush(stdout);
        wxTheApp->ExitMainLoop();
    });
    t3->StartOnce(1400);
}
