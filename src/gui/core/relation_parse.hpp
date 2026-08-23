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
// Split the clause AFTER " ON " into its parent-side and child-side field
// lists. This is the exact inverse of set_relations.cpp:894 format_on_fields,
// which emits `ON <parent-csv>` when the two lists match and
// `ON <parent-csv> TO <child-csv>` when they differ.
//
// Each side stays a CSV. A relation may bind SEVERAL fields -- the shipped
// grammar is `SET RELATIONS ADD <p> <c> ON <csv> [TO <csv>]`
// (cmd_relations.cpp:418-455) and add_relation requires the two lists to be
// the same LENGTH, not the same names. So "SID,TERM" is one key made of two
// fields, and callers that want a single FIELD NAME must say so.
//
// child_key is never left empty: with no TO clause, or a malformed empty one,
// it mirrors the parent side. An empty field name is not something a correct
// producer emits, so nothing downstream has to tell "no child key" apart from
// a real one.
void split_relation_keys(const std::string& on_clause,
                         std::string& parent_key,
                         std::string& child_key);

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

bool parse_relation_posture_line(const std::string& line,
                                 const std::string& owning_workspace,
                                 WorkspaceRelationInfo& out);

std::vector<WorkspaceRelationInfo> parse_relation_edges_from_output(
        const std::string& output,
        const std::string& owning_workspace);

} // namespace dottalk::gui
