#pragma once
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <string>
#include <unordered_map>
#include <vector>
namespace dottalk::datadict {
using DDictRow = std::unordered_map<std::string, std::string>;
struct FieldDef { std::string name; char type = 'C'; std::size_t width = 0; };
std::vector<unsigned char> read_binary(const std::filesystem::path& path);
std::vector<FieldDef> parse_fields(const std::vector<unsigned char>& data);
std::vector<DDictRow> read_dbf_table(const std::filesystem::path& catalog_dir, const std::string& table_name);
} // namespace dottalk::datadict
