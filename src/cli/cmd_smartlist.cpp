// src/cli/cmd_smartlist.cpp
//
// SMARTLIST — LIST-style output honoring current order with classic or AST-based FOR filtering.
//
// Usage:
//   SMARTLIST [ALL | <limit> | DELETED] [DEBUG] [TUPLES] [FOR <pred>]
//
// Notes:
//   • Ordering: respects current INX/CNX/CDX/LMDB (ASC/DESC) like LIST.
//   • Deletion visibility: default hides deleted unless ALL; "DELETED"
//     shows only deleted; "FOR !DELETED" also supported.
//   • Filtering: supports classic FOR <field> <op> <value> and AST-style expressions.
//     SQL-ish input is normalized via sql_to_dottalk_where before compile.
//   • DEBUG: prints a couple of diagnostics.
//

// @dottalk.usage v1
// owner: DOT|SMARTLIST
// command: SMARTLIST
// category: report
// status: supported
// noargs: report
// effect: report
// mutates: cursor
// usage-access: SMARTLIST USAGE
// summary:
//   Filter-aware, order-aware table listing with optional projections, tuple
//   output, debug tracing, deleted-record modes, and predicate filtering.
//
// usage:
//   SMARTLIST
//   SMARTLIST USAGE
//   SMARTLIST <fields>
//   SMARTLIST ALL
//   SMARTLIST <limit>
//   SMARTLIST NEXT <n>
//   SMARTLIST FIRST <n>
//   SMARTLIST DELETED
//   SMARTLIST DEBUG
//   SMARTLIST TUPLES
//   SMARTLIST FOR <pred>
//
// notes:
//   SMARTLIST requires an open table except for SMARTLIST USAGE.
//   SMARTLIST with no arguments preserves existing behavior and prints usage before continuing with default listing.
//   Field projections are comma-separated.
//   ALL removes the output limit.
//   NEXT and FIRST limit scan scope.
//   DELETED selects deleted records.
//   TUPLES emits tuple bridge output.
//   DEBUG emits order/filter diagnostics.
//   FOR applies predicate filtering.
//   SMARTLIST restores the original cursor best-effort after listing.
//   SMARTLIST is read-only for table data.
//
// risk:
//   reads_table_records: yes
//   mutates_cursor: temporary during scan
//   cursor_restore: best effort
//   mutates_table_data: no
//   uses_table_buffer_overlay: when TABLE buffer is available
//
// related:
//   LIST
//   COUNT
//   LOCATE
//   DUMP
//

#include "xbase.hpp"
#include "textio.hpp"
#include "predicates.hpp"
#include "filters/filter_registry.hpp"
#include "cli/order_state.hpp"
#include "cli/order_nav.hpp"
#include "cli/order_iterator.hpp"
#include "cli/smartlist_query.hpp"
#include "cli/smartlist_output.hpp"
#include "cli/table_object.hpp"
#include "cli/table_state.hpp"
#include "tuple_builder.hpp"
#include "value_normalize.hpp"
#include "set_relations.hpp"
#include "../xbase/cursor_hook.hpp"

// Expr engine + helpers
#include "cli/expr/api.hpp"
#include "cli/expr/glue_xbase.hpp"
#include "cli/expr/parse_utils.hpp"
#include "cli/expr/line_parse_utils.hpp"
#include "expr/sql_normalize.hpp"

// std
#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <memory>
#include <set>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

// LMDB (CDX.d pilot)
#include <lmdb.h>

extern "C" xbase::XBaseEngine* shell_engine();

namespace {

enum class DelFilter {
    Any,
    OnlyDeleted,
    OnlyAlive
};

struct Options {
    bool all{false};
    int  limit{20};
    DelFilter del{DelFilter::Any};

    bool haveExpr{false};
    std::string exprRaw;

    bool haveFieldFilter{false};
    std::string fld, op, val;

    bool debug{false};
    bool tuples{false};

    std::vector<int> projection_fields;   // 1-based field numbers; empty means full row
};

struct CursorRestore {
    xbase::DbArea& a;
    int32_t saved_recno{0};
    bool have{false};

    explicit CursorRestore(xbase::DbArea& area) : a(area) {
        try {
            saved_recno = a.recno();
            have = (saved_recno > 0);
        } catch (...) {
            have = false;
        }
    }

    ~CursorRestore() {
        if (!have) return;
        try {
            (void)a.gotoRec(saved_recno);
            (void)a.readCurrent();
        } catch (...) {}

        try { relations_api::refresh_if_enabled(); } catch (...) {}
    }
};

static inline bool is_uint(const std::string& s) {
    if (s.empty()) return false;
    for (unsigned char c : s) if (!std::isdigit(c)) return false;
    return true;
}

static inline std::string trim(std::string s) {
    auto sp = [](unsigned char c){ return c==' '||c=='\t'||c=='\r'||c=='\n'; };
    while (!s.empty() && sp((unsigned char)s.front())) s.erase(s.begin());
    while (!s.empty() && sp((unsigned char)s.back()))  s.pop_back();
    return s;
}

static inline std::string up(std::string s) {
    for (auto& ch : s) ch = (char)std::toupper((unsigned char)ch);
    return s;
}

static inline std::string strip_trailing_punct(std::string s) {
    while (!s.empty() && (s.back() == ',' || s.back() == ';')) s.pop_back();
    return s;
}

static inline bool is_smartlist_option_token(const std::string& tok) {
    if (tok.empty()) return false;
    std::string t = strip_trailing_punct(tok);
    if (is_uint(t)) return true;
    const std::string u = up(t);
    return u == "ALL"
        || u == "DELETED"
        || u == "DEBUG"
        || u == "TUPLES"
        || u == "TUPLE"
        || u == "FOR"
        || u == "NEXT"
        || u == "FIRST";
}


static bool is_smartlist_usage_request(const std::string& raw)
{
    std::string t = up(trim(raw));
    if (t.rfind("SMARTLIST ", 0) == 0) {
        t = up(trim(t.substr(10)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_smartlist_usage()
{
    std::cout
        << "Usage:\n"
        << "  SMARTLIST\n"
        << "  SMARTLIST USAGE\n"
        << "  SMARTLIST <fields>\n"
        << "  SMARTLIST ALL\n"
        << "  SMARTLIST <limit>\n"
        << "  SMARTLIST NEXT <n>\n"
        << "  SMARTLIST FIRST <n>\n"
        << "  SMARTLIST DELETED\n"
        << "  SMARTLIST DEBUG\n"
        << "  SMARTLIST TUPLES\n"
        << "  SMARTLIST FOR <pred>\n";
}

static std::string smartlist_options_tail(std::string raw) {
    raw = trim(std::move(raw));
    if (raw.empty()) return raw;

    std::istringstream scan(raw);
    std::string tok;

    while (true) {
        const std::streampos pos = scan.tellg();
        if (!(scan >> tok)) return std::string{};

        if (is_smartlist_option_token(tok)) {
            scan.clear();
            scan.seekg(pos);
            std::string tail;
            std::getline(scan, tail, '\0');
            return trim(std::move(tail));
        }
    }
}

static std::vector<std::string> split_projection_names(std::string part) {
    std::vector<std::string> out;
    part = trim(strip_line_comments(part));
    if (part.empty()) return out;

    std::string cur;
    for (char ch : part) {
        if (ch == ',') {
            cur = trim(cur);
            if (!cur.empty()) out.push_back(strip_trailing_punct(cur));
            cur.clear();
        } else {
            cur.push_back(ch);
        }
    }
    cur = trim(cur);
    if (!cur.empty()) out.push_back(strip_trailing_punct(cur));

    if (out.size() == 1 && out[0].find(' ') != std::string::npos) {
        std::vector<std::string> ws;
        std::istringstream iss(out[0]);
        std::string t;
        while (iss >> t) ws.push_back(strip_trailing_punct(t));
        out.swap(ws);
    }

    return out;
}

static int field_index_by_name(const xbase::DbArea& a, const std::string& name) {
    const auto& fields = a.fields();
    for (std::size_t i = 0; i < fields.size(); ++i) {
        if (textio::ieq(fields[i].name, name)) return static_cast<int>(i + 1);
    }
    return 0;
}

static std::vector<int> parse_projection_fields(const xbase::DbArea& a, std::string raw) {
    raw = trim(strip_line_comments(std::move(raw)));
    if (raw.empty()) return {};

    std::istringstream scan(raw);
    std::ostringstream prefix;
    std::string tok;
    bool any = false;

    while (scan >> tok) {
        if (is_smartlist_option_token(tok)) break;
        if (any) prefix << ' ';
        prefix << tok;
        any = true;
    }

    std::string part = trim(prefix.str());
    if (part.empty()) return {};

    auto names = split_projection_names(part);
    std::vector<int> fields;
    for (const auto& n0 : names) {
        std::string n = trim(n0);
        if (n.empty()) continue;
        if (n == "*") return {};
        int idx = field_index_by_name(a, n);
        if (idx <= 0) {
            std::cout << "SMARTLIST: unknown projection field '" << n << "'; using full row.\n";
            return {};
        }
        fields.push_back(idx);
    }
    return fields;
}

static int projected_width_for(const xbase::DbArea& a, int field1) {
    const auto& f = a.fields().at(static_cast<std::size_t>(field1 - 1));
    int w = std::max<int>(static_cast<int>(f.name.size()), static_cast<int>(f.length));
    if (f.type == 'C' || f.type == 'M') w = std::min(std::max(w, 8), 32);
    else w = std::min(std::max(w, 8), 18);
    return w;
}

static void print_projection_header(const xbase::DbArea& a,
                                    const std::vector<int>& fields,
                                    int recw) {
    std::cout << std::right << std::setw(recw) << "RECNO" << ' ';
    for (int field1 : fields) {
        const auto& f = a.fields().at(static_cast<std::size_t>(field1 - 1));
        const int w = projected_width_for(a, field1);
        std::cout << std::left << std::setw(w) << f.name << ' ';
    }
    std::cout << "\n\n";
}

static void print_projection_row(xbase::DbArea& a,
                                 const std::vector<int>& fields,
                                 int recw) {
    std::cout << std::right << std::setw(recw) << a.recno() << ' ';
    for (int field1 : fields) {
        const auto& f = a.fields().at(static_cast<std::size_t>(field1 - 1));
        const int w = projected_width_for(a, field1);
        std::string v = trim(a.get(field1));
        if (static_cast<int>(v.size()) > w) v = v.substr(0, static_cast<std::size_t>(w));
        if (f.type == 'N' || f.type == 'I' || f.type == 'Y' || f.type == 'B') {
            std::cout << std::right << std::setw(w) << v << ' ';
        } else {
            std::cout << std::left << std::setw(w) << v << ' ';
        }
    }
    std::cout << "\n";
}


static inline bool contains_bool_words(const std::string& s) {
    const std::string u = up(" " + s + " ");
    return u.find(" AND ") != std::string::npos
        || u.find(" OR ")  != std::string::npos
        || u.find(" NOT ") != std::string::npos;
}

static inline void dbg(bool on, const std::string& msg) {
    if (on) std::cout << "; " << msg << "\n";
}

static int resolve_area_index(xbase::DbArea& a) {
    xbase::XBaseEngine* eng = shell_engine();
    if (!eng) return -1;

    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        try {
            if (&eng->area(i) == &a) return i;
        } catch (...) {
        }
    }

    return -1;
}

static Options parse_opts(std::istringstream& iss) {
    Options o{};
    std::string tok;

    while (true) {
        std::streampos save = iss.tellg();
        if (!(iss >> tok)) break;

        if (textio::ieq(tok, "FOR")) {
            iss.clear();
            iss.seekg(save);
            break;
        }
        if (textio::ieq(tok, "ALL")) {
            o.all = true;
            continue;
        }
        if (textio::ieq(tok, "DELETED")) {
            o.del = DelFilter::OnlyDeleted;
            continue;
        }
        if (textio::ieq(tok, "DEBUG")) {
            o.debug = true;
            continue;
        }
        if (textio::ieq(tok, "TUPLES") || textio::ieq(tok, "TUPLE")) {
            o.tuples = true;
            continue;
        }
        if (textio::ieq(tok, "NEXT") || textio::ieq(tok, "FIRST")) {
            std::string n;
            std::streampos before_n = iss.tellg();
            if ((iss >> n) && is_uint(n)) {
                o.all = false;
                o.limit = std::max(0, std::stoi(n));
                continue;
            }
            iss.clear();
            iss.seekg(before_n);
            continue;
        }
        if (is_uint(tok)) {
            o.limit = std::max(0, std::stoi(tok));
            continue;
        }

        iss.clear();
        iss.seekg(save);
        break;
    }

    {
        std::streampos save = iss.tellg();
        std::string w;
        if (iss >> w && textio::ieq(w, "FOR")) {
            std::string first;
            std::streampos after_for = iss.tellg();

            if (iss >> first) {
                if (textio::ieq(first, "DELETED")) {
                    o.del = DelFilter::OnlyDeleted;
                    return o;
                }
                if ((first.size() == 8 || first.size() == 9) &&
                    (first[0] == '!' || first[0] == '~') &&
                    textio::ieq(first.c_str() + 1, "DELETED")) {
                    o.del = DelFilter::OnlyAlive;
                    return o;
                }

                std::string rest_of_line;
                std::getline(iss, rest_of_line);
                std::string cleaned = trim(strip_line_comments(first + (rest_of_line.empty() ? "" : " " + rest_of_line)));

                {
                    std::istringstream probe(cleaned);
                    std::string fld, op;
                    if (probe >> fld >> op) {
                        std::string rhs;
                        std::getline(probe, rhs);
                        rhs = textio::unquote(trim(rhs));

                        const bool rhs_has_bool = contains_bool_words(rhs);
                        const bool whole_has_bool = contains_bool_words(cleaned);

                        if (!fld.empty() && !op.empty() && !rhs_has_bool && !whole_has_bool) {
                            o.haveFieldFilter = true;
                            o.fld = fld;
                            o.op  = op;
                            o.val = rhs;
                            return o;
                        }
                    }
                }

                if (!cleaned.empty()) {
                    o.haveExpr = true;
                    o.exprRaw = cleaned;
                }
                return o;
            }

            iss.clear();
            iss.seekg(after_for);
        } else {
            iss.clear();
            iss.seekg(save);
        }
    }

    return o;
}

static std::shared_ptr<dottalk::expr::Expr> build_expr_program_from(const std::string& userExpr,
                                                                    bool debug=false) {
    const std::string normalized = sqlnorm::sql_to_dottalk_where(userExpr);
    const std::string cleaned    = strip_line_comments(normalized);

    auto cr = dottalk::expr::compile_where(cleaned);
    if (!cr) {
        auto raw_clean = strip_line_comments(userExpr);
        cr = dottalk::expr::compile_where(raw_clean);
    }
    if (!cr) {
        if (debug) std::cout << "; compile failed — FOR will match no records\n";
        struct AlwaysFalse final : dottalk::expr::Expr {
            bool eval(const dottalk::expr::RecordView&) const override { return false; }
        };
        return std::shared_ptr<dottalk::expr::Expr>(new AlwaysFalse{});
    }

    return std::shared_ptr<dottalk::expr::Expr>(std::move(cr.program));
}

static std::string tuple_safe_value(std::string v) {
    for (char& ch : v) {
        if (ch == '\r' || ch == '\n' || ch == '\t') ch = ' ';
    }
    return v;
}

static bool print_smartlist_tuple_row(xbase::DbArea& area,
                                      int area0,
                                      int32_t recno,
                                      int printed_so_far,
                                      bool debug) {
    dottalk::TupleBuildOptions buildOpt;
    buildOpt.refresh_relations  = true;
    buildOpt.header_area_prefix = false;
    buildOpt.strict_fields      = false;

    std::string spec = "*";
    if (area0 >= 0) spec = "#" + std::to_string(area0) + ".*";

    const auto built = dottalk::build_tuple_from_spec(spec, buildOpt);
    if (!built.ok) {
        if (debug) {
            std::cout << "; TUPLE: build failed for recno " << recno
                      << ": " << built.error << "\n";
        }
        return false;
    }

    const int logical = printed_so_far + 1;
    std::cout << "; TUPLE: " << recno << " | ROW=" << logical;

    const dottalk::TupleRow& row = built.row;
    const std::size_t n = std::min(row.columns.size(), row.values.size());
    for (std::size_t i = 0; i < n; ++i) {
        std::string name = row.columns[i].name.empty() ? row.columns[i].field : row.columns[i].name;
        if (name.empty()) name = "COL" + std::to_string(i + 1);
        std::cout << " | " << name << "=" << tuple_safe_value(row.values[i]);
    }
    std::cout << "\n";
    (void)area;
    return true;
}

} // namespace

void cmd_SMARTLIST(xbase::DbArea& a, std::istringstream& iss) {
    const std::string raw_args = iss.str();
    if (is_smartlist_usage_request(raw_args)) {
        print_smartlist_usage();
        return;
    }

    if (!a.isOpen()) { std::cout << "No table open.\n"; return; }

    CursorRestore __restore(a);

    std::string raw_tail;
    {
        std::ostringstream oss;
        oss << iss.rdbuf();
        raw_tail = oss.str();
        if (trim(raw_tail).empty()) {
            print_smartlist_usage();
        }
    }

    a.top();
    (void)a.readCurrent();

    std::istringstream opt_iss(smartlist_options_tail(raw_tail));
    Options opt = parse_opts(opt_iss);
    opt.projection_fields = parse_projection_fields(a, raw_tail);

    const int32_t total = a.recCount();
    if (total <= 0) { std::cout << "(empty)\n"; return; }

    std::shared_ptr<dottalk::expr::Expr> expr_prog;
    if (opt.haveExpr) {
        const std::string U = up(opt.exprRaw);
        if (U == "DELETED") {
            opt.del = DelFilter::OnlyDeleted;
            opt.haveExpr = false;
        } else if (U == "!DELETED" || U == "~DELETED") {
            opt.del = DelFilter::OnlyAlive;
            opt.haveExpr = false;
        } else {
            dbg(opt.debug, std::string("Expr (raw): ") + opt.exprRaw);
            expr_prog = build_expr_program_from(opt.exprRaw, opt.debug);
            dbg(opt.debug, "Expr mode: AST engine");
        }
    }
    if (opt.haveFieldFilter) {
        dbg(opt.debug, "Expr mode: classic predicate");
    }

    const int recw = cli::smartlist::recno_width(a);
    if (!opt.tuples) {
        if (!opt.projection_fields.empty()) {
            print_projection_header(a, opt.projection_fields, recw);
        } else {
            cli::smartlist::print_header(a, recw);
        }
    } else {
        dbg(opt.debug, "Tuple output: using tuple_builder bridge");
    }

    xbase::XBaseEngine* eng = shell_engine();
    const int area0 = resolve_area_index(a);
    std::unique_ptr<dottalk::table::Table> table_view;

    if (eng && area0 >= 0) {
        try {
            table_view = std::make_unique<dottalk::table::Table>(*eng, area0);
            if (opt.debug && dottalk::table::is_enabled(area0)) {
                dbg(opt.debug, "TABLE BUFFER: SMARTLIST output uses snapshot_view overlay");
            }
        } catch (const std::exception& e) {
            dbg(opt.debug, std::string("TABLE BUFFER: snapshot_view unavailable: ") + e.what());
            table_view.reset();
        } catch (...) {
            dbg(opt.debug, "TABLE BUFFER: snapshot_view unavailable");
            table_view.reset();
        }
    } else {
        dbg(opt.debug, "TABLE BUFFER: engine/area not available; using physical DbArea output");
    }

    cli::smartlist::QuerySpec spec{};
    spec.all = opt.all;
    spec.limit = opt.limit;
    spec.debug = opt.debug;
    spec.haveFieldFilter = opt.haveFieldFilter;
    spec.fld = opt.fld;
    spec.op = opt.op;
    spec.val = opt.val;
    spec.expr_prog = expr_prog;

    switch (opt.del) {
        case DelFilter::OnlyDeleted: spec.del = cli::smartlist::DelFilter::OnlyDeleted; break;
        case DelFilter::OnlyAlive:   spec.del = cli::smartlist::DelFilter::OnlyAlive;   break;
        case DelFilter::Any:
        default:                     spec.del = cli::smartlist::DelFilter::Any;          break;
    }

    auto stats = cli::smartlist::execute_query(
        a,
        spec,
        [&](xbase::DbArea& area, int32_t rn, int printed_so_far) -> bool {
            if (opt.tuples) {
                return print_smartlist_tuple_row(area, area0, rn, printed_so_far, opt.debug);
            }

            if (!opt.projection_fields.empty()) {
                print_projection_row(area, opt.projection_fields, recw);
                return true;
            }

            if (table_view) {
                try {
                    const bool physical_deleted = area.isDeleted();
                    dottalk::table::Row row = table_view->snapshot_view(static_cast<int>(rn));
                    cli::smartlist::print_row(area, row, recw, physical_deleted);
                    return true;
                } catch (const std::exception& e) {
                    dbg(opt.debug, std::string("TABLE BUFFER: snapshot_view failed for recno ")
                                   + std::to_string(rn) + ": " + e.what());
                } catch (...) {
                    dbg(opt.debug, std::string("TABLE BUFFER: snapshot_view failed for recno ")
                                   + std::to_string(rn));
                }
            }

            cli::smartlist::print_row(area, recw);
            return true;
        });

    if (opt.debug) {
        auto backend_name = [&](const cli::OrderIterSpec& os) -> const char* {
            switch (os.backend) {
                case cli::OrderBackend::Natural: return "NATURAL";
                case cli::OrderBackend::Inx:     return "INX";
                case cli::OrderBackend::Cnx:     return "CNX";
                case cli::OrderBackend::Cdx:
                    return (os.cdx_mode == cli::CdxExecMode::Lmdb) ? "CDX/LMDB" : "CDX/FALLBACK";
                case cli::OrderBackend::Isx:     return "ISX";
                case cli::OrderBackend::Csx:     return "CSX";
                default:                         return "?";
            }
        };

        if (stats.iter_used) {
            std::string msg = std::string("ORDER ITER: ")
                            + backend_name(stats.iter_spec)
                            + " path '" + (stats.iter_spec.container_path.empty() ? "(none)" : stats.iter_spec.container_path)
                            + "' tag '" + (stats.iter_spec.tag.empty() ? "(none)" : stats.iter_spec.tag)
                            + "' " + (stats.iter_spec.ascending ? "ASC" : "DESC");
            dbg(opt.debug, msg);
        } else {
            dbg(opt.debug, "ORDER ITER failed: " + stats.iter_err);
            dbg(opt.debug, "Falling back to physical order");
        }
    }

    cli::smartlist::print_footer(opt.all, opt.limit, stats.printed);
}

