#include "cli/table_state.hpp"

#include <array>
#include <cstring>
#include <stdexcept>
#include <iostream>
#include <iomanip>   // for std::setw, std::hex
#include <sstream>

#include "xbase.hpp"

#ifdef _WIN32
  #include <io.h>
  #include <windows.h>
#else
  #include <unistd.h>
#endif

namespace dottalk::table {

// Durable sync of the WAL file: flush the C stdio buffer to the OS, then force
// the OS to flush to stable storage (FlushFileBuffers on Windows / fsync).
static bool wal_durable_sync(std::FILE* fp) {
    if (!fp) return false;
    if (std::fflush(fp) != 0) return false;
#ifdef _WIN32
    const int fd = _fileno(fp);
    if (fd < 0) return false;
    const intptr_t h = _get_osfhandle(fd);
    if (h == -1) return false;
    return FlushFileBuffers(reinterpret_cast<HANDLE>(h)) != 0;
#else
    return ::fsync(::fileno(fp)) == 0;
#endif
}

// Hex-encode arbitrary stored bytes so they survive the line-based .tbj format.
static void wal_append_hex(std::string& out, const std::string& raw) {
    static const char* const H = "0123456789ABCDEF";
    for (unsigned char c : raw) {
        out.push_back(H[(c >> 4) & 0xF]);
        out.push_back(H[c & 0xF]);
    }
}

// Decode a hex string (as written by wal_append_hex) back to raw bytes.
static bool wal_hex_decode(const std::string& hex, std::string& out) {
    if (hex.size() % 2 != 0) return false;
    auto nyb = [](char c) -> int {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        return -1;
    };
    out.clear();
    out.reserve(hex.size() / 2);
    for (std::size_t i = 0; i < hex.size(); i += 2) {
        const int hi = nyb(hex[i]);
        const int lo = nyb(hex[i + 1]);
        if (hi < 0 || lo < 0) return false;
        out.push_back(static_cast<char>((hi << 4) | lo));
    }
    return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// Static Data
// ─────────────────────────────────────────────────────────────────────────────

static std::array<AreaState, xbase::MAX_AREA>& state_store() {
    static std::array<AreaState, xbase::MAX_AREA> state{};
    return state;
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

static inline bool any_stale_bits(const AreaState& s) {
    for (int i = 0; i < kWords; ++i) {
        if (s.stale_bits[i] != 0) return true;
    }
    return false;
}

// ─────────────────────────────────────────────────────────────────────────────
// State Access
// ─────────────────────────────────────────────────────────────────────────────

bool get_state(int area0, AreaState& out) {
    if (!in_range(area0)) return false;
    out = state_store()[area0];
    return true;
}

bool is_enabled(int area0) {
    return in_range(area0) && state_store()[area0].enabled;
}

bool is_dirty(int area0) {
    return in_range(area0) && state_store()[area0].dirty;
}

bool is_stale(int area0) {
    if (!in_range(area0)) return false;
    const auto& s = state_store()[area0];
    return s.stale_any || any_stale_bits(s);
}

// ─────────────────────────────────────────────────────────────────────────────
// Setters
// ─────────────────────────────────────────────────────────────────────────────

void set_enabled(int area0, bool enabled) {
    if (!in_range(area0)) return;
    auto& s = state_store()[area0];
    s.enabled = enabled;
    if (enabled) {
        s.tb.clear();
    }
}

void set_dirty(int area0, bool dirty) {
    if (!in_range(area0)) return;
    state_store()[area0].dirty = dirty;
}

void set_stale(int area0, bool stale) {
    if (!in_range(area0)) return;
    auto& s = state_store()[area0];
    if (stale) {
        s.stale_any = true;
    } else {
        s.stale_any = false;
        std::memset(s.stale_bits, 0, sizeof(s.stale_bits));
    }
}

void mark_stale_field(int area0, int field1) {
    if (!in_range(area0)) return;
    if (field1 <= 0 || field1 > kMaxFields) return;

    auto& s = state_store()[area0];
    const int idx0 = field1 - 1;
    const int word = idx0 / 64;
    const int bit  = idx0 % 64;
    s.stale_bits[word] |= (std::uint64_t{1} << bit);
}

void clear_stale_fields(int area0) {
    if (!in_range(area0)) return;
    std::memset(state_store()[area0].stale_bits, 0, sizeof(state_store()[area0].stale_bits));
}

bool get_stale_fields(int area0, std::vector<int>& out_field1) {
    out_field1.clear();
    if (!in_range(area0)) return false;

    const auto& s = state_store()[area0];
    for (int field1 = 1; field1 <= kMaxFields; ++field1) {
        const int idx0 = field1 - 1;
        const int word = idx0 / 64;
        const int bit  = idx0 % 64;
        if (s.stale_bits[word] & (std::uint64_t{1} << bit)) {
            out_field1.push_back(field1);
        }
    }
    return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// Global Operations
// ─────────────────────────────────────────────────────────────────────────────

void set_enabled_all(bool enabled) {
    for (int i = 0; i < xbase::MAX_AREA; ++i) set_enabled(i, enabled);
}

void clear_dirty_all() {
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        state_store()[i].dirty = false;
        state_store()[i].tb.clear();
    }
}

void clear_stale_all() {
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        state_store()[i].stale_any = false;
        std::memset(state_store()[i].stale_bits, 0, sizeof(state_store()[i].stale_bits));
    }
}

int count_enabled() {
    int n = 0;
    for (int i = 0; i < xbase::MAX_AREA; ++i)
        if (state_store()[i].enabled) ++n;
    return n;
}

int count_dirty() {
    int n = 0;
    for (int i = 0; i < xbase::MAX_AREA; ++i)
        if (state_store()[i].dirty) ++n;
    return n;
}

int count_stale() {
    int n = 0;
    for (int i = 0; i < xbase::MAX_AREA; ++i)
        if (is_stale(i)) ++n;
    return n;
}

void reset_all() {
    for (auto& state : state_store()) {
        state = AreaState{};
    }
}


// ─────────────────────────────────────────────────────────────────────────────
// Persistent Buffer / Journal Stubs
// ─────────────────────────────────────────────────────────────────────────────

BufferPersistenceMode persistence_mode(int area0) {
    if (!in_range(area0)) return BufferPersistenceMode::RamOnly;
    return state_store()[area0].journal.mode;
}

bool is_persistent_enabled(int area0) {
    return persistence_mode(area0) == BufferPersistenceMode::RamJournal;
}

void set_persistence_mode(int area0, BufferPersistenceMode mode) {
    if (!in_range(area0)) return;
    auto& j = state_store()[area0].journal;
    j.mode = mode;
    j.open = (mode == BufferPersistenceMode::RamJournal);

    // Stub only. Future implementation should create/open the append-only
    // journal here if RAM+JOURNAL mode is selected.
}

std::string journal_path(int area0) {
    if (!in_range(area0)) return {};
    return state_store()[area0].journal.path;
}

void set_journal_path(int area0, const std::string& path) {
    if (!in_range(area0)) return;
    state_store()[area0].journal.path = path;
}

void clear_journal_state(int area0) {
    if (!in_range(area0)) return;
    auto& j = state_store()[area0].journal;
    if (j.fp) { std::fclose(j.fp); j.fp = nullptr; }
    j.path.clear();
    j.open = false;
    j.change_count = 0;

    // Deliberately do not force mode back to RamOnly. Mode is a user/session
    // setting; COMMIT/ROLLBACK should close or clear journal state without
    // silently changing the selected buffering mode.
}

static std::string default_journal_path_for_area(int area0) {
    std::ostringstream oss;
    oss << "area" << area0 << ".tbj";
    return oss.str();
}

// (Re)open a fresh append-only redo log for a new transaction on this area.
// The log is a sidecar of the DBF (`<dbf>.tbj`) so recovery-on-open can find it.
bool journal_note_buffer_on(int area0, const std::string& table_name) {
    if (!is_persistent_enabled(area0)) return true;

    auto& j = state_store()[area0].journal;
    if (!table_name.empty())     j.path = table_name + ".tbj";
    else if (j.path.empty())     j.path = default_journal_path_for_area(area0);

    if (j.fp) { std::fclose(j.fp); j.fp = nullptr; }
    j.fp = std::fopen(j.path.c_str(), "wb");   // truncate: one log per transaction
    if (!j.fp) { j.open = false; return false; }

    const std::string hdr =
        "TBJ1 " + (table_name.empty() ? j.path : table_name) + "\n";
    if (std::fwrite(hdr.data(), 1, hdr.size(), j.fp) != hdr.size()) {
        std::fclose(j.fp); j.fp = nullptr; j.open = false;
        return false;
    }
    j.change_count = 0;
    j.open = true;
    return true;
}

// Append one redo record (UPDATE or DELETE) for the change just buffered.
// Idempotent on replay: "set recno's field to this value" / "mark deleted".
bool journal_note_change(int area0, const ChangeEntry& entry) {
    if (!is_persistent_enabled(area0)) return true;

    auto& j = state_store()[area0].journal;
    if (!j.fp) {
        // Buffer-on was not seen (or the handle was lost) -- open lazily.
        if (!journal_note_buffer_on(area0, std::string{})) return false;
    }

    // Full-fidelity retained-edit record. Each buffered write is one line, so the
    // multiple-retained-edits-per-field capability is preserved in the log:
    //   U <recno> <priority> <H|S> <field>:<hex> [<field>:<hex> ...]
    //   D <recno> <priority>
    // <priority> is the buffer's per-write priority; the H/S flag says whether the
    // edit is kept as history (H) or folded last-write-wins (S), so replay/audit
    // can reconstruct the retained edits, not just the final value.
    const char mode = is_history_enabled(area0) ? 'H' : 'S';
    std::string line;
    if (entry.dirty_flags & CHANGE_DELETE) {
        line = "D " + std::to_string(entry.recno)
             + " " + std::to_string(entry.priority) + "\n";
    } else {
        line = "U " + std::to_string(entry.recno)
             + " " + std::to_string(entry.priority)
             + " " + std::string(1, mode);
        for (const auto& kv : entry.new_values) {
            line += ' ';
            line += std::to_string(kv.first);
            line += ':';
            wal_append_hex(line, kv.second);
        }
        line += '\n';
    }
    if (std::fwrite(line.data(), 1, line.size(), j.fp) != line.size()) return false;
    ++j.change_count;
    // Durability is deferred to journal_begin_commit's single fsync.
    return true;
}

// Write-ahead: durably commit the redo log BEFORE the DBF apply. Appends the
// COMMIT marker and fsyncs. False -> caller must abort the commit.
bool journal_begin_commit(int area0) {
    if (!is_persistent_enabled(area0)) return true;

    auto& j = state_store()[area0].journal;
    if (!j.fp) return true;   // nothing was logged (e.g. empty transaction)

    const std::string marker = "C " + std::to_string(j.change_count) + "\n";
    if (std::fwrite(marker.data(), 1, marker.size(), j.fp) != marker.size()) return false;
    return wal_durable_sync(j.fp);
}

// Finalize a successful commit: the redo is now applied to the DBF, so close and
// delete the log. A crash before this leaves a committed log that recovery
// replays; a crash after leaves the DBF as the source of truth.
bool journal_note_commit(int area0) {
    if (!is_persistent_enabled(area0)) return true;

    auto& j = state_store()[area0].journal;
    if (j.fp) { std::fclose(j.fp); j.fp = nullptr; }
    if (!j.path.empty()) std::remove(j.path.c_str());
    clear_journal_state(area0);
    return true;
}

// Discard an uncommitted transaction: no COMMIT marker was written, so recovery
// would discard the log anyway; delete it now.
bool journal_note_rollback(int area0) {
    if (!is_persistent_enabled(area0)) return true;

    auto& j = state_store()[area0].journal;
    if (j.fp) {
        std::fputs("R\n", j.fp);   // best-effort marker; file is removed next
        std::fclose(j.fp);
        j.fp = nullptr;
    }
    if (!j.path.empty()) std::remove(j.path.c_str());
    clear_journal_state(area0);
    return true;
}

// Crash recovery: replay a committed <dbf>.tbj on open, else discard it.
bool recover_table_buffer_journal(xbase::DbArea& area) {
    if (!area.isOpen()) return false;
    const std::string path = area.filename() + ".tbj";

    std::FILE* fp = std::fopen(path.c_str(), "rb");
    if (!fp) return false;                       // no log -> nothing to recover

    // Read the whole log into lines (stripping CR/LF).
    std::vector<std::string> lines;
    {
        std::string cur;
        int ch;
        while ((ch = std::fgetc(fp)) != EOF) {
            if (ch == '\n') { lines.push_back(cur); cur.clear(); }
            else if (ch != '\r') cur.push_back(static_cast<char>(ch));
        }
        if (!cur.empty()) lines.push_back(cur);
    }
    std::fclose(fp);

    // Committed iff a "C" marker line is present.
    bool committed = false;
    for (const auto& ln : lines) {
        if (!ln.empty() && ln[0] == 'C' && (ln.size() == 1 || ln[1] == ' ')) {
            committed = true;
            break;
        }
    }

    if (!committed) {
        std::remove(path.c_str());               // uncommitted -> discard; DBF untouched
        return false;
    }

    // Replay U/D redo records in append order. Append order == priority order, so
    // the last write per field wins == highest priority (matches COMMIT's fold).
    for (const auto& ln : lines) {
        if (ln.empty()) continue;
        if (ln[0] == 'U') {
            std::istringstream is(ln);
            std::string tag, prio, mode;
            std::uint64_t recno = 0;
            is >> tag >> recno >> prio >> mode;  // "U" <recno> <priority> <H|S>
            if (recno == 0 || recno > area.recCount64()) continue;
            if (!area.gotoRec64(recno) || !area.readCurrent()) continue;

            std::string pair;
            bool wrote = false;
            while (is >> pair) {
                const auto colon = pair.find(':');
                if (colon == std::string::npos) continue;
                int field = 0;
                std::istringstream(pair.substr(0, colon)) >> field;
                std::string val;
                if (field > 0 && wal_hex_decode(pair.substr(colon + 1), val)) {
                    if (area.set(field, val)) wrote = true;
                }
            }
            if (wrote) (void)area.writeCurrent();
        } else if (ln[0] == 'D') {
            std::istringstream is(ln);
            std::string tag;
            std::uint64_t recno = 0;
            is >> tag >> recno;                  // "D" <recno>
            if (recno == 0 || recno > area.recCount64()) continue;
            if (area.gotoRec64(recno) && area.readCurrent()) (void)area.deleteCurrent();
        }
        // TBJ1 header, C, R lines: ignored.
    }

    // writeCurrent already flushed the DBF's fstream to the OS. A hardened DBF
    // fsync before removing the log is a follow-up (std::fstream does not expose
    // the OS handle portably). Remove the replayed log.
    std::remove(path.c_str());
    return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// History Mode Control
// ─────────────────────────────────────────────────────────────────────────────

bool is_history_enabled(int area0) {
    return in_range(area0) && state_store()[area0].tb.history_enabled;
}

void set_history_enabled(int area0, bool value) {
    if (!in_range(area0)) return;
    state_store()[area0].tb.history_enabled = value;
}

// ─────────────────────────────────────────────────────────────────────────────
// Table Buffer Access
// ─────────────────────────────────────────────────────────────────────────────

TableBuffer& get_tb(int area0) {
    if (!in_range(area0)) throw std::out_of_range("Invalid area index");
    return state_store()[area0].tb;
}

const TableBuffer& get_tb_const(int area0) {
    if (!in_range(area0)) throw std::out_of_range("Invalid area index");
    return state_store()[area0].tb;
}

// ─────────────────────────────────────────────────────────────────────────────
// TableBuffer Implementation
// ─────────────────────────────────────────────────────────────────────────────

int TableBuffer::add_change(std::uint64_t recno, std::uint64_t flags,
                            const std::uint64_t* source_field_bits,
                            int field1, const std::string& new_value) {
    if (changes.size() >= kMaxChanges) {
        std::cout << "Warning: TableBuffer max changes reached (" << kMaxChanges << ").";
        return 0;
    }

    auto next_prio = [&]() -> int {
        // Priority 0 is reserved ("null"/unset). We keep 1..255 and wrap.
        if (next_priority <= 0) next_priority = 1;
        const int p = next_priority;
        ++next_priority;
        if (next_priority > 255) next_priority = 1;
        return p;
    };

    // Non-history mode: keep exactly ONE merged snapshot per recno.
    if (!history_enabled) {
        auto range = changes.equal_range(recno);

        if (range.first == range.second) {
            ChangeEntry entry;
            entry.recno       = recno;
            entry.dirty_flags = flags;
            entry.priority    = 1;

            if (source_field_bits) {
                std::memcpy(entry.field_bits, source_field_bits, sizeof(entry.field_bits));
            }

            if (field1 > 0) {
                entry.new_values[field1] = new_value;
            }

            changes.emplace(recno, std::move(entry));
            return 1;   // non-history entries always carry priority 1
        }

        // If legacy state has multiple entries, pick newest and fold others into it.
        auto newest = range.first;
        for (auto it = std::next(range.first); it != range.second; ++it) {
            if (it->second.priority > newest->second.priority) newest = it;
        }

        newest->second.dirty_flags |= flags;

        if (source_field_bits) {
            for (int i = 0; i < kWords; ++i) {
                newest->second.field_bits[i] |= source_field_bits[i];
            }
        }

        if (field1 > 0) {
            newest->second.new_values[field1] = new_value;
        }

        for (auto it = range.first; it != range.second; ) {
            if (it == newest) { ++it; continue; }

            newest->second.dirty_flags |= it->second.dirty_flags;
            for (int i = 0; i < kWords; ++i) {
                newest->second.field_bits[i] |= it->second.field_bits[i];
            }
            for (const auto& kv : it->second.new_values) {
                newest->second.new_values[kv.first] = kv.second;
            }

            it = changes.erase(it);
        }

        newest->second.priority = 1;
        return 1;
    }

    // History mode: append an entry per write; reads pick highest priority per field.
    ChangeEntry entry;
    entry.recno       = recno;
    entry.dirty_flags = flags;
    entry.priority    = next_prio();

    if (source_field_bits) {
        std::memcpy(entry.field_bits, source_field_bits, sizeof(entry.field_bits));
    }

    if (field1 > 0) {
        entry.new_values[field1] = new_value;
    }

    const int assigned = entry.priority;   // capture before the move
    changes.emplace(recno, std::move(entry));
    return assigned;                        // history: the per-write priority
}


void test_add_change(int area0, std::uint64_t recno, std::uint64_t flags,
                     int field1, const std::string& new_value) {
    if (!in_range(area0)) {
        std::cout << "Invalid area index.\n";
        return;
    }

    auto& tb = get_tb(area0);

    std::uint64_t* field_ptr = nullptr;
    std::uint64_t temp_bits[kWords]{};

    if (field1 > 0 && field1 <= kMaxFields) {
        const int idx0 = field1 - 1;
        const int word = idx0 / 64;
        const int bit  = idx0 % 64;
        temp_bits[word] = (std::uint64_t{1} << bit);
        field_ptr = temp_bits;
    }

    std::cout << "test_add_change: area=" << area0
              << " recno=" << recno
              << " field=" << field1
              << " value=\"" << new_value << "\"\n";

    tb.add_change(recno, flags, field_ptr, field1, new_value);

    std::cout << " → Change added (history " << (tb.history_enabled ? "ON" : "OFF") << ")\n";
}

} // namespace dottalk::table
