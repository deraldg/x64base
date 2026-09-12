// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// cli/table_state.hpp
#pragma once

#include <cstdint>
#include <cstdio>
#include <vector>
#include <map>
#include <array>
#include <stdexcept>
#include <string>

#include "xbase.hpp"  // for xbase::MAX_AREA

namespace dottalk::table {

// ─────────────────────────────────────────────────────────────────────────────
// Constants & Types
// ─────────────────────────────────────────────────────────────────────────────

// Field cap derives from the one build-vector authority (AIF-044) instead of an
// independent literal, so the table-buffer bit-array width (kWords) can never silently
// disagree with xbase::MAX_FIELDS again. The static_assert enforces the invariant that
// was previously only a comment ("must always agree with xbase::MAX_FIELDS").
constexpr int kMaxFields = static_cast<int>(dottalk::build::max_fields);
constexpr int kWords     = (kMaxFields + 63) / 64;
static_assert(kMaxFields == static_cast<int>(xbase::MAX_FIELDS),
              "table-buffer kMaxFields must equal engine xbase::MAX_FIELDS (AIF-044)");

// Change operation bit flags
enum ChangeType : std::uint64_t {
    CHANGE_INSERT = 1ULL << 0,
    CHANGE_UPDATE = 1ULL << 1,
    CHANGE_DELETE = 1ULL << 2,
};

// Single change record
struct ChangeEntry {
    std::uint64_t              recno         = 0;   // RECNO64: 1-based; 0 = unset
    std::uint64_t              dirty_flags   = 0;
    int                        priority      = 0;       // higher = newer
    std::uint64_t              field_bits[kWords]{};
    std::map<int, std::string> new_values;              // field1 → new value
};

// Per-area change buffer
class TableBuffer {
public:
    static constexpr size_t kMaxChanges = dottalk::build::table_buffer::max_changes; // AIF-044

    bool                            history_enabled = false;  // true = keep full history, false = keep only latest
    std::multimap<std::uint64_t, ChangeEntry> changes;
    int                             next_priority = 0;

    bool empty() const { return changes.empty(); }

    void clear() {
        changes.clear();
        next_priority = 0;
    }

    // Returns the priority assigned to the resulting entry: in history mode the
    // new per-write priority (1..255), in non-history mode 1. 0 means "not added"
    // (buffer full). Callers use this to journal full-fidelity retained edits.
    int add_change(std::uint64_t recno, std::uint64_t flags,
                   const std::uint64_t* source_field_bits = nullptr,
                   int field1 = 0, const std::string& new_value = "");
};

// Per-area state
enum class BufferPersistenceMode {
    RamOnly = 0,
    RamJournal = 1,
};

struct BufferJournalInfo {
    BufferPersistenceMode mode {BufferPersistenceMode::RamOnly};
    std::string           path {};
    bool                  open {false};
    std::FILE*            fp {nullptr};       // append-only .tbj handle while open
    std::uint64_t         change_count {0};   // redo records since the log opened

    // ---- WHOSE TRANSACTION IS THIS, AND IS IT STILL OURS TO REVERSE? -------
    //
    // AIF-160. Two bits that turn this struct into a state machine, because a
    // grouped transaction has a state a single-table one never had: DECIDED BUT
    // NOT YET APPLIED.
    //
    //   prepared   a P record has been written. Set by journal_begin_prepare,
    //              which REFUSES a second call -- two P records in one log name
    //              two groups for one journal, the reader refuses such a log,
    //              and it then never replays and never goes away.
    //
    //   decided    the group log says this transaction COMMITTED. From this
    //              instant the journal is NOT THIS TRANSACTION'S TO DELETE.
    //              journal_note_rollback refuses while it is set.
    //
    // WHY THE SECOND ONE EXISTS AT ALL. After decide_committed lands, a member
    // whose APPLY then fails still holds its journal, on purpose: the decision
    // row exists and the P record is there, so the next USE replays it. Every
    // teardown path in the tree calls journal_note_rollback, which std::removes
    // that file. A committed transaction, a decision row saying so, and its
    // redo deleted by cleanup.
    //
    // THE ALTERNATIVE WAS A PARAMETER ON THE TEARDOWN and it was rejected: a
    // flag at the call site makes the deletion CONDITIONAL, correct only while
    // every present and future caller passes the right value, with a silently
    // lost commit as the price of one wrong one. Here the deletion is
    // IMPOSSIBLE instead, and the callers nobody has written yet are covered
    // by the same check.
    //
    // IN MEMORY, DELIBERATELY, AND THE CRASH CASE ARGUES FOR IT RATHER THAN
    // AGAINST. These only need to outlive the teardown, not the process. A
    // crash with `decided` set leaves the journal on disk with its P record and
    // the decision row in the group log, which is exactly the state recovery
    // knows how to finish. Writing the bit durably into each member's journal
    // would be a SECOND SPELLING of the decision, plus an fsync per member
    // after the group is already true.
    bool                  prepared {false};
    bool                  decided  {false};
};

struct AreaState {
    bool        enabled    {false};
    bool        dirty      {false};
    bool        stale_any  {false};

    BufferJournalInfo journal{};

    std::uint64_t stale_bits[kWords]{};

    TableBuffer tb{};
    int         tx_depth{0};
};

// ─────────────────────────────────────────────────────────────────────────────
// Interface
// ─────────────────────────────────────────────────────────────────────────────

bool get_state(int area0, AreaState& out);
bool is_enabled(int area0);
bool is_dirty(int area0);
bool is_stale(int area0);

void set_enabled(int area0, bool value);
void set_dirty(int area0, bool value);
void set_stale(int area0, bool value);

void mark_stale_field(int area0, int field1);
void clear_stale_fields(int area0);

bool get_stale_fields(int area0, std::vector<int>& out_field1);

void set_enabled_all(bool value);
void clear_dirty_all();
void clear_stale_all();

int  count_enabled();
int  count_dirty();
int  count_stale();

void reset_all();

// Persistent buffer / write-ahead journal.
//
// NOT stubs. This is an implemented WAL: `<dbf>.tbj`, a per-transaction append-only
// redo log (format TBJ1; `U`/`D` records carrying priority + H/S retention mode, values
// hex-encoded), durably fsynced with a `C <count>` COMMIT marker BEFORE the buffered
// changes are applied to the DBF, and replayed idempotently on open by
// recover_table_buffer_journal(), which refuses a format version it does not
// understand rather than half-replaying it. See src/cli/table_state.cpp.
//
// SCOPE (AIF-061): the log covers DBF RECORD writes. It does NOT yet cover the memo
// store -- an x64 memo REPLACE converts text to a stored object-id and journals only
// that id, so a crash between the DBF apply and the memo write can leave a recovered
// record referencing an object the memo store never durably wrote. Record-level
// atomicity is real; whole-row atomicity for memo-bearing rows is not yet.
// Lane: docs/maintenance/AI_MEMO_WAL_ATOMICITY_LANE_V1.md
BufferPersistenceMode persistence_mode(int area0);
bool is_persistent_enabled(int area0);
void set_persistence_mode(int area0, BufferPersistenceMode mode);
std::string journal_path(int area0);
void set_journal_path(int area0, const std::string& path);
void clear_journal_state(int area0);

// Implemented WAL hooks. Each is a no-op returning true when persistence mode is
// not RamJournal, so callers can invoke them unconditionally; when RamJournal is
// active they do real durable work. (These were placeholders once; they are not now.)
bool journal_note_buffer_on(int area0, const std::string& table_name = std::string{});
bool journal_note_change(int area0, const ChangeEntry& entry);
// Write-ahead: append the COMMIT marker and durably fsync the redo log BEFORE the
// buffered changes are applied to the DBF. Returns false if the durable sync
// fails (caller must abort the commit). No-op (true) unless RamJournal is active.
bool journal_begin_commit(int area0);
// Write-ahead for one member of a MULTI-AREA GROUP (AIF-160). Appends
// `P <group-key> <members>` in place of the `C <count>` marker, promotes this
// log's header to TBJ2, and durably fsyncs -- all before the buffered changes
// reach the DBF, exactly as journal_begin_commit does.
//
// A PREPARED SPAN IS DURABLE AND UNDECIDED. It commits only when
// dottalk::group::decide_committed lands its single row; until then every
// reader discards it by presumed abort. False means this member did not
// prepare, and the caller must abort the WHOLE group.
//
// Never call this on an area that also gets journal_begin_commit: a log
// carrying both markers names two authorities for one question and recovery
// refuses it outright.
bool journal_begin_prepare(int area0, const std::string& group_key, int members);

// THE GROUP SAID YES. Called once per member the instant decide_committed
// returns true, and nothing else may call it: it is the transfer of ownership
// described on BufferJournalInfo::decided. After this, journal_note_rollback
// refuses this area's journal and only journal_note_commit can remove it.
//
// Returns false only for an out-of-range area or one with no journal, and the
// caller has nothing useful to do with that -- the group is already committed
// by the time this runs.
bool journal_note_decided(int area0);

// True when the log for this area already carries a durable P record -- that
// is, when this transaction is a member of a group and journal_begin_commit
// will REFUSE to write a C over it. Read-only, and safe on an area with no
// journal at all.
//
// THE REFUSAL IS THE GUARANTEE; THIS IS THE COURTESY. A caller that skips
// this still cannot produce a C-and-P log, it just reports the refusal in
// worse words.
bool journal_is_prepared(int area0);

bool journal_note_commit(int area0);

// DISCARD AN UNCOMMITTED TRANSACTION. REFUSES, AND CHANGES NOTHING, once the
// area has been marked decided -- see BufferJournalInfo::decided. Every caller
// in the tree ignores the return, which is the correct posture for all of them
// except a caller that genuinely means to destroy a committed transaction, and
// there is no such caller.
bool journal_note_rollback(int area0);

// Is this file engine-owned state under the SYS slot? (AIF-160)
//
// SYS holds tables that cannot be rebuilt from anything -- the multi-area commit
// group log first among them -- and two rules follow, both ENFORCED rather than
// documented: a SYS table is refused the table buffer, and it is skipped by
// journal recovery. The second is why the first exists: recovering a prepared
// span means asking the group log whether its group committed, so a group log
// that could carry a journal would have to be recovered by consulting itself.
//
// A RULE ABOUT LOCATION, not a registry of exempt paths -- a guard that depends
// on something registering at startup is off whenever registration is missed.
bool is_engine_state_file(const std::string& file_path);

// Crash recovery: on table open, if a `<dbf>.tbj` redo log exists, replay it into
// the DBF when it carries a COMMIT marker (idempotent) or discard it otherwise,
// then remove the log. Returns true iff a committed log was replayed. Safe to
// call on every USE (a quick no-op when no log is present).
//
// THE VERSION IS CHECKED FIRST (2026-09-11), and it was not before. The header
// this WAL has always written was never read: the reader scanned for a `C`
// marker, replayed `I`/`U`/`D`, and skipped anything else with no default
// branch. A log from a NEWER build was therefore half replayed -- commit marker
// honoured, unknown records dropped in silence -- which for AIF-061's memo
// records means recovered rows referencing objects the memo store never wrote.
//
// A version this build does not understand is now REFUSED AND PRESERVED: no
// replay, and the log is deliberately NOT deleted, because it may be a
// committed transaction a newer build can still replay. The refusal prints and
// this function returns false; the table is open and usable either way. An
// EMPTY log is not a version problem -- it is a transaction that died before
// its header -- and is discarded as it always was.
//
// This build still WRITES TBJ1. The gate ships BEFORE the TBJ2 bump on purpose:
// a rule nothing enforces is not a compatibility rule, and adding the check
// afterwards leaves binaries in the field that half-replay silently.
// Graded by src/tests/test_journal_version_gate.cpp, whose G0 control proves
// the fixture can replay at all before the refusal arms are believed.
bool recover_table_buffer_journal(xbase::DbArea& area);

// History mode control
bool is_history_enabled(int area0);
void set_history_enabled(int area0, bool value);

// Table buffer access
TableBuffer&       get_tb(int area0);
const TableBuffer& get_tb_const(int area0);

// Area index validation
inline bool in_range(int area0) {
    return area0 >= 0 && area0 < xbase::MAX_AREA;
}

// Debug helper
void test_add_change(int area0, std::uint64_t recno, std::uint64_t flags = CHANGE_UPDATE,
                     int field1 = 0, const std::string& new_value = "");

} // namespace dottalk::table