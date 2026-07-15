#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "xbase.hpp"

namespace dottalk::tupleaugment {

struct RootRecnoSourceOptions {
    bool use_active_order{true};
    bool include_deleted{false}; // false = skip deleted root records
    bool only_deleted{false};    // true  = emit only deleted root records
};

struct RootRecnoSourceStats {
    std::string order_status{"NATURAL"};

    // Accounting surface.  table_rec_count is DbArea::recCount().
    // candidate_recnos is the number of root recnos considered before
    // goto/read/deleted filtering.  In natural order this normally equals
    // table_rec_count.  In ordered mode it is the index/order vector size.
    int table_rec_count{0};
    std::size_t candidate_recnos{0};
    std::size_t recnos_collected{0};

    // Skip diagnostics.  These are root-record-only diagnostics.
    std::size_t skipped_read{0};
    std::size_t skipped_deleted{0};
    std::size_t skipped_out_of_range{0};

    // Keep exact recno samples for practical debugging.  The vectors are capped
    // by the implementation so they do not become large on big tables.
    std::vector<int> skipped_read_recnos;
    std::vector<int> skipped_deleted_recnos;
    std::vector<int> skipped_out_of_range_recnos;

    int first_recno{0};
    int last_recno{0};
    bool ordered{false};
    bool order_fallback{false};
};

// Root-only traversal provider.
//
// This class deliberately knows nothing about relations, tuple projection, or
// tuple FOR predicates.  It provides root recnos in the traversal order that the
// current session/table establishes.  TupleGraphCursor consumes those recnos.
class RootRecnoSource {
public:
    RootRecnoSource(xbase::DbArea& root, RootRecnoSourceOptions options = {});

    bool collect(std::vector<int>& out, std::string& error);
    [[nodiscard]] const RootRecnoSourceStats& stats() const noexcept { return stats_; }

private:
    xbase::DbArea& root_;
    RootRecnoSourceOptions options_;
    RootRecnoSourceStats stats_;

    bool include_current_root_record_() const;
};

} // namespace dottalk::tupleaugment
