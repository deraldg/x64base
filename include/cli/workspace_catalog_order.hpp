// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: nesting order over durable workspace catalog rows
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: candidate

#pragma once

// WORKSPACES.dbf CARRIES TWO DIFFERENT EDGES AND ONLY ONE OF THEM IS NESTING.
//
//   PARENT_ID + TREE_DEPTH   containment. R135: a composition inherits its
//                            parent's durable id; 0 = root. cmd_workspace.cpp
//                            stamps both at :3497-3498, and its own comment at
//                            :3157 says TREE_DEPTH is DERIVABLE from PARENT_ID
//                            by walking rows.
//
//   PREV_ID + SUPERSEDED     retirement. D10.3 supersession: a destroyed
//                            workspace leaves a record, not a hole, so the
//                            name's history is a chain of rows.
//
// WALK THE SECOND ONE AND YOU BUILD A TREE OUT OF HISTORY -- every retired
// workspace becomes the parent of its own replacement, and a catalog with 134
// live rows and a long retirement tail renders as a staircase that never
// existed. The rule is borrowed, with credit, from the one place in this tree
// that had already written it down: gui/uidef/workbench_catalog.hpp, "Parent
// links are durable WS_IDs. PREV_ID is never used as a nesting edge."
//
// SO CatalogNode HAS NO prev_id FIELD. The wrong edge is not merely documented
// as wrong; it cannot be handed to this function at all. A rule a caller can
// follow by accident is better than a rule a caller must remember.
//
// NOTHING IS DROPPED, AND DAMAGE IS NAMED. A row whose parent is absent, a
// cycle, a chain past the depth cap -- each still appears in the output, and
// each is COUNTED and FLAGGED. An ordering that silently loses what it cannot
// place is the same defect as a gate that cannot express a miss: the caller
// reads a shorter list and has no way to know it was shortened.
//
// IT FILTERS NOTHING. Whether superseded rows belong in a nesting view is a
// maintainer ruling, not this function's. It orders the rows it is given.

#include <cstddef>
#include <cstdint>
#include <functional>
#include <map>
#include <set>
#include <vector>

namespace dottalk::cli {

struct CatalogNode {
    std::uint64_t ws_id{};      // durable WS_ID of this row
    std::uint64_t parent_id{};  // durable WS_ID of the container; 0 = root
};

struct OrderedRow {
    std::size_t index{};   // into the input vector, so the caller keeps its own fields
    unsigned    depth{};
    bool        orphan{};  // parent_id names an id absent from the input
    bool        cycle{};   // reached only by the second pass; its parent chain loops
    bool        capped{};  // placed at the depth limit rather than its true depth
};

struct CatalogOrder {
    std::vector<OrderedRow> rows;
    std::size_t orphans{};
    std::size_t cycles{};
    std::size_t capped{};

    // THE COUNT IS THE CONTRACT. Every input row appears exactly once.
    bool placed_every_row(std::size_t input_count) const {
        return rows.size() == input_count;
    }
};

inline CatalogOrder order_catalog(const std::vector<CatalogNode>& nodes,
                                  unsigned max_depth = 32)
{
    CatalogOrder out;
    std::set<std::uint64_t> ids;
    for (const auto& n : nodes) {
        ids.insert(n.ws_id);
    }

    std::map<std::uint64_t, std::vector<std::size_t>> children;
    for (std::size_t i = 0; i < nodes.size(); ++i) {
        children[nodes[i].parent_id].push_back(i);
    }

    std::set<std::size_t> visited;
    std::function<void(std::size_t, unsigned, bool, bool)> visit =
        [&](std::size_t i, unsigned depth, bool orphan, bool cycle) {
            if (!visited.insert(i).second) {
                return;
            }
            const bool at_cap = depth >= max_depth;
            OrderedRow row;
            row.index  = i;
            row.depth  = at_cap ? max_depth : depth;
            row.orphan = orphan;
            row.cycle  = cycle;
            row.capped = at_cap;
            out.rows.push_back(row);
            if (orphan) ++out.orphans;
            if (cycle)  ++out.cycles;
            if (at_cap) ++out.capped;
            if (at_cap) {
                return;
            }
            const auto kids = children.find(nodes[i].ws_id);
            if (kids == children.end()) {
                return;
            }
            for (std::size_t child : kids->second) {
                visit(child, depth + 1, false, cycle);
            }
        };

    // PASS 1 -- the real roots, and the orphans that behave like roots.
    // A row whose parent id is absent from this input is NOT an error: a
    // caller may legitimately order a SUBSET, and a parent outside the subset
    // is a missing container rather than a broken one. It is flagged so the
    // caller can tell the two apart.
    for (std::size_t i = 0; i < nodes.size(); ++i) {
        const std::uint64_t parent = nodes[i].parent_id;
        if (parent == 0) {
            visit(i, 0, false, false);
        } else if (!ids.count(parent)) {
            visit(i, 0, true, false);
        }
    }

    // PASS 2 -- whatever pass 1 could not reach is inside a cycle. It is shown
    // at depth 0 and FLAGGED, never dropped.
    for (std::size_t i = 0; i < nodes.size(); ++i) {
        visit(i, 0, false, true);
    }

    return out;
}

} // namespace dottalk::cli
