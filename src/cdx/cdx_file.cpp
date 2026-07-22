// cli/cdx/cdx_file.cpp
#include "cdx/cdx.hpp"
#include "xbase/ramfs.hpp"

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace cdxfile {

// In-memory containers (AIF-043 V4d): a path under a mounted ramfs root is served
// from RAM. The handle carries either the disk std::fstream or a ramfs
// std::iostream; io() is the single byte-store seam every primitive reads/writes
// through (identical to DbArea's io()). When no ramfs root is mounted (default),
// is_virtual() is false and the RAM branch is dead — byte-identical to before.
struct CDXHandle {
    std::string path;
    std::fstream f;
    std::unique_ptr<std::iostream> mem;
    bool in_memory{false};

    std::iostream& io() noexcept {
        return in_memory ? *mem : static_cast<std::iostream&>(f);
    }
    bool is_open() const noexcept {
        return in_memory ? (mem != nullptr) : f.is_open();
    }
};

static bool ensure_parent_dir(const std::string& path)
{
    std::error_code ec;
    fs::path p(path);
    fs::path parent = p.parent_path();
    if (parent.empty()) return true;
    if (fs::exists(parent, ec)) return true;
    return fs::create_directories(parent, ec);
}

static std::uint64_t file_size64(std::iostream& f)
{
    auto cur = f.tellg();
    f.seekg(0, std::ios::end);
    std::uint64_t n = static_cast<std::uint64_t>(f.tellg());
    f.seekg(cur);
    return n;
}

bool open(const std::string& path, CDXHandle*& out)
{
    out = nullptr;

    auto h = new CDXHandle();
    h->path = path;

    if (xbase::ramfs::is_virtual(path)) {
        // RAM container: create-or-open the ramfs byte store.
        h->in_memory = true;
        h->mem = xbase::ramfs::open(path, /*create=*/true);
        if (!h->mem) { delete h; return false; }
    } else {
        if (!ensure_parent_dir(path)) { delete h; return false; }

        // Try open existing read/write binary
        h->f.open(path, std::ios::in | std::ios::out | std::ios::binary);

        if (!h->f.is_open()) {
            // Create new
            h->f.clear();
            h->f.open(path, std::ios::out | std::ios::binary);
            if (!h->f.is_open()) { delete h; return false; }
            h->f.close();

            // Reopen read/write
            h->f.open(path, std::ios::in | std::ios::out | std::ios::binary);
            if (!h->f.is_open()) { delete h; return false; }
        }
    }

    // If file is empty, initialize minimal header + blank TableBind page + empty tagdir.
    std::uint64_t sz = file_size64(h->io());
    if (sz == 0) {
        CDXHeader hdr{};
        hdr.magic = CDX_MAGIC;
        hdr.version = CDX_VERSION;
        hdr.page_size = CDX_DEFAULT_PAGE_SIZE;
        hdr.flags = 0;

        // Put tagdir at end for now. Start with header + TableBind block.
        hdr.tagdir_offset = sizeof(CDXHeader) + sizeof(TableBind);
        hdr.tag_count = 0;

        // Write header
        h->io().seekp(0, std::ios::beg);
        h->io().write(reinterpret_cast<const char*>(&hdr), sizeof(hdr));

        // Write TableBind (page 1)
        TableBind bind{};
        h->io().write(reinterpret_cast<const char*>(&bind), sizeof(bind));

        // Write empty tagdir (nothing)
        h->io().flush();
    }

    out = h;
    return true;
}

void close(CDXHandle*& h)
{
    if (!h) return;
    if (h->in_memory) {
        h->mem.reset();
    } else if (h->f.is_open()) {
        h->f.close();
    }
    delete h;
    h = nullptr;
}

bool read_header(CDXHandle* h, CDXHeader& hdr)
{
    if (!h || !h->is_open()) return false;
    h->io().clear();
    h->io().seekg(0, std::ios::beg);
    h->io().read(reinterpret_cast<char*>(&hdr), sizeof(hdr));
    if (!h->io().good()) return false;

    if (hdr.magic != CDX_MAGIC) return false;
    if (hdr.version != CDX_VERSION) return false;
    if (hdr.page_size == 0) return false;

    return true;
}

bool set_dirty(CDXHandle* h, bool dirty)
{
    if (!h) return false;
    CDXHeader hdr{};
    if (!read_header(h, hdr)) return false;

    if (dirty) hdr.flags |= CDX_HDRF_DIRTY;
    else       hdr.flags &= ~CDX_HDRF_DIRTY;

    return flush_header(h, hdr);
}

bool flush_header(CDXHandle* h, const CDXHeader& hdr)
{
    if (!h || !h->is_open()) return false;
    h->io().clear();
    h->io().seekp(0, std::ios::beg);
    h->io().write(reinterpret_cast<const char*>(&hdr), sizeof(hdr));
    h->io().flush();
    return h->io().good();
}

std::optional<uint32_t> page_size(CDXHandle* h)
{
    CDXHeader hdr{};
    if (!read_header(h, hdr)) return std::nullopt;
    return hdr.page_size;
}

bool read_table_bind(CDXHandle* h, TableBind& out)
{
    if (!h || !h->is_open()) return false;
    h->io().clear();
    h->io().seekg(sizeof(CDXHeader), std::ios::beg);
    h->io().read(reinterpret_cast<char*>(&out), sizeof(out));
    return h->io().good();
}

bool write_table_bind(CDXHandle* h, const TableBind& in)
{
    if (!h || !h->is_open()) return false;
    h->io().clear();
    h->io().seekp(sizeof(CDXHeader), std::ios::beg);
    h->io().write(reinterpret_cast<const char*>(&in), sizeof(in));
    h->io().flush();
    return h->io().good();
}

static TagInfo to_taginfo(const TagDirEntry& e)
{
    TagInfo t;
    t.name = std::string(e.name);
    t.tag_id = e.tag_id;
    t.flags = e.flags;
    t.collation_id = e.collation_id;
    t.expr_hash64 = e.expr_hash64;
    t.for_hash64 = e.for_hash64;
    t.root_page_off = e.root_page_off;
    t.key_type = e.key_type;
    t.key_len = e.key_len;
    t.stats_rec = e.stats_rec;
    t.updated_ts = e.updated_ts;
    return t;
}

static TagDirEntry to_entry(const TagInfo& t)
{
    TagDirEntry e{};
    std::memset(&e, 0, sizeof(e));
    std::snprintf(e.name, sizeof(e.name), "%s", t.name.c_str());
    e.tag_id = t.tag_id;
    e.flags = t.flags;
    e.collation_id = t.collation_id;
    e.expr_hash64 = t.expr_hash64;
    e.for_hash64 = t.for_hash64;
    e.root_page_off = t.root_page_off;
    e.key_type = t.key_type;
    e.key_len = t.key_len;
    e.stats_rec = t.stats_rec;
    e.updated_ts = t.updated_ts;
    return e;
}

bool read_tagdir(CDXHandle* h, std::vector<TagInfo>& out)
{
    out.clear();
    if (!h || !h->is_open()) return false;

    CDXHeader hdr{};
    if (!read_header(h, hdr)) return false;

    if (hdr.tagdir_offset == 0) return true;
    if (hdr.tag_count == 0) return true;

    h->io().clear();
    h->io().seekg(static_cast<std::streamoff>(hdr.tagdir_offset), std::ios::beg);

    for (std::uint32_t i = 0; i < hdr.tag_count; ++i) {
        TagDirEntry e{};
        h->io().read(reinterpret_cast<char*>(&e), sizeof(e));
        if (!h->io().good()) return false;
        out.emplace_back(to_taginfo(e));
    }
    return true;
}

bool write_tagdir(CDXHandle* h, const std::vector<TagInfo>& tags)
{
    if (!h || !h->is_open()) return false;

    CDXHeader hdr{};
    if (!read_header(h, hdr)) return false;

    // Append tagdir at end of file (simple/robust approach)
    h->io().clear();
    h->io().seekp(0, std::ios::end);
    std::uint64_t off = static_cast<std::uint64_t>(h->io().tellp());

    for (const auto& t : tags) {
        TagDirEntry e = to_entry(t);
        h->io().write(reinterpret_cast<const char*>(&e), sizeof(e));
        if (!h->io().good()) return false;
    }

    hdr.tagdir_offset = off;
    hdr.tag_count = static_cast<std::uint32_t>(tags.size());
    if (!flush_header(h, hdr)) return false;

    h->io().flush();
    return h->io().good();
}

bool add_tag(CDXHandle* h, const std::string& tag_name_upper)
{
    std::vector<TagInfo> tags;
    if (!read_tagdir(h, tags)) return false;

    auto it = std::find_if(tags.begin(), tags.end(),
        [&](const TagInfo& t){ return t.name == tag_name_upper; });

    if (it != tags.end()) return false;

    TagInfo t{};
    t.name = tag_name_upper;

    std::uint32_t max_id = 0;
    for (const auto& x : tags) max_id = std::max(max_id, x.tag_id);
    t.tag_id = max_id + 1;

    tags.push_back(t);
    return write_tagdir(h, tags);
}

bool drop_tag(CDXHandle* h, const std::string& tag_name_upper)
{
    std::vector<TagInfo> tags;
    if (!read_tagdir(h, tags)) return false;

    auto it = std::remove_if(tags.begin(), tags.end(),
        [&](const TagInfo& t){ return t.name == tag_name_upper; });

    if (it == tags.end()) return false;

    tags.erase(it, tags.end());
    return write_tagdir(h, tags);
}

BindCheck validate_table_bind(const TableBind& bind,
                              const TableProbe& probe,
                              BindPolicy policy)
{
    BindCheck r{};

    // Minimal conservative behavior (same as CDX shim):
    // STRICT: require basename match + schema-ish fields match when present.
    // WARN: allow mismatch but warn.
    // LOOSE: always ok.

    auto bind_name = std::string(bind.table_basename);
    auto up = [](std::string s){
        for (auto& c : s) c = (char)std::toupper((unsigned char)c);
        return s;
    };

    const std::string bind_up = up(bind_name);
    const std::string probe_up = probe.table_basename_upper;

    const bool name_ok = (!bind_up.empty() && !probe_up.empty()) ? (bind_up == probe_up) : true;
    const bool len_ok  = (bind.record_len == 0 || probe.record_len == 0) ? true : (bind.record_len == probe.record_len);
    const bool fc_ok   = (bind.field_count == 0 || probe.field_count == 0) ? true : (bind.field_count == probe.field_count);

    const bool ok = (name_ok && len_ok && fc_ok);

    if (policy == BindPolicy::LOOSE) {
        r.ok = true;
        return r;
    }

    if (ok) {
        r.ok = true;
        return r;
    }

    if (policy == BindPolicy::WARN) {
        r.ok = true;
        r.warn = true;
        r.message = "CDX bind mismatch (WARN): table/schema differs.";
        return r;
    }

    // STRICT
    r.ok = false;
    r.warn = false;
    r.message = "CDX bind mismatch (STRICT): table/schema differs.";
    return r;
}

bool append_bytes(CDXHandle* h, const void* data, std::size_t len, std::uint64_t& out_off)
{
    out_off = 0;
    if (!h || !h->is_open()) return false;

    h->io().clear();
    h->io().seekp(0, std::ios::end);
    out_off = static_cast<std::uint64_t>(h->io().tellp());
    h->io().write(reinterpret_cast<const char*>(data), static_cast<std::streamsize>(len));
    h->io().flush();
    return h->io().good();
}

bool read_at(CDXHandle* h, std::uint64_t off, void* buf, std::size_t len)
{
    if (!h || !h->is_open()) return false;
    h->io().clear();
    h->io().seekg(static_cast<std::streamoff>(off), std::ios::beg);
    h->io().read(reinterpret_cast<char*>(buf), static_cast<std::streamsize>(len));
    return h->io().good();
}

bool write_at(CDXHandle* h, std::uint64_t off, const void* buf, std::size_t len)
{
    if (!h || !h->is_open()) return false;
    h->io().clear();
    h->io().seekp(static_cast<std::streamoff>(off), std::ios::beg);
    h->io().write(reinterpret_cast<const char*>(buf), static_cast<std::streamsize>(len));
    h->io().flush();
    return h->io().good();
}

} // namespace cdxfile
