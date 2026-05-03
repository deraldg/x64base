#include "smartlist_output.hpp"

#include "cli/table_state.hpp"

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <string>

namespace cli::smartlist {

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
    std::cout << "  " << std::setw(recw) << "" << " ";
    for (const auto& f : Fs) {
        std::cout << std::left << std::setw((int)f.length) << f.name << " ";
    }
    std::cout << std::right << "\n";
}

void print_row(const xbase::DbArea& a, int recw) {
    const auto& Fs = a.fields();

    std::cout << ' ' << (a.isDeleted() ? '*' : ' ')
              << ' ' << std::setw(recw) << a.recno() << " ";

    for (int i = 1; i <= (int)Fs.size(); ++i) {
        std::string s = a.get(i);
        const int w = (int)Fs[(size_t)(i - 1)].length;
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

        const int w = static_cast<int>(Fs[static_cast<size_t>(i)].length);
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
