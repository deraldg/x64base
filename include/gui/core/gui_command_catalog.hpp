#pragma once

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
