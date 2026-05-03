#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "workareas.hpp"
#include "cli/order_iterator.hpp"

// ---------- minimal filter pass (GPS uses default LIST semantics) ----------
static inline bool pass_deleted_filter(const xbase::DbArea& a)
{
    // Default reporting semantics: hide deleted rows from logical-row counting.
    return !a.isDeleted();
}

// ---------- logical row computation ----------
static std::int64_t compute_logical_row(xbase::DbArea& a, int32_t physical)
{
    if (physical < 1 || physical > a.recCount()) return 0;

    std::int64_t logical = 0;

    cli::OrderIterSpec spec{};
    std::string err;

    cli::order_iterate_recnos(
        a,
        [&](uint64_t rn64) -> bool
        {
            if (rn64 == 0 || rn64 > static_cast<uint64_t>(a.recCount64()))
                return true;

            const int32_t rn = static_cast<int32_t>(rn64);

            if (!a.gotoRec(rn) || !a.readCurrent())
                return true;

            if (!pass_deleted_filter(a))
                return true;

            ++logical;

            if (rn == physical)
                return false;

            return true;
        },
        &spec,
        &err
    );

    return logical;
}

// ---------- main command ----------
void cmd_GPS(xbase::DbArea& current, std::istringstream& /*iss*/)
{
    const std::size_t cur_area = workareas::current_slot();

    if (!current.isOpen()) {
        std::cout
            << "Cursor: Area " << cur_area
            << " of " << workareas::occupied_desc()
            << " ... No table open\n";
        return;
    }

    int recno = 0;
    try {
        recno = current.recno();
    } catch (...) {
        recno = 0;
    }

    std::string table_name;
    try {
        table_name = workareas::current()->label();
    } catch (...) {
        table_name.clear();
    }

    if (table_name.empty()) {
        table_name = "(unnamed)";
    }

    const std::int64_t logical_row = compute_logical_row(current, recno);

    std::cout
        << "Cursor: Area " << cur_area
        << " of " << workareas::occupied_desc()
        << " ... Table " << table_name
        << " ... Physical Recno " << recno
        << ", Logical Row " << logical_row
        << "\n";
}