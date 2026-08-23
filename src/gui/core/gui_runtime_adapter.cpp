// @dottalk.file v1
// subsystem: gui
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "gui/core/gui_runtime_adapter.hpp"
#include "xbase/workspace_membership.hpp"   // an area knows its workspace (AIF-078)

#include "cli/order_iterator.hpp"
#include "cli/order_state.hpp"
#include "xbase.hpp"
#include "common/path_state.hpp"
#include "memo/memo_auto.hpp"
#include "memo/memo_ref.hpp"

#include <cctype>
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

std::string gui_workspace_of_area(AreaId /*area_id*/) {
    // STILL A STUB, and now for a NARROWER reason than the one it used to give.
    //
    // It used to say "no owner back-pointer ... until the registry lands." The
    // registry landed (AIF-078), and an area DOES know its workspace -- see the
    // DbArea overload below, which is exact. What is still missing is a way to
    // get from an AreaId to an area, because AreaId itself had two spellings in
    // one type: session.cpp minted a private counter while another path derived
    // it as engine slot + 1. Unifying those onto DbArea::areaHandle() is the
    // next step and is what makes this body writable.
    //
    // Deliberately still ignores the id rather than pretending to consult
    // something -- and returns a real name rather than an empty string, because
    // invariant I1 says there is no null workspace.
    return std::string(kDefaultWorkspace);
}

std::string gui_workspace_of_area(const xbase::DbArea& area) {
    const std::uint64_t handle = area.wsHandle();
    if (handle == 0) {
        // Closed areas carry handle 0 -- "no workspace" -- and I1 says a name
        // must still come back.
        return std::string(kDefaultWorkspace);
    }
    const std::string name = xbase::workspace::name_of(handle);
    return name.empty() ? std::string(kDefaultWorkspace) : name;
}

AreaInfo gui_area_info_from_dbarea(AreaId area_id,
                                   bool active,
                                   const xbase::DbArea& area,
                                   const std::string& display_name) {
    AreaInfo info;
    info.area_id = area_id;
    // The AREA is in hand here, so ask the exact question rather than the
    // one that still cannot be answered from an id alone.
    info.workspace = gui_workspace_of_area(area);
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

// ---- AIF-120: the memo read path -------------------------------------------

namespace {

std::filesystem::path workspaces_catalog_path() {
    // Same slot and filename as cmd_workspace.cpp's WORKSPACE_root() /
    // catalog_path(). Not a second convention -- the same one, read.
    return dottalk::paths::get_slot(dottalk::paths::Slot::WORKSPACES) / "WORKSPACES.dbf";
}

// AIF-120. Case-insensitive field lookup over DbArea's PUBLIC fields()
// accessor.
//
// This is the third such lookup in the tree and I would rather reuse one of the
// existing two, but neither is reachable from here: DbArea's member version is
// private (include/xbase.hpp:464), and the free function in the fields
// namespace lives in src/core/fields_mgr.cpp -- 911 lines that include
// xindex/attach.hpp and xindex/index_manager.hpp, so linking it would pull
// xindex into dottalk_gui_core, which today needs only xbase and memo.
// Expanding a library's dependency graph to reach one function is the worse
// trade. Recorded here so the duplication is deliberate and findable.
//
// Returns a 0-BASED index to match the other two, so callers keep using
// get(i + 1) against DbArea's 1-based slots.
int find_field_ci(const xbase::DbArea& a, const char* name) {
    const auto& defs = a.fields();
    for (std::size_t i = 0; i < defs.size(); ++i) {
        const std::string& have = defs[i].name;
        std::size_t k = 0;
        for (; k < have.size() && name[k]; ++k) {
            const auto x = std::tolower(static_cast<unsigned char>(have[k]));
            const auto y = std::tolower(static_cast<unsigned char>(name[k]));
            if (x != y) break;
        }
        if (k == have.size() && name[k] == '\0') return static_cast<int>(i);
    }
    return -1;
}

std::string catalog_field(const xbase::DbArea& a, const char* name) {
    const int i = find_field_ci(a, name);
    if (i < 0) return {};
    try { return a.get(i + 1); } catch (...) { return {}; }
}

std::string trim_ascii_copy(std::string v) {
    auto sp = [](char ch) noexcept {
        return std::isspace(static_cast<unsigned char>(ch)) != 0;
    };
    std::size_t b = 0, e = v.size();
    while (b < e && sp(v[b])) ++b;
    while (e > b && sp(v[e - 1])) --e;
    return v.substr(b, e - b);
}

std::uint64_t to_u64(const std::string& v) {
    const std::string t = trim_ascii_copy(v);
    if (t.empty()) return 0;
    try { return static_cast<std::uint64_t>(std::stoull(t)); } catch (...) { return 0; }
}

// Open the catalog READ-ONLY with its memo sidecar attached. Never creates.
bool open_catalog_readonly(xbase::DbArea& a, std::string& error) {
    const auto path = workspaces_catalog_path();
    std::error_code ec;
    if (!std::filesystem::exists(path, ec) || ec) {
        error = "No workspace catalog at " + path.string() +
                ". Save a workspace to the memo first; this view never creates one.";
        return false;
    }
    try { a.open(path.string()); }
    catch (const std::exception& e) {
        error = std::string("Cannot open the workspace catalog: ") + e.what();
        return false;
    }
    if (find_field_ci(a, "WS_ID") < 0) {
        error = "The catalog at " + path.string() + " is pre-v2 (no WS_ID column).";
        a.close();
        return false;
    }
    const bool hasMemo = find_field_ci(a, "SNAPSHOT") >= 0;
    std::string merr;
    if (!cli_memo::memo_auto_on_use(a, path.string(), hasMemo, merr)) {
        error = "Cannot attach the memo sidecar: " + merr;
        a.close();
        return false;
    }
    return true;
}

} // namespace

std::vector<MemoWorkspaceRow> gui_list_memo_workspaces(std::string& error) {
    error.clear();
    std::vector<MemoWorkspaceRow> rows;

    xbase::DbArea a;
    if (!open_catalog_readonly(a, error)) return rows;

    const std::uint64_t n = a.recCount64();
    for (std::uint64_t r = 1; r <= n; ++r) {
        try {
            a.gotoRec(static_cast<std::int32_t>(r));
            a.readCurrent();
            MemoWorkspaceRow row;
            row.ws_id      = to_u64(catalog_field(a, "WS_ID"));
            row.name       = trim_ascii_copy(catalog_field(a, "WS_NAME"));
            row.fmt        = trim_ascii_copy(catalog_field(a, "FMT"));
            row.snapshot   = trim_ascii_copy(catalog_field(a, "SNAPSHOT"));
            row.size_b     = to_u64(catalog_field(a, "SIZE_B"));
            row.est_hyd_b  = to_u64(catalog_field(a, "EST_HYD_B"));
            row.saved_at   = trim_ascii_copy(catalog_field(a, "SAVED_AT"));
            row.author     = trim_ascii_copy(catalog_field(a, "AUTHOR"));
            row.superseded = trim_ascii_copy(catalog_field(a, "SUPERSEDED")) == "1";
            rows.push_back(std::move(row));
        } catch (...) {
            // A row that will not read is skipped, not fatal: the rest of the
            // catalog is still worth showing.
        }
    }

    cli_memo::memo_auto_on_close(a);
    a.close();
    return rows;
}

std::string gui_read_memo_payload(const std::string& snapshot_token,
                                  std::string& error) {
    error.clear();
    const std::string token = trim_ascii_copy(snapshot_token);
    if (token.empty()) {
        error = "This row carries no SNAPSHOT token.";
        return {};
    }

    xbase::DbArea a;
    if (!open_catalog_readonly(a, error)) return {};

    auto* store = cli_memo::memo_store_for(a);
    if (!store || !store->is_open()) {
        error = "The memo backend is not attached to the catalog.";
        cli_memo::memo_auto_on_close(a);
        a.close();
        return {};
    }

    dottalk::memo::MemoRef ref{};
    ref.token = token;
    dottalk::memo::MemoGetResult got = store->get_text(ref);

    cli_memo::memo_auto_on_close(a);
    a.close();

    if (!got.ok) {
        error = "Memo read failed" +
                (got.error.empty() ? std::string() : (": " + got.error));
        return {};
    }
    return std::move(got.text);
}

} // namespace dottalk::gui
