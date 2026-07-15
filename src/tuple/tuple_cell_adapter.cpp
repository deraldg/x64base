#include "tuple/tuple_cell_adapter.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>

#include "dt/data/cell_validate.hpp"
#include "workareas.hpp"

namespace dottalk::tupleaugment {
namespace {

std::string up(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

bool area_is_open(const xbase::DbArea* a) {
    if (!a) return false;
    try { return a->isOpen(); } catch (...) { return false; }
}

const xbase::DbArea* area_for_slot(int slot, const xbase::DbArea* fallback_area) {
    if (slot >= 0) {
        try {
            const auto idx = static_cast<std::size_t>(slot);
            if (idx < workareas::count()) {
                const xbase::DbArea* a = workareas::db(idx);
                if (area_is_open(a)) return a;
            }
        } catch (...) {}
    }
    return area_is_open(fallback_area) ? fallback_area : nullptr;
}

int recno_for_area(const xbase::DbArea* area) {
    if (!area) return 0;
    try { return static_cast<int>(area->recno()); } catch (...) { return 0; }
}

std::string table_name_for_area(const xbase::DbArea* area) {
    if (!area) return {};
    try {
        const std::string logical = area->logicalName();
        if (!logical.empty()) return logical;
    } catch (...) {}
    try {
        const std::string base = area->dbfBasename();
        if (!base.empty()) return base;
    } catch (...) {}
    try { return area->name(); } catch (...) {}
    return {};
}

int fragment_recno_for_slot(const dottalk::TupleRow& tuple, int slot) {
    for (const auto& f : tuple.fragments) {
        if (f.area_slot == slot && f.recno > 0) return f.recno;
    }
    for (const auto& f : tuple.fragments) {
        if (f.recno > 0) return f.recno;
    }
    return 0;
}

dt::data::CellType cell_type_from_dbf(char t) {
    switch (static_cast<char>(std::toupper(static_cast<unsigned char>(t)))) {
        case 'C': return dt::data::CellType::Character;
        case 'N': return dt::data::CellType::Numeric;
        case 'F': return dt::data::CellType::Numeric;
        case 'B': return dt::data::CellType::Numeric;
        case 'Y': return dt::data::CellType::Currency;
        case 'I': return dt::data::CellType::Integer;
        case 'D': return dt::data::CellType::Date;
        case 'T': return dt::data::CellType::DateTime;
        case 'L': return dt::data::CellType::Logical;
        case 'M': return dt::data::CellType::Memo;
        case 'G': return dt::data::CellType::Blob;
        case 'P': return dt::data::CellType::Blob;
        default:  return dt::data::CellType::Unknown;
    }
}

struct FieldLookupResult {
    bool found = false;
    int field1 = -1;
    char type = 0;
    int width = 0;
    int decimals = 0;
    std::string canonical_name;
};

FieldLookupResult lookup_field(const xbase::DbArea* area, const std::string& field_name) {
    FieldLookupResult r;
    if (!area_is_open(area)) return r;

    const std::string want = up(field_name);
    try {
        const auto& fields = area->fields();
        for (std::size_t i = 0; i < fields.size(); ++i) {
            const auto& f = fields[i];
            if (up(f.name) != want) continue;

            r.found = true;
            r.field1 = static_cast<int>(i) + 1;
            r.type = f.type;
            r.width = static_cast<int>(f.length);
            r.decimals = static_cast<int>(f.decimals);
            r.canonical_name = f.name;
            return r;
        }
    } catch (...) {}

    return r;
}

} // namespace

TupleCellAdapterResult cells_from_tuple_row(
    const dottalk::TupleRow& tuple,
    const xbase::DbArea* fallback_area,
    const TupleCellAdapterOptions& options
) {
    TupleCellAdapterResult result;

    if (!tuple.aligned()) {
        result.ok = false;
        result.error = "TUPVALIDATE: tuple row is not column/value aligned";
        return result;
    }

    result.row.cells.reserve(tuple.values.size());

    for (std::size_t i = 0; i < tuple.values.size(); ++i) {
        const auto& col = tuple.columns[i];
        const std::string& raw = tuple.values[i];

        const xbase::DbArea* area = area_for_slot(col.area_slot, fallback_area);
        const FieldLookupResult fld = lookup_field(area, col.field.empty() ? col.name : col.field);

        dt::data::Cell cell;
        cell.origin = dt::data::CellOrigin::Field;
        cell.area_slot = col.area_slot;
        cell.recno = fragment_recno_for_slot(tuple, col.area_slot);
        if (cell.recno <= 0) cell.recno = recno_for_area(area);
        cell.table_name = table_name_for_area(area);
        cell.field_name = fld.found ? fld.canonical_name : (col.field.empty() ? col.name : col.field);
        cell.field_index = fld.field1;
        cell.dbf_type = fld.type;
        cell.type = fld.found ? cell_type_from_dbf(fld.type) : dt::data::CellType::Unknown;
        cell.width = fld.width;
        cell.decimals = fld.decimals;
        cell.raw = raw;

        if (options.validate_cells) {
            std::string err;
            (void)dt::data::validate_cell(cell, &err);
        }

        result.row.cells.push_back(std::move(cell));
    }

    return result;
}

} // namespace dottalk::tupleaugment
