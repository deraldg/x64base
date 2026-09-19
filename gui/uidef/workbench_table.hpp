// @dottalk.file v1
// subsystem: gui
// layer: service
// owns: bounded snapshots of the selected live table
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#pragma once
#include <cstdint>
#include <string>
#include <vector>
namespace xbase { class XBaseEngine; }
namespace dottalk::workbench {
struct TableField { std::string name; char type{}; unsigned length{}; };
struct TableRow {
    std::uint64_t recno{};
    bool deleted{}, pending{}, delete_pending{};
    std::vector<std::string> values;
};
struct TablePage {
    std::uint64_t area_handle{}, records{}, current_record{}, offset{};
    std::size_t pending_records{};
    int slot{-1};
    std::string name, order, error;
    bool open{}, filtered{}, expression_filter{}, deleted_hidden{}, buffered{}, more{}, limited{};
    std::vector<TableField> fields;
    std::vector<TableRow> rows;
};
struct FieldValue {
    std::string title, text, error, edit_reason;
    std::uint64_t bytes{};
    bool memo{}, binary{}, pending{}, truncated{}, editable{};
};
struct FieldEdit {
    int slot{-1}, field1{};
    std::uint64_t handle{}, record{};
    std::string field_name, expected_value, value;
};
struct MemoPayload {
    std::string bytes, provenance, label, error;
};
struct MemoTarget {
    FieldEdit edit;
    std::string title, error;
};
// Validate a selected DTX field without loading its existing payload. The
// returned reference is compared again before allocating a replacement object.
MemoTarget read_memo_target(xbase::XBaseEngine& engine, FieldEdit edit);
std::string stage_memo_image(xbase::XBaseEngine& engine, const FieldEdit& edit, const std::string& payload);
// Explicit image inspection reads a committed memo under a caller-supplied
// byte budget. It never treats a pending buffer value as a stored reference.
MemoPayload read_field_memo(xbase::XBaseEngine& engine, int slot, std::uint64_t handle,
                           std::uint64_t record, int field1, const std::string& field_name,
                           std::size_t limit);
// Literal scalar or DTX memo text through the validators and buffered write
// funnel. Returns an error, or empty after verifying the actual buffer value.
std::string stage_field_edit(xbase::XBaseEngine& engine, const FieldEdit& edit);
std::string set_field_null(xbase::XBaseEngine& engine, const FieldEdit& edit);
TablePage read_table_page(xbase::XBaseEngine& engine, std::uint64_t offset = 0, bool follow_cursor = false);
FieldValue read_field_value(xbase::XBaseEngine& engine, int slot, std::uint64_t handle,
                           std::uint64_t record, int field1, const std::string& field_name);
}
