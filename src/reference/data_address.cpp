#include "reference/data_address.hpp"

#include <sstream>
#include <utility>

namespace dottalk::reference {

bool WorkspaceIdentity::operator==(const WorkspaceIdentity& other) const noexcept {
    return logical_name == other.logical_name &&
           profile_path == other.profile_path &&
           session_id == other.session_id;
}

bool DbAreaIdentity::operator==(const DbAreaIdentity& other) const noexcept {
    return slot == other.slot &&
           alias == other.alias &&
           generation == other.generation;
}

bool TableIdentity::operator==(const TableIdentity& other) const noexcept {
    return logical_name == other.logical_name &&
           descriptor_name == other.descriptor_name &&
           basename == other.basename &&
           physical_path == other.physical_path &&
           storage_flavor == other.storage_flavor;
}

RecordSelector RecordSelector::current() {
    return RecordSelector{};
}

RecordSelector RecordSelector::physical(std::uint64_t recno) {
    RecordSelector out;
    out.kind = RecordSelectorKind::PhysicalRecno;
    out.physical_recno = recno;
    return out;
}

RecordSelector RecordSelector::logical(std::uint64_t position,
                                       std::string order,
                                       std::string tag) {
    RecordSelector out;
    out.kind = RecordSelectorKind::LogicalPosition;
    out.logical_position = position;
    out.order_name = std::move(order);
    out.tag_name = std::move(tag);
    return out;
}

bool RecordSelector::same_identity(const RecordSelector& other) const noexcept {
    if (kind != other.kind) return false;

    switch (kind) {
        case RecordSelectorKind::Current:
            return true;
        case RecordSelectorKind::PhysicalRecno:
        case RecordSelectorKind::RelationSelected:
            return physical_recno == other.physical_recno;
        case RecordSelectorKind::LogicalPosition:
            return logical_position == other.logical_position &&
                   order_name == other.order_name &&
                   tag_name == other.tag_name;
        case RecordSelectorKind::PrimaryKey:
        case RecordSelectorKind::UniqueKey:
            // Value equality becomes policy-bearing. The first build compares
            // canonical key identity only and leaves typed comparison to the
            // shared Value comparison service.
            return key_name == other.key_name &&
                   key_value.has_value() == other.key_value.has_value();
        case RecordSelectorKind::ArrayIndexPath:
            return index_path == other.index_path;
        case RecordSelectorKind::ExternalRowId:
            return external_rowid == other.external_rowid;
    }

    return false;
}

bool FieldIdentity::operator==(const FieldIdentity& other) const noexcept {
    return canonical_name == other.canonical_name &&
           descriptor_name == other.descriptor_name &&
           ordinal == other.ordinal &&
           type_code == other.type_code;
}

DataAddress::DataAddress(WorkspaceIdentity workspace,
                         DbAreaIdentity area,
                         TableIdentity table,
                         RecordSelector record,
                         FieldIdentity field,
                         std::vector<RelationStep> relations)
    : workspace_(std::move(workspace)),
      area_(std::move(area)),
      table_(std::move(table)),
      record_(std::move(record)),
      field_(std::move(field)),
      relations_(std::move(relations)) {}

bool DataAddress::same_field_identity(const DataAddress& other) const noexcept {
    return workspace_ == other.workspace_ &&
           area_ == other.area_ &&
           table_ == other.table_ &&
           field_ == other.field_;
}

bool DataAddress::same_cell_identity(const DataAddress& other) const noexcept {
    return same_field_identity(other) &&
           record_.same_identity(other.record_);
}

std::string DataAddress::diagnostic_text() const {
    std::ostringstream out;

    out << (workspace_.logical_name.empty() ? "CURRENT_WORKSPACE"
                                            : workspace_.logical_name);

    out << ".#";
    if (area_.slot >= 0) out << area_.slot;
    else out << '?';

    out << '.'
        << (table_.logical_name.empty() ? table_.basename
                                        : table_.logical_name);

    switch (record_.kind) {
        case RecordSelectorKind::Current:
            out << ".CURRENT";
            break;
        case RecordSelectorKind::PhysicalRecno:
        case RecordSelectorKind::RelationSelected:
            out << ".RECNO(" << record_.physical_recno << ')';
            break;
        case RecordSelectorKind::LogicalPosition:
            out << ".POSITION(" << record_.logical_position << ')';
            break;
        case RecordSelectorKind::PrimaryKey:
            out << ".PRIMARY(" << record_.key_name << ')';
            break;
        case RecordSelectorKind::UniqueKey:
            out << ".UNIQUE(" << record_.key_name << ')';
            break;
        case RecordSelectorKind::ArrayIndexPath:
            out << ".INDEX";
            for (const auto index : record_.index_path) out << '[' << index << ']';
            break;
        case RecordSelectorKind::ExternalRowId:
            out << ".ROWID(" << record_.external_rowid << ')';
            break;
    }

    for (const auto& relation : relations_) {
        out << "->"
            << (relation.relation_name.empty()
                    ? relation.child_table.logical_name
                    : relation.relation_name);

        if (relation.selected_record.kind == RecordSelectorKind::PhysicalRecno ||
            relation.selected_record.kind == RecordSelectorKind::RelationSelected) {
            out << ".RECNO(" << relation.selected_record.physical_recno << ')';
        }
    }

    out << '.'
        << (field_.canonical_name.empty() ? field_.descriptor_name
                                          : field_.canonical_name);

    return out.str();
}

} // namespace dottalk::reference
