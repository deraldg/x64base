// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_sql.cpp
// SQL command -- COUNT with optional ALL|DELETED and FOR <expr>.
// Uses shared DotTalk evaluator + LRU cache (DOTTALK_WHERECACHE, default 256).
//
// Change: Suppress "false" per-record logs by default. Print per-record lines
// only for matches (ok==true). Use VERBOSE to print all (true/false) details.
//
// Change (AIF-074, 2026-07-29): COUNT now reports the number WITHOUT the
// per-match lines. The earlier behavior printed one line per hit even when the
// caller asked only for a count -- 90 lines before the answer on the students
// fixture. VERBOSE still prints every row, so no detail is lost, and a bare
// predicate scan (no COUNT) still lists its matches as before. Also: the seven
// SQL DEBUG emitters were unconditional and are now behind VERBOSE.

// @dottalk.usage v1
// owner: DOT|SQL
// command: SQL
// category: sql
// status: experimental
// noargs: scan/report
// effect: query
// mutates: cursor-temporary
// usage-access: SQL USAGE
// summary:
//   Evaluate SQL-like COUNT/FOR predicates over the current DBF work area.
//
// usage:
//   SQL USAGE
//   SQL [COUNT] [ALL|DELETED] [FOR <expr> | <expr>] [VERBOSE]
//
// examples:
//   SQL COUNT
//   SQL COUNT ALL
//   SQL COUNT DELETED
//   SQL COUNT FOR GPA >= 3.0
//   SQL LNAME = "SMITH"
//   SQL VERBOSE COUNT FOR GPA >= 3.0
//
// notes:
//   SQL USAGE prints usage before open-table checks.
//   SQL reads records and may temporarily move the cursor.
//   SQL does not mutate table data.
//   COUNT reports the number only. A bare predicate scan lists its matches.
//   VERBOSE prints every record with its true/false verdict, plus scan diagnostics.
//   SQL DOES NOT EXECUTE SQL STATEMENTS. The name is historical: this command
//   scans the CURRENT area with a predicate and reports matches or a count.
//   Family boundary, stated here because the three names invite confusion:
//     SQL     -- predicate scan/count over the current area (this command)
//     SQLSEL  -- SQLsel, the SELECT statement surface over a named open table
//     SQLITE  -- the SQLite bridge, for talking to an actual SQLite database
//   SQLSEL also accepts this same predicate-scan form for compatibility, so
//   `SQL COUNT FOR <expr>` and `SQLSEL COUNT FOR <expr>` are equivalent.
//
// risk:
//   requires_open_table: yes except usage
//   scans_records: yes
//   mutates_cursor: temporary
//   mutates_table_data: no
//
// related:
//   SQLSEL
//   WHERE
//   WHERECACHE
//
#include "xbase.hpp"
#include "xbase_field_getters.hpp"
#include "record_view.hpp"
#include "textio.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <set>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

#include "cli/expr/api.hpp"
#include "cli/expr/for_parser.hpp"
#include "expr/sql_normalize.hpp"
#include "cli/where_eval_shared.hpp"  // shared evaluator + env/LRU cache

using where_eval::dt_trim;
using where_eval::dt_upcase;

namespace { // ---------- local helpers ----------

static inline std::string up(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return (char)std::toupper(c); });
    return s;
}

// Remove standalone token (case-insensitive) from a string. Returns (new, removed?)
static std::pair<std::string,bool> strip_token_ci(const std::string& text, const std::string& token) {
    std::istringstream ss(text);
    std::ostringstream out;
    std::string w;
    bool removed = false;
    bool first = true;
    const std::string TOKEN = up(token);
    while (ss >> w) {
        if (up(w) == TOKEN) { removed = true; continue; }
        if (!first) out << ' ';
        out << w;
        first = false;
    }
    return { out.str(), removed };
}

// Deleted-record handling
enum class DelMode { SkipDeleted, OnlyDeleted, IncludeAll };

struct Opts {
    DelMode     mode      = DelMode::SkipDeleted;
    bool        haveFor   = false;
    bool        verbose   = false;
    bool        wantCount = false;  // COUNT was requested: report the number, not the rows
    std::string forRaw;    // expression after FOR, or whole expr if no "FOR"
    std::string tailRaw;   // everything after SQL keyword (for debug echo)
};

// Parse: SQL [VERBOSE] [COUNT] [ALL|DELETED] [FOR <expr> | <expr>] [VERBOSE]
static Opts parse_opts(std::istringstream& iss) {
    Opts o;

    // Rebuild unconsumed tail from the stream
    std::string rest;
    {
        const std::string& all = iss.str();
        auto pos = iss.tellg();
        if (pos != std::istringstream::pos_type(-1)) {
            size_t i = static_cast<size_t>(pos);
            if (i < all.size()) rest = all.substr(i);
        } else {
            rest = all;
        }
    }
    rest = dt_trim(rest);

    // Allow VERBOSE anywhere: first strip once, then again after we reshape.
    {
        auto [t1, found1] = strip_token_ci(rest, "VERBOSE");
        o.verbose = o.verbose || found1;
        rest = t1;
    }

    o.tailRaw = dt_trim(rest);

    std::istringstream head(o.tailRaw);

    // Optional COUNT. AIF-074: the token used to be read and DISCARDED, so the
    // command could not tell `SQL COUNT ...` from a bare predicate scan and
    // printed a per-match line for every hit either way. Asking for a count and
    // receiving 90 detail lines before the number is not an answer to the
    // question asked. Record it.
    std::streampos afterFirst = head.tellg();
    std::string t;
    if (head >> t) {
        if (up(t) == "COUNT") {
            o.wantCount = true;
        } else {
            head.clear();
            head.seekg(afterFirst);
        }
    }

    // Optional ALL | DELETED
    std::streampos afterMode = head.tellg();
    std::string modeTok;
    if (head >> modeTok) {
        const auto M = up(modeTok);
        if      (M == "ALL")     o.mode = DelMode::IncludeAll;
        else if (M == "DELETED") o.mode = DelMode::OnlyDeleted;
        else { head.clear(); head.seekg(afterMode); }
    }

    // Remaining text as potential FOR or raw expr
    std::string tail; std::getline(head, tail);
    tail = dt_trim(tail);

    // Permit a trailing VERBOSE as well
    {
        auto [t2, found2] = strip_token_ci(tail, "VERBOSE");
        o.verbose = o.verbose || found2;
        tail = dt_trim(t2);
    }

    if (!tail.empty()) {
        auto U = up(tail);
        if (U.rfind("FOR", 0) == 0) {
            o.haveFor = true;
            o.forRaw = dt_trim(tail.substr(3));
        } else {
            o.haveFor = true;
            o.forRaw = tail;
        }
    }

    return o;
}

// Record filter by deleted flag
static inline bool include_row(bool deleted, DelMode mode) {
    if (mode == DelMode::SkipDeleted && deleted)  return false;
    if (mode == DelMode::OnlyDeleted && !deleted) return false;
    return true;
}

} // anon

// ---------- command ----------
static void print_sql_usage_contract()
{
    std::cout
        << "Usage:\n"
        << "  SQL USAGE\n"
        << "  SQL [COUNT] [ALL|DELETED] [FOR <expr> | <expr>] [VERBOSE]\n"
        << "Examples:\n"
        << "  SQL COUNT\n"
        << "  SQL COUNT ALL\n"
        << "  SQL COUNT DELETED\n"
        << "  SQL COUNT FOR GPA >= 3.0\n"
        << "  SQL LNAME = \"SMITH\"\n"
        << "  SQL VERBOSE COUNT FOR GPA >= 3.0\n"
        << "Notes:\n"
        << "  - SQL USAGE does not require an open table.\n"
        << "  - SQL scans records and does not mutate table data.\n"
        << "  - SQL does NOT execute SQL statements. The name is historical.\n"
        << "Looking for something else?\n"
        << "  SQLSEL  -- SELECT statements: SQLSEL SELECT <cols> FROM <table> ...\n"
        << "  SQLITE  -- the SQLite bridge, for an actual SQLite database\n";
}

static bool sql_usage_contract(std::string tok)
{
    std::transform(tok.begin(), tok.end(), tok.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return tok == "USAGE" || tok == "HELP" || tok == "?";
}
void cmd_SQL(xbase::DbArea& A, std::istringstream& iss) {
    // SQL_USAGE_CONTRACT_BRANCH
    {
        const std::streampos usage_pos = iss.tellg();
        std::string usage_tok;
        if (iss >> usage_tok) {
            iss.clear();
            if (usage_pos != std::streampos(-1)) {
                iss.seekg(usage_pos);
            }

            if (sql_usage_contract(usage_tok)) {
                print_sql_usage_contract();
                return;
            }

            // AIF-074: SQL is a predicate scanner, not a statement executor, but
            // its name invites `SQL SELECT ... FROM ...`. Without this guard that
            // line is parsed as a PREDICATE and reports a confusing failure or a
            // false zero -- the silent-nonsense class this lane closed elsewhere.
            // Redirect to the command that does own the grammar.
            {
                std::string lead = textio::up(usage_tok);
                if (lead == "SELECT") {
                    std::cout << "SQL: SELECT statements are not run by SQL.\n"
                              << "     SQL scans the current area with a predicate; the name is historical.\n"
                              << "     Use SQLSEL for statements:\n"
                              << "       SQLSEL SELECT <col>[,<col>...] FROM <table>\n"
                              << "              [WHERE <predicate>] [ORDER BY <field> [ASC|DESC]] [LIMIT <n>]\n"
                              << "     See SQLSEL USAGE. For an actual SQLite database, see SQLITE USAGE.\n";
                    return;
                }
            }
        } else {
            iss.clear();
            if (usage_pos != std::streampos(-1)) {
                iss.seekg(usage_pos);
            }
        }
    }

    if (!A.isOpen()) { std::cout << "No file open\n"; return; }

    const Opts opt = parse_opts(iss);

    if (opt.verbose) std::cout << "SQL DEBUG -- raw: \"" << opt.tailRaw << "\"\n";

    std::vector<std::string> debug_fields;
    std::shared_ptr<const where_eval::CacheEntry> ce;

    if (opt.haveFor) {
        const std::string normalized = sqlnorm::sql_to_dottalk_where(opt.forRaw);
        if (opt.verbose) std::cout << "SQL DEBUG -- normalized: " << normalized << "\n";

        // Fields to print per-record when we emit lines
        debug_fields = where_eval::extract_field_names(normalized);
        if (!debug_fields.empty()) {
            if (opt.verbose) {
                std::cout << "SQL DEBUG -- fields: ";
                for (size_t i=0;i<debug_fields.size();++i) {
                    if (i) std::cout << ", ";
                    std::cout << debug_fields[i];
                }
                std::cout << "\n";
            }
        } else {
            if (opt.verbose) std::cout << "SQL DEBUG -- fields: (none detected)\n";
        }

        try {
            // Compile via shared env/LRU cache
            ce = where_eval::compile_where_expr_cached(opt.forRaw);
            if (opt.verbose) std::cout << "SQL DEBUG -- compiled: " << where_eval::plan_kind(*ce->plan) << "\n";
        } catch (const std::exception& ex) {
            std::cout << "Syntax error in FOR: " << ex.what() << "\n";
            return;
        }
    } else {
        if (opt.verbose) std::cout << "SQL DEBUG -- no clause (plain COUNT)\n";
    }

    long long cnt = 0, scanned = 0;

    if (A.top() && A.readCurrent()) {
        do {
            ++scanned;
            if (!include_row(A.isDeleted(), opt.mode)) continue;

            const bool ok = (!opt.haveFor) ? true : where_eval::run_program(*ce->plan, A);

            // Per-record output policy:
            // - VERBOSE: print every record with true/false
            // - Default: print matches only; suppress false lines entirely
            if (opt.verbose) {
                if (debug_fields.empty()) {
                    std::cout << "[rec " << A.recno() << "] => " << (ok ? "true" : "false") << "\n";
                } else {
                    std::ostringstream fv;
                    fv << "[rec " << A.recno() << "] ";
                    for (size_t i=0;i<debug_fields.size();++i) {
                        const std::string& fld = debug_fields[i];

                        std::string s;
                        try { s = xfg::getFieldAsString(A, fld); } catch (...) { s = "(ERR)"; }
                        fv << fld << "=\"" << dt_upcase(dt_trim(s)) << "\"";

                        try {
                            double n = xfg::getFieldAsNumber(A, fld);
                            if (std::isfinite(n)) fv << " (num=" << n << ")";
                        } catch (...) {}

                        if (i+1 < debug_fields.size()) fv << ", ";
                    }
                    fv << " => " << (ok ? "true" : "false");
                    std::cout << fv.str() << "\n";
                }
            } else if (ok && !opt.wantCount) {
                // Non-verbose: emit only matches (or nothing if none).
                // Suppressed under COUNT -- the caller asked for a number.
                // VERBOSE still shows every row, so the detail is never lost.
                if (debug_fields.empty()) {
                    std::cout << "[rec " << A.recno() << "]\n";
                } else {
                    std::ostringstream fv;
                    fv << "[rec " << A.recno() << "] ";
                    for (size_t i=0;i<debug_fields.size();++i) {
                        const std::string& fld = debug_fields[i];

                        std::string s;
                        try { s = xfg::getFieldAsString(A, fld); } catch (...) { s = "(ERR)"; }
                        fv << fld << "=\"" << dt_upcase(dt_trim(s)) << "\"";

                        try {
                            double n = xfg::getFieldAsNumber(A, fld);
                            if (std::isfinite(n)) fv << " (num=" << n << ")";
                        } catch (...) {}

                        if (i+1 < debug_fields.size()) fv << ", ";
                    }
                    std::cout << fv.str() << "\n";
                }
            }

            if (ok) ++cnt;

        } while (A.skip(+1) && A.readCurrent());
    }

    if (opt.verbose) std::cout << "SQL DEBUG -- scanned: " << scanned << "  matched: " << cnt << "\n";
    std::cout << cnt << "\n";
}



