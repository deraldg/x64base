// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported


// include/xindex/cli_bridge.hpp  (patched)
#pragma once

#include <string>

namespace xbase { class DbArea; }

namespace xindex_cli {

// Returns true if a logical order (index) is currently active for A.
bool db_index_attached(const xbase::DbArea& A);

// User-facing name/path for the active index (container or single index).
// e.g., "STUDENTS.inx", "lname.inx". Empty if none.
std::string db_index_path(const xbase::DbArea& A);

// New: when using a CNX container, returns the active tag name (UPPERCASED).
// Empty if none or not CNX.
std::string db_active_cnx_tag(const xbase::DbArea& A);

// New: current order direction (ASC if true).
bool db_order_asc(const xbase::DbArea& A);

// Is the area traversed in NATURAL (physical) order?
//
// AIF-148.  db_index_attached() above answers IS A CONTAINER ATTACHED, and
// callers that needed to know WHICH ORDER THE CURSOR FOLLOWS had no bridge
// function to ask -- so orderdisplay::summarize() printed the DIRECTION flag
// as the order and BROWSE reported ASCEND for a table in natural order.  The
// two questions are different and both bridge functions have to exist, for
// the same reason orderstate:: carries both hasOrder() and isNaturalOrder().
bool db_order_is_natural(const xbase::DbArea& A);

} // namespace xindex_cli

// ---- DbArea adapters (already present in your repo) ----
namespace xindex {
    int         db_select      (int n);
    int         db_area        ();
    int         db_record_count(const xbase::DbArea&);
    int         db_recno       (const xbase::DbArea&);
    std::string db_get_string  (const xbase::DbArea&, int recno, const std::string& field);
    double      db_get_double  (const xbase::DbArea&, int recno, const std::string& field);
    bool        db_is_deleted  (const xbase::DbArea&, int recno);

    // Always-on optional adapters:
    std::string db_filename    (const xbase::DbArea&);  // "" if unknown
    int         db_record_length(const xbase::DbArea&); // -1 if unknown
}

// Map to your DbArea methods now that they return real values.
#pragma once
#define XINDEX_DB_FILENAME(a)        ((a).filename())
#define XINDEX_DB_RECORD_LENGTH(a)   ((a).recordLength())



