#include "gui/core/gui_workspace_format.hpp"

#include <sstream>

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
    std::ostringstream graph;
    graph << title << "\n\n";
    graph << "Areas: " << model.tables.size() << "\n";
    graph << "Active area: " << visible_area_id(model.active_area_id) << "\n\n";

    if (model.tables.empty()) {
        graph << no_open_areas_text << "\n";
    } else {
        graph << "Tables\n";
        for (const auto& area : model.tables) {
            graph << (area.active ? "* " : "  ")
                  << visible_area_id(area.area_id) << "  "
                  << area.display_name << "\n"
                  << "    table: " << area.path.string() << "\n"
                  << "    records: " << area.record_count << "\n"
                  << "    fields: " << area.field_count << "\n";
        }
    }

    graph << "\nIndexes\n";
    if (model.indexes.empty()) {
        graph << "  none\n";
    } else {
        for (const auto& index : model.indexes) {
            graph << "  " << visible_area_id(index.area_id) << " "
                  << index.area_name << "  " << index.kind;
            if (index.active) {
                graph << " " << index.container.string();
                if (!index.tag.empty()) {
                    graph << " TAG " << index.tag;
                }
                graph << (index.ascending ? " ASC" : " DESC");
            }
            graph << " [" << index.backend << "]\n";
        }
    }

    graph << "\nRelations\n";
    if (model.relations.empty()) {
        graph << "  none\n";
    } else {
        for (const auto& relation : model.relations) {
            graph << "  " << relation.parent << " -> " << relation.child;
            if (!relation.parent_key.empty()) {
                graph << " ON " << relation.parent_key;
            }
            if (relation.match_count > 0) {
                graph << " (" << relation.match_count << " matches)";
            }
            graph << "\n";
        }
    }

    graph << "\nBrowsers/lists: workspace graph service pending\n";
    graph << "ERSATZ presets: runtime output available; visual presets pending\n";
    graph << "DTSchema load/save: routed through DotTalk++ runtime schema commands; graph service pending\n";
    return graph.str();
}

} // namespace dottalk::gui
