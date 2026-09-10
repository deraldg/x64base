// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: the WORKDESK observer implementation
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: experimental

// File: src/cli/workdesk.cpp
// Collective place for multi-workspaces.
//
// The header carries the reasoning. This file is the walk, and it is
// deliberately dull: read the workspace table, read the areas, join them,
// sort, and hand back a value. Every fact below comes from an existing
// accessor -- nothing here derives, infers, or repairs.

#include "cli/workdesk.hpp"

#include <algorithm>
#include <cctype>
#include <unordered_map>

#include "xbase.hpp"
#include "xbase/workspace_membership.hpp"
#include "workareas.hpp"

namespace cli { namespace workdesk {

namespace {

std::string upper_copy(const std::string& s) {
    std::string out = s;
    for (char& c : out) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return out;
}

} // namespace

Desk observe() {
    Desk desk;

    desk.current_handle       = xbase::workspace::current_handle();
    desk.recursion_enabled    = xbase::workspace::recursion_enabled();
    desk.max_workspace_depth  = xbase::workspace::kMaxWorkspaceDepth;

    const int current_area = static_cast<int>(workareas::current_slot());
    desk.current_engine_area = current_area;

    // ORDER. handles() walks an unordered_map; sort so two runs of the same
    // session shape produce the same desk. DEFAULT is handle 1 and lands first.
    std::vector<std::uint64_t> handles = xbase::workspace::handles();
    std::sort(handles.begin(), handles.end());

    // name -> every open area carrying it, for the fanout pass below.
    std::unordered_map<std::string, NameFanout> fanout;

    for (const std::uint64_t h : handles) {
        WorkspaceView ws;
        ws.handle     = h;
        ws.name       = xbase::workspace::name_of(h);
        ws.ws_id      = xbase::workspace::ws_id_of(h);
        ws.parent     = xbase::workspace::parent_of(h);
        ws.depth      = xbase::workspace::depth_of(h);
        ws.current    = (h == desk.current_handle);
        ws.is_default = (h == xbase::workspace::kDefaultHandle);

        ws.roots_stamped = xbase::workspace::roots_stamped(h);
        xbase::workspace::roots_of(h, ws.dbf_root, ws.idx_root, ws.lmdb_root);

        std::vector<std::int32_t> members = xbase::workspace::members(h);
        std::sort(members.begin(), members.end());

        for (const std::int32_t slot : members) {
            AreaView av;
            av.engine_slot = static_cast<int>(slot);
            av.current     = (av.engine_slot == current_area);

            // db() and not db_const(): DbArea::isOpen()/name() are reached
            // through a non-const handle everywhere else in this tree
            // (workareas::WorkArea does the same from its own const methods),
            // and a const_cast here would be a worse way to say so.
            if (xbase::DbArea* area =
                    workareas::db(static_cast<std::size_t>(slot))) {
                av.open = area->isOpen();
                if (av.open) {
                    av.name = area->name();
                }
            }

            if (av.open) {
                ++ws.open_areas;
                ++desk.open_area_count;

                const std::string key = upper_copy(av.name);
                if (!key.empty()) {
                    NameFanout& f = fanout[key];
                    f.name = key;
                    f.slots.push_back(av.engine_slot);
                    f.handles.push_back(h);
                }
            }

            ws.areas.push_back(av);
        }

        desk.workspaces.push_back(std::move(ws));
    }

    desk.workspace_count = desk.workspaces.size();

    // INVARIANT I1. An open area with no owning workspace cannot legally
    // exist. Walk every engine slot, not the membership lists, because the
    // whole point is to find a slot the membership lists FORGOT.
    const std::size_t slot_count = workareas::count();
    for (std::size_t i = 0; i < slot_count; ++i) {
        xbase::DbArea* area = workareas::db(i);
        if (!area || !area->isOpen()) continue;
        if (xbase::workspace::owner_of_slot(static_cast<std::int32_t>(i)) == 0) {
            desk.orphan_open_slots.push_back(static_cast<int>(i));
        }
    }

    // One name, more than one open area. Supported and deliberate; reported so
    // a caller can qualify rather than take first-wins by accident.
    for (auto& kv : fanout) {
        if (kv.second.slots.size() > 1) {
            desk.name_fanout.push_back(std::move(kv.second));
        }
    }
    std::sort(desk.name_fanout.begin(), desk.name_fanout.end(),
              [](const NameFanout& a, const NameFanout& b) { return a.name < b.name; });

    return desk;
}

}} // namespace cli::workdesk
