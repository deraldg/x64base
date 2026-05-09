#pragma once

#include "xbase.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace dottalk::edu_idx {

// EDU IDX: memory-only educational index laboratory.
//
// This subsystem is orthogonal to persistent index families.
// It is a teaching cousin of INX/CNX/CDX, not a persistent backend.
//
// EDU IDX must not:
//   - write index files
//   - open INX/CNX/CDX files
//   - implement IIndexBackend
//   - register with IndexManager
//   - participate in SET ORDER, REINDEX, or WORKSPACE restore
//   - silently alter production table order
//
// It exists to teach sorting, searching, timing, and index concepts.

enum class SortAlgo {
    Std,
    Bubble
};

enum class SortDirection {
    Asc,
    Desc
};

struct Entry {
    std::string key;
    uint32_t recno = 0;
};

struct AlgoStats {
    std::string name;
    uint64_t comparisons = 0;
    uint64_t swaps = 0;
    uint64_t moves = 0;
    uint64_t elapsed_us = 0;
};

struct BuildStats {
    int32_t records_scanned = 0;
    int32_t records_indexed = 0;
    int32_t deleted_skipped = 0;
    uint64_t elapsed_us = 0;   // total build: scan + normalize + sort + direction
    AlgoStats sort;            // sort-only timing/counters
};

struct MemoryIndex {
    std::string tag;
    std::string expr;
    std::vector<Entry> entries;

    uint16_t keylen = 0;
    char ftype = 0;
    int32_t rec_count_snapshot = 0;

    SortAlgo sort_algo = SortAlgo::Std;
    SortDirection direction = SortDirection::Asc;

    BuildStats build;
};

struct IndexSummary {
    std::string tag;
    std::string expr;
    std::string sort_algo;
    std::string direction;
    uint32_t entries = 0;
    uint64_t build_us = 0;
};

struct BuildRequest {
    std::string field_token;
    std::string tag;
    SortAlgo sort_algo = SortAlgo::Std;
    SortDirection direction = SortDirection::Asc;
};

struct BuildResult {
    bool ok = false;
    bool replaced = false;
    std::string message;
    std::string tag;
    BuildStats build;
};

std::string to_string(SortAlgo algo);
std::string to_string(SortDirection direction);

bool parse_sort_algo(const std::string& token, SortAlgo& out);
bool parse_direction(const std::string& token, SortDirection& out);

BuildResult build_and_store(xbase::DbArea& area, const BuildRequest& request);

const MemoryIndex* find_index(const std::string& tag);
std::vector<IndexSummary> list_indexes();

bool drop_index(const std::string& tag);
void drop_all_indexes();

} // namespace dottalk::edu_idx