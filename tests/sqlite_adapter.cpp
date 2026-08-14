// @dottalk.file v1
// subsystem: tests
// layer: test
// owns:
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: supported

#include "sqlite/sqlite_adapter.hpp"

#include <cassert>
#include <cstring>
#include <sstream>

#if DOTTALK_SQLITE_AVAILABLE
// Real implementation (SQLite found at build time)
extern "C" {
#include <sqlite3.h>
}

namespace dottalk::sqlite {

static inline sqlite3* as_ptr(void* p) { return static_cast<sqlite3*>(p); }
static inline void set_ptr(void*& slot, sqlite3* p) { slot = static_cast<void*>(p); }

bool sqlite_open(SqliteDb& db, const std::string& path, std::string& err) {
    // Close any previous handle
    if (db.handle) {
        sqlite_close(db);
    }
    sqlite3* h = nullptr;
    int rc = sqlite3_open(path.c_str(), &h);
    if (rc != SQLITE_OK) {
        err = h ? sqlite3_errmsg(h) : "sqlite3_open failed";
        if (h) sqlite3_close(h);
        return false;
    }
    set_ptr(db.handle, h);
    return true;
}

void sqlite_close(SqliteDb& db) {
    if (db.handle) {
        sqlite3_close(as_ptr(db.handle));
        db.handle = nullptr;
    }
}

bool sqlite_exec(SqliteDb& db, const std::string& sql, std::string& err) {
    if (!db.handle) {
        err = "No database open";
        return false;
    }
    char* errmsg = nullptr;
    int rc = sqlite3_exec(as_ptr(db.handle), sql.c_str(), nullptr, nullptr, &errmsg);
    if (rc != SQLITE_OK) {
        if (errmsg) {
            err.assign(errmsg);
            sqlite3_free(errmsg);
        } else {
            err = "sqlite3_exec failed";
        }
        return false;
    }
    return true;
}

bool sqlite_query(
    SqliteDb& db,
    const std::string& sql,
    const std::function<void(const Row&)>& on_row,
    std::string& err)
{
    if (!db.handle) {
        err = "No database open";
        return false;
    }

    sqlite3_stmt* stmt = nullptr;
    int rc = sqlite3_prepare_v2(as_ptr(db.handle), sql.c_str(), -1, &stmt, nullptr);
    if (rc != SQLITE_OK || !stmt) {
        err = sqlite3_errmsg(as_ptr(db.handle));
        if (stmt) sqlite3_finalize(stmt);
        return false;
    }

    const int col_count = sqlite3_column_count(stmt);
    Row row;
    row.reserve(col_count);

    for (;;) {
        rc = sqlite3_step(stmt);
        if (rc == SQLITE_ROW) {
            row.clear();
            for (int i = 0; i < col_count; ++i) {
                const unsigned char* txt = sqlite3_column_text(stmt, i);
                if (txt) {
                    row.emplace_back(reinterpret_cast<const char*>(txt));
                } else {
                    // Represent NULL as empty string; adjust if you prefer "<NULL>"
                    row.emplace_back("");
                }
            }
            on_row(row);
            continue;
        }
        if (rc == SQLITE_DONE) break;

        // Error
        err = sqlite3_errmsg(as_ptr(db.handle));
        sqlite3_finalize(stmt);
        return false;
    }

    sqlite3_finalize(stmt);
    return true;
}

std::string sqlite_version() {
    return std::string(sqlite3_libversion());
}

} // namespace dottalk::sqlite

#else
// Stub implementation (built without SQLite; compiles & links but reports unavailable)

namespace dottalk::sqlite {

bool sqlite_open(SqliteDb&, const std::string&, std::string& err) {
    err = "SQLite not available in this build";
    return false;
}

void sqlite_close(SqliteDb&) {
    // no-op
}

bool sqlite_exec(SqliteDb&, const std::string&, std::string& err) {
    err = "SQLite not available in this build";
    return false;
}

bool sqlite_query(
    SqliteDb&,
    const std::string&,
    const std::function<void(const Row&)>&,
    std::string& err)
{
    err = "SQLite not available in this build";
    return false;
}

std::string sqlite_version() {
    return "unavailable";
}

} // namespace dottalk::sqlite
#endif
