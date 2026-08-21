// @dottalk.file v1
// subsystem: gui
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "gui/core/gui_workspace_format.hpp"

#include <algorithm>
#include <iomanip>
#include <sstream>
#include <vector>

namespace dottalk::gui {

namespace {

std::string visible_area_id(AreaId id) {
    return id == 0 ? std::string("none") : std::to_string(id - 1);
}

} // namespace

std::string format_workspace_graph_text(const ListAreasResult& areas,
                                        const std::string& title,
                                        const std::string& no_open_areas_text) {
    std::ostringstream graph;
    graph << title << "\n\n";
    graph << "Areas: " << areas.areas.size() << "\n";
    graph << "Active area: " << visible_area_id(areas.active_area_id) << "\n\n";

    if (areas.areas.empty()) {
        graph << no_open_areas_text << "\n";
    } else {
        graph << "Areas\n";
        for (const auto& area : areas.areas) {
            graph << (area.active ? "* " : "  ")
                  << visible_area_id(area.area_id) << "  "
                  << area.display_name << "\n"
                  << "    table: " << area.path.string() << "\n"
                  << "    records: " << area.record_count << "\n"
                  << "    fields: " << area.field_count << "\n";
        }
    }

    graph << "\n";
    graph << "Relations: workspace graph service pending\n";
    graph << "Indexes: workspace graph service pending\n";
    graph << "Browsers/lists: workspace graph service pending\n";
    graph << "ERSATZ presets: workspace graph service pending\n";
    graph << "DTSchema load/save: routed through DotTalk++ runtime schema commands; graph service pending\n";
    return graph.str();
}

std::string format_workspace_graph_text(const WorkspaceModel& model,
                                        const std::string& title,
                                        const std::string& no_open_areas_text) {
    // AIF-120. Grouped BY WORKSPACE, because that is the scope every page above
    // is keyed on and because the grouping keeps this view proportional to the
    // working set rather than to the address space -- MAX_AREA is a build vector
    // with no upper bound, so nothing here may enumerate slots.
    //
    // One line per table, not four. The previous shape restated the Tables grid
    // sitting directly above it at four lines each; the thing this view can show
    // that no grid does is STRUCTURE -- who owns what, and how the tables relate.
    std::ostringstream graph;
    graph << title << "\n\n";

    std::vector<std::string> order;
    for (const auto& area : model.tables) {
        if (std::find(order.begin(), order.end(), area.workspace) == order.end()) {
            order.push_back(area.workspace);
        }
    }
    if (order.empty()) {
        order.push_back(model.current_workspace);
    }

    graph << "Workspaces: " << order.size()
          << "    Current: " << model.current_workspace << "\n";
    graph << "Areas: " << model.tables.size()
          << "    Active area: " << visible_area_id(model.active_area_id) << "\n\n";

    if (model.tables.empty()) {
        graph << no_open_areas_text << "\n";
    }

    for (const auto& workspace : order) {
        std::size_t count = 0;
        for (const auto& area : model.tables) {
            if (area.workspace == workspace) ++count;
        }
        graph << workspace << " -- " << count << " area(s)\n";

        for (const auto& area : model.tables) {
            if (area.workspace != workspace) continue;
            graph << (area.active ? "  * " : "    ")
                  << std::setw(4) << std::left << visible_area_id(area.area_id)
                  << std::setw(22) << std::left << area.display_name
                  << std::setw(8) << std::right << area.record_count << " rec"
                  << std::setw(5) << std::right << area.field_count << " fld   "
                  << area.path.string() << "\n";
        }

        graph << "\n  Indexes\n";
        std::size_t shown = 0;
        for (const auto& index : model.indexes) {
            if (index.workspace != workspace) continue;
            ++shown;
            graph << "    " << visible_area_id(index.area_id) << "  "
                  << index.area_name << "  " << index.kind;
            if (index.active) {
                graph << "  " << index.container.string();
                if (!index.tag.empty()) {
                    graph << " TAG " << index.tag;
                }
                graph << (index.ascending ? " ASC" : " DESC");
            }
            graph << "  [" << index.backend << "]\n";
        }
        if (shown == 0) graph << "    none\n";

        graph << "\n  Relations\n";
        shown = 0;
        for (const auto& relation : model.relations) {
            if (relation.workspace != workspace) continue;
            ++shown;
            graph << "    " << relation.parent << " -> " << relation.child;
            if (!relation.parent_key.empty()) {
                graph << " ON " << relation.parent_key;
                // AIF-120 G3. A relation may bind DIFFERENTLY NAMED endpoints --
                // `ON EMPLOYEE_ID TO APPROVED_BY`, and one table related to
                // itself by `ON EMPLOYEE_ID TO REPORTS_TO`. Measured across the
                // live workspace catalog: 190 of 1,102 RELATION lines (17.2%)
                // carry an explicit TO. Rendering only the parent key is wrong
                // one time in six, and wrong in a way that reads as correct.
                if (!relation.child_key.empty() &&
                    relation.child_key != relation.parent_key) {
                    graph << " TO " << relation.child_key;
                }
            }
            if (relation.match_count > 0) {
                graph << "  (" << relation.match_count << " matches)";
            }
            graph << "\n";
        }
        if (shown == 0) graph << "    none\n";
        graph << "\n";
    }

    // Named rather than left vague. The three lines this replaces read
    // "workspace graph service pending" and had said so for a long time, which
    // tells a reader nothing about WHAT is missing or why.
    graph << "Not shown: the posture's own identity -- WSID, FLAVOR, and the\n";
    graph << "DBFROOT/IDXROOT/LMDBROOT residence roots. The GUI model does not\n";
    graph << "carry them yet, so a RAM-hydrated workspace is indistinguishable\n";
    graph << "here from a disk-resident one. That is the next slice, and until it\n";
    graph << "lands this view cannot tell you where a table actually lives.\n";
    return graph.str();
}

} // namespace dottalk::gui
