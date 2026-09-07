// @dottalk.file v1
// subsystem: include
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// File: include/xbase.hpp
// Purpose: Core xBase engine types, constants, and DbArea/XBaseEngine contracts.
// Boundary: This header defines engine-facing runtime state only. CLI, shell,
//           messaging, and help-surface policy must stay outside this layer.
// Notes: Supports mixed runtime flavors plus the memo/index hooks needed by
//        higher layers without exposing CLI behavior here.

#pragma once
#include <functional>
#include <cstdint>
#include <string>
#include <vector>
#include <array>
#include <fstream>
#include <sstream>
#include <memory>
#include <stdexcept>
#include <optional>
#include <limits>
#include <utility>

// AIF-091 M1. THE ONE PLACE that answers "which bit belongs to which field"
// in the VFP `_NullFlags` column. Header-only, no dependency on this file.
#include "xbase/vfp_null_bits.hpp"
#include "memo/memo_context.hpp"
#include "dottalk/build_vectors.hpp"   // AIF-044 generated build-vector authority

namespace dottalk::memo { class MemoManager; }

namespace xbase {

// ---- Constants (derived from the generated build-vector authority; AIF-044) --
// Values now flow from dottalk::build (config/build_vectors.cmake -> configure_file).
// GATE #1: defaults preserve prior compiled behavior (areas 512, fields 256, index 5,
// record 16 MiB / advisory 64 KiB). Aliases keep every existing xbase:: name working.
constexpr int           MAX_FIELDS = static_cast<int>(dottalk::build::max_fields);             // was 256
constexpr int           MAX_INDEX  = static_cast<int>(dottalk::build::legacy_max_index_slots); // was 5
constexpr int           MAX_AREA   = static_cast<int>(dottalk::build::max_areas);              // was 512

// AIF-078 -- THE AREA'S SESSION HANDLE (steward, 2026-08-23: "i accept your
// recommendation").
//
// Workspaces got a monotonic never-reused handle; areas did not, and the gap
// showed. AreaId in the GUI had TWO spellings in one type: session.cpp minted a
// counter of its own, while another path derived it as engine slot + 1. Two
// spellings of one identity is the defect R5 of the identity ladder names, and
// it is why gui_workspace_of_area() could not be written honestly -- its
// parameter had no single meaning, so no correct body existed.
//
// A COMPOSITE OF (workspace, slot) WOULD NOT HAVE FIXED IT. Both parts are
// POSITIONS and both are reused -- workspace::join() deliberately reuses the
// lowest free local slot, and its own comment says renumbering is not an option
// "because a local slot is an address". Composing two addresses yields a
// two-dimensional address, not a name; and it would change if an area ever
// moved between workspaces, while an identity that changes when the thing has
// not is not an identity.
//
// So the area gets the same rung the workspace has: minted at open(), MONOTONIC
// within the session, NEVER REUSED after close, and 0 meaning "not open". Never
// reused for the reason the workspace handle is not: a stale id held by a view
// must resolve to GONE and never to somebody else.
//
// NOT PERSISTED. This is the SESSION rung. The durable rung for an area is its
// path (later a catalog id), and the positional rung stays the engine and local
// slots -- derivation runs downward only (ladder R1).
//
// AMENDMENT, same day, after the GUI side landed. The paragraph above says this
// is why gui_workspace_of_area() could not be written honestly, and implies
// that unifying AreaId would make it writable. THE SECOND HALF WAS WRONG, and
// the record is worth more than the tidy version. AreaId did become a real
// identity, and the function still could not be written -- because the GUI's
// areas are owned by its session and not by this engine's area array, so no
// registry maps a handle back to an area. Its one caller had the DbArea a frame
// earlier, so the stub was deleted instead of built. A correct diagnosis of a
// defect is not automatically a correct prediction of the fix.
//
// The GUI's positional rung is NOT the engine slot, for a related reason:
// setEngineSlot() is called only from dbf_file.cpp over this engine's own
// _areas array, so a session-owned DbArea keeps _engine_slot == -1 for life.
// The GUI's positional rung is the index in its own area list.
inline std::uint64_t next_area_handle() noexcept {
    static std::uint64_t next = 0;
    return ++next;
}
// Record-size guardrails (fixed record = sum of field widths). Hard ceiling catches
// corrupt/absurd 64-bit record lengths; soft advisory nudges wide rows toward memo.
constexpr std::uint64_t X64_MAX_RECORD_SIZE      = dottalk::build::x64::max_record_bytes;       // was 16 MiB
constexpr std::uint64_t X64_RECORD_SIZE_ADVISORY = dottalk::build::x64::record_advisory_bytes;  // was 64 KiB
constexpr char        IS_DELETED         = '*';
constexpr char        NOT_DELETED        = ' ';
constexpr uint8_t     HEADER_TERM_BYTE   = 0x0D;

// ---- Runtime Area Kind / Capability ---------------------------------------
enum class AreaKind : uint8_t {
    Unknown = 0,
    V32,
    V64,
    V128,
    Tup
};

enum class AreaCapability : uint64_t {
    None        = 0,
    ReadRows    = 1ull << 0,
    WriteRows   = 1ull << 1,
    DeleteRows  = 1ull << 2,
    Seek        = 1ull << 3,
    Filter      = 1ull << 4,
    Order       = 1ull << 5,
    Relations   = 1ull << 6,
    Memo        = 1ull << 7,
    TupleOps    = 1ull << 8
};

// Centralized version-byte -> runtime kind mapping.
inline AreaKind detect_area_kind_from_version(std::uint8_t ver) noexcept
{
    switch (ver) {
        case 0x03: // ClassicNoMemo
        case 0x83: // ClassicWithMemo
        case 0xF5: // Fox26Memo
            return AreaKind::V32;

        case 0x30: // VfpBase
        case 0x31: // VfpAutoInc
        case 0x32: // VfpVar
        case 0x64: // xbase_64 dialect
            return AreaKind::V64;

        default:
            return AreaKind::Unknown;
    }
}

// ---- Memo field storage contract ------------------------------------------
constexpr std::uint8_t LEGACY_MEMO_FIELD_LEN = 10; // pre-x64: plain fixed-width text slot
constexpr std::uint8_t X64_MEMO_FIELD_LEN    = 8;  // x64: uint64 object-id slot

// ---- On-disk structures (packed) ------------------------------------------
#pragma pack(push, 1)
struct HeaderRec {
    uint8_t   version;
    uint8_t   last_updated[3];
    int32_t   num_of_recs;
    int16_t   data_start;
    int16_t   cpr;              // characters per record (record length)
    uint8_t   reserved[20];
};

struct FieldRec {
    char      field_name[11];
    char      field_type;
    uint32_t  field_data_address; // present in some variants
    uint8_t   field_length;
    uint8_t   decimal_places;
    uint8_t   reserved[14];
};
#pragma pack(pop)

// ---- In-memory field metadata ---------------------------------------------
struct FieldDef {
    std::string name;
    char        type{};       // 'C','N','D','L', etc.
    uint32_t    length{};     // total bytes (runtime truth; X64 may exceed legacy descriptor byte)
    uint8_t     decimals{};   // for 'N'

    // X64FieldMetaEntry.flags, carried through from the x64 metadata block.
    //
    // THE HEADER IS SELF-DESCRIBING AND THIS IS WHERE THE KEY DESIGNATION LIVES
    // (AIF-156). The x64 header already carries the table's logical name, its
    // field names and the authoritative field lengths; a table that describes
    // its own schema describes its own key too. Before this, the PRIMARY
    // designation lived in a process-local std::unordered_map in
    // unique_registry.cpp -- whose own boundary comment called it "not
    // persistent schema metadata" -- so the key was forgotten at exit and a
    // REPLACE in a fresh session overwrote it in silence.
    //
    // These 16 bits were written as a hardcoded zero by the metadata builder
    // and READ BY NOBODY from the day the format was defined. Non-x64 tables
    // and x64 tables with no metadata block leave this at 0, which reads as
    // "no designation" -- the same answer they gave before.
    uint16_t    x64_flags{};
};

// ------------------------------------------------------------------------
// Per-field metadata carried by the VFP/x64 field descriptor's flags byte
// (byte 18) but NOT baked into FieldDef. Lives here rather than in
// xbase_vfp.hpp because DbArea holds it as state and xbase_vfp.hpp includes
// this header, not the other way round.
//
// The flags byte is decoded in exactly one place, xbase::decode_field_flags().
// Note that autoincrement (0x0C) CARRIES the binary bit (0x04), so `binary`
// here is already corrected for that -- do not re-derive it from raw flags.
// ------------------------------------------------------------------------
struct VfpFieldExtras {
    bool        nullable      {false};
    bool        binary        {false};
    // Flag 0x01. The `_NullFlags` column is a SYSTEM field and must be kept out
    // of the user field vector; nothing decoded this before AIF-091 M1.
    bool        system        {false};
    bool        autoincrement {false};
    uint32_t    next_autoinc  {0};
    uint8_t     step_autoinc  {0};
    std::string long_name     {};
};

// ------------------------------------------------------------------------
// Where the hidden `_NullFlags` column lives in a record, once it has been
// partitioned out of the visible field vector.
//
// `present` false means this table has no null bitmap -- which today is every
// table this engine has ever written. `offset` is the byte offset within the
// record buffer (record byte 0 is the deleted flag, so a real offset is >= 1).
// ------------------------------------------------------------------------
struct NullFlagsColumn {
    bool        present {false};
    std::size_t offset  {0};      // byte offset within the record buffer
    std::size_t length  {0};      // width of the bitmap in bytes
    std::string name    {};       // as the descriptor spelled it
};

namespace {
    static inline void clear() {
    #ifdef _WIN32
        std::system("cls");
    #else
        std::fputs("\x1b[2J\x1b[H", stdout);
        std::fflush(stdout);
    #endif
    }
}

// ---- DbArea ---------------------------------------------------------------
class DbArea {
public:
    enum class MemoKind { NONE, FPT, DBT };

    // ---- Lifecycle --------------------------------------------------------
    DbArea();
    ~DbArea();

    DbArea(const DbArea&)            = delete;
    DbArea& operator=(const DbArea&) = delete;

    DbArea(DbArea&&);
    DbArea& operator=(DbArea&&);

    // ---- Open / Close -----------------------------------------------------
    void open(const std::string& abs_filename);
    void close();

    // ---- State ------------------------------------------------------------
    bool isOpen() const noexcept { return _in_memory ? (_ram != nullptr) : _fp.is_open(); }

    // In-memory tables (AIF-043): record I/O routes through io(). While _in_memory is
    // false (every disk table) io() == _fp, so behavior is unchanged. DbArea::open
    // flips _in_memory and binds _ram to a ramfs byte store when the path resolves
    // under a mounted virtual root (V2).
    std::iostream& io() noexcept {
        return _in_memory ? *_ram
                          : static_cast<std::iostream&>(_fp);
    }
    bool isDeleted() const;

    // ---- Runtime kind / capability ---------------------------------------
    AreaKind kind() const noexcept { return _kind; }
    void setKind(AreaKind k) noexcept { _kind = k; }
    bool supports(AreaCapability cap) const noexcept;

    // ---- Navigation -------------------------------------------------------
    bool gotoRec(int32_t recno);          // 32-bit compatibility adapter -> gotoRec64
    bool gotoRec64(std::uint64_t recno);  // authoritative 64-bit record positioning (RECNO64)
    bool top();
    bool bottom();
    bool skip(int delta);

    // ---- Record I/O -------------------------------------------------------
    bool readCurrent();
    bool writeCurrent();
    bool appendBlank();
    bool deleteCurrent();

    // ---- Selective decode (scan-evaluator lane M2) ------------------------
    // readCurrentRaw() loads the current record's raw bytes into the record
    // buffer and updates the deleted flag, but does NOT decode every field into
    // per-field strings the way readCurrent() does. This skips the eager
    // all-fields std::string decode that dominates scan cost when a predicate
    // only touches a few fields. Additive: readCurrent() is unchanged. Callers
    // using this MUST read field values only via decodeFieldFromBuffer() (or the
    // numeric fast path) -- get()/_fd are NOT refreshed until the next full
    // readCurrent().
    bool readCurrentRaw();

    // Decode a single field (1-based) directly from the current record buffer,
    // using the exact same codec + x64-memo object-id handling as the full
    // loadFieldsFromBuffer(). Correct for every field type; decodes only the one
    // field asked for. Returns empty on any error/out-of-range.
    std::string decodeFieldFromBuffer(int idx1) const;

    // Numeric fast path: decode an N/F (ASCII-numeric) field from the current
    // record buffer straight to double with no std::string allocation. Returns
    // false for non-N/F types or an unparseable value (caller should fall back
    // to decodeFieldFromBuffer()).
    bool fieldNumFromBuffer(int idx1, double& out) const;

    // ---- Durable PRIMARY designation (AIF-156) ----------------------------
    //
    // Stamp field1 as the table's PRIMARY key IN THE FILE, by setting
    // X64_FIELD_FLAG_PRIMARY in that field's X64FieldMetaEntry and
    // DBF64_FLAG_HAS_RECID_PK in the table flags. Clears the bit from every
    // other field first, because a table has at most one primary key and a
    // second stamp must move the designation rather than add one.
    //
    // THIS IS THE META BLOCK'S FIRST WRITER. The block has only ever been built
    // at CREATE (dbf_create.cpp); nothing has ever rewritten one. That absence
    // is the whole reason the designation lived in a process-local map and did
    // not survive a close.
    //
    // Fixed-size patch in place, in the idiom the append path already uses for
    // record_count: no string moves, so no offset moves and total_length is
    // unchanged. Writes through this area's own stream rather than a second
    // handle on the same file.
    //
    // make_primary == false with field1 == 0 clears the designation entirely.
    // Returns false with a reason in *err on a non-x64 table, a table with no
    // metadata block, or a field that has no entry in that block.
    bool setFieldPrimaryDurable(int field1, bool make_primary, std::string* err = nullptr);

    // Field carrying X64_FIELD_FLAG_PRIMARY, or 0 if this table designates none.
    int primaryFieldIndex() const noexcept;

    // Core engine-owned replace entry point.
    // Contract:
    // - field1 is 1-based and already resolved by caller
    // - stored_value is already normalized into on-disk form
    // - performs the core write/update path only
    // - no TABLE buffering / shell integration behavior belongs here
    bool replaceFieldStored(int field1, const std::string& stored_value, std::string* err = nullptr);

    // Stage NULL (or not-null) and write, through the SAME lock / index-snapshot /
    // index-maintenance / trigger envelope replaceFieldStored() uses. Returns
    // false without writing when the field is not nullable. See the note in
    // dbarea.cpp on why this cannot be a bare setFieldNull() + writeCurrent().
    bool replaceFieldNull(int field1, bool make_null = true, std::string* err = nullptr);

    // ---- Record size ------------------------------------------------------
    // RECNO64: legacy 32-bit accessor. When the x64 value exceeds INT_MAX it returns
    // -1 (an impossible length) rather than clamping to INT_MAX, so a 32-bit consumer
    // sees "out of 32-bit range" instead of a plausible-but-wrong value. Use
    // recLength64() for the authoritative value.
    int  recLength() const noexcept {
        return (_record_length64 > static_cast<std::uint64_t>(std::numeric_limits<int>::max()))
            ? -1
            : static_cast<int>(_record_length64);
    }
    int  recordLength() const noexcept;
    int  cpr() const noexcept { return recLength(); }
    std::uint64_t recLength64() const noexcept { return _record_length64; }
    std::uint64_t dataStart64() const noexcept { return _data_start64; }

    // ---- Runtime truth (CANONICAL) ----------------------------------------
    const std::string& filename() const noexcept { return _dbf_abs_path; }
    const std::string& dbfDir() const noexcept { return _dbf_dir; }
    const std::string& dbfBasename() const noexcept { return _dbf_basename; }
    const std::string& logicalName() const noexcept { return _logical_name; }

    // ---- Workspace ownership (AIF-078 design I1) --------------------------
    // Which workspace owns this area, where the area sits in the ENGINE's
    // array, and where it sits inside its own workspace. 0 / -1 mean not
    // assigned. See the member declarations for the rules.
    //
    // CORRECTED 2026-08-22, AIF-078 stage 1, decision D4. This block used to
    // read "which slot it occupies inside it" -- inside the WORKSPACE -- while
    // the setter block below called the same member "a property of the array
    // position". Two descriptions, one member, and they are DIFFERENT NUMBERS
    // the moment a second workspace exists, with nothing in the code to
    // announce which one a caller had relied on. dbf_file.cpp stamps it with
    // the engine array index, so the setter was right and the accessor was
    // wrong. They are now two members with two names, and neither comment has
    // to be read as a claim about the other.
    [[nodiscard]] uint64_t wsHandle()    const noexcept { return _ws_handle;     }
    // The area's own session identity. 0 = not open. See next_area_handle().
    [[nodiscard]] uint64_t areaHandle()  const noexcept { return _area_handle;   }
    [[nodiscard]] int32_t  engineSlot()  const noexcept { return _engine_slot;   }
    [[nodiscard]] int32_t  wsLocalSlot() const noexcept { return _ws_local_slot; }

    // Stamped once by XBaseEngine's constructor and never again -- the engine
    // slot is a property of the array position, not of the table. Public
    // rather than friend because XBaseEngine is not the only conceivable owner
    // of a slot array, and a one-line setter is a smaller commitment than
    // friendship.
    void setEngineSlot(int32_t slot) noexcept { _engine_slot = slot; }

    // Assigned by the workspace registry when an area joins a workspace
    // (AIF-078 stage 2). CHARTERED AND UNSET until then -- -1 everywhere,
    // deliberately, which is the rule the workspace catalog already applies to
    // its own unpopulated columns: "an empty column is a chartered claim"
    // (cmd_workspace.cpp, catalog v2). Numbering is 1..n LOCAL TO THE
    // WORKSPACE (decision D2), so a member added mid-session -- every
    // USE AGAIN instance included -- is simply n+1 and never leaves a hole.
    // Bounded by MAX_AREA and therefore int32_t on purpose; see the note on
    // widths at the member declarations.
    void setWorkspaceLocalSlot(int32_t slot) noexcept { _ws_local_slot = slot; }

    // ---- Memo sidecar facts (co-located with DBF) -------------------------
    const std::string& memoPath() const noexcept { return _memo_abs_path; }
    MemoKind           memoKind() const noexcept { return _memo_kind; }

    // ---- Memo manager / context (per-area) --------------------------------
    dottalk::memo::MemoManager& memoManager();

    dottalk::memo::MemoManager* memoManagerPtr() noexcept {
        return _memo_mgr.get();
    }

    const dottalk::memo::MemoManager* memoManagerPtr() const noexcept {
        return _memo_mgr.get();
    }

    dottalk::memo::MemoContext& memoContext() noexcept { return _memo_ctx; }
    const dottalk::memo::MemoContext& memoContext() const noexcept { return _memo_ctx; }

    // ---- Field access (1-based) -------------------------------------------
    const std::vector<FieldDef>& fields() const { return _fields; }

    // ---- VFP/x64 per-field metadata (AIF-091 M1) --------------------------
    // PARALLEL TO fields() BY INDEX, and that invariant is load-bearing: it is
    // what lets a caller ask "is field 3 nullable" without re-parsing the
    // header. The loader is the only writer. Empty on a classic table, which
    // genuinely carries no flags byte -- an empty vector here means "this
    // flavor has nothing to say", never "not looked at".
    const std::vector<VfpFieldExtras>& fieldExtras() const noexcept { return _extras; }

    // The hidden `_NullFlags` column, if this table has one. Partitioned OUT of
    // fields() so it is not surfaced as a junk binary column; its position is
    // kept here because the record still contains it and the bitmap still has
    // to be read from somewhere.
    const NullFlagsColumn& nullFlagsColumn() const noexcept { return _null_flags; }

    // TRUE when a SYSTEM field was found somewhere other than the last physical
    // position, in which case the partition was DECLINED and the field is still
    // visible in fields(). See setNullFlagsColumn() for why refusing to
    // partition is the safe answer rather than the timid one.
    bool systemFieldNotLast() const noexcept { return _system_field_not_last; }

    // Where each user field's bits live in the `_NullFlags` bitmap. Parallel to
    // fields(), 0-based; a -1 index means "this field has no such bit". Empty
    // when the table has no `_NullFlags` column.
    const vfp::NullBitLayout& nullBitLayout() const noexcept { return _null_layout; }

    // CAN this field be null -- i.e. did its descriptor carry flag 0x02? This is a
    // property of the TABLE. Distinct from fieldIsNullFromBuffer(), which is a
    // property of the current ROW. A caller that conflates them reports every
    // non-nullable field as "not null" and cannot tell that apart from a nullable
    // field that happens to hold a value.
    bool fieldIsNullable(int idx1) const noexcept {
        if (idx1 < 1 || idx1 > static_cast<int>(_null_layout.fields.size())) return false;
        return _null_layout.fields[static_cast<std::size_t>(idx1 - 1)].null_bit >= 0;
    }

    // Is this field NULL in the record currently in the buffer? Reads the bitmap
    // out of `_recbuf` at the partitioned column's offset. FAILS CLOSED (false)
    // when there is no bitmap, when the field has no null bit, or when the buffer
    // is too short -- "not null" is the answer that cannot invent data.
    bool fieldIsNullFromBuffer(int idx1) const noexcept;

    // ---- set-to-null ------------------------------------------------------
    //
    // THREE PREDICATES, NOT ONE, AND THE DIFFERENCE IS THE WHOLE POINT:
    //
    //   fieldIsNullable(i)        the TABLE: does the descriptor carry 0x02
    //   fieldIsNullFromBuffer(i)  the ROW ON DISK: what the bitmap in _recbuf says
    //   fieldIsNull(i)            the STAGED row: what the next write WILL say
    //
    // `fieldIsNull` mirrors get()/set(): it reads the pending value that
    // storeFieldsToBuffer() has not written yet. Immediately after gotoRec() the
    // two row predicates agree; after setFieldNull() they disagree until the
    // record is written, exactly as get() disagrees with the buffer after set().
    // A caller that wants "what is on disk right now" wants the FromBuffer one.
    bool fieldIsNull(int idx1) const noexcept;

    // Stage this field NULL (or, with make_null=false, not-null).
    //
    // REFUSES a field the TABLE says cannot be null, and refuses a table with no
    // `_NullFlags` column at all -- returning false rather than setting a bit no
    // field owns. Nulling a field also CLEARS its staged value, because a null
    // cell has no value and leaving the old text behind would make get() describe
    // a cell that will be written as blanks. That mirrors what the bytes do:
    // Visual FoxPro writes a null field's value area as spaces (measured on
    // nullfix.DBF rows 2 and 5, and on the row VFP wrote into nullwrote.DBF).
    //
    // Clearing null does NOT restore the old value -- there is nothing to restore.
    // The caller sets one.
    //
    // The write itself still happens in storeFieldsToBuffer()/writeCurrent().
    bool setFieldNull(int idx1, bool make_null = true);

    std::string get(int idx) const;
    bool        set(int idx, const std::string& val);

    // ---- Info -------------------------------------------------------------
    // RECNO64: legacy 32-bit accessors. On an x64 table whose value exceeds INT32_MAX
    // these return -1 (an impossible recno / count) rather than silently clamping to
    // INT_MAX. A 32-bit consumer then sees "out of range" and skips/errors, instead of
    // acting on the wrong record (the old saturating behavior returned INT_MAX, which
    // reads as a valid record). Use recno64()/recCount64() for the authoritative value.
    int32_t recno() const noexcept {
        return (_crn64 > static_cast<uint64_t>(std::numeric_limits<int32_t>::max()))
            ? -1
            : static_cast<int32_t>(_crn64);
    }
    int32_t recCount() const noexcept {
        return (_rec_count64 > static_cast<uint64_t>(std::numeric_limits<int32_t>::max()))
            ? -1
            : static_cast<int32_t>(_rec_count64);
    }

    uint64_t recno64() const noexcept    { return _crn64; }
    uint64_t recCount64() const noexcept { return _rec_count64; }

    bool bof() const noexcept { return _crn64 == 0; }
    bool eof() const noexcept { return _rec_count64 == 0 || _crn64 > _rec_count64; }
    int  fieldCount() const { return static_cast<int>(_fields.size()); }

    // ---- Legacy compatibility --------------------------------------------
    std::string name() const { return _logical_name; }
    void        setFilename(std::string path);

    // ---- Resolved runtime names ------------------------------------------
    // These setters receive final names resolved by dialect-specific loaders
    // such as xbase_64.hpp. DbArea stores runtime truth only; it does not
    // mirror or own the underlying vector metadata blocks.
    void setLogicalName(std::string name) {
        _logical_name = std::move(name);
    }

    bool setFieldName(int field1, std::string name) {
        if (field1 < 1 || field1 > static_cast<int>(_fields.size())) return false;
        _fields[static_cast<std::size_t>(field1 - 1)].name = std::move(name);
        return true;
    }

    bool setFieldLength(int field1, std::uint32_t len) {
        if (field1 < 1 || field1 > static_cast<int>(_fields.size())) return false;
        _fields[static_cast<std::size_t>(field1 - 1)].length = len;
        return true;
    }

    bool setFieldX64Flags(int field1, std::uint16_t flags) {
        if (field1 < 1 || field1 > static_cast<int>(_fields.size())) return false;
        _fields[static_cast<std::size_t>(field1 - 1)].x64_flags = flags;
        return true;
    }

    std::uint16_t fieldX64Flags(int field1) const noexcept {
        if (field1 < 1 || field1 > static_cast<int>(_fields.size())) return 0;
        return _fields[static_cast<std::size_t>(field1 - 1)].x64_flags;
    }

    // ---- Where this table's own x64 metadata block lives ------------------
    //
    // Recorded at open so a later writer can patch one fixed-size entry in
    // place instead of re-deriving the location by walking the descriptors
    // again. The block runs from x64MetaStart() to dataStart64(); a zero start
    // means this table has no metadata block and nothing may be patched into
    // one. table_flags is kept for the same reason -- the summary bit that says
    // "somebody in this table is a key" lives there.
    void setX64MetaExtent(std::uint64_t start, std::uint32_t len) noexcept {
        _x64_meta_start = start;
        _x64_meta_len   = len;
    }
    std::uint64_t x64MetaStart()  const noexcept { return _x64_meta_start; }
    std::uint32_t x64MetaLength() const noexcept { return _x64_meta_len; }

    void setX64TableFlags(std::uint32_t f) noexcept { _x64_table_flags = f; }
    std::uint32_t x64TableFlags() const noexcept { return _x64_table_flags; }

    // ---- Internal lifecycle helpers --------------------------------------
    void _compute_paths_and_names_(const std::string& abs_dbf_path);
    void _clear_paths_and_names_() noexcept;

    // ---- VFP loader / compatibility setters -------------------------------
    void clearFields() noexcept {
        _fields.clear();
        _rawFields.clear();
        _extras.clear();
        _null_flags = NullFlagsColumn{};
        _system_field_not_last = false;
    }

    // ---- AIF-091 M1 loader hand-off -----------------------------------------
    // The loader parses the descriptors; DbArea keeps what it found. Both the
    // VFP and the x64 path funnel through vfp_loader::readFields, so there is
    // ONE writer for this state.
    void setFieldExtras(std::vector<VfpFieldExtras> ex) noexcept {
        _extras = std::move(ex);
    }

    // Partition the hidden `_NullFlags` column out of the visible field vector.
    //
    // WHY ONLY THE LAST FIELD. DbArea::fieldByteOffset_() computes a field's
    // position by ACCUMULATING the lengths of the fields before it and ignores
    // the descriptor's own `displacement` (bytes 12-15). So removing a field
    // from _fields shifts every field AFTER it. VFP always writes _NullFlags
    // last, which makes the partition safe -- but "always" is an assumption
    // about someone else's writer, and this is where it gets checked instead of
    // asserted in a comment.
    //
    // If a system field turns up anywhere else, we DECLINE to partition and
    // leave it visible. That is not timidity: a visible system column is
    // exactly today's behaviour and is merely ugly, whereas silently shifting
    // every subsequent field's byte offset would decode the whole record wrong.
    // Degrade to the status quo, loudly, rather than to corruption, quietly.
    bool partitionTrailingSystemField(const std::string& name) noexcept {
        if (_fields.empty() || _extras.size() != _fields.size()) return false;

        // Any system field that is NOT the final one blocks the partition.
        for (std::size_t i = 0; i + 1 < _extras.size(); ++i) {
            if (_extras[i].system) {
                _system_field_not_last = true;
                return false;
            }
        }
        if (!_extras.back().system) return false;

        std::size_t off = 1;                       // byte 0 is the deleted flag
        for (std::size_t i = 0; i + 1 < _fields.size(); ++i)
            off += _fields[i].length;

        _null_flags.present = true;
        _null_flags.offset  = off;
        _null_flags.length  = _fields.back().length;
        _null_flags.name    = name;

        _fields.pop_back();
        _extras.pop_back();
        if (!_rawFields.empty()) _rawFields.pop_back();

        // THE BIT LAYOUT IS BUILT HERE AND NOWHERE ELSE, for the same reason the
        // rule itself lives in one function: a second site that derives bit
        // indices is a second site that can drift. It is built AFTER the pops, so
        // it is indexed by the USER field vector the caller will actually see --
        // `_null_layout.fields[i]` is parallel to `_fields[i]`, 0-based.
        //
        // A field contributes a "full" bit if it is variable-length (V/Q) and a
        // null bit if flag 0x02 is set; the full bit is the LOWER of the two.
        // Measured against a Visual FoxPro-authored fixture, not assumed --
        // see include/xbase/vfp_null_bits.hpp.
        {
            std::vector<vfp::FieldNullSpec> specs;
            specs.reserve(_fields.size());
            for (std::size_t i = 0; i < _fields.size(); ++i) {
                vfp::FieldNullSpec sp;
                const char t = _fields[i].type;
                sp.varlength = (t == 'V' || t == 'v' || t == 'Q' || t == 'q');
                sp.nullable  = _extras[i].nullable;
                specs.push_back(sp);
            }
            _null_layout = vfp::assign_null_bits(specs);
        }
        return true;
    }
    void addField(FieldDef fd) {
        _fields.push_back(std::move(fd));
    }
    void addRawField(FieldRec fr) {
        _rawFields.push_back(std::move(fr));
    }
    void setVersionByte(uint8_t ver) noexcept {
        _dbf_version_byte = ver;
        _hdr.version = ver;
    }
    uint8_t versionByte() const noexcept {
        return _dbf_version_byte;
    }
    void setHeader(const HeaderRec& hdr) noexcept {
        _hdr = hdr;
        _dbf_version_byte = hdr.version;
        _rec_count64 = (hdr.num_of_recs < 0)
            ? 0u
            : static_cast<uint64_t>(hdr.num_of_recs);
        _data_start64 = (hdr.data_start < 0)
            ? 0u
            : static_cast<uint64_t>(static_cast<std::uint16_t>(hdr.data_start));
        _record_length64 = (hdr.cpr < 0)
            ? 0u
            : static_cast<uint64_t>(static_cast<std::uint16_t>(hdr.cpr));
    }
    void setRecordCount(int32_t n) noexcept {
        _hdr.num_of_recs = n;
        _rec_count64 = (n < 0) ? 0u : static_cast<uint64_t>(n);
    }
    void setRecordCount64(uint64_t n) noexcept {
        _rec_count64 = n;
        _hdr.num_of_recs = (n > static_cast<uint64_t>(std::numeric_limits<int32_t>::max()))
            ? std::numeric_limits<int32_t>::max()
            : static_cast<int32_t>(n);
    }
    void setRecno64(uint64_t n) noexcept {
        _crn64 = n;
        _crn = (n > static_cast<uint64_t>(std::numeric_limits<int32_t>::max()))
            ? std::numeric_limits<int32_t>::max()
            : static_cast<int32_t>(n);
    }
    void setDataStart(std::uint64_t start) noexcept {
        _data_start64 = start;
        _hdr.data_start =
            (start > static_cast<std::uint64_t>(std::numeric_limits<int16_t>::max()))
                ? 0
                : static_cast<int16_t>(start);
    }
    void setRecordLength(std::uint64_t len) noexcept {
        _record_length64 = len;
        _hdr.cpr =
            (len > static_cast<std::uint64_t>(std::numeric_limits<int16_t>::max()))
                ? 0
                : static_cast<int16_t>(len);
    }
    void setLastUpdated(uint8_t yy, uint8_t mm, uint8_t dd) noexcept {
        _hdr.last_updated[0] = yy;
        _hdr.last_updated[1] = mm;
        _hdr.last_updated[2] = dd;
    }

    // ---- 64-bit DBF compatibility additions -------------------------------
    // autoQNext64() has NO callers, by ruling rather than by accident: the
    // slot is reserved and unwired (R119, 2026-08-24, AIF-078). The full statement
    // and the recipe for making it live are at the LargeHeaderExtension
    // declaration in xbase_64.hpp. Do not add a store-back without a consumer.
    void setAutoQNext64(uint64_t v) noexcept {
        _autoq_next64 = v;
    }
    uint64_t autoQNext64() const noexcept {
        return _autoq_next64;
    }

    void setTableFlags(uint32_t v) noexcept {
        _table_flags = v;
    }
    uint32_t tableFlags() const noexcept {
        return _table_flags;
    }

private:
    // ===== Storage =========================================================
    std::fstream _fp;
    std::unique_ptr<std::iostream> _ram;  // AIF-043 in-memory tables: ramfs byte store (V2)
    bool _in_memory{false};               // when true, io() serves record bytes from *_ram
    HeaderRec    _hdr{};

    // ===== Schema & buffers ===============================================
    std::vector<FieldDef>  _fields;
    std::vector<FieldRec>  _rawFields;
    // AIF-091 M1. Parallel to _fields by index; see fieldExtras().
    std::vector<VfpFieldExtras> _extras;
    NullFlagsColumn             _null_flags;
    // Built by partitionTrailingSystemField(); parallel to _fields, 0-based.
    vfp::NullBitLayout          _null_layout;
    bool                        _system_field_not_last {false};
    std::vector<char>      _recbuf;

    // Current record values (1-based indexing: slot 0 unused)
    std::vector<std::string> _fd;
    // Snapshot retained for physical before/after record state.
    std::vector<std::string> _fd_snapshot;
    // STAGED null state, 1-based and parallel to `_fd`. Kept in lockstep with it
    // at every site that sizes or clears `_fd` -- if the two ever differ in
    // length the indices desync and a null lands on the wrong field, which is
    // the one failure mode here that no test would obviously catch.
    std::vector<char> _fd_null;

    // ===== Cursor state ====================================================
    int32_t  _crn{0};
    uint64_t _crn64{0};
    uint64_t _rec_count64{0};
    uint64_t _data_start64{0};
    uint64_t _x64_meta_start{0};
    uint32_t _x64_meta_len{0};
    uint32_t _x64_table_flags{0};
    uint64_t _record_length64{0};
    char     _del{NOT_DELETED};

    // ===== Runtime kind ====================================================
    AreaKind _kind{AreaKind::Unknown};

    // ===== Per-area managers ==============================================
    dottalk::memo::MemoContext _memo_ctx;
    std::unique_ptr<dottalk::memo::MemoManager> _memo_mgr;

    // ===== Runtime descriptors (CANONICAL) ================================
    std::string _dbf_abs_path;
    std::string _dbf_dir;
    std::string _dbf_basename;
    std::string _dbf_ext;
    std::string _logical_name;

    // Memo sidecar
    std::string _memo_abs_path;
    MemoKind    _memo_kind{MemoKind::NONE};

    // ===== Workspace ownership (AIF-078 design I1) ========================
    // An area belongs to exactly ONE workspace, and now knows which one and
    // which slot it occupies inside it. Before this, ownership existed only in
    // side tables -- which is why the relation graph is keyed on a bare
    // uppercased parent name with no owner field (set_relations.cpp:60), and
    // why slot_of_area() had to linear-scan the open areas to answer "which
    // slot am I" at 21 call sites across 15 files.
    //
    // 0 / -1 mean NOT ASSIGNED, which is the state of a closed area. The
    // engine constructs MAX_AREA areas eagerly (XBaseEngine's constructor in
    // dbf_file.cpp -- the old "409-411" here pointed at the append path, and
    // was already wrong before this commit shifted it further), so
    // _engine_slot is stamped there once and never changes; _ws_handle is set
    // when an area is opened into a workspace and cleared by close().
    //
    // One workspace exists today, so _ws_handle is 1 for every open area. That
    // is deliberate: the FIELD is the change, and a constant is the honest
    // value while there is exactly one workspace to name. See
    // docs/maintenance/AIF120_NAME_SCHEMA_RULING_V1.md sec 4 level 1.
    // WIDTHS ARE DELIBERATE, not an oversight (AIF-078 stage 1).
    // _ws_handle is 64-bit because it names a WORKSPACE, and workspace
    // identity is the catalog's WS_ID -- an N(10) column, up to ten digits,
    // which overflows int32. The two slots are 32-bit because they index
    // AREAS, which are bounded by MAX_AREA (itself an int); the steward ruled
    // unbounded areas OUT on 2026-08-22, so a wider slot would be churn with
    // no capacity behind it.
    uint64_t    _ws_handle{0};
    // AIF-078 2026-08-23. The AREA's session handle -- minted by open(), cleared
    // by close(), never reused. 64-bit for the same reason _ws_handle is: it is
    // a monotonic counter over the life of a session, not an index into
    // anything, so MAX_AREA does not bound it. Opening and closing one area in a
    // loop advances it without limit, which is the point.
    uint64_t    _area_handle{0};
    int32_t     _engine_slot{-1};
    int32_t     _ws_local_slot{-1};

    // RETIRED 2026-08-22 (AIF-120 I1.0): _db_name and _filename lived here
    // under a "Legacy storage (DEPRECATED, mapped internally)" banner. Neither
    // was mapped to anything. _db_name had four writers and ZERO readers;
    // _filename had zero of both -- not one line in src/ or include/ ever
    // touched it. Removed while the header was already open for the members
    // above, at no extra rebuild. The table-name-vs-alias split they were
    // shaped for is design I1's job and is done by _ws_handle/_engine_slot plus
    // the one real name, _logical_name.

    // ===== VFP compatibility additions =====================================
    uint8_t     _dbf_version_byte{0x03};

    // ===== 64-bit DBF compatibility additions ==============================
    uint64_t    _autoq_next64{0};
    uint32_t    _table_flags{0};

    // ===== Internals =======================================================
    void        readHeader();
    void        readFields();
    bool        loadFieldsFromBuffer();
    bool        replaceFieldEnveloped_(int field1,
                                       const std::function<bool()>& stage,
                                       std::string* err);
    void        storeFieldsToBuffer();
    static std::string rtrim(std::string s);

    // Byte offset of field idx1 (1-based) within _recbuf (record starts at 1,
    // after the deleted flag). Returns SIZE_MAX if idx1 is out of range.
    std::size_t fieldByteOffset_(int idx1) const;

    // ---- Varchar (V/Q) helpers -------------------------------------------
    // WHY THESE ARE NOT CODECS. fieldcodec::Codec::decode takes a field's OWN
    // bytes and its FULL width; a Varchar's true length lives in the
    // `_NullFlags` column -- a DIFFERENT field. `V` is the first type whose
    // decode depends on state outside its own byte span, and the seam cannot
    // express that. So Varchar is handled BESIDE the registry, the way the
    // x64-memo path already is, rather than by registering a codec that would
    // only work when the area secretly pre-chewed its arguments. A registry
    // entry that lies about what it can do on its own is worse than no entry.
    bool        isVarlengthField_(int idx1) const noexcept;
    // Effective value length for a V/Q field in the CURRENT buffer.
    std::size_t varlengthValueLen_(int idx1, std::size_t off) const noexcept;

    // Index helpers
    int         findFieldCI(const std::string& name) const;
    int         firstCharField() const;
    std::vector<uint8_t> encodeKeyFrom(const std::vector<std::string>& vals) const;
    std::vector<uint8_t> currentKey()  const { return encodeKeyFrom(_fd); }
    std::vector<uint8_t> snapshotKey() const { return encodeKeyFrom(_fd_snapshot); }
};

// ---- Engine wrapper --------------------------------------------------------
class XBaseEngine {
public:
    XBaseEngine();
    DbArea* areaPtr(int idx) noexcept {
        if (idx < 0 || idx >= MAX_AREA) return nullptr;
        return _areas[idx].get();
    }
    const DbArea* areaPtr(int idx) const noexcept {
        if (idx < 0 || idx >= MAX_AREA) return nullptr;
        return _areas[idx].get();
    }
    DbArea& area(int idx) {
        if (idx < 0 || idx >= MAX_AREA) throw std::out_of_range("area");
        return *_areas[idx];
    }
    void selectArea(int idx) {
        if (idx < 0 || idx >= MAX_AREA) throw std::out_of_range("area");
        _current = idx;
    }
    int currentArea() const { return _current; }

private:
    std::array<std::unique_ptr<DbArea>, MAX_AREA> _areas;
    int _current{0};
};

// Helpers
std::string dbNameWithExt(std::string s); // ensure .dbf

} // namespace xbase

using DbArea = xbase::DbArea;
