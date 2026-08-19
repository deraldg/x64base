// R45: nested-container cancellation. AIF-120.
//
// F1 > G1(group) > { BG, PIN(panel) > BIN }, and F1 > PSIB(panel) > BSIB.
// Three disjoint work areas, so all three handlers overlap. Destroy the MIDDLE
// container. Its own work and its DESCENDANT's work must drop; the sibling's
// must complete. R44 proved one level; this is the level R44 said it had not.
#include "uidef_rt.h"
#include <chrono>
#include <cstdio>
#include <thread>
#include <vector>

extern uidef::Runtime* g_rt;

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

static void fire_all(wxWindow* w) {
    for (auto* c : w->GetChildren()) {
        if (auto* btn = dynamic_cast<wxButton*>(c)) {
            wxCommandEvent e(wxEVT_BUTTON, btn->GetId());
            e.SetEventObject(btn);
            btn->GetEventHandler()->ProcessEvent(e);
        }
        fire_all(c);
    }
}

static bool logged(const std::string& kind, const std::string& scope) {
    for (auto& l : g_rt->lines())
        if (l.find(kind) != std::string::npos && l.find(scope) != std::string::npos)
            return true;
    return false;
}

static bool delivered(const std::string& scope) {
    std::lock_guard<std::mutex> g(g_dm);
    for (auto& d : g_done)
        if (d.rfind(scope + " |", 0) == 0 && d.find("completed") != std::string::npos)
            return true;
    return false;
}

static std::string g_target = "G1";

static void report() {
    printf("\n  completions delivered:\n");
    { std::lock_guard<std::mutex> g(g_dm);
      if (g_done.empty()) printf("     (none)\n");
      for (auto& d : g_done) printf("     %s\n", d.c_str()); }
    printf("  runtime log:\n");
    for (auto& l : g_rt->lines()) printf("     %s\n", l.c_str());
    printf("\n  destroyed %s -- per-scope outcome:\n", g_target.c_str());
    for (const char* n : {"G1", "PIN", "PSIB"})
        printf("     %-5s dropped=%-5s completed=%s\n", n,
               logged("dropped", n) ? "True" : "False",
               delivered(n) ? "True" : "False");
    wxTheApp->ExitMainLoop();
}

void uidef_after_init(wxWindow* frame) {
    if (wxTheApp->argc > 1) g_target = std::string(wxTheApp->argv[1].mb_str());
    for (const char* n : {"G1", "PIN", "PSIB"})
        printf("  found %s: %s\n", n,
               wxWindow::FindWindowByName(n, frame) ? "yes" : "NO");
    fire_all(frame);
    static wxTimer* t_kill = new wxTimer();
    static wxTimer* t_report = new wxTimer();
    t_kill->Bind(wxEVT_TIMER, [frame](wxTimerEvent&){
            printf("  destroying %s while all three are in flight\n", g_target.c_str());
        // R45: not t->Destroy(). A group is a wxStaticBox its sizer owns, and
        // destroying the window directly then laying out is a segfault.
        if (!uidef::destroy_container(frame, g_target))
            printf("  no container named %s\n", g_target.c_str());
        frame->Layout();
    });
    t_report->Bind(wxEVT_TIMER, [](wxTimerEvent&){ report(); });
    t_kill->StartOnce(120);
    t_report->StartOnce(1200);
}
