// R44: R21.4 at CONTAINER granularity, on a compiled target.
// Two panels, one worker in flight in each, separate lock domains so they really
// do overlap. Destroy P1. P2's completion must still arrive.
#include "uidef_rt.h"
#include <chrono>
#include <cstdio>
#include <thread>
#include <vector>

extern uidef::Runtime* g_rt;
extern wxWindow* g_scope_owner;

static std::vector<std::string> g_done;
static std::mutex g_dm;

void uidef_register(uidef::Runtime& rt) {
    rt.reg("Slow", [](uidef::Scope& sc) {
        for (int i = 0; i < 40; ++i) {
            if (sc.cancelled) return std::string("cancelled in ") + sc.name;
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
        return std::string("finished in ") + sc.name;
    });
    rt.comp("Done", [](uidef::Scope& sc, const std::string& r, const std::string& st) {
        std::lock_guard<std::mutex> g(g_dm);
        g_done.push_back(sc.name + " | " + r + " | " + st);
    });
}

static void report() {
    printf("\n  completions delivered:\n");
    { std::lock_guard<std::mutex> g(g_dm);
      if (g_done.empty()) printf("     (none)\n");
      for (auto& d : g_done) printf("     %s\n", d.c_str()); }
    printf("  runtime log:\n");
    bool dropped = false, survived = false;
    for (auto& l : g_rt->lines()) {
        printf("     %s\n", l.c_str());
        if (l.find("dropped") != std::string::npos && l.find("P1") != std::string::npos)
            dropped = true;
    }
    { std::lock_guard<std::mutex> g(g_dm);
      for (auto& d : g_done)
        if (d.find("P2") != std::string::npos && d.find("completed") != std::string::npos)
            survived = true; }
    printf("\n  R21.4  the destroyed container's work was dropped : %s\n",
           dropped ? "True" : "False");
    printf("  R21.4  the SURVIVING container's work completed   : %s\n",
           survived ? "True" : "False");
    wxTheApp->ExitMainLoop();
}

void uidef_after_init(wxWindow* frame) {
    auto* b1 = wxWindow::FindWindowByName("P1", frame);
    auto* b2 = wxWindow::FindWindowByName("P2", frame);
    printf("  found containers by name: P1=%s P2=%s\n", b1 ? "yes" : "NO", b2 ? "yes" : "NO");
    // Fire both buttons.
    for (const char* n : {"P1", "P2"}) {
        auto* p = wxWindow::FindWindowByName(n, frame);
        if (!p) continue;
        for (auto* c : p->GetChildren())
            if (auto* btn = dynamic_cast<wxButton*>(c)) {
                wxCommandEvent e(wxEVT_BUTTON, btn->GetId());
                e.SetEventObject(btn);
                btn->GetEventHandler()->ProcessEvent(e);
            }
    }
    // Destroy P1 while both are in flight, then let the rest run to completion.
    //
    // NOT via CallAfter + sleep: a completion is delivered BY CallAfter (R11.3),
    // so sleeping on the UI thread inside one starves the delivery it is waiting
    // for. The first version of this harness did exactly that and reported both
    // panels as failures -- a harness defect that looks identical to the defect
    // under test. Timers let the loop run.
    static wxTimer* t_kill = new wxTimer();
    static wxTimer* t_report = new wxTimer();
    t_kill->Bind(wxEVT_TIMER, [frame](wxTimerEvent&){
        printf("  destroying P1 while both handlers are in flight\n");
        auto* p1 = wxWindow::FindWindowByName("P1", frame);
        if (p1) p1->Destroy();
    });
    t_report->Bind(wxEVT_TIMER, [](wxTimerEvent&){ report(); });
    t_kill->StartOnce(120);
    t_report->StartOnce(1200);
}
