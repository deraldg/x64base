// @dottalk.file v1
// subsystem: datadict
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

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
enum class TableReadState { Missing, Ready, Error };
struct TableReadResult {
    TableReadState state = TableReadState::Error;
    std::vector<FieldDef> fields;
    std::vector<DDictRow> rows;
    std::string logical_name;
    bool x64 = false;
    std::string error;
};
std::vector<unsigned char> read_binary(const std::filesystem::path& path);
std::vector<FieldDef> parse_fields(const std::vector<unsigned char>& data);
// Checked physical read. Memo cells retain their raw pointer bytes; catalog
// inspection resolves them using MemoStore's read-only API.
TableReadResult read_dbf_table_checked(const std::filesystem::path& catalog_dir,
                                      const std::string& table_name);
std::vector<DDictRow> read_dbf_table(const std::filesystem::path& catalog_dir, const std::string& table_name);
} // namespace dottalk::datadict
