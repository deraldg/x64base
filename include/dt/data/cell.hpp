#pragma once

#include <cstdint>
#include <string>
#include <variant>

namespace dt::data {

// Logical type for a single interpreted value.
enum class CellType {
    Character,
    Numeric,
    Date,
    DateTime,
    Logical,
    Memo,
    Blob,
    Currency,
    Integer,
    Unknown
};

// Where the cell conceptually came from.
enum class CellOrigin {
    Field,      // Direct DBF field
    Computed,   // Expression/computed value
    Temp,       // Temporary variable / scratch
    Parameter   // Command parameter / argument
};

// Simple YYYY-MM-DD representation for DBF-style dates.
struct DateYMD {
    std::int32_t year  {0};
    std::int32_t month {0};
    std::int32_t day   {0};

    [[nodiscard]] bool is_valid() const noexcept {
        if (year == 0 || month < 1 || month > 12 || day < 1) return false;
        static constexpr int days_by_month[12] = {
            31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
        };
        int max_day = days_by_month[month - 1];
        const bool leap = ((year % 4 == 0) && (year % 100 != 0)) || (year % 400 == 0);
        if (month == 2 && leap) max_day = 29;
        return day <= max_day;
    }
};

// Underlying value carried by a Cell.
using CellValue = std::variant<
    std::monostate,   // no value / blank / uninitialized
    std::string,      // character, memo ref/display, datetime text, blob marker
    double,           // numeric, float, double, currency-as-double for now
    std::int64_t,     // integer/autokey-style value
    DateYMD,          // DBF date
    bool              // logical
>;

// Value object representing one field instance interpreted from tuple output.
struct Cell {
    CellType   type      { CellType::Unknown };
    CellOrigin origin    { CellOrigin::Field };

    // Identity / provenance
    std::string table_name;       // optional display/debug table name
    std::string field_name;       // resolved runtime field name
    int         area_slot   { -1 };// owning work area, if known
    int         recno       { 0 }; // 1-based physical recno, if known
    int         field_index { -1 };// 1-based DBF field index; -1 if unknown
    char        dbf_type    { 0 }; // raw DBF field type when known

    // Raw and parsed value
    std::string raw;              // tuple/display text before parsing
    CellValue   value;            // parsed/typed representation
    bool        has_value { false };

    // DBF formatting constraints
    int         width       { 0 };
    int         decimals    { 0 };
    bool        pad_right   { true };
    std::string format_mask;

    // State / validation
    bool        dirty       { false };
    bool        valid       { true };
    std::string error;
};

} // namespace dt::data
