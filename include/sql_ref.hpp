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
         "SUPPORTED -- SQLSEL INSERT targets an open table in the current workspace, "
         "validates typed values through the REPLACE storage gate, stages the row in "
         "TableBuffer/TBJ1, and commits through the house APPEND path. In SET MODE SQL, "
         "the SQLSEL prefix is optional. See SQLSEL USAGE."},
        {"INSERT-MULTI",
         "INSERT INTO users (name, email) VALUES ('Bob','bob@ex.com'), ('Charlie','charlie@ex.com');",
         "Insert multiple rows", "DML", true,
         "SUPPORTED -- one explicit field list may be followed by multiple parenthesized "
         "VALUES groups. The complete statement is staged before commit; an error refuses "
         "the batch. Explicit SQL transactions remain limited to one target table."},
        {"UPDATE",
         "UPDATE users SET status = 'active' WHERE id = 5;",
         "Update matching rows", "DML", true,
         "SUPPORTED -- SQLSEL UPDATE evaluates the typed house expression engine for every "
         "row retained by the required WHERE predicate and writes through the same field "
         "normalization, TableBuffer, WAL, and COMMIT machinery as REPLACE."},
        {"DELETE",
         "DELETE FROM users WHERE id = 42;",
         "Delete matching rows", "DML", true,
         "SUPPORTED -- SQLSEL DELETE requires WHERE and stages the existing xBase delete "
         "flag through TableBuffer/TBJ1. It marks rows deleted; RECALL can unmark them and "
         "PACK is still the physical removal boundary. See SQLSEL and DELETE USAGE."},
        {"TRUNCATE", 
         "TRUNCATE TABLE users;", 
         "Remove all rows quickly (MSSQL only)", "DML", false},

        // ────────────────────────────────────────────────
        // Querying & Filtering
        // ────────────────────────────────────────────────
        {"SELECT-BASIC",
         "SELECT name, email FROM users WHERE age > 30 ORDER BY name LIMIT 10;",
         "Basic query with WHERE, ORDER, LIMIT", "Query", true,
         "SUPPORTED -- SQLsel over an open table in the current workspace. Projection may "
         "use typed expressions and aliases; WHERE, multi-column ORDER BY, and LIMIT compose "
         "over the result. See SQLSEL USAGE."},
        {"SELECT-COUNT",
         "SELECT COUNT(*) FROM users WHERE status = 'active';",
         "Count matching rows", "Query", true,
         "SUPPORTED -- SQLsel, with or without WHERE. See SQLSEL USAGE."},
        {"SELECT-GROUP",
         "SELECT department, AVG(salary) FROM employees GROUP BY department HAVING COUNT(*) > 5;",
         "Aggregate + GROUP BY + HAVING", "Query", true,
         "SUPPORTED -- SQLsel implements GROUP BY and HAVING with COUNT, SUM, AVG, MIN, "
         "and MAX over typed TupleRows. Numeric blanks are skipped by field aggregates and "
         "the contributing/blank counts are reported. See SQLSEL USAGE."},
        {"SELECT-JOIN-INNER",
         "SELECT u.name, o.product FROM users u INNER JOIN orders o ON u.id = o.user_id;",
         "Matching rows from both tables", "Join", true,
         "SUPPORTED -- SQLsel INNER JOIN matches typed row sets from open tables. It accepts "
         "self-joins, composite ON predicates, and INNER/LEFT/CROSS chains, while reporting "
         "the table fence and access path. This is statement-scoped and does not read REL."},
        {"SELECT-JOIN-LEFT",
         "SELECT u.name, o.product FROM users u LEFT JOIN orders o ON u.id = o.user_id;",
         "All left rows + matching right rows", "Join", true,
         "SUPPORTED -- SQLsel LEFT JOIN preserves left rows, carries produced absence as a "
         "typed cell state, renders it as <UNMATCHED>, and applies SQL three-valued WHERE "
         "logic. RIGHT and FULL are supported for two-table joins."},

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
         "SUPPORTED -- in SET MODE SQL, BEGIN [TRANSACTION] opens an explicit SQLsel DML "
         "scope. It acquires one target table fence on first write and uses TableBuffer + "
         "TBJ1 WAL. Cross-table atomic commit is refused. Native TABLE BUFFER remains the "
         "cursor-oriented equivalent."},
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
