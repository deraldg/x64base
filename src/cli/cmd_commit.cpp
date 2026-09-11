// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

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
//   open. THE BACK HALF IS ALSO SYNCED: the table's contents are forced to stable
//   media BEFORE the redo log is deleted, because writeCurrent reaches only the OS
//   page cache and a log removed ahead of the platter would leave a power cut with
//   neither copy. If that sync fails the log is KEPT and the area is marked stale;
//   replay is idempotent, so a surviving log costs one repeat and a deleted one
//   costs the transaction.
//   BOTH SYNCS ARE GATED ON TABLE BUFFER PERSISTENT. Under the default RamOnly
//   there is no journal at all, so COMMIT is NOT durable by default and never has
//   been -- said plainly here because the paragraph above describes a protocol a
//   reader could otherwise assume is always running.
//   Atomicity and durability are partial (ACID beta-1), not a full transaction.
//   A registered BEFORE trigger is asked, at commit entry, whether each buffered
//   record may be written, and may refuse. A refusal aborts the WHOLE area
//   transaction -- one COMMIT marker covers the area, so one record cannot be
//   refused while the rest commit durably. Nothing is journaled, the buffer is
//   retained for correction and retry, and the refusal is reported at ERROR
//   severity so STOP_ON_ERROR governs it.
//   No BEFORE trigger registered means no cost and no behaviour change.
//
// risk:
//   writes_dbf_records: yes when buffered changes exist
//   writes_memo: when buffered memo changes exist
//   record_locking: yes at commit time
//   clears_table_buffer_changes: on successful commit
//   writes_write_ahead_journal: yes under PERSISTENT (durable redo log + COMMIT
//     marker before apply, and a durable sync of the table before the log is
//     deleted); no journal at all under the default RamOnly
//   partial_commit_possible: yes -- and this is a PER-AREA statement. COMMIT ALL
//     is a loop of independent per-area commits, so a group of areas has no
//     atomicity at all (AIF-160)
//   refusable_by_before_trigger: yes (whole transaction; nothing journaled)
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

#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <cctype>
#include <cstdint>
#include <limits>
#include <vector>

#include "xbase.hpp"
#include "xbase_locks.hpp"
#include "xbase/trigger_hooks.hpp"   // AIF-087 M2b: BEFORE phase at commit entry
#include "xbase/durable.hpp"        // AIF-161: durable_sync before the log dies

#include "cli/command_output.hpp"
#include "cli/settings.hpp"
#include "cli/table_state.hpp"
#include "cli/table_buffer.hpp"   // AIF-159: the verdict type this file fills in
#include "cli/order_state.hpp"
#include "memo/memo_manager.hpp"

#include "workarea_util.hpp"
#include "sqlsel_statement.hpp"   // AIF-159 s3: sqlsel::transaction_active()
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
    RefusedByTrigger,   // AIF-087 M2b: a BEFORE trigger vetoed; nothing journaled
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

struct InsertTableLockGuard {
    xbase::DbArea* area = nullptr;
    bool acquired_here = false;
    bool ready = true;
    std::string error;

    InsertTableLockGuard(xbase::DbArea& value, bool required) : area(&value) {
        if (!required) return;
        xbase::locks::LockHolder holder;
        const bool borrowed = xbase::locks::table_lock_holder(value, &holder) &&
                              holder.owner_id == xbase::locks::current_owner().id;
        if (!xbase::locks::try_lock_table(value, &error)) {
            ready = false;
            return;
        }
        acquired_here = !borrowed;
    }

    ~InsertTableLockGuard() {
        if (!acquired_here || !area) return;
        std::string ignored;
        (void)xbase::locks::unlock_table(
            *area, xbase::locks::current_owner(), &ignored);
    }
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

// The changed-field set for one folded record. ONE DERIVATION, used by the
// BEFORE pre-pass and the AFTER fire -- if each built its own, a change to the
// fold would silently give the two phases different views of the same write.
static std::vector<int> changed_fields_of(const Agg& agg)
{
    std::vector<int> fields;
    fields.reserve(agg.field_values.size());
    for (const auto& kv : agg.field_values) fields.push_back(kv.first);
    return fields;
}

// Stable event_kind literal for a buffered record write. DELETE dominates
// because apply_one_recno writes fields and THEN deletes, so a record both
// updated and deleted inside one transaction ends the transaction deleted.
//
// "record_update", NOT "field_replace". Every event from this path is a RECORD
// write that may carry N changed fields -- a MULTIREP of two fields reported
// kind=field_replace with field_count=2, so the label contradicted the count in
// the same struct. "field_replace" belongs to DbArea::replaceFieldStored, where
// one field genuinely is the whole write; reusing it here made the general case
// wear the degenerate case's name.
static const char* event_kind_for_flags(std::uint64_t flags) noexcept {
    if (flags & dottalk::table::CHANGE_DELETE) return "record_delete";
    if (flags & dottalk::table::CHANGE_INSERT) return "record_insert";
    return "record_update";
}

// AIF-160, 2026-09-11. THE RECORD LOCK GETS THE GUARD ITS SIBLING ALREADY HAD.
//
// InsertTableLockGuard above is RAII: the destructor returns the table lock on
// any scope exit. The per-record lock was a MANUAL PAIR -- try_lock_record at
// the top of apply_one_recno, unlock_record forty lines later -- with nothing
// structural between them.
//
// MEASURED BEFORE CHANGING IT, because the difference matters: there is NO
// EARLY RETURN between the two. Every ordinary failure path inside deliberately
// falls through to the unlock, so this is not a leak that has been happening.
// What it is, is a span with no defence: A.set(), A.writeCurrent() and the
// xbase::index_hooks capture/apply calls all sit inside it and NONE is noexcept,
// so a throw from any of them skips the release. Whether any of them actually
// throws was NOT swept, and this guard is written so that question stops
// mattering rather than being answered.
//
// The leak was survivable only by accident: DbArea::close() calls
// xbase::locks::release_held (AIF-113, wired the same morning for the unrelated
// reason that six leak routes converge there), so an escaped record lock came
// back when the area closed. A backstop found by accident is not a guard placed
// on purpose, and the owner's shape for this engine is that a record is held for
// "milliseconds, microseconds we hope" -- holding one until close is a different
// product.
//
// RELEASE IS EXPLICIT AND THE DESTRUCTOR IS THE BACKSTOP, never the other way
// round. The unlock point is LOAD-BEARING: the AIF-087 M3 AFTER trigger fires
// immediately after it, deliberately, because a trigger that touched this record
// while the lock was still held would deadlock against the write that notified
// it. Letting the guard run to end of scope would move the release PAST the
// trigger and reintroduce exactly that deadlock. So release() is called where
// the old unlock stood, and ~RecordLockGuard only ever fires on a path that
// never reached it.
struct RecordLockGuard {
    xbase::DbArea* area  = nullptr;
    std::uint64_t  recno = 0;
    bool           held  = false;

    RecordLockGuard(xbase::DbArea& value, std::uint64_t rn, std::string* err)
        : area(&value), recno(rn)
    {
        held = xbase::locks::try_lock_record(value, rn, err);
    }

    ~RecordLockGuard() { release(); }

    // Idempotent: the normal path calls this, the destructor calls it again.
    void release()
    {
        if (!held) return;
        held = false;
        xbase::locks::unlock_record(*area, recno);
    }

    bool ok() const noexcept { return held; }

    RecordLockGuard(const RecordLockGuard&)            = delete;
    RecordLockGuard& operator=(const RecordLockGuard&) = delete;
};

static bool apply_one_recno(xbase::DbArea& A, const Agg& agg, bool talk,
                            bool maintain_index) {
    const std::uint64_t rn = agg.recno;
    if (rn == 0) return false;
    const bool inserting = (agg.flags & dottalk::table::CHANGE_INSERT) != 0;
    bool appended_now = false;
    if (inserting && rn == A.recCount64() + 1) {
        if (!A.appendBlank() || !A.readCurrent()) return false;
        appended_now = true;
    } else {
        if (rn > A.recCount64() || !A.gotoRec64(rn) || !A.readCurrent()) return false;
    }

    // Lock at commit time (per-record). If you later add table locks, this is where it goes.
    std::string lock_err;
    RecordLockGuard rec_lock(A, rn, &lock_err);
    if (!rec_lock.ok()) {
        if (talk) cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitRecLockedText,
            {{"rn", std::to_string(rn)}, {"detail", lock_err}});
        return false;   // never acquired; the guard releases nothing
    }

#if DOTTALK_HAS_XINDEX
    // Pre-image key snapshot (all field-backed tags) BEFORE mutating field bytes.
    // Routes onto the open bulk txn via the installed index_hooks seam.
    xbase::index_hooks::Snapshot before_snap;
    if (maintain_index && !appended_now) before_snap = xbase::index_hooks::capture(A);
#else
    (void)maintain_index;
#endif

    bool ok = true;
    bool index_failed = false;

    if (agg.flags & (dottalk::table::CHANGE_INSERT |
                     dottalk::table::CHANGE_UPDATE)) {
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
            index_failed = true;
            if (talk) cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitIndexFinalizeFailedText);
        }
    }
#endif

    // EXPLICIT, and the position is the contract -- see RecordLockGuard above.
    // The AFTER trigger below must run with this lock already gone.
    rec_lock.release();

    // AIF-087 M3: THE AFTER PHASE FIRES HERE -- per record, once that record's
    // apply has succeeded, and AFTER THE RECORD LOCK IS RELEASED.
    //
    // Per record and not per transaction, because partial_commit_possible is
    // yes: a per-transaction AFTER would fire for records that never landed.
    //
    // After the unlock, matching DbArea::replaceFieldStored, which unlocks at
    // dbarea.cpp:289 and fires at :330. That is not incidental -- Decision E 4.3
    // lets an AFTER trigger write in its own transaction, and a trigger that
    // touched this record while we still held its lock would deadlock against
    // the write that notified it.
    //
    // Silent when index maintenance failed, also matching replaceFieldStored
    // ("No fire when index maintenance failed"). The rule is arguable -- the
    // DATA is durable either way -- but ONE RULE ACROSS BOTH AFTER PATHS beats
    // a defensible second one. A divergence here would be the same claim with
    // two homes, which is the defect this lane keeps finding.
    //
    // RECOVERY CANNOT REACH THIS. recover_table_buffer_journal replays with
    // area.set + writeCurrent and never calls apply_one_recno, so replay does
    // not re-fire BY CONSTRUCTION rather than by a suppression flag. Anyone
    // refactoring replay to share this function reopens the double-fire defect,
    // and that refactor would look like tidiness.
    if (ok && !index_failed) {
        const std::vector<int> fields = changed_fields_of(agg);
        xbase::trigger_hooks::WriteEvent ev;
        ev.event_kind  = event_kind_for_flags(agg.flags);
        ev.recno       = rn;
        ev.fields      = fields.empty() ? nullptr : fields.data();
        ev.field_count = fields.size();
        xbase::trigger_hooks::fire_record_write(A, ev);
    }

    return ok;
}

static bool auto_reindex_if_needed(xbase::DbArea& A,
                                   int area0,
                                   bool talk,
                                   bool /*interactive_rebuild*/,
                                   bool index_maintained)
{
#if !DOTTALK_HAS_XINDEX
    (void)A; (void)area0; (void)talk; (void)index_maintained;
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

    // Was the index ALREADY maintained, record by record, during this commit?
    // If so there is nothing to rebuild, and rebuilding would be redundant work
    // on an index that is already correct.
    //
    // NOTE THE PRECISE CONDITION. This asks whether maintenance HAPPENED, not
    // whether the backend COULD maintain. Those differ: in-COMMIT maintenance
    // is gated behind SET INDEXTXN, which defaults OFF. Skipping the rebuild
    // merely because a backend is capable would leave an INDEXTXN-off commit
    // neither maintained NOR rebuilt -- silently stale, and strictly worse than
    // the rebuild it replaced. Capability decides whether maintenance is
    // attempted (see the INDEXTXN gate above); only the outcome decides whether
    // the rebuild can be skipped.
    if (index_maintained) {
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

    const bool has_insert = std::any_of(tb.changes.begin(), tb.changes.end(),
        [](const auto& entry) {
            return (entry.second.dirty_flags & dottalk::table::CHANGE_INSERT) != 0;
        });
    InsertTableLockGuard insert_lock(A, has_insert);
    if (!insert_lock.ready) {
        std::cout << "COMMIT: insert table lock refused";
        if (!insert_lock.error.empty()) std::cout << " (" << insert_lock.error << ")";
        std::cout << ".\n";
        return {CommitStatus::PartialRecordFailure, 0, 1};
    }

    CursorRestore restore(A);

    // A later memo/index/journal failure must not make the pending operation
    // disappear. Inserts, updates, and deletes are idempotent at their reserved
    // record number and are safe to reapply on retry.
    const auto pending_before = tb.changes;

    // AIF-087 M2b: THE BEFORE PHASE FIRES HERE -- after the locks are held and
    // pending_before is snapshotted, and BEFORE the WAL COMMIT marker below.
    //
    // Why here and not when the edit was staged: a change staged by REPLACE may
    // be discarded by ROLLBACK, so a validation that passed where the INTENTION
    // was expressed can be stale by the time the DECISION is made. Validate
    // where the decision is made.
    //
    // ALL OR NOTHING, and that is a property of the journal, not a shortcut.
    // journal_begin_commit writes ONE COMMIT marker for the whole area's
    // transaction, so there is no way to refuse one record and durably commit
    // the rest without writing a partial transaction. One refusal aborts the
    // whole commit with NOTHING journaled and the buffer intact -- which is what
    // the buffer is for: correct it and retry.
    //
    // Costs nothing when no trigger is registered: allow_record_write returns
    // true immediately for an area with no Before callback.
    {
        xbase::trigger_hooks::RefusalCode reason = xbase::trigger_hooks::kNoReason;
        std::uint64_t refused_recno = 0;
        bool refused = false;

        for (auto it = tb.changes.begin(); it != tb.changes.end(); ) {
            const std::uint64_t recno = it->first;
            const auto range = tb.changes.equal_range(recno);
            const Agg agg = aggregate_for_recno(tb, recno);

            // The changed-field set for THIS record, folded exactly as
            // apply_one_recno will fold it. One decision per physical write.
            const std::vector<int> fields = changed_fields_of(agg);

            xbase::trigger_hooks::WriteEvent ev;
            ev.event_kind  = event_kind_for_flags(agg.flags);
            ev.recno       = recno;
            ev.fields      = fields.empty() ? nullptr : fields.data();
            ev.field_count = fields.size();

            if (!xbase::trigger_hooks::allow_record_write(A, ev, &reason)) {
                refused = true;
                refused_recno = recno;
                break;
            }
            it = range.second;
        }

        if (refused) {
            dottalk::table::set_dirty(area0, true);
            // The refusal reaches STOP_ON_ERROR as a catalog MessageId at ERROR
            // severity, per Decision E 4.2 / AIF-036. NOT YET DONE: mapping the
            // callback's RefusalCode to a message OF ITS OWN. That needs a
            // validated code -> MessageId table, and an unvalidated uint32
            // would print an unrelated message, so the code is reported as
            // detail rather than trusted as an index.
            std::string detail;
            if (reason != xbase::trigger_hooks::kNoReason) {
                detail = " (reason " + std::to_string(reason) + ")";
            }
            cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitRefusedByTriggerText,
                {{"rn", std::to_string(refused_recno)}, {"detail", detail}});
            // Nothing applied and nothing attempted: the veto ran before any
            // record was touched, so 0/0 is the honest count.
            return {CommitStatus::RefusedByTrigger, 0, 0};
        }
    }

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
    // and the live backend can actually maintain itself. Default OFF reproduces
    // prior behavior.
    //
    // OPEN INDEX API (2026-08-01): this asks the backend what it CAN DO, not
    // what it IS. It previously read `im->isCdx()`, which had to be revisited
    // every time a backend was added or gained a capability -- and was already
    // wrong: CNX gained working upsert/erase in XIDX-TXN-02 M1 while this line
    // still excluded it, so a buffered CNX edit was never maintained here and
    // fell through to a full rebuild. Any backend that honestly reports
    // maintainsIncrementally() now participates, including a future SIX/SNX,
    // with no edit to this file.
    bool maintain_index = false;
#if DOTTALK_HAS_XINDEX
    xindex::IndexManager* im = nullptr;
    if (cli::Settings::indexTxnOn()) {
        im = &xindex::ensure_manager(A);
        maintain_index = im->maintainsIncrementally();
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
            // COMMIT failed during memo flush: buffer retained for retry. The
            // DBF writes are idempotent, so restoring the original pending set
            // is safer than clearing state after a partial finalize failure.
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
    if (!auto_reindex_if_needed(A, area0, talk, interactive_rebuild, maintain_index)) {
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

    // DURABILITY (XIDX-TXN-02 M2). commitBulkWrite() closes the backend's own
    // transaction; for a backend that maintains IN MEMORY -- CNX -- that is not
    // yet a write to the container. saveIndex() is that write. It is a no-op
    // success for backends that already wrote through (CDX/LMDB), so this costs
    // nothing on the path that does not need it.
    //
    // BEFORE the journal commit marker, for the same reason the bulk commit is:
    // the marker must not claim a commit whose index side has not landed.
    // On failure the container keeps CNX_HDRF_DIRTY, so a later open rebuilds
    // rather than trusting a half-written ordering, and the buffer is retained
    // for retry exactly as the other finalize failures do.
    if (maintain_index) {
        std::string serr;
        if (!im->saveIndex(&serr)) {
            dottalk::table::set_stale(area0, true);
            tb.changes = pending_before;
            dottalk::table::set_dirty(area0, true);
            cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitIndexFinalizeFailedText);
            return {CommitStatus::FinalizeFailure, applied_ok, 1};
        }
    }
#endif

    // THE LAST MOMENT THE TRANSACTION EXISTS IN TWO PLACES.
    //
    // apply_one_recno ends at writeCurrent()/deleteCurrent(), which reach
    // io().flush() -- the OS page cache and NO FURTHER. journal_note_commit
    // below DELETES the redo log. Between those two facts sat a window in which
    // a power cut lost the rows AND the log that could have replayed them.
    //
    // THE COMMENT THAT USED TO DEFER THIS said std::fstream does not expose the
    // OS handle portably. That was true at AIF-023 (2026-07-19) and stopped
    // being binding on 2026-08-31: xbase::durable_sync opens a SECOND HANDLE BY
    // PATH, so the fstream is not in the way. See AIF-161 -- verifying that an
    // obstacle is still literally true is not verifying that it is still
    // binding.
    //
    // GATED ON PERSISTENCE, deliberately. This sync exists to protect the
    // LOG-DELETION invariant, and RamOnly has no log. The default path pays
    // nothing, exactly as AIF-023 left it.
    //
    // ON FAILURE: report, mark stale, and DO NOT DELETE THE LOG. The rows are
    // applied and correct; the log replays idempotently at the next USE, so a
    // surviving log costs one repeat and a deleted one costs the transaction.
    // KNOWN BOUND, stated rather than discovered: journal_note_buffer_on opens
    // with "wb", so the NEXT transaction on this area truncates the retained
    // log. Closing that needs a refuse-to-start-over-a-retained-log state and
    // is a decision, not a line -- it is NOT made here.
    //
    // std::cout rather than the catalogue matches the three shipped
    // durable_sync warnings in cmd_workspace.cpp.
    bool dbf_durable = true;
    if (dottalk::table::is_persistent_enabled(area0)) {
        std::string sync_err;
        dbf_durable = xbase::durable_sync(A.filename(), &sync_err);
        if (!dbf_durable) {
            dottalk::table::set_stale(area0, true);
            std::cout << "COMMIT: warning -- " << applied_ok
                      << " record(s) applied but the table was not synced to"
                         " durable media (" << sync_err << "); the redo log is"
                         " KEPT and replays at the next USE\n";
        }
    }

    // Persistent TABLE BUFFER stub hook. A future implementation must return
    // false when the durable journal cannot record/finalize the commit.
    if (dbf_durable && !dottalk::table::journal_note_commit(area0)) {
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

// ---------------------------------------------------------------------------
// AIF-159: hand the verdict out.
//
// commit_area() is the single-area body of cmd_COMMIT lifted verbatim, so the
// two cannot drift: cmd_COMMIT now calls it. Everything observable is the same
// -- slot_of_area first, the same CommitCannotDetermineAreaText on failure, the
// same SET TALK read, the same commit_one_area call. Only the return differs.
// ---------------------------------------------------------------------------
namespace cli { namespace commit {

std::string describe(const Outcome& outcome)
{
    switch (outcome.verdict) {
        case Verdict::Complete:
            return "the buffered changes are committed";
        case Verdict::NoChanges:
            return "there were no buffered changes to commit";
        case Verdict::PartialRecordFailure:
            return "COMMIT applied " + std::to_string(outcome.applied_ok) +
                   " record(s) and could not apply " + std::to_string(outcome.applied_fail) +
                   "; the unapplied changes are still buffered";
        case Verdict::FinalizeFailure:
            return "COMMIT applied the records but a finalize step failed "
                   "(memo, index, or journal); the buffered changes were restored";
        case Verdict::RefusedByTrigger:
            return "a BEFORE trigger refused the commit; nothing was applied and "
                   "the changes are still buffered";
        case Verdict::AreaUnknown:
            return "the work area holding the buffered changes could not be "
                   "determined; nothing was attempted";
    }
    return "COMMIT reported an unrecognized verdict";
}

void commit_area(xbase::DbArea& A, bool interactive_rebuild, Outcome& out)
{
    out = Outcome{};

    const int area0 = cli::slot_of_area(&A);
    if (area0 < 0) {
        cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitCannotDetermineAreaText);
        out.verdict = Verdict::AreaUnknown;
        return;
    }

    const bool talk = Settings::instance().talk_on.load();
    const CommitResult result = commit_one_area(A, area0, talk, interactive_rebuild);

    out.applied_ok   = result.applied_ok;
    out.applied_fail = result.applied_fail;
    switch (result.status) {
        case CommitStatus::NoChanges:            out.verdict = Verdict::NoChanges;            break;
        case CommitStatus::Complete:             out.verdict = Verdict::Complete;             break;
        case CommitStatus::PartialRecordFailure: out.verdict = Verdict::PartialRecordFailure; break;
        case CommitStatus::FinalizeFailure:      out.verdict = Verdict::FinalizeFailure;      break;
        case CommitStatus::RefusedByTrigger:     out.verdict = Verdict::RefusedByTrigger;     break;
    }
}

}} // namespace cli::commit

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


    // AIF-159 section 3 -- REFUSE A NATIVE COMMIT INSIDE A SQL TRANSACTION.
    //
    // The hazard: this command knows nothing about sql_transaction_state, so a
    // native COMMIT applies the buffer and leaves the SQL scope OPEN. Every
    // later autocommit DML then sees state.active and STAGES instead of
    // committing. The user opened no transaction, is now in one, and nothing
    // says so -- each statement reports success while the writes pile up
    // unapplied.
    //
    // Refuse rather than release, on the owner's ruling 2026-09-09, because
    // SET MODE already refuses on exactly this hazard: "SET MODE: COMMIT or
    // ROLLBACK the active SQL transaction first" (src/cli/cmd_set.cpp:730).
    // One policy for one hazard beats two answers in one codebase.
    //
    // THE GUARD IS ON THE COMMAND, NOT ON cli::commit::commit_area(). That
    // separation is the whole reason the earlier refactor was worth doing:
    // commit_sql_transaction calls the shared body, so a SQL-mode COMMIT still
    // reaches the buffer and cannot refuse itself here.
    //
    // Placed after the argument loop so COMMIT USAGE still prints, and before
    // both branches so COMMIT ALL is covered too -- ALL would otherwise walk
    // into the enlisted area from the side.
    if (sqlsel::transaction_active()) {
        std::cout << "COMMIT: a SQL transaction is active; end it with COMMIT or "
                     "ROLLBACK in SQL mode (SET MODE SQL). A native COMMIT would "
                     "apply the buffer and leave the transaction open.\n";
        return;
    }

    const bool talk = Settings::instance().talk_on.load();

    if (!all) {
        // AIF-159: same work, same output; the verdict is simply available now.
        cli::commit::Outcome outcome;
        cli::commit::commit_area(A, interactive_rebuild, outcome);
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
