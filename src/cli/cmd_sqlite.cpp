// src/cli/cmd_sqlite.cpp
// DotTalk++: SQLITE command (thin wrapper around SQLite3 via sqlite_adapter)
//
// Usage:
//   SQLITE                         -> status + brief usage
//   SQLITE HELP|?                  -> detailed usage
//   SQLITE STATUS                  -> status only
//   SQLITE CWD|PWD                 -> show process working directory
//   SQLITE VERSION                 -> show linked SQLite version
//   SQLITE OPEN <file>|:memory:    -> open/connect (creates if needed)
//   SQLITE DB <file>|:memory:      -> alias for OPEN
//   SQLITE BIBLE                   -> open canonical Bible SQLite seed if found
//   SQLITE BIBLECHECK              -> open/check canonical Bible SQLite seed
//   SQLITE BOOKS                   -> list canonical Bible books
//   SQLITE VERSE <ref>             -> show one Bible verse by reference
//   SQLITE SEARCH <phrase>         -> full-text phrase search Bible verses
//   SQLITE LIST <table> [limit]    -> quick table preview
//   SQLITE COLUMNS <table>         -> show table columns
//   SQLITE CLOSE                   -> close
//   SQLITE TABLES                  -> list user tables/views
//   SQLITE SCHEMA [name]           -> show schema rows; optional table/view name
//   SQLITE EXEC <sql...>           -> execute non-SELECT SQL
//   SQLITE SELECT <sql...>         -> run a SELECT and print rows
//
// Notes:
//   - Independent of DBF open/order state.
//   - SQLite is an external SQL/RDBMS backend surface, not native DbArea storage.
//   - EXEC/SELECT/TABLES/SCHEMA require an explicit SQLITE OPEN first.
//   - SELECT output is capped (MAX_SELECT_ROWS) to keep CLI responsive.

// @dottalk.usage v1
// owner: DOT|SQLITE
// command: SQLITE
// category: sql
// status: supported
// noargs: report
// effect: mixed
// mutates: sqlite-connection external-sqlite-db
// usage-access: SQLITE USAGE
// summary:
//   Thin SQLite command wrapper for status, connection management, Bible seed
//   helpers, metadata inspection, SELECT queries, and EXEC statements.
//
// usage:
//   SQLITE
//   SQLITE USAGE
//   SQLITE STATUS
//   SQLITE CWD
//   SQLITE PWD
//   SQLITE VERSION
//   SQLITE OPEN <file>
//   SQLITE OPEN :memory:
//   SQLITE DB <file>
//   SQLITE DB :memory:
//   SQLITE BIBLE
//   SQLITE BIBLECHECK
//   SQLITE BIBLECHK
//   SQLITE BOOKS
//   SQLITE VERSE <ref>
//   SQLITE SEARCH <phrase>
//   SQLITE LIST <table>
//   SQLITE LIST <table> <limit>
//   SQLITE COLUMNS <table>
//   SQLITE CLOSE
//   SQLITE TABLES
//   SQLITE SCHEMA
//   SQLITE SCHEMA <table-or-view>
//   SQLITE EXEC <sql>
//   SQLITE SELECT <sql>
//
// notes:
//   SQLITE with no arguments reports connection status and brief usage.
//   SQLITE USAGE, HELP, and question mark print detailed usage.
//   OPEN and DB connect to a SQLite database and create it if needed.
//   BIBLE and BIBLECHECK open/check the canonical Bible seed database when found.
//   EXEC runs non-SELECT SQL and may mutate the external SQLite database.
//   SELECT prints query rows and caps output for CLI responsiveness.
//   SQLITE is independent of DBF open/order state.
//
// risk:
//   opens_sqlite_db: OPEN DB BIBLE BIBLECHECK
//   closes_sqlite_db: CLOSE
//   reads_sqlite_db: SELECT TABLES SCHEMA LIST COLUMNS BOOKS VERSE SEARCH
//   writes_sqlite_db: EXEC depending on SQL
//   mutates_native_table_data: no
//
// related:
//   SQLVER
//   IMPORT
//   EXPORT
//

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "textio.hpp"
#include "sqlite/sqlite_adapter.hpp"

namespace {

static dottalk::sqlite::SqliteDb g_db;
static std::string g_db_path;

constexpr size_t MAX_SELECT_ROWS = 200;
constexpr size_t MAX_META_ROWS   = 500;

static inline std::string up_copy(std::string s) {
    for (auto& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static inline std::string ltrim_copy(std::string s) {
    s.erase(s.begin(), std::find_if(s.begin(), s.end(),
        [](unsigned char c) { return !std::isspace(c); }));
    return s;
}

static std::string sql_quote_literal(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 2);
    out.push_back('\'');

    for (char ch : s) {
        if (ch == '\'') out += "''";
        else out.push_back(ch);
    }

    out.push_back('\'');
    return out;
}

static void print_usage_brief() {
    std::cout << "SQLITE: USAGE, STATUS, CWD, VERSION, OPEN <file>, OPEN :memory:, BIBLE, BIBLECHECK, BOOKS, VERSE <ref>, SEARCH <phrase>, LIST <table> [limit], COLUMNS <table>, CLOSE, TABLES, SCHEMA [table], EXEC <sql>, SELECT <sql>\n";
}

static void print_usage_long() {
    std::cout <<
        "SQLITE\n"
        "  SQLITE <subcommand> ...\n"
        "  SQLite integration.\n\n"
        "Subcommands:\n"
        "  SQLITE USAGE\n"
        "  SQLITE HELP\n"
        "  SQLITE ?\n"
        "  SQLITE STATUS\n"
        "  SQLITE CWD\n"
        "  SQLITE PWD\n"
        "  SQLITE VERSION\n"
        "  SQLITE OPEN <file>|:memory:\n"
        "  SQLITE DB <file>|:memory:\n"
        "  SQLITE BIBLE\n"
        "  SQLITE BIBLECHECK\n"
        "  SQLITE BIBLECHK\n"
        "  SQLITE BOOKS\n"
        "  SQLITE VERSE <ref>\n"
        "  SQLITE SEARCH <phrase>\n"
        "  SQLITE LIST <table> [limit]\n"
        "  SQLITE COLUMNS <table>\n"
        "  SQLITE CLOSE\n"
        "  SQLITE TABLES\n"
        "  SQLITE SCHEMA [table-or-view]\n"
        "  SQLITE EXEC <sql...>\n"
        "  SQLITE SELECT <sql...>\n\n"
        "Canonical Bible seed paths:\n"
        "  If launched from dottalkpp\\data:\n"
        "    SQLITE OPEN bible_kjv_x64_rdbms\\bible_kjv_x64.sqlite\n"
        "  If launched from the repo root:\n"
        "    SQLITE OPEN data\\bible_kjv_x64_rdbms\\bible_kjv_x64.sqlite\n"
        "  Convenience form:\n"
        "    SQLITE BIBLE\n"
        "    SQLITE BIBLECHECK\n\n"
        "Examples:\n"
        "  SQLITE CWD\n"
        "  SQLITE BIBLE\n"
        "  SQLITE TABLES\n"
        "  SQLITE SCHEMA verses\n"
        "  SQLITE SELECT select count(*) as verse_count from verses\n"
        "  SQLITE SELECT select ref, text from verses where ref='John 3:16'\n"
        "  SQLITE VERSE John 3:16\n"
        "  SQLITE SEARCH kingdom of heaven\n"
        "  SQLITE LIST verses 10\n"
        "  SQLITE COLUMNS verses\n"
        "  SQLITE BIBLECHECK\n\n"
        "Notes:\n"
        "  SQLite is an external SQL/RDBMS backend surface.\n"
        "  It does not replace DbArea/native x64base storage.\n"
        "  EXEC, SELECT, TABLES, and SCHEMA require SQLITE OPEN first.\n"
        "  SELECT output is capped for CLI responsiveness.\n";
}

static void print_status() {
    std::cout << "SQLITE: "
              << (dottalk::sqlite::sqlite_is_open(g_db) ? "open" : "closed")
              << " (db='" << (g_db_path.empty() ? "" : g_db_path) << "')\n";
}

static bool ensure_open(std::string& err) {
    if (dottalk::sqlite::sqlite_is_open(g_db)) return true;

    err = "no SQLite database is open; use SQLITE OPEN <file>|:memory: or SQLITE BIBLE";
    return false;
}

static void print_cwd() {
    try {
        std::cout << "SQLITE CWD: " << std::filesystem::current_path().string() << "\n";
    } catch (const std::exception& e) {
        std::cout << "SQLITE CWD failed: " << e.what() << "\n";
    }
}

static bool open_sqlite_db(const std::string& path, std::string& err) {
    dottalk::sqlite::sqlite_close(g_db);
    g_db_path.clear();

    if (!dottalk::sqlite::sqlite_open(g_db, path, err)) {
        dottalk::sqlite::sqlite_close(g_db);
        g_db_path.clear();
        return false;
    }

    g_db_path = path;
    return true;
}

static bool file_exists_for_read(const std::string& path) {
    try {
        return std::filesystem::exists(std::filesystem::path(path));
    } catch (...) {
        return false;
    }
}

static bool open_bible_seed(std::string& opened_path, std::string& err) {
    const std::vector<std::string> candidates = {
        "bible_kjv_x64_rdbms\\bible_kjv_x64.sqlite",       // datarun.ps1 starts here: dottalkpp\data
        "data\\bible_kjv_x64_rdbms\\bible_kjv_x64.sqlite"  // repo-root launch
    };

    for (const auto& candidate : candidates) {
        if (!file_exists_for_read(candidate)) continue;

        if (open_sqlite_db(candidate, err)) {
            opened_path = candidate;
            return true;
        }

        return false;
    }

    std::ostringstream os;
    os << "Bible SQLite seed not found. Tried:";
    for (const auto& candidate : candidates) {
        os << "\n  " << candidate;
    }
    err = os.str();
    return false;
}


static bool ensure_open_or_bible(std::string& err) {
    if (dottalk::sqlite::sqlite_is_open(g_db)) return true;

    std::string opened_path;
    if (!open_bible_seed(opened_path, err)) return false;

    std::cout << "SQLITE: opened Bible seed " << opened_path << "\n";
    return true;
}

static std::string read_rest_trimmed(std::istringstream& args) {
    std::string rest;
    std::getline(args, rest);
    rest = textio::trim(rest);
    rest = textio::unquote(rest);
    return rest;
}

static bool is_safe_identifier(const std::string& s) {
    if (s.empty()) return false;

    const unsigned char first = static_cast<unsigned char>(s[0]);
    if (!(std::isalpha(first) || s[0] == '_')) return false;

    for (char ch : s) {
        const unsigned char c = static_cast<unsigned char>(ch);
        if (!(std::isalnum(c) || ch == '_')) return false;
    }

    return true;
}

static size_t parse_limit_or_default(const std::string& text,
                                     size_t default_limit,
                                     size_t max_limit) {
    if (text.empty()) return default_limit;

    try {
        const unsigned long parsed = std::stoul(text);
        if (parsed == 0) return default_limit;
        if (parsed > max_limit) return max_limit;
        return static_cast<size_t>(parsed);
    } catch (...) {
        return default_limit;
    }
}

static std::string fts_quote_phrase(const std::string& phrase) {
    std::string cleaned;
    cleaned.reserve(phrase.size() + 2);
    cleaned.push_back('"');

    for (char ch : phrase) {
        if (ch == '"') cleaned.push_back(' ');
        else cleaned.push_back(ch);
    }

    cleaned.push_back('"');
    return cleaned;
}

static void print_table(const std::vector<std::string>& cols,
                        const std::vector<dottalk::sqlite::Row>& rows) {
    if (cols.empty()) {
        std::cout << "(no columns)\n";
        return;
    }

    const size_t ncol = cols.size();
    std::vector<size_t> w(ncol, 0);

    for (size_t i = 0; i < ncol; ++i) {
        w[i] = cols[i].size();
    }

    for (const auto& r : rows) {
        for (size_t i = 0; i < ncol; ++i) {
            const std::string& cell = (i < r.size()) ? r[i] : std::string();
            if (cell.size() > w[i]) w[i] = cell.size();
        }
    }

    for (size_t i = 0; i < ncol; ++i) {
        if (i) std::cout << " | ";
        std::cout << std::left << std::setw(static_cast<int>(w[i])) << cols[i];
    }
    std::cout << "\n";

    for (size_t i = 0; i < ncol; ++i) {
        if (i) std::cout << "-+-";
        std::cout << std::string(w[i], '-');
    }
    std::cout << "\n";

    for (const auto& r : rows) {
        for (size_t i = 0; i < ncol; ++i) {
            if (i) std::cout << " | ";
            const std::string& cell = (i < r.size()) ? r[i] : std::string();
            std::cout << std::left << std::setw(static_cast<int>(w[i])) << cell;
        }
        std::cout << "\n";
    }
}

static bool query_to_rows(const std::string& sql,
                          size_t max_rows,
                          std::vector<std::string>& cols,
                          std::vector<dottalk::sqlite::Row>& rows,
                          bool& truncated,
                          std::string& err) {
    cols.clear();
    rows.clear();
    truncated = false;

    return dottalk::sqlite::sqlite_query_cols(
        g_db,
        sql,
        [&](const std::vector<std::string>& c, const dottalk::sqlite::Row& r) {
            if (cols.empty()) cols = c;

            if (rows.size() < max_rows) {
                rows.push_back(r);
            } else {
                truncated = true;
            }
        },
        err
    );
}

static void print_query_result_or_message(const std::vector<std::string>& cols,
                                          const std::vector<dottalk::sqlite::Row>& rows,
                                          bool truncated,
                                          size_t max_rows) {
    if (rows.empty()) {
        std::cout << "(no rows)\n";
        return;
    }

    print_table(cols, rows);

    if (truncated) {
        std::cout << "... (truncated at " << max_rows << " rows)\n";
    }
}

static bool run_and_print_query(const std::string& label,
                                const std::string& sql,
                                size_t max_rows) {
    std::string err;
    if (!ensure_open(err)) {
        std::cout << "SQLITE: open failed: " << err << "\n";
        return false;
    }

    std::vector<std::string> cols;
    std::vector<dottalk::sqlite::Row> rows;
    bool truncated = false;

    if (!query_to_rows(sql, max_rows, cols, rows, truncated, err)) {
        std::cout << label << " failed: " << err << "\n";
        return false;
    }

    print_query_result_or_message(cols, rows, truncated, max_rows);
    return true;
}


static bool run_bible_books() {
    std::string err;
    if (!ensure_open_or_bible(err)) {
        std::cout << "SQLITE BOOKS failed: " << err << "\n";
        return false;
    }

    const std::string sql =
        "select book_seq, testament_code, book_code, common_name, chapter_count, verse_count "
        "from books order by book_seq";

    return run_and_print_query("SQLITE BOOKS", sql, MAX_META_ROWS);
}

static bool run_bible_verse(const std::string& ref) {
    if (ref.empty()) {
        std::cout << "Usage: SQLITE VERSE <ref>\n";
        std::cout << "Example: SQLITE VERSE John 3:16\n";
        return false;
    }

    std::string err;
    if (!ensure_open_or_bible(err)) {
        std::cout << "SQLITE VERSE failed: " << err << "\n";
        return false;
    }

    const std::string qref = sql_quote_literal(ref);
    const std::string sql =
        "select ref, text from verses where lower(ref) = lower(" + qref + ")";

    return run_and_print_query("SQLITE VERSE", sql, 5);
}

static bool run_bible_search(const std::string& phrase) {
    if (phrase.empty()) {
        std::cout << "Usage: SQLITE SEARCH <phrase>\n";
        std::cout << "Example: SQLITE SEARCH kingdom of heaven\n";
        return false;
    }

    std::string err;
    if (!ensure_open_or_bible(err)) {
        std::cout << "SQLITE SEARCH failed: " << err << "\n";
        return false;
    }

    const std::string fts = sql_quote_literal(fts_quote_phrase(phrase));
    const std::string sql =
        "select ref, text from verses_fts where verses_fts match " + fts +
        " limit 20";

    return run_and_print_query("SQLITE SEARCH", sql, 20);
}

static bool run_quick_list(std::istringstream& args) {
    std::string table;
    args >> table;

    if (table.empty()) {
        std::cout << "Usage: SQLITE LIST <table> [limit]\n";
        std::cout << "Example: SQLITE LIST verses 10\n";
        return false;
    }

    if (!is_safe_identifier(table)) {
        std::cout << "SQLITE LIST failed: unsafe table name: " << table << "\n";
        return false;
    }

    std::string limit_text;
    args >> limit_text;
    const size_t limit = parse_limit_or_default(limit_text, 20, MAX_SELECT_ROWS);

    std::string err;
    if (!ensure_open(err)) {
        std::cout << "SQLITE LIST failed: " << err << "\n";
        return false;
    }

    std::ostringstream os;
    os << "select * from " << table << " limit " << limit;
    return run_and_print_query("SQLITE LIST", os.str(), limit);
}

static bool run_columns(std::istringstream& args) {
    std::string table;
    args >> table;

    if (table.empty()) {
        std::cout << "Usage: SQLITE COLUMNS <table>\n";
        std::cout << "Example: SQLITE COLUMNS verses\n";
        return false;
    }

    if (!is_safe_identifier(table)) {
        std::cout << "SQLITE COLUMNS failed: unsafe table name: " << table << "\n";
        return false;
    }

    std::string err;
    if (!ensure_open(err)) {
        std::cout << "SQLITE COLUMNS failed: " << err << "\n";
        return false;
    }

    const std::string sql = "pragma table_info(" + table + ")";
    return run_and_print_query("SQLITE COLUMNS", sql, MAX_META_ROWS);
}

static bool query_scalar_string(const std::string& sql,
                                std::string& value,
                                std::string& err) {
    std::vector<std::string> cols;
    std::vector<dottalk::sqlite::Row> rows;
    bool truncated = false;

    if (!query_to_rows(sql, 1, cols, rows, truncated, err)) {
        return false;
    }

    if (rows.empty() || rows[0].empty()) {
        value.clear();
        return true;
    }

    value = rows[0][0];
    return true;
}

static bool check_count(const std::string& label,
                        const std::string& table,
                        const std::string& expected) {
    std::string value;
    std::string err;

    if (!query_scalar_string("select count(*) from " + table, value, err)) {
        std::cout << "  " << label << ": FAILED (" << err << ")\n";
        return false;
    }

    const bool ok = (value == expected);
    std::cout << "  " << label << ": " << value
              << " / expected " << expected
              << (ok ? " OK" : " MISMATCH") << "\n";
    return ok;
}

static bool check_query_count(const std::string& label,
                              const std::string& sql,
                              const std::string& expected) {
    std::string value;
    std::string err;

    if (!query_scalar_string(sql, value, err)) {
        std::cout << "  " << label << ": FAILED (" << err << ")\n";
        return false;
    }

    const bool ok = (value == expected);
    std::cout << "  " << label << ": " << value
              << " / expected " << expected
              << (ok ? " OK" : " MISMATCH") << "\n";
    return ok;
}

static bool run_bible_check() {
    if (!dottalk::sqlite::sqlite_is_open(g_db)) {
        std::string opened_path;
        std::string err;

        if (!open_bible_seed(opened_path, err)) {
            std::cout << "SQLITE BIBLECHECK failed: " << err << "\n";
            return false;
        }

        std::cout << "SQLITE: opened Bible seed " << opened_path << "\n";
    }

    std::cout << "SQLITE BIBLE CHECK\n";
    std::cout << "  db: " << (g_db_path.empty() ? "" : g_db_path) << "\n";
    std::cout << "  sqlite: " << dottalk::sqlite::sqlite_version() << "\n";

    bool ok = true;
    ok = check_count("testaments", "testaments", "2") && ok;
    ok = check_count("books", "books", "66") && ok;
    ok = check_count("chapters", "chapters", "1189") && ok;
    ok = check_count("verses", "verses", "31102") && ok;
    ok = check_count("lexemes", "lexemes", "12765") && ok;
    ok = check_count("word_tokens", "word_tokens", "789645") && ok;
    ok = check_count("verse_lexeme_counts", "verse_lexeme_counts", "616199") && ok;

    ok = check_query_count(
        "John 3:16",
        "select count(*) from verses where ref='John 3:16' "
        "and text like 'For God so loved the world%'",
        "1"
    ) && ok;

    ok = check_query_count(
        "FTS table",
        "select count(*) from sqlite_schema where type='table' and name='verses_fts'",
        "1"
    ) && ok;

    if (ok) {
        std::cout << "  result: OK\n";
    } else {
        std::cout << "  result: FAILED\n";
    }

    return ok;
}

} // namespace

// ---- command entry ----
// MUST be global + MUST match shell registration signature.
void cmd_SQLITE(xbase::DbArea& /*A*/, std::istringstream& args) {
    std::string sub;

    if (!(args >> sub)) {
        print_status();
        print_usage_brief();
        return;
    }

    sub = up_copy(sub);

    if (sub == "USAGE" || sub == "HELP" || sub == "?") {
        print_usage_long();
        return;
    }

    if (sub == "STATUS") {
        print_status();
        return;
    }

    if (sub == "CWD" || sub == "PWD") {
        print_cwd();
        return;
    }

    if (sub == "VERSION") {
        std::cout << "SQLite: " << dottalk::sqlite::sqlite_version() << "\n";
        return;
    }

#if !defined(DOTTALK_SQLITE_AVAILABLE) || !DOTTALK_SQLITE_AVAILABLE
    std::cout << "SQLITE: not available in this build (DOTTALK_SQLITE_AVAILABLE=0)\n";
    return;
#else

    if (sub == "OPEN" || sub == "DB") {
        std::string rest;
        std::getline(args, rest);

        // textio.hpp provides trim()/unquote() (NOT trim_copy/unquote_copy)
        rest = textio::trim(rest);
        rest = textio::unquote(rest);

        if (rest.empty()) {
            std::cout << "Usage: SQLITE OPEN <file>|:memory:\n";
            return;
        }

        std::string err;
        if (!open_sqlite_db(rest, err)) {
            std::cout << "SQLITE OPEN failed: " << err << "\n";
            return;
        }

        std::cout << "SQLITE: opened " << g_db_path << "\n";
        return;
    }

    if (sub == "BIBLE") {
        std::string opened_path;
        std::string err;

        if (!open_bible_seed(opened_path, err)) {
            std::cout << "SQLITE BIBLE failed: " << err << "\n";
            return;
        }

        std::cout << "SQLITE: opened Bible seed " << opened_path << "\n";
        return;
    }

    if (sub == "BIBLECHECK" || sub == "BIBLECHK") {
        run_bible_check();
        return;
    }

    if (sub == "BOOKS") {
        run_bible_books();
        return;
    }

    if (sub == "VERSE") {
        run_bible_verse(read_rest_trimmed(args));
        return;
    }

    if (sub == "SEARCH" || sub == "FIND") {
        run_bible_search(read_rest_trimmed(args));
        return;
    }

    if (sub == "LIST") {
        run_quick_list(args);
        return;
    }

    if (sub == "COLUMNS" || sub == "COLS") {
        run_columns(args);
        return;
    }

    if (sub == "CLOSE") {
        dottalk::sqlite::sqlite_close(g_db);
        g_db_path.clear();
        std::cout << "SQLITE: closed\n";
        return;
    }

    if (sub == "TABLES") {
        const std::string sql =
            "select type, name, tbl_name "
            "from sqlite_schema "
            "where type in ('table','view') "
            "and name not like 'sqlite_%' "
            "order by type, name";

        run_and_print_query("SQLITE TABLES", sql, MAX_META_ROWS);
        return;
    }

    if (sub == "SCHEMA") {
        std::string name;
        std::getline(args, name);
        name = textio::trim(name);
        name = textio::unquote(name);

        std::string sql;
        if (name.empty()) {
            sql =
                "select type, name, sql "
                "from sqlite_schema "
                "where type in ('table','view','index','trigger') "
                "and name not like 'sqlite_%' "
                "order by type, name";
        } else {
            const std::string qname = sql_quote_literal(name);
            std::ostringstream os;
            os << "select type, name, sql "
               << "from sqlite_schema "
               << "where name = " << qname << " "
               << "or tbl_name = " << qname << " "
               << "order by type, name";
            sql = os.str();
        }

        run_and_print_query("SQLITE SCHEMA", sql, MAX_META_ROWS);
        return;
    }

    if (sub == "EXEC") {
        std::string sql;
        std::getline(args, sql);
        sql = ltrim_copy(sql);

        if (sql.empty()) {
            std::cout << "Usage: SQLITE EXEC <sql...>\n";
            return;
        }

        std::string err;
        if (!ensure_open(err)) {
            std::cout << "SQLITE: open failed: " << err << "\n";
            return;
        }

        if (!dottalk::sqlite::sqlite_exec(g_db, sql, err)) {
            std::cout << "SQLITE EXEC failed: " << err << "\n";
            return;
        }

        std::cout << "OK\n";
        return;
    }

    if (sub == "SELECT") {
        std::string sql;
        std::getline(args, sql);
        sql = ltrim_copy(sql);

        if (sql.empty()) {
            std::cout << "Usage: SQLITE SELECT <sql...>\n";
            return;
        }

        run_and_print_query("SQLITE SELECT", sql, MAX_SELECT_ROWS);
        return;
    }

    std::cout << "SQLITE: unknown subcommand: " << sub << "\n";
    print_usage_brief();
#endif
}
