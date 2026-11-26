// @dottalk.file v1
// subsystem: datadict
// layer: helper
// project: project.x64base.runtime
// owner: member.derald
// status: supported

#include "datadict/ddict_dbf_reader.hpp"
#include "datadict/ddict_read_helpers.hpp"
#include <fstream>
#include <set>
#include <stdexcept>

namespace dottalk::datadict {
namespace {
// Inspection decoder for the geometry in xbase_64.hpp. No DbArea is opened:
// catalog inspection must not initialize memo/index sidecars or update headers.
std::uint64_t number(const std::vector<unsigned char>& b, std::size_t p, unsigned n) {
    if (p > b.size() || n > b.size() - p) throw std::runtime_error("truncated header");
    std::uint64_t v = 0;
    for (unsigned i = 0; i < n; ++i) v |= std::uint64_t(b[p + i]) << (8 * i);
    return v;
}
struct Geometry {
    std::size_t start{}, length{}, count{};
    std::string name;
    std::vector<FieldDef> fields;
};
Geometry geometry(const std::vector<unsigned char>& b) {
    if (b.size() < 32) throw std::runtime_error("truncated DBF header");
    const bool x64 = b[0] == 0x64;
    const auto start = number(b, x64 ? 40 : 8, x64 ? 8 : 2);
    const auto length = number(b, x64 ? 48 : 10, x64 ? 8 : 2);
    const auto count = number(b, x64 ? 32 : 4, x64 ? 8 : 4);
    std::size_t p = x64 ? 96 : 32;
    if (start <= p || start > b.size() || length == 0 ||
        count > (b.size() - start) / length)
        throw std::runtime_error("invalid DBF record geometry or truncated records");
    Geometry g{static_cast<std::size_t>(start), static_cast<std::size_t>(length),
               static_cast<std::size_t>(count), {}, {}};
    while (p < start && b[p] != 0x0d) {
        if (start - p < 32) throw std::runtime_error("truncated field descriptor");
        std::string name;
        for (std::size_t j = 0; j < 11 && b[p + j]; ++j) name += char(b[p + j]);
        const char type = char(b[p + 11]);
        if (name.empty() || std::string("CDNLFIMBYT@GOVQ0").find(type) == std::string::npos)
            throw std::runtime_error("invalid field descriptor");
        // Character width uses both bytes in extended FoxPro descriptors.
        std::size_t width = static_cast<std::size_t>(number(b, p + 16, type == 'C' ? 2 : 1));
        g.fields.push_back({upper_copy(name), type, width});
        p += 32;
    }
    if (p >= start || g.fields.empty()) throw std::runtime_error("missing descriptor terminator or fields");
    ++p;
    if (x64 && start - p >= 4 && std::string(reinterpret_cast<const char*>(b.data() + p), 4) == "X64M") {
        if (start - p < 44) throw std::runtime_error("truncated X64M header");
        const auto version = number(b, p + 4, 2), total = number(b, p + 8, 4);
        const auto entries = number(b, p + 20, 4), n = number(b, p + 24, 4);
        const auto pool = number(b, p + 28, 4), pool_size = number(b, p + 32, 4);
        const std::size_t stride = version == 1 ? 12 : 16;
        if ((version != 1 && version != 2) || total < 44 || total > start - p ||
            entries < 44 || entries > total || n > (total - entries) / stride ||
            pool > total || pool_size > total - pool)
            throw std::runtime_error("invalid X64M bounds/version");
        auto text = [&](std::uint64_t off, std::uint64_t len) {
            if (off > pool_size || len > pool_size - off) throw std::runtime_error("invalid X64M string");
            return std::string(reinterpret_cast<const char*>(b.data() + p + pool + off), static_cast<std::size_t>(len));
        };
        g.name = text(number(b, p + 12, 4), number(b, p + 16, 2));
        std::set<std::uint64_t> seen;
        for (std::uint64_t i = 0; i < n; ++i) {
            const std::size_t e = p + static_cast<std::size_t>(entries + i * stride);
            const auto index = number(b, e, 4);
            if (!index || index > g.fields.size() || !seen.insert(index).second)
                throw std::runtime_error("invalid/duplicate X64M field index");
            auto name = text(number(b, e + 4, 4), number(b, e + 8, 2));
            if (!name.empty()) g.fields[index - 1].name = upper_copy(name);
            if (version == 2 && number(b, e + 12, 4))
                g.fields[index - 1].width = static_cast<std::size_t>(number(b, e + 12, 4));
        }
    } else if (x64 && start - p >= 4 && (b[p] || b[p+1] || b[p+2] || b[p+3])) {
        throw std::runtime_error("unrecognized x64 metadata");
    }
    std::set<std::string> names;
    std::size_t used = 1;
    for (const auto& f : g.fields) {
        if (!names.insert(f.name).second || !f.width || used > length || f.width > length - used)
            throw std::runtime_error("duplicate field name or invalid field width");
        used += f.width;
    }
    if (used != length) throw std::runtime_error("field widths do not match record size");
    return g;
}
}
std::vector<unsigned char> read_binary(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return {};
    return std::vector<unsigned char>(std::istreambuf_iterator<char>(in), {});
}
std::vector<FieldDef> parse_fields(const std::vector<unsigned char>& data) {
    try { return geometry(data).fields; } catch (const std::exception&) { return {}; }
}
TableReadResult read_dbf_table_checked(const std::filesystem::path& dir, const std::string& table) {
    TableReadResult result;
    try {
        const auto path = dir / (table + ".dbf");
        std::error_code ec;
        if (!std::filesystem::exists(path, ec)) {
            if (ec) throw std::runtime_error(ec.message());
            result.state = TableReadState::Missing;
            return result;
        }
        auto data = read_binary(path);
        auto g = geometry(data);
        result.fields = g.fields;
        result.x64 = data[0] == 0x64;
        result.logical_name = g.name.empty() ? table : g.name;
        for (std::size_t rec = 0; rec < g.count; ++rec) {
            const auto base = g.start + rec * g.length;
            if (data[base] == '*') continue;
            if (data[base] != ' ') throw std::runtime_error("invalid record deletion marker");
            DDictRow row;
            std::size_t pos = base + 1;
            for (const auto& f : g.fields) {
                std::string raw(reinterpret_cast<const char*>(data.data() + pos), f.width);
                row[f.name] = f.type == 'M' ? raw : trim_copy(raw);
                pos += f.width;
            }
            result.rows.push_back(std::move(row));
        }
        result.state = TableReadState::Ready;
    } catch (const std::exception& e) {
        result.rows.clear();
        result.error = e.what();
        result.state = TableReadState::Error;
    }
    return result;
}
std::vector<DDictRow> read_dbf_table(const std::filesystem::path& dir, const std::string& table) {
    // Compatibility API for metacollect. The catalog view uses checked reads.
    auto result = read_dbf_table_checked(dir, upper_copy(table));
    for (auto& row : result.rows) for (const auto& f : result.fields)
        if (f.type == 'M') row[f.name] = trim_copy(row[f.name]);
    return std::move(result.rows);
}
} // namespace dottalk::datadict
