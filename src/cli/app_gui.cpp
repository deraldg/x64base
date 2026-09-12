// @dottalk.file v1
// subsystem: cli
// layer: command
// owns:
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

// src/cli/app_gui.cpp
// -----------------------------------------------------------------------------
// Launch the windowed GUI from the shell.
//
// The windowed GUI is a SEPARATE EXECUTABLE (`dottalk_wb`, built by
// src/gui/wx/CMakeLists.txt behind DOTTALK_WITH_WX, OFF by default). dottalkpp
// does not link wxWidgets, so this command launches a process; it does not
// create a window in this one. That is deliberate: a wxApp event loop inside
// the CLI process would stand a second UI thread beside the shell's, which is
// what docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md governs.
//
// Registration is orthogonal to the Turbo Vision block in shell_commands.cpp:
// that block gates on DOTTALK_TV_AVAILABLE, and this is the wx surface. There is
// no compile-time flag to gate on here because the CLI never links wx -- and a
// gated-away command answers "Unknown command", which tells a user nothing. The
// command always exists and reports what it found. That is the house pattern:
// SQLITE is registered unconditionally (shell_commands.cpp:442) and answers
// "not available in this build (DOTTALK_SQLITE_AVAILABLE=0)" at run time from
// src/cli/cmd_sqlite.cpp:705 rather than vanishing from the registry.
// -----------------------------------------------------------------------------

// @dottalk.usage v1
// owner: DOT|APPGUI
// command: APPGUI
// aliases: GUI
// category: gui
// status: supported
// noargs: launch
// effect: launch-ui-or-report
// mutates: none
// usage-access: APPGUI USAGE
// summary:
//   Launch the windowed Workbench GUI -- `dottalk_wb`, built with wxWidgets --
//   as a separate process, or report by name why it cannot be launched.
//
//   The binary is named here on purpose. It was `dottalk_wx` until 2026-08-22,
//   and a contract that describes a command only by its toolkit cannot answer
//   the first question a reader has, which is what gets started. The BUILD
//   SWITCH is still DOTTALK_WITH_WX and is correct: that gates wxWidgets, not
//   the product.
//
// usage:
//   APPGUI
//   APPGUI USAGE
//
// examples:
//   APPGUI
//   GUI
//   APPGUI USAGE
//
// notes:
//   Authorized by identity permission `app.gui` (resource class "app", NOT
//   "host"), so it does not require DOTTALK_ALLOW_HOST_COMMANDS. The owner is
//   exempt; any other member needs the permission through a role or a grant.
//   A refusal names the acting member and the stage that denied it.
//   The GUI executable's declared home is the GUI path slot (SETPATH GUI),
//   root-relative and beside the product. When the GUI is absent the command
//   names DOTTALK_WITH_WX and lists every path it probed, each tagged with
//   where that path came from.
//   A document argument is refused by name: a UIDEF-generated frontend is a
//   separate target (gui/uidef/CMakeLists.txt) and is not wired to this command.
//
// risk:
//   launches_external_process: yes -- one first-party executable, no shell string
//   reads_files: yes -- probes for the GUI executable
//   mutates_data: no
//   mutates_session: no
//   writes_files: no
//
// related:
//   SIMPLEBROWSER
//   SMARTBROWSER
//   WORKSPACE

// @dottalk.location v1
// id: DOTSRC-DOTTALKPP-CLI-APP-GUI
// home: src/cli
// canonical-path: src/cli/app_gui.cpp
// project: dottalkpp
// role: command-implementation
// @dottalk.end

#include "cli/command_output.hpp"
#include "shell_commands.hpp"
#include "identity/identity_admin.hpp"
#include "common/path_state.hpp"
#include "textio.hpp"
#include "xbase.hpp"

#include <filesystem>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace {

namespace fs = std::filesystem;

#ifdef _WIN32
constexpr const char* kExeSuffix = ".exe";
#else
constexpr const char* kExeSuffix = "";
#endif

// Both are built from the same source list by src/gui/wx/CMakeLists.txt:54-55.
// `dottalk_wb` first: `_next` is the forward target and a tree that has both
// should launch the one the rest of the product means by "the GUI".
const char* const kGuiExecutables[] = {"dottalk_wb", "dottalk_wb_next"};

std::string upper_token(std::istringstream& iss)
{
    std::string tok;
    iss >> tok;
    return textio::up(tok);
}

/// Every place a GUI executable could reasonably be, in probe order, PAIRED
/// with where the idea came from.
///
/// R89. The first version asked `get_slot(Slot::BIN)` and nothing else, and it
/// came back EMPTY -- so the probe list was empty, the loop that prints it ran
/// zero times, and the command reported "not present in this build" having
/// looked nowhere. A diagnostic that can be empty is worse than no diagnostic:
/// it is a confident answer with no evidence under it.
///
/// The reason the slot is empty is worth writing down, because the banner says
/// otherwise. `INIT: Paths` prints `BIN` from `get_executable_dir()`
/// (cmd_init.cpp:287), NOT from `get_slot(Slot::BIN)`. Nothing in the CLI ever
/// calls `initialize_from_bin()`, so `state().bin_root` is never populated and
/// the two disagree. That is AIF-120 R82.1 again -- a hand-maintained printer
/// showing a value the slot does not hold -- and it is reported to the engine
/// lane rather than fixed here, because `set_slot(Slot::BIN, ...)` re-runs
/// `build_all_paths()` and that is not a side effect to introduce untested.
///
/// So DATA is used as the anchor instead. It is populated, and
/// `initialize_from_bin()` itself defines the relationship in reverse:
/// bin/../data. Reading it forwards -- data/../bin -- is the same fact.
std::vector<std::pair<std::string, fs::path>> candidate_paths()
{
    std::vector<std::pair<std::string, fs::path>> out;
    std::vector<std::pair<std::string, fs::path>> roots;

    // Slot::GUI is the DECLARED home: root-relative, beside the product, set by
    // init_defaults and re-rooted by SETPATH along with everything else. A path
    // the product declares is one this command can only report; a path it derives
    // is one it can get wrong.
    const fs::path gui = dottalk::paths::get_slot(dottalk::paths::Slot::GUI);
    if (!gui.empty()) {
        roots.emplace_back("Slot::GUI", gui);
    }

    // Kept as fallbacks, and ordered after the declaration on purpose. BIN exists
    // in the enum but nothing in the CLI populates it -- `INIT: Paths` prints a
    // BIN line computed from get_executable_dir() (cmd_init.cpp:287), not from
    // this slot, so the banner and the slot disagree. Probed anyway: if it is
    // ever populated it is authoritative, and if it is not, the tag says so.
    const fs::path bin = dottalk::paths::get_slot(dottalk::paths::Slot::BIN);
    if (!bin.empty()) {
        roots.emplace_back("Slot::BIN", bin);
    }

    const fs::path data = dottalk::paths::get_slot(dottalk::paths::Slot::DATA);
    if (!data.empty() && data.has_parent_path()) {
        roots.emplace_back("Slot::DATA/../bin", data.parent_path() / "bin");
    }

    std::error_code ec;
    const fs::path cwd = fs::current_path(ec);
    if (!ec && !cwd.empty()) {
        roots.emplace_back("current directory", cwd);
    }

    for (const auto& [why, root] : roots) {
        for (const char* name : kGuiExecutables) {
            out.emplace_back(why, root / (std::string(name) + kExeSuffix));
        }
        // A developer tree builds the GUI under its own target directory rather
        // than beside dottalkpp. Probed after the plain location so an installed
        // product always wins.
        for (const char* name : kGuiExecutables) {
            out.emplace_back(why, root / "gui" / "wx" / (std::string(name) + kExeSuffix));
        }
    }
    return out;
}

fs::path first_existing(const std::vector<std::pair<std::string, fs::path>>& candidates)
{
    std::error_code ec;
    for (const auto& [why, p] : candidates) {
        (void)why;
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

void print_usage()
{
    cli::cmdout::print_line("APPGUI -- launch the windowed GUI");
    cli::cmdout::print_line("  APPGUI            launch, or report why it cannot");
    cli::cmdout::print_line("  APPGUI USAGE      this text");
    cli::cmdout::print_line("  alias: GUI");
    cli::cmdout::print_line(
        "  Authorized by identity permission 'app.gui'. The GUI itself is a "
        "separate executable built by DOTTALK_WITH_WX.");
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

    // usage-access contract. Answered before the permission check and before any
    // probe -- the same ordering SIMPLEBROWSER uses, and for the same reason: a
    // user asking what a command does should not need permission to be told.
    if (tok == "USAGE" || tok == "HELP" || tok == "?") {
        print_usage();
        return;
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

    const std::vector<std::pair<std::string, fs::path>> candidates = candidate_paths();
    const fs::path exe = first_existing(candidates);

    if (exe.empty()) {
        cli::cmdout::print_line(
            "APPGUI: the windowed GUI is not present in this build.");
        cli::cmdout::print_line(
            "APPGUI: it is built by DOTTALK_WITH_WX, which is OFF by default "
            "(src/CMakeLists.txt:6).");
        if (candidates.empty()) {
            // Cannot happen with the current roots, and said anyway: the failure
            // this replaced was exactly a loop that ran zero times.
            cli::cmdout::print_line(
                "APPGUI: no probe location could be resolved at all -- "
                "Slot::BIN, Slot::DATA and the current directory are all empty.");
        }
        for (const auto& [why, p] : candidates) {
            cli::cmdout::print_line("APPGUI:   looked for " + p.string() +
                                    "   [" + why + "]");
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
