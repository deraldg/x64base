#pragma once
// @dottalk.contract v1
// component: extension_manifest
// role: read-only document-control manifest model for future DotTalk++ exits
// owner: DotTalk++ CLI extension lane
// docs: docs/contracts/DOTTALK_EXTENSION_EXIT_CONTRACT_V1.md
// safety: parses and validates manifest metadata only; does not execute extension entries
// @dottalk.contract.end

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace dottalk::extensions {

struct ManifestDiagnostic {
    enum class Severity {
        Info,
        Warning,
        Error,
    };

    Severity severity{Severity::Info};
    std::string message;
};

struct ManifestEntry {
    std::string id;
    std::string point;
    std::string kind;
    std::string language;
    std::string entry;
    bool enabled{false};
    std::optional<int> timeout_ms;
    std::string owner;
    std::string state;
    std::string usage_contract;
    std::string evidence;
};

struct Manifest {
    int api{0};
    std::string status;
    std::vector<ManifestEntry> entries;
    std::vector<ManifestDiagnostic> diagnostics;

    bool ok() const noexcept;
    std::size_t error_count() const noexcept;
    std::size_t warning_count() const noexcept;
};

std::filesystem::path default_exit_root();
std::filesystem::path default_manifest_path();

Manifest load_manifest(const std::filesystem::path& path);

const ManifestEntry* find_entry(const Manifest& manifest, const std::string& id);
const char* to_string(ManifestDiagnostic::Severity severity) noexcept;

} // namespace dottalk::extensions
