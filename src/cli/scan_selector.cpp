#include "cli/scan_selector.hpp"

#include "xbase.hpp"
#include "filters/filter_registry.hpp"
#include "cli/order_state.hpp"
#include "cli/order_iterator.hpp"
#include "cli/expr/value_eval.hpp"

#include <algorithm>
#include <cctype>
#include <memory>
#include <string>
#include <vector>

namespace cli::scan {

namespace {

// --------------------------------------------------
// local string helpers
// --------------------------------------------------
static inline void ltrim_inplace(std::string& s){
    size_t i = 0;
    while (i < s.size() && std::isspace((unsigned char)s[i])) ++i;
    if (i) s.erase(0, i);
}

static inline void rtrim_inplace(std::string& s){
    while (!s.empty() && std::isspace((unsigned char)s.back())) s.pop_back();
}

static inline std::string trim_copy(std::string s){
    rtrim_inplace(s);
    ltrim_inplace(s);
    return s;
}

// Conservative inline comment stripper
static inline std::string strip_inline_comments(std::string s){
    const auto pos_dblamp = s.find("&&");
    const auto pos_slash  = s.find(" //");

    size_t cut = std::string::npos;
    if (pos_dblamp != std::string::npos) cut = pos_dblamp;
    if (pos_slash  != std::string::npos) cut = (cut == std::string::npos ? pos_slash : std::min(cut, pos_slash));

    if (cut != std::string::npos) s.erase(cut);
    return trim_copy(s);
}

static std::string normalize_expr(std::string expr)
{
    expr = trim_copy(std::move(expr));
    expr = strip_inline_comments(std::move(expr));
    expr = trim_copy(std::move(expr));
    return expr;
}

// --------------------------------------------------
// shared row visibility (filter + deleted policy)
// --------------------------------------------------
static bool row_visible(xbase::DbArea& area,
                        DeletedMode dmode)
{
    if (!filter::visible(&area, nullptr))
        return false;

    if (dmode == DeletedMode::OnlyDeleted)
        return area.isDeleted();

    if (dmode == DeletedMode::OnlyAlive)
        return !area.isDeleted();

    return true;
}

// --------------------------------------------------
// collect base recnos (ordered or physical)
// --------------------------------------------------
static std::vector<uint64_t> collect_base_recnos(xbase::DbArea& area,
                                                 bool ordered)
{
    std::vector<uint64_t> recnos;

    if (ordered && orderstate::hasOrder(area)) {
        cli::OrderIterSpec spec{};
        std::string err;

        if (cli::order_collect_recnos_asc(area, recnos, &spec, &err))
            return recnos;
    }

    const int total = area.recCount();
    for (int i = 1; i <= total; ++i)
        recnos.push_back((uint64_t)i);

    return recnos;
}

// --------------------------------------------------
// apply scan mode
// --------------------------------------------------
static std::vector<uint64_t> apply_scope(xbase::DbArea& area,
                                         const std::vector<uint64_t>& base,
                                         const SelectionSpec& spec)
{
    std::vector<uint64_t> out;

    if (spec.scan_mode == ScanMode::All)
        return base;

    if (spec.scan_mode == ScanMode::Current) {
        const int rn = area.recno();
        if (rn >= 1) out.push_back((uint64_t)rn);
        return out;
    }

    if (spec.scan_mode == ScanMode::Rest) {
        const int start = area.recno();
        for (uint64_t rn : base) {
            if ((int)rn >= start)
                out.push_back(rn);
        }
        return out;
    }

    if (spec.scan_mode == ScanMode::NextN) {
        int count = 0;
        const int start = area.recno();

        for (uint64_t rn : base) {
            if ((int)rn < start) continue;
            if (count++ >= spec.next_n) break;
            out.push_back(rn);
        }
        return out;
    }

    return base;
}

} // namespace

bool match_current(xbase::DbArea& area,
                   const SelectionSpec& spec)
{
    if (!area.readCurrent()) return false;

    if (!row_visible(area, spec.deleted_mode))
        return false;

    if (spec.use_expr && !spec.expr.empty()) {
        const std::string expr_norm = normalize_expr(spec.expr);
        if (!expr_norm.empty()) {
            bool ok = false;
            try {
                bool result = false;
                std::string err;
                ok = dottalk::expr::eval_bool(area, expr_norm, result, &err) && result;
            } catch (...) {
                ok = false;
            }
            if (!ok) return false;
        }
    }

    return true;
}

// --------------------------------------------------
// main selector
// --------------------------------------------------
SelectionResult collect_selected_recnos(xbase::DbArea& area,
                                        const SelectionSpec& spec)
{
    SelectionResult res;

    // Explicit DELETED scans must inspect the physical table.
    // Active indexes/order vectors normally contain only live records, so using
    // the ordered snapshot for DeletedMode::OnlyDeleted makes deleted records
    // invisible to COUNT DELETED and other selector-backed commands.
    const bool use_ordered_snapshot =
        spec.ordered_snapshot && (spec.deleted_mode != DeletedMode::OnlyDeleted);

    auto base = collect_base_recnos(area, use_ordered_snapshot);
    auto scoped = apply_scope(area, base, spec);

    // Scan-evaluator lane M1: compile the FOR/WHERE predicate ONCE for the whole
    // scan instead of re-parsing/re-compiling it per row (the dominant scan
    // cost). compile_bool_predicate falls back to per-row eval_bool for anything
    // not safely hoistable, so this selection is identical to the previous
    // per-row match_current() path — which is retained for LOCATE/CONTINUE.
    std::shared_ptr<dottalk::expr::CompiledPredicate> compiled;
    const bool have_expr = spec.use_expr && !spec.expr.empty();
    if (have_expr) {
        const std::string expr_norm = normalize_expr(spec.expr);
        if (!expr_norm.empty()) {
            // M2 selective decode: allow the readCurrentRaw() fast path only
            // when no persistent SET FILTER is active — a filter evaluates its
            // own predicate against the fully decoded record, which the raw path
            // does not populate.
            const bool allow_raw = !filter::has_active_filter(&area);
            compiled = dottalk::expr::compile_bool_predicate(area, expr_norm, allow_raw);
        }
    }

    // When the predicate was bound to the selective-decode view, advance rows
    // with readCurrentRaw() (decode only the fields the predicate reads);
    // otherwise fall back to the full per-row decode.
    const bool use_raw =
        compiled && dottalk::expr::compiled_predicate_uses_raw(*compiled);

    for (uint64_t rn : scoped) {
        if (!area.gotoRec((int32_t)rn)) continue;
        if (use_raw) {
            if (!area.readCurrentRaw()) continue;
        } else {
            if (!area.readCurrent()) continue;
        }
        if (!row_visible(area, spec.deleted_mode)) continue;

        if (compiled) {
            bool ok = false;
            try {
                bool result = false;
                std::string err;
                ok = dottalk::expr::eval_bool_compiled(*compiled, area, result, &err) && result;
            } catch (...) {
                ok = false;
            }
            if (!ok) continue;
        }

        res.recnos.push_back(rn);
    }

    // The raw fast path leaves the area's decoded-field cache (_fd) stale at the
    // final scanned position. Restore the full-decode invariant so any caller
    // that reads the current record right after selection sees consistent state
    // (matches the previous per-row readCurrent() behavior). One record, cheap.
    if (use_raw) {
        (void)area.readCurrent();
    }

    return res;
}

} // namespace cli::scan
