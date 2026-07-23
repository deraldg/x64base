// src/cli/cmd_aggs.cpp
//
// Aggregates: AGGS owner/family, plus direct SUM/AVG/MIN/MAX commands.
//
// Key behavior:
//   - If <value_expr> compiles to a numeric program (LitNumber or Arith), use it.
//   - Else, if <value_expr> is a simple identifier matching a field name,
//     read that field directly and parse as double (FoxPro-ish SUM <field>).
//
// Filtering model:
//   - persistent SET FILTER is part of the logical rowset
//   - optional FOR/WHERE predicate is additionally applied
//   - optional DELETED / NOT DELETED / !DELETED suffix
//
// Cursor cohesion:
//   - save/restore recno()
// Relation refresh suppression during full scan:
//   - shell_rel_refresh_push/pop

// @dottalk.usage v1
// owner: DOT|AGGS
// command: AGGS
// category: aggregate
// status: supported
// noargs: usage
// effect: report
// mutates: cursor
// usage-access: AGGS USAGE
// summary:
//   AGGS is the aggregate family/owner for the direct aggregate verbs
//   SUM, AVG, MIN, and MAX.
//
// usage:
//   AGGS USAGE
//   SUM USAGE
//   SUM <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
//   AVG USAGE
//   AVG <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
//   MIN USAGE
//   MIN <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
//   MAX USAGE
//   MAX <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
//
// notes:
//   AGGS with no arguments prints aggregate-family usage.
//   SUM, AVG, MIN, and MAX are the direct aggregate verbs; AGGS owns the aggregate family.
//   Persistent SET FILTER and optional FOR/WHERE predicates both participate in visibility.
//   Cursor position is restored best-effort after the aggregate scan.
//   Aggregate commands report values; they do not mutate table data.
//
// risk:
//   scans_records: yes
//   mutates_cursor: temporary during scan
//   cursor_restore: best effort
//   mutates_table_data: no
//
// related:
//   COUNT
//   WHERE
//   SETFILTER
//

#include "cli/cmd_aggs.hpp"
#include "cli/command_output.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <locale>
#include <memory>
#include <optional>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "cli/expr/api.hpp"         // dottalk::expr::compile_where(...)
#include "cli/expr/ast.hpp"         // Expr, LitNumber, Arith, RecordView
#include "cli/expr/glue_xbase.hpp"  // glue::make_record_view(...)
#include "filters/filter_registry.hpp"
#include "cli/expr/normalize_where.hpp"  // parity with COUNT FOR / SET FILTER

// Must match the linkage used by shell.cpp (see cmd_count.cpp)
extern "C" void shell_rel_refresh_push() noexcept;
extern "C" void shell_rel_refresh_pop() noexcept;

using dottalk::expr::Arith;
using dottalk::expr::Expr;
using dottalk::expr::LitNumber;
using dottalk::expr::RecordView;

namespace {

enum class AggOp { SUM, AVG, MIN, MAX };
enum class DelMode { ALLRECS, ONLY_DELETED, ONLY_NOT_DELETED };

static inline bool is_ws(unsigned char c) { return std::isspace(c) != 0; }

static inline std::string ltrim(std::string s) {
    size_t i = 0;
    while (i < s.size() && is_ws((unsigned char)s[i])) ++i;
    if (i) s.erase(0, i);
    return s;
}

static inline std::string rtrim(std::string s) {
    while (!s.empty() && is_ws((unsigned char)s.back())) s.pop_back();
    return s;
}

static inline std::string trim(std::string s) {
    return rtrim(ltrim(std::move(s)));
}

static inline std::string upcopy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return (char)std::toupper(c); });
    return s;
}

static void print_aggs_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::AggsFamilyTitle);
    cli::cmdout::print_line("");
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalUsageTitle);
    cli::cmdout::print_line("  AGGS USAGE");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("  AGGS SUM USAGE");
    cli::cmdout::print_line("  AGGS SUM <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("  AGGS AVG USAGE");
    cli::cmdout::print_line("  AGGS AVG <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("  AGGS MIN USAGE");
    cli::cmdout::print_line("  AGGS MIN <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("  AGGS MAX USAGE");
    cli::cmdout::print_line("  AGGS MAX <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
    cli::cmdout::print_line("");
    cli::cmdout::print_message(dottalk::helpdata::MessageId::AggsDirectVerbsTitle);
    cli::cmdout::print_line("  SUM <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
    cli::cmdout::print_line("  AVG <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
    cli::cmdout::print_line("  MIN <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
    cli::cmdout::print_line("  MAX <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
    cli::cmdout::print_line("");
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalExamplesTitle);
    cli::cmdout::print_line("  AGGS SUM GPA");
    cli::cmdout::print_line("  AGGS AVG GPA FOR GPA >= 3.0");
    cli::cmdout::print_line("  AGGS MIN GPA WHERE MAJOR = \"CSCI\"");
    cli::cmdout::print_line("  AGGS MAX GPA NOT DELETED");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("  SUM GPA");
    cli::cmdout::print_line("  AVG GPA FOR GPA >= 3.0");
    cli::cmdout::print_line("  MIN GPA WHERE MAJOR = \"CSCI\"");
    cli::cmdout::print_line("  MAX GPA NOT DELETED");
    cli::cmdout::print_line("");
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalNotesTitle);
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AggsOwnerNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AggsDirectAliasNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AggsForWhereAcceptedNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AggsDeletedOnlyNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AggsNotDeletedOnlyNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AggsCursorRestoreNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AggsReadOnlyNote));
}

static bool is_usage_word(const std::string& s)
{
    const std::string u = upcopy(trim(s));
    return u == "USAGE" || u == "HELP" || u == "?";
}

static void print_agg_usage(const char* opname)
{
    std::string verb = opname ? trim(std::string(opname)) : std::string("SUM");
    verb = upcopy(verb);

    const std::string prefix = "AGGS ";
    if (verb.rfind(prefix, 0) == 0) {
        verb = trim(verb.substr(prefix.size()));
        verb = upcopy(verb);
    }

    if (verb != "SUM" && verb != "AVG" && verb != "MIN" && verb != "MAX") {
        verb = "SUM";
    }

    const std::string owner = std::string("AGGS ") + verb;

    cli::cmdout::print_line(owner);
    cli::cmdout::print_line("");
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalUsageTitle);
    cli::cmdout::print_line("  " + owner + " USAGE");
    cli::cmdout::print_line("  " + owner + " <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
    cli::cmdout::print_line("");
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalExamplesTitle);
    cli::cmdout::print_line("  " + owner + " GPA");
    cli::cmdout::print_line("  " + owner + " GPA FOR GPA >= 3.0");
    cli::cmdout::print_line("  " + owner + " GPA WHERE MAJOR = \"CSCI\"");
    cli::cmdout::print_line("  " + owner + " GPA NOT DELETED");
    cli::cmdout::print_line("");
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalDirectAliasTitle);
    cli::cmdout::print_line("  " + verb + " <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
    cli::cmdout::print_line("");
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalNotesTitle);
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AggUsageOwnerNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(
        dottalk::helpdata::MessageId::AggUsageDirectVerbNote,
        {{"verb", verb}}));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AggUsageReadOnlyNote));
}

// Strip inline comments (// or &&) outside quotes.
static std::string strip_line_comments(const std::string& in) {
    std::string out;
    out.reserve(in.size());
    bool in_s = false;
    bool in_d = false;

    for (size_t i = 0; i < in.size(); ++i) {
        char c = in[i];
        char n = (i + 1 < in.size() ? in[i + 1] : '\0');

        if (!in_s && !in_d) {
            if (c == '/' && n == '/') break;
            if (c == '&' && n == '&') break;
        }

        if (c == '"' && !in_s) {
            in_d = !in_d;
            out.push_back(c);
            continue;
        }

        if (c == '\'' && !in_d) {
            in_s = !in_s;
            out.push_back(c);
            continue;
        }

        out.push_back(c);
    }

    return trim(out);
}

static bool boundary_before(const std::string& s, size_t pos) {
    if (pos == 0) return true;
    return is_ws((unsigned char)s[pos - 1]);
}

static bool boundary_after(const std::string& s, size_t pos_end) {
    if (pos_end >= s.size()) return true;
    return is_ws((unsigned char)s[pos_end]);
}

struct KwHit {
    size_t pos;
    std::string kw;
};

// Find first top-level FOR/WHERE (not in quotes, paren depth 0).
static std::optional<KwHit> find_top_level_for_where(const std::string& s) {
    bool in_s = false;
    bool in_d = false;
    int depth = 0;

    auto match_kw = [&](size_t i, const char* kw) -> bool {
        const size_t n = std::char_traits<char>::length(kw);
        if (i + n > s.size()) return false;
        if (!boundary_before(s, i)) return false;

        for (size_t k = 0; k < n; ++k) {
            if ((char)std::toupper((unsigned char)s[i + k]) != kw[k]) return false;
        }

        if (!boundary_after(s, i + n)) return false;
        return true;
    };

    for (size_t i = 0; i < s.size(); ++i) {
        char c = s[i];

        if (c == '"' && !in_s) {
            in_d = !in_d;
            continue;
        }

        if (c == '\'' && !in_d) {
            in_s = !in_s;
            continue;
        }

        if (in_s || in_d) continue;

        if (c == '(') {
            ++depth;
            continue;
        }

        if (c == ')') {
            if (depth > 0) --depth;
            continue;
        }

        if (depth != 0) continue;

        if (match_kw(i, "FOR")) return KwHit{i, "FOR"};
        if (match_kw(i, "WHERE")) return KwHit{i, "WHERE"};
    }

    return std::nullopt;
}

// Suffix deleted-mode parser (suffix token/phrase only)
static void extract_deleted_suffix(std::string& s, DelMode& mode_out) {
    mode_out = DelMode::ALLRECS;
    s = trim(std::move(s));
    if (s.empty()) return;

    const std::string U = upcopy(s);

    auto ends_with_phrase = [&](const char* phrase) -> std::optional<size_t> {
        const size_t n = std::char_traits<char>::length(phrase);
        if (U.size() < n) return std::nullopt;

        const size_t start = U.size() - n;
        for (size_t i = 0; i < n; ++i) {
            if (U[start + i] != phrase[i]) return std::nullopt;
        }

        if (!boundary_before(U, start)) return std::nullopt;
        return start;
    };

    if (auto p = ends_with_phrase("NOT DELETED")) {
        mode_out = DelMode::ONLY_NOT_DELETED;
        s = trim(s.substr(0, *p));
        return;
    }

    if (auto p = ends_with_phrase("!DELETED")) {
        mode_out = DelMode::ONLY_NOT_DELETED;
        s = trim(s.substr(0, *p));
        return;
    }

    if (auto p = ends_with_phrase("! DELETED")) {
        mode_out = DelMode::ONLY_NOT_DELETED;
        s = trim(s.substr(0, *p));
        return;
    }

    if (auto p = ends_with_phrase("DELETED")) {
        mode_out = DelMode::ONLY_DELETED;
        s = trim(s.substr(0, *p));
        return;
    }
}

struct AggSpec {
    std::string value_expr; // required
    std::string pred_expr;  // optional
    bool has_pred = false;
    DelMode del_mode = DelMode::ALLRECS;
};

static bool parse_agg_spec(const std::string& raw_tail, AggSpec& out, std::string& err) {
    out = AggSpec{};
    err.clear();

    std::string s = strip_line_comments(raw_tail);
    s = trim(std::move(s));

    if (s.empty()) {
        err = "missing <value_expr>";
        return false;
    }

    extract_deleted_suffix(s, out.del_mode);

    if (s.empty()) {
        err = "missing <value_expr>";
        return false;
    }

    if (auto hit = find_top_level_for_where(s)) {
        const size_t kw_pos = hit->pos;
        const size_t kw_len = hit->kw.size();

        out.value_expr = trim(s.substr(0, kw_pos));
        out.pred_expr = trim(s.substr(kw_pos + kw_len));

        if (out.value_expr.empty()) {
            err = "missing <value_expr> before FOR/WHERE";
            return false;
        }

        if (out.pred_expr.empty()) {
            err = "missing predicate after FOR/WHERE";
            return false;
        }

        out.has_pred = true;
        return true;
    }

    out.value_expr = s;
    out.has_pred = false;
    return true;
}

// Normalize the aggregate FOR/WHERE predicate's unquoted RHS barewords to string
// literals, exactly as COUNT FOR / LIST FOR / SET FILTER do -- so
// `SUM GPA FOR MAJOR = CSCI` matches `COUNT FOR MAJOR = CSCI` (CSCI is the string
// "CSCI", not an undefined identifier that matches nothing). Function predicates
// (parens) are left untouched, and numeric/quoted RHS pass through unchanged.
static void normalize_agg_predicate(xbase::DbArea& area, AggSpec& spec) {
    if (!spec.has_pred || spec.pred_expr.empty()) return;
    if (spec.pred_expr.find('(') != std::string::npos &&
        spec.pred_expr.find(')') != std::string::npos) return;
    spec.pred_expr = normalize_unquoted_rhs_literals(area, spec.pred_expr);
}

static bool passes_deleted_mode(xbase::DbArea& area, DelMode m) {
    if (m == DelMode::ALLRECS) return true;

    const bool del = area.isDeleted();

    if (m == DelMode::ONLY_DELETED) return del;
    if (m == DelMode::ONLY_NOT_DELETED) return !del;

    return true;
}

// case-insensitive field lookup -> 1-based index
static int field_index_ci(const xbase::DbArea& A, const std::string& name) {
    std::string want = upcopy(trim(name));
    if (want.empty()) return -1;

    try {
        const auto defs = A.fields();
        for (size_t i = 0; i < defs.size(); ++i) {
            if (upcopy(defs[i].name) == want) return (int)i + 1;
        }
    } catch (...) {
        return -1;
    }

    return -1;
}

static bool is_simple_ident(const std::string& s) {
    std::string t = trim(s);
    if (t.empty()) return false;

    for (char c : t) {
        if (std::isalnum((unsigned char)c) || c == '_') continue;
        return false;
    }

    return true;
}

static bool try_parse_double(std::string s, double& out) {
    s = trim(std::move(s));
    if (s.empty()) return false;

    const char* p = s.c_str();
    char* end = nullptr;

    double v = std::strtod(p, &end);
    if (end == p) return false;

    while (*end && std::isspace((unsigned char)*end)) ++end;
    if (*end != '\0') return false;

    out = v;
    return std::isfinite(out);
}

struct ValuePlan {
    enum Mode { COMPILED_NUMERIC, DIRECT_FIELD, INVALID } mode{INVALID};

    std::string src;
    std::unique_ptr<Expr> prog_owner;
    const Expr* prog = nullptr;
    int field_idx = -1;
    std::string err;
};

static ValuePlan build_value_plan(xbase::DbArea& area, const std::string& value_expr) {
    ValuePlan vp;
    vp.src = trim(value_expr);

    auto cr = dottalk::expr::compile_where(vp.src);
    if (!cr) {
        vp.mode = ValuePlan::INVALID;
        vp.err = cr.error;
        return vp;
    }

    // Numeric program?
    const Expr* p = cr.program.get();
    if (dynamic_cast<const LitNumber*>(p) != nullptr ||
        dynamic_cast<const Arith*>(p) != nullptr) {
        vp.mode = ValuePlan::COMPILED_NUMERIC;
        vp.prog_owner = std::move(cr.program);
        vp.prog = vp.prog_owner.get();
        return vp;
    }

    // Otherwise, treat bare identifier as "field" (Fox SUM <field>)
    if (is_simple_ident(vp.src)) {
        int idx = field_index_ci(area, vp.src);
        if (idx > 0) {
            vp.mode = ValuePlan::DIRECT_FIELD;
            vp.field_idx = idx;
            return vp;
        }
    }

    // Not numeric and not a simple field
    vp.mode = ValuePlan::INVALID;
    vp.err = "value expression is not numeric (try: <field> + 0)";
    return vp;
}

// raw: when true the caller advanced the row with readCurrentRaw() (selective
// decode, scan-evaluator lane M4), so the compiled-numeric path uses the raw
// record view (rv is make_record_view_raw) and the direct-field path decodes
// straight from the record buffer instead of the eager _fd cache.
static bool eval_value_plan(ValuePlan& vp, xbase::DbArea& area, const RecordView& rv, double& out,
                            bool raw = false) {
    if (vp.mode == ValuePlan::COMPILED_NUMERIC) {
        if (auto ln = dynamic_cast<const LitNumber*>(vp.prog)) {
            out = ln->v;
            return std::isfinite(out);
        }

        if (auto ar = dynamic_cast<const Arith*>(vp.prog)) {
            try {
                out = ar->evalNumber(rv);
                return std::isfinite(out);
            } catch (...) {
                return false;
            }
        }

        return false;
    }

    if (vp.mode == ValuePlan::DIRECT_FIELD) {
        try {
            if (raw) {
                double d = 0.0;
                if (area.fieldNumFromBuffer(vp.field_idx, d)) {   // N/F fast path, no alloc
                    out = d;
                    return std::isfinite(out);
                }
                return try_parse_double(area.decodeFieldFromBuffer(vp.field_idx), out);
            }
            std::string s = area.get(vp.field_idx); // 1-based
            return try_parse_double(std::move(s), out);
        } catch (...) {
            return false;
        }
    }

    return false;
}

static std::shared_ptr<Expr> build_predicate_ast(const AggSpec& spec, std::string& err) {
    err.clear();

    if (!spec.has_pred || spec.pred_expr.empty()) {
        return nullptr;
    }

    auto cr = dottalk::expr::compile_where(spec.pred_expr);
    if (!cr) {
        err = cr.error;
        return nullptr;
    }

    return std::shared_ptr<Expr>(std::move(cr.program));
}

static std::string format_number_classic(double v) {
    std::ostringstream oss;
    oss.imbue(std::locale::classic());
    oss << v;
    return oss.str();
}

static void run_agg(AggOp op, const char* opname, xbase::DbArea& area, std::istringstream& args) {
    std::string tail;
    std::getline(args, tail);

    if (is_usage_word(tail)) {
        print_agg_usage(opname);
        return;
    }

    AggSpec spec;
    std::string perr;

    if (!parse_agg_spec(tail, spec, perr)) {
        cli::cmdout::print_line(
            std::string(opname) + " " +
            cli::cmdout::message_text(dottalk::helpdata::MessageId::AggUsageHeading));
        cli::cmdout::print_line(
            " " + std::string(opname) +
            " <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
        return;
    }

    if (!area.isOpen()) {
        if (op == AggOp::SUM) {
            cli::cmdout::print_line("0");
        } else {
            cli::cmdout::print_line("NULL");
        }
        return;
    }

    ValuePlan vp = build_value_plan(area, spec.value_expr);
    if (vp.mode == ValuePlan::INVALID) {
        cli::cmdout::print_line(
            std::string(opname) + " " +
            cli::cmdout::message_text(
                dottalk::helpdata::MessageId::AggErrorDetail,
                {{"detail", vp.err}}));
        return;
    }

    normalize_agg_predicate(area, spec);

    std::string ferr;
    std::shared_ptr<Expr> pred_ast = build_predicate_ast(spec, ferr);
    if (spec.has_pred && !pred_ast) {
        cli::cmdout::print_line(
            std::string(opname) + " " +
            cli::cmdout::message_text(
                dottalk::helpdata::MessageId::AggErrorDetail,
                {{"detail", ferr}}));
        return;
    }

    const int total = (int)area.recCount();
    if (total <= 0) {
        if (op == AggOp::SUM) {
            cli::cmdout::print_line("0");
        } else {
            cli::cmdout::print_line("NULL");
        }
        return;
    }

    const int saved = area.recno();

    // M4 selective decode: when there is no FOR/WHERE predicate and no persistent
    // SET FILTER, only the value expression's field(s) need decoding — advance
    // rows with readCurrentRaw() over the raw record view. Any predicate/filter
    // needs the fully decoded record (filter::visible), so fall back there.
    const bool use_raw = !spec.has_pred && !filter::has_active_filter(&area);
    RecordView rv = use_raw ? dottalk::expr::glue::make_record_view_raw(area)
                            : dottalk::expr::glue::make_record_view(area);

    shell_rel_refresh_push();

    double sum = 0.0;
    uint64_t n = 0;

    bool have_best = false;
    double best = 0.0;

    for (int r = 1; r <= total; ++r) {
        if (!area.gotoRec(r)) continue;
        if (use_raw) {
            if (!area.readCurrentRaw()) continue;
        } else {
            if (!area.readCurrent()) continue;
        }

        if (!passes_deleted_mode(area, spec.del_mode)) continue;

        // Persistent SET FILTER + optional command FOR/WHERE together define visibility.
        if (!filter::visible(&area, pred_ast)) continue;

        double v = 0.0;
        if (!eval_value_plan(vp, area, rv, v, use_raw)) continue;

        if (op == AggOp::SUM || op == AggOp::AVG) {
            sum += v;
            ++n;
            continue;
        }

        if (!have_best) {
            best = v;
            have_best = true;
        } else {
            if (op == AggOp::MIN) {
                if (v < best) best = v;
            } else {
                if (v > best) best = v;
            }
        }
    }

    shell_rel_refresh_pop();

    if (saved >= 1 && saved <= total) {
        (void)area.gotoRec(saved);
        (void)area.readCurrent();
    }

    if (op == AggOp::SUM) {
        cli::cmdout::print_line(format_number_classic(sum));
        return;
    }

    if (op == AggOp::AVG) {
        if (n == 0) {
            cli::cmdout::print_line("NULL");
        } else {
            cli::cmdout::print_line(format_number_classic(sum / (double)n));
        }
        return;
    }

    if (!have_best) {
        cli::cmdout::print_line("NULL");
    } else {
        cli::cmdout::print_line(format_number_classic(best));
    }
}

// Single-pass multi-aggregate: COUNT, SUM, AVG, MIN, MAX over the visible set in
// ONE scan (vs four separate full scans). Reuses the same spec parse, value plan,
// predicate, deleted-mode, and visibility gate as run_agg so results are identical.
static void run_agg_all(xbase::DbArea& area, std::istringstream& args) {
    std::string tail;
    std::getline(args, tail);

    if (is_usage_word(tail)) {
        print_aggs_usage();
        return;
    }

    AggSpec spec;
    std::string perr;
    if (!parse_agg_spec(tail, spec, perr)) {
        cli::cmdout::print_line(
            "AGGS " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AggUsageHeading));
        cli::cmdout::print_line(
            " AGGS ALL <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]");
        return;
    }

    if (!area.isOpen()) {
        cli::cmdout::print_line("COUNT=0 SUM=0 AVG=NULL MIN=NULL MAX=NULL");
        return;
    }

    ValuePlan vp = build_value_plan(area, spec.value_expr);
    if (vp.mode == ValuePlan::INVALID) {
        cli::cmdout::print_line(
            "AGGS " + cli::cmdout::message_text(
                dottalk::helpdata::MessageId::AggErrorDetail, {{"detail", vp.err}}));
        return;
    }

    normalize_agg_predicate(area, spec);

    std::string ferr;
    std::shared_ptr<Expr> pred_ast = build_predicate_ast(spec, ferr);
    if (spec.has_pred && !pred_ast) {
        cli::cmdout::print_line(
            "AGGS " + cli::cmdout::message_text(
                dottalk::helpdata::MessageId::AggErrorDetail, {{"detail", ferr}}));
        return;
    }

    const int total = (int)area.recCount();
    if (total <= 0) {
        cli::cmdout::print_line("COUNT=0 SUM=0 AVG=NULL MIN=NULL MAX=NULL");
        return;
    }

    const int saved = area.recno();

    // M4 selective decode (same gating as the single-aggregate path).
    const bool use_raw = !spec.has_pred && !filter::has_active_filter(&area);
    RecordView rv = use_raw ? dottalk::expr::glue::make_record_view_raw(area)
                            : dottalk::expr::glue::make_record_view(area);

    shell_rel_refresh_push();

    double sum = 0.0;
    uint64_t n = 0;
    bool have_best = false;
    double vmin = 0.0, vmax = 0.0;

    for (int r = 1; r <= total; ++r) {
        if (!area.gotoRec(r)) continue;
        if (use_raw) {
            if (!area.readCurrentRaw()) continue;
        } else {
            if (!area.readCurrent()) continue;
        }
        if (!passes_deleted_mode(area, spec.del_mode)) continue;
        if (!filter::visible(&area, pred_ast)) continue;

        double v = 0.0;
        if (!eval_value_plan(vp, area, rv, v, use_raw)) continue;

        sum += v;
        ++n;
        if (!have_best) { vmin = vmax = v; have_best = true; }
        else { if (v < vmin) vmin = v; if (v > vmax) vmax = v; }
    }

    shell_rel_refresh_pop();

    if (saved >= 1 && saved <= total) {
        (void)area.gotoRec(saved);
        (void)area.readCurrent();
    }

    std::string out = "COUNT=" + std::to_string(n)
        + " SUM=" + format_number_classic(sum)
        + " AVG=" + (n == 0 ? std::string("NULL") : format_number_classic(sum / (double)n))
        + " MIN=" + (have_best ? format_number_classic(vmin) : std::string("NULL"))
        + " MAX=" + (have_best ? format_number_classic(vmax) : std::string("NULL"));
    cli::cmdout::print_line(out);
}

} // namespace

// @dottalk.usage v1
// owner: DOT|SUM
// command: SUM
// category: aggregate
// status: supported
// noargs: usage
// effect: report
// mutates: cursor-temporarily
// usage-access: SUM USAGE
// summary:
//   Sum a numeric expression over the visible record set.
// usage:
//   SUM USAGE
//   SUM <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
// notes:
//   Cursor position is restored best-effort; table data is not mutated.
// related:
//   AGGS, AVG, MIN, MAX
//
void cmd_SUM(xbase::DbArea& area, std::istringstream& args) {
    run_agg(AggOp::SUM, "SUM", area, args);
}

// @dottalk.usage v1
// owner: DOT|AVG
// command: AVG
// aliases: AVERAGE
// category: aggregate
// status: supported
// noargs: usage
// effect: report
// mutates: cursor-temporarily
// usage-access: AVG USAGE; AVERAGE USAGE
// summary:
//   Average a numeric expression over the visible record set.
// usage:
//   AVG USAGE
//   AVG <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
//   AVERAGE <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
// notes:
//   AVERAGE is the registered long-form alias of AVG. Cursor position is restored best-effort.
// related:
//   AGGS, SUM, MIN, MAX
//
void cmd_AVG(xbase::DbArea& area, std::istringstream& args) {
    run_agg(AggOp::AVG, "AVG", area, args);
}

// @dottalk.usage v1
// owner: DOT|MIN
// command: MIN
// category: aggregate
// status: supported
// noargs: usage
// effect: report
// mutates: cursor-temporarily
// usage-access: MIN USAGE
// summary:
//   Report the minimum numeric value over the visible record set.
// usage:
//   MIN USAGE
//   MIN <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
// notes:
//   Cursor position is restored best-effort; table data is not mutated.
// related:
//   AGGS, SUM, AVG, MAX
//
void cmd_MIN(xbase::DbArea& area, std::istringstream& args) {
    run_agg(AggOp::MIN, "MIN", area, args);
}

// @dottalk.usage v1
// owner: DOT|MAX
// command: MAX
// category: aggregate
// status: supported
// noargs: usage
// effect: report
// mutates: cursor-temporarily
// usage-access: MAX USAGE
// summary:
//   Report the maximum numeric value over the visible record set.
// usage:
//   MAX USAGE
//   MAX <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
// notes:
//   Cursor position is restored best-effort; table data is not mutated.
// related:
//   AGGS, SUM, AVG, MIN
//
void cmd_MAX(xbase::DbArea& area, std::istringstream& args) {
    run_agg(AggOp::MAX, "MAX", area, args);
}

void cmd_AGGS(xbase::DbArea& area, std::istringstream& args) {
    std::string op;
    args >> op;
    op = upcopy(op);

    if (op.empty() || op == "USAGE" || op == "HELP" || op == "?") {
        print_aggs_usage();
        return;
    }

    // Single-pass multi-aggregate: COUNT/SUM/AVG/MIN/MAX in one scan.
    if (op == "ALL" || op == "STATS") {
        run_agg_all(area, args);
        return;
    }

    // Compatibility/family dispatch. AGGS owns the family, but the direct
    // executable aggregate verbs are SUM, AVG, MIN, and MAX.
    if (op == "SUM") {
        run_agg(AggOp::SUM, "SUM", area, args);
        return;
    }

    if (op == "AVG" || op == "AVERAGE") {
        run_agg(AggOp::AVG, "AVG", area, args);
        return;
    }

    if (op == "MIN") {
        run_agg(AggOp::MIN, "MIN", area, args);
        return;
    }

    if (op == "MAX") {
        run_agg(AggOp::MAX, "MAX", area, args);
        return;
    }

    print_aggs_usage();
}
