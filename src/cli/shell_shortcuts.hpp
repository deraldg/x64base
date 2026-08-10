// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#ifndef DOTTALK_CLI_SHELL_SHORTCUTS_HPP
#define DOTTALK_CLI_SHELL_SHORTCUTS_HPP

#include <string>
#include "shortcut_resolver.hpp"

namespace shell_shortcuts {

inline const cli::ShortcutResolver& resolver() {
    static cli::ShortcutResolver r;
    return r;
}

inline std::string resolve(const std::string& token) {
    return resolver().resolve(token);
}

} // namespace shell_shortcuts

#endif // DOTTALK_CLI_SHELL_SHORTCUTS_HPP
