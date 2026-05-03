#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "tuple_types.hpp"
#include "xbase.hpp"

namespace dottalk::tupleaugment {

struct TupleGraphCursorOptions {
    std::string tuple_spec{"*"};
    std::string for_expr;

    bool use_active_order{true};
    bool include_deleted{false}; // root-record deleted semantics, v1
    bool only_deleted{false};
    bool strict_fields{false};
    bool header_area_prefix{true}; // safer default for relation-aware output
};

struct TupleGraphCursorStats {
    // root_visited is the number of emitted root recnos consumed by next().
    // tuples_emitted is the number of TupleRows that passed the tuple predicate.
    std::int64_t root_visited{0};
    std::int64_t tuples_emitted{0};

    // RootRecnoSource accounting.
    int root_table_rec_count{0};
    std::size_t root_candidate_recnos{0};
    std::size_t root_recnos_collected{0};
    std::size_t root_skipped_read{0};
    std::size_t root_skipped_deleted{0};
    std::size_t root_skipped_out_of_range{0};
    std::vector<int> root_skipped_read_recnos;
    std::vector<int> root_skipped_deleted_recnos;
    std::vector<int> root_skipped_out_of_range_recnos;

    int first_root_recno{0};
    int last_root_recno{0};

    std::string order_status;
    std::string for_expr;

    bool ordered{false};
    bool order_fallback{false};
    bool cursors_restored{false};
};

// Relation-aware tuple iterator.
//
// Flow:
//   root recno traversal -> relation refresh -> tuple_builder projection
//   -> tuple-row FOR predicate -> emitted TupleRow
//
// This deliberately keeps root traversal table-aware while keeping tuple
// predicate/projection relation-aware.
class TupleGraphCursor {
public:
    TupleGraphCursor(xbase::DbArea& root, TupleGraphCursorOptions options);
    ~TupleGraphCursor();

    TupleGraphCursor(const TupleGraphCursor&) = delete;
    TupleGraphCursor& operator=(const TupleGraphCursor&) = delete;

    bool open(std::string& error);
    bool next(dottalk::TupleRow& out, std::string& error);
    void close() noexcept;

    [[nodiscard]] const TupleGraphCursorStats& stats() const;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace dottalk::tupleaugment
