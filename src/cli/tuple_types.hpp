// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace dottalk {

// -----------------------------------------------------------------------------
// RECNO64 canonical types (RECNO64_END_TO_END_64BIT_ADDRESSING_LANE_V1.md, plan
// item 1). Identity and delta are DIFFERENT types on purpose: a record number is
// unsigned and 64-bit because that is what the engine stores (xbase.hpp keeps
// _crn64/_rec_count64 as uint64_t and nothing narrower exists in the core), while
// a movement is signed and may be negative. `long` is never used for either --
// it is 64-bit under gcc (LP64) and 32-bit under MSVC (LLP64), so a record number
// carried in a `long` has a different width on the two builds of this program.
// -----------------------------------------------------------------------------
using RecordNo    = std::uint64_t;  // identity
using RecordDelta = std::int64_t;   // signed for backward movement

// Where a piece of a tuple came from.
// Keep this simple; expand later (memo blocks, json row ids, sqlite rowid, etc.)
enum class TupleSourceKind : uint8_t {
    Unknown = 0,
    DBF     = 1,
    Memo    = 2,
    Derived = 3,
    JSON    = 4,
    SQLite  = 5
};

struct TupleColumn {
    std::string name;       // column label (resolved to canonical field name when possible)
    int         area_slot;  // work area slot (0..MAX_AREA-1) that owns it; -1 if unknown
    std::string field;      // resolved field name in that area, or original token if unresolved
    // AIF-074 P1.2 (R16a): engine-owned type surface, mode-invariant.
    // Blank-is-a-value; there is no null state. ' ' = type not resolved.
    char        ftype = ' ';
    int         flen  = 0;
    int         fdec  = 0;
};

struct TupleFragment {
    int             area_slot = -1;
    RecordNo        recno     = 0; // 1-based recno if known; 0 if unknown
    TupleSourceKind kind      = TupleSourceKind::Unknown;
    bool            deleted   = false;
    std::string     note;          // optional breadcrumb
};

// NULL-READY: a produced-absent outer-join cell is not a DBF blank and is not
// a stored NULL. Keep that distinction in the row carrier so adding a future
// StoredNull enumerator does not change TupleRow's shape. Present remains the
// default for older producers that predate this aligned metadata vector.
enum class TupleCellKind : std::uint8_t {
    Present,
    ProducedAbsent
};

inline constexpr std::string_view kProducedAbsentMarker = "<UNMATCHED>";

// NULL-READY: every absent kind renders through this one routine. SQLsel LEFT
// JOIN is the first producer; future stored NULL must extend this switch rather
// than inventing a second surface-specific token.
inline std::string render_tuple_cell(std::string_view value, TupleCellKind kind) {
    switch (kind) {
        case TupleCellKind::Present:
            return std::string(value);
        case TupleCellKind::ProducedAbsent:
            return std::string(kProducedAbsentMarker);
    }
    return {};
}

struct TupleRow {
    std::vector<TupleColumn>   columns;    // stable ordering
    std::vector<std::string>   values;     // aligned with columns
    std::vector<TupleCellKind> cell_kinds; // empty means all Present (legacy producers)
    std::vector<TupleFragment> fragments;  // provenance

    bool empty() const   { return values.empty(); }
    bool aligned() const {
        return columns.size() == values.size() &&
               (cell_kinds.empty() || cell_kinds.size() == values.size());
    }
    TupleCellKind cell_kind(std::size_t index) const {
        return cell_kinds.empty() ? TupleCellKind::Present : cell_kinds.at(index);
    }
};

struct TupleBuildOptions {
    bool        want_header             = false; // builder returns data row; header built by caller
    bool        header_area_prefix      = false; // header names as AREA.FIELD
    bool        values_area_prefix_echo = false; // for pretty printers
    bool        strict_fields           = false; // error on missing explicit field
    bool        refresh_relations       = true;  // refresh SET RELATION before build
    bool        overlay_table_buffer    = true;  // preview uncommitted TABLE BUFFER edits
    std::string null_token              = "";    // pretty placeholder
};

} // namespace dottalk
