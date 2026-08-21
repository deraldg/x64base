// @dottalk.file v1
// subsystem: gui
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

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

// AIF-120. Read-only descent into a MINIDB container: what is inside a memo
// field, rendered without hydrating a single byte. The GUI panel displays this
// string; the scanning is dottalk::minidb::scan (include/dottalk/minidb.hpp),
// which performs no I/O, so clicking a memo costs a parse and nothing else.
//
// `payload` is the raw container bytes as read from the memo store.
std::string format_minidb_container_text(const std::string& payload,
                                         const std::string& title);

} // namespace dottalk::gui
