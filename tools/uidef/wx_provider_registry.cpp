// R49: the C++ lock provider seam, under a grouping locale. AIF-120.
//
// R48 proved what the PYTHON runtime says to the engine. The C++ seam was seven
// lines and untested, and worse, asymmetric: it handed the target a list of
// aliases and let the target write the commands, so R48.2's "the runtime never
// renders a number" was not a rule this target had. uidef::lock_provider moves the
// verbs into the runtime; this exercises them where AIF-116 lives.
#include "uidef_rt.h"
#include <cstdio>
#include <locale>
#include <sstream>
#include <string>
#include <vector>

extern uidef::Runtime* g_rt;

struct Grouping : std::numpunct<char> {
    char do_thousands_sep() const override { return ','; }
    std::string do_grouping()  const override { return "\3"; }
};

static std::vector<std::string> g_cmds;
static std::string g_refuse;                 // a command the fake engine says no to

static bool sink(const std::string& cmd) {
    g_cmds.push_back(cmd);
    return !(!g_refuse.empty() && cmd == g_refuse);
}

void uidef_register(uidef::Runtime&) {}

static std::string join(const std::vector<std::string>& v) {
    std::string s;
    for (size_t i = 0; i < v.size(); ++i) { if (i) s += " ; "; s += v[i]; }
    return s.empty() ? std::string("(none)") : s;
}

static bool no_rendered_digits() {
    for (const auto& c : g_cmds) {
        if (c.compare(0, 7, "SELECT ") == 0) continue;   // the alias is the document's
        for (char ch : c) if (isdigit((unsigned char)ch)) return false;
    }
    return true;
}

static void run_all(wxWindow* frame) {
    // AIF-116's runtime condition, set GLOBALLY -- exactly how the engine's own
    // un-imbued stream picked it up.
    std::locale::global(std::locale(std::locale::classic(), new Grouping));
    { std::ostringstream probe; probe << 16984;
      printf("  grouping locale is active : an un-imbued stream writes %s\n",
             probe.str().c_str()); }

    bool all = true;
    const std::vector<std::string> domain{"students", "enroll"};   // R26's closure

    for (int record = 0; record < 2; ++record) {
        g_cmds.clear(); g_refuse.clear();
        auto p = uidef::lock_provider(sink, record != 0);
        bool got = p(true, domain);
        std::vector<std::string> acq = g_cmds;
        g_cmds.clear();
        p(false, domain);
        const char* label = record ? "record" : "table ";
        printf("  %s acquire : %s\n", label, join(acq).c_str());
        printf("  %s release : %s\n", label, join(g_cmds).c_str());
        const std::string verb = record ? "LOCK" : "LOCK TABLE";
        bool ok = got && acq.size() == 4 && acq[0] == "SELECT enroll" && acq[1] == verb
                  && acq[2] == "SELECT students" && acq[3] == verb
                  && g_cmds.size() == 4 && g_cmds[0] == "SELECT students"
                  && g_cmds[1] == "UNLOCK" && g_cmds[3] == "UNLOCK";
        all = all && ok;
    }

    // All-or-nothing: refuse the SECOND area, the first must be released.
    g_cmds.clear();
    g_refuse.clear();
    int seen = 0;
    auto counting = [&seen](const std::string& cmd) {
        g_cmds.push_back(cmd);
        if (cmd == "LOCK TABLE") return ++seen == 1;     // first ok, second refused
        return true;
    };
    auto p2 = uidef::lock_provider(counting);
    bool second = p2(true, domain);
    int unlocks = 0;
    for (auto& c : g_cmds) if (c == "UNLOCK") ++unlocks;
    printf("  rollback       : returned %s, rolled back %d lock(s)  (%s)\n",
           second ? "true" : "false", unlocks, join(g_cmds).c_str());
    bool roll_ok = !second && unlocks == 1;

    bool digits_ok = no_rendered_digits();
    printf("  runtime-rendered numbers in any command : %s\n",
           digits_ok ? "none" : "PRESENT");

    // A provider that says no must REFUSE the handler, not run it anyway. This is
    // the case the Python suite has that this one did not, and it is the only one
    // that reaches through the provider into dispatch.
    static bool ran = false;
    static std::string state_seen;
    static uidef::Runtime rt(frame, {{"students", "enroll"}});
    rt.set_lock_provider(uidef::lock_provider(
        [](const std::string& cmd) { return cmd.compare(0, 4, "LOCK") != 0; }));
    rt.reg("H", [](uidef::Scope&) { ran = true; return std::string("ok"); });
    rt.comp("Done", [](uidef::Scope&, const std::string&, const std::string& st) {
        state_seen = st; });
    rt.fire("H", "worker", std::make_shared<uidef::Scope>("W"), "students", "Done");

    static wxTimer* t = new wxTimer();
    t->Bind(wxEVT_TIMER, [all, roll_ok, digits_ok](wxTimerEvent&){
        bool refuse_ok = !ran && state_seen == "refused";
        printf("  engine refuses : handler ran=%s  completion state=%s\n",
               ran ? "true" : "false",
               state_seen.empty() ? "(none)" : state_seen.c_str());
        printf("\n  %-36s : %s\n", "verbs and order (both granularities)", all ? "True" : "False");
        printf("  %-36s : %s\n", "all-or-nothing rollback", roll_ok ? "True" : "False");
        printf("  %-36s : %s\n", "no runtime-rendered numbers", digits_ok ? "True" : "False");
        printf("  %-36s : %s\n", "engine refusal refuses the handler", refuse_ok ? "True" : "False");
        fflush(stdout);
        wxTheApp->ExitMainLoop();
    });
    t->StartOnce(400);
}

void uidef_after_init(wxWindow* frame) {
    // NOT called directly. uidef_after_init runs from inside OnInit, BEFORE the
    // main loop exists, so ExitMainLoop() there is a no-op and the app runs
    // forever -- with every printf still sitting in a block-buffered stdout, so
    // the harness looks like it produced nothing at all. Queue the work instead:
    // CallAfter runs it once the loop is actually going.
    frame->CallAfter([frame]{ run_all(frame); });   // run_all owns the exit
}
