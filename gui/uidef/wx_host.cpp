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

#include <filesystem>

#include "xbase.hpp"
#include "xbase/cursor_hook.hpp"
#include "set_relations.hpp"
#include "common/path_state.hpp"

// The document's contribution to setup, emitted by uidef_wx.py --stream.
// Declared, not defined here: the host owns WHEN, the document owns WHAT.
void uidef_attach_source(xbase::XBaseEngine& eng);

// R83. WHICH tables, from the document's own SOURCE. Never where.
const std::vector<std::string>& uidef_source_tables();

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
namespace fs = std::filesystem;

// Contract section 10 resolves CASE-INSENSITIVELY (R28.3), and it is not
// decoration on a case-sensitive filesystem: the corpus writes `STUDENTS.DBF`
// and the file on disk is `STUDENTS.dbf`. Without this the host reports every
// table missing and the failure reads like a configuration problem.
fs::path resolve_ci(const fs::path& dir, const std::string& name) {
    std::error_code ec;
    fs::path exact = dir / name;
    if (fs::exists(exact, ec)) return exact;
    std::string low = name;
    for (char& c : low) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    for (fs::directory_iterator it(dir, ec), end; !ec && it != end; it.increment(ec)) {
        std::string have = it->path().filename().string();
        std::string hl = have;
        for (char& c : hl) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        if (hl == low) return it->path();
    }
    return exact;
}

// Where the tables are. R82: the DOCUMENT does not say, and this host must not
// invent it. Two sources, in the order the house itself uses -- the engine's
// own DBF slot first (what `SETPATH` and `DO X64` set, and what
// `WORKSPACE OPEN DBF` means), then an explicit override from the invocation.
//
// R82.3 is why the slot comes first: the house's answer to "name a location
// without hard-coding one" is that the INVOCATION names a slot. A frontend
// asking the same slot is asking the same question the shell asks.
fs::path table_root() {
    const fs::path slot = dottalk::paths::get_slot(dottalk::paths::Slot::DBF);
    if (!slot.empty()) return slot;
    if (const char* e = std::getenv("UIDEF_DBF_ROOT")) {
        if (*e) return fs::path(e);
    }
    return {};
}

// wxApp::OnInit runs after static initialization, so the host is up before the
// generated file constructs a stream.
//
// R83 replaced the UIDEF_TABLES environment variable this used to read. The
// tables a generated frontend opens now come from the document that generated
// it, which is what contract section 10 has always said and what this file's
// own comment asked for. Only the ROOT is still an input, because only the
// root is a workspace fact.
struct Boot {
    Boot() {
        const std::vector<std::string>& names = uidef_source_tables();
        if (names.empty()) return;          // the document declares no tables
        const fs::path root = table_root();
        if (root.empty()) {
            // Before R83 this returned in silence and the frontend came up with
            // every grid empty. `WORKSPACE LOAD` refuses a shortfall for this
            // reason -- "standing up empty areas over missing files is the
            // silent-success failure this codebase hunts" -- and a frontend that
            // does it quietly is the same failure with a window in front of it.
            std::cout << "uidef_host: the document declares " << names.size()
                      << " table(s) and NOTHING SAYS WHERE THEY ARE. The DBF path"
                      << " slot is unset and UIDEF_DBF_ROOT is not in the"
                      << " environment, so no area was opened and every bound"
                      << " control will be empty. Location is a workspace fact"
                      << " (AIF-120 R82).\n";
            return;
        }
        std::vector<std::string> t;
        t.reserve(names.size());
        for (const std::string& n : names) t.push_back(resolve_ci(root, n).string());
        if (uidef_host::begin(t)) {
            std::cout << "uidef_host: " << t.size() << " area(s) open from the "
                      << "document's SOURCE, cursor hook installed, "
                      << "SOURCE relations attached\n";
        }
    }
    ~Boot() { uidef_host::end(); }
} g_boot;
}
