#include "datadict/ddict_dbf_reader.hpp"
#include "datadict/ddict_read_helpers.hpp"

#include <fstream>

// DD-089C extraction preview only.
// This generated candidate is not installed or wired by DD-089C.

namespace dottalk::datadict {
namespace fs = std::filesystem;

bool plausible_name(const std::vector<unsigned char>& data, std::size_t off) {
    if (off + 11 > data.size()) {
        return false;
    }
    unsigned char first = data[off];
    if (!(std::isalpha(first) || first == '_')) {
        return false;
    }
    for (std::size_t i = off; i < off + 11 && data[i] != 0; ++i) {
        unsigned char ch = data[i];
        if (!(std::isalnum(ch) || ch == '_')) {
            return false;
        }
    }
    return true;
}

bool plausible_descriptor(const std::vector<unsigned char>& data, std::size_t off) {
    if (off + 32 > data.size() || data[off] == 0x0D || data[off] == 0x1A) {
        return false;
    }
    if (!plausible_name(data, off)) {
        return false;
    }
    char t = static_cast<char>(data[off + 11]);
    std::string allowed = "CDNLFIMBYT@GOVQ";
    return allowed.find(t) != std::string::npos;
}

std::size_t descriptor_start(const std::vector<unsigned char>& data) {
    if (plausible_descriptor(data, 96)) {
        return 96;
    }
    if (plausible_descriptor(data, 32)) {
        return 32;
    }
    const std::size_t limit = std::min<std::size_t>(data.size(), 512);
    for (std::size_t off = 0; off + 64 < limit; ++off) {
        if (plausible_descriptor(data, off) && plausible_descriptor(data, off + 32)) {
            return off;
        }
    }
    return static_cast<std::size_t>(-1);
}

std::uint16_t le16(const std::vector<unsigned char>& data, std::size_t off) {
    if (off + 2 > data.size()) {
        return 0;
    }
    return static_cast<std::uint16_t>(data[off] | (data[off + 1] << 8));
}

std::uint32_t le32(const std::vector<unsigned char>& data, std::size_t off) {
    if (off + 4 > data.size()) {
        return 0;
    }
    return static_cast<std::uint32_t>(data[off] | (data[off + 1] << 8) |
        (data[off + 2] << 16) | (data[off + 3] << 24));
}

std::string descriptor_name(const std::vector<unsigned char>& data, std::size_t off) {
    std::string s;
    for (std::size_t i = off; i < off + 11 && i < data.size() && data[i] != 0; ++i) {
        s.push_back(static_cast<char>(data[i]));
    }
    return upper_copy(trim_copy(s));
}

std::vector<unsigned char> read_binary(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        return {};
    }
    return std::vector<unsigned char>(std::istreambuf_iterator<char>(in), {});
}

std::vector<FieldDef> parse_fields(const std::vector<unsigned char>& data) {
    std::vector<FieldDef> fields;
    std::size_t start = descriptor_start(data);
    if (start == static_cast<std::size_t>(-1)) {
        return fields;
    }
    for (std::size_t off = start; off + 32 <= data.size(); off += 32) {
        if (data[off] == 0x0D || !plausible_descriptor(data, off)) {
            break;
        }
        FieldDef f;
        f.name = descriptor_name(data, off);
        f.type = static_cast<char>(data[off + 11]);
        f.width = data[off + 16];
        if (f.width == 0) {
            f.width = le16(data, off + 16);
        }
        if (!f.name.empty() && f.width > 0 && f.width < 4096) {
            fields.push_back(f);
        }
    }
    return fields;
}

std::vector<DDictRow> read_dbf_table(const fs::path& catalog_dir, const std::string& table_name) {
    fs::path path = catalog_dir / (upper_copy(table_name) + ".dbf");
    std::vector<unsigned char> data = read_binary(path);
    if (data.size() < 32) {
        return {};
    }

    std::uint32_t records = le32(data, 4);
    std::uint16_t header_len = le16(data, 8);
    std::uint16_t record_len = le16(data, 10);
    std::vector<FieldDef> fields = parse_fields(data);
    if (header_len == 0 || record_len == 0 || fields.empty()) {
        return {};
    }

    std::vector<DDictRow> rows;
    for (std::uint32_t rec = 0; rec < records; ++rec) {
        std::size_t base = static_cast<std::size_t>(header_len) + static_cast<std::size_t>(rec) * record_len;
        if (base + record_len > data.size()) {
            break;
        }
        if (data[base] == '*') {
            continue;
        }
        DDictRow row;
        std::size_t pos = base + 1;
        for (const auto& f : fields) {
            if (pos + f.width > data.size()) {
                break;
            }
            std::string raw(reinterpret_cast<const char*>(&data[pos]), f.width);
            row[f.name] = trim_copy(raw);
            pos += f.width;
        }
        rows.push_back(std::move(row));
    }
    return rows;
}

} // namespace dottalk::datadict
