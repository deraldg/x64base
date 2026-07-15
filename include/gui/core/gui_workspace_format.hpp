#pragma once

#include "gui/core/model.hpp"

#include <string>

namespace dottalk::gui {

std::string format_workspace_graph_text(const ListAreasResult& areas,
                                        const std::string& title,
                                        const std::string& no_open_areas_text);

std::string format_workspace_graph_text(const WorkspaceModel& model,
                                        const std::string& title,
                                        const std::string& no_open_areas_text);

} // namespace dottalk::gui
