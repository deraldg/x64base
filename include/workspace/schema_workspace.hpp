// @dottalk.file v1
// subsystem: workspace
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
// @dottalk.contract
// file: include/workspace/schema_workspace.hpp
// subsystem: workspace
// role: Declares workspace-layer interfaces for DotTalk++ session, area, or runtime workspace coordination
// authority: canonical-header-contract
// mutation: token-authorized
// notes: canonical contract annotation inserted by guarded SelfDoc apply script

#include "workspace/schema_area_state.hpp"

#include <string>
#include <vector>

namespace dottalk::workspace {

class WorkAreaManager;

class SchemaWorkspace
{
public:
    int current_slot = 0;
    std::vector<SchemaAreaState> areas;

    bool capture_from_runtime(const WorkAreaManager& wam);
    bool apply_to_runtime(WorkAreaManager& wam);

    // Runtime work-area snapshot I/O, format "DTWSSNAP 1" (pipe-delimited).
    // NOT the .dtschema posture format: cmd_workspace.cpp's serializer is
    // authoritative there and owns the DTSHEMA version namespace (collision
    // reconciled 2026-08-11 -- see the block comment on save_file; AIF-078
    // D5/Q5). Measured that day: this pair has ZERO callers -- unwired.
    bool save_file(const std::string& path) const;
    bool load_file(const std::string& path);
};

} // namespace dottalk::workspace

