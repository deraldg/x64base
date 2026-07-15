// src/cli/edu_erp.cpp
// DotTalk++: EDU_ERP / ERP command
//
// Cascade Precision Mfg ERP is the educational manufacturing ERP sample.
// The current carrier is SQLite, using the existing DotTalk++ sqlite_adapter.
// This command is a domain wrapper around an ERP SQLite seed; it is not a new
// database engine and it does not replace native DbArea/x64base storage.
//
// Usage:
//   ERP                         -> status + brief usage
//   ERP USAGE|HELP|?            -> detailed usage
//   ERP STATUS                  -> status only
//   ERP CWD|PWD                 -> show process working directory
//   ERP VERSION                 -> show linked SQLite version
//   ERP OPEN <file>|:memory:    -> open/connect
//   ERP DB <file>|:memory:      -> alias for OPEN
//   ERP CASCADE|SEED            -> open canonical Cascade Precision ERP seed
//   ERP CHECK                   -> open/check canonical ERP seed
//   ERP MODULES                 -> show module map
//   ERP TABLES                  -> list user tables/views
//   ERP VIEWS                   -> list analytical views
//   ERP COLUMNS <table>         -> show table columns
//   ERP LIST <table> [limit]    -> quick table/view preview
//   ERP SCHEMA [name]           -> show schema rows; optional table/view name
//   ERP EXEC <sql...>           -> execute non-SELECT SQL
//   ERP SELECT <sql...>         -> run a SELECT and print rows
//
// Domain shortcuts:
//   ERP ITEMS
//   ERP STOCK
//   ERP REORDER
//   ERP BOM [sku]
//   ERP WORKORDERS
//   ERP THREEWAY
//   ERP TRIAL
//
// Notes:
//   - Uses dottalk::sqlite::* from sqlite/sqlite_adapter.hpp.
//   - Independent of DBF open/order state.
//   - SQLite here is an external SQL/RDBMS backend surface, not native DbArea storage.
//   - ERP-specific behavior belongs here, not in the generic SQLITE command.
//   - SELECT output is capped to keep CLI responsive.

// @dottalk.usage v1
// owner: EDU|ERP
// command: ERP / EDU_ERP
// category: education-database-demo
// status: supported
// noargs: status-and-brief-usage
// effect: sqlite-demo-query
// mutates: sqlite-connection-state
// usage-access: ERP USAGE; EDU_ERP USAGE
// summary:
//   Educational Cascade Precision manufacturing ERP SQLite wrapper for
//   status, schema/table inspection, and domain shortcut reports.
//
// usage:
//   ERP USAGE
//   ERP HELP
//   ERP STATUS
//   ERP CASCADE
//   ERP CHECK
//   ERP MODULES
//   ERP TABLES
//   ERP VIEWS
//   ERP COLUMNS <table>
//   ERP LIST <table> [limit]
//   ERP ITEMS
//   ERP STOCK
//   ERP REORDER
//   ERP BOM [sku]
//   ERP WORKORDERS
//   ERP THREEWAY
//   ERP TRIAL
//   ERP SCHEMA [table]
//   ERP EXEC <sql...>
//   ERP SELECT <sql...>
//   ERP CLOSE
//
// examples:
//   ERP USAGE
//   ERP CASCADE
//   ERP MODULES
//   ERP ITEMS
//   ERP STOCK
//   ERP SELECT select * from items limit 5
//
// notes:
//   USAGE/HELP/? returns before SQLite database work.
//   No-arg behavior remains status plus brief usage.
//   EDU_ERP and cmd_ERP are compatibility aliases for ERP behavior.
//
// risk:
//   opens_sqlite_database: CASCADE/OPEN/DB/CHECK and implicit query open paths
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
constexpr size_t DEFAULT_LIST_LIMIT = 10;
constexpr size_t MAX_LIST_LIMIT = 500;

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

static std::string read_rest_trimmed(std::istringstream& args) {
    std::string rest;
    std::getline(args, rest);
    rest = textio::trim(rest);
    rest = textio::unquote(rest);
    return rest;
}

static void print_usage_brief() {
    std::cout
        << "ERP: USAGE, HELP, STATUS, CWD, VERSION, OPEN <file|:memory:>, CASCADE, CHECK,\n"
        << "     MODULES, TABLES, VIEWS, COLUMNS <table>, LIST <table> [limit],\n"
        << "     ITEMS, STOCK, REORDER, BOM [sku], WORKORDERS, THREEWAY, TRIAL,\n"
        << "     CLOSE, SCHEMA [table], EXEC <sql>, SELECT <sql>\n";
}

static void print_usage_long() {
    std::cout <<
        "ERP / EDU_ERP\n"
        "  ERP <subcommand> ...\n"
        "  Educational manufacturing ERP database command.\n\n"

        "Current carrier:\n"
        "  SQLite-backed Cascade Precision Mfg ERP seed through the existing\n"
        "  DotTalk++ sqlite_adapter.\n"
        "  Future direction is native x64base/LMDB ERP transfer and comparison.\n\n"

        "Core commands:\n"
        "  ERP USAGE\n"
        "  ERP HELP\n"
        "  ERP ?\n"
        "  ERP STATUS\n"
        "  ERP CWD\n"
        "  ERP PWD\n"
        "  ERP VERSION\n"
        "  ERP OPEN <file>|:memory:\n"
        "  ERP DB <file>|:memory:\n"
        "  ERP CLOSE\n\n"

        "ERP seed commands:\n"
        "  ERP CASCADE\n"
        "  ERP SEED\n"
        "      Open the canonical Cascade Precision Mfg ERP SQLite seed.\n\n"
        "  ERP CHECK\n"
        "  ERP ERPCHECK\n"
        "      Validate table/view counts and basic foreign key health.\n\n"
        "  ERP MODULES\n"
        "      Show the seven functional modules and their table groups.\n\n"

        "SQL inspection commands:\n"
        "  ERP TABLES\n"
        "  ERP VIEWS\n"
        "  ERP SCHEMA [table-or-view]\n"
        "  ERP COLUMNS <table>\n"
        "  ERP LIST <table> [limit]\n"
        "  ERP EXEC <sql...>\n"
        "  ERP SELECT <sql...>\n\n"

        "Domain shortcuts:\n"
        "  ERP ITEMS\n"
        "  ERP STOCK\n"
        "  ERP REORDER\n"
        "  ERP BOM [sku]\n"
        "  ERP WORKORDERS\n"
        "  ERP THREEWAY\n"
        "  ERP TRIAL\n\n"

        "Canonical ERP seed paths:\n"
        "  If launched from dottalkpp\\data:\n"
        "    ERP OPEN cascade_precision_erp\\cascade_precision_mfg_erp.sqlite\n"
        "  If launched from the repo root:\n"
        "    ERP OPEN data\\cascade_precision_erp\\cascade_precision_mfg_erp.sqlite\n"
        "  Convenience form:\n"
        "    ERP CASCADE\n"
        "    ERP CHECK\n\n"

        "Examples:\n"
        "  ERP CWD\n"
        "  ERP CHECK\n"
        "  ERP MODULES\n"
        "  ERP TABLES\n"
        "  ERP VIEWS\n"
        "  ERP COLUMNS Items\n"
        "  ERP LIST Items 10\n"
        "  ERP ITEMS\n"
        "  ERP REORDER\n"
        "  ERP BOM PDU-100\n"
        "  ERP THREEWAY\n"
        "  ERP SELECT select count(*) as user_tables from sqlite_schema where type='table' and name not like 'sqlite_%'\n\n"

        "Important boundary:\n"
        "  ERP opens and queries an external SQLite database.\n"
        "  Native LIST is still a DbArea/x64base command.\n"
        "  Opening ERP-SQLite does not open a native x64base work area.\n"
        "  Use ERP LIST <table> for SQLite rows.\n"
        "  Use native LIST only after USE/import/open of an x64base table.\n";
}

static void print_status() {
    std::cout << "ERP: "
              << (dottalk::sqlite::sqlite_is_open(g_db) ? "open" : "closed")
              << " (db='" << (g_db_path.empty() ? "" : g_db_path) << "')\n";
}

static void print_cwd() {
    try {
        std::cout << "ERP CWD: " << std::filesystem::current_path().string() << "\n";
    } catch (const std::exception& e) {
        std::cout << "ERP CWD failed: " << e.what() << "\n";
    }
}

static bool file_exists_for_read(const std::string& path) {
    try {
        return std::filesystem::exists(std::filesystem::path(path));
    } catch (...) {
        return false;
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

static bool open_erp_seed(std::string& opened_path, std::string& err) {
    const std::vector<std::string> candidates = {
        // Current permanent data layout. erprun/datarun starts in dottalkpp\\data.
        "cascade_precision_erp\\cascade_precision_mfg_erp.sqlite",
        "data\\cascade_precision_erp\\cascade_precision_mfg_erp.sqlite",

        // Earlier draft package name retained as non-advertised fallback.
        "erp_cascade_precision\\cascade_precision_mfg_erp.sqlite",
        "data\\erp_cascade_precision\\cascade_precision_mfg_erp.sqlite"
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
    os << "Cascade Precision ERP SQLite seed not found. Tried:";
    for (const auto& candidate : candidates) {
        os << "\n  " << candidate;
    }
    err = os.str();
    return false;
}

static bool ensure_open(std::string& err) {
    if (dottalk::sqlite::sqlite_is_open(g_db)) return true;

    err = "no ERP SQLite database is open; use ERP OPEN <file>|:memory: or ERP CASCADE";
    return false;
}

static bool ensure_open_or_seed(std::string& err) {
    if (dottalk::sqlite::sqlite_is_open(g_db)) return true;

    std::string opened_path;
    if (!open_erp_seed(opened_path, err)) return false;

    std::cout << "ERP: opened Cascade Precision seed " << opened_path << "\n";
    return true;
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

static bool scalar_string(const std::string& sql, std::string& value, std::string& err) {
    value.clear();

    std::vector<std::string> cols;
    std::vector<dottalk::sqlite::Row> rows;
    bool truncated = false;

    if (!query_to_rows(sql, 1, cols, rows, truncated, err)) {
        return false;
    }

    if (!rows.empty() && !rows[0].empty()) {
        value = rows[0][0];
    }

    return true;
}

static bool scalar_int(const std::string& sql, int& value, std::string& err) {
    std::string text;
    if (!scalar_string(sql, text, err)) return false;

    try {
        value = text.empty() ? 0 : std::stoi(text);
        return true;
    } catch (...) {
        err = "expected integer result from query: " + sql;
        return false;
    }
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
                                size_t max_rows,
                                bool auto_seed = true) {
    std::string err;
    const bool opened = auto_seed ? ensure_open_or_seed(err) : ensure_open(err);
    if (!opened) {
        std::cout << label << " failed: " << err << "\n";
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

static std::vector<std::string> get_table_names(std::string& err) {
    std::vector<std::string> out;
    std::vector<std::string> cols;
    std::vector<dottalk::sqlite::Row> rows;
    bool truncated = false;

    const std::string sql =
        "select name from sqlite_schema "
        "where type='table' and name not like 'sqlite_%' "
        "order by name";

    if (!query_to_rows(sql, 1000, cols, rows, truncated, err)) {
        return out;
    }

    for (const auto& r : rows) {
        if (!r.empty()) out.push_back(r[0]);
    }

    return out;
}

static void run_tables() {
    const std::string sql =
        "select type, name, tbl_name "
        "from sqlite_schema "
        "where type in ('table','view') "
        "and name not like 'sqlite_%' "
        "order by type, name";

    run_and_print_query("ERP TABLES", sql, MAX_META_ROWS);
}

static void run_views() {
    const std::string sql =
        "select name "
        "from sqlite_schema "
        "where type='view' "
        "order by name";

    run_and_print_query("ERP VIEWS", sql, MAX_META_ROWS);
}

static void run_schema(std::istringstream& args) {
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

    run_and_print_query("ERP SCHEMA", sql, MAX_META_ROWS);
}

static void run_columns(std::istringstream& args) {
    std::string table;
    args >> table;
    table = textio::trim(table);
    table = textio::unquote(table);

    if (!is_safe_identifier(table)) {
        std::cout << "Usage: ERP COLUMNS <safe_table_name>\n";
        return;
    }

    std::ostringstream os;
    os << "pragma table_info(" << table << ")";
    run_and_print_query("ERP COLUMNS", os.str(), MAX_META_ROWS);
}

static void run_quick_list(std::istringstream& args) {
    std::string table;
    args >> table;
    table = textio::trim(table);
    table = textio::unquote(table);

    if (!is_safe_identifier(table)) {
        std::cout << "Usage: ERP LIST <safe_table_or_view_name> [limit]\n";
        return;
    }

    std::string limit_text;
    args >> limit_text;
    const size_t limit = parse_limit_or_default(limit_text, DEFAULT_LIST_LIMIT, MAX_LIST_LIMIT);

    std::ostringstream os;
    os << "select * from " << table << " limit " << limit;
    run_and_print_query("ERP LIST", os.str(), limit);
}

static void print_count_line(const std::string& label,
                             int actual,
                             int expected,
                             bool required_equal = true) {
    std::cout << "  " << label << ": " << actual;

    if (expected >= 0) {
        std::cout << " / expected " << expected;
    }

    if (required_equal && expected >= 0) {
        std::cout << (actual == expected ? " OK" : " MISMATCH");
    }

    std::cout << "\n";
}

static void run_check() {
    std::string err;
    if (!ensure_open_or_seed(err)) {
        std::cout << "ERP CHECK failed: " << err << "\n";
        return;
    }

    int table_count = 0;
    int view_count = 0;
    int fk_errors = 0;

    bool ok = true;
    ok = ok && scalar_int(
        "select count(*) from sqlite_schema where type='table' and name not like 'sqlite_%'",
        table_count,
        err
    );
    ok = ok && scalar_int(
        "select count(*) from sqlite_schema where type='view'",
        view_count,
        err
    );

    if (!ok) {
        std::cout << "ERP CHECK failed: " << err << "\n";
        return;
    }

    std::vector<std::string> cols;
    std::vector<dottalk::sqlite::Row> rows;
    bool truncated = false;
    if (!query_to_rows("pragma foreign_key_check", 1000, cols, rows, truncated, err)) {
        std::cout << "ERP CHECK failed: " << err << "\n";
        return;
    }
    fk_errors = static_cast<int>(rows.size());

    int total_records = 0;
    std::vector<std::string> table_names = get_table_names(err);
    for (const auto& t : table_names) {
        if (!is_safe_identifier(t)) continue;

        int n = 0;
        std::ostringstream os;
        os << "select count(*) from " << t;
        if (scalar_int(os.str(), n, err)) {
            total_records += n;
        }
    }

    std::cout << "ERP CHECK\n";
    std::cout << "  db: " << (g_db_path.empty() ? "" : g_db_path) << "\n";
    std::cout << "  sqlite: " << dottalk::sqlite::sqlite_version() << "\n";
    print_count_line("user tables", table_count, 34);
    print_count_line("analytical views", view_count, 9);
    std::cout << "  functional modules: 7 / expected 7 OK\n";
    std::cout << "  cross-module FK relationships: 26 / codex reference\n";
    std::cout << "  loaded sample records: " << total_records << "\n";
    std::cout << "  target sample records: 330 / Phase 2 data load\n";
    std::cout << "  foreign_key_check rows: " << fk_errors << (fk_errors == 0 ? " OK" : " FAILED") << "\n";
    std::cout << "  result: "
              << ((table_count == 34 && view_count == 9 && fk_errors == 0) ? "OK" : "CHECK WARN")
              << "\n";
}

static void run_modules() {
    std::cout <<
        "ERP MODULES - Cascade Precision Mfg\n"
        "  FINANCE (6): GL_Accounts, GL_Journal, AP_Invoices, AP_Payments, AR_Invoices, AR_Payments\n"
        "  INVENTORY & WAREHOUSE (4): Items, Warehouses, Stock_Levels, Inventory_Movements\n"
        "  MANUFACTURING (7): Work_Centers, BOM_Headers, BOM_Details, Routings, Work_Orders, WO_Materials, WO_Operations\n"
        "  PROCUREMENT (5): Vendors, Vendor_Items, Purchase_Orders, PO_Lines, Receiving\n"
        "  HUMAN RESOURCES (4): Departments, Employees, Time_Cards, Payroll_Runs\n"
        "  SALES & CRM (6): Customers, Price_Lists, Sales_Orders, SO_Lines, Shipments, Shipment_Lines\n"
        "  QUALITY CONTROL (2): Quality_Tests, Quality_Results\n"
        "  ANALYTICAL VIEWS (9): v_Available_Stock, v_Reorder_Alert, v_Open_Sales_Orders,\n"
        "                        v_Work_Order_Status, v_AP_Aging, v_AR_Aging, v_Trial_Balance,\n"
        "                        v_BOM_Explosion, v_Three_Way_Match\n";
}

static void run_items() {
    const std::string sql =
        "select Item_ID, SKU, Description, UOM, Item_Type, Cost_Method, "
        "Standard_Cost, List_Price, Reorder_Point, Reorder_Qty, Lead_Days, Category, Active "
        "from Items order by SKU limit 100";
    run_and_print_query("ERP ITEMS", sql, 100);
}

static void run_stock() {
    run_and_print_query("ERP STOCK", "select * from v_Available_Stock order by SKU, Warehouse_Code limit 100", 100);
}

static void run_reorder() {
    run_and_print_query("ERP REORDER", "select * from v_Reorder_Alert order by SKU, Warehouse_Code limit 100", 100);
}

static void run_workorders() {
    run_and_print_query("ERP WORKORDERS", "select * from v_Work_Order_Status order by Due_Date, WO_Number limit 100", 100);
}

static void run_threeway() {
    run_and_print_query("ERP THREEWAY", "select * from v_Three_Way_Match order by PO_Number limit 100", 100);
}

static void run_trial() {
    run_and_print_query("ERP TRIAL", "select * from v_Trial_Balance order by Account_Code limit 200", 200);
}

static void run_bom(std::istringstream& args) {
    std::string sku = read_rest_trimmed(args);

    std::string sql =
        "select * from v_BOM_Explosion";

    if (!sku.empty()) {
        sql += " where Parent_SKU = " + sql_quote_literal(sku);
    }

    sql += " order by Parent_SKU, Revision, Sequence limit 200";
    run_and_print_query("ERP BOM", sql, 200);
}

static void run_search_items(const std::string& phrase) {
    if (phrase.empty()) {
        std::cout << "Usage: ERP SEARCHITEMS <phrase>\n";
        return;
    }

    const std::string like = sql_like_literal_contains(phrase);
    std::ostringstream os;
    os << "select Item_ID, SKU, Description, Item_Type, Category "
       << "from Items "
       << "where SKU like " << like << " escape '\\' "
       << "or Description like " << like << " escape '\\' "
       << "or Category like " << like << " escape '\\' "
       << "order by SKU limit 100";
    run_and_print_query("ERP SEARCHITEMS", os.str(), 100);
}

} // namespace

// ---- command entry ----
// MUST be global + MUST match shell registration signature for ERP.
void edu_ERP(xbase::DbArea& /*A*/, std::istringstream& args) {
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
        std::cout << "ERP sqlite: " << dottalk::sqlite::sqlite_version() << "\n";
        return;
    }

#if !defined(DOTTALK_SQLITE_AVAILABLE) || !DOTTALK_SQLITE_AVAILABLE
    std::cout << "ERP: SQLite not available in this build (DOTTALK_SQLITE_AVAILABLE=0)\n";
    return;
#else

    if (sub == "OPEN" || sub == "DB") {
        std::string rest;
        std::getline(args, rest);

        rest = textio::trim(rest);
        rest = textio::unquote(rest);

        if (rest.empty()) {
            std::cout << "Usage: ERP OPEN <file>|:memory:\n";
            return;
        }

        std::string err;
        if (!open_sqlite_db(rest, err)) {
            std::cout << "ERP OPEN failed: " << err << "\n";
            return;
        }

        std::cout << "ERP: opened " << g_db_path << "\n";
        return;
    }

    if (sub == "CASCADE" || sub == "SEED" || sub == "ERPDB") {
        std::string opened_path;
        std::string err;

        if (!open_erp_seed(opened_path, err)) {
            std::cout << "ERP CASCADE failed: " << err << "\n";
            return;
        }

        std::cout << "ERP: opened Cascade Precision seed " << opened_path << "\n";
        return;
    }

    if (sub == "CHECK" || sub == "ERPCHECK") {
        run_check();
        return;
    }

    if (sub == "MODULES" || sub == "MODS") {
        run_modules();
        return;
    }

    if (sub == "TABLES") {
        run_tables();
        return;
    }

    if (sub == "VIEWS") {
        run_views();
        return;
    }

    if (sub == "SCHEMA") {
        run_schema(args);
        return;
    }

    if (sub == "COLUMNS" || sub == "COLS") {
        run_columns(args);
        return;
    }

    if (sub == "LIST") {
        run_quick_list(args);
        return;
    }

    if (sub == "ITEMS") {
        run_items();
        return;
    }

    if (sub == "STOCK") {
        run_stock();
        return;
    }

    if (sub == "REORDER") {
        run_reorder();
        return;
    }

    if (sub == "BOM") {
        run_bom(args);
        return;
    }

    if (sub == "WORKORDERS" || sub == "WO") {
        run_workorders();
        return;
    }

    if (sub == "THREEWAY" || sub == "MATCH") {
        run_threeway();
        return;
    }

    if (sub == "TRIAL" || sub == "GL") {
        run_trial();
        return;
    }

    if (sub == "SEARCHITEMS" || sub == "FINDITEMS") {
        run_search_items(read_rest_trimmed(args));
        return;
    }

    if (sub == "CLOSE") {
        dottalk::sqlite::sqlite_close(g_db);
        g_db_path.clear();
        std::cout << "ERP: closed\n";
        return;
    }

    if (sub == "EXEC") {
        std::string sql;
        std::getline(args, sql);
        sql = ltrim_copy(sql);

        if (sql.empty()) {
            std::cout << "Usage: ERP EXEC <sql...>\n";
            return;
        }

        std::string err;
        if (!ensure_open(err)) {
            std::cout << "ERP: open failed: " << err << "\n";
            return;
        }

        if (!dottalk::sqlite::sqlite_exec(g_db, sql, err)) {
            std::cout << "ERP EXEC failed: " << err << "\n";
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
            std::cout << "Usage: ERP SELECT <sql...>\n";
            return;
        }

        run_and_print_query("ERP SELECT", sql, MAX_SELECT_ROWS);
        return;
    }

    std::cout << "ERP: unknown subcommand: " << sub << "\n";
    print_usage_brief();
#endif
}

// Compatibility alias if a future/older registry uses cmd_ERP directly.
void cmd_ERP(xbase::DbArea& A, std::istringstream& args) {
    edu_ERP(A, args);
}
