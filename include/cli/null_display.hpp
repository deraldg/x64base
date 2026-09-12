// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// owner: member.derald
// status: experimental
//
// include/cli/null_display.hpp -- ONE ANSWER TO "IS THIS CELL NULL, AND WHAT DO
// WE PRINT FOR IT".
//
// WHY THIS EXISTS. Set-to-null landed before anything could display a null. A
// grep across src/cli for fieldIsNullFromBuffer / fieldIsNull returned NOTHING:
// LIST, SMARTLIST and DISPLAY all render a cell through DbArea::get(), a null
// cell returns an empty string, and so does a blank one. At our own prompt a
// successful `REPLACE x WITH NULL` and a `REPLACE x WITH ""` were
// INDISTINGUISHABLE -- absence spelled as blank, the AIF-118 shape, in the one
// place a user would look to check the feature worked.
//
// THE MARKER IS VFP'S. `.NULL.` is what Visual FoxPro prints, and matching it is
// the same ruling as routing APPEND BLANK: the spelling a FoxPro user already
// knows should be the one they see. It is also unambiguous in a way a blank is
// not -- no C field can hold `.NULL.` and no numeric can render as it, so the
// marker cannot be confused with data.
//
// TWO RULES, AND THE SECOND IS THE ONE THAT IS EASY TO GET WRONG:
//
//   1. A NULLABLE COLUMN MUST BE WIDE ENOUGH FOR THE MARKER. field_column_width()
//      is max(data_width, name_width), so `id N(4)` yields a 4-wide column and
//      `.NULL.` truncates to `.NUL` -- which reads as DATA, and is worse than the
//      blank it replaced. Widening is applied through ONE function that both the
//      header and the row call, because if only the row widened every column
//      after it shifts and the whole table becomes unreadable.
//
//   2. A PENDING BUFFERED VALUE OUTRANKS THE PHYSICAL NULL. LIST's overlay path
//      shows what a COMMIT would produce. A field that is physically null but
//      carries a buffered edit must show the EDIT, not `.NULL.` -- painting the
//      physical flag over a pending value would report the opposite of what is
//      about to happen. Buffered NULL is refused (see cmd_replace.cpp), so the
//      reverse case cannot arise: an overlay can never make a cell null.
//
// FAILS TOWARD THE DATA. Every predicate here answers "not null" when it cannot
// be sure -- no bitmap, no null bit, a short buffer, or an area parked on a
// different record than the row being printed. Printing a value that is really
// there is recoverable; printing `.NULL.` over one is not.

#pragma once

#include <string>

#include "xbase.hpp"

namespace cli::nulldisp {

// What Visual FoxPro prints. Six characters.
inline constexpr const char* kMarker = ".NULL.";
inline constexpr int         kMarkerWidth = 6;

// Minimum column width for a field that can hold a null. Non-nullable fields are
// untouched, so this widens ONLY tables carrying a `_NullFlags` column.
inline int widen_for_null(const xbase::DbArea& a, int field1, int w) noexcept
{
    return a.fieldIsNullable(field1) ? (w > kMarkerWidth ? w : kMarkerWidth) : w;
}

// Is the cell at `field1` of the record CURRENTLY IN THE BUFFER null?
// `overlaid` is true when the caller holds a pending buffered value for this
// field, in which case the answer is always false -- see rule 2 above.
inline bool is_null_cell(const xbase::DbArea& a, int field1,
                         bool overlaid = false) noexcept
{
    if (overlaid) return false;
    return a.fieldIsNullFromBuffer(field1);
}

// Substitute the marker into `text` when the cell is null. Returns true when it
// did, so a caller that also right-justifies numerics can decide how to align.
inline bool apply(const xbase::DbArea& a, int field1, std::string& text,
                  bool overlaid = false)
{
    if (!is_null_cell(a, field1, overlaid)) return false;
    text = kMarker;
    return true;
}

} // namespace cli::nulldisp
