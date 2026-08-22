// @dottalk.file v1
// subsystem: gui
// layer: registry
// owns: uidef_register / uidef_after_init
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: supported
// summary:
//   R46 -- page and pageset teardown; DeletePage destroys, RemovePage detaches
//
// notes:
//   Contract added 2026-08-22. This directory was promoted from lane to
//   project in 898a37b62 without them, so 14 of its 15 C++ files were
//   INVISIBLE to the doc pass -- not undocumented, invisible: the pass
//   completed and reported success while covering less than it claimed.

// R46: page and pageset teardown. AIF-120.
//
// F1 > PS(pageset) > { PG1 > BP1, PG2 > BP2 }, and F1 > PSIB > BSIB.
// A notebook page is a THIRD removal verb: DeletePage destroys the page window,
// RemovePage detaches it and leaves it alive. R45.2 says the lifetime rule must
// not depend on which verb the caller used -- but RemovePage is not a destruction
// at all, so the rule it must obey is the opposite one.
#include "uidef_rt.h"
#include <wx/notebook.h>
#include <chrono>
#include <cstdio>
#include <thread>
#include <vector>

extern uidef::Runtime* g_rt;

static std::vector<std::string> g_done;
static std::mutex g_dm;
static std::string g_mode = "delete:PG1";

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

static bool logged(const std::string& k, const std::string& s) {
    for (auto& l : g_rt->lines())
        if (l.find(k) != std::string::npos && l.find(s) != std::string::npos) return true;
    return false;
}
static bool delivered(const std::string& s) {
    std::lock_guard<std::mutex> g(g_dm);
    for (auto& d : g_done)
        if (d.rfind(s + " |", 0) == 0 && d.find("completed") != std::string::npos) return true;
    return false;
}

static void report(wxWindow* frame) {
    printf("  notebook page count after: %d\n",
           wxDynamicCast(wxWindow::FindWindowByName("PS", frame), wxNotebook)
             ? (int)wxDynamicCast(wxWindow::FindWindowByName("PS", frame), wxNotebook)->GetPageCount()
             : -1);
    printf("  mode %s -- per-scope outcome:\n", g_mode.c_str());
    for (const char* n : {"PS", "PG1", "PG2", "PSIB"})
        printf("     %-5s dropped=%-5s completed=%s\n", n,
               logged("dropped", n) ? "True" : "False",
               delivered(n) ? "True" : "False");
    wxTheApp->ExitMainLoop();
}

void uidef_after_init(wxWindow* frame) {
    if (wxTheApp->argc > 1) g_mode = std::string(wxTheApp->argv[1].mb_str());
    fire_all(frame);
    static wxTimer* t_kill = new wxTimer();
    static wxTimer* t_report = new wxTimer();
    t_kill->Bind(wxEVT_TIMER, [frame](wxTimerEvent&){
        auto verb = g_mode.substr(0, g_mode.find(':'));
        auto who  = g_mode.substr(g_mode.find(':') + 1);
        printf("  %s %s while all three are in flight\n", verb.c_str(), who.c_str());
        auto* nb = wxDynamicCast(wxWindow::FindWindowByName("PS", frame), wxNotebook);
        auto* w  = wxWindow::FindWindowByName(who, frame);
        if (verb == "remove" && nb && w) {
            for (size_t i = 0; i < nb->GetPageCount(); ++i)
                if (nb->GetPage(i) == w) { nb->RemovePage(i); break; }
            w->Hide();                      // detached, still alive
        } else {
            if (!uidef::destroy_container(frame, who))
                printf("  no container named %s\n", who.c_str());
        }
        frame->Layout();
    });
    t_report->Bind(wxEVT_TIMER, [frame](wxTimerEvent&){ report(frame); });
    t_kill->StartOnce(120);
    t_report->StartOnce(1200);
}
