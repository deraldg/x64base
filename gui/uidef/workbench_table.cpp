// @dottalk.file v1
// subsystem: gui
// layer: service
// owns: live table and memo readback without cursor movement
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_table.hpp"
#include "xbase.hpp"
#include "xbase_64.hpp"
#include "cli/order_iterator.hpp"
#include "cli/order_state.hpp"
#include "cli/table_object.hpp"
#include "cli/null_display.hpp"
#include "cli/settings.hpp"
#include "xbase_cli.hpp"
#include "cli/field_store_validation.hpp"
#include "cli/cli_currency.hpp"
#include "shell_commands.hpp"
#include "sqlsel_statement.hpp"
#include "filters/filter_registry.hpp"
#include "memo/memo_auto.hpp"
#include "memo/memostore.hpp"
#include "dottalk/minidb.hpp"
#include <algorithm>
#include <charconv>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <set>

namespace dottalk::workbench {
namespace {
constexpr std::size_t page_size = 100, scan_limit = 100000, cell_limit = 256;
struct RestoreCursor {
    xbase::DbArea& area;
    std::uint64_t record;
    explicit RestoreCursor(xbase::DbArea& a) : area(a), record(a.recno64()) {
        if (a.recCount64() && (!record || record > a.recCount64()))
            throw std::runtime_error("Position the table with GO TOP before browsing.");
    }
    ~RestoreCursor() { try { if (record) area.gotoRec64(record); } catch (...) {} }
};
std::string short_cell(std::string value) {
    while (!value.empty() && value.back() == ' ') value.pop_back();
    const bool shortened = value.size() > cell_limit;
    value.resize(std::min(value.size(), cell_limit));
    for (auto& c : value) if (static_cast<unsigned char>(c) < 32) c = ' ';
    return value + (shortened ? "..." : "");
}
std::string raw_value(xbase::DbArea& area, int field1, const table::Overlay& overlay) {
    const auto changed = overlay.new_values.find(field1);
    if (changed != overlay.new_values.end()) return changed->second;
    if (cli::nulldisp::is_null_cell(area, field1)) return cli::nulldisp::kMarker;
    return area.get(field1);
}
std::string resolve_memo(xbase::DbArea& area, int field1, const std::string& value,
                         std::size_t limit, std::uint64_t& bytes) {
    if (value.empty() || value == "0") { bytes = 0; return {}; }
    auto* backend = cli_memo::memo_backend_for(area);
    if (!backend) throw std::runtime_error("No memo backend is attached to this table.");
    memo::MemoRef ref{value};
    if (area.versionByte() == xbase::DBF_VERSION_64 && area.fields()[field1 - 1].length == xbase::X64_MEMO_FIELD_LEN) {
        std::uint64_t id{};
        const auto parsed = std::from_chars(value.data(), value.data() + value.size(), id);
        auto* store = dynamic_cast<memo::MemoStore*>(backend);
        if (parsed.ec != std::errc{} || parsed.ptr != value.data() + value.size() || !store)
            throw std::runtime_error("Invalid or unsupported x64 memo reference");
        ref = store->ref_from_object_id(id);
    }
    const auto stat = backend->stat(ref);
    if (!stat.exists) throw std::runtime_error("Memo object is missing or deleted");
    bytes = stat.logical_bytes;
    if (bytes > limit) throw std::runtime_error("Memo exceeds the " + std::to_string(limit / (1024 * 1024)) + " MiB read limit.");
    auto read = backend->get_text(ref);
    if (!read.ok) throw std::runtime_error(read.error);
    if (read.text.size() != bytes || read.text.size() > limit)
        throw std::runtime_error("Memo changed while reading; retry when its writer is idle.");
    return std::move(read.text);
}
}
MemoTarget read_memo_target(xbase::XBaseEngine& engine, FieldEdit edit) {
    MemoTarget result; result.edit = std::move(edit);
    try {
        auto& e = result.edit;
        if (sqlsel::transaction_active()) throw std::runtime_error("End the active SQL transaction before storing an image.");
        if (e.slot < 0 || e.slot >= xbase::MAX_AREA || e.slot != engine.currentArea())
            throw std::runtime_error("The selected area changed; select the memo field again.");
        auto& area = engine.area(e.slot);
        if (!area.isOpen() || !e.handle || area.areaHandle() != e.handle)
            throw std::runtime_error("Table selection is stale; refresh the view.");
        if (e.field1 < 1 || e.field1 > area.fieldCount() || area.fields()[e.field1 - 1].name != e.field_name)
            throw std::runtime_error("Field selection is stale; refresh the view.");
        const auto& field = area.fields()[e.field1 - 1];
        const bool fixed = area.versionByte() == xbase::DBF_VERSION_64 && field.length == xbase::X64_MEMO_FIELD_LEN;
        if ((field.type != 'M' && field.type != 'm') || (!fixed && field.length != 16))
            throw std::runtime_error("Select a fixed x64 or 16-byte token memo field.");
        if (!e.record || e.record > area.recCount64()) throw std::runtime_error("Record is no longer available.");
        RestoreCursor restore(area);
        if (!area.gotoRec64(e.record)) throw std::runtime_error("Cannot read the selected record.");
        const auto overlay = table::is_enabled(e.slot) ? table::Table(engine, e.slot).overlay_for(e.record) : table::Overlay{};
        if (area.isDeleted() || (overlay.flags & (table::CHANGE_DELETE | table::CHANGE_INSERT)))
            throw std::runtime_error("Resolve this record's deletion or insertion before storing an image.");
        if (overlay.new_values.count(e.field1))
            throw std::runtime_error("Commit or roll back this memo before storing another image.");
        if (cli::nulldisp::is_null_cell(area, e.field1))
            throw std::runtime_error("NULL memo values require the command console first.");
        auto* store = dynamic_cast<memo::MemoStore*>(cli_memo::memo_backend_for(area));
        if (!store || !store->is_open()) throw std::runtime_error("Store image requires an attached DTX memo backend.");
        e.expected_value = area.get(e.field1);
        std::string error;
        if (!xbase::cli::gateFieldWrites(area, {{e.field1, e.expected_value}}, &error)) throw std::runtime_error(error);
        result.title = area.name() + " / record " + std::to_string(e.record) + " / " + e.field_name;
    } catch (const std::exception& e) { result.error = e.what(); }
    return result;
}

std::string stage_memo_image(xbase::XBaseEngine& engine, const FieldEdit& edit, const std::string& payload) {
    try {
        if (payload.size() > 128ull * 1024 * 1024) return "Image exceeds the 128 MiB storage limit.";
        const auto scan = minidb::scan(payload);
        if (!scan.ok) return "Cannot store an invalid MINIDB image: " + scan.error;
        const auto target = read_memo_target(engine, edit);
        if (!target.error.empty()) return target.error;
        if (target.edit.expected_value != edit.expected_value)
            return "The memo reference changed; select the field again before storing an image.";
        auto& area = engine.area(edit.slot);
        RestoreCursor restore(area);
        if (!area.gotoRec64(edit.record)) return "Cannot read the selected record.";
        auto* store = dynamic_cast<memo::MemoStore*>(cli_memo::memo_backend_for(area));
        if (!store) return "Memo backend changed; select the field again.";
        // Always allocate a new object. Shared references to the prior object
        // and a rollback of this reference must both keep the original bytes.
        const auto put = store->put_text(payload);
        if (!put.ok) return "Could not allocate the image memo: " + put.error;
        std::string stored = put.ref.token, error;
        if (area.versionByte() == xbase::DBF_VERSION_64 && area.fields()[edit.field1 - 1].length == xbase::X64_MEMO_FIELD_LEN) {
            std::uint64_t id{};
            if (!store->try_object_id_from_ref(put.ref, id) || !id) return "Cannot encode the new memo object reference.";
            stored = std::to_string(id);
        }
        if (!fieldstore::validate_and_normalize(area, edit.field1, stored, error)) return error;
        std::uint64_t size{};
        if (resolve_memo(area, edit.field1, stored, 128 * 1024 * 1024, size) != payload)
            return "Image memo readback differs; its reference was not buffered.";
        const auto flushed = store->flush();
        if (!flushed.ok) return "Image memo flush failed: " + flushed.error;
        if (!table::is_enabled(edit.slot)) {
            std::istringstream on("ON"); cmd_TABLE_BUFFER(area, on);
            if (!table::is_enabled(edit.slot)) return "Could not enable the table buffer; image reference was not written.";
        }
        if (!xbase::cli::replaceFieldStored(area, edit.field1, stored, &error))
            return error.empty() ? "Could not buffer the image reference." : error;
        const auto after = table::Table(engine, edit.slot).overlay_for(edit.record);
        const auto found = after.new_values.find(edit.field1);
        if (found == after.new_values.end() || found->second != stored || area.get(edit.field1) != edit.expected_value)
            return "Image reference readback failed. Inspect TABLE STATUS before continuing.";
        return error;
    } catch (const std::exception& e) { return e.what(); }
}

MemoPayload read_field_memo(xbase::XBaseEngine& engine, int slot, std::uint64_t handle,
                           std::uint64_t record, int field1, const std::string& field_name,
                           std::size_t limit) {
    MemoPayload result;
    try {
        if (slot < 0 || slot >= xbase::MAX_AREA) throw std::runtime_error("Invalid area slot");
        auto& area = engine.area(slot);
        if (!area.isOpen() || !handle || area.areaHandle() != handle)
            throw std::runtime_error("Table selection is stale; refresh the view.");
        if (field1 < 1 || field1 > area.fieldCount() || area.fields()[field1 - 1].name != field_name)
            throw std::runtime_error("Field selection is stale; refresh the view.");
        if (area.fields()[field1 - 1].type != 'M' && area.fields()[field1 - 1].type != 'm')
            throw std::runtime_error("Select a memo field containing a MINIDB image.");
        if (!record || record > area.recCount64()) throw std::runtime_error("Record is no longer available");
        RestoreCursor restore(area);
        if (!area.gotoRec64(record)) throw std::runtime_error("Cannot read the selected record");
        const auto overlay = table::is_enabled(slot) ? table::Table(engine, slot).overlay_for(record) : table::Overlay{};
        if (overlay.new_values.count(field1)) throw std::runtime_error("Commit or roll back this memo before inspecting its image.");
        if (cli::nulldisp::is_null_cell(area, field1)) throw std::runtime_error("The selected memo is NULL.");
        std::uint64_t bytes{};
        result.bytes = resolve_memo(area, field1, area.get(field1), limit, bytes);
        result.provenance = area.filename() + " / area " + std::to_string(handle) + " / record " +
            std::to_string(record) + " / field " + field_name + " / committed memo";
        result.label = area.name() + " / record " + std::to_string(record) + " / field " + field_name + " / committed memo";
    } catch (const std::exception& e) { result.error = e.what(); }
    return result;
}
TablePage read_table_page(xbase::XBaseEngine& engine, std::uint64_t offset, bool follow_cursor) {
    TablePage page; page.slot = engine.currentArea(); page.offset = offset;
    auto& area = engine.area(page.slot);
    if (!area.isOpen()) return page;
    page.open = true; page.area_handle = area.areaHandle(); page.name = area.name();
    page.records = area.recCount64(); page.current_record = area.recno64();
    page.filtered = filter::view_is_filtered(&area);
    page.expression_filter = filter::has_active_filter(&area);
    page.deleted_hidden = cli::Settings::instance().deleted_on.load();
    page.buffered = table::is_enabled(page.slot);
    std::set<std::uint64_t> changed_records;
    for (const auto& [record, change] : table::get_tb_const(page.slot).changes) changed_records.insert(record);
    page.pending_records = changed_records.size();
    page.order = orderstate::isNaturalOrder(area) ? "NATURAL" : orderstate::orderName(area) + " / " + orderstate::activeTag(area);
    page.order += orderstate::isNaturalOrder(area) || orderstate::isAscending(area) ? " ASC" : " DESC";
    for (const auto& field : area.fields()) page.fields.push_back({field.name, field.type, field.length});
    try {
        RestoreCursor restore(area);
        if (follow_cursor && page.current_record) {
            std::uint64_t visible = 0, scanned = 0;
            cli::order_stream_display(area, false, [&](std::uint64_t record) {
                if (++scanned > scan_limit || !area.gotoRec64(record)) return false;
                if (!filter::visible(&area, {})) return true;
                if (record == page.current_record) { offset = (visible / page_size) * page_size; return false; }
                ++visible; return true;
            });
            page.offset = offset;
        }
        table::Table table(engine, page.slot);
        std::uint64_t visible = 0, scanned = 0;
        std::string error;
        cli::OrderIterSpec order;
        const bool ok = cli::order_stream_display(area, false, [&](std::uint64_t record) {
            if (++scanned > scan_limit) { page.limited = true; return false; }
            if (!area.gotoRec64(record)) throw std::runtime_error("Cannot read record " + std::to_string(record));
            if (!filter::visible(&area, {})) return true;
            if (visible++ < offset) return true;
            if (page.rows.size() == page_size) { page.more = true; return false; }
            const auto overlay = page.buffered ? table.overlay_for(record) : table::Overlay{};
            TableRow row; row.recno = record; row.deleted = area.isDeleted(); row.pending = overlay.has;
            row.delete_pending = (overlay.flags & table::CHANGE_DELETE) != 0;
            for (int field1 = 1; field1 <= area.fieldCount(); ++field1) {
                auto value = raw_value(area, field1, overlay);
                const char type = page.fields[field1 - 1].type;
                if ((type == 'M' || type == 'm') && value != cli::nulldisp::kMarker)
                    value = value.empty() || value == "0" ? "[empty memo]" : "[memo: open value]";
                row.values.push_back(short_cell(std::move(value)));
            }
            page.rows.push_back(std::move(row)); return true;
        }, &order, &error);
        if (!ok) throw std::runtime_error(error.empty() ? "Cannot read the current order" : error);
        page.order = order.backend == cli::OrderBackend::Natural ? "NATURAL ASC" :
            order.container_path + (order.tag.empty() ? "" : " / " + order.tag) + (order.ascending ? " ASC" : " DESC");
    } catch (const std::exception& e) { page.error = e.what(); page.rows.clear(); }
    return page;
}

FieldValue read_field_value(xbase::XBaseEngine& engine, int slot, std::uint64_t handle,
                           std::uint64_t record, int field1, const std::string& field_name) {
    FieldValue result;
    try {
        if (slot < 0 || slot >= xbase::MAX_AREA) throw std::runtime_error("Invalid area slot");
        auto& area = engine.area(slot);
        if (!area.isOpen() || !handle || area.areaHandle() != handle)
            throw std::runtime_error("Table selection is stale; refresh the view.");
        if (field1 < 1 || field1 > area.fieldCount() || area.fields()[field1 - 1].name != field_name)
            throw std::runtime_error("Field selection is stale; refresh the view.");
        RestoreCursor restore(area);
        if (!area.gotoRec64(record)) throw std::runtime_error("Record is no longer available");
        const auto& field = area.fields()[field1 - 1];
        result.title = area.name() + " / record " + std::to_string(record) + " / " + field.name;
        const auto overlay = table::is_enabled(slot) ? table::Table(engine, slot).overlay_for(record) : table::Overlay{};
        result.pending = overlay.new_values.count(field1) != 0;
        std::string value = raw_value(area, field1, overlay);
        result.memo = field.type == 'M' || field.type == 'm';
        if (result.memo && !dynamic_cast<memo::MemoStore*>(cli_memo::memo_backend_for(area)))
            result.edit_reason = "Memo editing currently requires a DTX memo backend.";
        else if (result.memo && !(field.length == 16 || (area.versionByte() == xbase::DBF_VERSION_64 && field.length == xbase::X64_MEMO_FIELD_LEN)))
            result.edit_reason = "This memo reference format is inspect-only.";
        else if (!result.memo && std::string("CNFIBYDTL").find(field.type) == std::string::npos)
            result.edit_reason = "This field type is inspect-only in the value editor.";
        else if (cli::nulldisp::is_null_cell(area, field1)) result.edit_reason = "NULL values require the command console.";
        else if (area.isDeleted() || (overlay.flags & table::CHANGE_DELETE)) result.edit_reason = "Recall or roll back this deleted record before editing its values.";
        else {
            std::string refusal;
            if (!xbase::cli::gateFieldWrites(area, {{field1, value}}, &refusal)) result.edit_reason = refusal;
        }
        if (result.memo && value != cli::nulldisp::kMarker) {
            // GUI edits stage a new DTX reference. Legacy token-memo REPLACE
            // can instead buffer literal text; preserve that established view.
            bool reference = !result.pending;
            if (result.pending) {
                auto* store = dynamic_cast<memo::MemoStore*>(cli_memo::memo_backend_for(area));
                if (store) {
                    if (field.length == xbase::X64_MEMO_FIELD_LEN && area.versionByte() == xbase::DBF_VERSION_64) reference = true;
                    else reference = value.empty() || store->stat(memo::MemoRef{value}).exists;
                }
            }
            if (reference) value = resolve_memo(area, field1, value, 1024 * 1024, result.bytes);
            if (value.rfind("MINIDB ", 0) == 0) result.edit_reason = "Database images use Inspect image and Store image; text editing is disabled.";
        }
        result.bytes = value.size();
        result.binary = std::any_of(value.begin(), value.end(), [](unsigned char c) { return c < 32 && c != '\n' && c != '\r' && c != '\t'; });
        const auto limit = result.binary ? std::size_t{4096} : std::size_t{65536};
        result.truncated = value.size() > limit;
        if (result.binary || result.truncated) result.edit_reason = "Binary or truncated values are inspect-only.";
        result.editable = result.edit_reason.empty();
        value.resize(std::min(value.size(), limit));
        if (result.binary) {
            std::ostringstream hex; hex << "Binary value - hexadecimal preview\n" << std::hex << std::setfill('0');
            for (std::size_t i = 0; i < value.size(); ++i) {
                if (i % 16 == 0) hex << std::setw(8) << i << "  ";
                hex << std::setw(2) << static_cast<unsigned>(static_cast<unsigned char>(value[i])) << ' ';
                if (i % 16 == 15) hex << '\n';
            }
            result.text = hex.str();
        } else result.text = std::move(value);
        if (result.truncated) result.text += "\n[Preview truncated]\n";
    } catch (const std::exception& e) { result.error = e.what(); }
    return result;
}

std::string set_field_null(xbase::XBaseEngine& engine, const FieldEdit& edit) {
    try {
        if (sqlsel::transaction_active()) return "End the active SQL transaction first.";
        if (edit.slot != engine.currentArea()) return "The selected area changed; reopen the editor.";
        const auto before = read_field_value(engine, edit.slot, edit.handle, edit.record, edit.field1, edit.field_name);
        if (!before.error.empty()) return before.error;
        if (before.text != edit.expected_value) return "The field changed while the dialog was open.";
        auto& area = engine.area(edit.slot); RestoreCursor restore(area);
        if (!area.gotoRec64(edit.record)) return "Record is no longer available.";
        if (area.isDeleted()) return "Recall this record before editing.";
        if (table::is_enabled(edit.slot) || !table::get_tb_const(edit.slot).empty() || table::is_dirty(edit.slot))
            return "NULL cannot be buffered. Finish edits and explicitly use TABLE OFF first. Nothing was written.";
        std::string error;
        if (!xbase::cli::replaceFieldNull(area, edit.field1, true, &error)) return error.empty() ? "NULL write refused." : error;
        if (!cli::nulldisp::is_null_cell(area, edit.field1)) return "NULL readback failed.";
        return error;
    } catch (const std::exception& e) { return e.what(); }
}

std::string stage_field_edit(xbase::XBaseEngine& engine, const FieldEdit& edit) {
    try {
        if (sqlsel::transaction_active()) return "End the active SQL transaction before using the native value editor.";
        if (edit.slot != engine.currentArea()) return "The selected area changed; reopen the value editor.";
        const auto before = read_field_value(engine, edit.slot, edit.handle, edit.record, edit.field1, edit.field_name);
        if (!before.error.empty()) return before.error;
        if (!before.editable) return before.edit_reason;
        if (before.text != edit.expected_value) return "The field changed while the editor was open; reopen it before editing.";
        auto& area = engine.area(edit.slot);
        RestoreCursor restore(area);
        if (!area.gotoRec64(edit.record)) return "Record is no longer available.";
        const auto& field = area.fields()[edit.field1 - 1];
        if (edit.value.size() > 65536 || edit.value.find('\0') != std::string::npos)
            return "The value editor accepts at most 64 KiB of text without NUL bytes.";
        if (field.type == 'C' && edit.value.size() > field.length) return "Text exceeds the field's byte width.";
        if (edit.value == before.text) return {};
        std::string stored, error;
        if (before.memo) {
            auto* store = dynamic_cast<memo::MemoStore*>(cli_memo::memo_backend_for(area));
            if (!store) return "The DTX memo backend changed.";
            // A fresh object preserves shared references and rollback. Never
            // update the old memo object in place while TABLE is buffering.
            if (!edit.value.empty()) {
                const auto put = store->put_text(edit.value);
                if (!put.ok) return put.error;
                stored = put.ref.token;
                if (area.versionByte() == xbase::DBF_VERSION_64 && field.length == xbase::X64_MEMO_FIELD_LEN) {
                    std::uint64_t id{};
                    if (!store->try_object_id_from_ref(put.ref, id) || !id) return "Cannot encode the new memo reference.";
                    stored = std::to_string(id);
                }
                std::uint64_t size{};
                if (resolve_memo(area, edit.field1, stored, 65536, size) != edit.value) return "Memo readback differs; reference was not staged.";
                const auto flushed = store->flush(); if (!flushed.ok) return flushed.error;
            }
        } else if (!cli_currency::validate_and_normalize_currency_pair_field(area, edit.field1, edit.value, stored, error)) return error;
        if (!fieldstore::validate_and_normalize(area, edit.field1, stored, error)) return error;
        if (!xbase::cli::gateFieldWrites(area, {{edit.field1, stored}}, &error)) return error;
        if (!before.memo && stored == before.text) return {};
        if (!table::is_enabled(edit.slot)) {
            std::istringstream on("ON"); cmd_TABLE_BUFFER(area, on);
            if (!table::is_enabled(edit.slot)) return "Could not enable the table buffer; nothing was written.";
        }
        if (!xbase::cli::replaceFieldStored(area, edit.field1, stored, &error)) return error.empty() ? "Could not buffer the value." : error;
        const auto after = table::Table(engine, edit.slot).overlay_for(edit.record);
        const auto found = after.new_values.find(edit.field1);
        if (found == after.new_values.end() || found->second != stored)
            return "The requested value was not read back from the buffer. Inspect TABLE STATUS before continuing.";
        return error;
    } catch (const std::exception& e) { return e.what(); }
}
}
