// @dottalk.file v1
// subsystem: tests
// layer: test
// owns: 
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

// NESTING IS PARENT_ID. RETIREMENT IS PREV_ID. THEY ARE NOT THE SAME EDGE.
//
// cmd_workspace.cpp stamps PARENT_ID and TREE_DEPTH (:3497-3498) and says in
// its own comment (:3157) that depth is derivable by walking rows -- and
// nothing in this tree ever walked them. WORKSPACE CATALOG prints flat. So the
// first walker is also the first chance to get the edge wrong, and a catalog
// carrying a long retirement tail would render as a staircase that never
// existed.
//
// A4 IS THE DISCRIMINATOR FOR DAMAGE and A6 for the contract: every input row
// appears exactly once, whatever shape the data is in. An ordering that
// silently loses a row it cannot place hands the caller a shorter list with no
// way to know it was shortened.
//
// THE WRONG EDGE IS NOT TESTED HERE BECAUSE IT CANNOT BE EXPRESSED. CatalogNode
// has no prev_id field, so a caller cannot pass the supersession chain as the
// nesting chain even by mistake. That is a stronger guarantee than an arm, and
// it is recorded here so a later reader does not add the field back "for
// completeness" and quietly reopen the hole.
//
// EACH ARM RETURNS ITS OWN CODE so a failure names itself in ctest output.

#include "cli/workspace_catalog_order.hpp"

#include <vector>

using dottalk::cli::CatalogNode;
using dottalk::cli::order_catalog;

int main()
{
    // A1. FLAT. No parents: every row is a root at depth 0, order preserved.
    {
        std::vector<CatalogNode> flat{{1, 0}, {2, 0}, {3, 0}};
        const auto o = order_catalog(flat);
        if (!o.placed_every_row(flat.size())) return 1;
        for (const auto& r : o.rows) {
            if (r.depth != 0) return 2;
            if (r.orphan || r.cycle || r.capped) return 3;
        }
        if (o.orphans || o.cycles || o.capped) return 4;
    }

    // A2. NESTING. 1 <- 2 <- 3 gives depths 0, 1, 2 in containment order.
    {
        std::vector<CatalogNode> chain{{1, 0}, {2, 1}, {3, 2}};
        const auto o = order_catalog(chain);
        if (!o.placed_every_row(chain.size())) return 5;
        if (o.rows.size() != 3)                return 6;
        if (o.rows[0].index != 0 || o.rows[0].depth != 0) return 7;
        if (o.rows[1].index != 1 || o.rows[1].depth != 1) return 8;
        if (o.rows[2].index != 2 || o.rows[2].depth != 2) return 9;
        if (o.orphans || o.cycles || o.capped)            return 10;
    }

    // A3. ORPHAN. A parent outside this input is a MISSING container, not a
    //     broken one -- ordering a subset is legitimate. Root it and say so.
    {
        std::vector<CatalogNode> sub{{5, 99}, {6, 5}};
        const auto o = order_catalog(sub);
        if (!o.placed_every_row(sub.size())) return 11;
        if (o.orphans != 1)                  return 12;
        if (!o.rows[0].orphan)               return 13;
        if (o.rows[0].depth != 0)            return 14;
        if (o.rows[1].depth != 1)            return 15;  // child still nests under it
        if (o.cycles)                        return 16;
    }

    // A4. CYCLE. 1 <- 2 <- 1. Unreachable from any root, so it must arrive
    //     through the second pass -- PRESENT, FLAGGED, and counted.
    {
        std::vector<CatalogNode> loop{{1, 2}, {2, 1}};
        const auto o = order_catalog(loop);
        if (!o.placed_every_row(loop.size())) return 17;
        if (o.cycles != 2)                    return 18;
        for (const auto& r : o.rows) {
            if (!r.cycle) return 19;
        }
    }

    // A5. DEPTH CAP. A chain longer than the limit is capped, not truncated:
    //     the rows past the cap are still in the output.
    {
        std::vector<CatalogNode> deep;
        deep.push_back({1, 0});
        for (std::uint64_t i = 2; i <= 10; ++i) {
            deep.push_back({i, i - 1});
        }
        const auto o = order_catalog(deep, /*max_depth=*/3);
        if (!o.placed_every_row(deep.size())) return 20;
        if (o.capped == 0)                    return 21;
        for (const auto& r : o.rows) {
            if (r.depth > 3) return 22;
        }
    }

    // A6. THE CONTRACT, ON THE UGLIEST INPUT THIS TYPE CAN CARRY: a real root,
    //     an orphan, a cycle and a self-parent together. Every row once.
    {
        std::vector<CatalogNode> mess{{1, 0}, {2, 1}, {3, 77}, {4, 5}, {5, 4}, {6, 6}};
        const auto o = order_catalog(mess);
        if (!o.placed_every_row(mess.size())) return 23;
        std::vector<bool> seen(mess.size(), false);
        for (const auto& r : o.rows) {
            if (r.index >= mess.size()) return 24;
            if (seen[r.index])          return 25;   // no row twice
            seen[r.index] = true;
        }
        for (bool s : seen) {
            if (!s) return 26;                        // and none missing
        }
    }

    // A7. EMPTY. Zero rows in, zero out, no counters moved -- distinguishable
    //     from "nothing was placed", which is the failure A6 guards.
    {
        std::vector<CatalogNode> none;
        const auto o = order_catalog(none);
        if (!o.placed_every_row(0)) return 27;
        if (!o.rows.empty())        return 28;
    }

    return 0;
}
