// @dottalk.file v1
// subsystem: gui
// layer: service
// owns: workspace-scoped table snapshot projection
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_session.hpp"
#include <algorithm>
#include <cctype>
#include <map>
#include <set>
namespace dottalk::workbench {
namespace {
std::string search_text(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return value;
}
}
NavigatorView navigator_view(const SessionSnapshot& snapshot, const std::string& query) {
    NavigatorView result;
    auto filter = search_text(query);
    const auto first = filter.find_first_not_of(" \t\r\n");
    filter = first == std::string::npos ? "" : filter.substr(first, filter.find_last_not_of(" \t\r\n") - first + 1);
    std::map<std::uint64_t, std::uint64_t> parents;
    std::set<std::uint64_t> branches, visible;
    for (const auto& ws : snapshot.desk.workspaces) {
        parents[ws.handle] = ws.parent;
        if (filter.empty() || search_text(ws.name).find(filter) != std::string::npos) branches.insert(ws.handle);
    }
    bool added;
    do {
        added = false;
        for (const auto& ws : snapshot.desk.workspaces)
            if (branches.count(ws.parent) && branches.insert(ws.handle).second) added = true;
    } while (added);
    visible = branches;
    for (std::size_t i = 0; i < snapshot.areas.size(); ++i) {
        const auto& area = snapshot.areas[i];
        if (parents.count(area.workspace) && (branches.count(area.workspace) ||
            search_text(area.name).find(filter) != std::string::npos)) {
            result.areas.push_back(i); visible.insert(area.workspace);
        }
    }
    // Bound each ancestor walk independently; malformed cycles cannot hang UI.
    const auto matches = visible;
    for (auto id : matches) {
        std::set<std::uint64_t> seen;
        while (parents.count(id) && seen.insert(id).second) {
            visible.insert(id); id = parents.at(id);
        }
    }
    for (const auto& ws : snapshot.desk.workspaces)
        if (visible.count(ws.handle)) result.workspaces.push_back(ws.handle);
    return result;
}
AreaScope scope_areas(const SessionSnapshot& snapshot, std::uint64_t workspace,
                     bool all_workspaces, bool nested, const std::string& query) {
    AreaScope result;
    std::map<std::uint64_t, std::string> names;
    std::set<std::uint64_t> scope;
    for (const auto& ws : snapshot.desk.workspaces) {
        names[ws.handle] = search_text(ws.name);
        if (all_workspaces) scope.insert(ws.handle);
    }
    if (!all_workspaces) {
        if (!names.count(workspace)) { result.error = "Select an available workspace in the browser."; return result; }
        scope.insert(workspace);
        // A visited set bounds this walk even if an invalid snapshot contains
        // a cycle. Workdesk, not the browser, reports engine health problems.
        if (nested) {
            bool added;
            do {
                added = false;
                for (const auto& ws : snapshot.desk.workspaces)
                    if (scope.count(ws.parent) && scope.insert(ws.handle).second) added = true;
            } while (added);
        }
    }
    auto filter = search_text(query);
    const auto first = filter.find_first_not_of(" \t\r\n");
    filter = first == std::string::npos ? "" : filter.substr(first, filter.find_last_not_of(" \t\r\n") - first + 1);
    result.workspaces = scope.size();
    for (std::size_t i = 0; i < snapshot.areas.size(); ++i) {
        const auto& area = snapshot.areas[i];
        if (!scope.count(area.workspace)) continue;
        if (!filter.empty() && search_text(area.name).find(filter) == std::string::npos &&
            names[area.workspace].find(filter) == std::string::npos) continue;
        result.indices.push_back(i);
    }
    return result;
}
}
