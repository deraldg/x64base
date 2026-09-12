// @dottalk.file v1
// subsystem: xbase
// layer: header
// owns:
// project: project.x64base.runtime
// lane: application-ui-dsl
// owner: member.derald
// status: supported

#pragma once
// @dottalk.contract
// file: include/xbase/relation_wire.hpp
// subsystem: xbase
// role: THE RELATION WIRE RECORD -- what crosses the process boundary
// authority: canonical-header-contract
// mutation: token-authorized
//
// TOKEN for the 2026-08-24 creation: rulings R124 and R125, steward, recorded
// in docs/ai-friendly/R_RULING_REGISTER_V1.md. Design in
// claude/R122_DESIGN_RELATION_WIRE_PLACEMENT.md.

// WHY THIS LIVES IN xbase, AND NOT IN src/gui WHERE IT WAS BORN.
//
// R122 ruled that src/gui does not depend on src/cli, because the GUI does not
// call the engine at all -- it SPAWNS one (gui_shell_runtime.cpp CreateProcessW,
// gui_cli_bridge.cpp _popen) and reads its stdout. The fix for a GUI that
// re-derives the producer's grammar from prose is therefore not a link; it is
// for the producer to EMIT the data and the consumer to receive it.
//
// The format needed no design. `RELATION <parent> <child> ON <csv> [TO <csv>]`
// already existed, already round-tripped, and was already held by
// dottalkpp_relation_merge_test. What did not exist was a place BOTH SIDES
// COULD REACH: the formatter lived in src/gui/core/relation_parse.cpp, and
// dottalkpp does not link dottalk_gui_core.
//
// THE ALTERNATIVE WAS TO CHERRY-PICK, and it was declined on this tree's own
// recorded reasoning. include/xbase/area_alloc.hpp made exactly this choice on
// 2026-08-23 and wrote down why: placing shared code in xbase rather than
// beside the files a consumer already compiles by hand "keeps that list from
// growing by a third hand-maintained entry -- the enumeration-by-convention
// trap WORKSPACE WRITEBACK already paid for." Cherry-picking here would also
// have INVERTED the dependency direction R122 had just ruled, making src/cli
// depend on src/gui.
//
// IT COSTS NEITHER CONSUMER A BUILD CHANGE. src/xbase/CMakeLists.txt globs its
// sources; dottalkpp and dottalk_gui_core both already link xbase.
//
// AND IT DRAGS NOTHING IN. The implementation is standard-library only -- no
// DbArea, no engine, no filesystem. It is filed under xbase because that is
// where both consumers can reach it, not because it needs anything here. The
// same was true of the unit it came from, which is why a test target was
// already compiling that unit directly without linking the GUI
// (src/tests/CMakeLists.txt).

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xbase::relwire {

// ONE RELATION EDGE, AS IT CROSSES THE BOUNDARY.
//
// This is deliberately NOT either side's model type. The GUI's
// WorkspaceRelationInfo carries display concerns (a workspace NAME, a source
// label) and the CLI's Relation carries 1-based FIELD INDICES resolved against
// open tables, with the parent living in the relation store's MAP KEY rather
// than in the struct at all. Neither travels. This does.
struct RelationRecord {
    // R125: THE WORKSPACE IS A HANDLE, NOT A NAME.
    //
    // The engine has partitioned the relation store by handle since AIF-078
    // I1.2 while the GUI carried a name in six places and nothing converted
    // between them. GUI_LAYER_DECISION_OUTLINE step 2 asked for that conversion
    // to happen ONCE, IN A NAMED PLACE. This field is that place: a name is
    // produced for DISPLAY by xbase::workspace::name_of(), and a name coming
    // the other way resolves through find_by_name_ci().
    //
    // R6 IS SATISFIED BY CONSTRUCTION AND NOT BY A NEW CONVENTION. The handle
    // space already reserves 0 as not-a-legal-handle -- workspace_membership
    // .hpp sets kDefaultHandle to 1 "precisely so that 0 can mean" absent -- so
    // an absent workspace cannot be spelled as a present one. Nothing new had
    // to be invented to make absence unrepresentable among presences.
    std::uint64_t workspace {0};

    std::string parent;
    std::string child;

    // CSV, one key per side. A relation may bind SEVERAL fields: the shipped
    // grammar is `SET RELATIONS ADD <p> <c> ON <csv> [TO <csv>]` and the two
    // lists must be the same LENGTH, not the same names. So "SID,TERM" is ONE
    // key made of two fields, and a caller wanting a single FIELD NAME must
    // say so.
    //
    // child_key is never left empty by a correct producer: with no TO clause it
    // MIRRORS the parent side, so nothing downstream has to tell "no child key"
    // apart from a real one.
    std::string parent_key;
    std::string child_key;

    // ABSENT IS A REAL ANSWER HERE, and it is why this is an optional rather
    // than a count with a reserved value. A relation whose match count could
    // not be computed -- a truncated scan, a table not open -- has no honest
    // number, and a short count would claim to be the total. R123 made the GUI
    // stop computing this at all; when a count travels, it is the producer's,
    // computed once, from the producer's own state.
    std::optional<std::uint64_t> match_count;
};

// DO THE TWO FIELD LISTS NAME THE SAME KEY?
//
// NAKED AND CASE-INSENSITIVE: `A.SID` and `B.SID` are the SAME field name for
// this purpose, because the qualifier says which table the field was reached
// through and the key is about the field. This is the rule that decides whether
// a posture line gets a ` TO ` clause at all.
//
// IT WAS ALREADY IN THE TREE TWICE when this was written -- set_relations.cpp's
// same_field_lists and cmd_workspace.cpp's same_field_list_ci -- computing the
// same answer from two spellings, and a third was about to be avoided rather
// than added. Consolidated here on 2026-08-24 with the CLI's writer.
bool relation_field_lists_match(const std::vector<std::string>& a,
                                const std::vector<std::string>& b);

// Build a record from two field lists, applying the rule above.
//
// THE FIELD NAMES ARE CARRIED VERBATIM. Only the DECISION uses naked names: a
// key of `A.SID` is written as `A.SID`, because the posture is a record of what
// the relation was declared as, not of what it normalizes to. What the rule
// changes is whether child_key mirrors parent_key (no ` TO ` emitted) or stands
// on its own.
RelationRecord make_relation_record(std::uint64_t workspace,
                                    std::string parent,
                                    std::string child,
                                    const std::vector<std::string>& parent_fields,
                                    const std::vector<std::string>& child_fields);

// Split the clause AFTER " ON " into its parent-side and child-side lists.
// The exact inverse of the CLI's format_on_fields (set_relations.cpp), which
// emits `ON <parent-csv>` when the lists match and `ON <parent-csv> TO
// <child-csv>` when they differ.
//
// With no TO clause, or a malformed empty one, child_key mirrors the parent.
void split_relation_keys(const std::string& on_clause,
                         std::string& parent_key,
                         std::string& child_key);

// The posture line, BOTH DIRECTIONS, kept adjacent so they cannot drift apart.
// They were forty lines and sixteen hundred lines apart once, and for as long
// as that lasted the writer dropped the child side of every relation while the
// reader could not have read it back anyway -- the round trip was lossless only
// because both ends were broken the same way.
//
// THE LINE DOES NOT CARRY THE WORKSPACE. It is context, not content: the
// producer writes edges for one workspace at a time and the reader is told
// which. That is why format takes no handle and parse takes one.
//
// Both report refusal in the RETURN VALUE (R3) rather than by emitting
// something empty: a record missing a parent, a child, or a key has no posture
// line, and a line that is not a RELATION line is not half-parsed.
bool format_relation_posture_line(const RelationRecord& relation,
                                  std::string& out);

bool parse_relation_posture_line(const std::string& line,
                                 std::uint64_t owning_workspace,
                                 RelationRecord& out);

} // namespace xbase::relwire
