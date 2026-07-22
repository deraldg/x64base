#include "cdx/cdx_document.hpp"
#include "cdx/cdx.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <utility>
#include <vector>

namespace xindex {

namespace {

static std::uint32_t read_u32_le_(const std::uint8_t* p)
{
    return static_cast<std::uint32_t>(p[0])
         | (static_cast<std::uint32_t>(p[1]) << 8)
         | (static_cast<std::uint32_t>(p[2]) << 16)
         | (static_cast<std::uint32_t>(p[3]) << 24);
}

static std::uint64_t read_u64_le_(const std::uint8_t* p)
{
    std::uint64_t v = 0;
    for (int i = 0; i < 8; ++i) {
        v |= (static_cast<std::uint64_t>(p[i]) << (8 * i));
    }
    return v;
}

// RUN8: the 64-bit twin of CNX's RUN1. Identical header, 8-byte recnos.
//  0..3   magic "RUN8"
//  4..7   version
//  8..11  tag_id
// 12..15  flags
// 16..19  reserved0
// 20..23  rec_count
// 24..27  reserved1
// 28..31  run_bytes   (= 32 + rec_count * 8)
// 32..    rec_count * uint64 recno (LE)
static bool load_run8_payload_(cdxfile::CDXHandle* h,
                               std::uint64_t root_off,
                               const std::string& tag_name,
                               InxPayload& payload,
                               std::uint32_t& out_rec_count)
{
    out_rec_count = 0;
    payload.clear();

    if (!h || root_off == 0) return false;

    std::uint8_t hdr[32]{};
    if (!cdxfile::read_at(h, root_off, hdr, sizeof(hdr))) {
        return false;
    }

    if (hdr[0] != 'R' || hdr[1] != 'U' || hdr[2] != 'N' || hdr[3] != '8') {
        return false;
    }

    const std::uint32_t rec_count = read_u32_le_(hdr + 20);
    const std::uint32_t run_bytes = read_u32_le_(hdr + 28);

    if (run_bytes < 32) return false;
    if (static_cast<std::uint64_t>(run_bytes) <
        32u + static_cast<std::uint64_t>(rec_count) * 8u) return false;

    std::vector<std::uint8_t> buf(run_bytes);
    if (!cdxfile::read_at(h, root_off, buf.data(), buf.size())) {
        return false;
    }

    std::vector<InxEntry> entries;
    entries.reserve(rec_count);

    std::size_t pos = 32;
    for (std::uint32_t i = 0; i < rec_count; ++i) {
        if (pos + 8 > buf.size()) return false;
        const std::uint64_t rn = read_u64_le_(buf.data() + pos);
        entries.push_back(InxEntry{"", rn});
        pos += 8;
    }

    payload = InxPayload::fromEntries1Inx(tag_name, entries);
    out_rec_count = static_cast<std::uint32_t>(entries.size());
    return true;
}

} // namespace

std::string CdxDocument::upper_copy_ascii_(std::string s)
{
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

void CdxDocument::clear() noexcept
{
    header_ = CdxHeader{};
    tags_.clear();
    active_tag_index_ = 0;
}

bool CdxDocument::selectTagByIndex(std::size_t i) noexcept
{
    if (i >= tags_.size()) return false;
    active_tag_index_ = i;
    header_.active_tag_index = static_cast<std::uint32_t>(i);
    return true;
}

bool CdxDocument::selectTagByName(const std::string& tag_name)
{
    const std::string want = upper_copy_ascii_(tag_name);
    for (std::size_t i = 0; i < tags_.size(); ++i) {
        if (upper_copy_ascii_(tags_[i].tagName()) == want) {
            active_tag_index_ = i;
            header_.active_tag_index = static_cast<std::uint32_t>(i);
            return true;
        }
    }
    return false;
}

const CdxTag* CdxDocument::activeTag() const noexcept
{
    if (tags_.empty() || active_tag_index_ >= tags_.size()) return nullptr;
    return &tags_[active_tag_index_];
}

CdxTag* CdxDocument::activeTag() noexcept
{
    if (tags_.empty() || active_tag_index_ >= tags_.size()) return nullptr;
    return &tags_[active_tag_index_];
}

bool CdxDocument::open(const std::filesystem::path& path, std::string* err)
{
    clear();

    cdxfile::CDXHandle* h = nullptr;
    if (!cdxfile::open(path.string(), h) || !h) {
        if (err) *err = "cannot open CDX file: " + path.string();
        return false;
    }

    cdxfile::CDXHeader raw_hdr{};
    if (!cdxfile::read_header(h, raw_hdr)) {
        cdxfile::close(h);
        if (err) *err = "cannot read CDX header";
        return false;
    }

    std::vector<cdxfile::TagInfo> raw_tags;
    if (!cdxfile::read_tagdir(h, raw_tags)) {
        cdxfile::close(h);
        if (err) *err = "cannot read CDX tag directory";
        return false;
    }

    header_.magic[0] = 'C';
    header_.magic[1] = 'D';
    header_.magic[2] = 'X';
    header_.magic[3] = '1';
    header_.version = static_cast<std::uint16_t>(raw_hdr.version);
    header_.flags = raw_hdr.flags;
    header_.tag_count = static_cast<std::uint32_t>(raw_tags.size());
    header_.directory_offset = static_cast<std::uint32_t>(raw_hdr.tagdir_offset);
    header_.directory_size = 0;
    header_.record_count_snapshot = 0;
    header_.build_timestamp = 0;

    tags_.reserve(raw_tags.size());

    for (const auto& rt : raw_tags) {
        CdxTag::Meta m{};
        m.tag_name = upper_copy_ascii_(rt.name);
        m.expr_token = m.tag_name;
        m.ascending = true;
        m.embedded_fmt = InxPayload::Format::Unknown;
        m.field_type = static_cast<std::uint16_t>(rt.key_type);
        m.key_len = static_cast<std::uint16_t>(rt.key_len);
        m.record_count = 0;
        m.payload_offset = static_cast<std::uint32_t>(rt.root_page_off);
        m.payload_size = 0;

        InxPayload payload;
        std::uint32_t rec_count = 0;

        if (load_run8_payload_(h, rt.root_page_off, m.tag_name, payload, rec_count)) {
            m.record_count = rec_count;
            m.embedded_fmt = InxPayload::Format::V1_1INX;
        }

        tags_.emplace_back(std::move(m), std::move(payload));
    }

    cdxfile::close(h);

    if (!tags_.empty()) {
        active_tag_index_ = 0;
        header_.active_tag_index = 0;
    }

    return true;
}

} // namespace xindex
