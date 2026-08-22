// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: supported

// src/cli/workarea_util.cpp -- see workarea_util.hpp. Implementations are the
// canonical copies formerly duplicated in cmd_relations.cpp,
// rel_enum_engine.cpp, and set_relations.cpp (AIF-074 P0.2); behavior is
// intentionally identical to the removed copies.

#include "workarea_util.hpp"

#include "workareas.hpp"
#include "textio.hpp"
#include "command_output.hpp"

extern "C" xbase::XBaseEngine* shell_engine();

namespace cli {

namespace {
    std::string trim(std::string s) { return textio::trim(std::move(s)); }
    std::string up(std::string s)   { return textio::up(std::move(s)); }
} // namespace

// The one matching rule. logicalName() and name() are the SAME member
// (xbase.hpp:238 and :288; R112 sec 1), so this compares once and the old
// second comparison is not reproduced -- it was dead, and repeating it here
// would imply two name spaces that do not exist.
static std::string area_name_up(xbase::DbArea* a)
{
    if (!a) return {};
    bool open = false;
    try { open = a->isOpen(); } catch (...) { open = false; }
    if (!open) return {};
    try {
        const std::string ln = a->logicalName();
        if (!ln.empty()) return up(ln);
        const std::string nm = a->name();
        if (!nm.empty()) return up(nm);
    } catch (...) {}
    return {};
}

std::vector<xbase::DbArea*> find_open_areas_by_name_ci(const std::string& logical_or_name)
{
    std::vector<xbase::DbArea*> out;
    const std::string target = up(trim(logical_or_name));
    if (target.empty()) return out;

    const std::size_t n = workareas::count();
    for (std::size_t i = 0; i < n; ++i) {
        xbase::DbArea* a = workareas::db(i);
        if (area_name_up(a) == target) out.push_back(a);
    }
    return out;   // ascending by engine slot, because the array is walked in order
}

std::unordered_map<std::string, xbase::DbArea*> build_open_area_index_ci()
{
    std::unordered_map<std::string, xbase::DbArea*> out;
    const std::size_t n = workareas::count();
    out.reserve(n);

    for (std::size_t i = 0; i < n; ++i) {
        xbase::DbArea* a = workareas::db(i);
        const std::string key = area_name_up(a);
        if (key.empty()) continue;
        // emplace, NOT operator[]. This is the whole fix: the tree builder used
        // to assign, which silently promoted the LAST match over the first.
        out.emplace(key, a);
    }
    return out;
}

// ---- R112 migration instrument ------------------------------------------

namespace {

std::vector<AmbiguityHit>& ledger_ref()
{
    static std::vector<AmbiguityHit> v;
    return v;
}

std::size_t& resolution_count_ref()
{
    static std::size_t n = 0;
    return n;
}

// Announce ONCE per distinct (name, site) -- the same latch shape as
// set_relations.cpp's note_scan_truncated(), for the same reason: a resolver
// called from inside a refresh loop must not be able to spam a transcript.
void record_ambiguity(const std::string& target,
                      const std::vector<xbase::DbArea*>& cands,
                      const char* site)
{
    ++resolution_count_ref();

    const std::string tag = (site && *site) ? std::string(site) : std::string("unattributed");

    for (auto& h : ledger_ref()) {
        if (h.name == target && h.site == tag) { ++h.hits; return; }   // latched
    }

    AmbiguityHit h;
    h.name = target;
    h.site = tag;
    h.hits = 1;
    for (xbase::DbArea* a : cands) {
        if (!a) continue;
        h.engine_slots.push_back(static_cast<int>(a->engineSlot()));
        h.ws_handles.push_back(a->wsHandle());
    }
    h.chosen_slot = h.engine_slots.empty() ? -1 : h.engine_slots.front();
    ledger_ref().push_back(h);

    std::string line = "NAME: '" + target + "' is open in " +
                       std::to_string(h.engine_slots.size()) + " areas (";
    for (std::size_t i = 0; i < h.engine_slots.size(); ++i) {
        if (i) line += ", ";
        line += "ws " + std::to_string(static_cast<unsigned long long>(h.ws_handles[i])) +
                " area " + std::to_string(h.engine_slots[i]);
    }
    line += "); resolved to area " + std::to_string(h.chosen_slot) +
            " [" + tag + "]. Qualify the name -- first-wins is a migration step (R112).";
    try { cli::cmdout::print_line(line); } catch (...) {}
}

} // namespace

std::size_t ambiguity_count() { return resolution_count_ref(); }

const std::vector<AmbiguityHit>& ambiguity_ledger() { return ledger_ref(); }

void ambiguity_reset()
{
    ledger_ref().clear();
    resolution_count_ref() = 0;
}

xbase::DbArea* find_open_area_by_name_ci(const std::string& logical_or_name,
                                         const char* site)
{
    const std::string target = up(trim(logical_or_name));
    if (target.empty()) return nullptr;

    const std::vector<xbase::DbArea*> cands = find_open_areas_by_name_ci(target);
    if (cands.empty()) return nullptr;
    if (cands.size() > 1) record_ambiguity(target, cands, site);
    return cands.front();
}

xbase::DbArea* find_open_area_by_name_ci(const std::string& logical_or_name)
{
    return find_open_area_by_name_ci(logical_or_name, nullptr);
}

// AIF-120 I1.1. This was a linear scan over the open areas, comparing pointers
// to recover a number the area could simply have carried. It has 21 call sites
// across 15 files; none of them changes, because the SIGNATURE does not -- only
// the body. That is the whole shape of I1: ownership stops being reconstructed
// from side tables and starts being a property of the thing that has it.
//
// _engine_slot is stamped at engine construction (dbf_file.cpp, XBaseEngine ctor)
// and is never cleared, so this answers correctly for a closed area too -- the
// old scan did not, because workareas::db(i) only walks what is currently
// bound. Behaviour for an OPEN area is identical; for a closed one it is now
// right instead of -1.
//
// AIF-078 D8 sec 7, 2026-08-22: the parameter is CONST. It reads one member
// and mutates nothing, and set_relations.cpp's ScopedEngineSelect holds a
// const DbArea*. Widening to const is source-compatible for all existing
// callers and is what let the duplicate scan there be deleted rather than
// const_cast around.
int slot_of_area(const xbase::DbArea* area)
{
    if (!area) return -1;
    // The ENGINE slot -- the array position, which is what every caller here
    // selects on. Not the workspace-local slot; see DbArea::wsLocalSlot().
    return area->engineSlot();
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
