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
using AreaId = std::uint64_t;

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
    std::vector<AreaInfo> areas;
    std::vector<StatusMessage> messages;
};

struct WorkspaceIndexInfo {
    AreaId area_id {0};
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

struct WorkspaceRelationInfo {
    // The relation's OWNING workspace. Relations are engine-global today, so a
    // refresh has no group scope -- recorded here so the column can show what
    // the runtime cannot yet separate.
    std::string workspace {kDefaultWorkspace};
    std::string parent;
    std::string child;
    std::string parent_key;
    std::string child_key;
    std::uint64_t match_count {0};
    std::string source;
};

struct WorkspaceModel {
    AreaId active_area_id {0};
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
