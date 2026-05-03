#pragma once

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

    bool save_file(const std::string& path) const;
    bool load_file(const std::string& path);
};

} // namespace dottalk::workspace
