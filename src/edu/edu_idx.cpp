// @dottalk.usage v1
// owner: EDU|IDX_BACKEND
// command: IDX
// category: education-index-helper
// status: backend-helper
// noargs: n/a
// effect: in-memory-index-support
// mutates: in-memory-index-state
// usage-access: owned-by cmd_idx.cpp
// summary:
//   Backend/helper implementation for the educational memory-only IDX command.
//
// usage:
//   Runtime IDX command behavior and usage are owned by src/cli/cmd_idx.cpp.
//   This file provides dottalk::edu_idx support functions and should not define
//   a second command surface.
//
// notes:
//   Keep command dispatch and usage text centralized in cmd_idx.cpp to avoid
//   drift between the shell command and backend helper.
//
// risk:
//   mutates_table_data: no
//   mutates_in_memory_index_state: yes through backend API
//

#include "cli/edu_idx.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cstdint>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace dottalk::edu_idx {
namespace {

using Clock = std::chrono::steady_clock;

std::unordered_map<std::string, MemoryIndex> g_indexes;

std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

std::string trim_copy(const std::string& s) {
    const std::string ws = " \t\r\n";
    const std::size_t b = s.find_first_not_of(ws);
    if (b == std::string::npos) return std::string();
    const std::size_t e = s.find_last_not_of(ws);
    return s.substr(b, e - b + 1);
}

std::string canon_tag(const std::string& tag) {
    return upper_copy(trim_copy(tag));
}

bool is_hashnum(const std::string& tok, int& out) {
    if (tok.size() < 2 || tok[0] != '#') return false;
    for (std::size_t i = 1; i < tok.size(); ++i) {
        if (!std::isdigit(static_cast<unsigned char>(tok[i]))) return false;
    }
    try {
        out = std::stoi(tok.substr(1));
    } catch (...) {
        return false;
    }
    return true;
}

int resolve_field_index(const xbase::DbArea& area, const std::string& tok) {
    int n = 0;
    if (is_hashnum(tok, n)) {
        return (n >= 1 && n <= area.fieldCount()) ? n : -1;
    }

    const std::string want = upper_copy(trim_copy(tok));
    const auto& fields = area.fields();
    for (std::size_t i = 0; i < fields.size(); ++i) {
        if (upper_copy(fields[i].name) == want) {
            return static_cast<int>(i + 1);
        }
    }
    return -1;
}

std::string normalize_key(std::string key, const xbase::FieldDef& fd) {
    if (fd.type == 'C' || fd.type == 'c') {
        key = upper_copy(std::move(key));
        const std::size_t want = static_cast<std::size_t>(fd.length);
        if (key.size() > want) {
            key.resize(want);
        } else if (key.size() < want) {
            key.append(want - key.size(), ' ');
        }
    }
    return key;
}

uint64_t elapsed_us(Clock::time_point a, Clock::time_point b) {
    return static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::microseconds>(b - a).count());
}

class CursorGuard {
public:
    explicit CursorGuard(xbase::DbArea& area)
        : area_(&area) {
        try {
            saved_ = area.recno();
            active_ = area.isOpen() && saved_ >= 1 && saved_ <= area.recCount();
        } catch (...) {
            active_ = false;
        }
    }

    ~CursorGuard() {
        if (!active_ || !area_) return;
        try {
            if (area_->gotoRec(saved_)) {
                (void)area_->readCurrent();
            }
        } catch (...) {
        }
    }

    CursorGuard(const CursorGuard&) = delete;
    CursorGuard& operator=(const CursorGuard&) = delete;

private:
    xbase::DbArea* area_ = nullptr;
    int32_t saved_ = 0;
    bool active_ = false;
};

bool less_entry(const Entry& a, const Entry& b, AlgoStats& stats) {
    ++stats.comparisons;
    if (a.key == b.key) return a.recno < b.recno;
    return a.key < b.key;
}

void counted_swap(Entry& a, Entry& b, AlgoStats& stats) {
    using std::swap;
    swap(a, b);
    ++stats.swaps;
}

void sort_std(std::vector<Entry>& entries, AlgoStats& stats) {
    stats.name = to_string(SortAlgo::Std);
    std::sort(entries.begin(), entries.end(),
        [&stats](const Entry& a, const Entry& b) {
            return less_entry(a, b, stats);
        });
}

void sort_bubble(std::vector<Entry>& entries, AlgoStats& stats) {
    stats.name = to_string(SortAlgo::Bubble);
    const std::size_t n = entries.size();
    if (n < 2) return;

    for (std::size_t i = 0; i < n; ++i) {
        bool swapped = false;
        for (std::size_t j = 0; j + 1 < n - i; ++j) {
            if (less_entry(entries[j + 1], entries[j], stats)) {
                counted_swap(entries[j], entries[j + 1], stats);
                swapped = true;
            }
        }
        if (!swapped) break;
    }
}

void sort_entries(std::vector<Entry>& entries, SortAlgo algo, BuildStats& build) {
    build.sort = AlgoStats{};
    build.sort.name = to_string(algo);

    const auto t0 = Clock::now();
    switch (algo) {
        case SortAlgo::Bubble:
            sort_bubble(entries, build.sort);
            break;
        case SortAlgo::Std:
        default:
            sort_std(entries, build.sort);
            break;
    }
    const auto t1 = Clock::now();
    build.sort.elapsed_us = elapsed_us(t0, t1);
}

std::string unknown_field_message(const xbase::DbArea& area, const std::string& tok) {
    std::ostringstream out;
    out << "IDX: unknown field '" << tok << "'.";
    if (!area.fields().empty()) {
        out << " Available:";
        for (const auto& fd : area.fields()) {
            out << ' ' << fd.name;
        }
    }
    return out.str();
}

} // namespace

std::string to_string(SortAlgo algo) {
    switch (algo) {
        case SortAlgo::Bubble: return "BUBBLE";
        case SortAlgo::Std:
        default: return "STD";
    }
}

std::string to_string(SortDirection direction) {
    switch (direction) {
        case SortDirection::Desc: return "DESC";
        case SortDirection::Asc:
        default: return "ASC";
    }
}

bool parse_sort_algo(const std::string& token, SortAlgo& out) {
    const std::string t = upper_copy(trim_copy(token));
    if (t == "STD" || t == "STDSORT" || t == "STD_SORT" || t == "STANDARD") {
        out = SortAlgo::Std;
        return true;
    }
    if (t == "BUBBLE" || t == "BUBBLESORT" || t == "BUBBLE_SORT") {
        out = SortAlgo::Bubble;
        return true;
    }
    return false;
}

bool parse_direction(const std::string& token, SortDirection& out) {
    const std::string t = upper_copy(trim_copy(token));
    if (t == "ASC" || t == "ASCEND" || t == "ASCENDING") {
        out = SortDirection::Asc;
        return true;
    }
    if (t == "DESC" || t == "DESCEND" || t == "DESCENDING") {
        out = SortDirection::Desc;
        return true;
    }
    return false;
}

BuildResult build_and_store(xbase::DbArea& area, const BuildRequest& request) {
    BuildResult result{};

    if (!area.isOpen()) {
        result.message = "IDX: no table open.";
        return result;
    }

    if (trim_copy(request.field_token).empty()) {
        result.message = "IDX: missing field token.";
        return result;
    }

    if (trim_copy(request.tag).empty()) {
        result.message = "IDX: missing TAG name.";
        return result;
    }

    const int fld = resolve_field_index(area, request.field_token);
    if (fld < 1) {
        result.message = unknown_field_message(area, request.field_token);
        return result;
    }

    const auto& fields = area.fields();
    const auto& fd = fields[static_cast<std::size_t>(fld - 1)];

    CursorGuard restore(area);

    MemoryIndex idx{};
    idx.tag = trim_copy(request.tag);
    idx.expr = request.field_token;
    idx.keylen = static_cast<uint16_t>(fd.length);
    idx.ftype = fd.type;
    idx.rec_count_snapshot = area.recCount();
    idx.sort_algo = request.sort_algo;
    idx.direction = request.direction;

    const auto build_t0 = Clock::now();

    const int32_t total = area.recCount();
    idx.build.records_scanned = total;
    if (total > 0) {
        idx.entries.reserve(static_cast<std::size_t>(total));
    }

    for (int32_t rn = 1; rn <= total; ++rn) {
        if (!area.gotoRec(rn)) continue;
        if (!area.readCurrent()) continue;

        if (area.isDeleted()) {
            ++idx.build.deleted_skipped;
            continue;
        }

        std::string key = area.get(fld);
        key = normalize_key(std::move(key), fd);
        idx.entries.push_back(Entry{std::move(key), static_cast<uint32_t>(rn)});
    }

    idx.build.records_indexed = static_cast<int32_t>(idx.entries.size());

    sort_entries(idx.entries, request.sort_algo, idx.build);

    if (request.direction == SortDirection::Desc) {
        std::reverse(idx.entries.begin(), idx.entries.end());
    }

    const auto build_t1 = Clock::now();
    idx.build.elapsed_us = elapsed_us(build_t0, build_t1);

    const std::string key = canon_tag(idx.tag);
    result.replaced = (g_indexes.find(key) != g_indexes.end());

    result.tag = idx.tag;
    result.build = idx.build;

    g_indexes[key] = std::move(idx);

    result.ok = true;
    result.message = result.replaced ? "IDX: memory index replaced." : "IDX: memory index created.";
    return result;
}

const MemoryIndex* find_index(const std::string& tag) {
    const auto it = g_indexes.find(canon_tag(tag));
    if (it == g_indexes.end()) return nullptr;
    return &it->second;
}

std::vector<IndexSummary> list_indexes() {
    std::vector<IndexSummary> out;
    out.reserve(g_indexes.size());

    for (const auto& kv : g_indexes) {
        const MemoryIndex& idx = kv.second;
        IndexSummary s{};
        s.tag = idx.tag;
        s.expr = idx.expr;
        s.sort_algo = to_string(idx.sort_algo);
        s.direction = to_string(idx.direction);
        s.entries = static_cast<uint32_t>(idx.entries.size());
        s.build_us = idx.build.elapsed_us;
        out.push_back(std::move(s));
    }

    std::sort(out.begin(), out.end(),
        [](const IndexSummary& a, const IndexSummary& b) {
            return upper_copy(a.tag) < upper_copy(b.tag);
        });

    return out;
}

bool drop_index(const std::string& tag) {
    return g_indexes.erase(canon_tag(tag)) != 0;
}

void drop_all_indexes() {
    g_indexes.clear();
}

} // namespace dottalk::edu_idx