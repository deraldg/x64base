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
#include "xbase/relation_wire.hpp"

#include <cstdint>

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
// R124/R125, 2026-08-24. THE WIRE FORMAT MOVED TO xbase.
//
// split_relation_keys and the posture round trip now live in
// include/xbase/relation_wire.hpp, because the PRODUCER could not reach them
// here -- dottalkpp does not link dottalk_gui_core, and R122 ruled that the fix
// is for the producer to emit structured data rather than for anyone to change
// who links whom. What remains in this unit is what is genuinely the GUI's:
// merging edges into the GUI's model, and scraping the CLI's HUMAN output.
//
// The two functions below are ADAPTERS. They convert between the wire's
// RelationRecord and the GUI's WorkspaceRelationInfo, which carries display
// concerns the wire does not: a workspace NAME (rendered from the handle by
// xbase::workspace::name_of) and a `source` label.

void merge_relation(std::vector<WorkspaceRelationInfo>& relations,
                    WorkspaceRelationInfo relation);

// The posture's RELATION line, BOTH DIRECTIONS, kept next to each other so
// they cannot drift apart again. They were a `file <<` chain in the workspace
// writer and a `rfind("RELATION ")` block in the schema reader, forty lines
// and sixteen hundred lines apart respectively, and for as long as that lasted
// the writer dropped the child side of every relation while the reader could
// not have read it back anyway. The round trip was lossless only because both
// ends were broken the same way.
//
// Both report refusal in the RETURN VALUE (D10 R3) rather than by emitting
// something empty: a relation missing a parent, a child, or a key has no
// posture line, and a line that is not a RELATION line is not half-parsed.
bool format_relation_posture_line(const WorkspaceRelationInfo& relation,
                                  std::string& out);

// TAKES A HANDLE, NOT A NAME (R125). The caller is the side that knows which
// workspace it is reading for, and the engine has keyed relations by handle
// since I1.2. The name this stamps into the model is a RENDERING, produced
// here so that exactly one place in the GUI performs the conversion.
bool parse_relation_posture_line(const std::string& line,
                                 std::uint64_t owning_workspace,
                                 WorkspaceRelationInfo& out);

std::vector<WorkspaceRelationInfo> parse_relation_edges_from_output(
        const std::string& output,
        const std::string& owning_workspace);

} // namespace dottalk::gui
