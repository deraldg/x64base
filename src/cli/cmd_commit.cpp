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
#include "cli/group_log.hpp"        // AIF-160: one decision that spans N journals

#include <optional>                 // AIF-160: guards that outlive phase 1

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

// ---------------------------------------------------------------------------
// THE COMMIT SEAM (AIF-160)
//
// This function used to run DECIDE-WHETHER and DO-IT in one body, which is
// correct for one area and impossible for a group. A multi-area commit needs
// the phases interleaved ACROSS areas:
//
//     pass 1   BEFORE triggers, every area        -- commit_prepare_area
//     pass 2   journal_begin_prepare, every area  -- N durable prepares
//     DECIDE   decide_committed, ONCE             -- the group becomes true
//     pass 3   apply + sync + note_commit, all    -- commit_apply_area
//
// SPLITTING IT IS NOT A MATTER OF CUTTING AT THE WRITE-AHEAD MARKER. The insert
// table lock and the cursor restore are RAII with FUNCTION SCOPE, and a group
// must hold every member's lock from ITS OWN prepare until the WHOLE group has
// applied. Cut the body in two and those guards release at the end of phase 1,
// between the prepare and the decision -- which is the exact window the group
// log exists to make safe. That is why this struct exists and why the two
// halves are not free functions.
//
// DESTRUCTION ORDER IS LOad-BEARING. Members destroy in reverse declaration
// order, so `restore` must be declared AFTER `insert_lock` to reproduce the
// order the original function's locals had: cursor first, table lock second.
//
// THE SINGLE-AREA PATH IS THE SAME CODE IN THE SAME ORDER. commit_one_area is
// now prepare-then-marker-then-apply, so every existing COMMIT arm exercises
// both halves. That is deliberate: a refactor whose only proof is a new test
// proves the new test.
struct AreaCommitContext {
    xbase::DbArea* A                   = nullptr;
    int            area0               = -1;
    bool           talk                = false;
    bool           interactive_rebuild = false;

    std::optional<InsertTableLockGuard> insert_lock;   // released LAST
    std::optional<CursorRestore>        restore;       // released FIRST

    // A later memo/index/journal failure must not make the pending operation
    // disappear; every finalize failure in phase 3 restores this.
    std::multimap<std::uint64_t, dottalk::table::ChangeEntry> pending_before;

    // True only when phase 3 must run. False means the caller returns the
    // status it was given and writes NO write-ahead marker of any kind.
    bool prepared = false;
};

// PHASE 1. Locks, snapshot, BEFORE triggers. Stops immediately before the
// write-ahead marker -- which marker to write is the CALLER's decision, and is
// the only difference between a solo commit and a group member.
static CommitResult commit_prepare_area(AreaCommitContext& ctx)
{
    xbase::DbArea& A   = *ctx.A;
    const int      area0 = ctx.area0;
    const bool     talk  = ctx.talk;

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
    // Constructed IN THE CONTEXT, not as a local: for a group these must stay
    // held across the decision. emplace builds in place, so neither guard needs
    // to be movable.
    ctx.insert_lock.emplace(A, has_insert);
    if (!ctx.insert_lock->ready) {
        std::cout << "COMMIT: insert table lock refused";
        if (!ctx.insert_lock->error.empty())
            std::cout << " (" << ctx.insert_lock->error << ")";
        std::cout << ".\n";
        return {CommitStatus::PartialRecordFailure, 0, 1};
    }

    ctx.restore.emplace(A);

    // A later memo/index/journal failure must not make the pending operation
    // disappear. Inserts, updates, and deletes are idempotent at their reserved
    // record number and are safe to reapply on retry.
    ctx.pending_before = tb.changes;

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

    // ===================== THE SEAM ========================================
    // Everything above decided WHETHER. Everything below DOES IT. Between the
    // two sits exactly one act -- the write-ahead marker -- and which marker to
    // write is the only thing that distinguishes a solo commit from one member
    // of a group. The caller writes it.
    ctx.prepared = true;
    return {};
}

// PHASE 3. The write-ahead marker is already durable when this is entered:
// `C <count>` for a solo commit, or `P <key> <n>` PLUS a landed group decision
// row for a member. From here the two are identical, which is the property the
// whole lane rests on -- a group member applies exactly as a solo commit does,
// and recovery tells them apart by which marker it finds.
static CommitResult commit_apply_area(AreaCommitContext& ctx)
{
    xbase::DbArea& A     = *ctx.A;
    const int      area0 = ctx.area0;
    const bool     talk  = ctx.talk;
    const bool     interactive_rebuild = ctx.interactive_rebuild;

    auto& tb = dottalk::table::get_tb(area0);
    const auto& pending_before = ctx.pending_before;

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

// The solo path, unchanged in behaviour and now expressed as the same three
// steps a group takes with N=1: prepare, write the marker, apply. Every
// existing COMMIT arm runs through here, which is what makes those arms the
// regression net for the split rather than a separate test having to be it.
static CommitResult commit_one_area(xbase::DbArea& A,
                                    int area0,
                                    bool talk,
                                    bool interactive_rebuild)
{
    AreaCommitContext ctx;
    ctx.A                   = &A;
    ctx.area0               = area0;
    ctx.talk                = talk;
    ctx.interactive_rebuild = interactive_rebuild;

    const CommitResult prep = commit_prepare_area(ctx);
    if (!ctx.prepared) return prep;

    // Write-ahead: durably fsync the redo log + COMMIT marker BEFORE applying the
    // buffered changes to the DBF. If the durable sync fails, abort the commit and
    // keep the buffer intact (RamOnly mode returns true and is unaffected).
    if (!dottalk::table::journal_begin_commit(area0)) {
        dottalk::table::set_dirty(area0, true);
        cli::cmdout::print_prefixed_message(
            "COMMIT", dottalk::helpdata::MessageId::CommitJournalFinalizeFailedText);
        return {CommitStatus::FinalizeFailure, 0, 1};
    }

    return commit_apply_area(ctx);
}

} // namespace

namespace cli { namespace commit {

// ---------------------------------------------------------------------------
// ONE DECISION THAT SPANS N JOURNALS (AIF-160).
//
// DEFINED OUTSIDE THE ANONYMOUS NAMESPACE so something can prove it runs. The
// contract, and why it is exported at all, is in include/cli/table_buffer.hpp.
// It still uses the file-local halves above -- AreaCommitContext,
// commit_prepare_area, commit_apply_area -- which stay internal: the PHASES are
// this file's business, the DECISION is the lane's.
//
// TWO-PASS TRIGGERS, ruled 2026-09-11. Every BEFORE trigger fires in pass 1,
// before any area prepares, so a veto costs one pass and ZERO durable writes.
// Firing them at prepare would make a veto throw away prepares already synced
// to platter. This is cmd_commit.cpp's own all-or-nothing-per-area doctrine
// raised one level: all-or-nothing per GROUP.
//
// THE ONLY INSTANT THAT MATTERS is decide_committed below. Before it, N durable
// prepares are N nothings and every one of them is discarded by presumed abort.
// After it, the group is true and every member's apply is replayable from its
// own journal. There is no third state, which is the entire point.
//
// ABORT IS PERFORMED, NOT LEFT. Presumed abort is the RECOVERY rule, for a
// process killed between prepare and decide. This process holds every member
// open and knows the group failed, so it discards the prepared spans itself
// rather than leaving them for some future USE to notice.
GroupCommitResult commit_group(const std::vector<GroupMember>& members,
                               bool talk,
                               bool interactive_rebuild)
{
    GroupCommitResult out;

    // ---- PASS 1: locks, snapshots, and EVERY before-trigger ---------------
    std::vector<AreaCommitContext> ctxs(members.size());
    for (std::size_t i = 0; i < members.size(); ++i) {
        ctxs[i].A                   = members[i].A;
        ctxs[i].area0               = members[i].area0;
        ctxs[i].talk                = talk;
        ctxs[i].interactive_rebuild = interactive_rebuild;

        const CommitResult r = commit_prepare_area(ctxs[i]);
        if (ctxs[i].prepared) continue;

        // An EMPTY buffer is not a refusal. It contributes nothing and is
        // simply not a member -- dropping it is what keeps `members` equal to
        // the number of P records that will exist.
        if (r.status == CommitStatus::NoChanges) continue;

        // Anything else IS a refusal, and nothing has been written yet: no
        // journal marker, no member rows, no decision. The guards release as
        // ctxs unwinds.
        out.error = "group aborted in pass 1 -- a member refused before any"
                    " durable write";
        return out;
    }

    std::vector<std::size_t> live;
    for (std::size_t i = 0; i < ctxs.size(); ++i)
        if (ctxs[i].prepared) live.push_back(i);

    out.members = static_cast<int>(live.size());
    if (live.empty()) { out.committed = true; return out; }   // nothing to do

    // ---- The group's identity, and the members table ----------------------
    const std::string key = dottalk::group::mint_group_key();
    std::vector<std::string> member_paths;
    member_paths.reserve(live.size());
    for (const std::size_t i : live) member_paths.push_back(ctxs[i].A->filename());

    // Written BEFORE any prepare and deliberately NOT synced -- it is off the
    // critical path. Losing it is safe by construction: with no member rows,
    // retirement cannot establish that this group settled, so it keeps the
    // decision row. The conservative direction without anything choosing it.
    std::string merr;
    (void)dottalk::group::record_members(key, member_paths, &merr);

    // ---- PASS 2: N durable prepares, still N nothings ---------------------
    std::size_t prepared_through = 0;
    bool all_prepared = true;
    for (const std::size_t i : live) {
        if (!dottalk::table::journal_begin_prepare(
                ctxs[i].area0, key, static_cast<int>(live.size()))) {
            all_prepared = false;
            break;
        }
        ++prepared_through;
    }

    if (!all_prepared) {
        // NO DECISION ROW WAS WRITTEN, so every span above is already dead by
        // presumed abort. Discard them anyway -- see "abort is performed".
        //
        // INCLUSIVE OF THE ONE THAT FAILED, which is the whole reason for the
        // +1. prepared_through counts SUCCESSES, so live[prepared_through] is
        // the member whose prepare returned false -- and that member is the one
        // most likely to have left something on disk, not the least:
        // journal_begin_prepare can fail AFTER promoting the header, after the
        // seek back to end, on a partial fwrite of the marker, or in
        // wal_durable_sync. Stopping before it left the only residue anyone
        // would have to clean.
        //
        // The malformed-P residue is the expensive one. A torn P line is
        // "neither marker" and the reader discards it, which is fine; a
        // COMPLETE but unsynced P for a group that never decided is presumed
        // abort, also fine. But a P record that parses short -- key and no
        // member count -- is REFUSED AND PRESERVED, so it warns on every USE of
        // that table forever. That is the regression the empty-log branch was
        // added to avoid, in a different shape.
        //
        // It also restores the dirty flag for that member. Every other member
        // gets its buffer marked dirty again so the user can correct and retry;
        // the asymmetry was the tell that this index had been dropped rather
        // than excluded.
        //
        // journal_note_rollback is safe on an area whose journal never opened:
        // it removes a path that may not exist and clears state that may
        // already be clear.
        const std::size_t through = std::min(prepared_through + 1, live.size());
        for (std::size_t n = 0; n < through; ++n) {
            dottalk::table::journal_note_rollback(ctxs[live[n]].area0);
            dottalk::table::set_dirty(ctxs[live[n]].area0, true);
        }
        out.error = "group aborted in pass 2 -- a member could not durably"
                    " prepare; no decision was written";
        return out;
    }

    // ---- THE DECISION. One row, one fsync, one instant. -------------------
    std::string derr;
    if (!dottalk::group::decide_committed(key, static_cast<int>(live.size()), &derr)) {
        for (const std::size_t i : live) {
            dottalk::table::journal_note_rollback(ctxs[i].area0);
            dottalk::table::set_dirty(ctxs[i].area0, true);
        }
        out.error = "group aborted at the decision -- " + derr;
        return out;
    }

    // THE JOURNALS STOP BEING THIS TRANSACTION'S TO DELETE, HERE.
    //
    // One line per member, and it is the transfer of ownership described on
    // BufferJournalInfo::decided. A member whose apply fails below keeps its
    // journal ON PURPOSE -- the decision row exists, the P record is there, and
    // the next USE replays it -- and every teardown path in the tree reaches
    // journal_note_rollback, which would std::remove exactly that file.
    //
    // Marking is done in its own pass rather than inside the apply loop below,
    // because the apply loop can fail and this cannot be conditional on it: the
    // group is true for every member the instant decide_committed returned, not
    // member by member as each one finishes.
    for (const std::size_t i : live) {
        (void)dottalk::table::journal_note_decided(ctxs[i].area0);
    }

    // ---- PASS 3: from here the group IS committed -------------------------
    // A failure below is a member that has not yet APPLIED a transaction that
    // has already COMMITTED. That is not a lost commit: the member's journal
    // still carries its P record and the decision row exists, so the next USE
    // of that table replays it. This is the one place where reporting a failure
    // and losing data are genuinely different things.
    out.committed = true;
    for (const std::size_t i : live) {
        const CommitResult r = commit_apply_area(ctxs[i]);
        out.applied_ok  += r.applied_ok;
        out.applied_bad += r.applied_fail;
        if (r.status != CommitStatus::Complete && out.error.empty()) {
            out.error = "the group COMMITTED and a member did not finish"
                        " applying; its journal replays at the next USE";
        }
    }
    return out;
}

}} // namespace cli::commit

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

// ---------------------------------------------------------------------------
// GROUPCOMMIT -- COMMIT ALL's atomic twin (AIF-160)
//
// A SEPARATE VERB, per decision 6.4. COMMIT and COMMIT ALL are byte-for-byte
// unchanged, which AIF-159 spent four commits earning and this lane does not
// spend.
//
// THE CONTRAST IS THE WHOLE POINT, and the two commands sit next to each other
// so a reader sees it: COMMIT ALL loops areas and commits each independently,
// not stopping on failure. A crash between its second and third member leaves
// two tables written and one not, each of them perfectly consistent with its own
// journal, and the transaction the user meant torn in half. GROUPCOMMIT prepares
// every member, writes ONE durable decision, and only then applies. There is no
// instant at which some members are committed and others are not.
//
// STRAIGHT PROSE, NOT THE MESSAGE CATALOGUE. This verb is experimental and its
// output will change while the lane settles; minting catalogue MessageIds now
// would freeze wording that is not ready, and every one of them would need a
// locale row. std::cout matches how the durable_sync warnings in this file and
// in cmd_workspace.cpp already report.
void cmd_GROUPCOMMIT(xbase::DbArea& A, std::istringstream& in) {
    (void)A;   // the group is gathered from the engine, not from the current area

    auto* eng = shell_engine();
    if (!eng) {
        std::cout << "GROUPCOMMIT: engine unavailable.\n";
        return;
    }

    bool interactive_rebuild = false;
    for (std::string tok; in >> tok; ) {
        std::string up = tok;
        for (auto& c : up) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));

        if (up == "USAGE" || up == "HELP" || up == "?") {
            std::cout <<
                "GROUPCOMMIT -- commit every buffered area as ONE atomic decision.\n"
                "  GROUPCOMMIT              commit all dirty areas as one group\n"
                "  GROUPCOMMIT AUTO         rebuild indexes without prompting (default)\n"
                "  GROUPCOMMIT MANUAL       prompt on index rebuild\n"
                "  GROUPCOMMIT USAGE        this text\n"
                "\n"
                "Arguments may appear in any order; the LAST of AUTO/MANUAL wins. An\n"
                "unrecognized argument is REFUSED and nothing is committed.\n"
                "\n"
                "Unlike COMMIT ALL, which commits each area independently, a crash\n"
                "during GROUPCOMMIT leaves either ALL members applied or NONE.\n"
                "\n"
                "REQUIRES 'TABLE BUFFER ON PERSISTENT' for that guarantee to survive a\n"
                "power cut, and the ON is load-bearing: 'TABLE BUFFER PERSISTENT' alone\n"
                "sets the mode WITHOUT enabling the buffer, so no journal is opened and\n"
                "there is nothing to recover. Under the default RamOnly there is no log.\n"
                "\n"
                "IF A MEMBER DOES NOT FINISH APPLYING, the group has still COMMITTED and\n"
                "that member's journal replays at the next USE of its table. Its buffer\n"
                "is left holding a copy of a transaction that ALREADY committed, so\n"
                "COMMIT is refused and CLOSE, USE and QUIT each prompt and cancel.\n"
                "ROLLBACK is the exit: it discards the stale buffer and KEEPS the\n"
                "journal, which is what lets the next USE finish the transaction.\n";
            return;
        } else if (up == "MANUAL" || up == "INTERACTIVE") {
            interactive_rebuild = true;
        } else if (up == "AUTO") {
            interactive_rebuild = false;
        } else {
            std::cout << "GROUPCOMMIT: unrecognized argument '" << tok
                      << "'. GROUPCOMMIT USAGE for help.\n";
            return;
        }
    }

    // Same refusal as COMMIT, for the same reason (AIF-159 section 3): this
    // command knows nothing about sql_transaction_state, so it would apply the
    // buffer and leave the SQL scope open.
    if (sqlsel::transaction_active()) {
        std::cout << "GROUPCOMMIT: a SQL transaction is active; end it with COMMIT or "
                     "ROLLBACK in SQL mode (SET MODE SQL).\n";
        return;
    }

    std::vector<cli::commit::GroupMember> members;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        auto& Ai = eng->area(i);
        if (!Ai.isOpen()) continue;
        if (!dottalk::table::is_enabled(i)) continue;
        if (dottalk::table::get_tb(i).empty()) continue;

        cli::commit::GroupMember m;
        m.A     = &Ai;
        m.area0 = i;
        members.push_back(m);
    }

    if (members.empty()) {
        std::cout << "GROUPCOMMIT: no buffered changes in any area.\n";
        return;
    }

    const bool talk = Settings::instance().talk_on.load();
    const cli::commit::GroupCommitResult r =
        cli::commit::commit_group(members, talk, interactive_rebuild);

    if (!r.committed) {
        std::cout << "GROUPCOMMIT: REFUSED -- " << r.error << ".\n"
                  << "  NOTHING was applied and no group decision was written."
                     " Every buffer is intact.\n";
        return;
    }

    std::cout << "GROUPCOMMIT: committed " << r.members << " table(s) as one group, "
              << r.applied_ok << " record(s) applied";
    if (r.applied_bad > 0) std::cout << ", " << r.applied_bad << " failed";
    std::cout << ".\n";

    // The group is COMMITTED. A member that did not finish applying has not lost
    // its transaction -- its journal still carries the P record and the decision
    // row exists, so the next USE of that table replays it. Saying so matters:
    // this is the one place where reporting a failure and losing data are
    // genuinely different things, and a reader who assumes the usual meaning of
    // "failed" would reach for a backup they do not need.
    if (!r.error.empty()) {
        std::cout << "  NOTE: " << r.error << ".\n";
    }
}
