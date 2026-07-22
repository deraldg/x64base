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

// Persistent buffer / journal stubs
BufferPersistenceMode persistence_mode(int area0);
bool is_persistent_enabled(int area0);
void set_persistence_mode(int area0, BufferPersistenceMode mode);
std::string journal_path(int area0);
void set_journal_path(int area0, const std::string& path);
void clear_journal_state(int area0);

// Stub hooks. These are intentionally no-op placeholders for the future
// persistent TABLE BUFFER journal. They centralize the future update points.
bool journal_note_buffer_on(int area0, const std::string& table_name = std::string{});
bool journal_note_change(int area0, const ChangeEntry& entry);
// Write-ahead: append the COMMIT marker and durably fsync the redo log BEFORE the
// buffered changes are applied to the DBF. Returns false if the durable sync
// fails (caller must abort the commit). No-op (true) unless RamJournal is active.
bool journal_begin_commit(int area0);
bool journal_note_commit(int area0);
bool journal_note_rollback(int area0);

// Crash recovery: on table open, if a `<dbf>.tbj` redo log exists, replay it into
// the DBF when it carries a COMMIT marker (idempotent) or discard it otherwise,
// then remove the log. Returns true iff a committed log was replayed. Safe to
// call on every USE (a quick no-op when no log is present).
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