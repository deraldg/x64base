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

static int field_column_width(const xbase::FieldDef& f) {
    const int data_width = std::max(1, static_cast<int>(f.length));
    const int name_width = std::min(
        static_cast<int>(f.name.size()),
        LIST_FIELD_NAME_DISPLAY_CAP
    );
    return std::max(data_width, name_width);
}

static bool needs_header_truncation(const xbase::FieldDef& f) {
    return static_cast<int>(f.name.size()) > field_column_width(f);
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

    for (const auto& f : Fs) {
        const int w = field_column_width(f);
        const std::string label = fit_display(f.name, w);
        if (needs_header_truncation(f)) truncated = true;

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
        const int w = field_column_width(Fs[(size_t)(i - 1)]);
        if ((int)s.size() > w) s.resize((size_t)w);
        std::cout << std::left << std::setw(w) << s << " ";
    }

    std::cout << std::right << "\n";
}

void print_row(const xbase::DbArea& schema_area,
               const dottalk::table::Row& row,
               int recw,
               bool physical_deleted) {
    const auto& Fs = schema_area.fields();

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

        const int w = field_column_width(Fs[static_cast<size_t>(i)]);
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
