// @dottalk.file v1
// subsystem: cli
// layer: interface
// owns: synchronous observation of native MINIDB materialization
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#pragma once
#include <cstdint>
#include <filesystem>
#include <functional>
#include <string>
#include <vector>

namespace cli {
// A materialized payload is not proof that every declared table opened. These
// handles are measured after the native loader, excluding pre-existing areas.
struct WorkspaceImageEvent {
    std::string name, payload;
    std::filesystem::path catalog, ram_root;
    std::uint64_t workspace{};
    std::vector<std::uint64_t> opened_areas;
};
using WorkspaceImageObserver = std::function<void(const WorkspaceImageEvent&)>;
// Engine-thread only. Hosts restore the returned observer before teardown.
WorkspaceImageObserver set_workspace_image_observer(WorkspaceImageObserver observer);
}
