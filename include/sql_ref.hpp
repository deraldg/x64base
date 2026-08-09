// @dottalk.file v1
// subsystem: include
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// sql_ref.hpp
#pragma once
#include <string>
#include <vector>
#include <string_view>
#include <set>
#include <algorithm>

namespace sqlref {

struct Item {
    const char* name;       // e.g. "CREATE-TABLE", "CREATE-INDEX"
    const char* syntax;     // main syntax line
    const char* summary;    // short description
    const char* category;   // grouping: "DDL", "DML", "Indexing", etc.
    bool portable;          // true = mostly same in SQLite + MSSQL

    // x64base CONFORMANCE (AIF-074, 2026-07-29).
    //
    // What this field answers: "I know this SQL construct -- does x64base do it,
    // and by what command?" It turns this catalog from a reference for OTHER
    // engines into an honest map of our own coverage, gaps included.
    //
    // RULE, and it is the point of the field: NEVER restate a command's grammar
    // here. Name the command and point at its USAGE. Grammar copied into a second
    // place drifts from the first -- that failure was found four separate times in
    // this file's own lane on the day the field was added. One sentence, one
    // pointer, no duplication.
    //
    // Conventions:
    //   ""                 = NOT YET MAPPED (nobody has checked; not a claim of absence)
    //   "NOT SUPPORTED..." = verified absent, with the reason or the phase that adds it
    //   otherwise          = the command(s) that do this, plus any honest caveat
    //
    // Anything asserted here should be runtime-observed or read from a contract,
    // not assumed. Empty is always safer than wrong.
    const char* x64 = "";
};

inline const std::vector<Item>& catalog() {
    static const std::vector<Item> items = {
        // ────────────────────────────────────────────────
        // DDL - Data Definition Language
        // ────────────────────────────────────────────────
        {"CREATE-TABLE",
         "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE);",
         "Create table with columns, constraints, primary key", "DDL", true,
         "EQUIVALENT, different syntax -- CREATE X64 <name> (<field> <type>(<len>[,<dec>]), ...) "
         "for the interactive form, or DDL CREATE DBF ... FROM <schema.json> to build from a "
         "schema file. xBase types are C/N/D/L/M, not SQL types. No AUTOINCREMENT: identity "
         "columns are not a storage feature here. See CREATE USAGE and DDL USAGE."},
        {"CREATE-TABLE-MSSQL",
         "CREATE TABLE users (id INT IDENTITY(1,1) PRIMARY KEY, name NVARCHAR(100) NOT NULL, email NVARCHAR(255) UNIQUE);",
         "MSSQL version using IDENTITY", "DDL", false,
         "N/A -- dialect variant of CREATE-TABLE; see that entry. Table FLAVOR in x64base "
         "(MSDOS/DBASE/FOX26/FOXPRO/VFP/X64) is a storage-format choice, not a SQL dialect."},
        {"CREATE-INDEX",
         "CREATE INDEX idx_users_email ON users (email);",
         "Single-column index for faster lookups", "Indexing", true,
         "EQUIVALENT, different syntax and a second step -- INDEX ON <field> TAG <name> "
         "declares the tag; BUILDLMDB builds the actual LMDB store behind it. The CDX "
         "container holds tag metadata only. Attach with SET INDEX TO, choose with "
         "SET ORDER TO TAG. See INDEX USAGE and CDX USAGE."},
        {"CREATE-UNIQUE-INDEX", 
         "CREATE UNIQUE INDEX idx_users_email ON users (email);", 
         "Unique index – prevents duplicates", "Indexing", true},
        {"CREATE-COMPOSITE-INDEX", 
         "CREATE INDEX idx_orders_user_date ON orders (user_id, order_date);", 
         "Multi-column index (WHERE + ORDER BY)", "Indexing", true},
        {"DROP-TABLE", 
         "DROP TABLE IF EXISTS users;", 
         "Delete table (IF EXISTS is safe)", "DDL", true},
        {"DROP-INDEX", 
         "DROP INDEX idx_users_email;", 
         "Remove index", "Indexing", true},
        {"ALTER-TABLE-ADD", 
         "ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active';", 
         "Add new column (SQLite ALTER is limited)", "DDL", false},

        // ────────────────────────────────────────────────
        // DML - Data Manipulation Language
        // ────────────────────────────────────────────────
        {"INSERT",
         "INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');",
         "Insert single row", "DML", true,
         "EQUIVALENT, two steps -- APPEND adds a record and positions on it, then "
         "REPLACE <field> WITH <value> fills each field. Cursor-oriented rather than "
         "set-oriented: you land on the new row. SQL INSERT syntax is not accepted "
         "(planned, phase P5). See APPEND USAGE and REPLACE USAGE."},
        {"INSERT-MULTI",
         "INSERT INTO users (name, email) VALUES ('Bob','bob@ex.com'), ('Charlie','charlie@ex.com');",
         "Insert multiple rows", "DML", true,
         "NOT SUPPORTED as one statement. Repeat the APPEND/REPLACE pair, or script it. "
         "Under TABLE BUFFER ON the whole batch commits or rolls back together, which "
         "recovers the atomicity a multi-row INSERT would give you."},
        {"UPDATE",
         "UPDATE users SET status = 'active' WHERE id = 5;",
         "Update matching rows", "DML", true,
         "EQUIVALENT, different shape -- REPLACE <field> WITH <value> acts on the CURRENT "
         "record; scope it across rows with a FOR predicate. SQL UPDATE syntax is not "
         "accepted (planned, phase P5). Buffered when TABLE BUFFER is ON. See REPLACE USAGE."},
        {"DELETE",
         "DELETE FROM users WHERE id = 42;",
         "Delete matching rows", "DML", true,
         "EQUIVALENT, with a real semantic difference -- DELETE only MARKS a record "
         "deleted, and RECALL un-marks it; the row stays until PACK removes it. SET DELETED "
         "controls whether marked rows are visible to scans. SQL DELETE is immediate and "
         "has no undo; this is closer to a soft delete. See DELETE USAGE and RECALL USAGE."},
        {"TRUNCATE", 
         "TRUNCATE TABLE users;", 
         "Remove all rows quickly (MSSQL only)", "DML", false},

        // ────────────────────────────────────────────────
        // Querying & Filtering
        // ────────────────────────────────────────────────
        {"SELECT-BASIC",
         "SELECT name, email FROM users WHERE age > 30 ORDER BY name LIMIT 10;",
         "Basic query with WHERE, ORDER, LIMIT", "Query", true,
         "SUPPORTED -- SQLsel. The table must already be OPEN (USE <table>). Bare "
         "column names only in v1: no expression projection. See SQLSEL USAGE."},
        {"SELECT-COUNT",
         "SELECT COUNT(*) FROM users WHERE status = 'active';",
         "Count matching rows", "Query", true,
         "SUPPORTED -- SQLsel, with or without WHERE. See SQLSEL USAGE."},
        {"SELECT-GROUP",
         "SELECT department, AVG(salary) FROM employees GROUP BY department HAVING COUNT(*) > 5;",
         "Aggregate + GROUP BY + HAVING", "Query", true,
         "NOT SUPPORTED. No GROUP BY or HAVING anywhere in the engine. AGGS "
         "(SUM/AVG/MIN/MAX) aggregates a whole scope with an optional FOR predicate, "
         "so it answers 'average salary where dept=X' one department at a time, but "
         "cannot partition a scan into groups in a single pass."},
        {"SELECT-JOIN-INNER",
         "SELECT u.name, o.product FROM users u INNER JOIN orders o ON u.id = o.user_id;",
         "Matching rows from both tables", "Join", true,
         "NOT SUPPORTED as SQL syntax (planned, phase P4). The engine reaches related "
         "data by DECLARED TRAVERSAL instead: REL ADD wires parent->child on a key, "
         "then TUPLE/SMARTBROWSER project across the graph. That is a different "
         "relational methodology, not a join -- it follows configured paths rather "
         "than matching two row sets, and it does not produce a joined result set."},
        {"SELECT-JOIN-LEFT",
         "SELECT u.name, o.product FROM users u LEFT JOIN orders o ON u.id = o.user_id;",
         "All left rows + matching right rows", "Join", true,
         "NOT SUPPORTED as SQL syntax (planned, phase P4). See SELECT-JOIN-INNER: "
         "REL traversal keeps the parent row regardless of child matches, which "
         "RESEMBLES a left join in effect, but outer-join semantics are not defined "
         "or tested here. Do not rely on the resemblance."},

        // ────────────────────────────────────────────────
        // Indexing & Optimization
        // ────────────────────────────────────────────────
        {"EXPLAIN-QUERY",
         "EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = 'alice@example.com';",
         "Show SQLite query plan / index usage", "Optimization", false,
         "PARTIAL -- there is no planner to explain, because there is no plan chooser: "
         "access paths are selected by the operator, not by a cost model. What exists is "
         "reporting. SQLsel names its access path on every ORDER BY (for example, whether "
         "it materialized a sort and over how many rows), and GPS shows physical recno "
         "against logical row so index traversal is directly observable."},
        {"ANALYZE", 
         "ANALYZE users;", 
         "Update statistics for better query planning", "Optimization", true},
        {"VACUUM", 
         "VACUUM;", 
         "Reclaim space after deletes (SQLite)", "Optimization", false},
        {"REINDEX", 
         "REINDEX idx_users_email;", 
         "Rebuild index after heavy updates", "Indexing", true},

        // ────────────────────────────────────────────────
        // Transactions & Safety
        // ────────────────────────────────────────────────
        {"BEGIN-TRAN",
         "BEGIN TRANSACTION;",
         "Start transaction", "Transaction", true,
         "EQUIVALENT -- TABLE BUFFER ON opens the buffered editing scope that COMMIT "
         "and ROLLBACK close. Per-area rather than per-connection. See TABLE BUFFER USAGE."},
        {"COMMIT",
         "COMMIT;",
         "Save changes", "Transaction", true,
         "SUPPORTED -- COMMIT. Write-ahead journal: the redo log and COMMIT marker are "
         "fsynced BEFORE any DBF byte moves, the commit aborts if that sync fails, and "
         "committed journals replay at USE. Index maintenance happens inside the same "
         "commit. See COMMIT USAGE."},
        {"ROLLBACK",
         "ROLLBACK;",
         "Undo changes", "Transaction", true,
         "SUPPORTED -- ROLLBACK discards the buffered changes and reports how many. "
         "See ROLLBACK USAGE."},

        // ────────────────────────────────────────────────
        // Date & String Functions
        // ────────────────────────────────────────────────
        {"DATE-NOW-SQLITE", 
         "SELECT DATE('now'), TIME('now'), DATETIME('now');", 
         "Current date/time (SQLite)", "Date", false},
        {"DATE-NOW-MSSQL", 
         "SELECT GETDATE();", 
         "Current date/time (MSSQL)", "Date", false},
        {"DATE-ADD-SQLITE", 
         "SELECT DATE('now', '+7 days');", 
         "Add days (SQLite)", "Date", false},
        {"DATE-ADD-MSSQL", 
         "SELECT DATEADD(DAY, 7, GETDATE());", 
         "Add days (MSSQL)", "Date", false},
        {"STRFTIME", 
         "SELECT STRFTIME('%Y-%m-%d', created_at) FROM logs;", 
         "Format date (SQLite)", "Date", false},
        {"FORMAT-MSSQL", 
         "SELECT FORMAT(created_at, 'yyyy-MM-dd') FROM logs;", 
         "Format date (MSSQL)", "Date", false},

        // ────────────────────────────────────────────────
        // Utility / Admin
        // ────────────────────────────────────────────────
        {"PRAGMA-SQLITE", 
         "PRAGMA table_info(users);", 
         "Show table structure (SQLite)", "Utility", false},
        {"SP-HELP-MSSQL", 
         "EXEC sp_help 'users';", 
         "Show table info (MSSQL)", "Utility", false},
    };
    return items;
}

// ────────────────────────────────────────────────
// Lookup helpers
// ────────────────────────────────────────────────

inline const Item* find(std::string_view name_upper) {
    for (const auto& item : catalog()) {
        if (std::string_view(item.name) == name_upper) return &item;
    }
    return nullptr;
}

inline std::vector<const Item*> search(std::string_view token_upper) {
    std::vector<const Item*> matches;
    std::string token(token_upper);
    std::transform(token.begin(), token.end(), token.begin(), ::toupper);

    for (const auto& item : catalog()) {
        std::string n(item.name);
        std::transform(n.begin(), n.end(), n.begin(), ::toupper);

        std::string cat = item.category ? item.category : "";
        std::transform(cat.begin(), cat.end(), cat.begin(), ::toupper);

        if (n.find(token) != std::string::npos ||
            (!cat.empty() && cat.find(token) != std::string::npos)) {
            matches.push_back(&item);
        }
    }
    return matches;
}

inline std::vector<std::string> categories() {
    std::vector<std::string> cats;
    std::set<std::string> seen;
    for (const auto& item : catalog()) {
        if (item.category && seen.insert(item.category).second) {
            cats.push_back(item.category);
        }
    }
    return cats;
}

} // namespace sqlref