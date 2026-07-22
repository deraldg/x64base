// @dottalk.usage v1
// owner: DOT|SET FILTER
// command: SET FILTER
// category: query
// status: supported
// noargs: usage
// effect: configure
// mutates: filter-state
// usage-access: SET FILTER USAGE
// summary:
//   Set or clear the per-area filter expression used by selector-backed scans.
//
// usage:
//   SET FILTER USAGE
//   SET FILTER TO <expr>
//   SET FILTER TO
//   SETFILTER USAGE
//   SETFILTER TO <expr>
//   SETFILTER TO
//
// notes:
//   SET FILTER with no arguments shows usage.
//   SET FILTER TO with no expression clears the filter.
//   SET FILTER TO <expr> validates and activates the filter expression.
//   Filter state is keyed by DbArea pointer and also registered with the shared filter registry.
//   SET FILTER mutates selection/session state but not table records.
//
// risk:
//   mutates_filter_state: yes
//   mutates_table_data: no
//
// related:
//   COUNT
//   LOCATE
//   LIST
//   SET
//

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "filters/filter_registry.hpp"
#include "cli/expr/normalize_where.hpp"   // parity with COUNT FOR / LIST FOR
#include "help/helpdata_messages.hpp"

#include <cctype>
#include <sstream>
#include <string>
#include <unordered_map>

namespace {

struct FilterInfo {
    std::string expr;
    bool active{false};
};

static std::unordered_map<const xbase::DbArea*, FilterInfo> g_filter_by_area;

static inline std::string trim_left_one_space(std::string s) {
    if (!s.empty() && s.front() == ' ') {
        s.erase(0, 1);
    }
    return s;
}

static inline void uppercase_inplace(std::string& s) {
    for (auto& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
}


static std::string trim_copy_local(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string upper_copy_local(std::string s)
{
    uppercase_inplace(s);
    return s;
}

// Conservative guard, identical to cmd_count.cpp / cmd_scan.cpp / cmd_locate.cpp:
// any parenthesized predicate (a function call such as SOUNDEX(LNAME)="X") is
// passed through unchanged, so the RHS-literal normalizer cannot damage it.
static bool expression_has_function_call(const std::string& expr)
{
    return expr.find('(') != std::string::npos &&
           expr.find(')') != std::string::npos;
}

static void print_setfilter_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::SetFilterUsageText);
}

static bool is_setfilter_usage_request(const std::string& raw)
{
    std::string t = upper_copy_local(trim_copy_local(raw));
    if (t.rfind("SET FILTER ", 0) == 0) {
        t = upper_copy_local(trim_copy_local(t.substr(11)));
    }
    return t.empty() || t == "USAGE" || t == "HELP" || t == "?";
}

} // namespace

bool filter_is_active_for(const xbase::DbArea* area) {
    auto it = g_filter_by_area.find(area);
    return it != g_filter_by_area.end() && it->second.active;
}

std::string filter_expr_for(const xbase::DbArea* area) {
    auto it = g_filter_by_area.find(area);
    if (it == g_filter_by_area.end()) {
        return {};
    }
    return it->second.expr;
}

void cmd_SETFILTER(xbase::DbArea& area, std::istringstream& args) {
    const std::string raw_args = args.str();

    std::string first;
    if (!(args >> first)) {
        print_setfilter_usage();
        return;
    }

    if (is_setfilter_usage_request(first) || is_setfilter_usage_request(raw_args)) {
        print_setfilter_usage();
        return;
    }

    uppercase_inplace(first);

    if (first != "TO") {
        cli::cmdout::print_prefixed_message(
            "SET FILTER",
            dottalk::helpdata::MessageId::SetFilterExpectedToText);
        print_setfilter_usage();
        return;
    }

    std::string expr;
    std::getline(args, expr);
    expr = trim_left_one_space(std::move(expr));

    if (expr.empty()) {
        filter::clear(&area);

        auto& info = g_filter_by_area[&area];
        info.expr.clear();
        info.active = false;

        cli::cmdout::print_prefixed_message(
            "SET FILTER",
            dottalk::helpdata::MessageId::SetFilterClearedText);
        return;
    }

    // Normalize unquoted RHS barewords to string literals exactly as COUNT FOR /
    // LIST FOR do, so `SET FILTER TO MAJOR = CSCI` matches `COUNT FOR MAJOR =
    // CSCI` (CSCI is the string "CSCI", not an undefined identifier that resolves
    // empty and matches nothing). Numeric and already-quoted RHS pass through
    // unchanged; function predicates are skipped by the guard above.
    if (!expression_has_function_call(expr)) {
        expr = normalize_unquoted_rhs_literals(area, expr);
    }

    std::string err;
    if (!filter::set(&area, expr, err)) {
        cli::cmdout::print_prefixed_message(
            "SET FILTER",
            dottalk::helpdata::MessageId::SetFilterErrorText,
            {{"detail", err}});
        return;
    }

    auto& info = g_filter_by_area[&area];
    info.expr = expr;
    info.active = true;

    cli::cmdout::print_prefixed_message(
        "SET FILTER",
        dottalk::helpdata::MessageId::SetFilterAppliedText,
        {{"expr", expr}});
}
