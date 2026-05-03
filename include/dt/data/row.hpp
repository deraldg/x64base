#pragma once

#include "dt/data/cell.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace dt::data {

// Origin/provenance for a row moving through the data-transfer layer.
// This stays adapter metadata only; DbArea remains the runtime/table truth.
enum class RowSource {
    Unknown,
    Dbf,
    Csv,
    Fixed,
    Sql,
    Tuple,
    Generated
};

struct RowOrigin {
    RowSource source { RowSource::Unknown };

    // Optional provenance. Fill only what the producing codec knows.
    std::string path;      // source file/database path, if applicable
    std::string table;     // DBF/table/logical source name, if applicable
    std::string sheet;     // spreadsheet/worksheet name, if applicable

    // DBF / tuple provenance.
    // area_id is preserved for existing codecs.
    // area_slot is the newer tuple-facing spelling.
    // Keep both for now; do not force old codec code to change during this drop-in.
    int area_id   { -1 };
    int area_slot { -1 };

    int recno     { 0 };   // physical DBF recno when known; 0 = unknown/not applicable
    bool deleted  { false };

    // Text/CSV/fixed-width provenance.
    std::size_t line_no { 0 }; // 1-based line number when known; 0 = unknown
};

struct Row {
    RowOrigin origin;
    std::vector<Cell> cells;

    [[nodiscard]] bool empty() const noexcept { return cells.empty(); }
    [[nodiscard]] std::size_t size() const noexcept { return cells.size(); }

    Cell& operator[](std::size_t i) { return cells[i]; }
    const Cell& operator[](std::size_t i) const { return cells[i]; }
};

} // namespace dt::data
