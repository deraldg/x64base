// @dottalk.file v1
// subsystem: gui
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace dottalk::gui {

using TaskId = std::uint64_t;

// AIF-078, 2026-08-23. The area's SESSION rung: DbArea::areaHandle(), minted at
// open() and never reused. It is an IDENTITY -- do no arithmetic on it, do not
// persist it, and do not show it to anyone. It answers "is this the same area",
// and nothing else.
//
// It used to answer three questions at once. session.cpp minted it from a
// private counter in two places, derived it from a slot in four more, and three
// files reconstructed a display number from it as `id - 1`. That worked only
// because the counter started at 1, so `id - 1` equalled the open ordinal --
// which equals the list position only while nothing is ever closed.
using AreaId = std::uint64_t;

// The area's POSITIONAL rung: where it sits in the session's area list. This is
// the number the user types, the number the tables column shows, and the number
// a posture records as AREA <n>. 0-BASED, DENSE, and RENUMBERED when an area
// closes -- all three are properties, not defects. A position is an address,
// and addresses are reused; that is the whole difference between this rung and
// the one above.
//
// Derivation runs DOWNWARD only (ruling D10 R1): id -> ordinal is a lookup in
// the list, ordinal -> id is a lookup in the list, and neither is ever spelled
// with + 1 or - 1 again.
using AreaOrdinal = std::uint64_t;

// NO AREA is a TYPE, not a value -- ruling D10 R6.3, and it binds retroactively
// by steward direction 2026-08-23 ("clean start").
//
// This was `kNoAreaOrdinal = ~0`: reserved, named, and compliant under R6.1,
// because no correct producer can emit ~0 as an index into a list that will
// never hold 2^64-1 areas. It was still the WEAKER form. R6.3 orders the
// choices -- make absence unrepresentable BY TYPE where a type is free, and
// reserve a named value only where it is not -- and a type was free here.
//
// What the type buys over the sentinel, concretely: the DEFAULT is absence, so
// a field that nobody set cannot read as "area 0"; there is no constant to
// compare against and therefore none to forget; and arithmetic on an unset
// ordinal does not compile instead of quietly computing on ~0. The rule that
// excuses the code its author wrote is the rule to distrust, and this is the
// author's own sentinel being held to it.
using MaybeAreaOrdinal = std::optional<AreaOrdinal>;

// The ONE display conversion, replacing three identical copies that lived in
// session.cpp, main_frame.cpp and gui_workspace_format.cpp.
inline std::string format_area_ordinal(const MaybeAreaOrdinal& ordinal) {
    return ordinal ? std::to_string(*ordinal) : std::string("none");
}

// AIF-120, multi-workspace GUI slice. Design invariant I1
// (WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md): an area belongs to exactly ONE
// workspace and there is NO NULL -- a bare USE outside any workspace opens into
// an implicit, always-present workspace named DEFAULT, which behaves like every
// other workspace. So a workspace field is never blank, and the GUI never has a
// cell it has to explain.
//
// The name is a constant rather than a literal at each site because the runtime
// registry does not exist yet: when it lands, the workspace of an area stops
// being "DEFAULT, always" and becomes a lookup, and this is the one place that
// has to know.
inline constexpr const char* kDefaultWorkspace = "DEFAULT";

enum class TaskState {
    queued,
    running,
    completed,
    cancelled,
    failed
};

enum class Severity {
    info,
    warning,
    error
};

struct StatusMessage {
    Severity severity {Severity::info};
    std::string text;
    std::string code;
    std::string detail;
};

struct TaskProgress {
    TaskId task_id {0};
    TaskState state {TaskState::queued};
    std::string label_code;
    std::string label;
    std::optional<double> fraction;
    std::vector<StatusMessage> messages;
};

struct OpenTableRequest {
    std::filesystem::path path;
};

struct OpenTableResult {
    bool ok {false};
    AreaId area_id {0};
    // Where it landed in the list -- the number to show, never area_id - 1.
    MaybeAreaOrdinal ordinal;
    // Which workspace took it. Carried for the same reason the ordinal is:
    // the session had the DbArea in hand and knew the exact answer, and a view
    // that has only an id cannot work it out afterwards. Never blank (I1).
    std::string workspace {kDefaultWorkspace};
    std::filesystem::path path;
    std::string display_name;
    std::uint64_t record_count {0};
    std::vector<StatusMessage> messages;
};

struct CommandRequest {
    std::string text;
};

struct CommandResult {
    bool ok {false};
    int exit_code {0};
    std::string output;
    std::vector<StatusMessage> messages;
};

struct TableSnapshotRequest {
    AreaId area_id {0};
    std::uint64_t first_record {1};
    std::uint32_t max_records {200};
};

struct SelectAreaRequest {
    AreaId area_id {0};
};

struct SelectAreaResult {
    bool ok {false};
    AreaId area_id {0};
    std::string display_name;
    std::vector<StatusMessage> messages;
};

struct MoveCursorRequest {
    AreaId area_id {0};
    std::uint64_t record_number {0};
};

struct MoveCursorResult {
    bool ok {false};
    AreaId area_id {0};
    std::uint64_t record_number {0};
    std::vector<StatusMessage> messages;
};

struct CloseAreaRequest {
    AreaId area_id {0};
};

struct CloseAreaResult {
    bool ok {false};
    AreaId closed_area_id {0};
    AreaId active_area_id {0};
    std::vector<StatusMessage> messages;
};

struct AreaInfo {
    AreaId area_id {0};
    // The positional rung, carried rather than reconstructed. A view that
    // renders this never has to know what an AreaId is made of.
    MaybeAreaOrdinal ordinal;
    // Never blank -- DEFAULT is a workspace (invariant I1).
    std::string workspace {kDefaultWorkspace};
    bool active {false};
    std::filesystem::path path;
    std::string display_name;
    std::uint64_t record_count {0};
    std::uint64_t field_count {0};
};

struct ListAreasResult {
    AreaId active_area_id {0};
    MaybeAreaOrdinal active_ordinal;
    std::vector<AreaInfo> areas;
    std::vector<StatusMessage> messages;
};

struct WorkspaceIndexInfo {
    AreaId area_id {0};
    MaybeAreaOrdinal ordinal;
    std::string workspace {kDefaultWorkspace};
    std::string area_name;
    std::string kind;
    std::filesystem::path container;
    std::string tag;
    std::vector<std::string> tags;
    bool active {false};
    bool ascending {true};
    std::string backend;
};

// A relation's match count, and the ABSENCE of one.
//
// D10 R6: an absent value must not be representable in the space of present
// ones. This field was `std::uint64_t match_count {0}` and 0 meant BOTH "no
// rows matched" and "never computed" -- and the two are not the same answer.
// The producer already distinguishes them: set_relations.cpp:1010 prints
// "(matches: n/a)" when it could not compute one, and the parser threw that
// away with value_or(0). main_frame.cpp then showed the user "0".
//
// R6.3 says prefer the TYPE where it is free. It is free here, exactly as it
// was for MaybeAreaOrdinal, and R6.3 binds retroactively -- "clean start".
// The default is now ABSENCE, so a field nobody set cannot read as a measured
// zero, and arithmetic on an uncomputed count does not compile.
using MatchCount = std::uint64_t;
using MaybeMatchCount = std::optional<MatchCount>;

// Rendered form. Absent is not "0" and is not a lie -- it is nothing.
inline std::string format_match_count(const MaybeMatchCount& count) {
    return count ? std::to_string(*count) : std::string();
}

struct WorkspaceRelationInfo {
    // The relation's OWNING workspace.
    //
    // WAS: "Relations are engine-global today, so a refresh has no group scope
    // -- recorded here so the column can show what the runtime cannot yet
    // separate." That stopped being true at AIF-078 I1.2, which partitioned the
    // relation store by workspace: the runtime CAN separate them now, and this
    // field is written from the session's current workspace at parse time
    // (session.cpp, owning_workspace_now). Until then it had ZERO writers while
    // gui_workspace_format.cpp filtered on it -- a filter on a constant.
    std::string workspace {kDefaultWorkspace};
    std::string parent;
    std::string child;
    std::string parent_key;
    std::string child_key;
    MaybeMatchCount match_count;
    std::string source;
};

struct WorkspaceModel {
    AreaId active_area_id {0};
    MaybeAreaOrdinal active_ordinal;
    // Scope of the selector, and the grouping key of every page above.
    std::string current_workspace {kDefaultWorkspace};
    std::vector<std::string> workspaces {std::string(kDefaultWorkspace)};
    std::vector<AreaInfo> tables;
    std::vector<WorkspaceIndexInfo> indexes;
    std::vector<WorkspaceRelationInfo> relations;
    std::vector<StatusMessage> messages;
};

struct TableColumn {
    std::string name;
    char type {'C'};
    int width {0};
    int decimals {0};
};

struct TableRow {
    std::uint64_t record_number {0};
    bool deleted {false};
    std::vector<std::string> values;
};

struct TableSnapshot {
    AreaId area_id {0};
    std::string display_name;
    std::vector<TableColumn> columns;
    std::vector<TableRow> rows;
    std::uint64_t total_records {0};
    std::uint64_t current_record_number {0};
    std::uint64_t physical_record_number {0};
    std::uint64_t logical_record_number {0};
    bool ordered {false};
    std::string order_name;
    std::string order_tag;
    bool order_ascending {true};
    bool truncated {false};
    std::vector<StatusMessage> messages;
};

} // namespace dottalk::gui
