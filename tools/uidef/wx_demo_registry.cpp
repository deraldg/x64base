// What a TARGET supplies: handler bodies by name (R14), a host capability table,
// and its own entry point. The generated file references these and defines none.
#include "uidef_rt.h"
#include <chrono>
#include <cstdio>
#include <thread>
#include <vector>

static std::vector<std::string> g_order;
static std::mutex g_om;
static void mark(const std::string& s) {
    std::lock_guard<std::mutex> g(g_om);
    g_order.push_back(s + (wxThread::IsMain() ? "  [UI]" : "  [worker]"));
}

void uidef_register(uidef::Runtime& rt) {
    rt.reg("TotalGpa", [](uidef::Scope&) {
        mark("TotalGpa enter");
        std::this_thread::sleep_for(std::chrono::milliseconds(150));
        mark("TotalGpa leave");
        return std::string("588.74");
    });
    rt.reg("ListEnrolments", [](uidef::Scope&) {
        mark("ListEnrolments enter");
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        mark("ListEnrolments leave");
        return std::string("5 rows");
    });
    rt.comp("Done", [](uidef::Scope&, const std::string& r, const std::string& st) {
        mark("Done " + st + " (" + r + ")");
    });
    rt.host("edit.cut", [] { mark("host edit.cut"); });
}

extern uidef::Runtime* g_rt;

void uidef_after_init(wxWindow* frame) {
    // Click every button, in order, the way a user would.
    std::vector<wxButton*> btns;
    std::function<void(wxWindow*)> walk = [&](wxWindow* w) {
        for (auto* c : w->GetChildren()) {
            if (auto* b = dynamic_cast<wxButton*>(c)) btns.push_back(b);
            walk(c);
        }
    };
    walk(frame);
    for (auto* b : btns) {
        wxCommandEvent e(wxEVT_BUTTON, b->GetId());
        e.SetEventObject(b);
        b->GetEventHandler()->ProcessEvent(e);
    }
    frame->GetEventHandler()->CallAfter([frame] {
        wxTheApp->CallAfter([frame] {
            // let the workers finish, then print and quit
            std::thread([frame] {
                std::this_thread::sleep_for(std::chrono::milliseconds(900));
                wxTheApp->CallAfter([] {
                    std::lock_guard<std::mutex> g(g_om);
                    printf("  handler timeline:\n");
                    for (auto& s : g_order) printf("     %s\n", s.c_str());
                    printf("\n  runtime log:\n");
                    for (auto& s : g_rt->lines()) printf("     %s\n", s.c_str());
                    wxTheApp->ExitMainLoop();
                });
            }).detach();
        });
    });
}
