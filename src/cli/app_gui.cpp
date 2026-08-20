// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: application-ui-dsl
// owner: member.derald
// status: supported

// app_gui.cpp -- launch the windowed GUI from the shell.
//
// usage:
//   GUI
//   APPGUI
//   APPGUI <document>
//
//   Both keys are bound to this symbol in shell_commands.cpp (:178, :199).
//   The body does not care which one the user typed.
//
// notes:
//   The windowed GUI is a SEPARATE EXECUTABLE (`dottalk_wx`, built by
//   src/gui/wx/CMakeLists.txt behind DOTTALK_WITH_WX, OFF by default). dottalkpp
//   does not link wxWidgets, so this command launches a process; it does not
//   create a window in this one. That is deliberate and it is the existing
//   shape, not a shortcut -- putting a wxApp event loop inside the CLI process
//   would put a second UI thread beside the shell's, which is exactly what the
//   threading contract in docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md governs.
//
//   With no argument the GUI opens on the current workspace. With a document
//   argument the intent is a UIDEF-generated frontend; that target is not in
//   this build and the command SAYS SO rather than silently ignoring the word.
//
//   A GUI that is not in the build is reported by NAME, with every path that
//   was tried. Same choice `cmd_palette_stub` makes for PALETTE: a missing
//   feature answers, it does not vanish.
//
// risk:
//   reads_files: yes (probes for the GUI executable)
//   executes_commands: no
//   launches_external_process: yes -- gated by identity permission `app.gui`
//   mutates_data: no
//   mutates_session: no
//   writes_files: no

#include "cli/command_output.hpp"
#include "shell_commands.hpp"
#include "identity/identity_admin.hpp"
#include "common/path_state.hpp"
#include "textio.hpp"
#include "xbase.hpp"

#include <filesystem>
#include <sstream>
#include <string>
#include <vector>

namespace {

namespace fs = std::filesystem;

#ifdef _WIN32
constexpr const char* kExeSuffix = ".exe";
#else
constexpr const char* kExeSuffix = "";
#endif

// Both are built from the same source list by src/gui/wx/CMakeLists.txt:44-45.
// `dottalk_wx` first: `_next` is the forward target and a tree that has both
// should launch the one the rest of the product means by "the GUI".
const char* const kGuiExecutables[] = {"dottalk_wx", "dottalk_wx_next"};

std::string upper_token(std::istringstream& iss)
{
    std::string tok;
    iss >> tok;
    return textio::up(tok);
}

/// Every place a GUI executable could reasonably be, in probe order.
/// Returned rather than assumed: when nothing is found the caller prints this
/// list, so "not installed" is a statement with evidence behind it.
std::vector<fs::path> candidate_paths()
{
    std::vector<fs::path> out;
    std::error_code ec;

    const fs::path bin = dottalk::paths::get_slot(dottalk::paths::Slot::BIN);
    for (const char* name : kGuiExecutables) {
        if (!bin.empty()) {
            out.push_back(bin / (std::string(name) + kExeSuffix));
        }
    }
    // A developer tree builds the GUI under its own target directory rather than
    // beside dottalkpp. Probed second so an installed product always wins.
    if (!bin.empty()) {
        for (const char* name : kGuiExecutables) {
            out.push_back(bin / "gui" / "wx" / (std::string(name) + kExeSuffix));
        }
    }
    (void)ec;
    return out;
}

fs::path first_existing(const std::vector<fs::path>& candidates)
{
    std::error_code ec;
    for (const auto& p : candidates) {
        if (fs::exists(p, ec) && !ec && fs::is_regular_file(p, ec) && !ec) {
            return p;
        }
    }
    return {};
}

/// Launch without blocking the shell. A GUI that holds the prompt hostage until
/// the window closes is not a GUI the shell can sit beside, and the shell is the
/// thing the user came back to.
void launch_detached(const fs::path& exe)
{
#ifdef _WIN32
    const std::string cmd = "start \"\" \"" + exe.string() + "\"";
#else
    const std::string cmd = "\"" + exe.string() + "\" &";
#endif
    std::system(cmd.c_str());
}

} // namespace

void app_GUI(DbArea& /*area*/, std::istringstream& iss)
{
    // Tolerate both wirings. Registered as APPGUI the stream is empty here;
    // registered as APP with GUI as a subcommand the first token is GUI. The
    // handler should not care which one the shell chose, and if a THIRD verb is
    // ever added under APP this is where it is refused by name rather than
    // silently treated as a document.
    std::string tok = upper_token(iss);
    if (tok == "GUI") {
        tok = upper_token(iss);
    }

    // AIF-045 identity, not the host-shell policy. `app.gui` is resource class
    // "app", so agent_permitted() does NOT consult DOTTALK_ALLOW_HOST_COMMANDS
    // (identity_admin.cpp:463-468) and the owner is exempt outright (:453). The
    // console operator gets the window; a non-owner agent needs a live grant and
    // is refused BY NAME with the stage that denied it.
    //
    // Deliberately NOT also calling authorize_external_process(). BANG needs
    // both because `host.shell` runs an arbitrary user string; this launches one
    // verified first-party binary out of Slot::BIN, and demanding the shell door
    // for it would make a user enable arbitrary command execution to open their
    // own GUI.
    {
        const dottalk::identity::Decision d =
            dottalk::identity::agent_permitted("app.gui");
        if (!d.allowed()) {
            cli::cmdout::print_line(
                "APPGUI: refused for " + dottalk::identity::acting_member_key() +
                " -- " + d.reason);
            return;
        }
    }

    const std::vector<fs::path> candidates = candidate_paths();
    const fs::path exe = first_existing(candidates);

    if (exe.empty()) {
        cli::cmdout::print_line(
            "APPGUI: the windowed GUI is not present in this build.");
        cli::cmdout::print_line(
            "APPGUI: it is built by DOTTALK_WITH_WX, which is OFF by default "
            "(src/CMakeLists.txt:6).");
        for (const auto& p : candidates) {
            cli::cmdout::print_line("APPGUI:   looked for " + p.string());
        }
        return;
    }

    if (!tok.empty()) {
        // R12/R83: a UIDEF document names its own tables and its own layout, and
        // a frontend generated from one is a DIFFERENT executable from the
        // shipped GUI. Refusing by name costs one line; accepting the word and
        // ignoring it would make the command lie about what it launched.
        cli::cmdout::print_line(
            "APPGUI: refused document '" + tok +
            "' -- this build launches the shipped GUI only. A UIDEF-generated "
            "frontend is a separate target (gui/uidef/CMakeLists.txt) and is "
            "not wired to this command.");
        return;
    }

    cli::cmdout::print_line("APPGUI: launching " + exe.string());
    launch_detached(exe);
}

// NOT registered here. `shell_commands.cpp` already binds this symbol twice --
// "GUI" (:178) and "APPGUI" (:199) -- through the house wrapping lambda, and
// `shell_commands.hpp:43` declares it. A self-registering block in this file
// would be a third opinion about the command's name, in the one place nobody
// would look for it.
