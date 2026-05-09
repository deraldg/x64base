// @dottalk.usage v1
// owner: DOT|GPS
// command: GPS
// category: report
// status: supported
// noargs: report
// effect: report
// mutates: cursor
// usage-access: GPS USAGE
// summary:
//   Report current work-area position, including area slot, table label,
//   physical record number, and computed logical row.
//
// usage:
//   GPS
//   GPS USAGE
//
// notes:
//   GPS with no arguments reports cursor position.
//   GPS with no open table reports the current area and no-table state.
//   GPS computes logical row by iterating visible ordered records.
//   GPS is read-only for table data but may temporarily move the cursor while computing logical row.
//
// risk:
//   reads_table_records: yes when table is open
//   mutates_cursor: temporary during logical-row computation
//   mutates_table_data: no
//
// related:
//   GOTO
//   SKIP
//   AREA
//   STATUS
//

#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "workareas.hpp"
#include "cli/order_iterator.hpp"


namespace {
static std::string gps_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string gps_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_gps_usage_request(const std::string& raw)
{
    std::string t = gps_upper(gps_trim(raw));
    if (t.rfind("GPS ", 0) == 0) {
        t = gps_upper(gps_trim(t.substr(4)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_gps_usage()
{
    std::cout
        << "Usage:\n"
        << "  GPS\n"
        << "  GPS USAGE\n"
        << "Notes:\n"
        << "  - Reports area slot, table label, physical recno, and logical row.\n"
        << "  - With no open table, GPS reports the no-table cursor state.\n";
}
} // namespace

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
void cmd_GPS(xbase::DbArea& current, std::istringstream& iss)
{
    const std::string raw_args = iss.str();
    if (is_gps_usage_request(raw_args)) {
        print_gps_usage();
        return;
    }

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