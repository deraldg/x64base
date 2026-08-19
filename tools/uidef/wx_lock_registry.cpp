// R47: lock semantics on the compiled target. AIF-120.
// Same four cases as tools/uidef/deadlock_test.py, on std::thread/std::mutex.
#include "uidef_rt.h"
#include <chrono>
#include <cstdio>
#include <thread>
#include <vector>

extern uidef::Runtime* g_rt;
extern std::shared_ptr<uidef::Scope> g_scope;

static std::mutex g_m;
static std::vector<std::string> g_marks;
static void mark(const std::string& s) { std::lock_guard<std::mutex> g(g_m); g_marks.push_back(s); }

static std::mutex g_bm;
static std::condition_variable g_bcv;
static int g_barrier = 0;
static void rendezvous() {                     // both hold one domain before either wants two
    std::unique_lock<std::mutex> lk(g_bm);
    if (++g_barrier >= 2) { g_bcv.notify_all(); return; }
    g_bcv.wait_for(lk, std::chrono::milliseconds(800), []{ return g_barrier >= 2; });
}

void uidef_register(uidef::Runtime& rt) {
    rt.reg("Inner", [](uidef::Scope&) { mark("inner ran"); return std::string("inner"); });
    rt.reg("AB", [&rt](uidef::Scope& sc) {
        rendezvous();
        rt.fire("Inner", "ui", g_scope, "b", "");
        return std::string("AB returned");
    });
    rt.reg("BA", [&rt](uidef::Scope& sc) {
        rendezvous();
        rt.fire("Inner", "ui", g_scope, "a", "");
        return std::string("BA returned");
    });
    rt.reg("Slow", [](uidef::Scope&) {
        mark("slow enter");
        std::this_thread::sleep_for(std::chrono::milliseconds(250));
        mark("slow leave");
        return std::string("slow");
    });
    rt.comp("Done", [](uidef::Scope&, const std::string& r, const std::string& st) {
        mark("complete " + st + " (" + r + ")");
    });
}

static void report(const char* label) {
    printf("  %s\n", label);
    { std::lock_guard<std::mutex> g(g_m);
      for (auto& m : g_marks) printf("     %s\n", m.c_str()); }
    printf("  runtime log:\n");
    for (auto& l : g_rt->lines()) printf("     %s\n", l.c_str());
}

void uidef_after_init(wxWindow* frame) {
    std::string mode = wxTheApp->argc > 1
        ? std::string(wxTheApp->argv[1].mb_str()) : std::string("abba");
    if (mode == "abba") {
        g_rt->fire("AB", "worker", g_scope, "a", "Done");
        g_rt->fire("BA", "worker", g_scope, "b", "Done");
    } else {                                    // contention on ONE domain
        g_rt->fire("Slow", "worker", g_scope, "a", "Done");
        static wxTimer* t = new wxTimer();
        t->Bind(wxEVT_TIMER, [](wxTimerEvent&){
            g_rt->fire("Slow", "worker", g_scope, "a", "Done"); });
        t->StartOnce(50);
    }
    static wxTimer* t_report = new wxTimer();
    t_report->Bind(wxEVT_TIMER, [mode](wxTimerEvent&){
        report(mode == "abba" ? "AB-BA:" : "contention on one domain:");
        wxTheApp->ExitMainLoop(); });
    t_report->StartOnce(1500);
}
