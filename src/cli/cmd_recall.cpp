// src/cli/cmd_recall.cpp — RECALL using shared selector
//
// Incremental indexing behavior:
// - Direct-write mode: if a CDX/LMDB backend is active, RECALL rebuilds index
//   entries for all field-backed tags on the current record after the delete
//   flag is cleared successfully.
// - Buffered/table mode: unchanged here; COMMIT remains responsible for rebuild.
//
// Traversal behavior:
// - RECALL snapshots target recnos first, then recalls by recno.
// - This avoids mutating an active index while simultaneously iterating it.
// - RECALL target selection is explicitly deleted-only.
// - Deleted-only traversal must use physical records, because active indexes
//   normally contain only live records and would otherwise hide deleted rows.
// - REST / NEXT preserve physical-scope semantics through the shared selector.

#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "textio.hpp"
#include "xbase.hpp"
#include "xbase_locks.hpp"
#include "cli/command_registry.hpp"
#include "cli/table_state.hpp"
#include "cli/scan_selector.hpp"
#include "cli/expr/normalize_where.hpp"
#include "xindex/index_manager.hpp"

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
        } catch (...) {}
    }
};

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
    } catch (...) {}
}

// --- FOR parser (same shape as DELETE)
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

static bool dbf_clear_delete_flag_on_disk(const std::string& abs_dbf_path, uint32_t recno_1based)
{
    if (abs_dbf_path.empty() || recno_1based == 0) return false;

    std::fstream fp(abs_dbf_path, std::ios::in | std::ios::out | std::ios::binary);
    if (!fp) return false;

    xbase::HeaderRec hdr{};
    fp.seekg(0, std::ios::beg);
    fp.read(reinterpret_cast<char*>(&hdr), sizeof(hdr));
    if (!fp) return false;

    if (hdr.data_start <= 0) return false;
    if (hdr.cpr <= 0) return false;
    if (recno_1based > static_cast<uint32_t>(hdr.num_of_recs)) return false;

    const std::streamoff base   = static_cast<std::streamoff>(hdr.data_start);
    const std::streamoff stride = static_cast<std::streamoff>(hdr.cpr);
    const std::streamoff off    = base + (static_cast<std::streamoff>(recno_1based) - 1) * stride;

    fp.seekp(off, std::ios::beg);
    if (!fp) return false;

    const char not_del = xbase::NOT_DELETED;
    fp.write(&not_del, 1);
    fp.flush();
    return static_cast<bool>(fp);
}

static bool reindex_recalled_record_best_effort(xbase::DbArea& area, uint32_t rn)
{
    try {
        auto& im = area.indexManager();
        if (!im.hasBackend()) return true; // no active index to maintain

        // Use the same multi-tag snapshot/apply path as APPEND. Despite the
        // historical name, capture_delete_snapshot_for_current_record() is the
        // current canonical helper for capturing the record's field-backed tag
        // keys across the active container. For RECALL, the delete flag has
        // already been cleared and readCurrent() has refreshed the row, so the
        // captured keys are the live keys that must be inserted back into the
        // index view.
        auto snap = im.capture_delete_snapshot_for_current_record();
        if (snap.empty()) return false;

        return im.apply_insert_snapshot(
            snap,
            static_cast<xindex::RecNo>(rn));
    } catch (...) {
        return false;
    }
}

static void warn_recall_index_may_require_rebuild(const xbase::DbArea& area)
{
    try {
        const auto* im = area.indexManagerPtr();
        if (im && im->hasBackend()) {
            std::cout << "RECALL: warning - active index/order may now be stale after index update. "
                         "Rebuild/rebind indexes if needed.\n";
        }
    } catch (...) {
    }
}

static bool recall_current_with_lock(xbase::DbArea& area)
{
    const auto rn = static_cast<uint32_t>(area.recno());
    if (rn == 0) return false;

    std::string err;
    if (!xbase::locks::try_lock_record(area, rn, &err)) return false;

    bool ok = false;

    try {
        (void)area.readCurrent();

        if (!area.isDeleted()) {
            // Already live: RECALL is a no-op and should not be counted as
            // a recalled record or cause index reinsertion.
            ok = false;
        } else {
            ok = dbf_clear_delete_flag_on_disk(area.filename(), rn);
            if (ok) (void)area.readCurrent();

            if (ok) {
                const bool index_ok = reindex_recalled_record_best_effort(area, rn);
                if (!index_ok) {
                    warn_recall_index_may_require_rebuild(area);
                }
            }
        }
    } catch (...) {
        ok = false;
    }

    xbase::locks::unlock_record(area, rn);

    if (ok) {
        const int area0 = resolve_current_index(area);
        mark_all_fields_stale_best_effort(area, area0);
    }

    return ok;
}

static int32_t recall_targets(xbase::DbArea& area,
                              const std::vector<uint64_t>& recnos)
{
    int32_t cnt = 0;
    for (uint64_t rn : recnos) {
        if (!area.gotoRec((int32_t)rn)) continue;
        if (!area.readCurrent()) continue;
        if (recall_current_with_lock(area)) ++cnt;
    }
    return cnt;
}

} // namespace

void cmd_RECALL(xbase::DbArea& area, std::istringstream& iss)
{
    if (!area.isOpen()) {
        std::cout << "No table is open. Use USE <file> first.\n";
        return;
    }

    CursorRestore restore(area);

    // no args = current
    std::string tok;
    std::streampos save = iss.tellg();
    if (!(iss >> tok)) {
        if (!area.readCurrent()) {
            std::cout << "0 recalled\n";
            return;
        }
        std::cout << (recall_current_with_lock(area) ? 1 : 0) << " recalled\n";
        return;
    }
    iss.clear();
    iss.seekg(save);

    // FOR
    std::string fld, op, val;
    if (parse_for_clause(iss, fld, op, val)) {
        cli::scan::SelectionSpec spec{};
        spec.scan_mode = cli::scan::ScanMode::All;
        spec.deleted_mode = cli::scan::DeletedMode::OnlyDeleted;
        spec.ordered_snapshot = false;
        spec.use_expr = true;

        std::string expr = fld + " " + op + " " + val;
        spec.expr = normalize_unquoted_rhs_literals(area, expr);

        const auto sel = cli::scan::collect_selected_recnos(area, spec);
        std::cout << recall_targets(area, sel.recnos) << " recalled\n";
        return;
    }

    // modes
    std::string mode;
    iss >> mode;
    const auto UM = textio::up(mode);

    if (UM == "ALL") {
        cli::scan::SelectionSpec spec{};
        spec.scan_mode = cli::scan::ScanMode::All;
        spec.deleted_mode = cli::scan::DeletedMode::OnlyDeleted;
        spec.ordered_snapshot = false;

        const auto sel = cli::scan::collect_selected_recnos(area, spec);
        std::cout << recall_targets(area, sel.recnos) << " recalled\n";
        return;
    }

    if (UM == "REST") {
        cli::scan::SelectionSpec spec{};
        spec.scan_mode = cli::scan::ScanMode::Rest;
        spec.deleted_mode = cli::scan::DeletedMode::OnlyDeleted;
        spec.ordered_snapshot = false;

        const auto sel = cli::scan::collect_selected_recnos(area, spec);
        std::cout << recall_targets(area, sel.recnos) << " recalled\n";
        return;
    }

    if (UM == "NEXT") {
        int n = 0;
        if (!(iss >> n) || n <= 0) {
            std::cout << "Usage: RECALL NEXT <n>\n";
            return;
        }

        cli::scan::SelectionSpec spec{};
        spec.scan_mode = cli::scan::ScanMode::NextN;
        spec.next_n = n;
        spec.deleted_mode = cli::scan::DeletedMode::OnlyDeleted;
        spec.ordered_snapshot = false;

        const auto sel = cli::scan::collect_selected_recnos(area, spec);
        std::cout << recall_targets(area, sel.recnos) << " recalled\n";
        return;
    }

    std::cout << "Usage: RECALL [ALL | REST | NEXT <n> | FOR <expr>]  (no args => recall current)\n";
}

static bool s_registered = [](){
    dli::registry().add("RECALL", &cmd_RECALL);
    return true;
}();