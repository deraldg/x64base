#pragma once

#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace dottalk::gui {

using TaskId = std::uint64_t;
using AreaId = std::uint64_t;

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
    std::string parent;
    std::string child;
    std::string parent_key;
    std::string child_key;
    std::uint64_t match_count {0};
    std::string source;
};

struct WorkspaceModel {
    AreaId active_area_id {0};
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
    bool truncated {false};
    std::vector<StatusMessage> messages;
};

} // namespace dottalk::gui
