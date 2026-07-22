// src/cli/cmd_commit.cpp
//
// COMMIT [ALL] [MANUAL|INTERACTIVE|AUTO]
//
// Contract:
// - TABLE ON buffers changes; no OS locking should occur during REPLACE/DELETE.
// - COMMIT applies buffered changes with locking at commit time.
// - COMMIT is not an atomic transaction across DBF, memo, and index storage.
//   It reports staged failure precisely and retains retry information.
// - COMMIT ALL commits all open areas with buffered changes.
// - COMMIT does not rebuild CDX/LMDB. CDX/LMDB has a runtime lifecycle:
//   key-field mutations, append, delete, and recall are handled by mutation hooks.
// - Legacy index rebuild behavior remains only for legacy index families:
//     * INX/IDX -> REINDEX
//     * CNX     -> REBUILD
//
// Notes:
// - MANUAL / INTERACTIVE / AUTO are accepted for compatibility, but CDX/LMDB
//   rebuilds are intentionally ignored by COMMIT.
//
// @dottalk.usage v1
// owner: DOT|COMMIT
// command: COMMIT
// category: data
// status: supported
// noargs: mutate
// effect: commit
// mutates: table-data table-buffer memo stale-state index journal
// usage-access: COMMIT USAGE
// summary:
//   Apply buffered TABLE changes to the current area or all open buffered areas,
//   locking records at commit time and reporting persistence-stage failures.
//
// usage:
//   COMMIT USAGE
//   COMMIT
//   COMMIT ALL
//   COMMIT MANUAL
//   COMMIT INTERACTIVE
//   COMMIT AUTO
//   COMMIT ALL MANUAL
//   COMMIT ALL INTERACTIVE
//   COMMIT ALL AUTO
//
// notes:
//   COMMIT with no arguments applies buffered changes for the current area.
//   COMMIT ALL applies buffered changes for all open buffered areas.
//   TABLE ON buffers changes; COMMIT applies them with record locking.
//   MANUAL, INTERACTIVE, and AUTO are accepted for compatibility.
//   COMMIT does not rebuild CDX or LMDB containers.
//   Legacy INX/IDX and CNX rebuild behavior remains only for legacy index families.
//   COMMIT is a data mutation command when buffers contain changes.
//   COMMIT is write-ahead journaled: it durably records a redo log plus a COMMIT
//   marker before applying buffered changes to the DBF, and aborts the commit if
//   that durable sync fails. Committed journals are replayed on crash recovery at
//   open. Atomicity and durability are partial (ACID beta-1), not a full transaction.
//
// risk:
//   writes_dbf_records: yes when buffered changes exist
//   writes_memo: when buffered memo changes exist
//   record_locking: yes at commit time
//   clears_table_buffer_changes: on successful commit
//   writes_write_ahead_journal: yes (durable redo log + COMMIT marker before apply)
//   partial_commit_possible: yes
//   cdx_lmdb_rebuild: no
//
// related:
//   TABLE
//   REPLACE
//   CALCWRITE
//   ROLLBACK
//   REINDEX
//   REBUILD
//

#include <sstream>
#include <string>
#include <unordered_map>
#include <cctype>
#include <cstdint>
#include <limits>
#include <vector>

#include "xbase.hpp"
#include "xbase_locks.hpp"

#include "cli/command_output.hpp"
#include "cli/settings.hpp"
#include "cli/table_state.hpp"
#include "cli/order_state.hpp"
#include "memo/memo_manager.hpp"

#if DOTTALK_HAS_XINDEX
// Legacy index rebuild commands. CDX/LMDB is not rebuilt by COMMIT.
void cmd_REINDEX(xbase::DbArea& A, std::istringstream& args);
void cmd_REBUILD(xbase::DbArea& A, std::istringstream& args);

// SET INDEXTXN (default OFF): transactional in-COMMIT index maintenance.
#include "xindex/attach.hpp"          // xindex::ensure_manager
#include "xindex/index_manager.hpp"   // IndexManager::{isCdx,beginBulkWrite,commitBulkWrite,abortBulkWrite}
#include "xbase/index_hooks.hpp"      // xbase::index_hooks::{capture,apply_replace}
#include "cli/order_hooks.hpp"        // orderhooks::reconcile_after_mutation
#endif

extern "C" xbase::XBaseEngine* shell_engine();

using cli::Settings;

namespace {

enum class CommitStatus {
    NoChanges,
    Complete,
    PartialRecordFailure,
    FinalizeFailure,
};

struct CommitResult {
    CommitStatus status{CommitStatus::NoChanges};
    int applied_ok{0};
    int applied_fail{0};

    bool complete() const noexcept { return status == CommitStatus::Complete; }
    bool attempted() const noexcept { return status != CommitStatus::NoChanges; }
};


static void print_commit_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::CommitUsageText);
}

static int resolve_area0(xbase::DbArea& A) {
    if (auto* eng = shell_engine()) {
        for (int i = 0; i < xbase::MAX_AREA; ++i) {
            if (&eng->area(i) == &A) return i;
        }
    }
    return -1;
}

struct CursorRestore {
    xbase::DbArea* area = nullptr;
    int saved_recno = 0;
    bool active = false;

    explicit CursorRestore(xbase::DbArea& A) : area(&A) {
        try {
            saved_recno = A.recno();
            active = (saved_recno >= 1 && saved_recno <= A.recCount());
        } catch (...) {
            active = false;
        }
    }

    ~CursorRestore() {
        if (!active || !area) return;
        try {
            if (saved_recno >= 1 && saved_recno <= area->recCount()) {
                if (area->gotoRec(saved_recno)) {
                    (void)area->readCurrent();
                }
            }
        } catch (...) {
            // best-effort only
        }
    }

    CursorRestore(const CursorRestore&) = delete;
    CursorRestore& operator=(const CursorRestore&) = delete;
};

struct Agg {
    std::uint64_t recno = 0;
    std::uint64_t flags = 0;
    // last-write-wins per field1
    std::unordered_map<int, std::string> field_values;
};

// Aggregate all ChangeEntry rows for the same recno into one view.
static Agg aggregate_for_recno(const dottalk::table::TableBuffer& tb, std::uint64_t recno) {
    Agg a;
    a.recno = recno;

    auto range = tb.changes.equal_range(recno);

    // For history mode, choose highest priority per field.
    std::unordered_map<int, int> best_prio;

    for (auto it = range.first; it != range.second; ++it) {
        const auto& e = it->second;
        a.flags |= e.dirty_flags;

        for (const auto& kv : e.new_values) {
            const int f1 = kv.first;
            const std::string& v = kv.second;

            if (!tb.history_enabled) {
                a.field_values[f1] = v;
            } else {
                const int pr = e.priority;
                auto bp = best_prio.find(f1);
                if (bp == best_prio.end() || pr >= bp->second) {
                    best_prio[f1] = pr;
                    a.field_values[f1] = v;
                }
            }
        }
    }

    return a;
}

static bool apply_one_recno(xbase::DbArea& A, const Agg& agg, bool talk,
                            bool maintain_index) {
    const std::uint64_t rn = agg.recno;
    if (rn == 0 || rn > A.recCount64()) return false;

    if (!A.gotoRec64(rn)) return false;
    if (!A.readCurrent()) return false;

    // Lock at commit time (per-record). If you later add table locks, this is where it goes.
    std::string lock_err;
    if (!xbase::locks::try_lock_record(A, rn, &lock_err)) {
        if (talk) cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitRecLockedText,
            {{"rn", std::to_string(rn)}, {"detail", lock_err}});
        return false;
    }

#if DOTTALK_HAS_XINDEX
    // Pre-image key snapshot (all field-backed tags) BEFORE mutating field bytes.
    // Routes onto the open bulk txn via the installed index_hooks seam.
    xbase::index_hooks::Snapshot before_snap;
    if (maintain_index) before_snap = xbase::index_hooks::capture(A);
#else
    (void)maintain_index;
#endif

    bool ok = true;

    if (agg.flags & dottalk::table::CHANGE_UPDATE) {
        for (const auto& kv : agg.field_values) {
            const int f1 = kv.first;
            const std::string& v = kv.second;
            if (!A.set(f1, v)) {
                ok = false;
                break;
            }
        }
        if (ok) ok = A.writeCurrent();
    }

    if (ok && (agg.flags & dottalk::table::CHANGE_DELETE)) {
        ok = A.deleteCurrent();
    }

#if DOTTALK_HAS_XINDEX
    if (maintain_index && ok) {
        // DELETE => empty after-snapshot (erase keys; CDX excludes deleted rows).
        // UPDATE => post-image after-snapshot (delete old / insert new per tag).
        xbase::index_hooks::Snapshot after_snap;
        if (!(agg.flags & dottalk::table::CHANGE_DELETE)) {
            (void)A.readCurrent();
            after_snap = xbase::index_hooks::capture(A);
        }
        if (!xbase::index_hooks::apply_replace(A, before_snap, after_snap, rn)) {
            if (talk) cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitIndexFinalizeFailedText);
        }
    }
#endif

    xbase::locks::unlock_record(A, rn);
    return ok;
}

static bool auto_reindex_if_needed(xbase::DbArea& A,
                                   int area0,
                                   bool talk,
                                   bool /*interactive_rebuild*/)
{
#if !DOTTALK_HAS_XINDEX
    (void)A; (void)area0; (void)talk;
    return true;
#else
    if (area0 < 0) return true;
    if (!dottalk::table::is_stale(area0)) return true;

    // Current index contract:
    // - CDX/LMDB has a full runtime lifecycle. COMMIT must not call BUILDLMDB.
    // - CNX remains rebuild-based.
    // - INX/IDX remains reindex-based.
    // - No active order means no index rebuild.
    if (!orderstate::hasOrder(A)) {
        if (talk) cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitNoActiveOrderText);
        return true;
    }

    if (orderstate::isCdx(A)) {
        if (talk) {
            const std::string tag = orderstate::activeTag(A);
            cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitCdxSkippedText,
                {{"tag", tag.empty() ? std::string() : (" (tag " + tag + ")")}});
        }
        return true;
    }

    if (orderstate::isCnx(A)) {
        if (talk) cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitRebuildingCnxText);
        std::istringstream args("");
        cmd_REBUILD(A, args);
        if (dottalk::table::is_stale(area0)) {
            cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitCnxNotClearedText);
            return false;
        }
        return true;
    }

    if (talk) cli::cmdout::print_prefixed_message(
        "COMMIT", dottalk::helpdata::MessageId::CommitReindexingText);
    std::istringstream args("");
    cmd_REINDEX(A, args);
    if (dottalk::table::is_stale(area0)) {
        cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitReindexNotClearedText);
        return false;
    }
    return true;
#endif
}

static CommitResult commit_one_area(xbase::DbArea& A,
                                    int area0,
                                    bool talk,
                                    bool interactive_rebuild)
{
    auto& tb = dottalk::table::get_tb(area0);

    if (tb.empty()) {
        if (talk) cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitNoChangesText);
        return {};
    }

    CursorRestore restore(A);

    // A later memo/index/journal failure must not make the pending operation
    // disappear. Updates and deletes are safe to reapply on retry; COMMIT does
    // not currently materialize CHANGE_INSERT in apply_one_recno().
    const auto pending_before = tb.changes;

    // Write-ahead: durably fsync the redo log + COMMIT marker BEFORE applying the
    // buffered changes to the DBF. If the durable sync fails, abort the commit and
    // keep the buffer intact (RamOnly mode returns true and is unaffected).
    if (!dottalk::table::journal_begin_commit(area0)) {
        dottalk::table::set_dirty(area0, true);
        cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitJournalFinalizeFailedText);
        return {CommitStatus::FinalizeFailure, 0, 1};
    }

    // SET INDEXTXN gate: maintain the index in-COMMIT only when the flag is ON
    // and the live backend is CDX/LMDB. Default OFF reproduces prior behavior.
    bool maintain_index = false;
#if DOTTALK_HAS_XINDEX
    xindex::IndexManager* im = nullptr;
    if (cli::Settings::indexTxnOn()) {
        im = &xindex::ensure_manager(A);
        maintain_index = im->isCdx();
    }
    if (maintain_index) {
        std::string berr;
        if (!im->beginBulkWrite(&berr)) {
            dottalk::table::set_dirty(area0, true);
            cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitIndexFinalizeFailedText);
            return {CommitStatus::FinalizeFailure, 0, 1};
        }
    }
#endif

    // Iterate unique recnos in the multimap.
    int applied_ok = 0;
    int applied_fail = 0;

    for (auto it = tb.changes.begin(); it != tb.changes.end(); ) {
        const std::uint64_t recno = it->first;
        const auto range = tb.changes.equal_range(recno);

        const Agg agg = aggregate_for_recno(tb, recno);
        const bool ok = apply_one_recno(A, agg, talk, maintain_index);

        if (ok) {
            ++applied_ok;
            it = tb.changes.erase(range.first, range.second);
        } else {
            ++applied_fail;
            // Keep the entries so the user can retry COMMIT.
            it = range.second;
        }
    }

    if (applied_fail != 0) {
#if DOTTALK_HAS_XINDEX
        // Partial: applied records are durable + de-buffered; persist their index
        // edits to stay consistent -> commit the bulk. On failure, mark stale.
        if (maintain_index) {
            std::string cerr;
            if (!im->commitBulkWrite(&cerr)) dottalk::table::set_stale(area0, true);
        }
#endif
        // Keep dirty/stale; buffer still contains remaining failed recnos.
        dottalk::table::set_dirty(area0, true);
        if (talk) {
            cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitPartialRemainingText,
                {{"ok", std::to_string(applied_ok)}, {"fail", std::to_string(applied_fail)}});
        } else {
            cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitPartialText,
                {{"ok", std::to_string(applied_ok)}, {"fail", std::to_string(applied_fail)}});
        }
        return {CommitStatus::PartialRecordFailure, applied_ok, applied_fail};
    }

    if (auto* mm = A.memoManagerPtr()) {
        std::string memo_err;
        if (!mm->flush(&memo_err)) {
#if DOTTALK_HAS_XINDEX
            if (maintain_index) { im->abortBulkWrite(); dottalk::table::set_stale(area0, true); }
#endif
            tb.changes = pending_before;
            dottalk::table::set_dirty(area0, true);
            cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitMemoFlushFailedText,
                {{"detail", memo_err.empty() ? std::string{} : std::string(" (" + memo_err + ")")}});
            return {CommitStatus::FinalizeFailure, applied_ok, 1};
        }
    }

    // Legacy rebuild commands refuse a dirty TABLE state. Temporarily expose
    // the already-applied record stage as clean, then restore dirty state if
    // the rebuild does not prove success by clearing stale state.
    dottalk::table::set_dirty(area0, false);
    if (!auto_reindex_if_needed(A, area0, talk, interactive_rebuild)) {
#if DOTTALK_HAS_XINDEX
        if (maintain_index) { im->abortBulkWrite(); dottalk::table::set_stale(area0, true); }
#endif
        tb.changes = pending_before;
        dottalk::table::set_dirty(area0, true);
        cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitIndexFinalizeFailedText);
        return {CommitStatus::FinalizeFailure, applied_ok, 1};
    }

#if DOTTALK_HAS_XINDEX
    // Commit the index bulk BEFORE the journal commit marker. On failure the DBF
    // is already applied; mark stale so BUILDLMDB reconciles.
    if (maintain_index) {
        std::string cerr;
        if (!im->commitBulkWrite(&cerr)) {
            dottalk::table::set_stale(area0, true);
            tb.changes = pending_before;
            dottalk::table::set_dirty(area0, true);
            cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitIndexFinalizeFailedText);
            return {CommitStatus::FinalizeFailure, applied_ok, 1};
        }
    }
#endif

    // Persistent TABLE BUFFER stub hook. A future implementation must return
    // false when the durable journal cannot record/finalize the commit.
    if (!dottalk::table::journal_note_commit(area0)) {
        tb.changes = pending_before;
        dottalk::table::set_dirty(area0, true);
        cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitJournalFinalizeFailedText);
        return {CommitStatus::FinalizeFailure, applied_ok, 1};
    }

#if DOTTALK_HAS_XINDEX
    // Invalidate CLI order/nav caches so ordered browsers/relations rebuild from
    // the maintained index (DbTupleStream materializes from it). Best-effort.
    if (maintain_index) orderhooks::reconcile_after_mutation(A);
#endif

    tb.clear();
    dottalk::table::set_dirty(area0, false);
    dottalk::table::set_stale(area0, false);
    dottalk::table::clear_stale_fields(area0);

    if (talk) cli::cmdout::print_prefixed_message(
        "COMMIT", dottalk::helpdata::MessageId::CommitCompleteText,
        {{"ok", std::to_string(applied_ok)}});
    return {CommitStatus::Complete, applied_ok, 0};
}

} // namespace

void cmd_COMMIT(xbase::DbArea& A, std::istringstream& in) {
    auto* eng = shell_engine();
    if (!eng) {
        cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitEngineUnavailableText);
        return;
    }

    bool all = false;
    bool interactive_rebuild = false;

    for (std::string tok; in >> tok; ) {
        std::string up = tok;
        for (auto& c : up) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));

        if (up == "USAGE" || up == "HELP" || up == "?") {
            print_commit_usage();
            return;
        } else if (up == "ALL") {
            all = true;
        } else if (up == "MANUAL" || up == "INTERACTIVE") {
            interactive_rebuild = true;
        } else if (up == "AUTO") {
            interactive_rebuild = false;
        } else {
            print_commit_usage();
            return;
        }
    }

    const bool talk = Settings::instance().talk_on.load();

    if (!all) {
        const int area0 = resolve_area0(A);
        if (area0 < 0) {
            cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitCannotDetermineAreaText);
            return;
        }
        (void)commit_one_area(A, area0, talk, interactive_rebuild);
        return;
    }

    // COMMIT ALL
    int attempted = 0;
    int committed = 0;
    int failed = 0;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        auto& Ai = eng->area(i);
        if (!Ai.isOpen()) continue;
        if (!dottalk::table::is_enabled(i)) continue;

        auto& tb = dottalk::table::get_tb(i);
        if (tb.empty()) continue;

        const CommitResult result = commit_one_area(Ai, i, talk, interactive_rebuild);
        if (!result.attempted()) continue;
        ++attempted;
        if (result.complete()) ++committed;
        else                   ++failed;
    }

    if (attempted == 0) {
        cli::cmdout::print_prefixed_message(
            "COMMIT ALL", dottalk::helpdata::MessageId::CommitAllNoBufferedText);
    } else {
        cli::cmdout::print_prefixed_message(
            "COMMIT ALL", dottalk::helpdata::MessageId::CommitAllCompleteText,
            {{"committed", std::to_string(committed)}, {"failed", std::to_string(failed)}});
    }
}
