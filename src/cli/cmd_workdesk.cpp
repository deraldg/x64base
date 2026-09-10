// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: the WORKDESK verb
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: experimental

// ================================
// FILE: src/cli/cmd_workdesk.cpp
// ================================

// @dottalk.usage v1
// owner: DOT|WORKDESK
// command: WORKDESK
// category: diagnostics
// status: experimental
// noargs: report
// effect: report
// mutates: none
// usage-access: WORKDESK USAGE
// summary:
//   Report the desk -- every open workspace in this session with its areas,
//   identity, lineage and roots.
//
// usage:
//   WORKDESK
//   WORKDESK USAGE
//
// notes:
//   WORKDESK is the collective term for the OPEN WORKSPACES in a session, the
//   way a workspace is the collective for the AREAS it holds. IT IS NOT A
//   DESKTOP: no windows, no focus, no z-order, nothing visual.
//   WORKDESK is read-only. It reports an invariant violation; it repairs none.
//   The same section appears inside WSREPORT, rendered from the same call, so
//   the two cannot drift. WORKDESK is the verb for when that section is all
//   you want.
//   WORKSPACE REGISTRY answers WHICH AREAS BELONG WHERE and is not this; it
//   prints no roots and does not name the areas' tables.
//
// risk:
//   reads_workspace_state: yes except usage
//   writes_console: yes
//   mutates_table_data: no
//
// related:
//   WORKSPACE
//   WSREPORT
//   AREA
//

// Collective place for multi-workspaces.
//
// The header carries the reasoning. This file is the walk, and it is
// deliberately dull: read the workspace table, read the areas, join them,
// sort, and hand back a value. Every fact below comes from an existing
// accessor -- nothing here derives, infers, or repairs.

#include "cli/cmd_workdesk.hpp"

#include <algorithm>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <vector>
#include <ostream>
#include <string>
#include <unordered_map>

#include "xbase.hpp"
#include "xbase/workspace_membership.hpp"
#include "workareas.hpp"
#include "cli/output_router.hpp"

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

// ---------------------------------------------------------------------------
// RENDER
//
// The section WSREPORT used to print under the heading "Workspace" while
// showing nothing but areas. Every line below names a workspace fact that the
// old block could not reach, because it never called into the workspace table
// at all.
// ---------------------------------------------------------------------------

namespace {

std::string or_none(const std::string& s) {
    return s.empty() ? std::string("(none)") : s;
}

} // namespace

void render(const Desk& desk, std::ostream& os) {
    os << "Workspaces\n";
    os << "----------------------------------------\n";
    os << "  Open        : " << desk.workspace_count << "\n";
    os << "  Open areas  : " << desk.open_area_count << "\n";
    os << "  Recursion   : " << (desk.recursion_enabled ? "ON" : "OFF") << "\n";
    os << "  Max depth   : " << desk.max_workspace_depth << "\n";
    // CURRENT WORKSPACE AND CURRENT AREA ARE TWO DIFFERENT FACTS, and the
    // first run of this report proved they need saying separately: after
    // WORKSPACE SWITCH x32 the current workspace was x32 while the current
    // area was still 0, which belongs to DEFAULT. That is LEGAL -- SWITCH
    // moves the workspace, never the cursor -- and it means a bare command
    // then operates on a DEFAULT table while the session stands in x32.
    // Printing only "Current area" left the reader to infer the divergence
    // from an asterisk further down.
    const WorkspaceView* cur_ws = nullptr;
    for (const WorkspaceView& w : desk.workspaces) {
        if (w.current) { cur_ws = &w; break; }
    }

    os << "  Current ws  : ";
    if (cur_ws) os << cur_ws->name << " (handle " << cur_ws->handle << ")\n";
    else        os << "(none)\n";

    os << "  Current area: ";
    if (desk.current_engine_area >= 0) {
        os << desk.current_engine_area;
        const std::uint64_t owner =
            (desk.current_engine_area >= 0)
                ? xbase::workspace::owner_of_slot(
                      static_cast<std::int32_t>(desk.current_engine_area))
                : 0;
        if (cur_ws && owner != 0 && owner != cur_ws->handle) {
            os << "  -- NOTE: area " << desk.current_engine_area
               << " belongs to workspace " << owner
               << ", not to the current workspace";
        }
        os << "\n";
    } else {
        os << "(none)\n";
    }
    os << "\n";

    for (const WorkspaceView& ws : desk.workspaces) {
        os << "  " << (ws.current ? "*" : " ") << " "
           << ws.name << "  (handle " << ws.handle;

        // 0 means NO DURABLE IDENTITY YET, which is legal for exactly one
        // workspace. Printing a bare 0 would read as an id.
        os << ", ws_id ";
        if (ws.ws_id != 0) os << ws.ws_id;
        else               os << "unallocated";

        // parent 0 is ROOT, not "no workspace". Say which.
        os << ", ";
        if (ws.parent != 0) os << "parent " << ws.parent;
        else                os << "root";

        os << ", depth " << ws.depth << ")\n";

        // Empty roots mean NOT STAMPED YET -- true of DEFAULT before anything
        // asks. That is a different statement from "this workspace has no
        // roots", so it is spelled out rather than shown as three blanks.
        if (ws.roots_stamped) {
            os << "      roots  : dbf " << or_none(ws.dbf_root)
               << " | idx " << or_none(ws.idx_root)
               << " | lmdb " << or_none(ws.lmdb_root) << "\n";
        } else {
            os << "      roots  : not stamped yet\n";
        }

        if (ws.areas.empty()) {
            os << "      areas  : none\n";
        } else {
            os << "      areas  : " << ws.open_areas << " open of "
               << ws.areas.size() << " claimed\n";
            for (const AreaView& a : ws.areas) {
                os << "        " << std::setw(3) << a.engine_slot
                   << (a.current ? " *" : "  ")
                   << " " << (a.open ? or_none(a.name) : "(closed)") << "\n";
            }
        }
        os << "\n";
    }

    // One table, more than one open area. SUPPORTED and deliberate -- `USE <t>
    // AGAIN` asks for it. Reported so a caller qualifies on purpose instead of
    // taking first-wins by accident.
    if (!desk.name_fanout.empty()) {
        os << "  Names open in more than one area\n";
        for (const NameFanout& f : desk.name_fanout) {
            os << "    " << f.name << " :";
            for (std::size_t i = 0; i < f.slots.size(); ++i) {
                os << " (ws " << (i < f.handles.size() ? f.handles[i] : 0)
                   << " area " << f.slots[i] << ")";
            }
            os << "\n";
        }
        os << "  Not an error. First-wins is a migration step, not a promise --\n"
              "  qualify the name.\n\n";
    }

    // INVARIANT I1. Loud, and it says what it means rather than printing a
    // number somebody has to look up.
    if (!desk.orphan_open_slots.empty()) {
        os << "  INVARIANT I1 VIOLATED: open area(s) owned by no workspace:";
        for (const int slot : desk.orphan_open_slots) os << " " << slot;
        os << "\n"
              "  An area belongs to exactly ONE workspace and there is no null.\n"
              "  This is reported, not repaired. Nothing here changed it.\n\n";
    }
}

}} // namespace cli::workdesk

// ---------------------------------------------------------------------------
// COMMAND
// ---------------------------------------------------------------------------

namespace {

std::string upper_token(std::string s) {
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

} // namespace

void cmd_WORKDESK(xbase::DbArea&, std::istringstream& args) {
    // Everything leaves through the router. WSREPORT carried a second, console
    // only copy of its own usage for a while and the two disagreed about
    // whether SET ALTERNATE saw them; there is one path here from the start.
    auto& out = cli::OutputRouter::instance().out();

// THE ARGUMENT STREAM IS PAST THE VERB; ITS BUFFER IS NOT.
//
// shell_api.cpp builds one istringstream over the whole line, reads the verb
// out of it, and hands the SAME stream to the handler -- so `args >> tok`
// yields the first ARGUMENT, while `args.str()` yields the WHOLE LINE with the
// verb still on the front.
//
// This has now cost twice. cmd_wsreport.cpp carried two usage checks: a
// `_hotfix` pair reading the stream (which worked) and a router-bound pair
// comparing args.str() to "USAGE" (which could not). On 2026-09-11 the two
// were "consolidated" onto the buffer -- the broken half -- and WSREPORT USAGE
// stopped working; WORKDESK USAGE was written the same way the same hour and
// answered "unknown argument 'workdesk'" on its first run. The duplicate was
// real, and the copy that was kept was the wrong one.
//
// Read the STREAM. Never the buffer.
    std::vector<std::string> toks;
    {
        std::string t;
        while (args >> t) toks.push_back(upper_token(t));
    }

    const std::string u = toks.empty() ? std::string() : toks.front();

    if (u == "USAGE" || u == "HELP" || u == "?") {
        out << "Usage:\n"
            << "  WORKDESK\n"
            << "  WORKDESK USAGE\n"
            << "Notes:\n"
            << "  - WORKDESK reports every OPEN WORKSPACE and the areas it holds.\n"
            << "  - It is a collective noun, not a desktop. Nothing visual.\n"
            << "  - Read-only. An invariant violation is reported, never repaired.\n"
            << "  - The same section appears inside WSREPORT, from the same call.\n";
        out.flush();
        return;
    }

    if (!u.empty()) {
        out << "WORKDESK: unknown argument '" << toks.front() << "'.\n"
            << "  WORKDESK takes no arguments yet. Try WORKDESK or WORKDESK USAGE.\n";
        out.flush();
        return;
    }

    cli::workdesk::render(cli::workdesk::observe(), out);
    out.flush();
}
