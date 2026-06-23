// ===============================
// src/cli/cmd_where.cpp
// WHERE expression state + shared evaluator + optional DEBUG plan dump
// WHERE is bound into the runtime SET FILTER path.
// ===============================
// @dottalk.usage v1
// owner: DOT|WHERE
// command: WHERE
// category: filter
// status: supported
// noargs: report
// effect: filter
// mutates: where-state filter-state
// usage-access: WHERE USAGE
// summary:
//   Show, set, debug, or clear the WHERE predicate state bound into SET FILTER.
//
// usage:
//   WHERE
//   WHERE USAGE
//   WHERE <expr>
//   WHERE <expr> DEBUG
//   WHERE CLEAR
//   WHERE OFF
//
// notes:
//   WHERE with no arguments reports current WHERE state.
//   WHERE <expr> compiles the predicate, probes the current record for diagnostics, and delegates to SET FILTER.
//   WHERE CLEAR and WHERE OFF clear WHERE state and the associated SET FILTER path.
//   WHERE DEBUG prints compile/field diagnostics for the expression.
//   WHERE USAGE prints usage without changing filter state.
//
// risk:
//   mutates_where_state: WHERE <expr>, CLEAR, OFF
//   mutates_filter_state: delegated SET FILTER changes
//   mutates_table_data: no
//
// related:
//   SETFILTER
//   COUNT
//   LIST
//   SMARTLIST
//

#include <algorithm>
#include <cctype>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>

#include "xbase.hpp"
#include "xbase_field_getters.hpp"
#include "textio.hpp"
#include "cli/where_eval_shared.hpp"

namespace xbase { class DbArea; }

// SET FILTER command entry point.
// WHERE delegates to this so COUNT/LIST/SMARTLIST all see the same predicate state.
void cmd_SETFILTER(xbase::DbArea& area, std::istringstream& args);

namespace {

static inline bool iequals(const std::string& a, const std::string& b)
{
    if (a.size() != b.size()) return false;
    for (size_t i = 0; i < a.size(); ++i) {
        unsigned char ca = static_cast<unsigned char>(a[i]);
        unsigned char cb = static_cast<unsigned char>(b[i]);
        if (std::tolower(ca) != std::tolower(cb)) return false;
    }
    return true;
}

static inline std::string iupper(std::string s)
{
    for (auto& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static inline std::string read_rest(std::istringstream& iss)
{
    std::string rest;
    const std::string& all = iss.str();
    auto pos = iss.tellg();

    if (pos != std::istringstream::pos_type(-1)) {
        size_t i = static_cast<size_t>(pos);
        if (i < all.size()) {
            rest = all.substr(i);
        }
    } else {
        rest = all;
    }

    return where_eval::dt_trim(rest);
}

static std::pair<std::string, bool> strip_trailing_debug(std::string s)
{
    s = where_eval::dt_trim(std::move(s));
    if (s.empty()) return {s, false};

    auto last_space = s.find_last_of(" \t\r\n");
    if (last_space == std::string::npos) {
        if (iequals(s, "DEBUG")) return {std::string{}, true};
        return {s, false};
    }

    std::string tail = s.substr(last_space + 1);
    if (iequals(tail, "DEBUG")) {
        std::string head = s.substr(0, last_space);
        head = where_eval::dt_trim(std::move(head));
        return {head, true};
    }

    return {s, false};
}

struct WhereInfo {
    std::string expr;
    bool active{false};
};

static std::unordered_map<const xbase::DbArea*, WhereInfo> g_where_by_area;

static inline WhereInfo* where_info_for(const xbase::DbArea* area)
{
    return &g_where_by_area[area];
}

static void bind_filter_to_where(xbase::DbArea& area, const std::string& expr)
{
    // SET FILTER parser expects "TO <expr>" for setting a filter.
    std::istringstream filter_args(std::string("TO ") + expr);
    cmd_SETFILTER(area, filter_args);
}

static void clear_filter_for_where(xbase::DbArea& area)
{
    // SET FILTER TO clears in the public command surface.
    std::istringstream clear_args("TO");
    cmd_SETFILTER(area, clear_args);
}

} // namespace

const WhereInfo* where_active_for(const xbase::DbArea* area)
{
    auto it = g_where_by_area.find(area);
    return (it == g_where_by_area.end() ? nullptr : &it->second);
}

static void print_where_usage()
{
    std::cout
        << "Usage:\n"
        << "  WHERE\n"
        << "  WHERE USAGE\n"
        << "  WHERE <expr>\n"
        << "  WHERE <expr> DEBUG\n"
        << "  WHERE CLEAR\n"
        << "  WHERE OFF\n";
}

static void print_where_status(xbase::DbArea& area)
{
    auto* info = where_info_for(&area);
    if (info->active) {
        std::cout << "; WHERE: ON\n";
        std::cout << "; WHERE expr: " << (info->expr.empty() ? "(empty)" : info->expr) << "\n";
    } else {
        std::cout << "; WHERE: OFF\n";
    }
}

void cmd_WHERE(xbase::DbArea& area, std::istringstream& args)
{
    std::string rest = read_rest(args);

    if (rest.empty()) {
        print_where_status(area);
        return;
    }

    if (iequals(rest, "USAGE") || iequals(rest, "HELP") || iequals(rest, "?")) {
        print_where_usage();
        return;
    }

    {
        std::string up = iupper(rest);
        if (iequals(up, "CLEAR") || iequals(up, "OFF")) {
            auto* info = where_info_for(&area);
            info->expr.clear();
            info->active = false;

            clear_filter_for_where(area);

            std::cout << "; WHERE: cleared\n";
            return;
        }
    }

    auto [expr, wants_debug] = strip_trailing_debug(rest);
    expr = where_eval::dt_trim(std::move(expr));

    if (expr.empty()) {
        auto* info = where_info_for(&area);
        info->expr.clear();
        info->active = false;

        clear_filter_for_where(area);

        std::cout << "; WHERE: cleared\n";
        return;
    }

    bool ok = false;
    std::shared_ptr<const where_eval::CacheEntry> ce;

    try {
        ce = where_eval::compile_where_expr_cached(expr);
        if (!ce || !ce->plan) {
            throw std::runtime_error("WHERE compile produced no program");
        }

        // Probe current record for immediate syntax/runtime feedback.
        // The result is only diagnostic; runtime visibility is handled by SET FILTER.
        ok = where_eval::run_program(*ce->plan, area);
    } catch (const std::exception& ex) {
        std::cout << "WHERE error: " << ex.what() << "\n";
        if (wants_debug) {
            std::cout << "WHERE DEBUG - raw: \"" << expr << "\"\n";
        }
        return;
    }

    {
        auto* info = where_info_for(&area);
        info->expr = expr;
        info->active = true;
    }

    // Critical behavior:
    // WHERE must participate in the same predicate path used by COUNT/LIST/SMARTLIST.
    // Delegating to SET FILTER avoids creating a second, divergent predicate engine.
    bind_filter_to_where(area, expr);

    if (wants_debug) {
        std::cout << "WHERE DEBUG - raw: \"" << expr << "\"\n";
        std::cout << "WHERE DEBUG - compiled: " << where_eval::plan_kind(*ce->plan) << "\n";

        if (ce && !ce->fields.empty()) {
            for (const std::string& fld : ce->fields) {
                std::string s;
                try {
                    s = xfg::getFieldAsString(area, fld);
                } catch (...) {
                    s = "(ERR)";
                }

                std::cout << fld << " = \""
                          << where_eval::dt_upcase(where_eval::dt_trim(s))
                          << "\"\n";
            }
        } else {
            std::cout << "(no fields)\n";
        }

        std::cout << (ok ? "T\n" : "F\n");
    }
}