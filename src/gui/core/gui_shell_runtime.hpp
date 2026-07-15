#pragma once

#include "gui_cli_bridge.hpp"

#include <memory>
#include <string>

namespace dottalk::gui {

class GuiShellRuntime {
public:
    virtual ~GuiShellRuntime() = default;

    virtual RuntimeCliResult run(const RuntimeCliRequest& request) = 0;
    virtual std::string description() const = 0;
    virtual bool persistent() const = 0;
};

std::unique_ptr<GuiShellRuntime> make_script_shell_runtime();

} // namespace dottalk::gui
