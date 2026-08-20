// @dottalk.file v1
// subsystem: gui
// layer: host
// owns:
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: supported

// gui/uidef/wx_host.cpp -- AIF-120 R72. The host a generated wx frontend runs in.
//
// This is `run_shell()` MINUS THE REPL. Read src/cli/shell.cpp:506-550 beside it:
// every call below appears there, in that order, because the host contract was
// already written -- it was just written inside a function whose other two thirds
// are a terminal loop. The three parts of run_shell() are
//
//     506-550   host setup      <- this file
//     551-769   the REPL        <- wxWidgets replaces this
//     770-789   teardown        <- this file, symmetric
//
// R70's harness did the first third badly and the third not at all: it leaked a
// function-static engine, never detached the cursor hook, and left DbTupleStream
// objects holding cursor state into static destruction. run_shell() unwinds in
// the exact reverse order and this file follows it.
//
// PRIOR ART, and the reason this is an adoption rather than an invention:
// src/tv/foxtalk_app.cpp:469 and src/tv/cmd_foxpro.cpp:568 already host this
// engine from a non-CLI frontend, and both pass include_ui_cmds=false --
// a frontend with its own UI does not want the shell's UI launchers.
//
// WHAT THIS HOST DELIBERATELY DOES NOT DO, and what it would cost:
//   register_shell_commands(eng, false)  -- the command surface, and where the
//   command ALIASES live (src/cli/shell_commands.cpp:314, 517, 549). The main
//   shell loads them; a frontend that wants to dispatch command text calls the
//   same function rather than re-declaring anything. Text dispatch also owes
//   expand_shortcut_lead() first (shell.cpp:682 -> shell_shortcuts::resolve),
//   because SHORTCUTS are a separate mechanism from ALIASES: a shortcut rewrites
//   the leading token before dispatch, an alias is a second registered name.
//   Measured link cost of adding the command surface is in the ruling; it is not
//   small, and a grid does not need it. See AIF120_HOST_CONTRACT_V1.md.

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xbase/cursor_hook.hpp"
#include "set_relations.hpp"

// The document's contribution to setup, emitted by uidef_wx.py --stream.
// Declared, not defined here: the host owns WHEN, the document owns WHAT.
void uidef_attach_source(xbase::XBaseEngine& eng);

namespace {

xbase::XBaseEngine* g_engine = nullptr;

// shell.cpp:339. The engine tells the host the cursor moved; the host refreshes
// the relation set. A GUI grid repaints its detail/summary/statusbar from the
// same signal -- this is why selection-follows-record needs no new mechanism.
void on_cursor_changed(xbase::DbArea& moved, const char* /*reason*/,
                       void* user) noexcept {
    auto* eng = static_cast<xbase::XBaseEngine*>(user);
    if (!eng) return;
    try {
        xbase::DbArea* cur = eng->areaPtr(eng->currentArea());
        if (!cur || cur != &moved) return;
    } catch (...) { return; }
    relations_api::refresh_if_enabled();
}

} // namespace

extern "C" xbase::XBaseEngine* shell_engine() { return g_engine; }

namespace uidef_host {

// run_shell() 506-550, in its order.
bool begin(const std::vector<std::string>& tables) {
    static xbase::XBaseEngine eng;
    g_engine = &eng;
    eng.selectArea(0);

    xbase::cursor_hook::set_callback(&on_cursor_changed, &eng);

    for (std::size_t i = 0; i < tables.size(); ++i) {
        try {
            eng.selectArea(static_cast<int>(i));
            eng.area(static_cast<int>(i)).open(tables[i]);
        } catch (const std::exception& e) {
            std::cout << "uidef_host: open failed for " << tables[i]
                      << ": " << e.what() << "\n";
            return false;
        }
    }
    eng.selectArea(0);

    // The document's SOURCE graph. relations_api::attach_engine happens inside,
    // because the generated function is what knows which engine the document
    // was written against.
    uidef_attach_source(eng);
    return true;
}

// run_shell() 770-789, reversed. uidef_detach_source() is the generated half and
// runs from wxApp::OnExit; this is the engine half.
void end() {
    xbase::cursor_hook::set_callback(nullptr, nullptr);
    g_engine = nullptr;
}

} // namespace uidef_host

namespace {
// wxApp::OnInit runs after static initialization, so the host is up before the
// generated file constructs a stream. UIDEF_TABLES is the demo's stand-in for
// what a real host reads out of the document's SOURCE.
struct Boot {
    Boot() {
        const char* dir = std::getenv("R70_DBF");
        const char* csv = std::getenv("UIDEF_TABLES");
        if (!dir || !*dir) return;
        std::vector<std::string> t;
        std::string s(csv && *csv ? csv : "STUDENTS,ENROLL"), tok;
        for (char c : s) {
            if (c == ',') { if (!tok.empty()) t.push_back(tok); tok.clear(); }
            else tok += c;
        }
        if (!tok.empty()) t.push_back(tok);
        for (auto& n : t) n = std::string(dir) + "/" + n + ".dbf";
        if (uidef_host::begin(t)) {
            std::cout << "uidef_host: " << t.size() << " area(s) open, "
                      << "cursor hook installed, SOURCE relations attached\n";
        }
    }
    ~Boot() { uidef_host::end(); }
} g_boot;
}
