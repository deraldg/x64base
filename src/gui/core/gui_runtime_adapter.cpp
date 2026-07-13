#include "gui/core/gui_runtime_adapter.hpp"

#include "cli/order_iterator.hpp"
#include "cli/order_state.hpp"
#include "xbase.hpp"

#include <algorithm>
#include <exception>
#include <filesystem>
#include <limits>
#include <string>
#include <vector>

namespace dottalk::gui {

namespace {

StatusMessage adapter_status(Severity severity, std::string code, std::string text, std::string detail = {}) {
    StatusMessage message;
    message.severity = severity;
    message.code = std::move(code);
    message.text = std::move(text);
    message.detail = std::move(detail);
    return message;
}

StatusMessage adapter_warning(std::string code, std::string text, std::string detail = {}) {
    return adapter_status(Severity::warning, std::move(code), std::move(text), std::move(detail));
}

StatusMessage adapter_error(std::string code, std::string text, std::string detail = {}) {
    return adapter_status(Severity::error, std::move(code), std::move(text), std::move(detail));
}

int32_t clamp_runtime_recno(std::uint64_t value) {
    if (value == 0) {
        return 1;
    }
    if (value > static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max())) {
        return std::numeric_limits<int32_t>::max();
    }
    return static_cast<int32_t>(value);
}

std::filesystem::path runtime_path(const xbase::DbArea& area) {
    return std::filesystem::path(area.filename());
}

std::size_t ordered_start_index(const std::vector<std::uint64_t>& recnos,
                                std::uint64_t current_record,
                                std::uint64_t first_record,
                                std::uint32_t max_records) {
    if (recnos.empty()) {
        return 0;
    }
    if (first_record > 0) {
        return static_cast<std::size_t>(std::min<std::uint64_t>(first_record - 1, recnos.size() - 1));
    }

    auto it = std::find(recnos.begin(), recnos.end(), current_record);
    if (it == recnos.end()) {
        return 0;
    }

    std::uint64_t index = static_cast<std::uint64_t>(std::distance(recnos.begin(), it));
    if (max_records > 1) {
        index -= std::min<std::uint64_t>(index, max_records / 2);
    }
    if (recnos.size() >= max_records && index + max_records > recnos.size()) {
        index = static_cast<std::uint64_t>(recnos.size() - max_records);
    }
    return static_cast<std::size_t>(index);
}

bool gps_visible_record(xbase::DbArea& area, std::uint64_t recno) {
    if (recno == 0 || recno > area.recCount64() ||
        recno > static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max())) {
        return false;
    }
    if (!area.gotoRec(static_cast<int32_t>(recno)) || !area.readCurrent()) {
        return false;
    }
    return !area.isDeleted();
}

std::uint64_t compute_gps_logical_row(xbase::DbArea& area, std::uint64_t physical_record) {
    if (physical_record == 0 || physical_record > area.recCount64()) {
        return 0;
    }

    std::uint64_t logical = 0;
    cli::OrderIterSpec spec{};
    std::string err;
    (void)cli::order_iterate_recnos(
        area,
        [&](std::uint64_t recno) -> bool {
            if (!gps_visible_record(area, recno)) {
                return true;
            }
            ++logical;
            return recno != physical_record;
        },
        &spec,
        &err);
    return logical;
}

void populate_cursor_state(TableSnapshot& snapshot, xbase::DbArea& area, int32_t saved_recno) {
    snapshot.physical_record_number = saved_recno > 0 ? static_cast<std::uint64_t>(saved_recno) : 0;
    snapshot.current_record_number = snapshot.physical_record_number;
    snapshot.ordered = orderstate::hasOrder(area);
    snapshot.order_ascending = orderstate::isAscending(area);
    if (snapshot.ordered) {
        snapshot.order_name = orderstate::orderName(area);
        snapshot.order_tag = orderstate::activeTag(area);
    }

    snapshot.logical_record_number = compute_gps_logical_row(area, snapshot.physical_record_number);
    if (saved_recno > 0 && saved_recno <= area.recCount()) {
        (void)area.gotoRec(saved_recno);
        (void)area.readCurrent();
    }
}

} // namespace

AreaInfo gui_area_info_from_dbarea(AreaId area_id,
                                   bool active,
                                   const xbase::DbArea& area,
                                   const std::string& display_name) {
    AreaInfo info;
    info.area_id = area_id;
    info.active = active;
    info.path = runtime_path(area);
    info.display_name = display_name.empty() ? area.logicalName() : display_name;
    if (info.display_name.empty()) {
        info.display_name = info.path.filename().string();
    }
    info.record_count = area.isOpen() ? area.recCount64() : 0;
    info.field_count = area.isOpen() ? static_cast<std::uint64_t>(area.fields().size()) : 0;
    return info;
}

TableSnapshot gui_snapshot_from_dbarea(AreaId area_id,
                                       xbase::DbArea& area,
                                       const std::string& display_name,
                                       std::uint64_t first_record,
                                       std::uint32_t max_records) {
    TableSnapshot snapshot;
    snapshot.area_id = area_id;

    if (!area.isOpen()) {
        snapshot.messages.push_back(adapter_warning("gui.snapshot.no_current_table",
                                                    "No current table is selected."));
        return snapshot;
    }

    try {
        const std::filesystem::path path = runtime_path(area);
        snapshot.display_name = display_name.empty() ? area.logicalName() : display_name;
        if (snapshot.display_name.empty()) {
            snapshot.display_name = path.filename().string();
        }

        const auto& fields = area.fields();
        snapshot.columns.reserve(fields.size());
        for (const auto& field : fields) {
            snapshot.columns.push_back(TableColumn{
                field.name,
                field.type,
                static_cast<int>(field.length),
                static_cast<int>(field.decimals)
            });
        }

        const std::uint64_t total = area.recCount64();
        snapshot.total_records = total;
        const int32_t saved_recno = area.recno();
        populate_cursor_state(snapshot, area, saved_recno);

        if (total == 0 || max_records == 0) {
            snapshot.truncated = total > 0;
            return snapshot;
        }

        if (orderstate::hasOrder(area)) {
            std::vector<std::uint64_t> ordered_recnos;
            std::string order_error;
            cli::OrderIterSpec spec;
            if (cli::order_collect_recnos_asc(area, ordered_recnos, &spec, &order_error)) {
                if (!spec.ascending) {
                    std::reverse(ordered_recnos.begin(), ordered_recnos.end());
                }

                const std::size_t start = ordered_start_index(ordered_recnos,
                                                              snapshot.current_record_number,
                                                              first_record,
                                                              max_records);
                const std::size_t end = std::min<std::size_t>(ordered_recnos.size(),
                                                              start + static_cast<std::size_t>(max_records));
                snapshot.truncated = end < ordered_recnos.size();
                snapshot.rows.reserve(end - start);

                for (std::size_t i = start; i < end; ++i) {
                    const std::uint64_t recno = ordered_recnos[i];
                    if (recno == 0 || recno > static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max()) ||
                        !area.gotoRec(static_cast<int32_t>(recno))) {
                        snapshot.messages.push_back(adapter_warning("gui.snapshot.record_read_failed",
                                                                    "Stopped ordered snapshot because a record could not be read."));
                        break;
                    }

                    TableRow row;
                    row.record_number = recno;
                    row.deleted = area.isDeleted();
                    row.values.reserve(fields.size());
                    for (std::size_t field_index = 0; field_index < fields.size(); ++field_index) {
                        row.values.push_back(area.get(static_cast<int>(field_index + 1)));
                    }
                    snapshot.rows.push_back(std::move(row));
                }

                if (saved_recno > 0 && saved_recno <= area.recCount()) {
                    (void)area.gotoRec(saved_recno);
                }
                return snapshot;
            }

            snapshot.messages.push_back(adapter_warning("gui.snapshot.order_unavailable",
                                                        "Active order could not be used; falling back to physical order.",
                                                        order_error));
        }

        std::uint64_t first = std::max<std::uint64_t>(1, first_record);
        if (first_record == 0 && snapshot.current_record_number > 0) {
            first = snapshot.current_record_number;
            if (max_records > 1) {
                first -= std::min<std::uint64_t>(first - 1, max_records / 2);
            }
            if (total >= max_records && first + max_records - 1 > total) {
                first = total - max_records + 1;
            }
        }
        if (first > total) {
            snapshot.messages.push_back(adapter_warning("gui.snapshot.first_record_past_end",
                                                        "Requested first record is past the end of the table."));
            return snapshot;
        }

        const std::uint64_t available = total - first + 1;
        const std::uint64_t count = std::min<std::uint64_t>(available, max_records);
        snapshot.truncated = count < available;
        snapshot.rows.reserve(static_cast<std::size_t>(std::min<std::uint64_t>(count, 100000)));

        for (std::uint64_t offset = 0; offset < count; ++offset) {
            const std::uint64_t recno = first + offset;
            if (!area.gotoRec(clamp_runtime_recno(recno))) {
                snapshot.messages.push_back(adapter_warning("gui.snapshot.record_read_failed",
                                                            "Stopped snapshot because a record could not be read."));
                break;
            }

            TableRow row;
            row.record_number = recno;
            row.deleted = area.isDeleted();
            row.values.reserve(fields.size());
            for (std::size_t i = 0; i < fields.size(); ++i) {
                row.values.push_back(area.get(static_cast<int>(i + 1)));
            }
            snapshot.rows.push_back(std::move(row));
        }

        if (saved_recno > 0 && saved_recno <= area.recCount()) {
            (void)area.gotoRec(saved_recno);
        }
    } catch (const std::exception& ex) {
        snapshot.messages.push_back(adapter_error("gui.snapshot.failed",
                                                  "Unable to build table snapshot.",
                                                  ex.what()));
    } catch (...) {
        snapshot.messages.push_back(adapter_error("gui.snapshot.failed",
                                                  "Unable to build table snapshot.",
                                                  "unknown error"));
    }

    return snapshot;
}

} // namespace dottalk::gui
