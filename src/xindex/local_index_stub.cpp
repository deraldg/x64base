#include "xindex/local_index_stub.hpp"
#include "xbase.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <tuple>
#include <utility>

namespace fs = std::filesystem;

namespace xindex {

namespace {

template <typename T>
bool write_pod(std::ofstream& out, const T& v) {
    out.write(reinterpret_cast<const char*>(&v), sizeof(T));
    return static_cast<bool>(out);
}

template <typename T>
bool read_pod(std::ifstream& in, T& v) {
    in.read(reinterpret_cast<char*>(&v), sizeof(T));
    return static_cast<bool>(in);
}

bool is_valid_header(const LocalIndexHeader& h) {
    return std::memcmp(h.family, kIndexKind, 3) == 0 && h.version == kFileVersion;
}

std::string trim_cstr32(const char buf[32]) {
    std::string s(buf, buf + 32);
    const auto pos = s.find('\0');
    if (pos != std::string::npos) s.resize(pos);
    return s;
}

void copy_name32(char dst[32], const std::string& src) {
    std::memset(dst, 0, 32);
    const std::size_t n = std::min<std::size_t>(31, src.size());
    std::memcpy(dst, src.data(), n);
}

template <class Area>
std::string safe_get_field_as_string(Area& area, std::uint32_t field_index1) {
    try {
        return area.get(static_cast<int>(field_index1));
    } catch (...) {
        return {};
    }
}

template <class Area>
std::vector<SimpleEntry> collect_entries_for_field(Area& area, std::uint32_t field_index1, bool descending) {
    std::vector<SimpleEntry> out;
    const std::uint32_t rc = static_cast<std::uint32_t>(area.recCount());

    for (std::uint32_t rec = 1; rec <= rc; ++rec) {
        if (!area.gotoRec(rec)) continue;
        if (!area.readCurrent()) continue;
        if (area.isDeleted()) continue;

        out.push_back(SimpleEntry{safe_get_field_as_string(area, field_index1), rec});
    }

    std::stable_sort(out.begin(), out.end(), [descending](const SimpleEntry& a, const SimpleEntry& b) {
        if (a.key == b.key) {
            return descending ? (a.recno > b.recno) : (a.recno < b.recno);
        }
        return descending ? (a.key > b.key) : (a.key < b.key);
    });

    return out;
}

bool write_entries(std::ofstream& out, const std::vector<SimpleEntry>& entries) {
    for (const auto& e : entries) {
        const std::uint32_t n = static_cast<std::uint32_t>(e.key.size());
        if (!write_pod(out, n)) return false;

        out.write(e.key.data(), static_cast<std::streamsize>(n));
        if (!static_cast<bool>(out)) return false;

        if (!write_pod(out, e.recno)) return false;
    }
    return true;
}

bool read_entries_at(std::ifstream& in,
                     std::uint64_t offset,
                     std::uint64_t count,
                     std::vector<std::uint32_t>& out_recnos) {
    in.seekg(static_cast<std::streamoff>(offset), std::ios::beg);
    if (!in) return false;

    out_recnos.clear();
    out_recnos.reserve(static_cast<std::size_t>(count));

    for (std::uint64_t i = 0; i < count; ++i) {
        std::uint32_t n = 0;
        std::uint32_t recno = 0;

        if (!read_pod(in, n)) return false;

        in.seekg(static_cast<std::streamoff>(n), std::ios::cur);
        if (!in) return false;

        if (!read_pod(in, recno)) return false;

        out_recnos.push_back(recno);
    }

    return true;
}

} // namespace

std::string upper_ascii_copy(std::string s) {
    for (char& ch : s) {
        if (ch >= 'a' && ch <= 'z') {
            ch = static_cast<char>(ch - ('a' - 'A'));
        }
    }
    return s;
}

bool write_six_create(const std::string& path,
                      const std::string& tag_name_upper,
                      std::uint32_t field_index1,
                      std::string* err) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        if (err) *err = "unable to create SIX file";
        return false;
    }

    LocalIndexHeader h{};
    std::memset(h.family, 0, sizeof(h.family));
    std::memcpy(h.family, kIndexKind, 3);
    h.format = static_cast<std::uint32_t>(LocalIndexFormat::SIX);
    h.version = kFileVersion;
    h.tag_count = 1;
    h.tag_dir_offset = sizeof(LocalIndexHeader);

    TagDesc d{};
    copy_name32(d.name, upper_ascii_copy(tag_name_upper));
    d.field_index1 = field_index1;
    d.flags = LIF_NONE;
    d.root_offset = sizeof(LocalIndexHeader) + sizeof(TagDesc);
    d.entry_count = 0;

    return write_pod(out, h) && write_pod(out, d);
}

bool write_scx_create(const std::string& path, std::string* err) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        if (err) *err = "unable to create SCX file";
        return false;
    }

    LocalIndexHeader h{};
    std::memset(h.family, 0, sizeof(h.family));
    std::memcpy(h.family, kIndexKind, 3);
    h.format = static_cast<std::uint32_t>(LocalIndexFormat::SCX);
    h.version = kFileVersion;
    h.tag_count = 0;
    h.tag_dir_offset = sizeof(LocalIndexHeader);

    return write_pod(out, h);
}

bool scx_add_tag(const std::string& path,
                 const std::string& tag_name_upper,
                 std::uint32_t field_index1,
                 bool descending,
                 std::string* err) {
    std::fstream io(path, std::ios::binary | std::ios::in | std::ios::out);
    if (!io) {
        if (err) *err = "unable to open SCX file";
        return false;
    }

    LocalIndexHeader h{};
    io.read(reinterpret_cast<char*>(&h), sizeof(h));
    if (!io || !is_valid_header(h) ||
        h.format != static_cast<std::uint32_t>(LocalIndexFormat::SCX)) {
        if (err) *err = "invalid SCX header";
        return false;
    }

    io.seekg(static_cast<std::streamoff>(h.tag_dir_offset), std::ios::beg);
    for (std::uint32_t i = 0; i < h.tag_count; ++i) {
        TagDesc d{};
        io.read(reinterpret_cast<char*>(&d), sizeof(d));
        if (!io) {
            if (err) *err = "unable to read SCX tag directory";
            return false;
        }

        if (upper_ascii_copy(trim_cstr32(d.name)) == upper_ascii_copy(tag_name_upper)) {
            if (err) *err = "tag already exists";
            return false;
        }
    }

    io.clear();
    io.seekp(0, std::ios::end);

    TagDesc d{};
    copy_name32(d.name, upper_ascii_copy(tag_name_upper));
    d.field_index1 = field_index1;
    d.flags = descending ? LIF_DESC : LIF_NONE;
    d.root_offset = 0;
    d.entry_count = 0;

    io.write(reinterpret_cast<const char*>(&d), sizeof(d));
    if (!io) {
        if (err) *err = "unable to append SCX tag";
        return false;
    }

    ++h.tag_count;
    io.seekp(0, std::ios::beg);
    io.write(reinterpret_cast<const char*>(&h), sizeof(h));

    return static_cast<bool>(io);
}

bool six_build_from_area(const std::string& path,
                         xbase::DbArea& area,
                         std::string* err) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        if (err) *err = "unable to open SIX file";
        return false;
    }

    LocalIndexHeader h{};
    TagDesc d{};
    if (!read_pod(in, h) || !read_pod(in, d) ||
        !is_valid_header(h) ||
        h.format != static_cast<std::uint32_t>(LocalIndexFormat::SIX)) {
        if (err) *err = "invalid SIX file";
        return false;
    }
    in.close();

    auto entries = collect_entries_for_field(area, d.field_index1, (d.flags & LIF_DESC) != 0);

    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        if (err) *err = "unable to rewrite SIX file";
        return false;
    }

    d.root_offset = sizeof(LocalIndexHeader) + sizeof(TagDesc);
    d.entry_count = static_cast<std::uint64_t>(entries.size());

    if (!write_pod(out, h) || !write_pod(out, d) || !write_entries(out, entries)) {
        if (err) *err = "unable to write SIX entries";
        return false;
    }

    return true;
}

bool scx_build_from_area(const std::string& path,
                         xbase::DbArea& area,
                         std::string* err) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        if (err) *err = "unable to open SCX file";
        return false;
    }

    LocalIndexHeader h{};
    if (!read_pod(in, h) || !is_valid_header(h) ||
        h.format != static_cast<std::uint32_t>(LocalIndexFormat::SCX)) {
        if (err) *err = "invalid SCX file";
        return false;
    }

    std::vector<TagDesc> tags(h.tag_count);
    for (auto& d : tags) {
        if (!read_pod(in, d)) {
            if (err) *err = "unable to read SCX tags";
            return false;
        }
    }
    in.close();

    std::vector<std::vector<SimpleEntry>> all_entries;
    all_entries.reserve(tags.size());

    std::uint64_t next_offset =
        sizeof(LocalIndexHeader) + static_cast<std::uint64_t>(tags.size()) * sizeof(TagDesc);

    for (auto& d : tags) {
        auto entries = collect_entries_for_field(area, d.field_index1, (d.flags & LIF_DESC) != 0);

        d.root_offset = next_offset;
        d.entry_count = static_cast<std::uint64_t>(entries.size());

        std::uint64_t bytes = 0;
        for (const auto& e : entries) {
            bytes += sizeof(std::uint32_t) + static_cast<std::uint64_t>(e.key.size()) + sizeof(std::uint32_t);
        }
        next_offset += bytes;

        all_entries.push_back(std::move(entries));
    }

    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        if (err) *err = "unable to rewrite SCX file";
        return false;
    }

    if (!write_pod(out, h)) {
        if (err) *err = "unable to write SCX header";
        return false;
    }

    for (const auto& d : tags) {
        if (!write_pod(out, d)) {
            if (err) *err = "unable to write SCX tags";
            return false;
        }
    }

    for (const auto& entries : all_entries) {
        if (!write_entries(out, entries)) {
            if (err) *err = "unable to write SCX entries";
            return false;
        }
    }

    return true;
}

bool six_info(const std::string& path, std::ostream& os, std::string* err) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        if (err) *err = "unable to open SIX file";
        return false;
    }

    LocalIndexHeader h{};
    TagDesc d{};
    if (!read_pod(in, h) || !read_pod(in, d) || !is_valid_header(h)) {
        if (err) *err = "invalid SIX file";
        return false;
    }

    os << "SIX file : " << path << "\n";
    os << "Format   : SIX\n";
    os << "Version  : " << h.version << "\n";
    os << "Tag      : " << trim_cstr32(d.name) << "\n";
    os << "Field    : " << d.field_index1 << "\n";
    os << "Flags    : " << d.flags << "\n";
    os << "Entries  : " << d.entry_count << "\n";
    return true;
}

bool scx_info(const std::string& path, std::ostream& os, std::string* err) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        if (err) *err = "unable to open SCX file";
        return false;
    }

    LocalIndexHeader h{};
    if (!read_pod(in, h) || !is_valid_header(h)) {
        if (err) *err = "invalid SCX file";
        return false;
    }

    os << "SCX file : " << path << "\n";
    os << "Format   : SCX\n";
    os << "Version  : " << h.version << "\n";
    os << "Tags     : " << h.tag_count << "\n";

    for (std::uint32_t i = 0; i < h.tag_count; ++i) {
        TagDesc d{};
        if (!read_pod(in, d)) {
            if (err) *err = "unable to read SCX tag";
            return false;
        }

        os << "  [" << (i + 1) << "] "
           << trim_cstr32(d.name)
           << " field=" << d.field_index1
           << " flags=" << d.flags
           << " entries=" << d.entry_count << "\n";
    }

    return true;
}

bool scx_tags(const std::string& path, std::ostream& os, std::string* err) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        if (err) *err = "unable to open SCX file";
        return false;
    }

    LocalIndexHeader h{};
    if (!read_pod(in, h) || !is_valid_header(h)) {
        if (err) *err = "invalid SCX file";
        return false;
    }

    os << "SCX tags : " << path << "\n";
    for (std::uint32_t i = 0; i < h.tag_count; ++i) {
        TagDesc d{};
        if (!read_pod(in, d)) {
            if (err) *err = "unable to read SCX tag";
            return false;
        }

        os << "  " << trim_cstr32(d.name) << " -> field " << d.field_index1 << "\n";
    }

    return true;
}

bool load_six_recnos(const std::string& path,
                     std::vector<std::uint32_t>& out_recnos,
                     std::string* err) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        if (err) *err = "unable to open SIX file";
        return false;
    }

    LocalIndexHeader h{};
    TagDesc d{};
    if (!read_pod(in, h) || !read_pod(in, d) || !is_valid_header(h)) {
        if (err) *err = "invalid SIX file";
        return false;
    }

    if (!read_entries_at(in, d.root_offset, d.entry_count, out_recnos)) {
        if (err) *err = "unable to read SIX entries";
        return false;
    }

    return true;
}

bool load_scx_recnos(const std::string& path,
                     const std::string& tag_name_upper,
                     std::vector<std::uint32_t>& out_recnos,
                     std::string* err) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        if (err) *err = "unable to open SCX file";
        return false;
    }

    LocalIndexHeader h{};
    if (!read_pod(in, h) || !is_valid_header(h)) {
        if (err) *err = "invalid SCX file";
        return false;
    }

    const std::string want = upper_ascii_copy(tag_name_upper);

    for (std::uint32_t i = 0; i < h.tag_count; ++i) {
        TagDesc d{};
        if (!read_pod(in, d)) {
            if (err) *err = "unable to read SCX tag";
            return false;
        }

        if (upper_ascii_copy(trim_cstr32(d.name)) == want) {
            if (!read_entries_at(in, d.root_offset, d.entry_count, out_recnos)) {
                if (err) *err = "unable to read SCX entries";
                return false;
            }
            return true;
        }
    }

    if (err) *err = "tag not found";
    return false;
}

} // namespace xindex