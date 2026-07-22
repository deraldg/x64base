// src/cli/edu_bibletalk.cpp
// DotTalk++: EDU_BIBLETALK command
//
// BibleTalk is the educational Bible database module.  The current carrier is
// SQLite, using the existing DotTalk++ sqlite_adapter.  This command is an
// educational/domain wrapper around SQLite-backed BibleTalk data; it is not a
// new database engine and it does not replace native DbArea/x64base storage.
//
// Usage:
//   EDU_BIBLETALK                         -> status + brief usage
//   EDU_BIBLETALK USAGE|HELP|?            -> detailed usage
//   EDU_BIBLETALK STATUS                  -> status only
//   EDU_BIBLETALK CWD|PWD                 -> show process working directory
//   EDU_BIBLETALK VERSION                 -> show linked SQLite version
//   EDU_BIBLETALK OPEN <file>|:memory:    -> open/connect (creates if needed)
//   EDU_BIBLETALK DB <file>|:memory:      -> alias for OPEN
//   EDU_BIBLETALK BIBLE                   -> open canonical BibleTalk SQLite seed
//   EDU_BIBLETALK BIBLECHECK              -> open/check canonical BibleTalk SQLite seed
//   EDU_BIBLETALK BOOKS                   -> list canonical Bible books
//   EDU_BIBLETALK VERSE <ref>             -> show one Bible verse by reference
//   EDU_BIBLETALK QUOTE                   -> print a random scripture
//   EDU_BIBLETALK SEARCH <phrase>         -> search Bible verses (FTS5, then LIKE fallback)
//   EDU_BIBLETALK LIST <table> [limit]    -> quick table preview
//   EDU_BIBLETALK COLUMNS <table>         -> show table columns
//   EDU_BIBLETALK CLOSE                   -> close
//   EDU_BIBLETALK TABLES                  -> list user tables/views
//   EDU_BIBLETALK SCHEMA [name]           -> show schema rows; optional table/view name
//   EDU_BIBLETALK EXEC <sql...>           -> execute non-SELECT SQL
//   EDU_BIBLETALK SELECT <sql...>         -> run a SELECT and print rows
//
// Notes:
//   - Uses dottalk::sqlite::* from sqlite/sqlite_adapter.hpp.
//   - Independent of DBF open/order state.
//   - SQLite here is an external SQL/RDBMS backend surface, not native DbArea storage.
//   - SELECT output is capped (MAX_SELECT_ROWS) to keep CLI responsive.

// @dottalk.usage v1
// owner: EDU|BIBLETALK
// command: BIBLETALK
// category: education-database-demo
// status: supported
// noargs: status-and-brief-usage
// effect: sqlite-demo-query
// mutates: sqlite-connection-state
// usage-access: BIBLETALK USAGE
// summary:
//   Educational BibleTalk/KJV SQLite database wrapper for status, schema,
//   table inspection, verse lookup, search, and random scripture output.
//
// usage:
//   BIBLETALK USAGE
//   BIBLETALK HELP
//   BIBLETALK STATUS
//   BIBLETALK BIBLE
//   BIBLETALK BIBLECHECK
//   BIBLETALK BOOKS
//   BIBLETALK VERSE <ref>
//   BIBLETALK QUOTE
//   BIBLETALK SEARCH <phrase>
//   BIBLETALK LIST <table> [limit]
//   BIBLETALK COLUMNS <table>
//   BIBLETALK TABLES
//   BIBLETALK SCHEMA [table]
//   BIBLETALK EXEC <sql...>
//   BIBLETALK SELECT <sql...>
//   BIBLETALK CLOSE
//
// examples:
//   BIBLETALK USAGE
//   BIBLETALK BIBLE
//   BIBLETALK VERSE John 3:16
//   BIBLETALK SEARCH faith
//   BIBLETALK QUOTE
//
// notes:
//   USAGE/HELP/? returns before SQLite database work.
//   No-arg behavior remains status plus brief usage.
//   BIBLETALK is the registered public command; cmd_EDU_BIBLETALK is an
//   internal implementation symbol, not a top-level command spelling.
//
// risk:
//   opens_sqlite_database: BIBLE/OPEN/DB/BIBLECHECK and implicit query open paths
//   executes_sql: EXEC/SELECT
//   mutates_table_data: no native x64base table mutation
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

static std::string sql_like_literal_contains(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 4);
    out.push_back('\'');
    out.push_back('%');

    for (char ch : s) {
        if (ch == '\'') out += "''";
        else if (ch == '%' || ch == '_' || ch == '\\') {
            out.push_back('\\');
            out.push_back(ch);
        } else {
            out.push_back(ch);
        }
    }

    out.push_back('%');
    out.push_back('\'');
    return out;
}

static void print_usage_brief() {
    std::cout
        << "BIBLETALK: USAGE, HELP, STATUS, CWD, VERSION, OPEN <file|:memory:>, BIBLE, BIBLECHECK,\n"
        << "               BOOKS, VERSE <ref>, QUOTE, SEARCH <phrase>, LIST <table> [limit],\n"
        << "               COLUMNS <table>, CLOSE, TABLES, SCHEMA [table], EXEC <sql>, SELECT <sql>\n";
}

static void print_usage_long() {
    std::cout <<
        "BIBLETALK\n"
        "  BIBLETALK <subcommand> ...\n"
        "  Educational BibleTalk database command.\n\n"

        "Current carrier:\n"
        "  SQLite-backed KJV Bible seed through the existing DotTalk++ sqlite_adapter.\n"
        "  Future direction is native x64base/LMDB BibleTalk transfer and comparison.\n\n"

        "Core commands:\n"
        "  BIBLETALK USAGE\n"
        "  BIBLETALK HELP\n"
        "  BIBLETALK ?\n"
        "  BIBLETALK STATUS\n"
        "  BIBLETALK CWD\n"
        "  BIBLETALK PWD\n"
        "  BIBLETALK VERSION\n"
        "  BIBLETALK OPEN <file>|:memory:\n"
        "  BIBLETALK DB <file>|:memory:\n"
        "  BIBLETALK CLOSE\n\n"

        "SQL inspection commands:\n"
        "  BIBLETALK TABLES\n"
        "  BIBLETALK SCHEMA [table-or-view]\n"
        "  BIBLETALK COLUMNS <table>\n"
        "  BIBLETALK EXEC <sql...>\n"
        "  BIBLETALK SELECT <sql...>\n"
        "  BIBLETALK LIST <table> [limit]\n\n"

        "Bible seed commands:\n"
        "  BIBLETALK BIBLE\n"
        "      Open the canonical KJV BibleTalk SQLite seed.\n\n"
        "  BIBLETALK BIBLECHECK\n"
        "  BIBLETALK BIBLECHK\n"
        "      Validate BibleTalk counts and basic queryability.\n\n"
        "  BIBLETALK BOOKS\n"
        "      List the 66 Bible books with testament, code, chapter count, and verse count.\n\n"
        "  BIBLETALK VERSE <ref>\n"
        "      Show a verse by reference.\n"
        "      Example: BIBLETALK VERSE John 3:16\n\n"
        "  BIBLETALK QUOTE\n"
        "      Print a random scripture. Safe for init.ini startup use.\n"
        "      Example: BIBLETALK QUOTE\n\n"
        "  BIBLETALK SEARCH <phrase>\n"
        "      Search Bible verse text. Tries FTS5 first, then falls back to LIKE.\n\n"

        "Canonical Bible seed paths:\n"
        "  If launched from dottalkpp\\data:\n"
        "    BIBLETALK OPEN biblebase\\biblebase.sqlite\n"
        "  If launched from the repo root:\n"
        "    BIBLETALK OPEN data\\biblebase\\biblebase.sqlite\n"
        "  Convenience form:\n"
        "    BIBLETALK BIBLE\n"
        "    BIBLETALK BIBLECHECK\n\n"

        "Examples:\n"
        "  BIBLETALK CWD\n"
        "  BIBLETALK BIBLE\n"
        "  BIBLETALK BIBLECHECK\n"
        "  BIBLETALK TABLES\n"
        "  BIBLETALK SCHEMA verses\n"
        "  BIBLETALK COLUMNS verses\n"
        "  BIBLETALK LIST verses 10\n"
        "  BIBLETALK BOOKS\n"
        "  BIBLETALK VERSE John 3:16\n"
        "  BIBLETALK QUOTE\n"
        "  BIBLETALK SEARCH kingdom of heaven\n"
        "  BIBLETALK SELECT select count(*) as verse_count from verses\n"
        "  BIBLETALK SELECT select ref, text from verses where ref='John 3:16'\n\n"

        "Important boundary:\n"
        "  BIBLETALK opens and queries an external SQLite database.\n"
        "  Native LIST is still a DbArea/x64base command.\n"
        "  Opening BibleTalk-SQLite does not open a native x64base work area.\n"
        "  Use BIBLETALK LIST <table> for SQLite rows.\n"
        "  Use native LIST only after USE/import/open of an x64base table.\n";
}

static void print_status() {
    std::cout << "EDU_BIBLETALK: "
              << (dottalk::sqlite::sqlite_is_open(g_db) ? "open" : "closed")
              << " (db='" << (g_db_path.empty() ? "" : g_db_path) << "')\n";
}

static bool ensure_open(std::string& err) {
    if (dottalk::sqlite::sqlite_is_open(g_db)) return true;

    err = "no BibleTalk SQLite database is open; use EDU_BIBLETALK OPEN <file>|:memory: or EDU_BIBLETALK BIBLE";
    return false;
}

static void print_cwd() {
    try {
        std::cout << "EDU_BIBLETALK CWD: " << std::filesystem::current_path().string() << "\n";
    } catch (const std::exception& e) {
        std::cout << "EDU_BIBLETALK CWD failed: " << e.what() << "\n";
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
        // Current permanent BibleTalk layout.
        // datarun/biblerun normally starts in dottalkpp\data.
        "biblebase\\biblebase.sqlite",
        "data\\biblebase\\biblebase.sqlite",

        // Compatibility fallbacks from the original KJV seed package and rename transition.
        "biblebase\\bible_kjv_x64.sqlite",
        "data\\biblebase\\bible_kjv_x64.sqlite",
        "bible_kjv_x64_rdbms\\bible_kjv_x64.sqlite",
        "data\\bible_kjv_x64_rdbms\\bible_kjv_x64.sqlite"
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
    os << "BibleTalk SQLite seed not found. Tried:";
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

    std::cout << "EDU_BIBLETALK: opened BibleTalk seed " << opened_path << "\n";
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
            const std::string cell = (i < r.size()) ? r[i] : std::string();
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
            const std::string cell = (i < r.size()) ? r[i] : std::string();
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
        std::cout << "EDU_BIBLETALK: open failed: " << err << "\n";
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
        std::cout << "EDU_BIBLETALK BOOKS failed: " << err << "\n";
        return false;
    }

    const std::string sql =
        "select book_seq, testament_code, book_code, common_name, chapter_count, verse_count "
        "from books order by book_seq";

    return run_and_print_query("EDU_BIBLETALK BOOKS", sql, MAX_META_ROWS);
}

static bool run_bible_verse(const std::string& ref) {
    if (ref.empty()) {
        std::cout << "Usage: EDU_BIBLETALK VERSE <ref>\n";
        std::cout << "Example: EDU_BIBLETALK VERSE John 3:16\n";
        return false;
    }

    std::string err;
    if (!ensure_open_or_bible(err)) {
        std::cout << "EDU_BIBLETALK VERSE failed: " << err << "\n";
        return false;
    }

    const std::string qref = sql_quote_literal(ref);
    const std::string sql =
        "select ref, text from verses where lower(ref) = lower(" + qref + ")";

    return run_and_print_query("EDU_BIBLETALK VERSE", sql, 5);
}

static bool run_bible_quote() {
    std::string err;
    if (!ensure_open_or_bible(err)) {
        std::cout << "EDU_BIBLETALK QUOTE failed: " << err << "\n";
        return false;
    }

    std::vector<std::string> cols;
    std::vector<dottalk::sqlite::Row> rows;
    bool truncated = false;

    const std::string sql =
        "select ref, text from verses order by random() limit 1";

    if (!query_to_rows(sql, 1, cols, rows, truncated, err)) {
        std::cout << "EDU_BIBLETALK QUOTE failed: " << err << "\n";
        return false;
    }

    if (rows.empty() || rows[0].size() < 2) {
        std::cout << "EDU_BIBLETALK QUOTE: no verse found\n";
        return false;
    }

    std::cout << "BibleTalk Quote\n";
    std::cout << "  " << rows[0][0] << "\n";
    std::cout << "  " << rows[0][1] << "\n";
    return true;
}

static bool run_bible_search(const std::string& phrase) {
    if (phrase.empty()) {
        std::cout << "Usage: EDU_BIBLETALK SEARCH <phrase>\n";
        std::cout << "Example: EDU_BIBLETALK SEARCH kingdom of heaven\n";
        return false;
    }

    std::string err;
    if (!ensure_open_or_bible(err)) {
        std::cout << "EDU_BIBLETALK SEARCH failed: " << err << "\n";
        return false;
    }

    const std::string fts = sql_quote_literal(fts_quote_phrase(phrase));
    const std::string fts_sql =
        "select ref, text from verses_fts where verses_fts match " + fts +
        " limit 20";

    std::vector<std::string> cols;
    std::vector<dottalk::sqlite::Row> rows;
    bool truncated = false;

    if (query_to_rows(fts_sql, 20, cols, rows, truncated, err)) {
        print_query_result_or_message(cols, rows, truncated, 20);
        return true;
    }

    std::cout << "EDU_BIBLETALK SEARCH: FTS5 unavailable or failed; using LIKE fallback.\n";

    const std::string like_sql =
        "select ref, text from verses where lower(text) like lower(" +
        sql_like_literal_contains(phrase) + ") escape '\\\\' limit 20";

    cols.clear();
    rows.clear();
    truncated = false;
    err.clear();

    if (!query_to_rows(like_sql, 20, cols, rows, truncated, err)) {
        std::cout << "EDU_BIBLETALK SEARCH failed: " << err << "\n";
        return false;
    }

    print_query_result_or_message(cols, rows, truncated, 20);
    return true;
}

static bool run_quick_list(std::istringstream& args) {
    std::string table;
    args >> table;

    if (table.empty()) {
        std::cout << "Usage: EDU_BIBLETALK LIST <table> [limit]\n";
        std::cout << "Example: EDU_BIBLETALK LIST verses 10\n";
        return false;
    }

    if (!is_safe_identifier(table)) {
        std::cout << "EDU_BIBLETALK LIST failed: unsafe table name: " << table << "\n";
        return false;
    }

    std::string limit_text;
    args >> limit_text;
    const size_t limit = parse_limit_or_default(limit_text, 20, MAX_SELECT_ROWS);

    std::string err;
    if (!ensure_open(err)) {
        std::cout << "EDU_BIBLETALK LIST failed: " << err << "\n";
        return false;
    }

    std::ostringstream os;
    os << "select * from " << table << " limit " << limit;
    return run_and_print_query("EDU_BIBLETALK LIST", os.str(), limit);
}

static bool run_columns(std::istringstream& args) {
    std::string table;
    args >> table;

    if (table.empty()) {
        std::cout << "Usage: EDU_BIBLETALK COLUMNS <table>\n";
        std::cout << "Example: EDU_BIBLETALK COLUMNS verses\n";
        return false;
    }

    if (!is_safe_identifier(table)) {
        std::cout << "EDU_BIBLETALK COLUMNS failed: unsafe table name: " << table << "\n";
        return false;
    }

    std::string err;
    if (!ensure_open(err)) {
        std::cout << "EDU_BIBLETALK COLUMNS failed: " << err << "\n";
        return false;
    }

    const std::string sql = "pragma table_info(" + table + ")";
    return run_and_print_query("EDU_BIBLETALK COLUMNS", sql, MAX_META_ROWS);
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
            std::cout << "EDU_BIBLETALK BIBLECHECK failed: " << err << "\n";
            return false;
        }

        std::cout << "EDU_BIBLETALK: opened BibleTalk seed " << opened_path << "\n";
    }

    std::cout << "EDU_BIBLETALK BIBLE CHECK\n";
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
// MUST be global + MUST match shell registration signature for EDU_BIBLETALK.
void cmd_EDU_BIBLETALK(xbase::DbArea& /*A*/, std::istringstream& args) {
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
        std::cout << "EDU_BIBLETALK sqlite: " << dottalk::sqlite::sqlite_version() << "\n";
        return;
    }

#if !defined(DOTTALK_SQLITE_AVAILABLE) || !DOTTALK_SQLITE_AVAILABLE
    std::cout << "EDU_BIBLETALK: SQLite not available in this build (DOTTALK_SQLITE_AVAILABLE=0)\n";
    return;
#else

    if (sub == "OPEN" || sub == "DB") {
        std::string rest;
        std::getline(args, rest);

        rest = textio::trim(rest);
        rest = textio::unquote(rest);

        if (rest.empty()) {
            std::cout << "Usage: EDU_BIBLETALK OPEN <file>|:memory:\n";
            return;
        }

        std::string err;
        if (!open_sqlite_db(rest, err)) {
            std::cout << "EDU_BIBLETALK OPEN failed: " << err << "\n";
            return;
        }

        std::cout << "EDU_BIBLETALK: opened " << g_db_path << "\n";
        return;
    }

    if (sub == "BIBLE") {
        std::string opened_path;
        std::string err;

        if (!open_bible_seed(opened_path, err)) {
            std::cout << "EDU_BIBLETALK BIBLE failed: " << err << "\n";
            return;
        }

        std::cout << "EDU_BIBLETALK: opened BibleTalk seed " << opened_path << "\n";
        return;
    }

    if (sub == "BIBLECHECK" || sub == "BIBLECHK" || sub == "CHECK") {
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

    if (sub == "QUOTE" || sub == "RANDOM") {
        run_bible_quote();
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
        std::cout << "EDU_BIBLETALK: closed\n";
        return;
    }

    if (sub == "TABLES") {
        const std::string sql =
            "select type, name, tbl_name "
            "from sqlite_schema "
            "where type in ('table','view') "
            "and name not like 'sqlite_%' "
            "order by type, name";

        run_and_print_query("EDU_BIBLETALK TABLES", sql, MAX_META_ROWS);
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

        run_and_print_query("EDU_BIBLETALK SCHEMA", sql, MAX_META_ROWS);
        return;
    }

    if (sub == "EXEC") {
        std::string sql;
        std::getline(args, sql);
        sql = ltrim_copy(sql);

        if (sql.empty()) {
            std::cout << "Usage: EDU_BIBLETALK EXEC <sql...>\n";
            return;
        }

        std::string err;
        if (!ensure_open(err)) {
            std::cout << "EDU_BIBLETALK: open failed: " << err << "\n";
            return;
        }

        if (!dottalk::sqlite::sqlite_exec(g_db, sql, err)) {
            std::cout << "EDU_BIBLETALK EXEC failed: " << err << "\n";
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
            std::cout << "Usage: EDU_BIBLETALK SELECT <sql...>\n";
            return;
        }

        run_and_print_query("EDU_BIBLETALK SELECT", sql, MAX_SELECT_ROWS);
        return;
    }

    std::cout << "EDU_BIBLETALK: unknown subcommand: " << sub << "\n";
    print_usage_brief();
#endif
}

// Shell registry entrypoint used by shell_commands.cpp.
void edu_BIBLETALK(xbase::DbArea& A, std::istringstream& args) {
    cmd_EDU_BIBLETALK(A, args);
}

// Optional compatibility alias while command registration catches up. Remove if the
// project intentionally wants only EDU_BIBLETALK.
void cmd_BIBLETALK(xbase::DbArea& A, std::istringstream& args) {
    cmd_EDU_BIBLETALK(A, args);
}
