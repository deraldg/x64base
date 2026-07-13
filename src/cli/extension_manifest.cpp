#include "extension_manifest.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <optional>
#include <string>
#include <string_view>
#include <system_error>

#include <nlohmann/json.hpp>

#include "common/path_state.hpp"
#include "textio.hpp"
#include "user_scope_paths.hpp"

namespace fs = std::filesystem;
using nlohmann::json;

namespace dottalk::extensions {

namespace {

static void add_diag(Manifest& manifest,
                     ManifestDiagnostic::Severity severity,
                     std::string message)
{
    manifest.diagnostics.push_back(ManifestDiagnostic{severity, std::move(message)});
}

static bool is_one_of(const std::string& value, std::initializer_list<std::string_view> allowed)
{
    return std::any_of(allowed.begin(), allowed.end(),
        [&](std::string_view item) { return value == item; });
}

static std::string get_string(const json& object, const char* key)
{
    const auto it = object.find(key);
    if (it == object.end() || !it->is_string()) return {};
    return it->get<std::string>();
}

static bool get_bool(const json& object, const char* key, bool fallback)
{
    const auto it = object.find(key);
    if (it == object.end() || !it->is_boolean()) return fallback;
    return it->get<bool>();
}

static std::optional<int> get_int(const json& object, const char* key)
{
    const auto it = object.find(key);
    if (it == object.end() || !it->is_number_integer()) return std::nullopt;
    return it->get<int>();
}

static std::string up(std::string value)
{
    return textio::up(textio::trim(std::move(value)));
}

static bool starts_with_custom_prefix(const std::string& id)
{
    const std::string u = up(id);
    return u.rfind("Z_", 0) == 0 ||
           u.rfind("Y_", 0) == 0 ||
           u.rfind("STU_", 0) == 0;
}

static bool has_parent_reference(const fs::path& path)
{
    for (const auto& part : path) {
        if (part == "..") return true;
    }
    return false;
}

static bool looks_like_exit_root(const fs::path& path)
{
    std::error_code ec;
    return fs::exists(path / "exits.json", ec) || fs::exists(path / "README.md", ec);
}

static std::optional<fs::path> find_workspace_exit_root(fs::path start)
{
    if (start.empty()) return std::nullopt;

    std::error_code ec;
    start = fs::absolute(start, ec).lexically_normal();
    if (ec) return std::nullopt;

    if (fs::is_regular_file(start, ec)) start = start.parent_path();
    ec.clear();

    for (fs::path probe = start; !probe.empty(); probe = probe.parent_path()) {
        const fs::path candidate = probe / "dottalkpp" / "user" / "exits";
        if (looks_like_exit_root(candidate)) return candidate;

        if (probe == probe.root_path() || probe.parent_path() == probe) break;
    }

    return std::nullopt;
}

static void validate_entry(Manifest& manifest, const ManifestEntry& entry, std::size_t index)
{
    const std::string where = "entry[" + std::to_string(index) + "]";

    if (textio::trim(entry.id).empty()) {
        add_diag(manifest, ManifestDiagnostic::Severity::Error, where + ": missing id");
    } else if (!starts_with_custom_prefix(entry.id)) {
        add_diag(manifest, ManifestDiagnostic::Severity::Warning,
                 where + ": id should use Z_, Y_, or STU_ custom namespace");
    }

    if (!is_one_of(entry.point, {
        "startup.after",
        "shutdown.before",
        "command.before",
        "command.after",
        "command.error",
        "command.unknown",
        "timer.after"
    })) {
        add_diag(manifest, ManifestDiagnostic::Severity::Error,
                 where + ": unknown exit point '" + entry.point + "'");
    }

    if (!is_one_of(entry.kind, {"cpp-static", "cpp-dll", "process", "document"})) {
        add_diag(manifest, ManifestDiagnostic::Severity::Error,
                 where + ": unknown kind '" + entry.kind + "'");
    }

    if (entry.entry.empty()) {
        add_diag(manifest, ManifestDiagnostic::Severity::Error, where + ": missing entry path");
    } else {
        fs::path p(entry.entry);
        if (p.is_absolute() || has_parent_reference(p)) {
            add_diag(manifest, ManifestDiagnostic::Severity::Error,
                     where + ": entry must be a relative path inside dottalkpp/user/exits");
        }
    }

    if (entry.kind == "process") {
        if (!entry.timeout_ms.has_value() || *entry.timeout_ms <= 0) {
            add_diag(manifest, ManifestDiagnostic::Severity::Error,
                     where + ": process entries require timeout_ms > 0");
        }
        if (entry.enabled) {
            add_diag(manifest, ManifestDiagnostic::Severity::Warning,
                     where + ": process execution is not implemented; enabled=true is document-control only");
        }
    }

    if (!entry.state.empty() &&
        !is_one_of(entry.state, {"intake", "curated", "tested", "disabled", "enabled-local", "retired", "rejected"})) {
        add_diag(manifest, ManifestDiagnostic::Severity::Warning,
                 where + ": unknown state '" + entry.state + "'");
    }

    if (!entry.usage_contract.empty() &&
        !is_one_of(entry.usage_contract, {"source", "manifest", "curated-doc", "none"})) {
        add_diag(manifest, ManifestDiagnostic::Severity::Warning,
                 where + ": unknown usage_contract '" + entry.usage_contract + "'");
    }
}

} // namespace

bool Manifest::ok() const noexcept
{
    return error_count() == 0;
}

std::size_t Manifest::error_count() const noexcept
{
    return static_cast<std::size_t>(std::count_if(diagnostics.begin(), diagnostics.end(),
        [](const ManifestDiagnostic& d) { return d.severity == ManifestDiagnostic::Severity::Error; }));
}

std::size_t Manifest::warning_count() const noexcept
{
    return static_cast<std::size_t>(std::count_if(diagnostics.begin(), diagnostics.end(),
        [](const ManifestDiagnostic& d) { return d.severity == ManifestDiagnostic::Severity::Warning; }));
}

fs::path default_exit_root()
{
    // Source-tree builds should prefer the checked-in document-control manifest
    // even when DATA/USER roots point at a local profile directory.
    try {
        if (auto root = find_workspace_exit_root(fs::path(__FILE__))) return *root;
    } catch (...) {
    }

    try {
        if (auto root = find_workspace_exit_root(fs::current_path())) return *root;
    } catch (...) {
    }

    try {
        const auto& state = paths::state();
        if (auto root = find_workspace_exit_root(state.bin_root)) return *root;
        if (auto root = find_workspace_exit_root(state.root)) return *root;
    } catch (...) {
    }

    try {
        return paths::get_slot(paths::Slot::USER) / "exits";
    } catch (...) {
    }

    try {
        return userpaths::user_root() / "exits";
    } catch (...) {
    }

    try {
        const fs::path cwd = fs::current_path();
        if (cwd.filename() == "dottalkpp") return cwd / "user" / "exits";
        return cwd / "dottalkpp" / "user" / "exits";
    } catch (...) {
        return fs::path("dottalkpp") / "user" / "exits";
    }
}

fs::path default_manifest_path()
{
    return default_exit_root() / "exits.json";
}

Manifest load_manifest(const fs::path& path)
{
    Manifest manifest;

    std::error_code ec;
    if (!fs::exists(path, ec)) {
        add_diag(manifest, ManifestDiagnostic::Severity::Warning,
                 "manifest not found: " + path.string());
        return manifest;
    }
    if (!fs::is_regular_file(path, ec)) {
        add_diag(manifest, ManifestDiagnostic::Severity::Error,
                 "manifest path is not a file: " + path.string());
        return manifest;
    }

    json root;
    try {
        std::ifstream in(path);
        root = json::parse(in, nullptr, true, true);
    } catch (const std::exception& ex) {
        add_diag(manifest, ManifestDiagnostic::Severity::Error,
                 std::string("manifest parse failed: ") + ex.what());
        return manifest;
    }

    if (!root.is_object()) {
        add_diag(manifest, ManifestDiagnostic::Severity::Error, "manifest root must be an object");
        return manifest;
    }

    if (const auto it = root.find("api"); it != root.end() && it->is_number_integer()) {
        manifest.api = it->get<int>();
    } else {
        add_diag(manifest, ManifestDiagnostic::Severity::Error, "manifest api must be an integer");
    }

    if (manifest.api != 1) {
        add_diag(manifest, ManifestDiagnostic::Severity::Error,
                 "manifest api must be 1 for this runtime");
    }

    manifest.status = get_string(root, "status");

    const auto entries_it = root.find("entries");
    if (entries_it == root.end()) {
        add_diag(manifest, ManifestDiagnostic::Severity::Error, "manifest entries array is missing");
        return manifest;
    }
    if (!entries_it->is_array()) {
        add_diag(manifest, ManifestDiagnostic::Severity::Error, "manifest entries must be an array");
        return manifest;
    }

    std::size_t index = 0;
    for (const auto& raw : *entries_it) {
        if (!raw.is_object()) {
            add_diag(manifest, ManifestDiagnostic::Severity::Error,
                     "entry[" + std::to_string(index) + "]: entry must be an object");
            ++index;
            continue;
        }

        ManifestEntry entry;
        entry.id = get_string(raw, "id");
        entry.point = get_string(raw, "point");
        entry.kind = get_string(raw, "kind");
        entry.language = get_string(raw, "language");
        entry.entry = get_string(raw, "entry");
        entry.enabled = get_bool(raw, "enabled", false);
        entry.timeout_ms = get_int(raw, "timeout_ms");
        entry.owner = get_string(raw, "owner");
        entry.state = get_string(raw, "state");
        entry.usage_contract = get_string(raw, "usage_contract");
        entry.evidence = get_string(raw, "evidence");

        validate_entry(manifest, entry, index);
        manifest.entries.push_back(std::move(entry));
        ++index;
    }

    return manifest;
}

const ManifestEntry* find_entry(const Manifest& manifest, const std::string& id)
{
    const std::string want = up(id);
    for (const auto& entry : manifest.entries) {
        if (up(entry.id) == want) return &entry;
    }
    return nullptr;
}

const char* to_string(ManifestDiagnostic::Severity severity) noexcept
{
    switch (severity) {
        case ManifestDiagnostic::Severity::Info: return "info";
        case ManifestDiagnostic::Severity::Warning: return "warning";
        case ManifestDiagnostic::Severity::Error: return "error";
    }
    return "unknown";
}

} // namespace dottalk::extensions
