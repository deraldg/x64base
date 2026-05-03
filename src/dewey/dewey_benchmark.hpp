#pragma once
#include "xbase.hpp"
#include <string>
#include <vector>
#include <stdexcept>

namespace xbase {

/**
 * DeweyIndex - Plug-and-play hierarchical indexing using abstracted Dewey decimal coordinates
 * 
 * This class provides a purely structural hierarchical node indexing system.
 * It works on top of your existing B+Tree IndexManager by using a single 'dewey_id' C(200) field.
 * Supports both basic sparse-gap and advanced dynamic (ORDPATH-style) insertion strategies.
 */
class DeweyIndex {
public:
    explicit DeweyIndex(DbArea& area);

    // ====================== Basic Sparse-Gap Operations ======================
    
    /**
     * Insert a new root-level node
     */
    std::string insertRoot(const std::string& label = "", const std::string& payload = "");

    /**
     * Insert a new child under parent_id using sparse gaps (fast, low relabeling)
     */
    std::string insertChild(const std::string& parent_id,
                            const std::string& label = "",
                            const std::string& payload = "");

    /**
     * Insert a new node between two existing siblings (fractional midpoint)
     */
    std::string insertBetween(const std::string& left_id,
                              const std::string& right_id,
                              const std::string& label = "",
                              const std::string& payload = "");

    // ====================== Advanced Dynamic Operations (Zero Relabeling) ======================

    /**
     * Insert child using ORDPATH-inspired dynamic strategy (odd numbers + even components)
     * Guarantees minimal to zero relabeling even under heavy insertions
     */
    std::string insertChildDynamic(const std::string& parent_id,
                                   const std::string& label = "",
                                   const std::string& payload = "");

    /**
     * Insert between siblings using dynamic ORDPATH-style rules
     */
    std::string insertBetweenDynamic(const std::string& left_id,
                                     const std::string& right_id,
                                     const std::string& label = "",
                                     const std::string& payload = "");

    // ====================== Navigation Operations ======================

    /**
     * Get all descendants (subtree) including the root node itself
     * Returns list of 64-bit record numbers
     */
    std::vector<uint64_t> getSubtreeRecnos(const std::string& root_id) const;

    /**
     * Get only direct children of a node
     */
    std::vector<uint64_t> getDirectChildrenRecnos(const std::string& parent_id) const;

    /**
     * Get path from node to root (ancestors)
     */
    std::vector<uint64_t> getPathToRootRecnos(const std::string& node_id) const;

    // ====================== Helper Methods ======================

    /**
     * Get dewey_id for a given record number
     */
    std::string getDeweyId(uint64_t recno64) const;

    /**
     * Set dewey_id for a given record number
     */
    bool setDeweyId(uint64_t recno64, const std::string& new_id);

    /**
     * Get parent dewey_id
     */
    std::string parentOf(const std::string& id) const;

    /**
     * Check if id is descendant of ancestor
     */
    bool isDescendant(const std::string& id, const std::string& ancestor) const;

    /**
     * One-time migration to make existing tree more dynamic-friendly
     */
    bool migrateToDynamic();

private:
    DbArea& _area;
    int     _deweyFieldIdx{0};   // 1-based field index of dewey_id

    // Internal helpers
    int findDeweyField() const;
    std::string nextSparseSibling(const std::string& prefix) const;

    // Low-level string utilities
    static std::string removeLastSegment(const std::string& id);
    static int countDots(const std::string& id);
};

} // namespace xbase