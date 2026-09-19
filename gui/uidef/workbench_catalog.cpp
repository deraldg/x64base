// @dottalk.file v1
// subsystem: gui
// layer: service
// owns: inspect_catalog
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_catalog.hpp"
#include "xbase.hpp"
#include "memo/memostore.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <fstream>
#include <functional>
#include <set>
#include <stdexcept>

namespace dottalk::workbench {
namespace fs = std::filesystem;
namespace {
std::string trim(std::string s) {
    const auto b = s.find_first_not_of(" \t\r\n\0", 0, 5);
    if (b == std::string::npos) return {};
    return s.substr(b, s.find_last_not_of(" \t\r\n\0", std::string::npos, 5) - b + 1);
}
std::uint64_t number(const std::string& s) {
    if (s.empty()) return 0;
    std::size_t used{};
    const auto n = std::stoull(s, &used);
    if (used != s.size() || s.front() == '-') throw std::runtime_error("Invalid catalog identity: " + s);
    return n;
}
struct Stamp {
    std::uintmax_t size;
    fs::file_time_type modified;
    bool operator==(const Stamp&) const = default;
};
Stamp stamp(const fs::path& p) { return {fs::file_size(p), fs::last_write_time(p)}; }
struct PrivateCopy {
    fs::path dir;
    PrivateCopy() {
        static std::atomic<unsigned> serial{};
        const auto tick = std::chrono::steady_clock::now().time_since_epoch().count();
        for (unsigned attempt = 0; attempt < 100; ++attempt) {
            auto p = fs::temp_directory_path() /
                ("arctictalk-catalog-" + std::to_string(tick) + "-" + std::to_string(serial++));
            if (fs::create_directory(p)) { dir = std::move(p); return; }
        }
        throw std::runtime_error("Cannot allocate private catalog copy");
    }
    ~PrivateCopy() {
        std::error_code ec;
        // Only files this object creates; never recursively remove an input path.
        fs::remove(dir / "CATALOG.dbf", ec);
        fs::remove(dir / "CATALOG.dtx", ec);
        fs::remove(dir, ec);
    }
};
void check_cancel(std::stop_token stop) {
    if (stop.stop_requested()) throw std::runtime_error("Catalog inspection cancelled");
}
}
std::string SavedWorkspace::value(const std::string& field) const {
    const auto it = fields.find(field);
    return it == fields.end() ? std::string{} : it->second;
}
bool is_workspace_definition(const std::string& payload) {
    if (payload.find('\0') != std::string::npos) return false;
    const auto header = trim(payload.substr(0, payload.find('\n')));
    return header == "DTSHEMA 2" || header == "DTSHEMA 3";
}
CatalogAction SavedWorkspace::action() const {
    if (!error.empty() || value("FMT") == "BIRTH 1") return CatalogAction::None;
    if (container.ok) return CatalogAction::Hydrate;
    if (is_workspace_definition(payload)) return CatalogAction::LoadDefinition;
    return CatalogAction::None;
}
std::string SavedWorkspace::action_note() const {
    const auto version = superseded ? "Historical version. " : "";
    if (action() == CatalogAction::Hydrate)
        return std::string(version) + "Hydrate this exact saved image into a new RAM workspace. Memo sidecars remain on disk.";
    if (action() == CatalogAction::LoadDefinition)
        return std::string(version) + "Load this exact saved definition using its table files. Choose their location in the next dialog.";
    if (!error.empty()) return "Unavailable: " + error;
    if (value("FMT") == "BIRTH 1") return "Birth record only: no saved definition or database image to load.";
    return payload.empty() ? "No saved payload to load." : "This saved payload format cannot be loaded here.";
}
CatalogSnapshot inspect_catalog(const fs::path& input, std::stop_token stop) {
    CatalogSnapshot result;
    result.code = "gui.catalog.failed";
    try {
        result.path = fs::absolute(input);
        check_cancel(stop);
        const auto before = stamp(result.path);
        if (before.size > 64 * 1024 * 1024) throw std::runtime_error("Catalog exceeds this inspector's 64 MiB limit");
        auto memo_path = result.path;
        memo_path.replace_extension(".dtx");
        if (!fs::exists(memo_path)) { memo_path.replace_extension(".DTX"); }
        const bool has_memo = fs::exists(memo_path);
        const auto memo_before = has_memo ? stamp(memo_path) : Stamp{};
        if (memo_before.size > 256 * 1024 * 1024) throw std::runtime_error("Memo sidecar exceeds this inspector's 256 MiB limit");
        PrivateCopy copy;
        fs::copy_file(result.path, copy.dir / "CATALOG.dbf");
        if (has_memo) fs::copy_file(memo_path, copy.dir / "CATALOG.dtx");
        if (!(before == stamp(result.path)) ||
            (has_memo && !(memo_before == stamp(memo_path))))
            throw std::runtime_error("Catalog changed while copying; refresh to retry");
        check_cancel(stop);
        xbase::DbArea area;
        area.open((copy.dir / "CATALOG.dbf").string());
        std::set<std::string> names;
        for (const auto& f : area.fields()) names.insert(f.name);
        for (const auto* required : {"WS_ID", "WS_NAME", "FMT", "SNAPSHOT", "SUPERSEDED"})
            if (!names.count(required)) throw std::runtime_error(std::string("Not a workspace catalog: missing ") + required);
        memo::MemoStore store;
        std::string memo_error;
        if (has_memo) {
            const auto opened = store.open((copy.dir / "CATALOG.dtx").string(), memo::OpenMode::OpenExisting);
            if (!opened.ok) memo_error = opened.error;
        } else memo_error = "Catalog memo sidecar is missing";
        std::set<std::uint64_t> ids;
        std::size_t total_payload{};
        for (std::uint64_t rec = 1; rec <= area.recCount64(); ++rec) {
            check_cancel(stop);
            if (!area.gotoRec64(rec)) throw std::runtime_error("Cannot read catalog record " + std::to_string(rec));
            if (area.isDeleted()) { ++result.deleted; continue; }
            SavedWorkspace row;
            row.record = rec;
            int field = 1;
            for (const auto& f : area.fields()) row.fields[f.name] = trim(area.get(field++));
            row.id = number(row.value("WS_ID"));
            row.parent_id = number(row.value("PARENT_ID"));
            row.previous_id = number(row.value("PREV_ID"));
            row.superseded = row.value("SUPERSEDED") == "1";
            if (!row.id || !ids.insert(row.id).second) throw std::runtime_error("Missing or duplicate WS_ID in catalog");
            const auto token = row.value("SNAPSHOT");
            if (!token.empty() && token != "0000000000000000") {
                if (!memo_error.empty()) row.error = memo_error;
                else {
                    auto payload = store.get_text(memo::MemoRef{token});
                    if (!payload.ok) row.error = payload.error;
                    else {
                        total_payload += payload.text.size();
                        if (total_payload > 128 * 1024 * 1024) throw std::runtime_error("Payload preview exceeds 128 MiB limit");
                        row.payload = std::move(payload.text);
                        if (minidb::is_container(row.payload)) {
                            row.container = minidb::scan(row.payload);
                            if (!row.container.ok) row.error = row.container.error;
                        } else if (row.value("FMT") == "MINIDB 1") row.error = "Declared MINIDB payload has no MINIDB header";
                    }
                }
            } else if (row.value("FMT") == "MINIDB 1") row.error = "MINIDB record has no snapshot reference";
            result.entries.push_back(std::move(row));
        }
        result.code = "gui.catalog.ready";
    } catch (const std::exception& e) {
        result.entries.clear();
        result.error = e.what();
        if (stop.stop_requested()) result.code = "gui.catalog.cancelled";
    }
    return result;
}
std::vector<std::pair<std::size_t, unsigned>> catalog_order(const CatalogSnapshot& s) {
    std::vector<std::pair<std::size_t, unsigned>> out;
    std::map<std::uint64_t, std::vector<std::size_t>> children;
    std::set<std::uint64_t> ids;
    for (const auto& e : s.entries) ids.insert(e.id);
    for (std::size_t i = 0; i < s.entries.size(); ++i) children[s.entries[i].parent_id].push_back(i);
    std::set<std::size_t> visited;
    std::function<void(std::size_t, unsigned)> visit = [&](std::size_t i, unsigned depth) {
        if (!visited.insert(i).second) return;
        out.emplace_back(i, depth);
        if (depth < 32) for (auto child : children[s.entries[i].id]) visit(child, depth + 1);
    };
    for (std::size_t i = 0; i < s.entries.size(); ++i)
        if (!s.entries[i].parent_id || !ids.count(s.entries[i].parent_id)) visit(i, 0);
    // Cycles/over-depth rows remain visible; do not silently lose damaged records.
    for (std::size_t i = 0; i < s.entries.size(); ++i) visit(i, 0);
    return out;
}
}
