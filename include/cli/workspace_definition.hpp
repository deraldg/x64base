// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: read-only workspace definition preflight
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: candidate
#pragma once
#include <filesystem>
#include <string>
#include <vector>

namespace cli {
struct WorkspaceDefinitionCheck {
    int version{}, declared{};
    std::vector<std::string> missing;
    std::string error;
    bool ready() const { return error.empty() && missing.empty(); }
};
// Uses the loader's parser/resolver. A saved DBFROOT overrides the supplied
// default in line order. Never changes SET PATH, areas, cursors or the file.
WorkspaceDefinitionCheck check_workspace_definition(const std::filesystem::path& file,
                                                    const std::filesystem::path& default_dbf);
}
