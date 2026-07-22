#include "xindex/cdx_native_backend.hpp"

#include "xbase.hpp"
#include "cdx/cdx.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <ctime>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace xindex {

namespace {

static void append_u32_le_(std::vector<std::uint8_t>& out, std::uint32_t v)
{
    out.push_back(static_cast<std::uint8_t>( v        & 0xFFu));
    out.push_back(static_cast<std::uint8_t>((v >>  8) & 0xFFu));
    out.push_back(static_cast<std::uint8_t>((v >> 16) & 0xFFu));
    out.push_back(static_cast<std::uint8_t>((v >> 24) & 0xFFu));
}

static void append_u64_le_(std::vector<std::uint8_t>& out, std::uint64_t v)
{
    for (int i = 0; i < 8; ++i) {
        out.push_back(static_cast<std::uint8_t>((v >> (8 * i)) & 0xFFu));
    }
}

static std::string trim_copy_(std::string s)
{
    std::size_t b = 0;
    while (b < s.size()) {
        const unsigned char ch = static_cast<unsigned char>(s[b]);
        if (ch != ' ' && ch != '\0' && ch != '\t' && ch != '\r' && ch != '\n') break;
        ++b;
    }

    std::size_t e = s.size();
    while (e > b) {
        const unsigned char ch = static_cast<unsigned char>(s[e - 1]);
        if (ch != ' ' && ch != '\0' && ch != '\t' && ch != '\r' && ch != '\n') break;
        --e;
    }

    return s.substr(b, e - b);
}

static std::string upper_copy_ascii_local_(std::string s)
{
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static int field_index_for_tag_(const xbase::DbArea& A, const std::string& tag_upper)
{
    try {
        const auto defs = A.fields();
        const std::string want = upper_copy_ascii_local_(tag_upper);

        for (std::size_t i = 0; i < defs.size(); ++i) {
            std::string have = defs[i].name;
            const auto nul = have.find('\0');
            if (nul != std::string::npos) have.resize(nul);
            have = trim_copy_(have);
            have = upper_copy_ascii_local_(have);

            if (have == want) {
                return static_cast<int>(i) + 1; // 1-based
            }
        }
    } catch (...) {
    }
    return 0;
}

enum class SortKind_ {
    Character,
    Numeric,
    Date,
    Other
};

static SortKind_ sort_kind_for_field_type_(char t)
{
    switch (std::toupper(static_cast<unsigned char>(t))) {
        case 'C': return SortKind_::Character;
        case 'N':
        case 'F':
        case 'B':
        case 'I':
        case 'Y': return SortKind_::Numeric;
        case 'D': return SortKind_::Date;
        default:  return SortKind_::Other;
    }
}

struct SortEntry_ {
    bool valid{false};
    std::string s_key{};
    long double n_key{0.0L};
    std::uint64_t recno{};   // build for big: 64-bit recno
};

static bool parse_numeric_key_(const std::string& raw, long double& out)
{
    const std::string t = trim_copy_(raw);
    if (t.empty()) return false;

    try {
        std::size_t pos = 0;
        const long double v = std::stold(t, &pos);
        if (pos != t.size()) return false;
        out = v;
        return true;
    } catch (...) {
        return false;
    }
}

static bool parse_date_key_(const std::string& raw, std::string& out)
{
    const std::string t = trim_copy_(raw);
    if (t.size() != 8) return false;

    for (char c : t) {
        if (!std::isdigit(static_cast<unsigned char>(c))) return false;
    }

    out = t; // YYYYMMDD lexical order == chronological order
    return true;
}

static std::vector<std::uint64_t> collect_sorted_recnos_for_tag_(xbase::DbArea& A,
                                                                 const std::string& tag_upper)
{
    std::vector<std::uint64_t> out;

    const int field1 = field_index_for_tag_(A, tag_upper);
    if (field1 <= 0) {
        return out;
    }

    const auto defs = A.fields();
    const auto& fdef = defs[static_cast<std::size_t>(field1 - 1)];
    const SortKind_ kind = sort_kind_for_field_type_(fdef.type);

    std::vector<SortEntry_> rows;
    rows.reserve(static_cast<std::size_t>(A.recCount64()));

    if (A.top()) {
        do {
            const std::uint64_t rn = A.recno64();
            if (rn == 0) continue;

            SortEntry_ e{};
            e.recno = rn;

            std::string raw;
            try {
                raw = A.get(field1);
            } catch (...) {
                raw.clear();
            }

            switch (kind) {
                case SortKind_::Character: {
                    std::string t = trim_copy_(raw);
                    if (!t.empty()) {
                        e.valid = true;
                        e.s_key = upper_copy_ascii_local_(std::move(t));
                    }
                    break;
                }

                case SortKind_::Numeric: {
                    long double v = 0.0L;
                    if (parse_numeric_key_(raw, v)) {
                        e.valid = true;
                        e.n_key = v;
                    }
                    break;
                }

                case SortKind_::Date: {
                    std::string t;
                    if (parse_date_key_(raw, t)) {
                        e.valid = true;
                        e.s_key = std::move(t);
                    }
                    break;
                }

                case SortKind_::Other: {
                    std::string t = trim_copy_(raw);
                    if (!t.empty()) {
                        e.valid = true;
                        e.s_key = upper_copy_ascii_local_(std::move(t));
                    }
                    break;
                }
            }

            rows.push_back(std::move(e));
        } while (A.skip(1));
    }

    std::stable_sort(rows.begin(), rows.end(),
        [kind](const SortEntry_& a, const SortEntry_& b) {
            if (a.valid != b.valid) return a.valid && !b.valid;

            if (!a.valid && !b.valid) {
                return a.recno < b.recno;
            }

            switch (kind) {
                case SortKind_::Numeric:
                    if (a.n_key < b.n_key) return true;
                    if (a.n_key > b.n_key) return false;
                    return a.recno < b.recno;

                case SortKind_::Date:
                case SortKind_::Character:
                case SortKind_::Other:
                default:
                    if (a.s_key < b.s_key) return true;
                    if (a.s_key > b.s_key) return false;
                    return a.recno < b.recno;
            }
        });

    out.reserve(rows.size());
    for (const auto& r : rows) {
        out.push_back(r.recno);
    }

    return out;
}

static std::string key_to_string_safe(const Key& k)
{
    return std::string(k.begin(), k.end());
}

} // namespace

class CdxNativeBackend::CdxCursor final : public Cursor {
public:
    CdxCursor(const InxPayload* payload,
              std::optional<std::size_t> first_pos,
              std::optional<std::size_t> last_pos)
        : payload_(payload), first_pos_(first_pos), last_pos_(last_pos)
    {
    }

    bool first(Key& outKey, RecNo& outRec) override
    {
        if (!payload_ || !first_pos_ || !last_pos_ || *first_pos_ > *last_pos_) {
            valid_ = false;
            return false;
        }
        pos_ = *first_pos_;
        valid_ = true;
        return fill_(outKey, outRec);
    }

    bool next(Key& outKey, RecNo& outRec) override
    {
        if (!valid_ || !payload_ || !last_pos_) return false;
        if (pos_ >= *last_pos_) {
            valid_ = false;
            return false;
        }
        ++pos_;
        return fill_(outKey, outRec);
    }

    bool last(Key& outKey, RecNo& outRec) override
    {
        if (!payload_ || !first_pos_ || !last_pos_ || *first_pos_ > *last_pos_) {
            valid_ = false;
            return false;
        }
        pos_ = *last_pos_;
        valid_ = true;
        return fill_(outKey, outRec);
    }

    bool prev(Key& outKey, RecNo& outRec) override
    {
        if (!valid_ || !payload_ || !first_pos_) return false;
        if (pos_ <= *first_pos_) {
            valid_ = false;
            return false;
        }
        --pos_;
        return fill_(outKey, outRec);
    }

private:
    bool fill_(Key& outKey, RecNo& outRec)
    {
        if (!payload_ || pos_ >= payload_->size()) return false;
        const auto& e = payload_->entryAt(pos_);
        outKey = Key{};
        outRec = static_cast<RecNo>(e.recno);
        return true;
    }

private:
    const InxPayload* payload_{nullptr};
    std::optional<std::size_t> first_pos_{};
    std::optional<std::size_t> last_pos_{};
    std::size_t pos_{0};
    bool valid_{false};
};

std::string CdxNativeBackend::upper_copy_ascii_(std::string s)
{
    return upper_copy_ascii_local_(std::move(s));
}

CdxNativeBackend::CdxNativeBackend(xbase::DbArea& area, std::string cdx_path, std::string tag_upper)
    : area_(area),
      cdx_path_(std::move(cdx_path)),
      active_tag_upper_(upper_copy_ascii_(std::move(tag_upper)))
{
}

const CdxTag* CdxNativeBackend::activeTag_() const noexcept
{
    if (!active_tag_upper_.empty()) {
        const_cast<CdxDocument&>(doc_).selectTagByName(active_tag_upper_);
    }
    return doc_.activeTag();
}

CdxTag* CdxNativeBackend::activeTag_() noexcept
{
    if (!active_tag_upper_.empty()) {
        doc_.selectTagByName(active_tag_upper_);
    }
    return doc_.activeTag();
}

bool CdxNativeBackend::open(const std::string& path)
{
    if (!doc_.empty() && path == cdx_path_.string() && !stale_) {
        if (!active_tag_upper_.empty()) {
            (void)doc_.selectTagByName(active_tag_upper_);
        }
        return true;
    }

    cdx_path_ = path;

    std::string err;
    if (!doc_.open(cdx_path_, &err)) {
        return false;
    }

    if (!active_tag_upper_.empty()) {
        (void)doc_.selectTagByName(active_tag_upper_);
    } else if (doc_.tagCount() > 0) {
        (void)doc_.selectTagByIndex(0);
        if (const CdxTag* t = doc_.activeTag()) {
            active_tag_upper_ = upper_copy_ascii_(t->tagName());
        }
    }

    stale_ = false;
    return true;
}

void CdxNativeBackend::close()
{
    doc_.clear();
    cdx_path_.clear();
    active_tag_upper_.clear();
    stale_ = false;
}

void CdxNativeBackend::invalidate()
{
    stale_ = true;
}

void CdxNativeBackend::rebuild()
{
    if (cdx_path_.empty()) {
        throw std::runtime_error("CDX rebuild: no container path");
    }

    cdxfile::CDXHandle* h = nullptr;
    if (!cdxfile::open(cdx_path_.string(), h) || !h) {
        throw std::runtime_error("CDX rebuild: unable to open CDX");
    }

    std::vector<cdxfile::TagInfo> tags;
    if (!cdxfile::read_tagdir(h, tags)) {
        cdxfile::close(h);
        throw std::runtime_error("CDX rebuild: read_tagdir failed");
    }

    const std::uint64_t saved_recno = area_.recno64();

    try {
        for (auto& tag : tags) {
            const std::string tag_name = upper_copy_ascii_(tag.name);

            std::vector<std::uint64_t> recnos =
                collect_sorted_recnos_for_tag_(area_, tag_name);

            if (recnos.empty() && area_.recCount64() > 0) {
                cdxfile::close(h);
                throw std::runtime_error(
                    "CDX rebuild: tag field not found or no rows for tag " + tag_name);
            }

            std::vector<std::uint8_t> block;
            block.reserve(32 + recnos.size() * 8);

            // RUN8 header (8-byte-recno twin of CNX RUN1)
            block.push_back('R');
            block.push_back('U');
            block.push_back('N');
            block.push_back('8');

            append_u32_le_(block, 1u); // version
            append_u32_le_(block, static_cast<std::uint32_t>(tag.tag_id));
            append_u32_le_(block, 0u); // flags
            append_u32_le_(block, 0u); // reserved0
            append_u32_le_(block, static_cast<std::uint32_t>(recnos.size())); // rec_count
            append_u32_le_(block, 0u); // reserved1

            const std::uint32_t run_bytes =
                static_cast<std::uint32_t>(32u + recnos.size() * 8u);
            append_u32_le_(block, run_bytes);

            for (std::uint64_t r : recnos) {
                append_u64_le_(block, r);
            }

            std::uint64_t root_off = 0;
            if (!cdxfile::append_bytes(h, block.data(), block.size(), root_off)) {
                cdxfile::close(h);
                throw std::runtime_error("CDX rebuild: append_bytes failed");
            }

            tag.root_page_off = root_off;
            tag.stats_rec     = static_cast<std::uint64_t>(recnos.size());
            tag.updated_ts    = static_cast<std::uint64_t>(std::time(nullptr));
        }

        if (!cdxfile::write_tagdir(h, tags)) {
            cdxfile::close(h);
            throw std::runtime_error("CDX rebuild: write_tagdir failed");
        }

        cdxfile::close(h);

        if (saved_recno > 0) {
            (void)area_.gotoRec64(saved_recno);
        }

        invalidate();
        doc_.clear();

        std::string err;
        if (!doc_.open(cdx_path_, &err)) {
            throw std::runtime_error("CDX rebuild: reopen failed: " + err);
        }

        if (!active_tag_upper_.empty()) {
            (void)doc_.selectTagByName(active_tag_upper_);
        }

        stale_ = false;
    } catch (...) {
        cdxfile::close(h);
        if (saved_recno > 0) {
            (void)area_.gotoRec64(saved_recno);
        }
        throw;
    }
}

// batch-family contract: native CDX does not incrementally maintain on mutation
// in v1. These just mark the container stale (rebuild reconstructs).
void CdxNativeBackend::upsert(const Key& key, RecNo rec)
{
    (void)key;
    (void)rec;
    stale_ = true;
}

void CdxNativeBackend::erase(const Key& key, RecNo rec)
{
    (void)key;
    (void)rec;
    stale_ = true;
}

std::unique_ptr<Cursor> CdxNativeBackend::seek(const Key& key) const
{
    const CdxTag* tag = activeTag_();
    if (!tag) return nullptr;

    const InxPayload& payload = tag->payload();
    const std::string probe = key_to_string_safe(key);

    std::optional<std::size_t> pos = payload.seekFirstGe(probe);
    if (!pos) return std::make_unique<CdxCursor>(&payload, std::nullopt, std::nullopt);

    return std::make_unique<CdxCursor>(&payload, pos, payload.bottomPos());
}

std::unique_ptr<Cursor> CdxNativeBackend::scan(const Key& low, const Key& high) const
{
    const CdxTag* tag = activeTag_();
    if (!tag) return nullptr;

    const InxPayload& payload = tag->payload();
    const std::string low_key = key_to_string_safe(low);
    const std::string high_key = key_to_string_safe(high);

    std::optional<std::size_t> first = payload.entries().empty()
        ? std::nullopt
        : payload.seekFirstGe(low_key);

    std::optional<std::size_t> last = payload.bottomPos();

    (void)high_key;

    return std::make_unique<CdxCursor>(&payload, first, last);
}

void CdxNativeBackend::setTag(const std::string& tag_upper)
{
    const std::string want = upper_copy_ascii_(tag_upper);
    (void)doc_.selectTagByName(want);
    active_tag_upper_ = want;
}

bool CdxNativeBackend::selectTag(const std::string& tag_upper)
{
    const std::string want = upper_copy_ascii_(tag_upper);
    if (!doc_.selectTagByName(want)) return false;
    active_tag_upper_ = want;
    return true;
}

std::string CdxNativeBackend::activeTag() const
{
    if (const CdxTag* t = activeTag_()) {
        return t->tagName();
    }
    return std::string{};
}

std::vector<std::string> CdxNativeBackend::listTags() const
{
    std::vector<std::string> out;
    out.reserve(doc_.tagCount());
    for (const auto& t : doc_.tags()) {
        out.push_back(t.tagName());
    }
    return out;
}

} // namespace xindex
