#pragma once
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>
namespace dottalk::datadict {
struct CatalogStats { std::filesystem::path dir; int dbf_present = 0; int dtx_present = 0; std::uintmax_t total_dbf_bytes = 0; };
bool exists_quiet(const std::filesystem::path& path);
std::uintmax_t size_quiet(const std::filesystem::path& path);
std::filesystem::path normalize_quiet(const std::filesystem::path& path);
std::vector<std::filesystem::path> base_roots();
std::vector<std::filesystem::path> catalog_candidates();
std::filesystem::path find_catalog_dir();
std::filesystem::path find_cdx_file(const std::string& table_name);
std::filesystem::path find_lmdb_dir(const std::string& table_name);
CatalogStats collect_stats();
} // namespace dottalk::datadict
