#include "datadict/ddict_catalog_paths.hpp"
#include "datadict/ddict_read_helpers.hpp"

#include <array>
#include <system_error>

// DD-089C extraction preview only.
// This generated candidate is not installed or wired by DD-089C.

namespace dottalk::datadict {
namespace fs = std::filesystem;


namespace {
struct TableInfo {
    const char* name;
};

constexpr TableInfo kTables[] = {
    {"DDRUN"},
    {"DDBASE"},
    {"DDSOURCE"},
    {"DDOBJECT"},
    {"DDATTR"},
    {"DDEDGE"},
    {"DDEVID"},
    {"DDGATE"},
    {"DDREVIEW"},
    {"DDARTIF"},
    {"DDPROFILE"},
};
} // namespace

bool exists_quiet(const fs::path& p) {
    std::error_code ec;
    return fs::exists(p, ec);
}

std::uintmax_t size_quiet(const fs::path& p) {
    std::error_code ec;
    if (!fs::exists(p, ec) || !fs::is_regular_file(p, ec)) {
        return 0;
    }
    auto n = fs::file_size(p, ec);
    return ec ? 0 : n;
}

fs::path normalize_quiet(const fs::path& p) {
    std::error_code ec;
    auto c = fs::weakly_canonical(p, ec);
    return ec ? p : c;
}

std::vector<fs::path> base_roots() {
    std::vector<fs::path> roots;
    std::error_code ec;
    fs::path cwd = fs::current_path(ec);
    if (ec) {
        cwd = fs::path(".");
    }

    roots.push_back(cwd);
    roots.push_back(cwd / "..");
    roots.push_back(cwd / "../..");
    roots.push_back(cwd / "../../..");
    return roots;
}

std::vector<fs::path> catalog_candidates() {
    std::vector<fs::path> candidates;
    for (const auto& root : base_roots()) {
        candidates.push_back(root / "data" / "datadict");
        candidates.push_back(root / "data" / "metadata" / "datadict");
        candidates.push_back(root / "dottalkpp" / "data" / "metadata" / "datadict");
        candidates.push_back(root / "dottalkpp" / "data" / "datadict" / "datadict");
    }
    candidates.push_back(fs::path("data") / "metadata" / "datadict");
    candidates.push_back(fs::path("dottalkpp") / "data" / "metadata" / "datadict");
    candidates.push_back(fs::path("dottalkpp") / "data" / "datadict" / "datadict");
    return candidates;
}

fs::path find_catalog_dir() {
    for (const auto& c : catalog_candidates()) {
        if (exists_quiet(c)) {
            return normalize_quiet(c);
        }
    }
    return normalize_quiet(fs::path("dottalkpp") / "data" / "metadata" / "datadict");
}

fs::path find_cdx_file(const std::string& table_name) {
    std::string lower = lower_copy(table_name);
    std::string upper = upper_copy(table_name);
    for (const auto& root : base_roots()) {
        std::vector<fs::path> candidates{
                        root / "data" / "indexes" / "datadict" / (lower + ".cdx"),
            root / "data" / "indexes" / "datadict" / (upper + ".cdx"),
            root / "dottalkpp" / "data" / "indexes" / "datadict" / (lower + ".cdx"),
            root / "dottalkpp" / "data" / "indexes" / "datadict" / (upper + ".cdx"),
root / "data" / "indexes" / (lower + ".cdx"),
            root / "data" / "indexes" / (upper + ".cdx"),
            root / "dottalkpp" / "data" / "indexes" / (lower + ".cdx"),
            root / "dottalkpp" / "data" / "indexes" / (upper + ".cdx"),
            root / "indexes" / (lower + ".cdx"),
            root / "indexes" / (upper + ".cdx"),
        };
        for (const auto& p : candidates) {
            if (exists_quiet(p)) {
                return normalize_quiet(p);
            }
        }
    }
    return {};
}

fs::path find_lmdb_dir(const std::string& table_name) {
    std::string lower = lower_copy(table_name);
    std::string upper = upper_copy(table_name);
    for (const auto& root : base_roots()) {
        std::vector<fs::path> candidates{
                        root / "data" / "lmdb" / "datadict" / (lower + ".cdx.d"),
            root / "data" / "lmdb" / "datadict" / (upper + ".cdx.d"),
            root / "dottalkpp" / "data" / "lmdb" / "datadict" / (lower + ".cdx.d"),
            root / "dottalkpp" / "data" / "lmdb" / "datadict" / (upper + ".cdx.d"),
root / "data" / "lmdb" / (lower + ".cdx.d"),
            root / "data" / "lmdb" / (upper + ".cdx.d"),
            root / "dottalkpp" / "data" / "lmdb" / (lower + ".cdx.d"),
            root / "dottalkpp" / "data" / "lmdb" / (upper + ".cdx.d"),
            root / "lmdb" / (lower + ".cdx.d"),
            root / "lmdb" / (upper + ".cdx.d"),
        };
        for (const auto& p : candidates) {
            if (exists_quiet(p)) {
                return normalize_quiet(p);
            }
        }
    }
    return {};
}

CatalogStats collect_stats() {
    CatalogStats stats;
    stats.dir = find_catalog_dir();
    for (const auto& t : kTables) {
        fs::path dbf = stats.dir / (std::string(t.name) + ".dbf");
        fs::path dtx = stats.dir / (std::string(t.name) + ".dtx");
        if (exists_quiet(dbf)) {
            ++stats.dbf_present;
            stats.total_dbf_bytes += size_quiet(dbf);
        }
        if (exists_quiet(dtx)) {
            ++stats.dtx_present;
        }
    }
    return stats;
}

} // namespace dottalk::datadict
