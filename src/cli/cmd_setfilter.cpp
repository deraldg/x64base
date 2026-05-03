#include "xbase.hpp"
#include "filters/filter_registry.hpp"

#include <cctype>
#include <iostream>
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
    std::string first;
    if (!(args >> first)) {
        std::cout << "SET FILTER TO <expr> | SET FILTER TO (clear)\n";
        return;
    }

    uppercase_inplace(first);

    if (first != "TO") {
        std::cout << "SET FILTER: expected 'TO'.\n";
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

        std::cout << "SET FILTER: cleared.\n";
        return;
    }

    std::string err;
    if (!filter::set(&area, expr, err)) {
        std::cout << "SET FILTER: error: " << err << "\n";
        return;
    }

    auto& info = g_filter_by_area[&area];
    info.expr = expr;
    info.active = true;

    std::cout << "SET FILTER TO " << expr << "\n";
}