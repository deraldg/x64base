#pragma once
// @dottalk.contract v1
// family: selfdoc.ui_contract
// component: gui_command_catalog
// role: GUI presentation catalog for common actions and command prefills
// owner: DotTalk++ GUI open-architecture lane
// contract: GUI command catalog entries may label, prefill, or invoke DotTalk++ commands, but they must not redefine command syntax or behavior.
// authority: canonical command meaning belongs to dottalkpp command handlers, usage contracts, HELP/CMDHELP, and related selfdoc lanes.
// drift: if a GUI action differs from runtime command truth, runtime/help truth wins and the catalog must be corrected.
// @dottalk.contract.end

#include <string>
#include <vector>

namespace dottalk::gui {

enum class GuiCommandActionKind {
    run,
    prefill,
    info
};

struct GuiCommandAction {
    std::string category;
    std::string label;
    std::string command;
    GuiCommandActionKind kind {GuiCommandActionKind::run};
    std::string note;
};

const std::vector<GuiCommandAction>& gui_command_catalog();

} // namespace dottalk::gui
