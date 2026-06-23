/*
  DotTalk++ Catalog Reader Adapter v1

  Area-first implementation stage:
    - load_commands_from_area reads an already-open SYSCMD area
    - load_commands(options) remains NOT_WIRED and does not directly open DBFs
    - helper/query operations remain read-only

  Boundary:
    USE / WORKSPACE own path resolution, companion files, table flavor,
    indexes, and workspace opening doctrine. This adapter normalizes catalog
    rows from a table DotTalk++ already opened/proved.
*/

#include "cli/catalog_reader_adapter.hpp"
#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <cstddef>
#include <string>
#include <utility>
#include <vector>

namespace dottalk::metadata {
namespace {

std::string upper_ascii(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(),
                   [](unsigned char ch) {
                       return static_cast<char>(std::toupper(ch));
                   });
    return value;
}

bool iequals_ascii(const std::string& a, const std::string& b) {
    return upper_ascii(a) == upper_ascii(b);
}

std::string trim_ascii(std::string value) {
    auto is_space = [](unsigned char ch) {
        return std::isspace(ch) != 0;
    };

    while (!value.empty() && is_space(static_cast<unsigned char>(value.front()))) {
        value.erase(value.begin());
    }
    while (!value.empty() && is_space(static_cast<unsigned char>(value.back()))) {
        value.pop_back();
    }
    return value;
}

bool parse_logical_true(const std::string& raw) {
    const std::string v = upper_ascii(trim_ascii(raw));
    return v == "T" || v == "Y" || v == "1" || v == "TRUE";
}

void add_diag(std::vector<CatalogDiagnostic>& diagnostics,
              std::string severity,
              std::string code,
              std::string message,
              std::string row_key = {}) {
    diagnostics.push_back({
        std::move(severity),
        std::move(code),
        std::move(message),
        std::move(row_key)
    });
}

int find_field_index_ci(const xbase::DbArea& area, const std::string& name) {
    const auto& fields = area.fields();
    for (std::size_t i = 0; i < fields.size(); ++i) {
        if (iequals_ascii(fields[i].name, name)) {
            return static_cast<int>(i + 1); // DbArea::get is 1-based.
        }
    }
    return 0;
}

void require_field(std::vector<CatalogDiagnostic>& diagnostics,
                   int field_index,
                   const std::string& field_name) {
    if (field_index <= 0) {
        add_diag(diagnostics,
                 "ERROR",
                 "CATALOG_REQUIRED_FIELD_MISSING",
                 "SYSCMD required field is missing: " + field_name,
                 "SYSCMD");
    }
}

void diagnose_row(const CatalogCommandRow& row,
                  std::vector<CatalogDiagnostic>& diagnostics,
                  const std::string& row_key) {
    if (row.command_id.empty()) {
        add_diag(diagnostics,
                 "WARN",
                 "CATALOG_ROW_EMPTY_COMMAND_ID",
                 "Catalog row has an empty command_id.",
                 row_key);
    }
    if (row.canonical_name.empty()) {
        add_diag(diagnostics,
                 "WARN",
                 "CATALOG_ROW_EMPTY_CANONICAL_NAME",
                 "Catalog row has an empty canonical_name.",
                 row_key);
    }
    if (row.kind.empty()) {
        add_diag(diagnostics,
                 "WARN",
                 "CATALOG_ROW_EMPTY_KIND",
                 "Catalog row has an empty kind.",
                 row_key);
    }
    if (row.visibility.empty()) {
        add_diag(diagnostics,
                 "WARN",
                 "CATALOG_ROW_EMPTY_VISIBILITY",
                 "Catalog row has an empty visibility.",
                 row_key);
    }
    if (row.handler.empty()) {
        add_diag(diagnostics,
                 "WARN",
                 "CATALOG_ROW_EMPTY_HANDLER",
                 "Catalog row has an empty handler.",
                 row_key);
    }
    if (!row.active) {
        add_diag(diagnostics,
                 "INFO",
                 "CATALOG_ROW_INACTIVE",
                 "Catalog row is inactive.",
                 row_key);
    }
}

} // namespace

bool CatalogLoadResult::ok() const {
    for (const auto& diagnostic : diagnostics) {
        if (iequals_ascii(diagnostic.severity, "ERROR")) {
            return false;
        }
    }
    return true;
}

CatalogLoadResult load_commands_from_area(xbase::DbArea& syscmd_area) {
    CatalogLoadResult result;

    const int idx_cmd_id = find_field_index_ci(syscmd_area, "CMD_ID");
    const int idx_can_name = find_field_index_ci(syscmd_area, "CAN_NAME");
    const int idx_type = find_field_index_ci(syscmd_area, "TYPE");
    const int idx_vis = find_field_index_ci(syscmd_area, "VIS");
    const int idx_handler = find_field_index_ci(syscmd_area, "HANDLER");
    const int idx_active = find_field_index_ci(syscmd_area, "ACTIVE");

    require_field(result.diagnostics, idx_cmd_id, "CMD_ID");
    require_field(result.diagnostics, idx_can_name, "CAN_NAME");
    require_field(result.diagnostics, idx_type, "TYPE");
    require_field(result.diagnostics, idx_vis, "VIS");
    require_field(result.diagnostics, idx_handler, "HANDLER");
    require_field(result.diagnostics, idx_active, "ACTIVE");

    if (!result.ok()) {
        return result;
    }

    const auto record_count = syscmd_area.recCount();
    if (record_count <= 0) {
        add_diag(result.diagnostics,
                 "WARN",
                 "CATALOG_SYSCMD_EMPTY",
                 "SYSCMD contains zero records.",
                 "SYSCMD");
        return result;
    }

    result.rows.reserve(static_cast<std::size_t>(record_count));

    // Area-first note:
    // This function reads an already-open area and uses gotoRec(rec), which
    // moves that area's cursor. If a caller must preserve an interactive cursor,
    // pass a scratch/read-only area or add a reviewed save/restore wrapper using
    // the project's public cursor API.
    for (int rec = 1; rec <= record_count; ++rec) {
        syscmd_area.gotoRec(rec);

        if (syscmd_area.isDeleted()) {
            add_diag(result.diagnostics,
                     "INFO",
                     "CATALOG_SYSCMD_DELETED_ROW_SKIPPED",
                     "Deleted SYSCMD row skipped.",
                     std::to_string(rec));
            continue;
        }

        CatalogCommandRow row;
        row.command_id = trim_ascii(syscmd_area.get(idx_cmd_id));
        row.canonical_name = trim_ascii(syscmd_area.get(idx_can_name));
        row.kind = trim_ascii(syscmd_area.get(idx_type));
        row.visibility = trim_ascii(syscmd_area.get(idx_vis));
        row.handler = trim_ascii(syscmd_area.get(idx_handler));
        row.active = parse_logical_true(syscmd_area.get(idx_active));

        const std::string row_key =
            !row.command_id.empty() ? row.command_id :
            (!row.canonical_name.empty() ? row.canonical_name : std::to_string(rec));

        diagnose_row(row, result.diagnostics, row_key);
        result.rows.push_back(std::move(row));
    }

    return result;
}

CatalogLoadResult load_commands(const CatalogReaderOptions& options) {
    CatalogLoadResult result;
    (void)options;

    add_diag(result.diagnostics,
             "INFO",
             "CATALOG_READER_REQUIRES_RUNTIME_AREA",
             "load_commands is not wired to open SYSCMD directly. Use load_commands_from_area on a DotTalk++-opened SYSCMD area, or wire this through the shared USE/WORKSPACE open helper.",
             "SYSCMD");

    return result;
}

std::vector<CatalogCommandRow>
list_active_commands(const std::vector<CatalogCommandRow>& rows) {
    std::vector<CatalogCommandRow> out;
    out.reserve(rows.size());
    for (const auto& row : rows) {
        if (row.active) {
            out.push_back(row);
        }
    }
    return out;
}

std::vector<CatalogCommandRow>
list_by_type(const std::vector<CatalogCommandRow>& rows, const std::string& kind) {
    std::vector<CatalogCommandRow> out;
    for (const auto& row : rows) {
        if (iequals_ascii(row.kind, kind)) {
            out.push_back(row);
        }
    }
    return out;
}

std::optional<CatalogCommandRow>
find_by_canonical_name(const std::vector<CatalogCommandRow>& rows,
                       const std::string& canonical_name) {
    for (const auto& row : rows) {
        if (iequals_ascii(row.canonical_name, canonical_name)) {
            return row;
        }
    }
    return std::nullopt;
}

std::optional<CatalogCommandRow>
find_by_command_id(const std::vector<CatalogCommandRow>& rows,
                   const std::string& command_id) {
    for (const auto& row : rows) {
        if (iequals_ascii(row.command_id, command_id)) {
            return row;
        }
    }
    return std::nullopt;
}

std::vector<CatalogCommandRow>
find_by_handler(const std::vector<CatalogCommandRow>& rows,
                const std::string& handler) {
    std::vector<CatalogCommandRow> out;
    for (const auto& row : rows) {
        if (iequals_ascii(row.handler, handler)) {
            out.push_back(row);
        }
    }
    return out;
}

std::vector<CatalogDiagnostic>
produce_readonly_diagnostics(const std::vector<CatalogCommandRow>& rows) {
    std::vector<CatalogDiagnostic> diagnostics;

    if (rows.empty()) {
        add_diag(diagnostics,
                 "WARN",
                 "CATALOG_EMPTY",
                 "Catalog reader adapter saw zero command rows.",
                 "");
        return diagnostics;
    }

    for (const auto& row : rows) {
        const std::string key =
            row.command_id.empty() ? row.canonical_name : row.command_id;

        diagnose_row(row, diagnostics, key);
    }

    return diagnostics;
}

} // namespace dottalk::metadata
