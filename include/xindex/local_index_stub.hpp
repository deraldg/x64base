#pragma once
#include "xindex/common.hpp"
#include <cstdint>
#include <iosfwd>
#include <optional>
#include <string>
#include <vector>

namespace xbase { class DbArea; }

namespace xindex {

enum class LocalIndexFormat : uint32_t {
    SIX = 1,
    SCX = 2
};

enum LocalIndexFlags : uint32_t {
    LIF_NONE = 0u,
    LIF_DESC = 1u << 0
};

#pragma pack(push, 1)
struct LocalIndexHeader {
    char     family[4];        // "IDX"
    uint32_t format;           // LocalIndexFormat
    uint32_t version;          // kFileVersion
    Fingerprint fp{};
    uint32_t tag_count;        // 1 for SIX
    uint64_t tag_dir_offset;   // 0 for SIX
    uint64_t reserved0{0};
    uint64_t reserved1{0};
};

struct TagDesc {
    char     name[32];         // uppercase tag
    uint32_t field_index1;     // 1-based
    uint32_t flags;            // LocalIndexFlags
    uint64_t root_offset;      // start of serialized entries
    uint64_t entry_count;      // number of serialized entries
};
#pragma pack(pop)

struct SimpleEntry {
    std::string key;
    std::uint32_t recno{0};
};

bool write_six_create(const std::string& path,
                      const std::string& tag_name_upper,
                      std::uint32_t field_index1,
                      std::string* err = nullptr);

bool write_scx_create(const std::string& path,
                      std::string* err = nullptr);

bool scx_add_tag(const std::string& path,
                 const std::string& tag_name_upper,
                 std::uint32_t field_index1,
                 bool descending = false,
                 std::string* err = nullptr);

bool six_build_from_area(const std::string& path,
                         xbase::DbArea& area,
                         std::string* err = nullptr);

bool scx_build_from_area(const std::string& path,
                         xbase::DbArea& area,
                         std::string* err = nullptr);

bool six_info(const std::string& path, std::ostream& os, std::string* err = nullptr);
bool scx_info(const std::string& path, std::ostream& os, std::string* err = nullptr);
bool scx_tags(const std::string& path, std::ostream& os, std::string* err = nullptr);

bool load_six_recnos(const std::string& path,
                     std::vector<std::uint32_t>& out_recnos,
                     std::string* err = nullptr);

bool load_scx_recnos(const std::string& path,
                     const std::string& tag_name_upper,
                     std::vector<std::uint32_t>& out_recnos,
                     std::string* err = nullptr);

std::string upper_ascii_copy(std::string s);

} // namespace xindex
