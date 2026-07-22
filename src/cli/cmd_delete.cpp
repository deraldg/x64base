// src/cli/cmd_delete.cpp — DELETE with implicit filesystem record locking
//
// Incremental indexing behavior:
// - Direct-write mode: if a CDX/LMDB or CNX backend is active, DELETE snapshots
//   all relevant tag keys for the current record before delete, then removes
//   that recno from all captured tags after delete succeeds.
// - Buffered/table mode: unchanged here; COMMIT remains responsible for rebuild.
//
// SET FILTER behavior:
// - DELETE honors active SET FILTER in ALL / REST / NEXT / FOR scans.
// - No-arg DELETE (current record) remains explicit on the current row.
//
// Traversal behavior:
// - DELETE snapshots target recnos first, then deletes by recno.
// - This avoids mutating an active index while simultaneously iterating it.
// - ALL / FOR use ordered snapshot traversal when an order is active.
// - REST / NEXT preserve current navigation semantics through the shared selector.
//
// Stabilization notes:
// - If index snapshot/apply fails while an order/index backend is active,
//   DELETE still succeeds at the data layer, but a warning is emitted that the
//   active index may now require rebuild.
// - After a successful delete, current navigation is refreshed best-effort.

// @dottalk.usage v1
// owner: DOT|DELETE
// command: DELETE
// category: data
// status: supported
// noargs: mutate
// effect: mutate
// mutates: table-data deletion-flag index stale-state cursor
// usage-access: DELETE USAGE
// summary:
//   Mark the current record or selected records deleted, honoring filters and
//   applying index delete snapshots in direct-write mode.
//
// usage:
//   DELETE USAGE
//   DELETE
//   DELETE ALL
//   DELETE REST
//   DELETE NEXT <n>
//   DELETE FOR <field> <op> <value>
//
// notes:
//   DELETE with no arguments deletes the current record.
//   DELETE requires an open table except for DELETE USAGE.
//   DELETE honors active SET FILTER in ALL, REST, NEXT, and FOR scans.
//   DELETE snapshots target recnos before mutating to avoid active-index traversal mutation.
//   Direct-write mode captures index keys before delete and applies index delete snapshots after delete.
//   Buffered table mode leaves rebuild or final application to COMMIT.
//   DELETE marks fields stale best-effort and refreshes current navigation best-effort.
//   If index snapshot or apply fails, data delete may still succeed and a rebuild warning is emitted.
//
// risk:
//   marks_records_deleted: yes
//   record_locking: yes
//   writes_table_data: yes
//   updates_indexes: direct-write snapshot path when available
//   marks_stale_field: yes
//   cursor_movement: during selected deletes
//   cursor_restore: best effort
//   requires_open_table: yes except usage
//
// related:
//   RECALL
//   PACK
//   TABLE
//   COMMIT
//   COUNT
//   SET FILTER
//

#include <algorithm>
#include <cstdint>
#include <sstream>
#include <string>
#include <vector>

#include "textio.hpp"
#include "xbase.hpp"
#include "xbase_locks.hpp"
#include "cli/command_output.hpp"
#include "cli/command_registry.hpp"
#include "cli/table_state.hpp"
#include "cli/scan_selector.hpp"
#include "cli/expr/normalize_where.hpp"
#include "cli/nav_move.hpp"
#include "cli/order_state.hpp"
#include "xindex/index_manager.hpp"
#include "xindex/attach.hpp"

// Provided by the interactive shell.
extern "C" xbase::XBaseEngine* shell_engine(void);

using namespace std;

namespace {

struct CursorRestore {
    xbase::DbArea* area{nullptr};
    int32_t saved{0};
    bool active{false};

    explicit CursorRestore(xbase::DbArea& a) : area(&a) {
        saved = a.recno();
        active = (saved >= 1 && saved <= a.recCount());
    }

    ~CursorRestore() {
        if (!active || !area) return;
        try {
            (void)area->gotoRec(saved);
            (void)area->readCurrent();
        } catch (...) {
        }
    }
};


static void print_delete_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DeleteUsageText);
}

static bool is_delete_usage_request(const std::string& raw)
{
    std::string t = textio::up(textio::trim(raw));

    // Some dispatch paths pass the whole raw line ("DELETE USAGE")
    // instead of only the command tail ("USAGE"). Accept both.
    if (t.rfind("DELETE ", 0) == 0) {
        t = textio::up(textio::trim(t.substr(7)));
    }

    return t == "USAGE" || t == "HELP" || t == "?";
}

static int resolve_current_index(xbase::DbArea& A) {
    xbase::XBaseEngine* eng = shell_engine();
    if (!eng) return -1;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (&eng->area(i) == &A) return i;
    }
    return -1;
}

static void mark_all_fields_stale_best_effort(xbase::DbArea& A, int area0) {
    if (area0 < 0) return;
    try {
        const int n = A.fieldCount();
        for (int field1 = 1; field1 <= n; ++field1) {
            dottalk::table::mark_stale_field(area0, field1);
        }
    } catch (...) {
    }
}

static bool parse_for_clause(std::istringstream& iss,
                             std::string& fld, std::string& op, std::string& val)
{
    std::streampos pos = iss.tellg();
    std::string kw;
    if (!(iss >> kw)) { iss.clear(); iss.seekg(pos); return false; }
    if (textio::up(kw) != "FOR") { iss.clear(); iss.seekg(pos); return false; }
    if (!(iss >> fld)) { iss.clear(); iss.seekg(pos); return false; }
    if (!(iss >> op )) { iss.clear(); iss.seekg(pos); return false; }

    std::string rest;
    std::getline(iss, rest);
    val = textio::unquote(textio::trim(rest));

    return !fld.empty() && !op.empty();
}

static void warn_index_may_require_rebuild(const xbase::DbArea& area,
                                           const char* stage)
{
    try {
        if (orderstate::hasOrder(area)) {
            cli::cmdout::print_prefixed_message(
                "DELETE",
                dottalk::helpdata::MessageId::DeleteIndexStaleWarningText,
                {{"stage", stage}});
        }
    } catch (...) {
    }
}

static void refresh_after_delete_best_effort(xbase::DbArea& area)
{
    try {
        if (orderstate::hasOrder(area)) {
            cli::nav::refresh_current(area, "DELETE");
        }
    } catch (...) {
    }
}

static bool delete_current_with_lock(xbase::DbArea& area)
{
    const std::uint64_t rn = area.recno64();
    if (rn == 0) return false;

    std::string err;
    if (!xbase::locks::try_lock_record(area, rn, &err)) return false;

    bool ok = false;
    bool snapshot_ok = true;
    bool index_apply_ok = true;
#if DOTTALK_HAS_XINDEX
    xindex::IndexManager::DeleteSnapshot delete_snap;
#endif

    try {
        if (!area.readCurrent()) {
            ok = false;
        } else if (area.isDeleted()) {
            ok = true;
        } else {
#if DOTTALK_HAS_XINDEX
            // Capture all relevant index keys BEFORE delete, while the row is live.
            try {
                auto& im = xindex::ensure_manager(area);
                delete_snap = im.capture_delete_snapshot_for_current_record();
                snapshot_ok = true;
            } catch (...) {
                snapshot_ok = false;
            }

            ok = area.deleteCurrent();

            if (ok && snapshot_ok && !delete_snap.empty()) {
                try {
                    xindex::ensure_manager(area).apply_delete_snapshot(
                        delete_snap,
                        static_cast<xindex::RecNo>(rn));
                    index_apply_ok = true;
                } catch (...) {
                    index_apply_ok = false;
                }
            }
#endif
        }
    } catch (...) {
        ok = false;
    }

    xbase::locks::unlock_record(area, rn);

    if (ok) {
        const int area0 = resolve_current_index(area);
        mark_all_fields_stale_best_effort(area, area0);
        refresh_after_delete_best_effort(area);

        // Data delete succeeded, but index lifecycle may not have completed cleanly.
#if DOTTALK_HAS_XINDEX
        if (!snapshot_ok) {
            warn_index_may_require_rebuild(area, "snapshot");
        } else if (!index_apply_ok) {
            warn_index_may_require_rebuild(area, "index update");
        }
#endif
    }

    return ok;
}

// Buffered delete: stage a CHANGE_DELETE in the table buffer and journal a D redo
// record, deferring the actual DBF/index mutation to COMMIT (or discard on
// ROLLBACK / crash recovery). Used only when TABLE BUFFER is enabled; the
// write-through path (with the Phase 1.3d batched index) remains the default.
static bool buffer_delete_recno(int area0, std::uint64_t recno) {
    if (recno == 0) return false;
    auto& tb = dottalk::table::get_tb(area0);
    const int prio = tb.add_change(recno, dottalk::table::CHANGE_DELETE);
    if (dottalk::table::is_persistent_enabled(area0)) {
        dottalk::table::ChangeEntry je;
        je.recno = recno;
        je.dirty_flags = dottalk::table::CHANGE_DELETE;
        je.priority = prio;
        (void)dottalk::table::journal_note_change(area0, je);
    }
    if (!dottalk::table::is_dirty(area0)) dottalk::table::set_dirty(area0, true);
    return true;
}

// Single-record DELETE: buffer it when TABLE BUFFER is on, else write through.
static bool delete_current_buffered_or_through(xbase::DbArea& area) {
    const int area0 = resolve_current_index(area);
    if (area0 >= 0 && dottalk::table::is_enabled(area0)) {
        return buffer_delete_recno(area0, area.recno64());
    }
    return delete_current_with_lock(area);
}

static int32_t delete_targets_by_recno(xbase::DbArea& area,
                                       const std::vector<uint64_t>& targets)
{
    int32_t cnt = 0;

    // Buffered mode: stage each delete + journal it; defer to COMMIT/ROLLBACK.
    {
        const int area0 = resolve_current_index(area);
        if (area0 >= 0 && dottalk::table::is_enabled(area0)) {
            for (uint64_t rn : targets) {
                if (!area.gotoRec64(rn)) continue;
                if (buffer_delete_recno(area0, rn)) ++cnt;
            }
            return cnt;
        }
    }

#if DOTTALK_HAS_XINDEX
    // Batch the per-row index-key erasures into one LMDB transaction (chunked)
    // instead of one commit+fsync per deleted row -- the dominant cost of a bulk
    // DELETE under an active CDX order. DBF marks stay per-row under lock; only
    // the index writes batch. On any error we abort the batch and warn the index
    // needs a rebuild (the DBF deletes still stand). Chunk keeps the txn well
    // under LMDB's dirty-page limit so very large deletes don't overflow it.
    constexpr std::size_t kBulkChunk = 10000;
    xindex::IndexManager* im = nullptr;
    bool bulk = false;
    try {
        im = &xindex::ensure_manager(area);
        std::string berr;
        bulk = im->beginBulkWrite(&berr);
    } catch (...) { im = nullptr; bulk = false; }
    std::size_t since_commit = 0;

    try {
        for (uint64_t rn : targets) {
            if (!area.gotoRec64(rn)) continue;
            if (!area.readCurrent()) continue;
            if (delete_current_with_lock(area)) {
                ++cnt;
                if (bulk && ++since_commit >= kBulkChunk) {
                    std::string ce;
                    if (!im->commitBulkWrite(&ce) || !im->beginBulkWrite(&ce)) {
                        bulk = false; // degrade to per-row writes (still correct)
                        warn_index_may_require_rebuild(area, "bulk chunk commit");
                    }
                    since_commit = 0;
                }
            }
        }
    } catch (...) {
        if (bulk && im) {
            im->abortBulkWrite();
            warn_index_may_require_rebuild(area, "bulk delete aborted");
        }
        throw;
    }

    if (bulk && im) {
        std::string ce;
        if (!im->commitBulkWrite(&ce)) {
            warn_index_may_require_rebuild(area, "bulk index commit");
        }
    }
    return cnt;
#else
    for (uint64_t rn : targets) {
        if (!area.gotoRec((int32_t)rn)) continue;
        if (!area.readCurrent()) continue;
        if (delete_current_with_lock(area)) ++cnt;
    }
    return cnt;
#endif
}

} // namespace

void cmd_DELETE(xbase::DbArea& area, std::istringstream& iss)
{
    const std::string raw_args = iss.str();
    if (is_delete_usage_request(raw_args)) {
        print_delete_usage();
        return;
    }

    if (!area.isOpen()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DeleteNoTableOpenText);
        return;
    }

    CursorRestore restore(area);

    // No-arg (current record)
    std::string tok;
    std::streampos savepos = iss.tellg();
    if (!(iss >> tok)) {
        if (!area.readCurrent()) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::DeleteCountText, {{"count", "0"}});
            return;
        }
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::DeleteCountText,
            {{"count", std::to_string(delete_current_buffered_or_through(area) ? 1 : 0)}});
        return;
    }
    iss.clear();
    iss.seekg(savepos);

    // Mode: FOR ...
    std::string fld, op, val;
    if (parse_for_clause(iss, fld, op, val)) {
        cli::scan::SelectionSpec spec{};
        spec.scan_mode = cli::scan::ScanMode::All;
        spec.use_expr = true;

        std::string expr = fld + " " + op + " " + val;
        spec.expr = normalize_unquoted_rhs_literals(area, expr);

        const auto sel = cli::scan::collect_selected_recnos(area, spec);
        const int32_t cnt = delete_targets_by_recno(area, sel.recnos);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::DeleteCountText,
            {{"count", std::to_string(cnt)}});
        return;
    }

    // Modes: ALL | REST | NEXT n
    std::string mode;
    iss >> mode;
    const auto UM = textio::up(mode);

    if (UM == "ALL") {
        cli::scan::SelectionSpec spec{};
        spec.scan_mode = cli::scan::ScanMode::All;

        const auto sel = cli::scan::collect_selected_recnos(area, spec);
        const int32_t cnt = delete_targets_by_recno(area, sel.recnos);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::DeleteCountText,
            {{"count", std::to_string(cnt)}});
        return;
    }

    if (UM == "REST") {
        cli::scan::SelectionSpec spec{};
        spec.scan_mode = cli::scan::ScanMode::Rest;

        const auto sel = cli::scan::collect_selected_recnos(area, spec);
        const int32_t cnt = delete_targets_by_recno(area, sel.recnos);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::DeleteCountText,
            {{"count", std::to_string(cnt)}});
        return;
    }

    if (UM == "NEXT") {
        int n = 0;
        if (!(iss >> n) || n <= 0) {
            print_delete_usage();
            return;
        }

        cli::scan::SelectionSpec spec{};
        spec.scan_mode = cli::scan::ScanMode::NextN;
        spec.next_n = n;

        const auto sel = cli::scan::collect_selected_recnos(area, spec);
        const int32_t cnt = delete_targets_by_recno(area, sel.recnos);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::DeleteCountText,
            {{"count", std::to_string(cnt)}});
        return;
    }

    print_delete_usage();
}

static bool s_registered = [](){
    dli::registry().add("DELETE", &cmd_DELETE);
    return true;
}();
