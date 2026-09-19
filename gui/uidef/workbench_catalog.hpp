// @dottalk.file v1
// subsystem: gui
// layer: service
// owns: saved catalog immutable inspection model
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#pragma once
#include "dottalk/minidb.hpp"
#include <filesystem>
#include <map>
#include <stop_token>
#include <string>
#include <vector>

namespace dottalk::workbench {
enum class CatalogAction { None, LoadDefinition, Hydrate };
bool is_workspace_definition(const std::string& payload);
struct SavedWorkspace {
    std::uint64_t id{}, parent_id{}, previous_id{}, record{};
    bool superseded{};
    std::map<std::string, std::string> fields;
    std::string payload, error;
    minidb::Scan container;
    std::string value(const std::string& field) const;
    CatalogAction action() const;
    std::string action_note() const;
};
struct CatalogSnapshot {
    std::filesystem::path path;
    std::vector<SavedWorkspace> entries;
    std::size_t deleted{};
    std::string code, error;
    bool ok() const { return error.empty(); }
};
// Uses private file copies because DbArea/MemoStore do not offer read-only opens.
// Calls no workspace command, creates no live workspace and hydrates no container.
CatalogSnapshot inspect_catalog(const std::filesystem::path&, std::stop_token = {});
// Parent links are durable WS_IDs. PREV_ID is never used as a nesting edge.
std::vector<std::pair<std::size_t, unsigned>> catalog_order(const CatalogSnapshot&);
}
