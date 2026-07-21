#pragma once

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
};

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

    DataAddress(WorkspaceIdentity workspace,
                DbAreaIdentity area,
                TableIdentity table,
                RecordSelector record,
                FieldIdentity field,
                std::vector<RelationStep> relations = {});

    [[nodiscard]] const WorkspaceIdentity& workspace() const noexcept {
        return workspace_;
    }
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
    WorkspaceIdentity workspace_;
    DbAreaIdentity area_;
    TableIdentity table_;
    RecordSelector record_;
    FieldIdentity field_;
    std::vector<RelationStep> relations_;
};

} // namespace dottalk::reference
