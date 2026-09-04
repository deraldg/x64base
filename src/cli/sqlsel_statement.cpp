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
#include <cmath>
#include <filesystem>
#include <iomanip>
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
#include "xbase/field_codec.hpp"
#include "cli/field_constraints.hpp"
#include "cli/field_store_validation.hpp"
#include "cli/table_buffer.hpp"
#include "cli/table_state.hpp"
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
#include "sqlsel/mode.hpp"

extern "C" xbase::XBaseEngine* shell_engine();

namespace {

std::string up(std::string s)   { return textio::up(std::move(s)); }
std::string trim(std::string s) { return textio::trim(std::move(s)); }

// Find a top-level keyword (outside single/double quotes), case-insensitive,
// bounded by non-identifier characters. Returns npos when absent.
std::size_t find_kw(const std::string& text, const std::string& kw, std::size_t from = 0) {
    const std::string U = up(text);
    const std::string K = up(kw);
    bool in_s = false, in_d = false;
    int paren_depth = 0;
    for (std::size_t i = from; i + K.size() <= U.size(); ++i) {
        const char c = U[i];
        if (c == '\'' && !in_d) { in_s = !in_s; continue; }
        if (c == '"'  && !in_s) { in_d = !in_d; continue; }
        if (in_s || in_d) continue;
        if (c == '(') { ++paren_depth; continue; }
        if (c == ')') { if (paren_depth > 0) --paren_depth; continue; }
        if (paren_depth != 0) continue;
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
    bool in_single = false;
    bool in_double = false;
    int depth = 0;
    for (const char c : s) {
        if (c == '\'' && !in_double) in_single = !in_single;
        else if (c == '"' && !in_single) in_double = !in_double;
        else if (!in_single && !in_double && c == '(') ++depth;
        else if (!in_single && !in_double && c == ')' && depth > 0) --depth;
        if (c == ',' && !in_single && !in_double && depth == 0) {
            const std::string item = trim(cur);
            if (!item.empty()) out.push_back(item);
            cur.clear();
            continue;
        }
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

xbase::DbArea* resolve_sqlsel_area(const std::string& name) {
    auto* engine = shell_engine();
    if (!engine) return nullptr;
    const int current = engine->currentArea();
    if (current < 0 || current >= xbase::MAX_AREA) return nullptr;
    const std::uint64_t workspace = engine->area(current).wsHandle();
    return cli::find_open_area_in_workspace_ci(name, workspace, "SQLSEL table");
}

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

        for (std::size_t i = 0; i < order.size(); ++i) {
            xbase::DbArea* area = order[i];
            if (i > 0 && area == order[i - 1]) continue;
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

enum class PredicateState { True, False, Unknown, Error };

struct PredicateVerdict {
    PredicateState state = PredicateState::Error;
    std::string error;
};

struct QueryResult {
    bool ok = false;
    std::vector<dottalk::TupleColumn> columns;
    std::vector<dottalk::TupleRow> rows;
};

void emit_query_result(const QueryResult& result) {
    for (std::size_t i = 0; i < result.columns.size(); ++i) {
        if (i) std::cout << " | ";
        std::cout << result.columns[i].name;
    }
    std::cout << "\n";
    for (const auto& row : result.rows) {
        for (std::size_t i = 0; i < row.values.size(); ++i) {
            if (i) std::cout << " | ";
            std::cout << trim(dottalk::render_tuple_cell(row.values[i], row.cell_kind(i)));
        }
        std::cout << "\n";
    }
    std::cout << result.rows.size() << " row(s) selected.\n";
}

bool tuple_value_equal(const dottalk::TupleRow& lhs,
                       const dottalk::TupleRow& rhs) {
    if (lhs.values.size() != rhs.values.size()) return false;
    for (std::size_t i = 0; i < lhs.values.size(); ++i) {
        const auto left_kind = lhs.cell_kind(i);
        const auto right_kind = rhs.cell_kind(i);
        if (left_kind != right_kind) return false;
        if (left_kind == dottalk::TupleCellKind::ProducedAbsent) continue;
        if (!value_equal(lhs.values[i], rhs.values[i])) return false;
    }
    return true;
}

void distinct_rows(std::vector<dottalk::TupleRow>& rows) {
    std::vector<dottalk::TupleRow> unique;
    unique.reserve(rows.size());
    for (auto& row : rows) {
        const bool seen = std::any_of(unique.begin(), unique.end(), [&](const auto& prior) {
            return tuple_value_equal(row, prior);
        });
        if (!seen) unique.push_back(std::move(row));
    }
    rows = std::move(unique);
}

PredicateState evaluate_tuple_predicate_node(const dottalk::expr::Expr* node,
                                             const dottalk::expr::RecordView& view) {
    if (const auto* boolean = dynamic_cast<const dottalk::expr::BoolBin*>(node)) {
        const PredicateState left = evaluate_tuple_predicate_node(boolean->lhs.get(), view);
        if (boolean->op == dottalk::expr::BoolOp::AND) {
            if (left == PredicateState::False) return PredicateState::False;
            const PredicateState right = evaluate_tuple_predicate_node(boolean->rhs.get(), view);
            if (left == PredicateState::True) return right;
            if (right == PredicateState::False) return PredicateState::False;
            return PredicateState::Unknown;
        }
        if (left == PredicateState::True) return PredicateState::True;
        const PredicateState right = evaluate_tuple_predicate_node(boolean->rhs.get(), view);
        if (left == PredicateState::False) return right;
        if (right == PredicateState::True) return PredicateState::True;
        return PredicateState::Unknown;
    }
    if (const auto* negation = dynamic_cast<const dottalk::expr::Not*>(node)) {
        const PredicateState inner = evaluate_tuple_predicate_node(negation->inner.get(), view);
        if (inner == PredicateState::True) return PredicateState::False;
        if (inner == PredicateState::False) return PredicateState::True;
        return inner;
    }
    try {
        return node->eval(view) ? PredicateState::True : PredicateState::False;
    } catch (const dottalk::exprglue::ProducedAbsentCellAccess&) {
        return PredicateState::Unknown;
    }
}

// NULL-READY: SQLsel owns a four-state predicate seam. Produced-absent outer
// cells yield UNKNOWN without pretending that x64base stores SQL NULL. Boolean
// composition follows SQL truth tables, while every other evaluator error
// remains a reported failure.
PredicateVerdict evaluate_tuple_predicate(const dottalk::expr::Expr* program,
                                          const dottalk::TupleRow& row) {
    if (!program) return {PredicateState::True, {}};
    try {
        const auto view = dottalk::exprglue::make_record_view(row);
        return {evaluate_tuple_predicate_node(program, view), {}};
    } catch (const std::exception& ex) {
        return {PredicateState::Error, ex.what()};
    } catch (...) {
        return {PredicateState::Error, "unknown predicate evaluation error"};
    }
}

enum class JoinKind { Inner, Left, Right, Full, Cross };

const char* join_kind_name(JoinKind kind) {
    switch (kind) {
        case JoinKind::Inner: return "INNER";
        case JoinKind::Left: return "LEFT";
        case JoinKind::Right: return "RIGHT";
        case JoinKind::Full: return "FULL";
        case JoinKind::Cross: return "CROSS";
    }
    return "INNER";
}

struct MultiJoinStage {
    JoinKind kind = JoinKind::Inner;
    TableRef table;
    std::string on_text;
};

class MultiJoinReadTransaction {
public:
    explicit MultiJoinReadTransaction(const std::vector<TableRef>& tables) {
        std::vector<xbase::DbArea*> order;
        for (const auto& table : tables) {
            if (std::find(order.begin(), order.end(), table.area) == order.end()) {
                order.push_back(table.area);
            }
        }
        std::sort(order.begin(), order.end(), [](const auto* left, const auto* right) {
            return JoinReadTransaction::path_key(*left) < JoinReadTransaction::path_key(*right);
        });
        for (xbase::DbArea* area : order) {
            const bool borrowed = JoinReadTransaction::owned_by_current_process(*area);
            std::string lock_error;
            if (!xbase::locks::try_lock_table(*area, &lock_error)) {
                error = JoinReadTransaction::table_name(*area) + ": " +
                        (lock_error.empty() ? "table lock refused" : lock_error);
                release();
                return;
            }
            held_.push_back({area, !borrowed});
            if (!fence.empty()) fence += " -> ";
            fence += JoinReadTransaction::table_name(*area);
        }
        ready = true;
    }
    ~MultiJoinReadTransaction() { release(); }
    MultiJoinReadTransaction(const MultiJoinReadTransaction&) = delete;
    MultiJoinReadTransaction& operator=(const MultiJoinReadTransaction&) = delete;

    bool ready = false;
    std::string fence;
    std::string error;

private:
    struct Held { xbase::DbArea* area = nullptr; bool acquired = false; };
    std::vector<Held> held_;
    void release() noexcept {
        while (!held_.empty()) {
            const Held one = held_.back();
            held_.pop_back();
            if (one.acquired && one.area) {
                std::string ignored;
                (void)xbase::locks::unlock_table(
                    *one.area, xbase::locks::current_owner(), &ignored);
            }
        }
    }
};

bool parse_multi_join_clause(const std::string& clause,
                             TableRef& first,
                             std::vector<MultiJoinStage>& stages,
                             std::string& error) {
    std::vector<std::size_t> joins;
    for (std::size_t from = 0;;) {
        const std::size_t pos = find_kw(clause, "JOIN", from);
        if (pos == std::string::npos) break;
        joins.push_back(pos);
        from = pos + 4;
    }
    if (joins.size() < 2) return false;

    std::vector<std::size_t> modifier_starts(joins.size());
    std::vector<JoinKind> kinds(joins.size(), JoinKind::Inner);
    for (std::size_t i = 0; i < joins.size(); ++i) {
        std::size_t end = joins[i];
        while (end > 0 && std::isspace(static_cast<unsigned char>(clause[end - 1]))) --end;
        std::size_t begin = end;
        while (begin > 0 && std::isalpha(static_cast<unsigned char>(clause[begin - 1]))) --begin;
        const std::string word = up(clause.substr(begin, end - begin));
        modifier_starts[i] = joins[i];
        if (word == "INNER") { kinds[i] = JoinKind::Inner; modifier_starts[i] = begin; }
        else if (word == "LEFT") { kinds[i] = JoinKind::Left; modifier_starts[i] = begin; }
        else if (word == "CROSS") { kinds[i] = JoinKind::Cross; modifier_starts[i] = begin; }
        else if (word == "RIGHT" || word == "FULL") {
            error = "multi-join chains currently accept INNER, LEFT, and CROSS stages; " +
                    word + " remains available as a two-table JOIN";
            return false;
        }
    }

    if (!parse_table_ref(trim(clause.substr(0, modifier_starts[0])), first, error)) return false;
    for (std::size_t i = 0; i < joins.size(); ++i) {
        const std::size_t begin = joins[i] + 4;
        const std::size_t end = i + 1 < joins.size() ? modifier_starts[i + 1] : clause.size();
        const std::string segment = trim(clause.substr(begin, end - begin));
        const std::size_t on_pos = find_kw(segment, "ON");
        if (kinds[i] == JoinKind::Cross && on_pos != std::string::npos) {
            error = "CROSS JOIN stage does not accept an ON clause";
            return false;
        }
        if (kinds[i] != JoinKind::Cross && on_pos == std::string::npos) {
            error = std::string(join_kind_name(kinds[i])) +
                    " JOIN stage requires an ON predicate";
            return false;
        }
        MultiJoinStage stage;
        stage.kind = kinds[i];
        const std::string table_text = kinds[i] == JoinKind::Cross
            ? segment : trim(segment.substr(0, on_pos));
        stage.on_text = kinds[i] == JoinKind::Cross
            ? std::string{} : trim(segment.substr(on_pos + 2));
        if (!parse_table_ref(table_text, stage.table, error)) return false;
        stages.push_back(std::move(stage));
    }
    return true;
}

std::vector<dottalk::TupleColumn> join_source_columns(const TableRef& table) {
    std::vector<dottalk::TupleColumn> columns;
    columns.reserve(table.area->fields().size());
    for (const auto& field : table.area->fields()) {
        columns.push_back({table.alias + "." + field.name, -1, field.name,
                           field.type, static_cast<int>(field.length),
                           static_cast<int>(field.decimals)});
    }
    return columns;
}

bool materialize_join_source(const TableRef& table,
                             const std::vector<dottalk::TupleColumn>& columns,
                             std::vector<dottalk::TupleRow>& rows,
                             std::string& error) {
    (void)error;
    const std::uint64_t count = static_cast<std::uint64_t>(table.area->recCount());
    for (std::uint64_t recno = 1; recno <= count; ++recno) {
        std::vector<std::string> values;
        cli::ScopedAreaSelect focus(table.area);
        try { table.area->gotoRec64(recno); } catch (...) { continue; }
        if (!read_area_row(*table.area, values) || table.area->isDeleted()) continue;
        dottalk::TupleRow row;
        row.columns = columns;
        row.values = std::move(values);
        row.cell_kinds.assign(row.values.size(), dottalk::TupleCellKind::Present);
        row.fragments.push_back({-1, recno, dottalk::TupleSourceKind::DBF,
                                 false, "SQLSEL:" + table.alias});
        rows.push_back(std::move(row));
    }
    return true;
}

dottalk::TupleRow combine_join_rows(const dottalk::TupleRow& left,
                                    const dottalk::TupleRow& right) {
    dottalk::TupleRow combined = left;
    combined.columns.insert(combined.columns.end(), right.columns.begin(), right.columns.end());
    combined.values.insert(combined.values.end(), right.values.begin(), right.values.end());
    if (combined.cell_kinds.empty()) {
        combined.cell_kinds.assign(left.values.size(), dottalk::TupleCellKind::Present);
    }
    if (right.cell_kinds.empty()) {
        combined.cell_kinds.insert(combined.cell_kinds.end(), right.values.size(),
                                   dottalk::TupleCellKind::Present);
    } else {
        combined.cell_kinds.insert(combined.cell_kinds.end(), right.cell_kinds.begin(),
                                   right.cell_kinds.end());
    }
    combined.fragments.insert(combined.fragments.end(), right.fragments.begin(),
                              right.fragments.end());
    return combined;
}

dottalk::TupleRow extend_join_row(const dottalk::TupleRow& left,
                                  const std::vector<dottalk::TupleColumn>& right_columns) {
    dottalk::TupleRow row = left;
    row.columns.insert(row.columns.end(), right_columns.begin(), right_columns.end());
    row.values.insert(row.values.end(), right_columns.size(), std::string{});
    if (row.cell_kinds.empty()) {
        row.cell_kinds.assign(left.values.size(), dottalk::TupleCellKind::Present);
    }
    row.cell_kinds.insert(row.cell_kinds.end(), right_columns.size(),
                          dottalk::TupleCellKind::ProducedAbsent);
    return row;
}

bool resolve_multi_result_column(const QueryResult& source,
                                 const std::string& token,
                                 std::size_t& position,
                                 std::string& error) {
    const std::string want = up(token);
    std::optional<std::size_t> found;
    for (std::size_t i = 0; i < source.columns.size(); ++i) {
        const std::string full = up(source.columns[i].name);
        const std::size_t dot = full.rfind('.');
        const std::string short_name = dot == std::string::npos ? full : full.substr(dot + 1);
        const bool matches = token.find('.') == std::string::npos
            ? want == short_name : want == full;
        if (!matches) continue;
        if (found) {
            error = "column '" + token + "' is ambiguous; qualify it with a table alias";
            return false;
        }
        found = i;
    }
    if (!found) {
        error = "column '" + token + "' was not found in the joined result";
        return false;
    }
    position = *found;
    return true;
}

bool project_multi_join_columns(const std::string& select_list,
                                const QueryResult& full,
                                QueryResult& result,
                                std::string& error) {
    if (trim(select_list) == "*") {
        result = full;
        return true;
    }
    std::vector<std::size_t> positions;
    for (const std::string& token : split_csv(select_list)) {
        if (!is_bare_column(token)) {
            error = "multi-join direct projection accepts columns; expression projection "
                    "is evaluated by the outer TupleRow projection stage";
            return false;
        }
        std::size_t position = 0;
        if (!resolve_multi_result_column(full, token, position, error)) return false;
        positions.push_back(position);
        result.columns.push_back(full.columns[position]);
    }
    result.ok = true;
    for (const auto& source_row : full.rows) {
        dottalk::TupleRow row;
        row.columns = result.columns;
        row.fragments = source_row.fragments;
        for (const std::size_t position : positions) {
            row.values.push_back(source_row.values[position]);
            row.cell_kinds.push_back(source_row.cell_kind(position));
        }
        result.rows.push_back(std::move(row));
    }
    return true;
}

bool execute_multi_join(const std::string& select_list,
                        const std::string& from_clause,
                        const std::string& where_text,
                        const std::string& order_token,
                        bool order_desc,
                        long long limit_n,
                        QueryResult* result_out) {
    TableRef first;
    std::vector<MultiJoinStage> stages;
    std::string error;
    if (!parse_multi_join_clause(from_clause, first, stages, error)) {
        std::cout << "SQLSEL: " << error << ".\n";
        return true;
    }
    std::vector<TableRef> tables{first};
    for (auto& stage : stages) tables.push_back(stage.table);
    for (auto& table : tables) {
        table.area = resolve_sqlsel_area(table.name);
        if (!table.area) {
            std::cout << "SQLSEL: table '" << table.name << "' is not open.\n";
            return true;
        }
    }
    for (std::size_t i = 0; i < tables.size(); ++i) {
        for (std::size_t j = i + 1; j < tables.size(); ++j) {
            if (up(tables[i].alias) == up(tables[j].alias)) {
                std::cout << "SQLSEL: every table in a multi-join needs a distinct alias.\n";
                return true;
            }
        }
    }
    for (std::size_t i = 0; i < stages.size(); ++i) stages[i].table = tables[i + 1];

    MultiJoinReadTransaction transaction(tables);
    if (!transaction.ready) {
        std::cout << "SQLSEL: multi-join read transaction refused -- "
                  << transaction.error << ".\n";
        return true;
    }
    dottalk::tupleaugment::WorkAreaCursorRestore restore;
    cli::ScopedEngineArea keep_current_area;
    std::cout << "SQLSEL: multi-join read transaction -- table fence ("
              << transaction.fence << ").\n";

    std::vector<std::vector<dottalk::TupleColumn>> source_columns;
    source_columns.reserve(tables.size());
    for (const auto& table : tables) source_columns.push_back(join_source_columns(table));
    std::vector<std::vector<dottalk::TupleRow>> sources(tables.size());
    for (std::size_t i = 0; i < tables.size(); ++i) {
        if (!materialize_join_source(tables[i], source_columns[i], sources[i], error)) {
            std::cout << "SQLSEL: " << error << ".\n";
            return true;
        }
    }
    std::vector<dottalk::TupleRow> rows = std::move(sources[0]);
    for (std::size_t stage_index = 0; stage_index < stages.size(); ++stage_index) {
        const MultiJoinStage& stage = stages[stage_index];
        std::unique_ptr<dottalk::expr::Expr> on;
        if (stage.kind != JoinKind::Cross) {
            auto compiled = dottalk::expr::compile_where(stage.on_text);
            if (!compiled) {
                std::cout << "SQLSEL: could not compile JOIN stage " << (stage_index + 1)
                          << " ON predicate: " << stage.on_text << " ("
                          << compiled.error << ")\n";
                return true;
            }
            on = std::move(compiled.program);
        }
        std::vector<dottalk::TupleRow> joined;
        for (const auto& left_row : rows) {
            bool matched = false;
            for (const auto& right_row : sources[stage_index + 1]) {
                dottalk::TupleRow candidate = combine_join_rows(left_row, right_row);
                bool keep = stage.kind == JoinKind::Cross;
                if (on) {
                    const PredicateVerdict verdict = evaluate_tuple_predicate(on.get(), candidate);
                    if (verdict.state == PredicateState::Error) {
                        std::cout << "SQLSEL: JOIN stage " << (stage_index + 1)
                                  << " ON evaluation failed: " << verdict.error << "\n";
                        return true;
                    }
                    keep = verdict.state == PredicateState::True;
                }
                if (keep) { matched = true; joined.push_back(std::move(candidate)); }
            }
            if (!matched && stage.kind == JoinKind::Left) {
                joined.push_back(extend_join_row(left_row, source_columns[stage_index + 1]));
            }
        }
        std::cout << "SQLSEL: " << join_kind_name(stage.kind) << " JOIN stage "
                  << (stage_index + 1) << " access path -- nested-loop scan (outer="
                  << rows.size() << " row(s), inner=" << sources[stage_index + 1].size()
                  << " row(s), output=" << joined.size() << ").\n";
        rows = std::move(joined);
    }

    if (!where_text.empty()) {
        auto compiled = dottalk::expr::compile_where(where_text);
        if (!compiled) {
            std::cout << "SQLSEL: could not compile the WHERE predicate: " << where_text
                      << " (" << compiled.error << ")\n";
            return true;
        }
        std::vector<dottalk::TupleRow> filtered;
        for (auto& row : rows) {
            const PredicateVerdict verdict = evaluate_tuple_predicate(compiled.program.get(), row);
            if (verdict.state == PredicateState::Error) {
                std::cout << "SQLSEL: predicate evaluation failed: " << verdict.error << "\n";
                return true;
            }
            if (verdict.state == PredicateState::True) filtered.push_back(std::move(row));
        }
        rows = std::move(filtered);
    }

    QueryResult full;
    full.ok = true;
    if (!rows.empty()) full.columns = rows.front().columns;
    else {
        for (const auto& table : tables) {
            for (const auto& field : table.area->fields()) {
                full.columns.push_back({table.alias + "." + field.name, -1, field.name,
                                        field.type, static_cast<int>(field.length),
                                        static_cast<int>(field.decimals)});
            }
        }
    }
    full.rows = std::move(rows);

    QueryResult result;
    std::string compact;
    for (const char c : select_list) {
        if (!std::isspace(static_cast<unsigned char>(c))) compact.push_back(c);
    }
    if (up(compact) == "COUNT(*)") {
        result.ok = true;
        result.columns.push_back({"COUNT(*)", -1, "COUNT(*)", 'N'});
        dottalk::TupleRow row;
        row.columns = result.columns;
        row.values.push_back(std::to_string(full.rows.size()));
        row.cell_kinds.push_back(dottalk::TupleCellKind::Present);
        result.rows.push_back(std::move(row));
    } else if (!project_multi_join_columns(select_list, full, result, error)) {
        std::cout << "SQLSEL: " << error << ".\n";
        return true;
    }

    if (!order_token.empty()) {
        std::size_t position = 0;
        if (!resolve_multi_result_column(result, order_token, position, error)) {
            std::cout << "SQLSEL: ORDER BY " << error << ".\n";
            return true;
        }
        std::stable_sort(result.rows.begin(), result.rows.end(), [&](const auto& left,
                                                                     const auto& right) {
            return order_desc ? value_less(right.values[position], left.values[position])
                              : value_less(left.values[position], right.values[position]);
        });
    }
    const std::size_t before_limit = result.rows.size();
    if (limit_n >= 0 && result.rows.size() > static_cast<std::size_t>(limit_n)) {
        result.rows.resize(static_cast<std::size_t>(limit_n));
    }
    if (result_out) *result_out = std::move(result);
    else emit_query_result(result);
    if (limit_n >= 0 && before_limit > static_cast<std::size_t>(limit_n)) {
        std::cout << "SQLSEL: LIMIT reached; "
                  << (before_limit - static_cast<std::size_t>(limit_n))
                  << " more row(s) available.\n";
    }
    return true;
}

// P4.1-P4.4 are deliberately independent of REL/SET RELATION
// (R17/R21/R27). Outer joins change row production, not source resolution,
// locking, ON equality, cursor restoration, or index selection. CROSS JOIN
// deliberately has no ON clause and always uses the correctness-first scan.
// The correctness-first nested loop remains the fallback. When the inner ON
// field is the active tag of an attached CDX/LMDB index, P4.2 probes that tag
// and still re-verifies every landed row against the ON comparison.
bool execute_join(const std::string& select_list,
                  const std::string& from_clause,
                  const std::string& where_text,
                  const std::string& order_token,
                  bool order_desc,
                  long long limit_n,
                  QueryResult* result_out) {
    if (result_out) *result_out = QueryResult{};
    const std::size_t join_pos = find_kw(from_clause, "JOIN");
    if (join_pos == std::string::npos) return false;
    if (find_kw(from_clause, "JOIN", join_pos + 4) != std::string::npos) {
        return execute_multi_join(select_list, from_clause, where_text,
                                  order_token, order_desc, limit_n, result_out);
    }

    std::string left_text = trim(from_clause.substr(0, join_pos));
    JoinKind join_kind = JoinKind::Inner;
    bool saw_join_modifier = false;
    for (const auto& modifier : std::array<std::pair<const char*, JoinKind>, 5>{{
             {"INNER", JoinKind::Inner},
             {"LEFT", JoinKind::Left},
             {"RIGHT", JoinKind::Right},
             {"FULL", JoinKind::Full},
             {"CROSS", JoinKind::Cross},
         }}) {
        const std::size_t modifier_pos = find_kw(left_text, modifier.first);
        if (modifier_pos == std::string::npos) continue;
        if (saw_join_modifier) {
            std::cout << "SQLSEL: choose one JOIN type.\n";
            return true;
        }
        if (up(trim(left_text.substr(modifier_pos))) != modifier.first) {
            std::cout << "SQLSEL: expected " << modifier.first << " JOIN.\n";
            return true;
        }
        saw_join_modifier = true;
        join_kind = modifier.second;
        left_text = trim(left_text.substr(0, modifier_pos));
    }
    const std::string join_name = join_kind_name(join_kind);

    const std::string after_join = trim(from_clause.substr(join_pos + 4));
    const std::size_t on_pos = find_kw(after_join, "ON");
    if (join_kind == JoinKind::Cross && on_pos != std::string::npos) {
        std::cout << "SQLSEL: CROSS JOIN does not accept an ON clause.\n";
        return true;
    }
    if (join_kind != JoinKind::Cross && on_pos == std::string::npos) {
        std::cout << "SQLSEL: " << join_name
                  << " JOIN requires ON <left-column> = <right-column>.\n";
        return true;
    }
    const std::string right_text = join_kind == JoinKind::Cross
        ? after_join
        : trim(after_join.substr(0, on_pos));
    const std::string on_text = join_kind == JoinKind::Cross
        ? std::string{}
        : trim(after_join.substr(on_pos + 2));

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
    left.area = resolve_sqlsel_area(left.name);
    right.area = resolve_sqlsel_area(right.name);
    if (!left.area || !right.area) {
        const std::string missing = !left.area ? left.name : right.name;
        std::cout << "SQLSEL: table '" << missing << "' is not open.\n";
        std::cout << "        Open both joined tables first -- SQLSEL reads open work areas.\n";
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

    ResolvedColumn on_left, on_right;
    bool simple_equi_on = false;
    std::unique_ptr<dottalk::expr::Expr> on_program;
    if (join_kind != JoinKind::Cross) {
        const std::size_t eq = on_text.find('=');
        if (eq != std::string::npos && on_text.find('=', eq + 1) == std::string::npos &&
            is_bare_column(trim(on_text.substr(0, eq))) &&
            is_bare_column(trim(on_text.substr(eq + 1)))) {
            if (!resolve_join_column(trim(on_text.substr(0, eq)), left, right, true,
                                     on_left, error) ||
                !resolve_join_column(trim(on_text.substr(eq + 1)), left, right, true,
                                     on_right, error)) {
                std::cout << "SQLSEL: " << error << ".\n";
                return true;
            }
            if (on_left.side == on_right.side) {
                std::cout << "SQLSEL: JOIN ON must compare one column from each table.\n";
                return true;
            }
            if (on_left.side == 1) std::swap(on_left, on_right);
            simple_equi_on = true;
        } else {
            auto compiled = dottalk::expr::compile_where(on_text);
            if (!compiled) {
                std::cout << "SQLSEL: could not compile JOIN ON predicate: " << on_text
                          << " (" << compiled.error << ")\n";
                return true;
            }
            on_program = std::move(compiled.program);
        }
    }

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

    const auto make_joined_row = [&](const std::vector<std::string>& left_values,
                                     const std::vector<std::string>& right_values,
                                     std::uint64_t left_recno,
                                     std::uint64_t right_recno,
                                     dottalk::TupleCellKind left_kind,
                                     dottalk::TupleCellKind right_kind) {
        dottalk::TupleRow tuple;
        tuple.columns.reserve(left.area->fields().size() + right.area->fields().size());
        tuple.values.reserve(left.area->fields().size() + right.area->fields().size());
        tuple.cell_kinds.reserve(left.area->fields().size() + right.area->fields().size());
        for (std::size_t i = 0; i < left.area->fields().size(); ++i) {
            const auto& fd = left.area->fields()[i];
            tuple.columns.push_back({left.alias + "." + fd.name,
                                     -1, fd.name, fd.type,
                                     static_cast<int>(fd.length), static_cast<int>(fd.decimals)});
            tuple.values.push_back(left_kind == dottalk::TupleCellKind::Present
                                       ? left_values[i]
                                       : std::string{});
            tuple.cell_kinds.push_back(left_kind);
        }
        for (std::size_t i = 0; i < right.area->fields().size(); ++i) {
            const auto& fd = right.area->fields()[i];
            tuple.columns.push_back({right.alias + "." + fd.name,
                                     -1, fd.name, fd.type,
                                     static_cast<int>(fd.length), static_cast<int>(fd.decimals)});
            tuple.values.push_back(right_kind == dottalk::TupleCellKind::Present
                                       ? right_values[i]
                                       : std::string{});
            tuple.cell_kinds.push_back(right_kind);
        }
        tuple.fragments.push_back({-1, left_recno, dottalk::TupleSourceKind::DBF,
                                   false, "SQLSEL:" + left.alias});
        tuple.fragments.push_back({-1, right_recno, dottalk::TupleSourceKind::DBF,
                                   false, "SQLSEL:" + right.alias});
        return tuple;
    };
    std::vector<dottalk::TupleRow> rows;
    std::size_t left_extended_rows = 0;
    std::size_t right_extended_rows = 0;
    JoinReadTransaction read_transaction{*left.area, *right.area};
    if (!read_transaction.ready) {
        std::cout << "SQLSEL: " << join_name << " JOIN read transaction refused -- "
                  << read_transaction.error << ".\n";
        return true;
    }
    dottalk::tupleaugment::WorkAreaCursorRestore restore;
    cli::ScopedEngineArea keep_current_area;

    std::cout << "SQLSEL: " << join_name << " JOIN read transaction -- table fence ("
              << read_transaction.first_name << " -> "
              << read_transaction.second_name << ").\n";

    const std::uint64_t left_count = static_cast<std::uint64_t>(left.area->recCount());
    const std::uint64_t right_count = static_cast<std::uint64_t>(right.area->recCount());
    std::vector<bool> right_matched(static_cast<std::size_t>(right_count) + 1, false);
    xindex::IndexManager* inner_index = xindex::manager_if_attached(*right.area);
    const bool index_candidate = join_kind != JoinKind::Cross && simple_equi_on &&
                                 inner_index != nullptr &&
                                 inner_index->isCdx() &&
                                 inner_index->activeTagMatchesField(
                                     static_cast<int>(on_right.field_index) + 1);
    std::size_t index_probes = 0;
    std::size_t index_candidates = 0;
    std::size_t scan_probes = 0;
    std::string join_evaluation_error;

    for (std::uint64_t li = 1; li <= left_count; ++li) {
        std::vector<std::string> lv;
        {
            cli::ScopedAreaSelect focus(left.area);
            left.area->gotoRec64(li);
            if (!read_area_row(*left.area, lv) || left.area->isDeleted()) continue;
        }

        bool matched_outer = false;
        const auto append_match = [&](std::vector<std::string> rv,
                                      std::uint64_t ri,
                                      bool mark_right) {
            dottalk::TupleRow candidate = make_joined_row(
                lv, rv, li, ri, dottalk::TupleCellKind::Present,
                dottalk::TupleCellKind::Present);
            bool matches = join_kind == JoinKind::Cross;
            if (simple_equi_on) {
                matches = value_equal(lv[on_left.field_index], rv[on_right.field_index]);
            } else if (on_program) {
                const PredicateVerdict verdict = evaluate_tuple_predicate(on_program.get(), candidate);
                if (verdict.state == PredicateState::Error) {
                    join_evaluation_error = verdict.error;
                    return;
                }
                matches = verdict.state == PredicateState::True;
            }
            if (matches) {
                matched_outer = true;
                if (mark_right &&
                    (join_kind == JoinKind::Right || join_kind == JoinKind::Full)) {
                    right_matched[static_cast<std::size_t>(ri)] = true;
                }
                rows.push_back(std::move(candidate));
            }
        };

        const auto append_unmatched = [&]() {
            if ((join_kind == JoinKind::Left || join_kind == JoinKind::Full) &&
                !matched_outer) {
                rows.push_back(make_joined_row(lv, {}, li, 0,
                                               dottalk::TupleCellKind::Present,
                                               dottalk::TupleCellKind::ProducedAbsent));
                ++left_extended_rows;
            }
        };

        bool used_index_for_outer = false;
        std::vector<std::uint64_t> probe_right_matches;
        if (index_candidate) {
            const std::size_t rows_before_probe = rows.size();
            try {
                const xindex::Key key = inner_index->buildActiveTagBaseKeyFromString(
                    lv[on_left.field_index]);
                if (!key.empty()) {
                    used_index_for_outer = true;
                    ++index_probes;
                    auto cursor = inner_index->seek(key);
                    if (cursor) {
                        bool probe_usable = true;
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
                                    const std::size_t rows_before_candidate = rows.size();
                                    append_match(std::move(rv), ri, false);
                                    if (rows.size() != rows_before_candidate &&
                                        (join_kind == JoinKind::Right || join_kind == JoinKind::Full)) {
                                        probe_right_matches.push_back(ri);
                                    }
                                }
                            }
                            if (!probe_usable) break;
                            found = cursor->next(landed_key, ri);
                        }
                        if (!probe_usable) {
                            rows.resize(rows_before_probe);
                            matched_outer = false;
                            probe_right_matches.clear();
                            used_index_for_outer = false;
                        }
                    }
                }
            } catch (...) {
                // Correctness outranks acceleration. If a usable-looking index
                // cannot serve this probe, scan this outer row and report the
                // hybrid path rather than returning a partial answer silently.
                rows.resize(rows_before_probe);
                matched_outer = false;
                probe_right_matches.clear();
                used_index_for_outer = false;
            }
        }

        if (used_index_for_outer) {
            for (const auto ri : probe_right_matches) {
                right_matched[static_cast<std::size_t>(ri)] = true;
            }
            append_unmatched();
            continue;
        }

        ++scan_probes;
        for (std::uint64_t ri = 1; ri <= right_count; ++ri) {
            std::vector<std::string> rv;
            {
                cli::ScopedAreaSelect focus(right.area);
                right.area->gotoRec64(ri);
                if (!read_area_row(*right.area, rv) || right.area->isDeleted()) continue;
            }
            append_match(std::move(rv), ri, true);
            if (!join_evaluation_error.empty()) break;
        }
        if (!join_evaluation_error.empty()) break;
        append_unmatched();
    }

    if (!join_evaluation_error.empty()) {
        std::cout << "SQLSEL: JOIN ON evaluation failed: " << join_evaluation_error << "\n";
        return true;
    }

    if (join_kind == JoinKind::Right || join_kind == JoinKind::Full) {
        for (std::uint64_t ri = 1; ri <= right_count; ++ri) {
            if (right_matched[static_cast<std::size_t>(ri)]) continue;
            std::vector<std::string> rv;
            {
                cli::ScopedAreaSelect focus(right.area);
                right.area->gotoRec64(ri);
                if (!read_area_row(*right.area, rv) || right.area->isDeleted()) continue;
            }
            rows.push_back(make_joined_row({}, rv, 0, ri,
                                           dottalk::TupleCellKind::ProducedAbsent,
                                           dottalk::TupleCellKind::Present));
            ++right_extended_rows;
        }
    }

    if (where_program) {
        std::vector<dottalk::TupleRow> filtered;
        filtered.reserve(rows.size());
        for (auto& tuple : rows) {
            const PredicateVerdict verdict = evaluate_tuple_predicate(where_program.get(), tuple);
            if (verdict.state == PredicateState::Error) {
                std::cout << "SQLSEL: predicate evaluation failed: " << verdict.error << "\n";
                return true;
            }
            if (verdict.state == PredicateState::True) filtered.push_back(std::move(tuple));
        }
        rows = std::move(filtered);
    }

    struct CellView {
        std::string_view value;
        dottalk::TupleCellKind kind = dottalk::TupleCellKind::Present;
    };
    const std::size_t right_offset = left.area->fields().size();
    const auto cell = [right_offset](const dottalk::TupleRow& row,
                                     const ResolvedColumn& col) -> CellView {
        const std::size_t pos = col.side == 0 ? col.field_index : right_offset + col.field_index;
        return {row.values[pos], row.cell_kind(pos)};
    };
    const auto rendered_cell = [&](const dottalk::TupleRow& row, const ResolvedColumn& col) {
        const CellView one = cell(row, col);
        return trim(dottalk::render_tuple_cell(one.value, one.kind));
    };
    if (order_col) {
        // NULL-READY: ProducedAbsent orders by its visible marker today. Stored
        // NULL will need an explicit NULLS FIRST/LAST ruling at this site.
        std::stable_sort(rows.begin(), rows.end(), [&](const dottalk::TupleRow& a,
                                                       const dottalk::TupleRow& b) {
            return order_desc ? value_less(rendered_cell(b, *order_col), rendered_cell(a, *order_col))
                              : value_less(rendered_cell(a, *order_col), rendered_cell(b, *order_col));
        });
    }

    if (index_probes > 0 && scan_probes == 0) {
        std::cout << "SQLSEL: " << join_name << " JOIN access path -- CDX seek (inner="
                  << right.name << ", tag=" << inner_index->activeTag()
                  << ", probes=" << index_probes
                  << ", candidates=" << index_candidates << ").\n";
    } else if (index_probes > 0) {
        std::cout << "SQLSEL: " << join_name << " JOIN access path -- hybrid CDX seek + nested-loop scan"
                  << " (inner=" << right.name << ", tag=" << inner_index->activeTag()
                  << ", index probes=" << index_probes
                  << ", scan probes=" << scan_probes << ").\n";
    } else {
        std::cout << "SQLSEL: " << join_name << " JOIN access path -- nested-loop scan (outer="
                  << left_count << " row(s), inner=" << right_count << " row(s)).\n";
    }
    if (join_kind == JoinKind::Left) {
        std::cout << "SQLSEL: LEFT JOIN left-extended " << left_extended_rows
                  << " row(s) with " << dottalk::kProducedAbsentMarker
                  << " right-side cells.\n";
    } else if (join_kind == JoinKind::Right) {
        std::cout << "SQLSEL: RIGHT JOIN right-extended " << right_extended_rows
                  << " row(s) with " << dottalk::kProducedAbsentMarker
                  << " left-side cells.\n";
    } else if (join_kind == JoinKind::Full) {
        std::cout << "SQLSEL: FULL JOIN left-extended " << left_extended_rows
                  << " row(s) with " << dottalk::kProducedAbsentMarker
                  << " right-side cells.\n";
        std::cout << "SQLSEL: FULL JOIN right-extended " << right_extended_rows
                  << " row(s) with " << dottalk::kProducedAbsentMarker
                  << " left-side cells.\n";
    }
    QueryResult result;
    result.ok = true;
    if (count_star) {
        dottalk::TupleColumn count_column;
        count_column.name = "COUNT(*)";
        count_column.field = "COUNT(*)";
        count_column.ftype = 'N';
        result.columns.push_back(count_column);
        dottalk::TupleRow count_row;
        count_row.columns = result.columns;
        count_row.values.push_back(std::to_string(rows.size()));
        count_row.cell_kinds.push_back(dottalk::TupleCellKind::Present);
        result.rows.push_back(std::move(count_row));
    } else {
        for (const auto& col : projection) {
            const auto& fd = (col.side == 0 ? left.area : right.area)->fields()[col.field_index];
            result.columns.push_back({col.label, -1, fd.name, fd.type,
                                      static_cast<int>(fd.length), static_cast<int>(fd.decimals)});
        }
        const std::size_t shown = limit_n >= 0
            ? std::min<std::size_t>(rows.size(), static_cast<std::size_t>(limit_n))
            : rows.size();
        result.rows.reserve(shown);
        for (std::size_t r = 0; r < shown; ++r) {
            dottalk::TupleRow projected;
            projected.columns = result.columns;
            projected.fragments = rows[r].fragments;
            for (const auto& col : projection) {
                const std::size_t pos = col.side == 0
                    ? col.field_index
                    : right_offset + col.field_index;
                projected.values.push_back(rows[r].values[pos]);
                projected.cell_kinds.push_back(rows[r].cell_kind(pos));
            }
            result.rows.push_back(std::move(projected));
        }
    }
    const std::size_t result_row_count = result.rows.size();
    if (result_out) {
        *result_out = std::move(result);
    } else {
        emit_query_result(result);
    }
    const std::size_t shown = count_star ? rows.size() : result_row_count;
    if (shown < rows.size()) {
        std::cout << "SQLSEL: LIMIT reached; " << (rows.size() - shown)
                  << " more row(s) available.\n";
    }
    return true;
}

} // namespace

namespace sqlsel {

enum class AggregateKind { None, CountStar, Count, Sum, Avg, Min, Max };

struct AggregateItem {
    AggregateKind kind = AggregateKind::None;
    std::string source;
    std::string label;
    std::size_t source_pos = 0;
    char source_type = ' ';
    int source_decimals = 0;
};

bool execute_select_term(const std::string& tail_in, QueryResult* result_out);

bool parse_aggregate_item(const std::string& raw,
                          AggregateItem& item,
                          std::string& error) {
    std::string text = trim(raw);
    std::string explicit_label;
    const std::size_t as_pos = find_kw(text, "AS");
    if (as_pos != std::string::npos) {
        explicit_label = trim(text.substr(as_pos + 2));
        text = trim(text.substr(0, as_pos));
        if (!is_identifier(explicit_label)) {
            error = "aggregate alias '" + explicit_label + "' must be an identifier";
            return false;
        }
        if (text.empty()) {
            error = "aggregate alias '" + explicit_label + "' has no expression";
            return false;
        }
    }
    const std::string upper = up(text);
    for (const auto& candidate : std::array<std::pair<const char*, AggregateKind>, 5>{{
             {"COUNT", AggregateKind::Count},
             {"SUM", AggregateKind::Sum},
             {"AVG", AggregateKind::Avg},
             {"MIN", AggregateKind::Min},
             {"MAX", AggregateKind::Max},
         }}) {
        const std::string name = candidate.first;
        if (upper.rfind(name, 0) != 0) continue;
        std::size_t open = name.size();
        while (open < text.size() &&
               std::isspace(static_cast<unsigned char>(text[open]))) ++open;
        if (open >= text.size() || text[open] != '(' || text.back() != ')') {
            error = "aggregate '" + text + "' must use " + name + "(<column>)";
            return false;
        }
        const std::string argument = trim(text.substr(open + 1, text.size() - open - 2));
        if (argument.empty()) {
            error = "aggregate '" + text + "' requires an argument";
            return false;
        }
        if (argument == "*") {
            if (candidate.second != AggregateKind::Count) {
                error = name + "(*) is not supported; only COUNT(*) accepts '*'";
                return false;
            }
            item.kind = AggregateKind::CountStar;
        } else {
            if (!is_bare_column(argument)) {
                error = "aggregate argument '" + argument + "' must be a column name";
                return false;
            }
            item.kind = candidate.second;
            item.source = argument;
        }
        item.label = explicit_label.empty() ? name + "(" + argument + ")"
                                            : explicit_label;
        return true;
    }
    item.kind = AggregateKind::None;
    item.source = text;
    item.label = explicit_label.empty() ? text : explicit_label;
    return true;
}

bool resolve_result_column(const QueryResult& source,
                           const std::string& token,
                           std::size_t& position,
                           std::string& error) {
    const std::string want = up(token);
    std::optional<std::size_t> found;
    for (std::size_t i = 0; i < source.columns.size(); ++i) {
        const auto& column = source.columns[i];
        const std::string full = up(column.name);
        const std::string field = up(column.field);
        const std::size_t dot = full.rfind('.');
        const std::string short_name = dot == std::string::npos ? full : full.substr(dot + 1);
        const bool matches = token.find('.') == std::string::npos
            ? (want == field || want == short_name)
            : want == full;
        if (!matches) continue;
        if (found) {
            error = "column '" + token + "' is ambiguous; qualify it with a table alias";
            return false;
        }
        found = i;
    }
    if (!found) {
        error = "column '" + token + "' was not found in the aggregate source";
        return false;
    }
    position = *found;
    return true;
}

struct SubqueryRuntime {
    std::size_t correlated_evaluations = 0;
    std::size_t uncorrelated_evaluations = 0;
    std::vector<std::pair<std::string, QueryResult>> cache;
};

std::size_t find_subquery_paren(const std::string& text) {
    bool in_single = false;
    bool in_double = false;
    for (std::size_t i = 0; i < text.size(); ++i) {
        const char c = text[i];
        if (c == '\'' && !in_double) { in_single = !in_single; continue; }
        if (c == '"' && !in_single) { in_double = !in_double; continue; }
        if (in_single || in_double || c != '(') continue;
        std::size_t next = i + 1;
        while (next < text.size() &&
               std::isspace(static_cast<unsigned char>(text[next]))) ++next;
        if (up(text.substr(next, 6)) == "SELECT") return i;
    }
    return std::string::npos;
}

std::size_t matching_paren(const std::string& text, std::size_t open) {
    int depth = 0;
    bool in_single = false;
    bool in_double = false;
    for (std::size_t i = open; i < text.size(); ++i) {
        const char c = text[i];
        if (c == '\'' && !in_double) { in_single = !in_single; continue; }
        if (c == '"' && !in_single) { in_double = !in_double; continue; }
        if (in_single || in_double) continue;
        if (c == '(') ++depth;
        else if (c == ')' && --depth == 0) return i;
    }
    return std::string::npos;
}

bool context_is_referenced(const std::string& sql, const dottalk::TupleRow& context) {
    const std::string upper_sql = up(sql);
    for (const auto& column : context.columns) {
        const std::size_t dot = column.name.find('.');
        if (dot == std::string::npos) continue;
        const std::string qualifier = up(column.name.substr(0, dot)) + ".";
        if (upper_sql.find(qualifier) != std::string::npos) return true;
    }
    return false;
}

dottalk::TupleRow combine_scopes(const dottalk::TupleRow& local,
                                 const dottalk::TupleRow& outer) {
    dottalk::TupleRow combined = local;
    combined.columns.insert(combined.columns.end(), outer.columns.begin(), outer.columns.end());
    combined.values.insert(combined.values.end(), outer.values.begin(), outer.values.end());
    if (combined.cell_kinds.empty()) {
        combined.cell_kinds.assign(local.values.size(), dottalk::TupleCellKind::Present);
    }
    if (outer.cell_kinds.empty()) {
        combined.cell_kinds.insert(combined.cell_kinds.end(), outer.values.size(),
                                   dottalk::TupleCellKind::Present);
    } else {
        combined.cell_kinds.insert(combined.cell_kinds.end(), outer.cell_kinds.begin(),
                                   outer.cell_kinds.end());
    }
    combined.fragments.insert(combined.fragments.end(), outer.fragments.begin(), outer.fragments.end());
    return combined;
}

bool evaluate_sql_predicate(const std::string& text,
                            const dottalk::TupleRow& context,
                            SubqueryRuntime& runtime,
                            PredicateState& state,
                            std::string& error);

bool materialize_subquery(const std::string& sql,
                          const dottalk::TupleRow& outer,
                          SubqueryRuntime& runtime,
                          QueryResult& result,
                          std::string& error) {
    const bool correlated = context_is_referenced(sql, outer);
    if (!correlated) {
        const auto cached = std::find_if(runtime.cache.begin(), runtime.cache.end(),
            [&](const auto& entry) { return entry.first == sql; });
        if (cached != runtime.cache.end()) {
            result = cached->second;
            return true;
        }
        ++runtime.uncorrelated_evaluations;
        if (!execute_select_term(sql, &result) || !result.ok) {
            error = "uncorrelated subquery failed";
            return false;
        }
        runtime.cache.push_back({sql, result});
        return true;
    }

    ++runtime.correlated_evaluations;
    const std::string query = trim(sql);
    const std::size_t select_pos = find_kw(query, "SELECT");
    const std::size_t from_pos = find_kw(query, "FROM", 6);
    if (select_pos != 0 || from_pos == std::string::npos) {
        error = "correlated subquery requires SELECT <column|*> FROM <table>";
        return false;
    }
    const std::size_t where_pos = find_kw(query, "WHERE", from_pos + 4);
    if (find_kw(query, "GROUP", from_pos + 4) != std::string::npos ||
        find_kw(query, "HAVING", from_pos + 4) != std::string::npos ||
        find_kw(query, "ORDER", from_pos + 4) != std::string::npos ||
        find_kw(query, "LIMIT", from_pos + 4) != std::string::npos) {
        error = "correlated subquery P4.7 accepts SELECT/FROM/WHERE only";
        return false;
    }
    const std::string select_text = trim(query.substr(6, from_pos - 6));
    const std::size_t from_end = where_pos == std::string::npos ? query.size() : where_pos;
    const std::string table_text = trim(query.substr(from_pos + 4, from_end - from_pos - 4));
    std::string where_text;
    if (where_pos != std::string::npos) where_text = trim(query.substr(where_pos + 5));

    TableRef table;
    if (!parse_table_ref(table_text, table, error)) return false;
    QueryResult local;
    if (!execute_select_term("SELECT * FROM " + table_text, &local) || !local.ok) {
        error = "could not materialize correlated subquery table '" + table.name + "'";
        return false;
    }
    for (auto& column : local.columns) column.name = table.alias + "." + column.field;
    for (auto& row : local.rows) row.columns = local.columns;

    std::vector<std::size_t> projection;
    if (select_text != "*") {
        for (const std::string& token : split_csv(select_text)) {
            if (!is_bare_column(token)) {
                error = "correlated subquery projects bare columns or '*' only";
                return false;
            }
            std::size_t position = 0;
            if (!resolve_result_column(local, token, position, error)) return false;
            projection.push_back(position);
            result.columns.push_back(local.columns[position]);
        }
    } else {
        result.columns = local.columns;
        for (std::size_t i = 0; i < local.columns.size(); ++i) projection.push_back(i);
    }

    result.ok = true;
    for (const auto& local_row : local.rows) {
        dottalk::TupleRow combined = combine_scopes(local_row, outer);
        PredicateState keep = PredicateState::True;
        if (!where_text.empty() &&
            !evaluate_sql_predicate(where_text, combined, runtime, keep, error)) {
            return false;
        }
        if (keep != PredicateState::True) continue;
        dottalk::TupleRow projected;
        projected.columns = result.columns;
        projected.fragments = local_row.fragments;
        for (const std::size_t position : projection) {
            projected.values.push_back(local_row.values[position]);
            projected.cell_kinds.push_back(local_row.cell_kind(position));
        }
        result.rows.push_back(std::move(projected));
    }
    return true;
}

bool same_column_family(char left_raw, char right_raw) {
    const auto family = [](char raw) {
        const char type = static_cast<char>(std::toupper(static_cast<unsigned char>(raw)));
        if (type == 'C' || type == 'M') return 1;
        if (type == 'N' || type == 'F' || type == 'B' || type == 'Y' || type == 'I') return 2;
        if (type == 'D' || type == 'T') return 3;
        if (type == 'L') return 4;
        return 0;
    };
    return family(left_raw) != 0 && family(left_raw) == family(right_raw);
}

bool evaluate_sql_predicate(const std::string& raw,
                            const dottalk::TupleRow& context,
                            SubqueryRuntime& runtime,
                            PredicateState& state,
                            std::string& error) {
    const std::string text = trim(raw);
    const std::string upper = up(text);
    const std::size_t sub_open = find_subquery_paren(text);
    if (sub_open == std::string::npos) {
        auto compiled = dottalk::expr::compile_where(text);
        if (!compiled) {
            error = "could not compile predicate '" + text + "': " + compiled.error;
            return false;
        }
        const PredicateVerdict verdict = evaluate_tuple_predicate(compiled.program.get(), context);
        if (verdict.state == PredicateState::Error) {
            error = verdict.error;
            return false;
        }
        state = verdict.state;
        return true;
    }
    const std::size_t sub_close = matching_paren(text, sub_open);
    if (sub_close == std::string::npos || !trim(text.substr(sub_close + 1)).empty()) {
        error = "subquery predicate has trailing or unbalanced input";
        return false;
    }
    const std::string sub_sql = trim(text.substr(sub_open + 1, sub_close - sub_open - 1));
    QueryResult subquery;
    if (!materialize_subquery(sub_sql, context, runtime, subquery, error)) return false;

    const std::string prefix = trim(text.substr(0, sub_open));
    const std::string upper_prefix = up(prefix);
    if (upper_prefix == "EXISTS" || upper_prefix == "NOT EXISTS") {
        const bool exists = !subquery.rows.empty();
        state = (upper_prefix == "NOT EXISTS" ? !exists : exists)
            ? PredicateState::True : PredicateState::False;
        return true;
    }

    const std::size_t in_pos = find_kw(prefix, "IN");
    if (in_pos != std::string::npos && in_pos + 2 == prefix.size()) {
        std::string left_token = trim(prefix.substr(0, in_pos));
        bool negate = false;
        const std::size_t not_pos = find_kw(left_token, "NOT");
        if (not_pos != std::string::npos && not_pos + 3 == left_token.size()) {
            negate = true;
            left_token = trim(left_token.substr(0, not_pos));
        }
        QueryResult context_result;
        context_result.columns = context.columns;
        std::size_t left_pos = 0;
        if (!resolve_result_column(context_result, left_token, left_pos, error)) return false;
        if (subquery.columns.size() != 1) {
            error = "IN subquery must return exactly one column";
            return false;
        }
        if (!same_column_family(context.columns[left_pos].ftype, subquery.columns[0].ftype)) {
            error = "IN subquery compares incompatible typed columns";
            return false;
        }
        bool found = false;
        for (const auto& row : subquery.rows) {
            if (context.cell_kind(left_pos) == dottalk::TupleCellKind::ProducedAbsent ||
                row.cell_kind(0) == dottalk::TupleCellKind::ProducedAbsent) continue;
            if (value_equal(context.values[left_pos], row.values[0])) { found = true; break; }
        }
        state = (negate ? !found : found) ? PredicateState::True : PredicateState::False;
        return true;
    }

    std::string op;
    std::size_t op_pos = std::string::npos;
    for (const char* candidate : {"<=", ">=", "<>", "!=", "=", "<", ">"}) {
        const std::size_t hit = prefix.rfind(candidate);
        if (hit != std::string::npos &&
            (op_pos == std::string::npos || hit > op_pos)) {
            op = candidate;
            op_pos = hit;
        }
    }
    if (op_pos == std::string::npos) {
        error = "subquery predicate must be EXISTS, IN, or a scalar comparison";
        return false;
    }
    const std::string left_token = trim(prefix.substr(0, op_pos));
    QueryResult context_result;
    context_result.columns = context.columns;
    std::size_t left_pos = 0;
    if (!resolve_result_column(context_result, left_token, left_pos, error)) return false;
    if (subquery.columns.size() != 1 || subquery.rows.size() != 1) {
        error = "scalar subquery must return exactly one row and one column (got " +
                std::to_string(subquery.rows.size()) + " row(s), " +
                std::to_string(subquery.columns.size()) + " column(s))";
        return false;
    }
    if (!same_column_family(context.columns[left_pos].ftype, subquery.columns[0].ftype)) {
        error = "scalar subquery compares incompatible typed columns";
        return false;
    }
    dottalk::TupleRow comparison;
    comparison.columns = {
        {"__SQ_LEFT", -1, "__SQ_LEFT", context.columns[left_pos].ftype},
        {"__SQ_RIGHT", -1, "__SQ_RIGHT", subquery.columns[0].ftype}
    };
    comparison.values = {context.values[left_pos], subquery.rows[0].values[0]};
    comparison.cell_kinds = {context.cell_kind(left_pos), subquery.rows[0].cell_kind(0)};
    auto compiled = dottalk::expr::compile_where("__SQ_LEFT " + op + " __SQ_RIGHT");
    if (!compiled) {
        error = "could not compile scalar subquery comparison";
        return false;
    }
    const PredicateVerdict verdict = evaluate_tuple_predicate(compiled.program.get(), comparison);
    if (verdict.state == PredicateState::Error) {
        error = verdict.error;
        return false;
    }
    state = verdict.state;
    return true;
}

char projected_expression_type(const dottalk::expr::Expr* expression) {
    if (dynamic_cast<const dottalk::expr::LitNumber*>(expression) ||
        dynamic_cast<const dottalk::expr::Arith*>(expression)) return 'N';
    if (dynamic_cast<const dottalk::expr::LitBool*>(expression) ||
        dynamic_cast<const dottalk::expr::Cmp*>(expression) ||
        dynamic_cast<const dottalk::expr::BoolBin*>(expression) ||
        dynamic_cast<const dottalk::expr::Not*>(expression)) return 'L';
    if (const auto* call = dynamic_cast<const dottalk::expr::FunctionCall*>(expression)) {
        const std::string name = up(call->name);
        if (name == "CTOD" || name == "DATEADD") return 'D';
        if (name == "EMPTY" || name == "DELETED") return 'L';
    }
    return 'C';
}

bool project_query_expressions(const std::string& select_list,
                               const QueryResult& source,
                               QueryResult& result,
                               std::string& error) {
    struct Plan {
        std::string label;
        std::optional<std::size_t> direct;
        std::unique_ptr<dottalk::expr::Expr> expression;
        char type = 'C';
    };
    if (trim(select_list) == "*") {
        result = source;
        return true;
    }
    std::vector<Plan> plans;
    for (const std::string& raw_item : split_csv(select_list)) {
        std::string expression_text = trim(raw_item);
        std::string label = expression_text;
        const std::size_t as_pos = find_kw(expression_text, "AS");
        if (as_pos != std::string::npos) {
            label = trim(expression_text.substr(as_pos + 2));
            expression_text = trim(expression_text.substr(0, as_pos));
            if (!is_identifier(label)) {
                error = "projection alias '" + label + "' must be an identifier";
                return false;
            }
        }
        Plan plan;
        plan.label = label;
        if (is_bare_column(expression_text)) {
            std::size_t position = 0;
            if (!resolve_result_column(source, expression_text, position, error)) return false;
            plan.direct = position;
            if (as_pos == std::string::npos) plan.label = source.columns[position].name;
            plan.type = source.columns[position].ftype;
        } else {
            auto compiled = dottalk::expr::compile_where(expression_text);
            if (!compiled) {
                error = "could not compile projection expression '" + expression_text +
                        "': " + compiled.error;
                return false;
            }
            plan.type = projected_expression_type(compiled.program.get());
            plan.expression = std::move(compiled.program);
        }
        plans.push_back(std::move(plan));
    }
    if (plans.empty()) {
        error = "the select list is empty";
        return false;
    }

    result.ok = true;
    for (const Plan& plan : plans) {
        result.columns.push_back({plan.label, -1, plan.label, plan.type, 0, 0});
    }
    for (const auto& source_row : source.rows) {
        dottalk::TupleRow projected;
        projected.columns = result.columns;
        projected.fragments = source_row.fragments;
        const auto view = dottalk::exprglue::make_record_view(source_row);
        for (const Plan& plan : plans) {
            if (plan.direct) {
                projected.values.push_back(source_row.values[*plan.direct]);
                projected.cell_kinds.push_back(source_row.cell_kind(*plan.direct));
                continue;
            }
            try {
                projected.values.push_back(trim(plan.expression->evalString(view)));
                projected.cell_kinds.push_back(dottalk::TupleCellKind::Present);
            } catch (const dottalk::exprglue::ProducedAbsentCellAccess&) {
                projected.values.emplace_back();
                projected.cell_kinds.push_back(dottalk::TupleCellKind::ProducedAbsent);
            } catch (const std::exception& ex) {
                error = "projection evaluation failed for '" + plan.label + "': " + ex.what();
                return false;
            }
        }
        result.rows.push_back(std::move(projected));
    }
    return true;
}

bool execute_expression_projection(const std::string& tail,
                                   const std::string& select_list,
                                   bool select_distinct,
                                   QueryResult* result_out) {
    const std::size_t from_pos = find_kw(tail, "FROM");
    const std::size_t order_pos = find_kw(tail, "ORDER", from_pos + 4);
    const std::size_t limit_pos = find_kw(tail, "LIMIT", from_pos + 4);
    std::size_t source_end = tail.size();
    if (order_pos != std::string::npos) source_end = std::min(source_end, order_pos);
    if (limit_pos != std::string::npos) source_end = std::min(source_end, limit_pos);
    const std::string source_query = "SELECT * " + tail.substr(from_pos, source_end - from_pos);
    QueryResult source;
    if (!execute_select_term(source_query, &source) || !source.ok) return true;

    QueryResult result;
    std::string error;
    if (!project_query_expressions(select_list, source, result, error)) {
        std::cout << "SQLSEL: " << error << ".\n";
        return true;
    }
    if (select_distinct) {
        const std::size_t before = result.rows.size();
        distinct_rows(result.rows);
        std::cout << "SQLSEL: DISTINCT reduced " << before << " row(s) to "
                  << result.rows.size() << " row(s).\n";
    }

    struct OrderPlan { std::size_t position = 0; bool descending = false; };
    std::vector<OrderPlan> order;
    if (order_pos != std::string::npos) {
        const std::size_t end = limit_pos != std::string::npos && limit_pos > order_pos
            ? limit_pos : tail.size();
        std::string text = trim(tail.substr(order_pos + 5, end - order_pos - 5));
        if (find_kw(text, "BY") != 0) {
            std::cout << "SQLSEL: expected ORDER BY <result-column>[,<result-column>...].\n";
            return true;
        }
        text = trim(text.substr(2));
        for (std::string item : split_csv(text)) {
            bool descending = false;
            std::istringstream in(item);
            std::string token, direction, extra;
            in >> token >> direction >> extra;
            if (token.empty() || !extra.empty() ||
                (!direction.empty() && up(direction) != "ASC" && up(direction) != "DESC")) {
                std::cout << "SQLSEL: invalid ORDER BY item '" << item << "'.\n";
                return true;
            }
            descending = up(direction) == "DESC";
            std::size_t position = 0;
            if (!resolve_result_column(result, token, position, error)) {
                std::cout << "SQLSEL: ORDER BY " << error << ".\n";
                return true;
            }
            order.push_back({position, descending});
        }
        std::stable_sort(result.rows.begin(), result.rows.end(), [&](const auto& left,
                                                                     const auto& right) {
            for (const OrderPlan& one : order) {
                if (value_equal(left.values[one.position], right.values[one.position])) continue;
                const bool less = value_less(left.values[one.position], right.values[one.position]);
                return one.descending ? !less : less;
            }
            return false;
        });
        std::cout << "SQLSEL: ORDER BY " << order.size()
                  << " result column(s) -- materialized sort over "
                  << result.rows.size() << " row(s).\n";
    }

    long long limit_n = -1;
    if (limit_pos != std::string::npos) {
        const std::string limit_text = trim(tail.substr(limit_pos + 5));
        try {
            std::size_t used = 0;
            limit_n = std::stoll(limit_text, &used);
            if (used != limit_text.size() || limit_n < 0) throw std::invalid_argument("bad");
        } catch (...) {
            std::cout << "SQLSEL: LIMIT expects a non-negative integer (got '"
                      << limit_text << "').\n";
            return true;
        }
    }
    const std::size_t before_limit = result.rows.size();
    if (limit_n >= 0 && result.rows.size() > static_cast<std::size_t>(limit_n)) {
        result.rows.resize(static_cast<std::size_t>(limit_n));
    }
    std::cout << "SQLSEL: expression projection evaluated " << source.rows.size()
              << " typed TupleRow source row(s).\n";
    if (result_out) *result_out = std::move(result);
    else emit_query_result(result);
    if (limit_n >= 0 && before_limit > static_cast<std::size_t>(limit_n)) {
        std::cout << "SQLSEL: LIMIT reached; "
                  << (before_limit - static_cast<std::size_t>(limit_n))
                  << " more row(s) available.\n";
    }
    return true;
}

std::string format_aggregate_number(double value, int decimals) {
    std::ostringstream out;
    out << std::fixed << std::setprecision(std::max(0, decimals)) << value;
    return out.str();
}

bool replace_ci_all(std::string& text,
                    const std::string& needle,
                    const std::string& replacement) {
    if (needle.empty()) return false;
    bool changed = false;
    for (std::size_t pos = 0;;) {
        const std::string upper_text = up(text);
        const std::size_t hit = upper_text.find(up(needle), pos);
        if (hit == std::string::npos) break;
        text.replace(hit, needle.size(), replacement);
        pos = hit + replacement.size();
        changed = true;
    }
    return changed;
}

bool execute_aggregate_term(const std::string& tail,
                            const std::string& select_list,
                            bool select_distinct,
                            QueryResult* result_out) {
    if (result_out) *result_out = QueryResult{};
    const std::size_t from_pos = find_kw(tail, "FROM");
    const std::size_t where_pos = find_kw(tail, "WHERE", from_pos + 4);
    const std::size_t group_pos = find_kw(tail, "GROUP", from_pos + 4);
    const std::size_t having_pos = find_kw(tail, "HAVING", from_pos + 4);
    const std::size_t order_pos = find_kw(tail, "ORDER", from_pos + 4);
    const std::size_t limit_pos = find_kw(tail, "LIMIT", from_pos + 4);
    const auto clause_end = [&](std::size_t begin) {
        std::size_t end = tail.size();
        for (const std::size_t pos : {where_pos, group_pos, having_pos, order_pos, limit_pos}) {
            if (pos != std::string::npos && pos > begin) end = std::min(end, pos);
        }
        return end;
    };

    std::size_t from_end = tail.size();
    for (const std::size_t pos : {where_pos, group_pos, having_pos, order_pos, limit_pos}) {
        if (pos != std::string::npos) from_end = std::min(from_end, pos);
    }
    const std::string from_clause = trim(tail.substr(from_pos + 4, from_end - from_pos - 4));
    if (from_clause.empty()) {
        std::cout << "SQLSEL: expected a table after FROM.\n";
        return true;
    }
    if (group_pos != std::string::npos &&
        up(trim(tail.substr(group_pos, 8))) != "GROUP BY") {
        std::cout << "SQLSEL: expected GROUP BY <column>[,<column>...].\n";
        return true;
    }

    std::string where_text;
    if (where_pos != std::string::npos) {
        where_text = trim(tail.substr(where_pos + 5, clause_end(where_pos) - where_pos - 5));
        if (where_text.empty()) {
            std::cout << "SQLSEL: WHERE requires a predicate.\n";
            return true;
        }
    }
    std::string group_text;
    if (group_pos != std::string::npos) {
        group_text = trim(tail.substr(group_pos + 8, clause_end(group_pos) - group_pos - 8));
        if (group_text.empty()) {
            std::cout << "SQLSEL: GROUP BY requires at least one column.\n";
            return true;
        }
    }
    std::string having_text;
    if (having_pos != std::string::npos) {
        having_text = trim(tail.substr(having_pos + 6, clause_end(having_pos) - having_pos - 6));
        if (having_text.empty()) {
            std::cout << "SQLSEL: HAVING requires a predicate.\n";
            return true;
        }
    }

    std::string order_text;
    bool order_desc = false;
    if (order_pos != std::string::npos) {
        order_text = trim(tail.substr(order_pos + 5, clause_end(order_pos) - order_pos - 5));
        std::istringstream in(order_text);
        std::string by;
        in >> by >> order_text;
        if (up(by) != "BY" || order_text.empty()) {
            std::cout << "SQLSEL: expected ORDER BY <result-column> [ASC|DESC].\n";
            return true;
        }
        std::string direction;
        if (in >> direction) {
            if (up(direction) == "DESC") order_desc = true;
            else if (up(direction) != "ASC") {
                std::cout << "SQLSEL: ORDER BY direction must be ASC or DESC (got '"
                          << direction << "').\n";
                return true;
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
            std::cout << "SQLSEL: LIMIT expects a non-negative integer (got '"
                      << limit_text << "').\n";
            return true;
        }
    }

    // Validate aggregate syntax before materializing the source. A malformed
    // item must not scan a large table before it can fail closed.
    std::vector<AggregateItem> items;
    std::string error;
    for (const std::string& token : split_csv(select_list)) {
        AggregateItem item;
        if (!parse_aggregate_item(token, item, error)) {
            std::cout << "SQLSEL: " << error << ".\n";
            return true;
        }
        items.push_back(std::move(item));
    }
    if (items.empty()) {
        std::cout << "SQLSEL: the select list is empty.\n";
        return true;
    }

    std::string source_query = "SELECT * FROM " + from_clause;
    if (!where_text.empty()) source_query += " WHERE " + where_text;
    QueryResult source;
    if (!execute_select_term(source_query, &source) || !source.ok) return true;

    std::vector<std::size_t> group_positions;
    std::vector<std::string> group_tokens;
    if (!group_text.empty()) {
        group_tokens = split_csv(group_text);
        for (const std::string& token : group_tokens) {
            if (!is_bare_column(token)) {
                std::cout << "SQLSEL: GROUP BY item '" << token
                          << "' must be a column name.\n";
                return true;
            }
            std::size_t position = 0;
            if (!resolve_result_column(source, token, position, error)) {
                std::cout << "SQLSEL: " << error << ".\n";
                return true;
            }
            group_positions.push_back(position);
        }
    }

    for (AggregateItem& item : items) {
        if (item.kind == AggregateKind::None) {
            if (!is_bare_column(item.source)) {
                std::cout << "SQLSEL: aggregate query item '" << item.source
                          << "' must be a grouped column or aggregate.\n";
                return true;
            }
            if (!resolve_result_column(source, item.source, item.source_pos, error)) {
                std::cout << "SQLSEL: " << error << ".\n";
                return true;
            }
            if (std::find(group_positions.begin(), group_positions.end(), item.source_pos) ==
                group_positions.end()) {
                std::cout << "SQLSEL: selected column '" << item.source
                          << "' must appear in GROUP BY.\n";
                return true;
            }
            if (up(item.label) == up(item.source)) {
                item.label = source.columns[item.source_pos].name;
            }
            item.source_type = source.columns[item.source_pos].ftype;
            item.source_decimals = source.columns[item.source_pos].fdec;
        } else if (item.kind != AggregateKind::CountStar) {
            if (!resolve_result_column(source, item.source, item.source_pos, error)) {
                std::cout << "SQLSEL: " << error << ".\n";
                return true;
            }
            item.source_type = source.columns[item.source_pos].ftype;
            item.source_decimals = source.columns[item.source_pos].fdec;
            const char aggregate_type = static_cast<char>(std::toupper(
                static_cast<unsigned char>(item.source_type)));
            const bool numeric_type = aggregate_type == 'N' || aggregate_type == 'F' ||
                                      aggregate_type == 'B' || aggregate_type == 'Y' ||
                                      aggregate_type == 'I';
            if ((item.kind == AggregateKind::Sum || item.kind == AggregateKind::Avg) &&
                !numeric_type) {
                std::cout << "SQLSEL: " << item.label
                          << " requires a numeric column (got type '" << item.source_type
                          << "').\n";
                return true;
            }
        }
    }
    const std::size_t visible_item_count = items.size();

    // SQL HAVING may use an aggregate that is not projected. Materialize those
    // as hidden typed columns for predicate evaluation, then remove them before
    // ORDER BY/LIMIT/output. This keeps HAVING set-oriented without requiring a
    // second aggregate evaluator.
    if (!having_text.empty()) {
        const std::string upper_having = up(having_text);
        for (std::size_t cursor = 0; cursor < having_text.size();) {
            std::size_t hit = std::string::npos;
            for (const char* name : {"COUNT", "SUM", "AVG", "MIN", "MAX"}) {
                const std::size_t candidate = upper_having.find(name, cursor);
                if (candidate != std::string::npos &&
                    (hit == std::string::npos || candidate < hit)) hit = candidate;
            }
            if (hit == std::string::npos) break;
            const std::size_t open = having_text.find('(', hit);
            const std::size_t close = open == std::string::npos
                ? std::string::npos : having_text.find(')', open + 1);
            if (open == std::string::npos || close == std::string::npos) break;
            const std::string expression = trim(having_text.substr(hit, close - hit + 1));
            AggregateItem hidden;
            if (!parse_aggregate_item(expression, hidden, error) ||
                hidden.kind == AggregateKind::None) {
                std::cout << "SQLSEL: unsupported HAVING aggregate '" << expression << "'.\n";
                return true;
            }
            const bool already_present = std::any_of(items.begin(), items.end(),
                [&](const AggregateItem& item) { return up(item.label) == up(hidden.label); });
            if (!already_present && hidden.kind != AggregateKind::CountStar) {
                if (!resolve_result_column(source, hidden.source, hidden.source_pos, error)) {
                    std::cout << "SQLSEL: " << error << ".\n";
                    return true;
                }
                hidden.source_type = source.columns[hidden.source_pos].ftype;
                hidden.source_decimals = source.columns[hidden.source_pos].fdec;
                const char type = static_cast<char>(std::toupper(
                    static_cast<unsigned char>(hidden.source_type)));
                const bool numeric = type == 'N' || type == 'F' || type == 'B' ||
                                     type == 'Y' || type == 'I';
                if ((hidden.kind == AggregateKind::Sum || hidden.kind == AggregateKind::Avg) &&
                    !numeric) {
                    std::cout << "SQLSEL: " << hidden.label
                              << " requires a numeric column (got type '"
                              << hidden.source_type << "').\n";
                    return true;
                }
            }
            if (!already_present) items.push_back(std::move(hidden));
            cursor = close + 1;
        }
    }

    struct Group {
        dottalk::TupleRow key;
        std::vector<const dottalk::TupleRow*> rows;
    };
    std::vector<Group> groups;
    for (const auto& row : source.rows) {
        dottalk::TupleRow key;
        for (const std::size_t position : group_positions) {
            key.columns.push_back(source.columns[position]);
            key.values.push_back(row.values[position]);
            key.cell_kinds.push_back(row.cell_kind(position));
        }
        auto found = std::find_if(groups.begin(), groups.end(), [&](const Group& group) {
            return tuple_value_equal(group.key, key);
        });
        if (found == groups.end()) {
            groups.push_back({std::move(key), {&row}});
        } else {
            found->rows.push_back(&row);
        }
    }
    if (group_positions.empty()) {
        groups.clear();
        groups.push_back({{}, {}});
        for (const auto& row : source.rows) groups.front().rows.push_back(&row);
    }

    QueryResult result;
    result.ok = true;
    for (const auto& item : items) {
        dottalk::TupleColumn column;
        column.name = item.label;
        column.field = item.label;
        if (item.kind == AggregateKind::None) {
            column = source.columns[item.source_pos];
            column.name = item.label;
            column.field = item.label;
        } else if (item.kind == AggregateKind::Min || item.kind == AggregateKind::Max) {
            column.ftype = item.source_type;
            column.fdec = item.source_decimals;
        } else {
            column.ftype = 'N';
            column.fdec = item.kind == AggregateKind::Avg
                ? std::max(2, item.source_decimals) : item.source_decimals;
        }
        result.columns.push_back(std::move(column));
    }

    std::vector<std::size_t> contributed(items.size(), 0);
    std::vector<std::size_t> blanks(items.size(), 0);
    for (const Group& group : groups) {
        dottalk::TupleRow output;
        output.columns = result.columns;
        for (std::size_t item_index = 0; item_index < items.size(); ++item_index) {
            const AggregateItem& item = items[item_index];
            if (item.kind == AggregateKind::None) {
                const auto key_it = std::find(group_positions.begin(), group_positions.end(),
                                              item.source_pos);
                const std::size_t key_pos = static_cast<std::size_t>(
                    std::distance(group_positions.begin(), key_it));
                output.values.push_back(group.key.values[key_pos]);
                output.cell_kinds.push_back(group.key.cell_kind(key_pos));
                continue;
            }
            if (item.kind == AggregateKind::CountStar) {
                output.values.push_back(std::to_string(group.rows.size()));
                output.cell_kinds.push_back(dottalk::TupleCellKind::Present);
                continue;
            }

            std::vector<std::string> values;
            for (const dottalk::TupleRow* row : group.rows) {
                if (row->cell_kind(item.source_pos) == dottalk::TupleCellKind::ProducedAbsent ||
                    trim(row->values[item.source_pos]).empty()) {
                    ++blanks[item_index];
                    continue;
                }
                values.push_back(trim(row->values[item.source_pos]));
                ++contributed[item_index];
            }
            if (item.kind == AggregateKind::Count) {
                output.values.push_back(std::to_string(values.size()));
            } else if (values.empty()) {
                output.values.emplace_back();
            } else if (item.kind == AggregateKind::Sum || item.kind == AggregateKind::Avg) {
                double sum = 0.0;
                for (const std::string& value : values) sum += std::stod(value);
                if (item.kind == AggregateKind::Avg) sum /= static_cast<double>(values.size());
                const int decimals = item.kind == AggregateKind::Avg
                    ? std::max(2, item.source_decimals) : item.source_decimals;
                output.values.push_back(format_aggregate_number(sum, decimals));
            } else {
                std::string chosen = values.front();
                for (std::size_t i = 1; i < values.size(); ++i) {
                    const bool less = value_less(values[i], chosen);
                    if ((item.kind == AggregateKind::Min && less) ||
                        (item.kind == AggregateKind::Max && value_less(chosen, values[i]))) {
                        chosen = values[i];
                    }
                }
                output.values.push_back(std::move(chosen));
            }
            output.cell_kinds.push_back(dottalk::TupleCellKind::Present);
        }
        result.rows.push_back(std::move(output));
    }

    if (!having_text.empty()) {
        std::string rewritten = having_text;
        for (std::size_t i = 0; i < items.size(); ++i) {
            if (items[i].kind != AggregateKind::None) {
                replace_ci_all(rewritten, items[i].label, "__AGG_" + std::to_string(i));
            }
        }
        auto compiled = dottalk::expr::compile_where(rewritten);
        if (!compiled) {
            std::cout << "SQLSEL: could not compile the HAVING predicate: " << having_text
                      << " (" << compiled.error << ")\n";
            return true;
        }
        std::vector<dottalk::TupleRow> retained;
        for (auto& row : result.rows) {
            dottalk::TupleRow evaluation = row;
            for (std::size_t i = 0; i < items.size(); ++i) {
                if (items[i].kind != AggregateKind::None) {
                    evaluation.columns[i].name = "__AGG_" + std::to_string(i);
                    evaluation.columns[i].field = evaluation.columns[i].name;
                }
            }
            const PredicateVerdict verdict = evaluate_tuple_predicate(compiled.program.get(), evaluation);
            if (verdict.state == PredicateState::Error) {
                std::cout << "SQLSEL: HAVING evaluation failed: " << verdict.error << "\n";
                return true;
            }
            if (verdict.state == PredicateState::True) retained.push_back(std::move(row));
        }
        result.rows = std::move(retained);
    }

    if (items.size() > visible_item_count) {
        result.columns.resize(visible_item_count);
        for (auto& row : result.rows) {
            row.columns = result.columns;
            row.values.resize(visible_item_count);
            row.cell_kinds.resize(visible_item_count);
        }
        items.resize(visible_item_count);
        contributed.resize(visible_item_count);
        blanks.resize(visible_item_count);
    }

    if (select_distinct) {
        const std::size_t before = result.rows.size();
        distinct_rows(result.rows);
        std::cout << "SQLSEL: DISTINCT reduced " << before << " row(s) to "
                  << result.rows.size() << " row(s).\n";
    }
    if (!order_text.empty()) {
        std::size_t order_column = 0;
        if (!resolve_result_column(result, order_text, order_column, error)) {
            std::cout << "SQLSEL: ORDER BY " << error << ".\n";
            return true;
        }
        std::stable_sort(result.rows.begin(), result.rows.end(), [&](const auto& left,
                                                                     const auto& right) {
            return order_desc ? value_less(right.values[order_column], left.values[order_column])
                              : value_less(left.values[order_column], right.values[order_column]);
        });
        std::cout << "SQLSEL: aggregate ORDER BY " << order_text
                  << (order_desc ? " DESC" : " ASC") << " -- materialized sort over "
                  << result.rows.size() << " group(s).\n";
    }
    const std::size_t before_limit = result.rows.size();
    if (limit_n >= 0 && result.rows.size() > static_cast<std::size_t>(limit_n)) {
        result.rows.resize(static_cast<std::size_t>(limit_n));
    }

    for (std::size_t i = 0; i < items.size(); ++i) {
        if (items[i].kind != AggregateKind::None &&
            items[i].kind != AggregateKind::CountStar && blanks[i] > 0) {
            std::cout << "SQLSEL: " << items[i].label << " aggregate -- "
                      << contributed[i] << " of " << (contributed[i] + blanks[i])
                      << " row(s) carried a value; " << blanks[i] << " blank.\n";
        }
    }
    std::cout << "SQLSEL: aggregation produced " << result.rows.size()
              << " group row(s) from " << source.rows.size() << " source row(s).\n";
    if (result_out) *result_out = std::move(result);
    else emit_query_result(result);
    if (limit_n >= 0 && before_limit > static_cast<std::size_t>(limit_n)) {
        std::cout << "SQLSEL: LIMIT reached; "
                  << (before_limit - static_cast<std::size_t>(limit_n))
                  << " more row(s) available.\n";
    }
    return true;
}

void print_statement_usage() {
    std::cout
        << "SQLSEL statement usage:\n"
        << "  SQLSEL <col>[,<col>...] FROM <table> [[AS] <alias>]\n"
        << "         [WHERE <predicate>] [ORDER BY <field> [ASC|DESC]] [LIMIT <n>]\n"
        << "  SQLSEL * FROM <table>\n"
        << "  SQLSEL COUNT(*) FROM <table> [WHERE <predicate>]\n"
        << "  SQLSEL <list> FROM <table> [AS] <a> [INNER] JOIN\n"
        << "         <table> [AS] <b> ON <a.field> = <b.field>\n"
        << "  SQLSEL <list> FROM <table> [AS] <a> LEFT JOIN\n"
        << "         <table> [AS] <b> ON <a.field> = <b.field>\n"
        << "  SQLSEL <list> FROM <table> [AS] <a> RIGHT JOIN\n"
        << "         <table> [AS] <b> ON <a.field> = <b.field>\n"
        << "  SQLSEL <list> FROM <table> [AS] <a> FULL JOIN\n"
        << "         <table> [AS] <b> ON <a.field> = <b.field>\n"
        << "  SQLSEL <list> FROM <table> [AS] <a> CROSS JOIN <table> [AS] <b>\n"
        << "  SQLSEL DISTINCT <list> FROM <table>\n"
        << "  SQLSEL <select> UNION [ALL] <select>\n"
        << "  SQLSEL <select> INTERSECT <select> | <select> EXCEPT <select>\n"
        << "  SQLSEL <group-list>,<aggregate-list> FROM <source>\n"
        << "         [WHERE <predicate>] [GROUP BY <list>] [HAVING <predicate>]\n"
        << "  SQLSEL <list> FROM <table> WHERE <value> IN (<select>)\n"
        << "  SQLSEL <list> FROM <table> WHERE [NOT] EXISTS (<select>)\n"
        << "  SQLSEL INSERT INTO <table> (<fields>) VALUES (<values>)[,(<values>)...]\n"
        << "  SQLSEL UPDATE <table> [[AS] <alias>] SET <field>=<expr>[,...]\n"
        << "         WHERE <predicate>\n"
        << "  SQLSEL DELETE FROM <table> [[AS] <alias>] WHERE <predicate>\n"
        << "  SET MODE SQL; BEGIN [TRANSACTION]; <DML>; COMMIT|ROLLBACK\n"
        << "Notes:\n"
        << "  SQLSEL is itself the select verb; the SELECT keyword is OPTIONAL\n"
        << "  (SQLSEL SELECT ... still parses). Not to be confused with xBase\n"
        << "  SELECT <area>, which switches the active work area.\n"
        << "  The table must be OPEN (USE <table>) -- SQLSEL reads open work areas.\n"
        << "  INNER, LEFT, RIGHT, and FULL join two open tables; INNER/LEFT/CROSS\n"
        << "  may chain across three or more. CROSS emits a Cartesian product\n"
        << "  without ON. JOIN WHERE evaluates\n"
        << "  after outer extension; produced-absent comparisons are UNKNOWN and\n"
        << "  WHERE retains only TRUE. No REL or SET RELATION state is read.\n"
        << "  Outer-join absence renders as " << dottalk::kProducedAbsentMarker
        << "; genuine DBF blanks remain blank.\n"
        << "  JOIN takes a non-blocking two-table read fence; lock contention\n"
        << "  refuses the statement before either table is read.\n"
        << "  Aggregate functions are COUNT, SUM, AVG, MIN, and MAX. Numeric\n"
        << "  aggregates skip blank cells and report the contributing/blank split.\n"
        << "  Set operands require equal column counts and compatible tuple types.\n"
        << "  Correlated subqueries report their actual evaluation count. Subqueries\n"
        << "  over a joined outer scope are refused.\n"
        << "  SELECT restores the current area and every source record pointer.\n"
        << "  DML uses typed TableBuffer + TBJ1 WAL writes. Explicit transactions\n"
        << "  require SQL mode and accept one target table; cross-table atomic\n"
        << "  commit, stored NULL, and memo-field DML are refused.\n";
}

bool execute_select_term(const std::string& tail_in, QueryResult* result_out) {
    if (result_out) *result_out = QueryResult{};
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

    std::string select_list = trim(tail.substr(list_start, from_pos - list_start));
    if (select_list.empty()) {
        std::cout << "SQLSEL: the select list is empty.\n";
        print_statement_usage();
        return true;
    }
    bool select_distinct = false;
    if (find_kw(select_list, "DISTINCT") == 0) {
        select_distinct = true;
        select_list = trim(select_list.substr(8));
        if (select_list.empty()) {
            std::cout << "SQLSEL: DISTINCT requires a select list.\n";
            return true;
        }
    }

    const bool has_grouping_clause = find_kw(tail, "GROUP", from_pos + 4) != std::string::npos ||
                                     find_kw(tail, "HAVING", from_pos + 4) != std::string::npos;
    bool has_new_aggregate = false;
    for (const std::string& token : split_csv(select_list)) {
        AggregateItem aggregate;
        std::string aggregate_error;
        if (!parse_aggregate_item(token, aggregate, aggregate_error)) {
            if (find_kw(up(token), "SUM") == 0 || find_kw(up(token), "AVG") == 0 ||
                find_kw(up(token), "MIN") == 0 || find_kw(up(token), "MAX") == 0 ||
                find_kw(up(token), "COUNT") == 0) {
                return execute_aggregate_term(tail, select_list, select_distinct, result_out);
            }
            continue;
        }
        if (aggregate.kind != AggregateKind::None &&
            (aggregate.kind != AggregateKind::CountStar ||
             find_kw(token, "AS") != std::string::npos)) {
            has_new_aggregate = true;
        }
    }
    if (has_grouping_clause || has_new_aggregate) {
        return execute_aggregate_term(tail, select_list, select_distinct, result_out);
    }

    bool expression_projection = false;
    for (const std::string& raw : split_csv(select_list)) {
        std::string core = raw;
        const std::size_t as_pos = find_kw(core, "AS");
        if (as_pos != std::string::npos) {
            expression_projection = true;
            core = trim(core.substr(0, as_pos));
        }
        std::string compact;
        for (const char c : core) {
            if (!std::isspace(static_cast<unsigned char>(c))) compact.push_back(c);
        }
        if (core != "*" && up(compact) != "COUNT(*)" && !is_bare_column(core)) {
            expression_projection = true;
        }
    }
    const std::size_t projection_order_pos = find_kw(tail, "ORDER", from_pos + 4);
    bool multi_order = false;
    if (projection_order_pos != std::string::npos) {
        const std::size_t projection_limit_pos = find_kw(tail, "LIMIT", projection_order_pos + 5);
        const std::size_t order_end = projection_limit_pos == std::string::npos
            ? tail.size() : projection_limit_pos;
        multi_order = tail.substr(projection_order_pos, order_end - projection_order_pos)
                          .find(',') != std::string::npos;
    }
    if (expression_projection || multi_order) {
        return execute_expression_projection(tail, select_list, select_distinct, result_out);
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

    // P4 JOIN owns the full FROM clause. Keep it out of the single-table
    // resolver below so no REL/session state can leak into matching.
    if (has_join) {
        if (find_subquery_paren(where_text) != std::string::npos) {
            std::cout << "SQLSEL: P4.7 subquery predicates currently require a single-table "
                         "outer query; joined outer scopes arrive with generalized JOIN.\n";
            return true;
        }
        if (!select_distinct) {
            return execute_join(select_list, table_clause, where_text,
                                order_field, order_desc, limit_n, result_out);
        }
        QueryResult result;
        if (!execute_join(select_list, table_clause, where_text,
                          order_field, order_desc, -1, &result) || !result.ok) {
            return true;
        }
        const std::size_t input_rows = result.rows.size();
        distinct_rows(result.rows);
        const std::size_t distinct_count = result.rows.size();
        if (limit_n >= 0 && result.rows.size() > static_cast<std::size_t>(limit_n)) {
            result.rows.resize(static_cast<std::size_t>(limit_n));
        }
        std::cout << "SQLSEL: DISTINCT reduced " << input_rows << " row(s) to "
                  << distinct_count << " row(s).\n";
        if (result_out) {
            *result_out = std::move(result);
        } else {
            emit_query_result(result);
        }
        if (limit_n >= 0 && distinct_count > static_cast<std::size_t>(limit_n)) {
            std::cout << "SQLSEL: LIMIT reached; "
                      << (distinct_count - static_cast<std::size_t>(limit_n))
                      << " more row(s) available.\n";
        }
        return true;
    }

    // --- resolve FROM against OPEN work areas (statement-scoped) -------------
    xbase::DbArea* area = resolve_sqlsel_area(table_name);
    if (!area) {
        std::cout << "SQLSEL: table '" << table_name << "' is not open.\n";
        std::cout << "        Open it first (USE " << table_name
                  << ") -- SQLSEL reads open work areas.\n";
        return true;
    }

    // --- build the projection spec ------------------------------------------
    // The statement resolver has already selected the table inside the current
    // workspace. Feed that exact handle to the house tuple builder. Repeating a
    // logical-name lookup here would throw the workspace decision away and
    // become ambiguous when another workspace has the same table name.
    const int resolved_slot = cli::slot_of_area(area);
    if (resolved_slot < 0) {
        std::cout << "SQLSEL: could not determine the resolved table's work-area slot.\n";
        return true;
    }
    const std::string area_label = "#" + std::to_string(resolved_slot);
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

    QueryResult result;
    if (count_star) {
        dottalk::TupleColumn count_column;
        count_column.name = "COUNT(*)";
        count_column.field = "COUNT(*)";
        count_column.ftype = 'N';
        result.columns.push_back(count_column);
    } else if (star) {
        for (const auto& fd : area->fields()) {
            result.columns.push_back({fd.name, -1, fd.name, fd.type,
                                      static_cast<int>(fd.length), static_cast<int>(fd.decimals)});
        }
    } else {
        for (const auto& token : split_csv(select_list)) {
            const std::size_t dot = token.find('.');
            const std::string field = dot == std::string::npos ? token : token.substr(dot + 1);
            const auto index = field_index_ci(*area, field);
            if (!index) {
                std::cout << "SQLSEL: column '" << token << "' was not found in "
                          << table_name << ".\n";
                return true;
            }
            const auto& fd = area->fields()[*index];
            result.columns.push_back({fd.name, -1, fd.name, fd.type,
                                      static_cast<int>(fd.length), static_cast<int>(fd.decimals)});
        }
    }

    // --- compile the predicate ONCE (not per row) ----------------------------
    std::unique_ptr<dottalk::expr::Expr> pred;
    const bool subquery_where = find_subquery_paren(where_text) != std::string::npos;
    SubqueryRuntime subquery_runtime;
    if (!where_text.empty() && !subquery_where) {
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

                if (keep && (pred || subquery_where)) {
                    dottalk::TupleBuildResult predicate_row =
                        dottalk::build_tuple_from_spec(area_label + ".*", opts);
                    if (!predicate_row.ok) {
                        scan_error = "predicate row build failed: " + predicate_row.error;
                        break;
                    }
                    for (auto& column : predicate_row.row.columns) {
                        column.name = single_table.alias + "." + column.field;
                    }
                    if (subquery_where) {
                        PredicateState verdict = PredicateState::Error;
                        std::string predicate_error;
                        if (!evaluate_sql_predicate(where_text, predicate_row.row,
                                                    subquery_runtime, verdict,
                                                    predicate_error)) {
                            scan_error = "subquery predicate failed: " + predicate_error;
                            break;
                        }
                        keep = verdict == PredicateState::True;
                    } else {
                        const auto verdict = evaluate_tuple_predicate(pred.get(), predicate_row.row);
                        if (verdict.state == PredicateState::Error) {
                            scan_error = "predicate evaluation failed: " + verdict.error;
                            break;
                        }
                        keep = verdict.state == PredicateState::True;
                    }
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

        // PASS 2: materialize typed TupleRows. DISTINCT is applied after
        // projection and before LIMIT, so it requests the complete match set.
        if (scan_error.empty() && !count_star) {
            std::size_t shown = 0;
            const long long projection_limit = select_distinct ? -1 : limit_n;
            for (const auto& m : matches) {
                if (projection_limit >= 0 && static_cast<long long>(shown) >= projection_limit) break;
                try {
                    area->gotoRec64(static_cast<std::uint64_t>(m.recno));
                    if (!area->readCurrent()) break;
                } catch (...) { break; }

                const dottalk::TupleBuildResult r = dottalk::build_tuple_from_spec(spec, opts);
                if (!r.ok) { scan_error = "projection failed: " + r.error; break; }
                dottalk::TupleRow projected = r.row;
                projected.columns = result.columns;
                if (projected.cell_kinds.empty()) {
                    projected.cell_kinds.assign(projected.values.size(),
                                                dottalk::TupleCellKind::Present);
                }
                result.rows.push_back(std::move(projected));
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

    if (subquery_where) {
        std::cout << "SQLSEL: subquery evaluation count -- correlated="
                  << subquery_runtime.correlated_evaluations << ", uncorrelated="
                  << subquery_runtime.uncorrelated_evaluations << ".\n";
    }

    if (count_star) {
        dottalk::TupleRow count_row;
        count_row.columns = result.columns;
        count_row.values.push_back(std::to_string(matched_total));
        count_row.cell_kinds.push_back(dottalk::TupleCellKind::Present);
        result.rows.push_back(std::move(count_row));
    }

    std::size_t pre_limit_count = count_star ? result.rows.size() : matches.size();
    if (select_distinct && !count_star) {
        const std::size_t input_rows = result.rows.size();
        distinct_rows(result.rows);
        pre_limit_count = result.rows.size();
        std::cout << "SQLSEL: DISTINCT reduced " << input_rows << " row(s) to "
                  << pre_limit_count << " row(s).\n";
        if (limit_n >= 0 && result.rows.size() > static_cast<std::size_t>(limit_n)) {
            result.rows.resize(static_cast<std::size_t>(limit_n));
        }
    }
    result.ok = true;
    if (result_out) {
        *result_out = std::move(result);
    } else {
        emit_query_result(result);
    }
    if (!count_star && limit_n >= 0 && pre_limit_count > static_cast<std::size_t>(limit_n)) {
        std::cout << "SQLSEL: LIMIT reached; "
                  << (pre_limit_count - static_cast<std::size_t>(limit_n))
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

enum class SetOperation { UnionDistinct, UnionAll, Intersect, Except };

const char* set_operation_name(SetOperation op) {
    switch (op) {
        case SetOperation::UnionDistinct: return "UNION";
        case SetOperation::UnionAll: return "UNION ALL";
        case SetOperation::Intersect: return "INTERSECT";
        case SetOperation::Except: return "EXCEPT";
    }
    return "SET";
}

bool split_set_expression(const std::string& text,
                          std::vector<std::string>& terms,
                          std::vector<SetOperation>& operations,
                          std::string& error) {
    std::size_t cursor = 0;
    for (;;) {
        const std::size_t union_pos = find_kw(text, "UNION", cursor);
        const std::size_t intersect_pos = find_kw(text, "INTERSECT", cursor);
        const std::size_t except_pos = find_kw(text, "EXCEPT", cursor);
        std::size_t pos = std::string::npos;
        SetOperation op = SetOperation::UnionDistinct;
        std::size_t width = 0;
        const auto consider = [&](std::size_t candidate, SetOperation candidate_op,
                                  std::size_t candidate_width) {
            if (candidate != std::string::npos &&
                (pos == std::string::npos || candidate < pos)) {
                pos = candidate;
                op = candidate_op;
                width = candidate_width;
            }
        };
        consider(union_pos, SetOperation::UnionDistinct, 5);
        consider(intersect_pos, SetOperation::Intersect, 9);
        consider(except_pos, SetOperation::Except, 6);
        if (pos == std::string::npos) {
            terms.push_back(trim(text.substr(cursor)));
            break;
        }
        terms.push_back(trim(text.substr(cursor, pos - cursor)));
        cursor = pos + width;
        while (cursor < text.size() &&
               std::isspace(static_cast<unsigned char>(text[cursor]))) ++cursor;
        if (op == SetOperation::UnionDistinct &&
            find_kw(text, "ALL", cursor) == cursor) {
            op = SetOperation::UnionAll;
            cursor += 3;
        } else if (find_kw(text, "ALL", cursor) == cursor) {
            error = std::string(set_operation_name(op)) +
                    " ALL is not part of the SQLsel P4.5 set-operation contract";
            return false;
        } else if (op == SetOperation::UnionDistinct &&
                   find_kw(text, "DISTINCT", cursor) == cursor) {
            cursor += 8;
        }
        operations.push_back(op);
    }
    if (terms.size() != operations.size() + 1 ||
        std::any_of(terms.begin(), terms.end(), [](const auto& term) { return term.empty(); })) {
        error = "every set operator requires a SELECT operand on both sides";
        return false;
    }
    return true;
}

enum class ColumnFamily { Text, Numeric, Date, Logical, Unknown };

ColumnFamily column_family(char raw_type) {
    const char type = static_cast<char>(std::toupper(static_cast<unsigned char>(raw_type)));
    if (type == 'C' || type == 'M') return ColumnFamily::Text;
    if (type == 'N' || type == 'F' || type == 'B' || type == 'Y' || type == 'I') {
        return ColumnFamily::Numeric;
    }
    if (type == 'D' || type == 'T') return ColumnFamily::Date;
    if (type == 'L') return ColumnFamily::Logical;
    return ColumnFamily::Unknown;
}

bool set_columns_compatible(const QueryResult& left,
                            const QueryResult& right,
                            std::string& error) {
    if (left.columns.size() != right.columns.size()) {
        error = "set operands have " + std::to_string(left.columns.size()) + " and " +
                std::to_string(right.columns.size()) + " columns; counts must match";
        return false;
    }
    for (std::size_t i = 0; i < left.columns.size(); ++i) {
        const ColumnFamily lf = column_family(left.columns[i].ftype);
        const ColumnFamily rf = column_family(right.columns[i].ftype);
        if (lf == ColumnFamily::Unknown || rf == ColumnFamily::Unknown || lf != rf) {
            error = "set operand column " + std::to_string(i + 1) + " has incompatible types '" +
                    left.columns[i].ftype + "' and '" + right.columns[i].ftype + "'";
            return false;
        }
    }
    return true;
}

bool contains_tuple(const std::vector<dottalk::TupleRow>& rows,
                    const dottalk::TupleRow& candidate) {
    return std::any_of(rows.begin(), rows.end(), [&](const auto& row) {
        return tuple_value_equal(row, candidate);
    });
}

QueryResult apply_set_operation(QueryResult left,
                                QueryResult right,
                                SetOperation op) {
    QueryResult result;
    result.ok = true;
    result.columns = left.columns;
    auto append = [&](dottalk::TupleRow row) {
        row.columns = result.columns;
        result.rows.push_back(std::move(row));
    };

    if (op == SetOperation::UnionAll) {
        result.rows.reserve(left.rows.size() + right.rows.size());
        for (auto& row : left.rows) append(std::move(row));
        for (auto& row : right.rows) append(std::move(row));
    } else if (op == SetOperation::UnionDistinct) {
        for (auto& row : left.rows) {
            if (!contains_tuple(result.rows, row)) append(std::move(row));
        }
        for (auto& row : right.rows) {
            if (!contains_tuple(result.rows, row)) append(std::move(row));
        }
    } else if (op == SetOperation::Intersect) {
        for (auto& row : left.rows) {
            if (contains_tuple(right.rows, row) && !contains_tuple(result.rows, row)) {
                append(std::move(row));
            }
        }
    } else {
        for (auto& row : left.rows) {
            if (!contains_tuple(right.rows, row) && !contains_tuple(result.rows, row)) {
                append(std::move(row));
            }
        }
    }
    return result;
}

// ---------------------------------------------------------------------------
// P5: typed SQL DML over the house table-buffer / WAL / lock machinery.
// ---------------------------------------------------------------------------

struct SqlTransactionState {
    bool active = false;
    bool explicit_scope = false;
    xbase::DbArea* area = nullptr;
    int area0 = -1;
    bool lock_acquired_here = false;
    bool prior_buffer_enabled = false;
    bool prior_history_enabled = false;
    dottalk::table::BufferPersistenceMode prior_persistence =
        dottalk::table::BufferPersistenceMode::RamOnly;
};

SqlTransactionState& sql_transaction_state() {
    static SqlTransactionState state;
    return state;
}

std::string statement_without_semicolon(std::string text) {
    text = trim(std::move(text));
    if (!text.empty() && text.back() == ';') text = trim(text.substr(0, text.size() - 1));
    return text;
}

std::string leading_word(const std::string& text) {
    std::istringstream input(text);
    std::string word;
    input >> word;
    return up(word);
}

std::string after_leading_word(const std::string& text) {
    std::size_t pos = 0;
    while (pos < text.size() && std::isspace(static_cast<unsigned char>(text[pos]))) ++pos;
    while (pos < text.size() && !std::isspace(static_cast<unsigned char>(text[pos]))) ++pos;
    return trim(text.substr(pos));
}

std::size_t top_level_equal(const std::string& text) {
    bool in_single = false, in_double = false;
    int depth = 0;
    for (std::size_t i = 0; i < text.size(); ++i) {
        const char c = text[i];
        if (c == '\'' && !in_double) { in_single = !in_single; continue; }
        if (c == '"' && !in_single) { in_double = !in_double; continue; }
        if (in_single || in_double) continue;
        if (c == '(') { ++depth; continue; }
        if (c == ')') { if (depth > 0) --depth; continue; }
        if (depth == 0 && c == '=') return i;
    }
    return std::string::npos;
}

bool split_value_groups(const std::string& text,
                        std::vector<std::string>& groups,
                        std::string& error) {
    groups.clear();
    std::size_t pos = 0;
    while (pos < text.size()) {
        while (pos < text.size() &&
               (std::isspace(static_cast<unsigned char>(text[pos])) || text[pos] == ',')) ++pos;
        if (pos >= text.size()) break;
        if (text[pos] != '(') {
            error = "VALUES expects one or more parenthesized rows";
            return false;
        }
        const std::size_t start = ++pos;
        bool in_single = false, in_double = false;
        int depth = 1;
        for (; pos < text.size() && depth > 0; ++pos) {
            const char c = text[pos];
            if (c == '\'' && !in_double) { in_single = !in_single; continue; }
            if (c == '"' && !in_single) { in_double = !in_double; continue; }
            if (in_single || in_double) continue;
            if (c == '(') ++depth;
            else if (c == ')') --depth;
        }
        if (depth != 0) {
            error = "VALUES row has unbalanced parentheses";
            return false;
        }
        groups.push_back(text.substr(start, pos - start - 1));
        while (pos < text.size() && std::isspace(static_cast<unsigned char>(text[pos]))) ++pos;
        if (pos < text.size() && text[pos] != ',') {
            error = "unexpected input after VALUES row";
            return false;
        }
    }
    if (groups.empty()) {
        error = "VALUES requires at least one row";
        return false;
    }
    return true;
}

void release_sql_transaction(bool restore_buffer_policy) noexcept {
    auto& state = sql_transaction_state();
    if (state.area && state.area0 >= 0 && restore_buffer_policy) {
        dottalk::table::set_history_enabled(state.area0, state.prior_history_enabled);
        dottalk::table::set_persistence_mode(state.area0, state.prior_persistence);
        if (!state.prior_buffer_enabled) dottalk::table::set_enabled(state.area0, false);
    }
    if (state.area && state.lock_acquired_here) {
        std::string ignored;
        (void)xbase::locks::unlock_table(
            *state.area, xbase::locks::current_owner(), &ignored);
    }
    state = SqlTransactionState{};
}

void rollback_sql_transaction(const char* reason = nullptr) {
    auto& state = sql_transaction_state();
    if (state.area && state.area0 >= 0) {
        cli::ScopedAreaSelect focus(state.area);
        std::istringstream empty;
        cmd_ROLLBACK(*state.area, empty);
    }
    release_sql_transaction(true);
    if (reason && *reason) std::cout << "SQLSEL: transaction rolled back -- " << reason << ".\n";
}

bool enlist_sql_transaction(xbase::DbArea& area, std::string& error) {
    auto& state = sql_transaction_state();
    if (!state.active) {
        error = "internal transaction state was not started";
        return false;
    }
    if (state.area == &area) return true;
    if (state.area) {
        error = "one SQL transaction may modify one table; cross-table atomic commit is not available";
        return false;
    }
    const int area0 = cli::slot_of_area(&area);
    if (area0 < 0) {
        error = "could not determine the target work area";
        return false;
    }
    if (!dottalk::table::get_tb_const(area0).empty() || dottalk::table::is_dirty(area0)) {
        error = "target table already has buffered changes outside this SQL transaction";
        return false;
    }

    xbase::locks::LockHolder holder;
    const bool borrowed = xbase::locks::table_lock_holder(area, &holder) &&
                          holder.owner_id == xbase::locks::current_owner().id;
    std::string lock_error;
    if (!xbase::locks::try_lock_table(area, &lock_error)) {
        error = lock_error.empty() ? "table lock refused" : lock_error;
        return false;
    }

    state.area = &area;
    state.area0 = area0;
    state.lock_acquired_here = !borrowed;
    state.prior_buffer_enabled = dottalk::table::is_enabled(area0);
    state.prior_history_enabled = dottalk::table::is_history_enabled(area0);
    state.prior_persistence = dottalk::table::persistence_mode(area0);
    if (!state.prior_buffer_enabled) dottalk::table::set_enabled(area0, true);
    dottalk::table::set_history_enabled(area0, false);
    dottalk::table::set_persistence_mode(
        area0, dottalk::table::BufferPersistenceMode::RamJournal);
    if (!dottalk::table::journal_note_buffer_on(area0, area.filename())) {
        error = "could not open the table-buffer write-ahead journal";
        release_sql_transaction(true);
        return false;
    }
    return true;
}

bool commit_sql_transaction(std::string& error) {
    auto& state = sql_transaction_state();
    if (!state.area) {
        release_sql_transaction(false);
        return true;
    }
    {
        cli::ScopedAreaSelect focus(state.area);
        std::istringstream empty;
        cmd_COMMIT(*state.area, empty);
    }
    if (!dottalk::table::get_tb_const(state.area0).empty()) {
        error = "the house COMMIT path retained buffered changes; the transaction remains active for retry or rollback";
        return false;
    }
    release_sql_transaction(true);
    return true;
}

bool begin_dml_scope(bool explicit_scope, std::string& error) {
    auto& state = sql_transaction_state();
    if (state.active) {
        if (explicit_scope) error = "a SQL transaction is already active";
        return !explicit_scope;
    }
    state = SqlTransactionState{};
    state.active = true;
    state.explicit_scope = explicit_scope;
    return true;
}

bool field_is_memo(const xbase::DbArea& area, int field1) {
    if (field1 < 1 || field1 > area.fieldCount()) return false;
    return std::toupper(static_cast<unsigned char>(
               area.fields()[static_cast<std::size_t>(field1 - 1)].type)) == 'M';
}

std::string trim_generated_numeric(std::string value) {
    const std::size_t dot = value.find('.');
    if (dot == std::string::npos) return value;
    while (!value.empty() && value.back() == '0') value.pop_back();
    if (!value.empty() && value.back() == '.') value.pop_back();
    return value.empty() ? "0" : value;
}

bool evaluate_store_expression(const std::string& expression,
                               const dottalk::TupleRow& row,
                               xbase::DbArea& area,
                               int field1,
                               std::string& value,
                               std::string& error) {
    if (up(trim(expression)) == "NULL") {
        error = "NULL is not a stored x64base value; use an explicit typed blank";
        return false;
    }
    if (field_is_memo(area, field1)) {
        error = "memo-field DML is refused until the memo store joins the DBF WAL atomicity boundary";
        return false;
    }
    auto compiled = dottalk::expr::compile_where(expression);
    if (!compiled) {
        error = "could not compile value expression '" + expression + "': " + compiled.error;
        return false;
    }
    try {
        value = compiled.program->evalString(dottalk::exprglue::make_record_view(row));
    } catch (const std::exception& ex) {
        error = "value expression '" + expression + "' failed: " + ex.what();
        return false;
    }
    const auto& field = area.fields()[static_cast<std::size_t>(field1 - 1)];
    const char type = static_cast<char>(std::toupper(static_cast<unsigned char>(field.type)));
    if (type == 'N' || type == 'F' || type == 'I' || type == 'B' || type == 'Y') {
        value = trim_generated_numeric(value);
    }
    if (type == 'C' && value.size() > static_cast<std::size_t>(field.length)) {
        error = "value for '" + field.name + "' exceeds its declared width " +
                std::to_string(field.length);
        return false;
    }
    if (!dottalk::fieldstore::validate_and_normalize(area, field1, value, error)) {
        error = field.name + ": " + error;
        return false;
    }
    std::string constraint_error;
    if (!dottalk::constraints::validate_field_constraint_for_store(
            area, field1, value, constraint_error)) {
        error = constraint_error;
        return false;
    }
    return true;
}

struct PendingDmlRow {
    std::uint64_t recno = 0;
    std::uint64_t flags = 0;
    std::vector<std::pair<int, std::string>> fields;
};

bool stage_dml_rows(xbase::DbArea& area,
                    const std::vector<PendingDmlRow>& rows,
                    std::string& error) {
    (void)area;
    auto& state = sql_transaction_state();
    auto& buffer = dottalk::table::get_tb(state.area0);
    std::size_t new_records = 0;
    for (const auto& row : rows) {
        if (buffer.changes.find(row.recno) == buffer.changes.end()) ++new_records;
    }
    if (buffer.changes.size() + new_records > dottalk::table::TableBuffer::kMaxChanges) {
        error = "table-buffer capacity would be exceeded";
        return false;
    }

    for (const auto& row : rows) {
        if (row.fields.empty()) {
            const int priority = buffer.add_change(row.recno, row.flags);
            if (priority == 0) { error = "table buffer refused a change"; return false; }
            dottalk::table::ChangeEntry journal;
            journal.recno = row.recno;
            journal.dirty_flags = row.flags;
            journal.priority = priority;
            if (!dottalk::table::journal_note_change(state.area0, journal)) {
                error = "write-ahead journal refused a change";
                return false;
            }
            dottalk::table::set_stale(state.area0, true);
            continue;
        }
        for (const auto& [field1, value] : row.fields) {
            std::uint64_t bits[dottalk::table::kWords]{};
            const int index0 = field1 - 1;
            bits[index0 / 64] |= (std::uint64_t{1} << (index0 % 64));
            const int priority = buffer.add_change(
                row.recno, row.flags, bits, field1, value);
            if (priority == 0) { error = "table buffer refused a change"; return false; }
            dottalk::table::ChangeEntry journal;
            journal.recno = row.recno;
            journal.dirty_flags = row.flags;
            journal.priority = priority;
            journal.new_values[field1] = value;
            if (!dottalk::table::journal_note_change(state.area0, journal)) {
                error = "write-ahead journal refused a change";
                return false;
            }
            dottalk::table::mark_stale_field(state.area0, field1);
        }
    }
    if (!rows.empty()) dottalk::table::set_dirty(state.area0, true);
    return true;
}

bool materialize_dml_source(const TableRef& table,
                            std::vector<dottalk::TupleRow>& rows,
                            std::string& error) {
    const auto columns = join_source_columns(table);
    if (!materialize_join_source(table, columns, rows, error)) return false;
    const auto& state = sql_transaction_state();
    if (state.area != table.area || state.area0 < 0) return true;

    const auto& changes = dottalk::table::get_tb_const(state.area0).changes;
    std::vector<dottalk::TupleRow> visible;
    visible.reserve(rows.size() + changes.size());
    for (auto row : rows) {
        const std::uint64_t recno = row.fragments.empty() ? 0 : row.fragments.front().recno;
        const auto it = changes.find(recno);
        if (it != changes.end()) {
            const auto& change = it->second;
            if (change.dirty_flags & dottalk::table::CHANGE_DELETE) continue;
            for (const auto& [field1, value] : change.new_values) {
                if (field1 > 0 && static_cast<std::size_t>(field1) <= row.values.size()) {
                    row.values[static_cast<std::size_t>(field1 - 1)] = value;
                }
            }
        }
        visible.push_back(std::move(row));
    }
    for (const auto& [recno, change] : changes) {
        if (!(change.dirty_flags & dottalk::table::CHANGE_INSERT) ||
            (change.dirty_flags & dottalk::table::CHANGE_DELETE)) continue;
        dottalk::TupleRow row;
        row.columns = columns;
        row.values.assign(columns.size(), std::string{});
        row.cell_kinds.assign(columns.size(), dottalk::TupleCellKind::Present);
        row.fragments.push_back({-1, recno, dottalk::TupleSourceKind::DBF,
                                 false, "SQLSEL:" + table.alias + ":buffer"});
        for (const auto& [field1, value] : change.new_values) {
            if (field1 > 0 && static_cast<std::size_t>(field1) <= row.values.size()) {
                row.values[static_cast<std::size_t>(field1 - 1)] = value;
            }
        }
        visible.push_back(std::move(row));
    }
    rows = std::move(visible);
    return true;
}

bool finish_dml_statement(bool implicit_scope,
                          const char* verb,
                          std::size_t affected) {
    if (!implicit_scope) {
        std::cout << "SQLSEL: " << verb << " staged " << affected
                  << " row(s) in the active transaction.\n";
        return true;
    }
    std::string error;
    if (!commit_sql_transaction(error)) {
        std::cout << "SQLSEL: " << verb << " commit failed -- " << error << ".\n";
        return true;
    }
    std::cout << "SQLSEL: " << verb << " affected " << affected
              << " row(s); committed through table buffer + WAL.\n";
    return true;
}

bool prepare_dml_table(const TableRef& table,
                       bool& implicit_scope,
                       std::string& error) {
    auto& state = sql_transaction_state();
    implicit_scope = !state.active;
    if (implicit_scope && !begin_dml_scope(false, error)) return false;
    if (!enlist_sql_transaction(*table.area, error)) {
        if (implicit_scope) release_sql_transaction(false);
        return false;
    }
    return true;
}

bool execute_insert_statement(const std::string& statement) {
    const std::string body0 = after_leading_word(statement);
    if (leading_word(body0) != "INTO") {
        std::cout << "SQLSEL: INSERT requires INTO <table> (<fields>) VALUES (...).\n";
        return true;
    }
    const std::string body = after_leading_word(body0);
    const std::size_t values_pos = find_kw(body, "VALUES");
    if (values_pos == std::string::npos) {
        std::cout << "SQLSEL: INSERT requires a VALUES clause.\n";
        return true;
    }
    const std::string target = trim(body.substr(0, values_pos));
    const std::size_t open = target.find('(');
    const std::size_t close = target.rfind(')');
    if (open == std::string::npos || close == std::string::npos || close < open ||
        !trim(target.substr(close + 1)).empty()) {
        std::cout << "SQLSEL: INSERT requires an explicit parenthesized field list.\n";
        return true;
    }
    TableRef table;
    std::string error;
    if (!parse_table_ref(trim(target.substr(0, open)), table, error) ||
        up(table.name) != up(table.alias)) {
        std::cout << "SQLSEL: INSERT target must be one unaliased table.\n";
        return true;
    }
    table.area = resolve_sqlsel_area(table.name);
    if (!table.area) {
        std::cout << "SQLSEL: table '" << table.name << "' is not open in the current workspace.\n";
        return true;
    }

    const std::vector<std::string> names = split_csv(target.substr(open + 1, close - open - 1));
    if (names.empty()) {
        std::cout << "SQLSEL: INSERT field list is empty.\n";
        return true;
    }
    std::vector<int> fields;
    for (const auto& name : names) {
        if (!is_identifier(name)) {
            std::cout << "SQLSEL: INSERT field '" << name << "' is not an identifier.\n";
            return true;
        }
        const auto index = field_index_ci(*table.area, name);
        if (!index) {
            std::cout << "SQLSEL: INSERT column '" << name << "' was not found.\n";
            return true;
        }
        const int field1 = static_cast<int>(*index) + 1;
        if (std::find(fields.begin(), fields.end(), field1) != fields.end()) {
            std::cout << "SQLSEL: INSERT column '" << name << "' appears more than once.\n";
            return true;
        }
        fields.push_back(field1);
    }
    std::vector<std::string> groups;
    if (!split_value_groups(trim(body.substr(values_pos + 6)), groups, error)) {
        std::cout << "SQLSEL: " << error << ".\n";
        return true;
    }

    bool implicit_scope = false;
    if (!prepare_dml_table(table, implicit_scope, error)) {
        std::cout << "SQLSEL: INSERT refused -- " << error << ".\n";
        return true;
    }
    dottalk::tupleaugment::WorkAreaCursorRestore restore;
    dottalk::TupleRow empty_row;
    std::vector<PendingDmlRow> changes;
    std::uint64_t next_recno = table.area->recCount64() + 1;
    for (const auto& entry : dottalk::table::get_tb_const(cli::slot_of_area(table.area)).changes) {
        if (entry.second.dirty_flags & dottalk::table::CHANGE_INSERT) {
            next_recno = std::max(next_recno, entry.first + 1);
        }
    }
    for (const auto& group : groups) {
        const auto expressions = split_csv(group);
        if (expressions.size() != fields.size()) {
            error = "INSERT field/value counts differ";
            break;
        }
        PendingDmlRow change;
        change.recno = next_recno++;
        change.flags = dottalk::table::CHANGE_INSERT;
        for (std::size_t i = 0; i < fields.size(); ++i) {
            std::string value;
            if (!evaluate_store_expression(
                    expressions[i], empty_row, *table.area, fields[i], value, error)) break;
            change.fields.push_back({fields[i], std::move(value)});
        }
        if (!error.empty()) break;
        changes.push_back(std::move(change));
    }
    if (!error.empty()) {
        if (implicit_scope) rollback_sql_transaction(error.c_str());
        std::cout << "SQLSEL: INSERT refused -- " << error << ".\n";
        return true;
    }
    if (!stage_dml_rows(*table.area, changes, error)) {
        rollback_sql_transaction(error.c_str());
        std::cout << "SQLSEL: INSERT refused -- " << error << ".\n";
        return true;
    }
    return finish_dml_statement(implicit_scope, "INSERT", changes.size());
}

struct UpdatePlan {
    int field1 = 0;
    std::string field_name;
    std::string expression;
};

bool execute_update_statement(const std::string& statement) {
    const std::string body = after_leading_word(statement);
    const std::size_t set_pos = find_kw(body, "SET");
    const std::size_t where_pos = find_kw(body, "WHERE");
    if (set_pos == std::string::npos || where_pos == std::string::npos || where_pos < set_pos) {
        std::cout << "SQLSEL: UPDATE requires SET assignments and an explicit WHERE predicate.\n";
        return true;
    }
    TableRef table;
    std::string error;
    if (!parse_table_ref(trim(body.substr(0, set_pos)), table, error)) {
        std::cout << "SQLSEL: UPDATE " << error << ".\n";
        return true;
    }
    table.area = resolve_sqlsel_area(table.name);
    if (!table.area) {
        std::cout << "SQLSEL: table '" << table.name << "' is not open in the current workspace.\n";
        return true;
    }
    const std::string predicate_text = trim(body.substr(where_pos + 5));
    if (predicate_text.empty()) {
        std::cout << "SQLSEL: UPDATE requires a non-empty WHERE predicate.\n";
        return true;
    }
    auto predicate = dottalk::expr::compile_where(predicate_text);
    if (!predicate) {
        std::cout << "SQLSEL: could not compile UPDATE WHERE: " << predicate.error << ".\n";
        return true;
    }
    std::vector<UpdatePlan> plans;
    for (const auto& assignment : split_csv(
             body.substr(set_pos + 3, where_pos - (set_pos + 3)))) {
        const std::size_t equals = top_level_equal(assignment);
        if (equals == std::string::npos) {
            std::cout << "SQLSEL: UPDATE assignment '" << assignment << "' needs '='.\n";
            return true;
        }
        std::string name = trim(assignment.substr(0, equals));
        const std::size_t dot = name.find('.');
        if (dot != std::string::npos) {
            if (!qualifier_matches(table, name.substr(0, dot))) {
                std::cout << "SQLSEL: UPDATE qualifier '" << name.substr(0, dot)
                          << "' does not name the target table.\n";
                return true;
            }
            name = name.substr(dot + 1);
        }
        const auto index = field_index_ci(*table.area, name);
        if (!index) {
            std::cout << "SQLSEL: UPDATE column '" << name << "' was not found.\n";
            return true;
        }
        const int field1 = static_cast<int>(*index) + 1;
        if (std::any_of(plans.begin(), plans.end(),
                        [field1](const UpdatePlan& p) { return p.field1 == field1; })) {
            std::cout << "SQLSEL: UPDATE column '" << name << "' appears more than once.\n";
            return true;
        }
        const std::string expression = trim(assignment.substr(equals + 1));
        if (expression.empty()) {
            std::cout << "SQLSEL: UPDATE value for '" << name << "' is empty.\n";
            return true;
        }
        plans.push_back({field1, name, expression});
    }
    if (plans.empty()) {
        std::cout << "SQLSEL: UPDATE assignment list is empty.\n";
        return true;
    }

    bool implicit_scope = false;
    if (!prepare_dml_table(table, implicit_scope, error)) {
        std::cout << "SQLSEL: UPDATE refused -- " << error << ".\n";
        return true;
    }
    dottalk::tupleaugment::WorkAreaCursorRestore restore;
    std::vector<dottalk::TupleRow> rows;
    if (!materialize_dml_source(table, rows, error)) {
        if (implicit_scope) rollback_sql_transaction(error.c_str());
        std::cout << "SQLSEL: UPDATE refused -- " << error << ".\n";
        return true;
    }
    std::vector<PendingDmlRow> changes;
    for (const auto& row : rows) {
        const auto verdict = evaluate_tuple_predicate(predicate.program.get(), row);
        if (verdict.state == PredicateState::Error) {
            error = verdict.error;
            break;
        }
        if (verdict.state != PredicateState::True) continue;
        PendingDmlRow change;
        change.recno = row.fragments.empty() ? 0 : row.fragments.front().recno;
        change.flags = dottalk::table::CHANGE_UPDATE;
        for (const auto& plan : plans) {
            std::string value;
            if (!evaluate_store_expression(
                    plan.expression, row, *table.area, plan.field1, value, error)) break;
            change.fields.push_back({plan.field1, std::move(value)});
        }
        if (!error.empty()) break;
        changes.push_back(std::move(change));
    }
    if (!error.empty()) {
        if (implicit_scope) rollback_sql_transaction(error.c_str());
        std::cout << "SQLSEL: UPDATE refused -- " << error << ".\n";
        return true;
    }
    if (!stage_dml_rows(*table.area, changes, error)) {
        rollback_sql_transaction(error.c_str());
        std::cout << "SQLSEL: UPDATE refused -- " << error << ".\n";
        return true;
    }
    return finish_dml_statement(implicit_scope, "UPDATE", changes.size());
}

bool execute_delete_statement(const std::string& statement) {
    const std::string body0 = after_leading_word(statement);
    if (leading_word(body0) != "FROM") {
        std::cout << "SQLSEL: DELETE requires FROM <table> WHERE <predicate>.\n";
        return true;
    }
    const std::string body = after_leading_word(body0);
    const std::size_t where_pos = find_kw(body, "WHERE");
    if (where_pos == std::string::npos) {
        std::cout << "SQLSEL: DELETE without WHERE is refused.\n";
        return true;
    }
    TableRef table;
    std::string error;
    if (!parse_table_ref(trim(body.substr(0, where_pos)), table, error)) {
        std::cout << "SQLSEL: DELETE " << error << ".\n";
        return true;
    }
    table.area = resolve_sqlsel_area(table.name);
    if (!table.area) {
        std::cout << "SQLSEL: table '" << table.name << "' is not open in the current workspace.\n";
        return true;
    }
    const std::string predicate_text = trim(body.substr(where_pos + 5));
    auto predicate = dottalk::expr::compile_where(predicate_text);
    if (!predicate) {
        std::cout << "SQLSEL: could not compile DELETE WHERE: " << predicate.error << ".\n";
        return true;
    }
    bool implicit_scope = false;
    if (!prepare_dml_table(table, implicit_scope, error)) {
        std::cout << "SQLSEL: DELETE refused -- " << error << ".\n";
        return true;
    }
    dottalk::tupleaugment::WorkAreaCursorRestore restore;
    std::vector<dottalk::TupleRow> rows;
    if (!materialize_dml_source(table, rows, error)) {
        if (implicit_scope) rollback_sql_transaction(error.c_str());
        std::cout << "SQLSEL: DELETE refused -- " << error << ".\n";
        return true;
    }
    std::vector<PendingDmlRow> changes;
    for (const auto& row : rows) {
        const auto verdict = evaluate_tuple_predicate(predicate.program.get(), row);
        if (verdict.state == PredicateState::Error) {
            error = verdict.error;
            break;
        }
        if (verdict.state != PredicateState::True) continue;
        changes.push_back({row.fragments.empty() ? 0 : row.fragments.front().recno,
                           dottalk::table::CHANGE_DELETE, {}});
    }
    if (!error.empty()) {
        if (implicit_scope) rollback_sql_transaction(error.c_str());
        std::cout << "SQLSEL: DELETE refused -- " << error << ".\n";
        return true;
    }
    if (!stage_dml_rows(*table.area, changes, error)) {
        rollback_sql_transaction(error.c_str());
        std::cout << "SQLSEL: DELETE refused -- " << error << ".\n";
        return true;
    }
    return finish_dml_statement(implicit_scope, "DELETE", changes.size());
}

bool try_execute_select(const std::string& tail_in) {
    std::vector<std::string> terms;
    std::vector<SetOperation> operations;
    std::string error;
    if (!split_set_expression(trim(tail_in), terms, operations, error)) {
        std::cout << "SQLSEL: " << error << ".\n";
        return true;
    }
    if (operations.empty()) return execute_select_term(tail_in, nullptr);

    for (const std::string& term : terms) {
        if (find_kw(term, "ORDER") != std::string::npos ||
            find_kw(term, "LIMIT") != std::string::npos) {
            std::cout << "SQLSEL: P4.5 set expressions do not accept ORDER BY or LIMIT; "
                         "materialize or filter each source before combining it.\n";
            return true;
        }
    }

    std::vector<QueryResult> results(terms.size());
    for (std::size_t i = 0; i < terms.size(); ++i) {
        if (!execute_select_term(terms[i], &results[i]) || !results[i].ok) return true;
        if (i > 0 && !set_columns_compatible(results[0], results[i], error)) {
            std::cout << "SQLSEL: " << error << ".\n";
            return true;
        }
    }

    // SQL precedence: INTERSECT binds more tightly than UNION and EXCEPT.
    for (std::size_t i = 0; i < operations.size();) {
        if (operations[i] != SetOperation::Intersect) {
            ++i;
            continue;
        }
        const std::size_t left_count = results[i].rows.size();
        const std::size_t right_count = results[i + 1].rows.size();
        results[i] = apply_set_operation(std::move(results[i]), std::move(results[i + 1]),
                                         operations[i]);
        std::cout << "SQLSEL: INTERSECT set operation -- left=" << left_count
                  << ", right=" << right_count << ", output=" << results[i].rows.size()
                  << ".\n";
        results.erase(results.begin() + static_cast<std::ptrdiff_t>(i + 1));
        operations.erase(operations.begin() + static_cast<std::ptrdiff_t>(i));
    }

    QueryResult result = std::move(results.front());
    for (std::size_t i = 0; i < operations.size(); ++i) {
        const std::size_t left_count = result.rows.size();
        const std::size_t right_count = results[i + 1].rows.size();
        result = apply_set_operation(std::move(result), std::move(results[i + 1]), operations[i]);
        std::cout << "SQLSEL: " << set_operation_name(operations[i])
                  << " set operation -- left=" << left_count << ", right=" << right_count
                  << ", output=" << result.rows.size() << ".\n";
    }
    emit_query_result(result);
    return true;
}

bool transaction_active() noexcept {
    return sql_transaction_state().active;
}

bool try_execute_statement(const std::string& statement_in) {
    const std::string statement = statement_without_semicolon(statement_in);
    const std::string verb = leading_word(statement);

    if (verb == "INSERT") return execute_insert_statement(statement);
    if (verb == "UPDATE") return execute_update_statement(statement);
    if (verb == "DELETE") return execute_delete_statement(statement);

    if (verb == "BEGIN") {
        if (!sql_mode()) {
            std::cout << "SQLSEL: BEGIN requires SET MODE SQL so native COMMIT cannot bypass its state.\n";
            return true;
        }
        const std::string tail = after_leading_word(statement);
        if (!tail.empty() && up(tail) != "TRANSACTION") {
            std::cout << "SQLSEL: BEGIN accepts only optional TRANSACTION.\n";
            return true;
        }
        std::string error;
        if (!begin_dml_scope(true, error)) {
            std::cout << "SQLSEL: BEGIN refused -- " << error << ".\n";
            return true;
        }
        std::cout << "SQLSEL: transaction begun; the first DML statement will take its table fence.\n";
        return true;
    }

    if (verb == "COMMIT") {
        if (!after_leading_word(statement).empty()) {
            std::cout << "SQLSEL: COMMIT takes no trailing input.\n";
            return true;
        }
        if (!sql_transaction_state().active) {
            std::cout << "SQLSEL: no SQL transaction is active.\n";
            return true;
        }
        std::string error;
        if (!commit_sql_transaction(error)) {
            std::cout << "SQLSEL: COMMIT failed -- " << error << ".\n";
            return true;
        }
        std::cout << "SQLSEL: transaction committed.\n";
        return true;
    }

    if (verb == "ROLLBACK") {
        if (!after_leading_word(statement).empty()) {
            std::cout << "SQLSEL: ROLLBACK takes no trailing input.\n";
            return true;
        }
        if (!sql_transaction_state().active) {
            std::cout << "SQLSEL: no SQL transaction is active.\n";
            return true;
        }
        rollback_sql_transaction();
        std::cout << "SQLSEL: transaction rolled back.\n";
        return true;
    }

    return try_execute_select(statement_in);
}

} // namespace sqlsel
