// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: supported

// src/cli/sqlsel_statement.cpp -- see sqlsel_statement.hpp.
//
// P3 slice 1 grammar:
//   SELECT <select-list> FROM <table> [WHERE <predicate>] [LIMIT <n>]
//   <select-list> := '*' | <col> [, <col>]*      (bare column names only in v1)
//
// consumes:
//   cli::find_open_area_by_name_ci        workarea_util.hpp        (P0.2)
//   cli::ScopedEngineArea                 workarea_util.hpp        (P0.2)
//   sqlnorm::sql_to_dottalk_where         expr/sql_normalize.hpp
//   dottalk::expr::compile_bool_predicate cli/expr/value_eval.hpp
//   dottalk::expr::eval_bool_compiled     cli/expr/value_eval.hpp
//   dottalk::build_tuple_from_spec        tuple_builder.hpp        (typed P1.2)
// searched-and-absent:
//   statement parser -- no SELECT/FROM grammar exists anywhere in src/ (verified
//   twice, AIF-073 + AIF-074); this file is the lane's only new capability.

#include "sqlsel_statement.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xbase_field_getters.hpp"
#include "textio.hpp"
#include "workarea_util.hpp"
#include "tuple_builder.hpp"
#include "tuple_types.hpp"
#include "cli/expr/value_eval.hpp"
#include "expr/sql_normalize.hpp"

namespace {

std::string up(std::string s)   { return textio::up(std::move(s)); }
std::string trim(std::string s) { return textio::trim(std::move(s)); }

// Find a top-level keyword (outside single/double quotes), case-insensitive,
// bounded by non-identifier characters. Returns npos when absent.
std::size_t find_kw(const std::string& text, const std::string& kw, std::size_t from = 0) {
    const std::string U = up(text);
    const std::string K = up(kw);
    bool in_s = false, in_d = false;
    for (std::size_t i = from; i + K.size() <= U.size(); ++i) {
        const char c = U[i];
        if (c == '\'' && !in_d) { in_s = !in_s; continue; }
        if (c == '"'  && !in_s) { in_d = !in_d; continue; }
        if (in_s || in_d) continue;
        if (U.compare(i, K.size(), K) != 0) continue;
        const bool left_ok  = (i == 0) ||
                              !(std::isalnum(static_cast<unsigned char>(U[i - 1])) || U[i - 1] == '_');
        const std::size_t after = i + K.size();
        const bool right_ok = (after >= U.size()) ||
                              !(std::isalnum(static_cast<unsigned char>(U[after])) || U[after] == '_');
        if (left_ok && right_ok) return i;
    }
    return std::string::npos;
}

std::vector<std::string> split_csv(const std::string& s) {
    std::vector<std::string> out;
    std::string cur;
    for (const char c : s) {
        if (c == ',') { out.push_back(trim(cur)); cur.clear(); continue; }
        cur.push_back(c);
    }
    const std::string last = trim(cur);
    if (!last.empty()) out.push_back(last);
    return out;
}

// v1 accepts bare column names only: NAME or TABLE.NAME. Anything else (a call,
// an operator, a literal) is reported, never silently mis-projected (R16d).
bool is_bare_column(const std::string& s) {
    if (s.empty()) return false;
    int dots = 0;
    for (std::size_t i = 0; i < s.size(); ++i) {
        const unsigned char c = static_cast<unsigned char>(s[i]);
        if (c == '.') { if (++dots > 1) return false; continue; }
        if (!(std::isalnum(c) || c == '_')) return false;
    }
    if (s.front() == '.' || s.back() == '.') return false;
    return !std::isdigit(static_cast<unsigned char>(s.front()));
}

// Numeric-literal test and typed comparison, matching the engine's P1.4 rule:
// compare numerically when BOTH sides are numeric literals, else as trimmed text.
// One ordering model, shared with relation equality (R16 orthogonality).
bool is_numeric_literal(const std::string& s) {
    if (s.empty()) return false;
    std::size_t i = 0;
    if (s[0] == '+' || s[0] == '-') i = 1;
    bool digit = false, dot = false;
    for (; i < s.size(); ++i) {
        const unsigned char c = static_cast<unsigned char>(s[i]);
        if (std::isdigit(c)) { digit = true; continue; }
        if (c == '.' && !dot) { dot = true; continue; }
        return false;
    }
    return digit;
}

bool value_less(const std::string& a, const std::string& b) {
    if (is_numeric_literal(a) && is_numeric_literal(b)) {
        try { return std::stod(a) < std::stod(b); } catch (...) {}
    }
    return a < b;
}

} // namespace

namespace sqlsel {

void print_statement_usage() {
    std::cout
        << "SQLSEL statement usage:\n"
        << "  SQLSEL <col>[,<col>...] FROM <table>\n"
        << "         [WHERE <predicate>] [ORDER BY <field> [ASC|DESC]] [LIMIT <n>]\n"
        << "  SQLSEL * FROM <table>\n"
        << "  SQLSEL COUNT(*) FROM <table> [WHERE <predicate>]\n"
        << "Notes:\n"
        << "  SQLSEL is itself the select verb; the SELECT keyword is OPTIONAL\n"
        << "  (SQLSEL SELECT ... still parses). Not to be confused with xBase\n"
        << "  SELECT <area>, which switches the active work area.\n"
        << "  The table must be OPEN (USE <table>) -- SQLSEL reads open work areas.\n"
        << "  v1 accepts bare column names; expression projection is not yet supported.\n"
        << "  A statement does not change the current area or any record pointer.\n";
}

bool try_execute_select(const std::string& tail_in) {
    const std::string tail = trim(tail_in);
    if (tail.empty()) return false;

    // OQ-14 (owner ruling, 2026-08-08): the inner SELECT is OPTIONAL. SQLSEL is itself the
    // select verb -- `SQLSEL <list> FROM ...` is canonical; `SQLSEL SELECT <list> FROM ...`
    // still parses. A SQL select is identified by a top-level FROM; a LEADING SELECT is
    // consumed if present. No FROM with a leading SELECT is a malformed select (reported);
    // no FROM and no SELECT is not our statement, so the caller keeps its legacy scan path.
    const bool had_select = (find_kw(tail, "SELECT") == 0);
    const std::size_t list_start = had_select ? 6 : 0;   // skip a leading "SELECT" (6 chars)

    const std::size_t from_pos = find_kw(tail, "FROM", list_start);
    if (from_pos == std::string::npos) {
        if (!had_select) return false;   // no SELECT, no FROM -> legacy predicate-scan path
        std::cout << "SQLSEL: expected FROM after the select list.\n";
        print_statement_usage();
        return true;
    }

    const std::string select_list = trim(tail.substr(list_start, from_pos - list_start));
    if (select_list.empty()) {
        std::cout << "SQLSEL: the select list is empty.\n";
        print_statement_usage();
        return true;
    }

    // Optional trailing clauses, in grammar order.
    const std::size_t where_pos = find_kw(tail, "WHERE", from_pos + 4);
    const std::size_t order_pos = find_kw(tail, "ORDER", from_pos + 4);
    const std::size_t limit_pos = find_kw(tail, "LIMIT", from_pos + 4);

    std::size_t from_end = tail.size();
    if (where_pos != std::string::npos) from_end = std::min(from_end, where_pos);
    if (order_pos != std::string::npos) from_end = std::min(from_end, order_pos);
    if (limit_pos != std::string::npos) from_end = std::min(from_end, limit_pos);

    const std::string table_clause = trim(tail.substr(from_pos + 4, from_end - (from_pos + 4)));
    std::string table_name;
    {
        std::istringstream ts(table_clause);
        ts >> table_name;
        std::string extra;
        if (ts >> extra) {
            std::cout << "SQLSEL: unexpected token '" << extra << "' after the table name.\n";
            std::cout << "        v1 reads a single table; joins arrive with the join phase.\n";
            return true;
        }
    }
    if (table_name.empty()) {
        std::cout << "SQLSEL: expected a table name after FROM.\n";
        print_statement_usage();
        return true;
    }

    std::string where_text;
    if (where_pos != std::string::npos) {
        std::size_t where_end = tail.size();
        if (order_pos != std::string::npos && order_pos > where_pos) where_end = std::min(where_end, order_pos);
        if (limit_pos != std::string::npos && limit_pos > where_pos) where_end = std::min(where_end, limit_pos);
        where_text = trim(tail.substr(where_pos + 5, where_end - (where_pos + 5)));
        if (where_text.empty()) {
            std::cout << "SQLSEL: WHERE requires a predicate.\n";
            return true;
        }
    }

    // ORDER BY <field> [ASC|DESC]
    std::string order_field;
    bool order_desc = false;
    if (order_pos != std::string::npos) {
        std::size_t order_end = tail.size();
        if (limit_pos != std::string::npos && limit_pos > order_pos) order_end = limit_pos;
        std::string order_text = trim(tail.substr(order_pos + 5, order_end - (order_pos + 5)));
        std::istringstream os(order_text);
        std::string by_tok;
        os >> by_tok;
        if (up(by_tok) != "BY") {
            std::cout << "SQLSEL: expected ORDER BY <field> [ASC|DESC].\n";
            return true;
        }
        os >> order_field;
        if (order_field.empty()) {
            std::cout << "SQLSEL: ORDER BY requires a field name.\n";
            return true;
        }
        std::string dir;
        if (os >> dir) {
            const std::string D = up(dir);
            if (D == "DESC")      order_desc = true;
            else if (D != "ASC") {
                std::cout << "SQLSEL: ORDER BY direction must be ASC or DESC (got '" << dir << "').\n";
                return true;
            }
        }
        if (!is_bare_column(order_field)) {
            std::cout << "SQLSEL: ORDER BY accepts a bare field name (got '" << order_field << "').\n";
            return true;
        }
        // strip any TABLE. prefix for the field read
        const std::size_t dot = order_field.find('.');
        if (dot != std::string::npos) order_field = order_field.substr(dot + 1);
    }

    long long limit_n = -1;
    if (limit_pos != std::string::npos) {
        const std::string limit_text = trim(tail.substr(limit_pos + 5));
        try {
            std::size_t used = 0;
            limit_n = std::stoll(limit_text, &used);
            if (used != limit_text.size() || limit_n < 0) throw std::invalid_argument("bad");
        } catch (...) {
            std::cout << "SQLSEL: LIMIT expects a non-negative integer (got '" << limit_text << "').\n";
            return true;
        }
    }

    // --- resolve FROM against OPEN work areas (statement-scoped) -------------
    xbase::DbArea* area = cli::find_open_area_by_name_ci(table_name);
    if (!area) {
        std::cout << "SQLSEL: table '" << table_name << "' is not open.\n";
        std::cout << "        Open it first (USE " << table_name
                  << ") -- SQLSEL reads open work areas.\n";
        return true;
    }

    // --- build the projection spec ------------------------------------------
    const std::string area_label = table_name;
    std::string spec;

    // COUNT(*) -- an aggregate, not a projection: one row, one column.
    std::string count_norm;
    for (const char c : select_list) {
        if (!std::isspace(static_cast<unsigned char>(c))) count_norm.push_back(c);
    }
    const bool count_star = (up(count_norm) == "COUNT(*)");
    if (count_star && !order_field.empty()) {
        std::cout << "SQLSEL: ORDER BY does not apply to COUNT(*).\n";
        return true;
    }

    const bool star = (trim(select_list) == "*");
    if (count_star) {
        spec.clear();   // no projection needed
    } else if (star) {
        spec = area_label + ".*";
    } else {
        const std::vector<std::string> cols = split_csv(select_list);
        if (cols.empty()) {
            std::cout << "SQLSEL: the select list is empty.\n";
            return true;
        }
        for (const auto& c : cols) {
            if (!is_bare_column(c)) {
                std::cout << "SQLSEL: '" << c << "' is not a bare column name.\n";
                std::cout << "        v1 projects bare columns only; expression projection\n";
                std::cout << "        is not yet supported (it would report empty values).\n";
                return true;
            }
            if (!spec.empty()) spec.push_back(',');
            spec += (c.find('.') == std::string::npos) ? (area_label + "." + c) : c;
        }
    }

    // --- compile the predicate ONCE (not per row) ----------------------------
    std::shared_ptr<dottalk::expr::CompiledPredicate> pred;
    if (!where_text.empty()) {
        const std::string dt_where = sqlnorm::sql_to_dottalk_where(where_text);
        pred = dottalk::expr::compile_bool_predicate(*area, dt_where, /*allow_raw=*/false);
        if (!pred) {
            std::cout << "SQLSEL: could not compile the WHERE predicate: " << where_text << "\n";
            return true;
        }
    }

    // --- scan, projecting each surviving row ---------------------------------
    // Cursor neutrality (R16b): remember where every cursor was and put it back.
    cli::ScopedEngineArea keep_current_area;
    const int64_t saved_recno = static_cast<int64_t>(area->recno());

    dottalk::TupleBuildOptions opts;
    opts.refresh_relations = false;   // a statement must not touch relation state
    opts.strict_fields     = true;    // missing field reports; never a silent blank
    opts.want_header       = false;
    opts.overlay_table_buffer = false; // SELECT projects the same committed truth WHERE scans

    // Two passes. PASS 1 collects every matching recno (plus its sort key when
    // ORDER BY is present); PASS 2 projects. Collecting first is what makes
    // ORDER BY correct: LIMIT must cut the SORTED set, not the scan order.
    struct MatchRow { int64_t recno; std::string key; };
    std::vector<MatchRow> matches;
    long long matched_total = 0;
    std::string scan_error;

    {
        cli::ScopedAreaSelect focus(area);
        bool ok = false;
        try { ok = area->top(); } catch (...) { ok = false; }
        if (ok) {
            const int64_t rec_count = static_cast<int64_t>(area->recCount());
            for (;;) {
                const int64_t cur = static_cast<int64_t>(area->recno());
                if (cur <= 0 || cur > rec_count) break;

                bool keep = true;
                try {
                    if (!area->readCurrent()) break;
                    if (area->isDeleted()) keep = false;
                } catch (...) { break; }

                if (keep && pred) {
                    bool tf = false;
                    std::string perr;
                    if (!dottalk::expr::eval_bool_compiled(*pred, *area, tf, &perr)) {
                        scan_error = "predicate evaluation failed: " +
                                     (perr.empty() ? where_text : perr);
                        break;
                    }
                    keep = tf;
                }

                if (keep) {
                    ++matched_total;
                    if (!count_star) {
                        MatchRow m;
                        m.recno = cur;
                        if (!order_field.empty()) {
                            try { m.key = trim(xfg::getFieldAsString(*area, order_field)); }
                            catch (...) { m.key.clear(); }
                        }
                        matches.push_back(std::move(m));
                    }
                }

                const int64_t prev = static_cast<int64_t>(area->recno());
                bool moved = false;
                try { moved = area->skip(1); } catch (...) { moved = false; }
                if (!moved) break;
                const int64_t next = static_cast<int64_t>(area->recno());
                if (next <= prev || next > rec_count) break;
            }
        }

        if (scan_error.empty() && !count_star && !order_field.empty()) {
            // Field existence check: an unknown ORDER BY field must report, not
            // silently sort every row on an empty key (R16d).
            bool have_field = false;
            try {
                const std::string want = up(order_field);
                for (const auto& fd : area->fields()) {
                    if (up(fd.name) == want) { have_field = true; break; }
                }
            } catch (...) {}
            if (!have_field) {
                scan_error = "ORDER BY field '" + order_field + "' is not in " + table_name + ".";
            } else {
                std::stable_sort(matches.begin(), matches.end(),
                    [&](const MatchRow& a, const MatchRow& b) {
                        return order_desc ? value_less(b.key, a.key)
                                          : value_less(a.key, b.key);
                    });
            }
        }

        // PASS 2: project the (possibly sorted) match set, honoring LIMIT.
        if (scan_error.empty() && !count_star) {
            bool header_done = false;
            std::size_t shown = 0;
            for (const auto& m : matches) {
                if (limit_n >= 0 && static_cast<long long>(shown) >= limit_n) break;
                try {
                    area->gotoRec64(static_cast<std::uint64_t>(m.recno));
                    if (!area->readCurrent()) break;
                } catch (...) { break; }

                const dottalk::TupleBuildResult r = dottalk::build_tuple_from_spec(spec, opts);
                if (!r.ok) { scan_error = "projection failed: " + r.error; break; }

                if (!header_done) {
                    std::string head;
                    for (std::size_t i = 0; i < r.row.columns.size(); ++i) {
                        if (i) head += " | ";
                        head += r.row.columns[i].name;
                    }
                    std::cout << head << "\n";
                    header_done = true;
                }

                std::string line;
                for (std::size_t i = 0; i < r.row.values.size(); ++i) {
                    if (i) line += " | ";
                    line += trim(r.row.values[i]);
                }
                std::cout << line << "\n";
                ++shown;
            }
        }

        // Restore this area's record pointer. gotoRec64 is the authoritative
        // RECNO64 positioning call; the 32-bit gotoRec() adapter must not be
        // used by new x64 code.
        try {
            if (saved_recno >= 1) {
                area->gotoRec64(static_cast<std::uint64_t>(saved_recno));
                area->readCurrent();
            }
        } catch (...) {}
    }

    if (!scan_error.empty()) {
        std::cout << "SQLSEL: " << scan_error << "\n";
        return true;
    }

    if (count_star) {
        std::cout << "COUNT(*)\n" << matched_total << "\n";
        std::cout << "1 row(s) selected.\n";
        return true;
    }

    const long long shown = (limit_n >= 0 && limit_n < static_cast<long long>(matches.size()))
                          ? limit_n : static_cast<long long>(matches.size());
    std::cout << shown << " row(s) selected.\n";
    if (limit_n >= 0 && static_cast<long long>(matches.size()) > limit_n) {
        std::cout << "SQLSEL: LIMIT reached; " << (static_cast<long long>(matches.size()) - limit_n)
                  << " more row(s) available.\n";
    }
    if (!order_field.empty()) {
        // Report the access path. A plan choice is never silent: this v1 always
        // materializes and sorts; the index-ordered path arrives with the first
        // production seek() consumer (P1.5).
        std::cout << "SQLSEL: ORDER BY " << order_field
                  << (order_desc ? " DESC" : " ASC")
                  << " -- materialized sort over " << matched_total << " matching row(s).\n";
    }
    return true;
}

} // namespace sqlsel
