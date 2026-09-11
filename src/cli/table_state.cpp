// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "cli/table_state.hpp"

#include <array>
#include <cctype>
#include <cstring>
#include <stdexcept>
#include <iostream>
#include <iomanip>   // for std::setw, std::hex
#include <sstream>

#include "xbase.hpp"
#include "xbase/durable.hpp"   // AIF-161: durable_sync before the log dies
#include "common/path_state.hpp"  // AIF-160: the SYS slot, and what it exempts

#include <filesystem>
#include <vector>

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

// ---------------------------------------------------------------------------
// ENGINE STATE IS WRITTEN DIRECTLY, AND THAT IS ENFORCED RATHER THAN ASSUMED.
//
// The SYS slot holds engine-owned tables that cannot be rebuilt from anything --
// the multi-area commit group log first among them. Two things must be true of
// every table under it, and BOTH are structural rather than conventional:
//
//   1. IT IS NEVER TABLE-BUFFERED. A buffered write goes through the WAL, so a
//      SYS table could acquire a `.tbj`.
//   2. IT IS NEVER RECOVERED. Which is the reason for (1): recovering a `P`
//      span requires asking the group log whether its group committed, and if
//      the group log itself could carry a journal, recovering it would require
//      asking the file being recovered. That is not a deadlock -- it is a table
//      opening itself -- and it has to be made IMPOSSIBLE rather than avoided.
//
// `writeCurrent()` is the direct path and does not re-enter TABLE BUFFER, which
// is why there is no bootstrap problem today. THAT IS A PROPERTY OF THE CURRENT
// CODE, NOT A GUARANTEE. A convention that is only documented is one refactor
// away from being untrue, and this tree has a folder of findings about exactly
// that gap. So the rule is a predicate, and the predicate is called.
//
// IT IS A RULE ABOUT LOCATION, NOT A REGISTRY OF PATHS. A list of exempt files
// has to be populated by somebody at startup, and a guard that depends on
// registration is off whenever registration is missed -- "a gate that does not
// read a file can still depend on it". Being UNDER SYS is intrinsic: a table
// cannot be moved there by accident and cannot forget to register.
bool is_engine_state_file(const std::string& file_path) {
    namespace fs = std::filesystem;
    if (file_path.empty()) return false;

    fs::path sys_root;
    try { sys_root = dottalk::paths::get_slot(dottalk::paths::Slot::SYS); }
    catch (...) { return false; }
    if (sys_root.empty()) return false;

    std::error_code ec;
    fs::path file = fs::weakly_canonical(fs::path(file_path), ec);
    if (ec) { ec.clear(); file = fs::path(file_path).lexically_normal(); }
    fs::path root = fs::weakly_canonical(sys_root, ec);
    if (ec) { ec.clear(); root = sys_root.lexically_normal(); }

    // COMPONENT-WISE, never a string prefix: "<data>/system" must not match
    // "<data>/sys". And case-folded, because these are Windows paths and a
    // case-only difference is not a different directory.
    auto parts = [](const fs::path& p) {
        std::vector<std::string> out;
        for (const auto& c : p) {
            std::string t = c.string();
            if (t.empty()) continue;
            for (auto& ch : t) ch = static_cast<char>(
                std::tolower(static_cast<unsigned char>(ch)));
            out.push_back(t);
        }
        return out;
    };

    const std::vector<std::string> f = parts(file);
    const std::vector<std::string> r = parts(root);
    if (r.empty() || f.size() < r.size()) return false;
    for (std::size_t i = 0; i < r.size(); ++i) {
        if (f[i] != r[i]) return false;
    }
    return true;
}

// ---------------------------------------------------------------------------
// THE JOURNAL FORMAT VERSION, AND THE READER THAT NEVER LOOKED AT IT
//
// journal_note_buffer_on has written a "TBJ1 <table>" header since this WAL
// shipped, and until 2026-09-11 NOTHING EVER READ IT. recover_table_buffer_
// journal scanned for a line starting with 'C', replayed 'I'/'U'/'D', and
// skipped every other line without comment -- its own closing note said so:
// "TBJ1 header, C, R lines: ignored." There was no default branch, so an
// unrecognised record was not an error and not a refusal. It was silence.
//
// THE HALF THAT WAS NEVER AT RISK is the one both format designs wrote down:
// "TBJ2 still accepts TBJ1". Nothing here could ever have REJECTED a TBJ1 log,
// because nothing here read a version.
//
// THE HALF THAT IS AT RISK is the reverse, and it splits in two:
//
//   The PREPARE marker would be safe BY ACCIDENT. A prepared-but-undecided
//   span carries 'P' and no 'C'; an old reader finds no 'C', calls it
//   uncommitted and discards. That is presumed abort -- the right answer,
//   reached for the wrong reason, and only while no future marker is spelled
//   with a leading 'C'.
//
//   The MEMO record would NOT be. A committed TBJ2 log carries 'M' memo
//   payloads, 'U' record writes and a 'C'. An old reader honours the 'C',
//   replays every 'U', and drops every 'M' -- so the recovered rows reference
//   memo object ids the memo store was never told to write. The table opens
//   clean and the damage is one field deep. Worse than a refusal and worse
//   than a discard.
//
// SO THIS GATE SHIPS BEFORE THE BUMP, NOT WITH IT. A version bump is only a
// compatibility rule if something enforces it, and adding the check after TBJ2
// exists means the fleet already holds binaries that half-replay in silence.
// This build still WRITES TBJ1 -- kJournalVersionWritten is unmoved -- because
// a header claiming a version whose records do not exist would strand older
// builds for nothing.
//
// REFUSE AND PRESERVE, never refuse and delete. A log this build cannot read
// may be a committed transaction a NEWER build can still replay; removing it
// converts "unreadable here" into "gone". The cost is a repeated warning until
// someone acts, which is the correct direction for a durability instrument.
constexpr int kJournalVersionWritten = 1;
constexpr int kJournalVersionMaxRead = 1;

// "TBJ<digits>", followed by a space or end of line. Returns 0 when the line is
// not a header this family wrote -- deliberately strict, because the whole
// point is to stop guessing at bytes whose meaning is unknown.
static int journal_header_version(const std::string& line) {
    if (line.rfind("TBJ", 0) != 0) return 0;
    std::size_t i = 3;
    if (i >= line.size() || line[i] < '0' || line[i] > '9') return 0;
    int v = 0;
    while (i < line.size() && line[i] >= '0' && line[i] <= '9') {
        v = v * 10 + (line[i] - '0');
        if (v > 9999) return 0;          // a runaway number, not a version
        ++i;
    }
    if (i < line.size() && line[i] != ' ') return 0;
    return v;
}

// ---------------------------------------------------------------------------
// THE RECORD TAG, AND THE SILENCE UNDER THE VERSION GATE
//
// The gate above compares ONE NUMBER. It stops a log whose header names a
// version this build cannot read, and that is the whole of what it can do. It
// says nothing about a record this build does not understand inside a version
// it DOES read -- which is exactly what every future format bump produces for
// every build older than it.
//
// AND THE REPLAY LOOP DID NOT MERELY IGNORE SUCH A RECORD. It matched on ONE
// BYTE: `ln[0] == 'I' || ln[0] == 'U'`, with no check that the byte was the
// whole tag. A future record spelled `UPDATE_META ...` or `INDEX ...` is
// therefore not dropped -- it is READ AS A WRITE. istringstream takes the token
// as the tag, the next integer as a recno, and any `<n>:<hex>` pair that
// follows as a field to set. That is worse than the silence the note above
// describes, and it was one byte away from the `C` test three lines below it,
// which had spelled the delimiter rule by hand since it shipped.
//
// A tag is a TOKEN, delimited by a space or end of line. 'C' and 'CX' are
// different records, and a reader matching one character cannot tell them
// apart.
static std::string journal_record_tag(const std::string& line) {
    const auto end = line.find(' ');
    return (end == std::string::npos) ? line : line.substr(0, end);
}

// EVERY RECORD A TBJ1 LOG CAN CONTAIN, and nothing else.
//
//   I  insert redo     U  update redo     D  delete redo
//   C  commit marker   R  rollback marker
//
// The header is deliberately NOT in this set. It is line one, already read and
// accepted by the version gate, and admitting "TBJ1" as a record would let a
// second header appear mid-log without complaint.
static bool journal_record_is_known(const std::string& tag) {
    return tag == "I" || tag == "U" || tag == "D" || tag == "C" || tag == "R";
}

// A tag from a log we are refusing has not been validated by anything, so it
// reaches the console as bytes of unknown provenance. Bound it and strip what
// a terminal would interpret.
static std::string journal_tag_for_display(const std::string& tag) {
    std::string out;
    for (std::size_t i = 0; i < tag.size() && i < 16; ++i) {
        const unsigned char c = static_cast<unsigned char>(tag[i]);
        out.push_back((c >= 0x20 && c < 0x7F) ? static_cast<char>(c) : '?');
    }
    if (tag.size() > 16) out += "...";
    return out;
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

    // The version we write is kJournalVersionWritten and NOT a literal. It was a
    // literal "TBJ1 " until 2026-09-11, three hundred lines from the reader that
    // was supposed to agree with it and never looked -- which is the same
    // two-declarations-of-one-fact shape the version-coherence gate exists to
    // stop one layer up, in a file that gate does not scan.
    const std::string hdr =
        "TBJ" + std::to_string(kJournalVersionWritten) + " "
        + (table_name.empty() ? j.path : table_name) + "\n";
    if (std::fwrite(hdr.data(), 1, hdr.size(), j.fp) != hdr.size()) {
        std::fclose(j.fp); j.fp = nullptr; j.open = false;
        return false;
    }
    j.change_count = 0;
    j.open = true;
    return true;
}

// Append one redo record (INSERT, UPDATE, or DELETE) for the change just
// buffered. Idempotent on replay: insert reserves its final recno while a table
// lock is held, then replay either appends that record or finishes its fields.
bool journal_note_change(int area0, const ChangeEntry& entry) {
    if (!is_persistent_enabled(area0)) return true;

    auto& j = state_store()[area0].journal;
    if (!j.fp) {
        // Buffer-on was not seen (or the handle was lost) -- open lazily.
        if (!journal_note_buffer_on(area0, std::string{})) return false;
    }

    // Full-fidelity retained-edit record. Each buffered write is one line, so the
    // multiple-retained-edits-per-field capability is preserved in the log:
    //   I <recno> <priority> <H|S> <field>:<hex> [<field>:<hex> ...]
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
        const char tag = (entry.dirty_flags & CHANGE_INSERT) ? 'I' : 'U';
        line = std::string(1, tag) + " " + std::to_string(entry.recno)
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

    // SYS IS NEVER RECOVERED -- see is_engine_state_file above. This returns
    // BEFORE the log is even looked for, so a stray .tbj under SYS is neither
    // replayed nor deleted: an engine-state table that somehow acquired a
    // journal is a bug to be found, not a file to be quietly consumed.
    if (is_engine_state_file(area.filename())) return false;

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

    // AN EMPTY LOG IS NOT A VERSION PROBLEM. fopen(path, "wb") creates the file
    // and the header is written immediately after, so a zero-byte .tbj is a
    // transaction that died in that gap -- nothing was logged, nothing can be
    // replayed. Discard it exactly as before. Routing it through the refusal
    // below would leave an empty file warning on every USE forever, which is a
    // regression this gate would otherwise introduce and this branch removes.
    if (lines.empty()) {
        std::remove(path.c_str());
        return false;
    }

    // THE VERSION GATE. See the note above kJournalVersionWritten.
    const int version = journal_header_version(lines.front());
    if (version <= 0 || version > kJournalVersionMaxRead) {
        std::string why;
        if (version <= 0) {
            why = "  its first line is not a TBJ journal header, so this build cannot tell\n"
                  "  what the rest of the file means.\n";
        } else {
            why = "  it is TBJ" + std::to_string(version) + " and this build reads TBJ"
                + std::to_string(kJournalVersionMaxRead) + " and older.\n";
        }
        std::cout << "RECOVER: REFUSED -- " << path << "\n"
                  << why
                  << "  THE LOG IS KEPT, NOT DISCARDED, and nothing was replayed. A log this\n"
                     "  build cannot read may still be a committed transaction that a newer\n"
                     "  build can replay; deleting it would turn 'unreadable here' into\n"
                     "  'gone'. This table is open and usable; the journal is not applied.\n";
        return false;
    }

    // Committed iff a "C" marker record is present. The delimiter rule used to
    // be spelled out here by hand -- ln[0] == 'C' and (size == 1 or ln[1] == ' ')
    // -- which was correct, and was the ONLY place in this reader that knew a
    // tag is a token. journal_record_tag now holds that rule once.
    bool committed = false;
    for (const auto& ln : lines) {
        if (!ln.empty() && journal_record_tag(ln) == "C") {
            committed = true;
            break;
        }
    }

    if (!committed) {
        std::remove(path.c_str());               // uncommitted -> discard; DBF untouched
        return false;
    }

    // THE WHOLE LOG IS READ BEFORE THE FIRST WRITE.
    //
    // Discovering an unreadable record halfway through a replay would leave the
    // table HALF APPLIED and the log then refused -- strictly worse than either
    // outcome alone, and unrecoverable by repeating, because the next USE sees
    // the same refusal over a table that has already moved. Count first, read
    // verdicts second.
    //
    // THE RECORD THAT IS NOT SAFE BY ACCIDENT is why this is worth a pass. A
    // TBJ2 PREPARE marker degrades correctly against an old reader: no 'C', so
    // no replay. AIF-061's memo record does not. A committed TBJ2 log carries
    // 'M' payloads, 'U' writes and a 'C'; a reader that honours the 'C',
    // replays the 'U's and drops the 'M's produces rows pointing at memo
    // objects the memo store was never told to write. The table opens clean and
    // the damage is one field deep.
    //
    // COMMITTED LOGS ONLY, AND THAT PLACEMENT IS LOAD-BEARING. An uncommitted
    // log is discarded above without a record being read, and it carries NO
    // durability guarantee: this WAL performs exactly one fsync, in
    // journal_begin_commit, AFTER the C marker is appended. So every byte
    // preceding a durable 'C' is complete, and a torn tail can exist only in a
    // log that has no 'C' -- one already on the discard path. Validating those
    // would turn every interrupted transaction into a permanent warning about a
    // file that is correctly deletable.
    {
        bool        unknown_found = false;
        std::string unknown_tag;
        for (std::size_t i = 1; i < lines.size(); ++i) {
            if (lines[i].empty()) continue;    // a blank line is not a record
            const std::string tag = journal_record_tag(lines[i]);
            if (!journal_record_is_known(tag)) {
                unknown_found = true;
                unknown_tag   = tag;
                break;
            }
        }
        if (unknown_found) {
            std::cout
                << "RECOVER: REFUSED -- " << path << "\n"
                << "  it is TBJ" << version << ", which this build reads, but it carries"
                   " a record\n"
                << "  this build does not know: '" << journal_tag_for_display(unknown_tag)
                << "'.\n"
                << "  THE LOG IS KEPT, NOT DISCARDED, and NOTHING was replayed -- not"
                   " even the\n"
                   "  records this build does understand. A log half applied and then\n"
                   "  refused is worse than either half. This table is open and usable;\n"
                   "  the journal is not applied.\n";
            return false;
        }
    }

    // Replay I/U/D redo records in append order. Append order == priority order, so
    // the last write per field wins == highest priority (matches COMMIT's fold).
    for (const auto& ln : lines) {
        if (ln.empty()) continue;
        const std::string rec_tag = journal_record_tag(ln);
        if (rec_tag == "I" || rec_tag == "U") {
            std::istringstream is(ln);
            std::string tag, prio, mode;
            std::uint64_t recno = 0;
            is >> tag >> recno >> prio >> mode;  // "I|U" <recno> <priority> <H|S>
            if (recno == 0) continue;
            if (tag == "I" && recno == area.recCount64() + 1) {
                if (!area.appendBlank() || !area.readCurrent()) continue;
            } else {
                if (recno > area.recCount64()) continue;
                if (!area.gotoRec64(recno) || !area.readCurrent()) continue;
            }

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
        } else if (rec_tag == "D") {
            std::istringstream is(ln);
            std::string tag;
            std::uint64_t recno = 0;
            is >> tag >> recno;                  // "D" <recno>
            if (recno == 0 || recno > area.recCount64()) continue;
            if (area.gotoRec64(recno) && area.readCurrent()) (void)area.deleteCurrent();
        }
        // Header, C, R lines: ignored HERE -- the header was already read
        // and accepted by the version gate above, which is what makes
        // ignoring the remaining lines safe rather than merely quiet.
    }

    // THE REPLAYED ROWS ARE IN THE PAGE CACHE, NOT ON THE PLATTER.
    //
    // writeCurrent() ends in io().flush(), which reaches the OS and no further.
    // Removing the log here used to leave a second power cut with neither the
    // rows nor the log -- and this is the CRASH PATH, so a machine that already
    // failed once is exactly where that matters. Idempotent replay is the
    // property that makes recovery safe, and deleting the log before the replay
    // is durable throws it away at the moment it is most needed.
    //
    // THIS COMMENT USED TO DEFER THE FIX because std::fstream does not expose
    // the OS handle portably. True at AIF-023 (2026-07-19); not binding since
    // 2026-08-31, because xbase::durable_sync opens a SECOND HANDLE BY PATH and
    // never asks the fstream for anything. AIF-161 is about how that sentence
    // survived eleven days after it stopped mattering.
    //
    // ON FAILURE, KEEP THE LOG: replay is idempotent, so the cost is one repeat
    // at the next USE. Reported loudly, because a table that will not sync is a
    // fact the operator needs, and std::cout matches the shipped durable_sync
    // warnings in cmd_workspace.cpp.
    {
        std::string sync_err;
        if (!xbase::durable_sync(area.filename(), &sync_err)) {
            std::cout << "RECOVER: warning -- journal replayed but the table was"
                         " not synced to durable media (" << sync_err << "); the"
                         " journal is KEPT and replays again at the next USE\n";
            return true;   // replayed; log deliberately retained
        }
    }

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
    // In snapshot mode, a second field for an already-buffered record merges
    // into that record and consumes no capacity. Test capacity only when this
    // call would create a new entry; otherwise the final record at the limit
    // could accept its first field and incorrectly reject all remaining fields.
    const bool existing_snapshot = !history_enabled && changes.find(recno) != changes.end();
    if (!existing_snapshot && changes.size() >= kMaxChanges) {
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
