// @dottalk.file v1
// subsystem: reference
// layer: header
// owns:
// project: project.x64base.runtime
// lane: AIF-078
// owner: member.derald
// status: experimental

#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "value/value.hpp"

namespace dottalk::reference {

enum class StorageFlavor : std::uint8_t {
    None,
    V32,
    V64,
    V128,
    NativeTuple
};

struct WorkspaceIdentity final {
    std::string logical_name;
    std::string profile_path;
    std::uint64_t session_id{0};

    [[nodiscard]] bool operator==(const WorkspaceIdentity& other) const noexcept;

    // True when this names no workspace at all (the implicit "current" one).
    [[nodiscard]] bool unspecified() const noexcept;
};

// A workspace PATH, OUTERMOST FIRST. AIF-078 Q7.
//
// Depth 0 and depth 1 are the model the engine implements today: exactly one
// workspace, implicit and unnamed (see xbase.hpp:494 -- one flat _areas array
// under one XBaseEngine). An unspecified identity and an empty path both mean
// "the current workspace", and compare equal.
//
// Depth > 1 is RESERVED, NOT RESOLVABLE. It exists so that nesting is a policy
// decision rather than a type change once a consumer arrives:
//   - AIF-070 (memo-resident mini-databases) nests structurally -- a workspace
//     living in a memo field lives in a row, in a table, in a workspace;
//   - AIF-073 (agent memory retention) expresses retention scope as a subtree.
// The parser already accepts arbitrary depth (qualified_reference.cpp, the
// unlimited segment loop); nothing resolves it. See
// docs/maintenance/WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_LANE_V1.md sec 5b.
//
// searched-and-absent: no runtime workspace registry, no containment invariant,
// no cycle guard, no depth cap. Q8 (does an unqualified name walk up ancestors?
// proposed: NO) must be ruled before any depth > 1 is resolved.
using WorkspacePath = std::vector<WorkspaceIdentity>;

struct DbAreaIdentity final {
    std::int32_t slot{-1};
    std::string alias;
    std::uint64_t generation{0};

    [[nodiscard]] bool operator==(const DbAreaIdentity& other) const noexcept;
};

struct TableIdentity final {
    std::string logical_name;
    std::string descriptor_name;
    std::string basename;
    std::string physical_path;
    StorageFlavor storage_flavor{StorageFlavor::None};

    [[nodiscard]] bool operator==(const TableIdentity& other) const noexcept;
};

enum class RecordSelectorKind : std::uint8_t {
    Current,
    PhysicalRecno,
    LogicalPosition,
    PrimaryKey,
    UniqueKey,
    RelationSelected,
    ArrayIndexPath,
    ExternalRowId
};

struct RecordSelector final {
    RecordSelectorKind kind{RecordSelectorKind::Current};

    std::uint64_t physical_recno{0};
    std::uint64_t logical_position{0};

    std::string order_name;
    std::string tag_name;

    std::string key_name;
    std::optional<dottalk::value::Value> key_value;

    std::vector<std::uint64_t> index_path;
    std::string external_rowid;

    static RecordSelector current();
    static RecordSelector physical(std::uint64_t recno);
    static RecordSelector logical(std::uint64_t position,
                                  std::string order_name = {},
                                  std::string tag_name = {});

    [[nodiscard]] bool same_identity(const RecordSelector& other) const noexcept;
};

struct FieldIdentity final {
    std::string canonical_name;
    std::string descriptor_name;
    std::int32_t ordinal{-1};
    char type_code{0};

    [[nodiscard]] bool operator==(const FieldIdentity& other) const noexcept;
};

struct RelationStep final {
    DbAreaIdentity parent_area;
    TableIdentity parent_table;
    std::string relation_name;

    DbAreaIdentity child_area;
    TableIdentity child_table;

    std::vector<std::string> parent_fields;
    std::vector<std::string> child_fields;

    RecordSelector selected_record;
};

class DataAddress final {
public:
    DataAddress() = default;

    // Single-workspace form. Unchanged signature and unchanged behavior: the
    // identity becomes a depth-1 path. Every existing caller keeps compiling.
    DataAddress(WorkspaceIdentity workspace,
                DbAreaIdentity area,
                TableIdentity table,
                RecordSelector record,
                FieldIdentity field,
                std::vector<RelationStep> relations = {});

    // Nested form, outermost workspace first. Depth > 1 is reserved and is not
    // resolvable at runtime -- see the WorkspacePath note above.
    DataAddress(WorkspacePath workspace_path,
                DbAreaIdentity area,
                TableIdentity table,
                RecordSelector record,
                FieldIdentity field,
                std::vector<RelationStep> relations = {});

    // The INNERMOST (most specific) workspace, or an unspecified identity when
    // the path is empty. This is the depth-1 accessor; it is what every
    // pre-AIF-078 caller means by "the workspace".
    [[nodiscard]] const WorkspaceIdentity& workspace() const noexcept;

    [[nodiscard]] const WorkspacePath& workspace_path() const noexcept {
        return workspace_path_;
    }

    // Count of SPECIFIED workspaces, outermost to innermost. 0 == current.
    [[nodiscard]] std::size_t workspace_depth() const noexcept;

    [[nodiscard]] const DbAreaIdentity& area() const noexcept { return area_; }
    [[nodiscard]] const TableIdentity& table() const noexcept { return table_; }
    [[nodiscard]] const RecordSelector& record() const noexcept { return record_; }
    [[nodiscard]] const FieldIdentity& field() const noexcept { return field_; }
    [[nodiscard]] const std::vector<RelationStep>& relations() const noexcept {
        return relations_;
    }

    [[nodiscard]] bool same_field_identity(const DataAddress& other) const noexcept;
    [[nodiscard]] bool same_cell_identity(const DataAddress& other) const noexcept;
    [[nodiscard]] std::string diagnostic_text() const;

private:
    WorkspacePath workspace_path_;
    DbAreaIdentity area_;
    TableIdentity table_;
    RecordSelector record_;
    FieldIdentity field_;
    std::vector<RelationStep> relations_;
};

} // namespace dottalk::reference
