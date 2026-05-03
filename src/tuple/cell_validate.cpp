#include "dt/data/cell_validate.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <sstream>
#include <string>

namespace dt::data {
namespace {

std::string trim(std::string s) {
    auto issp = [](unsigned char c) { return std::isspace(c) != 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [&](unsigned char c) { return !issp(c); }));
    s.erase(std::find_if(s.rbegin(), s.rend(), [&](unsigned char c) { return !issp(c); }).base(), s.end());
    return s;
}

std::string up(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

bool parse_double_strict(const std::string& s, double& out) {
    const std::string t = trim(s);
    if (t.empty()) return false;

    char* end = nullptr;
    out = std::strtod(t.c_str(), &end);
    if (end == t.c_str()) return false;
    while (end && *end) {
        if (!std::isspace(static_cast<unsigned char>(*end))) return false;
        ++end;
    }
    return true;
}

bool parse_int64_strict(const std::string& s, std::int64_t& out) {
    const std::string t = trim(s);
    if (t.empty()) return false;

    char* end = nullptr;
    out = std::strtoll(t.c_str(), &end, 10);
    if (end == t.c_str()) return false;
    while (end && *end) {
        if (!std::isspace(static_cast<unsigned char>(*end))) return false;
        ++end;
    }
    return true;
}

bool parse_bool(const std::string& s, bool& out) {
    const std::string t = up(trim(s));
    if (t.empty()) return false;

    if (t == "T" || t == ".T." || t == "TRUE" || t == "Y" || t == "YES" || t == "1") {
        out = true;
        return true;
    }
    if (t == "F" || t == ".F." || t == "FALSE" || t == "N" || t == "NO" || t == "0") {
        out = false;
        return true;
    }
    return false;
}

bool all_digits(const std::string& s) {
    return !s.empty() && std::all_of(s.begin(), s.end(), [](unsigned char c) { return std::isdigit(c) != 0; });
}

bool parse_date(const std::string& s, DateYMD& out) {
    std::string t = trim(s);
    if (t.empty()) return false;

    if (t.size() == 8 && all_digits(t)) {
        out.year  = std::stoi(t.substr(0, 4));
        out.month = std::stoi(t.substr(4, 2));
        out.day   = std::stoi(t.substr(6, 2));
        return out.is_valid();
    }

    if (t.size() == 10 && t[4] == '-' && t[7] == '-') {
        const std::string y = t.substr(0, 4);
        const std::string m = t.substr(5, 2);
        const std::string d = t.substr(8, 2);
        if (!all_digits(y) || !all_digits(m) || !all_digits(d)) return false;
        out.year  = std::stoi(y);
        out.month = std::stoi(m);
        out.day   = std::stoi(d);
        return out.is_valid();
    }

    return false;
}

int decimal_places_in_text(const std::string& s) {
    const std::string t = trim(s);
    const auto p = t.find('.');
    if (p == std::string::npos) return 0;

    int n = 0;
    for (std::size_t i = p + 1; i < t.size(); ++i) {
        const unsigned char c = static_cast<unsigned char>(t[i]);
        if (std::isdigit(c)) ++n;
        else break;
    }
    return n;
}

std::string cell_label(const Cell& c) {
    if (!c.field_name.empty()) return c.field_name;
    return "<cell>";
}

void fail(Cell& cell, const std::string& msg, std::string* error_out) {
    cell.valid = false;
    cell.error = msg;
    if (error_out) *error_out = msg;
}

void pass(Cell& cell, std::string* error_out) {
    cell.valid = true;
    cell.error.clear();
    if (error_out) error_out->clear();
}

} // namespace

bool validate_cell(Cell& cell, std::string* error_out) {
    const std::string raw_trimmed = trim(cell.raw);
    cell.has_value = !raw_trimmed.empty();

    // Blank DBF field values are acceptable at this layer.
    if (!cell.has_value) {
        cell.value = std::monostate{};
        pass(cell, error_out);
        return true;
    }

    switch (cell.type) {
        case CellType::Character:
        case CellType::Memo:
        case CellType::Blob:
        case CellType::DateTime:
        case CellType::Unknown: {
            if (cell.width > 0 && cell.type == CellType::Character &&
                static_cast<int>(cell.raw.size()) > cell.width) {
                std::ostringstream oss;
                oss << cell_label(cell) << " exceeds width " << cell.width;
                fail(cell, oss.str(), error_out);
                return false;
            }
            cell.value = cell.raw;
            pass(cell, error_out);
            return true;
        }

        case CellType::Numeric:
        case CellType::Currency: {
            double v = 0.0;
            if (!parse_double_strict(cell.raw, v)) {
                fail(cell, cell_label(cell) + " is not a valid numeric value", error_out);
                return false;
            }
            if (cell.width > 0 && static_cast<int>(raw_trimmed.size()) > cell.width) {
                std::ostringstream oss;
                oss << cell_label(cell) << " exceeds numeric width " << cell.width;
                fail(cell, oss.str(), error_out);
                return false;
            }
            if (cell.decimals >= 0 && decimal_places_in_text(cell.raw) > cell.decimals) {
                std::ostringstream oss;
                oss << cell_label(cell) << " exceeds decimal count " << cell.decimals;
                fail(cell, oss.str(), error_out);
                return false;
            }
            cell.value = v;
            pass(cell, error_out);
            return true;
        }

        case CellType::Integer: {
            std::int64_t v = 0;
            if (!parse_int64_strict(cell.raw, v)) {
                fail(cell, cell_label(cell) + " is not a valid integer value", error_out);
                return false;
            }
            if (cell.width > 0 && static_cast<int>(raw_trimmed.size()) > cell.width) {
                std::ostringstream oss;
                oss << cell_label(cell) << " exceeds integer width " << cell.width;
                fail(cell, oss.str(), error_out);
                return false;
            }
            cell.value = v;
            pass(cell, error_out);
            return true;
        }

        case CellType::Date: {
            DateYMD d{};
            if (!parse_date(cell.raw, d)) {
                fail(cell, cell_label(cell) + " is not a valid date", error_out);
                return false;
            }
            cell.value = d;
            pass(cell, error_out);
            return true;
        }

        case CellType::Logical: {
            bool b = false;
            if (!parse_bool(cell.raw, b)) {
                fail(cell, cell_label(cell) + " is not a valid logical value", error_out);
                return false;
            }
            cell.value = b;
            pass(cell, error_out);
            return true;
        }
    }

    fail(cell, cell_label(cell) + " has unsupported cell type", error_out);
    return false;
}

bool validate_row(Row& row, RowErrorSummary& summary) {
    summary = RowErrorSummary{};

    for (auto& cell : row.cells) {
        std::string err;
        if (!validate_cell(cell, &err)) {
            summary.ok = false;
            ++summary.invalid_cells;
            if (summary.first_error.empty()) summary.first_error = err;
        }
    }

    return summary.ok;
}

RowErrorSummary summarize_row_errors(const Row& row) {
    Row copy = row;
    RowErrorSummary summary;
    (void)validate_row(copy, summary);
    return summary;
}

} // namespace dt::data
