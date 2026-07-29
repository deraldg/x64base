// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: experimental

// src/cli/workarea_util.cpp -- see workarea_util.hpp. Implementations are the
// canonical copies formerly duplicated in cmd_relations.cpp,
// rel_enum_engine.cpp, and set_relations.cpp (AIF-074 P0.2); behavior is
// intentionally identical to the removed copies.

#include "workarea_util.hpp"

#include "workareas.hpp"
#include "textio.hpp"

extern "C" xbase::XBaseEngine* shell_engine();

namespace cli {

namespace {
    std::string trim(std::string s) { return textio::trim(std::move(s)); }
    std::string up(std::string s)   { return textio::up(std::move(s)); }
} // namespace

xbase::DbArea* find_open_area_by_name_ci(const std::string& logical_or_name)
{
    const std::string target = up(trim(logical_or_name));
    if (target.empty()) return nullptr;

    const std::size_t n = workareas::count();
    for (std::size_t i = 0; i < n; ++i) {
        xbase::DbArea* a = workareas::db(i);
        if (!a) continue;

        bool open = false;
        try { open = a->isOpen(); } catch (...) { open = false; }
        if (!open) continue;

        try {
            const std::string ln = a->logicalName();
            if (!ln.empty() && up(ln) == target) return a;
            const std::string nm = a->name();
            if (!nm.empty() && up(nm) == target) return a;
        } catch (...) {}
    }
    return nullptr;
}

int slot_of_area(xbase::DbArea* area)
{
    if (!area) return -1;
    const std::size_t n = workareas::count();
    for (std::size_t i = 0; i < n; ++i) {
        if (workareas::db(i) == area) return static_cast<int>(i);
    }
    return -1;
}

ScopedAreaSelect::ScopedAreaSelect(xbase::DbArea* area) noexcept
{
    eng_ = shell_engine();
    if (!eng_ || !area) return;

    const int slot = slot_of_area(area);
    if (slot < 0) return;

    try {
        prev_ = eng_->currentArea();
        if (prev_ != slot) {
            eng_->selectArea(slot);
            active_ = true;
        }
    } catch (...) { active_ = false; }
}

ScopedAreaSelect::~ScopedAreaSelect() noexcept
{
    if (!active_ || !eng_) return;
    try { eng_->selectArea(prev_); } catch (...) {}
}

ScopedEngineArea::ScopedEngineArea() noexcept
{
    eng_ = shell_engine();
    if (!eng_) return;
    try {
        prev_ = eng_->currentArea();
        active_ = true;
    } catch (...) { active_ = false; }
}

ScopedEngineArea::~ScopedEngineArea() noexcept
{
    if (!active_ || !eng_) return;
    try { eng_->selectArea(prev_); } catch (...) {}
}

std::vector<std::string> split_tuple_expr_csv(const std::string& s)
{
    std::vector<std::string> out;
    std::string cur;
    int paren_depth = 0;
    bool in_quote = false;

    for (std::size_t i = 0; i < s.size(); ++i) {
        const char c = s[i];

        if (c == '"' && (i == 0 || s[i - 1] != '\\')) {
            in_quote = !in_quote;
            cur.push_back(c);
            continue;
        }
        if (!in_quote) {
            if (c == '(') { ++paren_depth; cur.push_back(c); continue; }
            if (c == ')' && paren_depth > 0) { --paren_depth; cur.push_back(c); continue; }
            if (c == ',' && paren_depth == 0) {
                std::string t = trim(cur);
                if (!t.empty()) out.push_back(std::move(t));
                cur.clear();
                continue;
            }
        }
        cur.push_back(c);
    }

    std::string t = trim(cur);
    if (!t.empty()) out.push_back(std::move(t));
    return out;
}

} // namespace cli
