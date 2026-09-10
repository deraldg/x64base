// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: the WORKDESK observer -- one session's open workspaces as one value
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: experimental

// File: include/cli/workdesk.hpp
// Purpose: A READ-ONLY view of the whole desk: every open workspace in this
//          session, the areas each one holds, and the facts a reporter needs
//          without walking the engine itself.
// Boundary: Owns NOTHING. It reads xbase::workspace::default_table() and the
//           engine's areas through cli/workareas.hpp, composes them, and
//           returns a value. It creates, destroys, switches and stamps nothing.
//
// WHY THIS EXISTS, stated once so it is not rediscovered.
//
// The two-level truth already exists and is already reachable.
// `xbase::workspace::WorkspaceTable` answers name, ws_id, parent, depth,
// members, owner_of_slot, roots and the current handle. The AREA level answers
// name and open-state through the engine. NOTHING JOINS THEM. cmd_workspace.cpp
// does the join inline and prints it, WSREPORT does its own, and the ambiguity
// ledger built a third -- `cli::AmbiguityHit` carries `ws_handles` parallel to
// `engine_slots`, which is this same pairing, reinvented because there was
// nowhere to get it. Three consumers, three private joins, console text as the
// only output. That is why nothing outside those three can report at the
// workspace level: not a silent engine, an unpublished composition.
//
// `workareas::WorkAreaSet` is NOT this. It is a flat vector of MAX_AREA slots
// bound to one engine, with no workspace dimension at all -- its print() emits
// `Slot Cur Name`. WORKDESK sits ABOVE it and changes nothing about it.
//
// IT IS NOT A DESKTOP. No windows, no focus, no z-order, no visual anything.
// "Desk" is the collective noun for the workspaces a session has open, the way
// WorkAreaSet is the collective for the areas one workspace holds.
//
// TWO THINGS IT SETTLES THAT CALLERS OTHERWISE EACH GET WRONG:
//
//   1. ORDER. `handles()` walks a std::unordered_map, so its order is
//      UNSPECIFIED and may differ between two runs of the same session shape.
//      Any report built straight on it is non-deterministic and cannot be
//      asserted on. observe() sorts by handle ascending, which also puts
//      DEFAULT (handle 1) first, always.
//
//   2. INVARIANT I1. `owner_of_slot()` returns 0 when no workspace claims a
//      slot. Invariant I1 says an area belongs to exactly ONE workspace and
//      there is NO NULL, so for an OPEN area that answer is impossible.
//      observe() collects those slots in `orphan_open_slots` rather than
//      hiding them. It REPORTS the violation; it never repairs one.

#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace cli { namespace workdesk {

// One work area, as the desk sees it.
struct AreaView {
    int         engine_slot{-1};   // 0-based engine slot
    std::string name;              // DbArea::name(); empty when not open
    bool        open{false};
    bool        current{false};    // the engine's current area
};

// One workspace and the areas it holds.
struct WorkspaceView {
    std::uint64_t handle{0};
    std::string   name;
    std::uint64_t ws_id{0};        // 0 = no durable identity yet; legal ONLY for DEFAULT
    std::uint64_t parent{0};       // 0 = this workspace is a root, NOT "no workspace"
    int           depth{0};
    bool          current{false};  // handle == workspace::current_handle()
    bool          is_default{false};

    // R131 environment. Empty means NOT STAMPED YET, which is true of exactly
    // one entry -- DEFAULT, which exists before any command runs. These are
    // strings the table HOLDS and cannot RESOLVE.
    bool        roots_stamped{false};
    std::string dbf_root;
    std::string idx_root;
    std::string lmdb_root;

    std::vector<AreaView> areas;      // ascending by engine slot
    std::size_t           open_areas{0};
};

// One table name resolving to more than one open area. The manual calls this
// "the case a global registry cannot represent", and it is SUPPORTED -- `USE
// <t> AGAIN` asks for it on purpose. Recorded as a fact, never as an error.
struct NameFanout {
    std::string                name;    // upper-cased
    std::vector<int>           slots;   // ascending
    std::vector<std::uint64_t> handles; // owning workspace, parallel to slots
};

// The whole desk.
struct Desk {
    std::vector<WorkspaceView> workspaces;   // ascending by handle; DEFAULT first
    std::uint64_t current_handle{0};
    int           current_engine_area{-1};
    bool          recursion_enabled{false};
    int           max_workspace_depth{0};    // the build vector, not a guess

    std::size_t workspace_count{0};
    std::size_t open_area_count{0};

    // Observed, never repaired. See I1 above.
    std::vector<int>        orphan_open_slots;
    std::vector<NameFanout> name_fanout;

    bool healthy() const noexcept { return orphan_open_slots.empty(); }
};

// Walk the workspace table and the engine's areas once, and return the join.
// Read-only: no command runs, no cursor moves, no state is stamped.
Desk observe();

}} // namespace cli::workdesk
