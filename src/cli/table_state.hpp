// cli/table_state.hpp
#pragma once

#include <cstdint>
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

constexpr int kMaxFields = 256;
constexpr int kWords     = (kMaxFields + 63) / 64;

// Change operation bit flags
enum ChangeType : std::uint64_t {
    CHANGE_INSERT = 1ULL << 0,
    CHANGE_UPDATE = 1ULL << 1,
    CHANGE_DELETE = 1ULL << 2,
};

// Single change record
struct ChangeEntry {
    int                        recno         = -1;
    std::uint64_t              dirty_flags   = 0;
    int                        priority      = 0;       // higher = newer
    std::uint64_t              field_bits[kWords]{};
    std::map<int, std::string> new_values;              // field1 → new value
};

// Per-area change buffer
class TableBuffer {
public:
    static constexpr size_t kMaxChanges = 10000;

    bool                            history_enabled = false;  // true = keep full history, false = keep only latest
    std::multimap<int, ChangeEntry> changes;
    int                             next_priority = 0;

    bool empty() const { return changes.empty(); }

    void clear() {
        changes.clear();
        next_priority = 0;
    }

    void add_change(int recno, std::uint64_t flags,
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
bool journal_note_commit(int area0);
bool journal_note_rollback(int area0);

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
void test_add_change(int area0, int recno, std::uint64_t flags = CHANGE_UPDATE,
                     int field1 = 0, const std::string& new_value = "");

} // namespace dottalk::table