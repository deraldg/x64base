#pragma once
// include/cli/order_iterator.hpp
//
// Single-point order traversal provider for CLI commands.
// Goal: keep LIST/SMARTLIST/BROWSE/SCAN from re-implementing index walking.
//
// Policy:
// - If no order: NATURAL (1..recCount64)
// - INX: use INX loader
// - CNX: use CNX loader (or stopgap DB-derived order if that is your current rule)
// - CDX: use CDX family semantics, with execution mode selected per area
//        (Fallback or Lmdb)
//
// This file does not print. It only yields recnos.

#include <cstdint>
#include <functional>
#include <string>
#include <vector>

namespace xbase { class DbArea; }

namespace cli {

enum class OrderBackend {
    Natural,
    Inx,
    Cnx,
    Cdx,
    Isx,
    Csx,
};

enum class CdxExecMode {
    Fallback,
    Lmdb,
};

struct OrderIterSpec {
    OrderBackend backend = OrderBackend::Natural;
    CdxExecMode  cdx_mode = CdxExecMode::Fallback;
    std::string  container_path;  // active order file path (.inx/.cnx/.cdx/.isx/.csx), if any
    std::string  tag;             // active tag (CNX/CDX), if any
    bool         ascending = true;
};

// Collect ordered recnos in ASC order (caller can reverse if descending).
// Returns false if an ordered backend was requested but could not be read.
bool order_collect_recnos_asc(xbase::DbArea& area,
                              std::vector<uint64_t>& out_recnos,
                              OrderIterSpec* out_spec = nullptr,
                              std::string* out_err = nullptr);

// Visitor-based iteration (lets you avoid materializing all recnos if you later stream LMDB).
// Visitor returns false to stop early.
bool order_iterate_recnos(xbase::DbArea& area,
                          const std::function<bool(uint64_t recno)>& visitor,
                          OrderIterSpec* out_spec = nullptr,
                          std::string* out_err = nullptr);

// Genuinely streaming traversal in display order. Walks the active backend
// cursor (CDX first/next or last/prev), CNX payload entries, or a natural range
// WITHOUT materializing a full recno vector first, invoking `visitor` per recno.
// The visitor returns false to stop early (used by TOP/BOTTOM/SKIP/GO endpoints
// to stop at the first visible record).
//
// reverse == false -> yields records in display order (first .. last)
// reverse == true  -> yields records in reverse display order (last .. first)
//
// For index families without a streaming backend (INX/ISX/CSX) this falls back
// to order_collect_recnos_asc() and iterates the materialized vector.
bool order_stream_display(xbase::DbArea& area,
                          bool reverse,
                          const std::function<bool(uint64_t recno)>& visitor,
                          OrderIterSpec* out_spec = nullptr,
                          std::string* out_err = nullptr);

// Result of a single ordered CDX cursor step.
enum class OrderStep {
    Moved,        // out_recno holds the landing record number
    Boundary,     // current entry located, but the step ran off the order (no move)
    Unavailable   // not a usable CDX order / current record not in the index
};

// Move `index_delta` positions from the current record in ASCENDING index order
// (positive = forward / MDB_NEXT) using one ordered LMDB cursor -- no position
// map, no DBF scan. This is the O(log n) fast path for ordered SKIP on CDX. On
// Unavailable the caller should fall back to the position-map cache.
OrderStep order_step_cdx(xbase::DbArea& area, int index_delta, int32_t& out_recno);

} // namespace cli