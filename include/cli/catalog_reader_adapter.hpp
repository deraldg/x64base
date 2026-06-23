#pragma once
/*
  DotTalk++ Catalog Reader Adapter v1

  Doctrine:
    DotTalk++ proves and opens database tables through its own runtime surface:
      USE, WORKSPACE OPEN DBF, SELECT, FIELDS, LIST, COUNT, etc.

    The catalog reader consumes an already-open SYSCMD area. It does not
    directly open SYSCMD.dbf, does not manage companion files, does not perform
    path resolution, and does not compete with USE/WORKSPACE.
*/

#include <optional>
#include <string>
#include <vector>

namespace xbase {
class DbArea;
}

namespace dottalk::metadata {

struct CatalogCommandRow {
    std::string command_id;
    std::string canonical_name;
    std::string kind;
    std::string visibility;
    std::string handler;
    bool active = false;
};

struct CatalogDiagnostic {
    std::string severity;
    std::string code;
    std::string message;
    std::string row_key;
};

struct CatalogReaderOptions {
    // Retained for compatibility. The preferred boundary is area-first:
    // load_commands_from_area(xbase::DbArea&).
    //
    // load_commands(options) must not directly open SYSCMD.dbf. It may later be
    // wired to resolve an already-open area or to call a shared USE/WORKSPACE
    // helper once that helper exists.
    std::string metadata_dbf_root;
    bool strict = false;
};

struct CatalogLoadResult {
    std::vector<CatalogCommandRow> rows;
    std::vector<CatalogDiagnostic> diagnostics;

    bool ok() const;
};

// Primary area-first boundary.
// Caller supplies a SYSCMD table already opened/proven by DotTalk++.
CatalogLoadResult load_commands_from_area(xbase::DbArea& syscmd_area);

// Compatibility placeholder.
// Must not directly open DBFs. Remains not-wired until it can use a shared
// USE/WORKSPACE helper or resolve an already-open SYSCMD area.
CatalogLoadResult load_commands(const CatalogReaderOptions& options);

std::vector<CatalogCommandRow>
list_active_commands(const std::vector<CatalogCommandRow>& rows);

std::vector<CatalogCommandRow>
list_by_type(const std::vector<CatalogCommandRow>& rows, const std::string& kind);

std::optional<CatalogCommandRow>
find_by_canonical_name(const std::vector<CatalogCommandRow>& rows,
                       const std::string& canonical_name);

std::optional<CatalogCommandRow>
find_by_command_id(const std::vector<CatalogCommandRow>& rows,
                   const std::string& command_id);

std::vector<CatalogCommandRow>
find_by_handler(const std::vector<CatalogCommandRow>& rows,
                const std::string& handler);

std::vector<CatalogDiagnostic>
produce_readonly_diagnostics(const std::vector<CatalogCommandRow>& rows);

} // namespace dottalk::metadata
