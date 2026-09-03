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
//   dottalk::expr::compile_bool_predicate cli/expr/value_eval.hpp
//   dottalk::expr::eval_bool_compiled     cli/expr/value_eval.hpp
//   dottalk::build_tuple_from_spec        tuple_builder.hpp        (typed P1.2)
// searched-and-absent:
//   statement parser -- no SELECT/FROM grammar exists anywhere in src/ (verified
//   twice, AIF-073 + AIF-074); this file is the lane's only new capability.

#include "sqlsel_statement.hpp"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <memory>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xbase_field_getters.hpp"
#include "xbase_locks.hpp"
#include "cli/workarea_cursor_restore.hpp"
#include "textio.hpp"
#include "workarea_util.hpp"
#include "tuple_builder.hpp"
#include "tuple_types.hpp"
#include "cli/expr/value_eval.hpp"
#include "cli/expr/api.hpp"
#include "expr_tuple_glue.hpp"
#include "xindex/attach.hpp"
#include "xindex/index_manager.hpp"

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

bool value_equal(const std::string& a_raw, const std::string& b_raw) {
    const std::string a = trim(a_raw);
    const std::string b = trim(b_raw);
    if (!a.empty() && !b.empty() && is_numeric_literal(a) && is_numeric_literal(b)) {
        try { return std::stod(a) == std::stod(b); } catch (...) {}
    }
    return a == b;
}

bool is_identifier(const std::string& s) {
    if (s.empty() || std::isdigit(static_cast<unsigned char>(s.front()))) return false;
    return std::all_of(s.begin(), s.end(), [](unsigned char c) {
        return std::isalnum(c) || c == '_';
    });
}

struct TableRef {
    std::string name;
    std::string alias;
    xbase::DbArea* area = nullptr;
};

bool parse_table_ref(const std::string& text, TableRef& out, std::string& error) {
    std::istringstream in(text);
    std::vector<std::string> words;
    for (std::string word; in >> word;) words.push_back(word);
    if (words.empty()) {
        error = "expected a table name";
        return false;
    }
    if (words.size() == 1) {
        out.name = words[0];
        out.alias = words[0];
    } else if (words.size() == 2) {
        out.name = words[0];
        out.alias = words[1];
    } else if (words.size() == 3 && up(words[1]) == "AS") {
        out.name = words[0];
        out.alias = words[2];
    } else {
        error = "expected <table> [AS] <alias>";
        return false;
    }
    if (!is_identifier(out.name) || !is_identifier(out.alias)) {
        error = "table names and aliases must be identifiers";
        return false;
    }
    return true;
}

struct ResolvedColumn {
    int side = -1;
    std::size_t field_index = 0;
    std::string label;
    char type = ' ';
};

std::optional<std::size_t> field_index_ci(xbase::DbArea& area, const std::string& name) {
    const auto& fields = area.fields();
    const std::string want = up(name);
    for (std::size_t i = 0; i < fields.size(); ++i) {
        if (up(fields[i].name) == want) return i;
    }
    return std::nullopt;
}

bool qualifier_matches(const TableRef& table, const std::string& qualifier) {
    return up(qualifier) == up(table.alias) || up(qualifier) == up(table.name);
}

bool resolve_join_column(const std::string& token,
                         const TableRef& left,
                         const TableRef& right,
                         bool require_qualified,
                         ResolvedColumn& out,
                         std::string& error) {
    if (!is_bare_column(token)) {
        error = "'" + token + "' is not a column name";
        return false;
    }
    const std::size_t dot = token.find('.');
    const std::string qualifier = dot == std::string::npos ? "" : token.substr(0, dot);
    const std::string field = dot == std::string::npos ? token : token.substr(dot + 1);
    if (require_qualified && qualifier.empty()) {
        error = "JOIN ON columns must be qualified (got '" + token + "')";
        return false;
    }

    const bool may_left = qualifier.empty() || qualifier_matches(left, qualifier);
    const bool may_right = qualifier.empty() || qualifier_matches(right, qualifier);
    const auto li = may_left ? field_index_ci(*left.area, field) : std::nullopt;
    const auto ri = may_right ? field_index_ci(*right.area, field) : std::nullopt;
    if (li && ri) {
        error = "column '" + token + "' is ambiguous; qualify it with a table alias";
        return false;
    }
    if (!li && !ri) {
        error = "column '" + token + "' was not found in either joined table";
        return false;
    }
    out.side = li ? 0 : 1;
    out.field_index = li ? *li : *ri;
    const auto& fd = (li ? left.area : right.area)->fields()[out.field_index];
    out.type = fd.type;
    out.label = (li ? left.alias : right.alias) + "." + fd.name;
    return true;
}

// SQLSEL JOIN is a statement over two independently open xBase tables. Saving
// two cursors makes the statement session-neutral; it does not make the two
// reads one point in time. This guard does that with the engine's own
// cooperative FLOCK seam. Both locks are taken without waiting, in a path-based
// canonical order, so two reversed JOINs cannot form an AB-BA wait. A lock the
// current owner already held is borrowed and never released by SQLSEL.
struct JoinReadTransaction {
    struct Held {
        xbase::DbArea* area = nullptr;
        bool acquired_here = false;
    };

    std::array<Held, 2> held{};
    std::size_t held_count = 0;
    std::string first_name;
    std::string second_name;
    std::string error;
    bool ready = false;

    static std::string path_key(const xbase::DbArea& area) {
        const std::string raw = std::filesystem::path(area.filename())
                                    .lexically_normal().generic_string();
        return up(raw) + "\n" + raw;
    }

    static std::string table_name(const xbase::DbArea& area) {
        return up(std::filesystem::path(area.filename()).stem().string());
    }

    static bool owned_by_current_process(const xbase::DbArea& area) {
        xbase::locks::LockHolder holder;
        return xbase::locks::table_lock_holder(area, &holder) &&
               holder.owner_id == xbase::locks::current_owner().id;
    }

    JoinReadTransaction(xbase::DbArea& a, xbase::DbArea& b) {
        std::array<xbase::DbArea*, 2> order{{&a, &b}};
        std::sort(order.begin(), order.end(), [](const auto* lhs, const auto* rhs) {
            return path_key(*lhs) < path_key(*rhs);
        });
        first_name = table_name(*order[0]);
        second_name = table_name(*order[1]);

        for (xbase::DbArea* area : order) {
            const bool borrowed = owned_by_current_process(*area);
            std::string lock_error;
            if (!xbase::locks::try_lock_table(*area, &lock_error)) {
                error = table_name(*area) + ": " +
                        (lock_error.empty() ? "table lock refused" : lock_error);
                release_acquired();
                return;
            }
            held[held_count++] = Held{area, !borrowed};
        }
        ready = true;
    }

    ~JoinReadTransaction() { release_acquired(); }

    JoinReadTransaction(const JoinReadTransaction&) = delete;
    JoinReadTransaction& operator=(const JoinReadTransaction&) = delete;

private:
    void release_acquired() noexcept {
        while (held_count > 0) {
            Held& one = held[--held_count];
            if (one.acquired_here && one.area) {
                std::string ignored;
                (void)xbase::locks::unlock_table(
                    *one.area, xbase::locks::current_owner(), &ignored);
            }
        }
    }
};

bool read_area_row(xbase::DbArea& area, std::vector<std::string>& values) {
    try {
        if (!area.readCurrent()) return false;
        values.clear();
        values.reserve(area.fields().size());
        for (const auto& fd : area.fields()) values.push_back(xfg::getFieldAsString(area, fd.name));
        return true;
    } catch (...) {
        return false;
    }
}

enum class PredicateState { True, False, Error };

struct PredicateVerdict {
    PredicateState state = PredicateState::Error;
    std::string error;
};

// NULL-READY: predicate truth is an enum, never a bool. UNKNOWN can be added
// without changing SQLsel's evaluator seam or every caller signature (R29).
PredicateVerdict evaluate_tuple_predicate(const dottalk::expr::Expr* program,
                                          const dottalk::TupleRow& row) {
    if (!program) return {PredicateState::True, {}};
    try {
        const auto view = dottalk::exprglue::make_record_view(row);
        return {program->eval(view) ? PredicateState::True : PredicateState::False, {}};
    } catch (const std::exception& ex) {
        return {PredicateState::Error, ex.what()};
    } catch (...) {
        return {PredicateState::Error, "unknown predicate evaluation error"};
    }
}

// P4.1/P4.2 are deliberately independent of REL/SET RELATION (R17/R21/R27).
// The correctness-first nested loop remains the fallback. When the inner ON
// field is the active tag of an attached CDX/LMDB index, P4.2 probes that tag
// and still re-verifies every landed row against the ON comparison.
bool execute_inner_join(const std::string& select_list,
                        const std::string& from_clause,
                        const std::string& where_text,
                        const std::string& order_token,
                        bool order_desc,
                        long long limit_n) {
    const std::size_t join_pos = find_kw(from_clause, "JOIN");
    if (join_pos == std::string::npos) return false;
    if (find_kw(from_clause, "JOIN", join_pos + 4) != std::string::npos) {
        std::cout << "SQLSEL: P4.1 accepts exactly one INNER JOIN.\n";
        return true;
    }

    std::string left_text = trim(from_clause.substr(0, join_pos));
    const std::size_t inner_pos = find_kw(left_text, "INNER");
    if (inner_pos != std::string::npos) {
        if (trim(left_text.substr(inner_pos)) != "INNER" && up(trim(left_text.substr(inner_pos))) != "INNER") {
            std::cout << "SQLSEL: expected [INNER] JOIN.\n";
            return true;
        }
        left_text = trim(left_text.substr(0, inner_pos));
    }

    const std::string after_join = trim(from_clause.substr(join_pos + 4));
    const std::size_t on_pos = find_kw(after_join, "ON");
    if (on_pos == std::string::npos) {
        std::cout << "SQLSEL: INNER JOIN requires ON <left-column> = <right-column>.\n";
        return true;
    }
    const std::string right_text = trim(after_join.substr(0, on_pos));
    const std::string on_text = trim(after_join.substr(on_pos + 2));

    TableRef left, right;
    std::string error;
    if (!parse_table_ref(left_text, left, error) || !parse_table_ref(right_text, right, error)) {
        std::cout << "SQLSEL: " << error << ".\n";
        return true;
    }
    if (up(left.alias) == up(right.alias)) {
        std::cout << "SQLSEL: joined table aliases must be distinct.\n";
        return true;
    }
    left.area = cli::find_open_area_by_name_ci(left.name);
    right.area = cli::find_open_area_by_name_ci(right.name);
    if (!left.area || !right.area) {
        const std::string missing = !left.area ? left.name : right.name;
        std::cout << "SQLSEL: table '" << missing << "' is not open.\n";
        std::cout << "        Open both joined tables first -- SQLSEL reads open work areas.\n";
        return true;
    }
    if (left.area == right.area) {
        std::cout << "SQLSEL: P4.1 joins two distinct open tables; self-join is not yet supported.\n";
        return true;
    }
    std::unique_ptr<dottalk::expr::Expr> where_program;
    if (!where_text.empty()) {
        // Qualified names and function calls are already part of the repaired
        // AST grammar. The legacy SQL normalizer predates both and erases '.'.
        auto compiled = dottalk::expr::compile_where(where_text);
        if (!compiled) {
            std::cout << "SQLSEL: could not compile the WHERE predicate: " << where_text
                      << " (" << compiled.error << ")\n";
            return true;
        }
        where_program = std::move(compiled.program);
    }

    const std::size_t eq = on_text.find('=');
    if (eq == std::string::npos || on_text.find('=', eq + 1) != std::string::npos) {
        std::cout << "SQLSEL: P4.1 JOIN ON requires one equi-key comparison.\n";
        return true;
    }
    ResolvedColumn on_left, on_right;
    if (!resolve_join_column(trim(on_text.substr(0, eq)), left, right, true, on_left, error) ||
        !resolve_join_column(trim(on_text.substr(eq + 1)), left, right, true, on_right, error)) {
        std::cout << "SQLSEL: " << error << ".\n";
        return true;
    }
    if (on_left.side == on_right.side) {
        std::cout << "SQLSEL: JOIN ON must compare one column from each table.\n";
        return true;
    }
    if (on_left.side == 1) std::swap(on_left, on_right);

    std::vector<ResolvedColumn> projection;
    std::string count_norm;
    for (const char c : select_list) {
        if (!std::isspace(static_cast<unsigned char>(c))) count_norm.push_back(c);
    }
    const bool count_star = up(count_norm) == "COUNT(*)";
    if (!count_star) {
        if (trim(select_list) == "*") {
            for (std::size_t i = 0; i < left.area->fields().size(); ++i) {
                const auto& fd = left.area->fields()[i];
                projection.push_back({0, i, left.alias + "." + fd.name, fd.type});
            }
            for (std::size_t i = 0; i < right.area->fields().size(); ++i) {
                const auto& fd = right.area->fields()[i];
                projection.push_back({1, i, right.alias + "." + fd.name, fd.type});
            }
        } else {
            for (const auto& token : split_csv(select_list)) {
                ResolvedColumn col;
                if (!resolve_join_column(token, left, right, false, col, error)) {
                    std::cout << "SQLSEL: " << error << ".\n";
                    return true;
                }
                projection.push_back(std::move(col));
            }
        }
    }

    std::optional<ResolvedColumn> order_col;
    if (!order_token.empty()) {
        if (count_star) {
            std::cout << "SQLSEL: ORDER BY does not apply to COUNT(*).\n";
            return true;
        }
        ResolvedColumn col;
        if (!resolve_join_column(order_token, left, right, false, col, error)) {
            std::cout << "SQLSEL: " << error << ".\n";
            return true;
        }
        order_col = std::move(col);
    }

    struct JoinedRow {
        std::vector<std::string> left_values;
        std::vector<std::string> right_values;
        std::uint64_t left_recno = 0;
        std::uint64_t right_recno = 0;
    };
    std::vector<JoinedRow> rows;
    JoinReadTransaction read_transaction{*left.area, *right.area};
    if (!read_transaction.ready) {
        std::cout << "SQLSEL: INNER JOIN read transaction refused -- "
                  << read_transaction.error << ".\n";
        return true;
    }
    dottalk::tupleaugment::WorkAreaCursorRestore restore;
    cli::ScopedEngineArea keep_current_area;

    std::cout << "SQLSEL: INNER JOIN read transaction -- table fence ("
              << read_transaction.first_name << " -> "
              << read_transaction.second_name << ").\n";

    const std::uint64_t left_count = static_cast<std::uint64_t>(left.area->recCount());
    const std::uint64_t right_count = static_cast<std::uint64_t>(right.area->recCount());
    xindex::IndexManager* inner_index = xindex::manager_if_attached(*right.area);
    const bool index_candidate = inner_index != nullptr &&
                                 inner_index->isCdx() &&
                                 inner_index->activeTagMatchesField(
                                     static_cast<int>(on_right.field_index) + 1);
    std::size_t index_probes = 0;
    std::size_t index_candidates = 0;
    std::size_t scan_probes = 0;

    for (std::uint64_t li = 1; li <= left_count; ++li) {
        std::vector<std::string> lv;
        {
            cli::ScopedAreaSelect focus(left.area);
            left.area->gotoRec64(li);
            if (!read_area_row(*left.area, lv) || left.area->isDeleted()) continue;
        }

        const auto append_match = [&](std::vector<std::string> rv,
                                      std::uint64_t ri) -> bool {
            if (value_equal(lv[on_left.field_index], rv[on_right.field_index])) {
                JoinedRow joined{lv, rv, li, ri};
                if (where_program) {
                    dottalk::TupleRow tuple;
                    for (std::size_t i = 0; i < left.area->fields().size(); ++i) {
                        const auto& fd = left.area->fields()[i];
                        tuple.columns.push_back({left.alias + "." + fd.name,
                                                 -1, fd.name, fd.type,
                                                 static_cast<int>(fd.length), static_cast<int>(fd.decimals)});
                        tuple.values.push_back(lv[i]);
                    }
                    for (std::size_t i = 0; i < right.area->fields().size(); ++i) {
                        const auto& fd = right.area->fields()[i];
                        tuple.columns.push_back({right.alias + "." + fd.name,
                                                 -1, fd.name, fd.type,
                                                 static_cast<int>(fd.length), static_cast<int>(fd.decimals)});
                        tuple.values.push_back(rv[i]);
                    }
                    tuple.fragments.push_back({-1, li, dottalk::TupleSourceKind::DBF,
                                               false, "SQLSEL:" + left.alias});
                    tuple.fragments.push_back({-1, ri, dottalk::TupleSourceKind::DBF,
                                               false, "SQLSEL:" + right.alias});
                    const auto verdict = evaluate_tuple_predicate(where_program.get(), tuple);
                    if (verdict.state == PredicateState::Error) {
                        std::cout << "SQLSEL: predicate evaluation failed: " << verdict.error << "\n";
                        return false;
                    }
                    if (verdict.state == PredicateState::False) return true;
                }
                rows.push_back(std::move(joined));
            }
            return true;
        };

        bool used_index_for_outer = false;
        if (index_candidate) {
            const std::size_t rows_before_probe = rows.size();
            try {
                const xindex::Key key = inner_index->buildActiveTagBaseKeyFromString(
                    lv[on_left.field_index]);
                if (!key.empty()) {
                    auto cursor = inner_index->seek(key);
                    if (cursor) {
                        used_index_for_outer = true;
                        bool probe_usable = true;
                        ++index_probes;
                        xindex::Key landed_key;
                        xindex::RecNo ri = 0;
                        bool found = cursor->first(landed_key, ri);
                        while (found && landed_key == key) {
                            ++index_candidates;
                            std::vector<std::string> rv;
                            {
                                cli::ScopedAreaSelect focus(right.area);
                                if (!right.area->gotoRec64(ri) ||
                                    !read_area_row(*right.area, rv)) {
                                    probe_usable = false;
                                } else if (!right.area->isDeleted()) {
                                    if (!append_match(std::move(rv), ri)) return true;
                                }
                            }
                            if (!probe_usable) break;
                            found = cursor->next(landed_key, ri);
                        }
                        if (!probe_usable) {
                            rows.resize(rows_before_probe);
                            used_index_for_outer = false;
                        }
                    }
                }
            } catch (...) {
                // Correctness outranks acceleration. If a usable-looking index
                // cannot serve this probe, scan this outer row and report the
                // hybrid path rather than returning a partial answer silently.
                rows.resize(rows_before_probe);
                used_index_for_outer = false;
            }
        }

        if (used_index_for_outer) continue;

        ++scan_probes;
        for (std::uint64_t ri = 1; ri <= right_count; ++ri) {
            std::vector<std::string> rv;
            {
                cli::ScopedAreaSelect focus(right.area);
                right.area->gotoRec64(ri);
                if (!read_area_row(*right.area, rv) || right.area->isDeleted()) continue;
            }
            if (!append_match(std::move(rv), ri)) return true;
        }
    }

    const auto cell = [](const JoinedRow& row, const ResolvedColumn& col) -> const std::string& {
        return col.side == 0 ? row.left_values[col.field_index] : row.right_values[col.field_index];
    };
    if (order_col) {
        std::stable_sort(rows.begin(), rows.end(), [&](const JoinedRow& a, const JoinedRow& b) {
            return order_desc ? value_less(trim(cell(b, *order_col)), trim(cell(a, *order_col)))
                              : value_less(trim(cell(a, *order_col)), trim(cell(b, *order_col)));
        });
    }

    if (index_probes > 0 && scan_probes == 0) {
        std::cout << "SQLSEL: INNER JOIN access path -- CDX seek (inner="
                  << right.name << ", tag=" << inner_index->activeTag()
                  << ", probes=" << index_probes
                  << ", candidates=" << index_candidates << ").\n";
    } else if (index_probes > 0) {
        std::cout << "SQLSEL: INNER JOIN access path -- hybrid CDX seek + nested-loop scan"
                  << " (inner=" << right.name << ", tag=" << inner_index->activeTag()
                  << ", index probes=" << index_probes
                  << ", scan probes=" << scan_probes << ").\n";
    } else {
        std::cout << "SQLSEL: INNER JOIN access path -- nested-loop scan (outer="
                  << left_count << " row(s), inner=" << right_count << " row(s)).\n";
    }
    if (count_star) {
        std::cout << "COUNT(*)\n" << rows.size() << "\n1 row(s) selected.\n";
        return true;
    }

    for (std::size_t i = 0; i < projection.size(); ++i) {
        if (i) std::cout << " | ";
        std::cout << projection[i].label;
    }
    std::cout << "\n";
    const std::size_t shown = limit_n >= 0
        ? std::min<std::size_t>(rows.size(), static_cast<std::size_t>(limit_n))
        : rows.size();
    for (std::size_t r = 0; r < shown; ++r) {
        for (std::size_t i = 0; i < projection.size(); ++i) {
            if (i) std::cout << " | ";
            std::cout << trim(cell(rows[r], projection[i]));
        }
        std::cout << "\n";
    }
    std::cout << shown << " row(s) selected.\n";
    if (shown < rows.size()) {
        std::cout << "SQLSEL: LIMIT reached; " << (rows.size() - shown)
                  << " more row(s) available.\n";
    }
    return true;
}

} // namespace

namespace sqlsel {

void print_statement_usage() {
    std::cout
        << "SQLSEL statement usage:\n"
        << "  SQLSEL <col>[,<col>...] FROM <table> [[AS] <alias>]\n"
        << "         [WHERE <predicate>] [ORDER BY <field> [ASC|DESC]] [LIMIT <n>]\n"
        << "  SQLSEL * FROM <table>\n"
        << "  SQLSEL COUNT(*) FROM <table> [WHERE <predicate>]\n"
        << "  SQLSEL <list> FROM <table> [AS] <a> [INNER] JOIN\n"
        << "         <table> [AS] <b> ON <a.field> = <b.field>\n"
        << "Notes:\n"
        << "  SQLSEL is itself the select verb; the SELECT keyword is OPTIONAL\n"
        << "  (SQLSEL SELECT ... still parses). Not to be confused with xBase\n"
        << "  SELECT <area>, which switches the active work area.\n"
        << "  The table must be OPEN (USE <table>) -- SQLSEL reads open work areas.\n"
        << "  P4.1 joins two open tables with one equi-key. WHERE evaluates the\n"
        << "  resulting qualified TupleRow; no REL or SET RELATION state is read.\n"
        << "  JOIN takes a non-blocking two-table read fence; lock contention\n"
        << "  refuses the statement before either table is read.\n"
        << "  v1 accepts column names; expression projection is not yet supported.\n"
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
    const bool has_join = find_kw(table_clause, "JOIN") != std::string::npos;
    std::string table_name;
    TableRef single_table;
    if (!has_join) {
        std::string table_error;
        if (!parse_table_ref(table_clause, single_table, table_error)) {
            std::cout << "SQLSEL: " << table_error << ".\n";
            return true;
        }
        table_name = single_table.name;
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
        if (!has_join) {
            const std::size_t dot = order_field.find('.');
            if (dot != std::string::npos) {
                const std::string qualifier = order_field.substr(0, dot);
                if (!qualifier_matches(single_table, qualifier)) {
                    std::cout << "SQLSEL: ORDER BY qualifier '" << qualifier
                              << "' does not name table alias '" << single_table.alias << "'.\n";
                    return true;
                }
                order_field = order_field.substr(dot + 1);
            }
        }
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

    // P4.1 JOIN owns the full FROM clause. Keep it out of the single-table
    // resolver below so no REL/session state can leak into matching.
    if (has_join) {
        return execute_inner_join(select_list, table_clause, where_text,
                                  order_field, order_desc, limit_n);
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
            const std::size_t dot = c.find('.');
            if (dot == std::string::npos) {
                spec += area_label + "." + c;
            } else {
                const std::string qualifier = c.substr(0, dot);
                if (!qualifier_matches(single_table, qualifier)) {
                    std::cout << "SQLSEL: select qualifier '" << qualifier
                              << "' does not name table alias '" << single_table.alias << "'.\n";
                    return true;
                }
                spec += area_label + "." + c.substr(dot + 1);
            }
        }
    }

    // --- compile the predicate ONCE (not per row) ----------------------------
    std::unique_ptr<dottalk::expr::Expr> pred;
    if (!where_text.empty()) {
        auto compiled = dottalk::expr::compile_where(where_text);
        if (!compiled) {
            std::cout << "SQLSEL: could not compile the WHERE predicate: " << where_text
                      << " (" << compiled.error << ")\n";
            return true;
        }
        pred = std::move(compiled.program);
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
                    dottalk::TupleBuildResult predicate_row =
                        dottalk::build_tuple_from_spec(area_label + ".*", opts);
                    if (!predicate_row.ok) {
                        scan_error = "predicate row build failed: " + predicate_row.error;
                        break;
                    }
                    for (auto& column : predicate_row.row.columns) {
                        column.name = single_table.alias + "." + column.field;
                    }
                    const auto verdict = evaluate_tuple_predicate(pred.get(), predicate_row.row);
                    if (verdict.state == PredicateState::Error) {
                        scan_error = "predicate evaluation failed: " + verdict.error;
                        break;
                    }
                    keep = verdict.state == PredicateState::True;
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
