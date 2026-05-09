// @dottalk.usage v1
// owner: DOT|MCC
// command: MCC
// category: demo
// status: supported
// noargs: execute
// effect: onboarding
// mutates: path-state workspace-state relation-state work-area-state cursor
// usage-access: MCC USAGE
// summary:
//   Load the MCC v32 demo workspace as a one-command starter demo.
//
// usage:
//   MCC
//   MCC USAGE
//
// notes:
//   MCC prepares and loads the MCC sample workspace for demonstration.
//   MCC runs DotScript x32 to set the v32 DBF and INDEX paths.
//   MCC then runs WORKSPACE LOAD mcc.dtschemas.
//   Equivalent manual sequence is DOTSCRIPT x32, then WORKSPACE LOAD mcc.dtschemas.
//   MCC is a convenience command and does not directly open tables or create relations itself.
//   Table/session/relation restoration remains owned by WORKSPACE.
//   Environment/path setup remains owned by DotScript.
//   DO X32 is a command-surface shortcut for DotScript x32; MCC should be documented as using DotScript.
//
// risk:
//   delegates_dotscript: yes
//   delegates_workspace_load: yes
//   mutates_path_state: through DotScript x32
//   mutates_workspace_state: through WORKSPACE LOAD
//   mutates_relation_state: through WORKSPACE LOAD
//   mutates_table_data: no direct table-data mutation
//
// related:
//   DOTSCRIPT
//   WORKSPACE
//   REL
//   USE
//

// cmd_mcc.cpp
//
// Convenience command for the MCC demo workspace.
//
// Intent:
//   Give a new user one simple command that prepares the v32 demo environment
//   and then loads the MCC workspace definition.
//
// Policy:
//   Do not duplicate workspace/table-loading logic here.  This command is only
//   a small command-surface convenience wrapper around the existing script and
//   WORKSPACE command path.
//
// Behavior:
//   MCC
//      -> DOTSCRIPT X32
//      -> WORKSPACE LOAD MCC.DTSCHEMAS
//
// Notes:
//   - The extension requested here is .dtschemas, matching the current user
//     request.  If the checked-in file is singular .dtschema, change the single
//     constant below rather than changing the command logic.
//   - This file intentionally avoids directly opening DBFs, indexes, relations,
//     or memo files.  WORKSPACE remains the owner of live area/session restore.

#include "xbase.hpp"
#include "shell_api.hpp"

#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

// -----------------------------------------------------------------------------
// Project integration hooks
// -----------------------------------------------------------------------------
//
// The DotTalk++ command dispatcher already has a way to execute another command
// line from inside a command handler.  Wire this small wrapper to that existing
// mechanism.
//
// If your local command helper has a different name, only adapt this shim.  Keep
// cmd_mcc itself as a thin command-surface wrapper.

namespace dottalkpp {
namespace cmd_mcc_detail {

static constexpr const char* kSetupCommand = "dotscript x32";
static constexpr const char* kWorkspaceLoadCommand = "workspace load mcc.dtschemas";

static void mcc_say(const std::string& line)
{
    std::cout << line << '\n';
}

// Replace the body of this function with the existing internal command-runner
// used elsewhere by command wrappers.  It should return true on success.
//
// Examples of acceptable project-local implementations:
//   return command_dispatch(line);
//   return run_command_line(line);
//   return repl_execute_line(line);
//   return dot_exec(line.c_str()) == 0;
//
// This deliberate shim keeps the rest of the file stable even if the dispatcher
// helper has project-specific naming.
static bool run_inner_command(const std::string& line)
{
    // TODO: connect to the existing DotTalk++ command dispatcher.
    // This fallback is intentionally loud so the file cannot silently pretend
    // to load the demo without being wired into the command surface.
    mcc_say("MCC: command shim not wired; would run: " + line);
    return false;
}

static bool run_checked(const char* line)
{
    mcc_say(std::string("MCC: ") + line);
    if (!run_inner_command(line)) {
        mcc_say(std::string("MCC: failed while running: ") + line);
        return false;
    }
    return true;
}

} // namespace cmd_mcc_detail
} // namespace dottalkpp

// -----------------------------------------------------------------------------
// Command entry point
// -----------------------------------------------------------------------------
//
// Keep the exported name simple and predictable for registration from the
// command table.  If the project command convention expects a different
// signature, adapt only this outer entry point and leave cmd_mcc_run() intact.

bool cmd_mcc_run()
{
    using namespace dottalkpp::cmd_mcc_detail;

    mcc_say("MCC: preparing v32 demo environment");

    if (!run_checked(kSetupCommand)) {
        return false;
    }

    mcc_say("MCC: loading MCC workspace");

    if (!run_checked(kWorkspaceLoadCommand)) {
        return false;
    }

    mcc_say("MCC: workspace loaded");
    return true;
}

// Optional argv-style adapter for command tables that pass raw arguments.
// MCC should not require arguments; extra args are rejected so new-user behavior
// stays deterministic.
bool cmd_mcc(const std::vector<std::string>& args)
{
    using dottalkpp::cmd_mcc_detail::mcc_say;

    if (!args.empty()) {
        if (args.size() == 1) {
            std::string arg = args[0];
            for (char& ch : arg) {
                ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
            }
            if (arg == "USAGE" || arg == "HELP" || arg == "?") {
                mcc_say("Usage:");
                mcc_say("  MCC");
                mcc_say("  MCC USAGE");
                mcc_say("Notes:");
                mcc_say("  - Loads the MCC v32 demo workspace.");
                mcc_say("  - Equivalent manual sequence: DOTSCRIPT x32, then WORKSPACE LOAD mcc.dtschemas.");
                return true;
            }
        }
        mcc_say("Usage: MCC");
        mcc_say("Loads the v32 MCC demo workspace.");
        return false;
    }

    return cmd_mcc_run();
}

// Canonical DotTalk++ shell-command adapter.
// shell_commands.cpp registers MCC as cmd_MCC(DbArea&, istringstream&).
void cmd_MCC(xbase::DbArea& area, std::istringstream& iss)
{
    using dottalkpp::cmd_mcc_detail::kSetupCommand;
    using dottalkpp::cmd_mcc_detail::kWorkspaceLoadCommand;
    using dottalkpp::cmd_mcc_detail::mcc_say;

    std::vector<std::string> args;
    std::string tok;
    while (iss >> tok) {
        args.push_back(tok);
    }

    if (!args.empty()) {
        if (args.size() == 1) {
            std::string arg = args[0];
            for (char& ch : arg) {
                ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
            }
            if (arg == "USAGE" || arg == "HELP" || arg == "?") {
                mcc_say("Usage:");
                mcc_say("  MCC");
                mcc_say("  MCC USAGE");
                mcc_say("Notes:");
                mcc_say("  - Loads the MCC v32 demo workspace.");
                mcc_say("  - Equivalent manual sequence: DOTSCRIPT x32, then WORKSPACE LOAD mcc.dtschemas.");
                return;
            }
        }

        mcc_say("Usage: MCC");
        mcc_say("Loads the v32 MCC demo workspace.");
        return;
    }

    mcc_say("MCC: preparing v32 demo environment");

    mcc_say(std::string("MCC: ") + kSetupCommand);
    if (!shell_execute_line(area, kSetupCommand)) {
        mcc_say(std::string("MCC: failed while running: ") + kSetupCommand);
        return;
    }

    mcc_say("MCC: loading MCC workspace");

    mcc_say(std::string("MCC: ") + kWorkspaceLoadCommand);
    if (!shell_execute_line(area, kWorkspaceLoadCommand)) {
        mcc_say(std::string("MCC: failed while running: ") + kWorkspaceLoadCommand);
        return;
    }

    mcc_say("MCC: done");
}

// Optional C-style adapter for older command registries.
// argc/argv may include the command name as argv[0]; this adapter accepts either
// argc == 0 or argc == 1 and rejects user-supplied trailing arguments.
extern "C" bool cmd_mcc_c(int argc, const char* const* argv)
{
    using dottalkpp::cmd_mcc_detail::mcc_say;

    (void)argv;

    if (argc > 1) {
        mcc_say("Usage: MCC");
        mcc_say("Loads the v32 MCC demo workspace.");
        return false;
    }

    return cmd_mcc_run();
}
