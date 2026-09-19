// @dottalk.file v1
// subsystem: gui
// layer: service
// owns: Workbench installation discovery
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_session.hpp"
namespace dottalk::workbench {
namespace fs = std::filesystem;
fs::path find_workbench_data_root(const fs::path& executable, const fs::path& working_directory) {
    // Prefer the executable's installation, including development builds.
    for (auto base : {executable.parent_path(), working_directory}) {
        if (base.empty()) continue;
        base = fs::absolute(base).lexically_normal();
        for (;;) {
            for (const auto& candidate : {base / "data", base / "dottalkpp/data", base}) {
                std::error_code ec;
                if (fs::is_directory(candidate / "dbf", ec) && !ec &&
                    fs::is_directory(candidate / "workspaces", ec) && !ec)
                    return candidate.lexically_normal();
            }
            const auto parent = base.parent_path();
            if (parent == base || parent.empty()) break;
            base = parent;
        }
    }
    return {};
}
}
