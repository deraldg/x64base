// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "cli/null_display.hpp"
#include "smartlist_output.hpp"

#include "cli/table_state.hpp"

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <string>

namespace cli::smartlist {

namespace {

// Presentation policy only.
//
// Storage/name authority is not affected here:
// - STRUCT and diagnostics remain the place to see full schema names.
// - LIST is a report-style view and should stay readable when x64 field-name
//   vectors allow 64/128-byte identifiers.
constexpr int LIST_FIELD_NAME_DISPLAY_CAP = 24;

// WIDTH IS COMPUTED IN EXACTLY ONE PLACE, and it now needs the area because
// nullability is a property of the table rather than of the FieldDef. The header
// and every row call THIS -- if only one of them widened, the columns after a
// nullable field would shift and the table would be unreadable.
static int field_column_width(const xbase::DbArea& a, int field1) {
    const auto& f = a.fields().at(static_cast<std::size_t>(field1 - 1));
    const int data_width = std::max(1, static_cast<int>(f.length));
    const int name_width = std::min(
        static_cast<int>(f.name.size()),
        LIST_FIELD_NAME_DISPLAY_CAP
    );
    const int w = std::max(data_width, name_width);

    // `.NULL.` is six characters. A 4-wide numeric column would truncate it to
    // `.NUL`, which reads as data and is worse than the blank it replaced.
    // Non-nullable fields are untouched, so this widens ONLY tables that carry a
    // `_NullFlags` column.
    return cli::nulldisp::widen_for_null(a, field1, w);
}

static bool needs_header_truncation(const xbase::DbArea& a, int field1) {
    const auto& f = a.fields().at(static_cast<std::size_t>(field1 - 1));
    return static_cast<int>(f.name.size()) > field_column_width(a, field1);
}

static std::string fit_display(std::string s, int width) {
    if (width <= 0) return std::string{};
    if (static_cast<int>(s.size()) <= width) return s;

    if (width <= 3) {
        s.resize(static_cast<std::size_t>(width));
        return s;
    }

    s.resize(static_cast<std::size_t>(width - 3));
    s += "...";
    return s;
}

} // namespace

int recno_width(const xbase::DbArea& a) {
    int n = std::max(1, a.recCount());
    int w = 0;
    while (n) {
        n /= 10;
        ++w;
    }
    return std::max(3, w);
}

void print_header(const xbase::DbArea& a, int recw) {
    const auto& Fs = a.fields();

    bool truncated = false;
    std::cout << "  " << std::setw(recw) << "" << " ";

    for (int i = 1; i <= static_cast<int>(Fs.size()); ++i) {
        const auto& f = Fs[static_cast<std::size_t>(i - 1)];
        const int w = field_column_width(a, i);
        const std::string label = fit_display(f.name, w);
        if (needs_header_truncation(a, i)) truncated = true;

        std::cout << std::left << std::setw(w) << label << " ";
    }

    std::cout << std::right << "\n";

    if (truncated) {
        std::cout
            << "; LIST display note: one or more field-name headers were "
            << "truncated for readability; use STRUCT for full names.\n";
    }
}

void print_row(const xbase::DbArea& a, int recw) {
    const auto& Fs = a.fields();

    std::cout << ' ' << (a.isDeleted() ? '*' : ' ')
              << ' ' << std::setw(recw) << a.recno() << " ";

    for (int i = 1; i <= (int)Fs.size(); ++i) {
        std::string s = a.get(i);
        // A NULL prints as VFP prints it. Applied AFTER get() and BEFORE the
        // width clamp, so the marker is never the thing that gets truncated --
        // the column was widened for it above.
        (void)cli::nulldisp::apply(a, i, s);
        const int w = field_column_width(a, i);
        if ((int)s.size() > w) s.resize((size_t)w);
        std::cout << std::left << std::setw(w) << s << " ";
    }

    std::cout << std::right << "\n";
}

void print_row(const xbase::DbArea& schema_area,
               const dottalk::table::Row& row,
               int recw,
               bool physical_deleted,
               const dottalk::table::Overlay* overlay) {
    const auto& Fs = schema_area.fields();

    // THE NULL MARKER IS ONLY SAFE HERE IF THIS AREA IS PARKED ON THE ROW BEING
    // PRINTED, because fieldIsNullFromBuffer() reads the record in `_recbuf` and
    // has no idea which recno the caller meant. Callers do position it (LIST
    // reads isDeleted() off the same area), but a future caller might not, and a
    // null painted from the wrong row is the kind of wrong answer that looks
    // like data. When they disagree, print no markers at all.
    const bool null_flags_trustworthy =
        (static_cast<int>(schema_area.recno()) == row.recno);

    const bool buffered_delete =
        (row.flags & dottalk::table::CHANGE_DELETE) != 0;

    std::cout << ' ' << ((physical_deleted || buffered_delete) ? '*' : ' ')
              << ' ' << std::setw(recw) << row.recno << " ";

    const int field_count = static_cast<int>(Fs.size());
    for (int i = 0; i < field_count; ++i) {
        std::string s;
        if (i < static_cast<int>(row.values.size())) {
            s = row.values[static_cast<size_t>(i)];
        }

        if (null_flags_trustworthy) {
            // A PENDING BUFFERED VALUE OUTRANKS THE PHYSICAL NULL: this path
            // shows what a COMMIT would produce, so a physically-null field
            // carrying a buffered edit must show the EDIT. Buffered NULL is
            // refused, so an overlay can never make a cell null -- the rule only
            // ever runs one way.
            const bool overlaid =
                overlay && overlay->new_values.count(i + 1) != 0;
            (void)cli::nulldisp::apply(schema_area, i + 1, s, overlaid);
        }

        const int w = field_column_width(schema_area, i + 1);
        if (static_cast<int>(s.size()) > w) {
            s.resize(static_cast<size_t>(w));
        }
        std::cout << std::left << std::setw(w) << s << " ";
    }

    std::cout << std::right << "\n";
}

void print_footer(bool all, int limit, int printed) {
    if (!all) {
        std::cout << printed << " record(s) listed (limit " << limit
                  << "). Use SMARTLIST ALL to show more.\n";
    } else {
        std::cout << printed << " record(s) listed.\n";
    }
}

} // namespace cli::smartlist
