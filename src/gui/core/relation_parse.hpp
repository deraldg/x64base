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
#include <vector>

namespace dottalk::gui {

// WHY THIS UNIT EXISTS. Both functions below lived in session.cpp's ANONYMOUS
// namespace, which meant no fixture could link them: the only way to reach
// merge_relation was to drive a whole Session, and the only way to reach the
// parser was to make a real CLI command emit the text you wanted. They are
// pure -- text in, rows out -- and being unreachable was an accident of where
// they were typed, not a property of what they do.
//
// THE PARSER NO LONGER READS A GLOBAL. It used to call owning_workspace_now()
// for every row it built, so its output depended on xbase::workspace state
// that never appears in its signature. The owning workspace is now a
// PARAMETER. That is the same correction as ruling D10 R3 -- a dependency
// travels in the signature, not through a side channel -- and it is what lets
// this unit link nothing and touch no filesystem.
void merge_relation(std::vector<WorkspaceRelationInfo>& relations,
                    WorkspaceRelationInfo relation);

std::vector<WorkspaceRelationInfo> parse_relation_edges_from_output(
        const std::string& output,
        const std::string& owning_workspace);

} // namespace dottalk::gui
