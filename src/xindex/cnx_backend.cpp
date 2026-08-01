// @dottalk.file v1
// subsystem: xindex
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "cnx/cnx_backend.hpp"

#include "xbase.hpp"
#include "cnx/cnx.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <ctime>
#include <iostream>
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
    std::uint32_t recno{};
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

// ---- shared key derivation: REBUILD and REALTIME must agree ----------------
//
// A CNX RUN1 payload stores 4 bytes per recno and NO keys (cnx_document.cpp:81
// builds every entry as InxEntry{"", rn}). Order therefore lives in the
// SEQUENCE of entries, and the ordering authority is the live table -- the same
// authority a rebuild uses. Realtime maintenance is only correct if it derives
// and compares keys exactly as a rebuild would, so both paths go through
// derive_sort_entry_ and sort_entry_less_. Neither keeps its own copy of the
// rules: if they drift, a REBUILD reorders differently from an in-session edit
// and every ordering proof flaps.

static SortEntry_ derive_sort_entry_(const std::string& raw,
                                     SortKind_ kind,
                                     std::uint64_t recno)
{
    SortEntry_ e{};
    e.recno = static_cast<std::uint32_t>(recno);

    switch (kind) {
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

        case SortKind_::Character:
        case SortKind_::Other:
        default: {
            std::string t = trim_copy_(raw);
            if (!t.empty()) {
                e.valid = true;
                e.s_key = upper_copy_ascii_local_(std::move(t));
            }
            break;
        }
    }

    return e;
}

static bool sort_entry_less_(const SortEntry_& a, const SortEntry_& b, SortKind_ kind)
{
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
}

// Read ONE record's key. Moves the record pointer, so every caller saves and
// restores it. Verifies the landing recno rather than trusting gotoRec's return
// type, so a refused seek cannot silently key off the wrong record.
static bool read_sort_entry_for_recno_(xbase::DbArea& A,
                                       int field1,
                                       SortKind_ kind,
                                       std::uint64_t recno,
                                       SortEntry_& out)
{
    if (recno == 0) return false;

    (void)A.gotoRec(static_cast<int>(recno));
    if (A.recno() != static_cast<int>(recno)) return false;

    std::string raw;
    try {
        raw = A.get(field1);
    } catch (...) {
        raw.clear();
    }

    out = derive_sort_entry_(raw, kind, recno);
    return true;
}

// Resolve a tag to its 1-based field index and sort kind. Returns false when the
// tag names no field on this table, which is the one case realtime maintenance
// legitimately cannot serve.
static bool tag_field_and_kind_(xbase::DbArea& A,
                                const std::string& tag_upper,
                                int& out_field1,
                                SortKind_& out_kind)
{
    out_field1 = field_index_for_tag_(A, tag_upper);
    if (out_field1 <= 0) return false;

    try {
        const auto defs = A.fields();
        if (static_cast<std::size_t>(out_field1) > defs.size()) return false;
        out_kind = sort_kind_for_field_type_(defs[static_cast<std::size_t>(out_field1 - 1)].type);
    } catch (...) {
        return false;
    }

    return true;
}

static std::vector<std::uint32_t> collect_sorted_recnos_for_tag_(xbase::DbArea& A,
                                                                  const std::string& tag_upper)
{
    std::vector<std::uint32_t> out;

    const int field1 = field_index_for_tag_(A, tag_upper);
    if (field1 <= 0) {
        return out;
    }

    const auto defs = A.fields();
    const auto& fdef = defs[static_cast<std::size_t>(field1 - 1)];
    const SortKind_ kind = sort_kind_for_field_type_(fdef.type);

    std::vector<SortEntry_> rows;
    rows.reserve(static_cast<std::size_t>(A.recCount()));

    if (A.top()) {
        do {
            const int rn = A.recno();
            if (rn <= 0) continue;

            std::string raw;
            try {
                raw = A.get(field1);
            } catch (...) {
                raw.clear();
            }

            rows.push_back(derive_sort_entry_(raw, kind, static_cast<std::uint64_t>(rn)));
        } while (A.skip(1));
    }

    std::stable_sort(rows.begin(), rows.end(),
        [kind](const SortEntry_& a, const SortEntry_& b) {
            return sort_entry_less_(a, b, kind);
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

class CnxBackend::CnxCursor final : public Cursor {
public:
    CnxCursor(const InxPayload* payload,
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

std::string CnxBackend::upper_copy_ascii_(std::string s)
{
    return upper_copy_ascii_local_(std::move(s));
}

CnxBackend::CnxBackend(xbase::DbArea& area, std::string cnx_path, std::string tag_upper)
    : area_(area),
      cnx_path_(std::move(cnx_path)),
      active_tag_upper_(upper_copy_ascii_(std::move(tag_upper)))
{
}

const CnxTag* CnxBackend::activeTag_() const noexcept
{
    if (!active_tag_upper_.empty()) {
        const_cast<CnxDocument&>(doc_).selectTagByName(active_tag_upper_);
    }
    return doc_.activeTag();
}

CnxTag* CnxBackend::activeTag_() noexcept
{
    if (!active_tag_upper_.empty()) {
        doc_.selectTagByName(active_tag_upper_);
    }
    return doc_.activeTag();
}

bool CnxBackend::open(const std::string& path)
{
    if (!doc_.empty() && path == cnx_path_.string() && !stale_) {
        if (!active_tag_upper_.empty()) {
            (void)doc_.selectTagByName(active_tag_upper_);
        }
        return true;
    }

    cnx_path_ = path;

    std::string err;
    if (!doc_.open(cnx_path_, area_, &err)) {
        return false;
    }

    if (!active_tag_upper_.empty()) {
        (void)doc_.selectTagByName(active_tag_upper_);
    } else if (doc_.tagCount() > 0) {
        (void)doc_.selectTagByIndex(0);
        if (const CnxTag* t = doc_.activeTag()) {
            active_tag_upper_ = upper_copy_ascii_(t->tagName());
        }
    }

    stale_ = false;
    return true;
}

void CnxBackend::close()
{
    doc_.clear();
    cnx_path_.clear();
    active_tag_upper_.clear();
    stale_ = false;
}

void CnxBackend::invalidate()
{
    stale_ = true;
}

void CnxBackend::rebuild()
{
    if (cnx_path_.empty()) {
        throw std::runtime_error("CNX rebuild: no container path");
    }

    cnxfile::CNXHandle* h = nullptr;
    if (!cnxfile::open(cnx_path_.string(), h) || !h) {
        throw std::runtime_error("CNX rebuild: unable to open CNX");
    }

    std::vector<cnxfile::TagInfo> tags;
    if (!cnxfile::read_tagdir(h, tags)) {
        cnxfile::close(h);
        throw std::runtime_error("CNX rebuild: read_tagdir failed");
    }

    const int saved_recno = area_.recno();

    try {
        for (auto& tag : tags) {
            const std::string tag_name = upper_copy_ascii_(tag.name);

            std::vector<std::uint32_t> recnos =
                collect_sorted_recnos_for_tag_(area_, tag_name);

            if (recnos.empty() && area_.recCount() > 0) {
                cnxfile::close(h);
                throw std::runtime_error(
                    "CNX rebuild: tag field not found or no rows for tag " + tag_name);
            }

            std::vector<std::uint8_t> block;
            block.reserve(32 + recnos.size() * 4);

            // RUN1 header
            block.push_back('R');
            block.push_back('U');
            block.push_back('N');
            block.push_back('1');

            append_u32_le_(block, 1u); // version
            append_u32_le_(block, static_cast<std::uint32_t>(tag.tag_id));
            append_u32_le_(block, 0u); // flags
            append_u32_le_(block, 0u); // reserved0
            append_u32_le_(block, static_cast<std::uint32_t>(recnos.size())); // rec_count
            append_u32_le_(block, 0u); // reserved1

            const std::uint32_t run_bytes =
                static_cast<std::uint32_t>(32u + recnos.size() * 4u);
            append_u32_le_(block, run_bytes);

            for (std::uint32_t r : recnos) {
                append_u32_le_(block, r);
            }

            // Capture start offset before append for diagnostics.
            std::uint64_t root_off = 0;
            if (!cnxfile::append_bytes(h, block.data(), block.size(), root_off)) {
                cnxfile::close(h);
                throw std::runtime_error("CNX rebuild: append_bytes failed");
            }

            // Immediate verify: does root_off actually point at RUN1?
            std::uint8_t verify_hdr[4]{};
            bool verify_ok = cnxfile::read_at(h, root_off, verify_hdr, sizeof(verify_hdr));

            std::cout << "[VERIFY WRITE] tag=" << tag_name
                      << " root=" << root_off
                      << " read_ok=" << (verify_ok ? "yes" : "no")
                      << " hdr="
                      << static_cast<char>(verify_hdr[0])
                      << static_cast<char>(verify_hdr[1])
                      << static_cast<char>(verify_hdr[2])
                      << static_cast<char>(verify_hdr[3])
                      << "\n";

            tag.root_page_off = root_off;
            tag.stats_rec     = static_cast<std::uint64_t>(recnos.size());
            tag.updated_ts    = static_cast<std::uint64_t>(std::time(nullptr));

            std::cout << "[CNX REBUILD] tag=" << tag_name
                      << " recs=" << recnos.size()
                      << " root=" << root_off << "\n";
        }

        if (!cnxfile::write_tagdir(h, tags)) {
            cnxfile::close(h);
            throw std::runtime_error("CNX rebuild: write_tagdir failed");
        }

        cnxfile::close(h);

        if (saved_recno > 0) {
            (void)area_.gotoRec(saved_recno);
        }

        invalidate();
        doc_.clear();

        std::string err;
        if (!doc_.open(cnx_path_, area_, &err)) {
            throw std::runtime_error("CNX rebuild: reopen failed: " + err);
        }

        if (!active_tag_upper_.empty()) {
            (void)doc_.selectTagByName(active_tag_upper_);
        }

        stale_ = false;
        std::cout << "[CNX REBUILD COMPLETE]\n";
    } catch (...) {
        cnxfile::close(h);
        if (saved_recno > 0) {
            (void)area_.gotoRec(saved_recno);
        }
        throw;
    }
}

// XIDX-TXN-02 M1 -- realtime CNX maintenance.
//
// These were no-ops that set stale_ and returned NORMALLY, so every CNX edit
// left the order wrong while reporting success. They now maintain the loaded
// permutation, which is what makes an ordered traversal immediately after a
// REPLACE correct. Realtime is a property of the in-memory payload; persisting
// it is a separate milestone (see PERSISTENCE below).
//
// HOW A KEYLESS INDEX IS MAINTAINED. A CNX RUN1 payload stores 4 bytes per
// recno and NO keys (cnx_document.cpp:81 -> InxEntry{"", rn}); CnxCursor::fill_
// confirms it by returning outKey = Key{}. So entries_ is a PERMUTATION, and
// there is nothing stored to binary-search against. The table is the ordering
// authority instead -- exactly as it is for a rebuild -- so upsert locates its
// insertion point by comparing the edited record's live field value against the
// live field value of the record at each probe position. About log2(n) record
// reads per edit, no key storage, no format change.
//
// This is why the first attempt failed, and the failure is worth keeping: it
// routed through key-ordered InxPayload mutators, and against an all-empty-key
// vector lower_bound always returns end(), so the delete removed nothing and
// the insert appended at the bottom. Measured as
// "emitted_del=1 emitted_ins=1 ... leftStale=no" with the traversal order
// unchanged -- broken AND silent, strictly worse than broken and honest.
//
// WHY THE SEAM'S KEY IS IGNORED. apply_replace_snapshot supplies before/after
// keys, but those are normalized by the capture path, not by
// derive_sort_entry_. Ordering by one and rebuilding by the other would let a
// REBUILD disagree with an in-session edit. Reading the field through the SAME
// helper a rebuild uses makes the two agree by construction rather than by
// review. erase locates by recno for the same reason: it needs no key at all,
// so it cannot disagree about one.
//
// ORDERING WITHIN apply_replace_snapshot. Deletes are emitted before inserts,
// so by the time upsert probes, rec is already out of the permutation and
// cannot be encountered as its own comparand. An insert with no matching
// delete (APPEND, or a tag absent from the before-image) is equally safe: rec
// was not in the permutation to begin with.
//
// WHY stale_ IS NOT SET ON THE SUCCESS PATH. stale_ means "the index does not
// reflect the table." Once the permutation carries the edit that is false, and
// apply_replace_snapshot reports a false->true wasStale() transition as
// "record written, but index update failed". Leaving stale_ set would warn
// about maintenance that now happens. When maintenance is genuinely NOT
// possible -- no document, no active tag, tag names no field, a probe that
// cannot be read -- stale_ IS set and the warning fires correctly.
//
// PERSISTENCE IS DELIBERATELY NOT HERE. A RAM-resident container has no
// durability requirement: it cannot outlive its process, so there is nothing a
// torn write could corrupt, and RAM/vdisk tables are the case this milestone
// exists to serve. A disk-resident container still needs a persist-once-at-
// close/commit step; until that lands, an edited disk CNX is correct for the
// session and reverts to its last rebuilt order afterwards. Writing per edit
// was rejected: RUN1 is 4 bytes per recno, so one tag block for a 1M-row table
// is about 4 MB, and appending that on every single-record edit is not realtime
// at any useful scale. See
// XIDX_TXN_02_M0_ADDENDUM_PERSISTENCE_SEAM_V1_20260731.md.
//
// .inx AND .idx ARE UNTOUCHED. Their formats and their code are not this lane's
// to change. Everything above is CNX-owned and reaches InxPayload only through
// its EXISTING public surface -- entries() to read, fromEntries1Inx() to
// rebuild one. The cost is an O(n) vector copy per edit, which is a knowingly
// accepted first cut: it is correct, it is contained, and it can be optimized
// behind this same seam without touching the INX side.
void CnxBackend::upsert(const Key& key, RecNo rec)
{
    (void)key;   // ordering authority is the live field value, not the seam key

    CnxTag* tag = activeTag_();
    if (!tag) {
        stale_ = true;
        return;
    }

    const std::string tag_name = upper_copy_ascii_(tag->tagName());

    int field1 = 0;
    SortKind_ kind = SortKind_::Other;
    if (!tag_field_and_kind_(area_, tag_name, field1, kind)) {
        stale_ = true;
        return;
    }

    const int saved_recno = area_.recno();
    bool ok = false;

    try {
        SortEntry_ target{};
        if (read_sort_entry_for_recno_(area_, field1, kind, rec, target)) {
            std::vector<InxEntry> entries = tag->payload().entries();

            // Lower-bound over the permutation: find the first position whose
            // record does NOT sort before the edited record.
            std::size_t lo = 0;
            std::size_t hi = entries.size();
            bool probes_ok = true;

            while (lo < hi) {
                const std::size_t mid = lo + (hi - lo) / 2;

                SortEntry_ probe{};
                if (!read_sort_entry_for_recno_(area_, field1, kind,
                                                entries[mid].recno, probe)) {
                    probes_ok = false;
                    break;
                }

                if (sort_entry_less_(probe, target, kind)) lo = mid + 1;
                else                                       hi = mid;
            }

            if (probes_ok) {
                entries.insert(entries.begin() + static_cast<std::ptrdiff_t>(lo),
                               InxEntry{std::string{}, rec});
                tag->payload() = InxPayload::fromEntries1Inx(tag_name, entries);
                ok = true;
            }
        }
    } catch (...) {
        ok = false;
    }

    if (saved_recno > 0) {
        (void)area_.gotoRec(saved_recno);
    }

    if (!ok) stale_ = true;
}

void CnxBackend::erase(const Key& key, RecNo rec)
{
    (void)key;   // located by recno; a keyless payload has no key to match on

    CnxTag* tag = activeTag_();
    if (!tag) {
        stale_ = true;
        return;
    }

    std::vector<InxEntry> entries = tag->payload().entries();

    for (std::size_t i = 0; i < entries.size(); ++i) {
        if (entries[i].recno != rec) continue;

        entries.erase(entries.begin() + static_cast<std::ptrdiff_t>(i));
        tag->payload() = InxPayload::fromEntries1Inx(
            upper_copy_ascii_(tag->tagName()), entries);
        return;
    }

    // Absent is not a failure: a record that was never indexed, or was already
    // removed, needs no maintenance. Setting stale_ here would warn on every
    // edit to an unindexed record.
}

std::unique_ptr<Cursor> CnxBackend::seek(const Key& key) const
{
    const CnxTag* tag = activeTag_();
    if (!tag) return nullptr;

    const InxPayload& payload = tag->payload();
    const std::string probe = key_to_string_safe(key);

    std::optional<std::size_t> pos = payload.seekFirstGe(probe);
    if (!pos) return std::make_unique<CnxCursor>(&payload, std::nullopt, std::nullopt);

    return std::make_unique<CnxCursor>(&payload, pos, payload.bottomPos());
}

std::unique_ptr<Cursor> CnxBackend::scan(const Key& low, const Key& high) const
{
    const CnxTag* tag = activeTag_();
    if (!tag) return nullptr;

    const InxPayload& payload = tag->payload();
    const std::string low_key = key_to_string_safe(low);
    const std::string high_key = key_to_string_safe(high);

    std::optional<std::size_t> first = payload.entries().empty()
        ? std::nullopt
        : payload.seekFirstGe(low_key);

    std::optional<std::size_t> last = payload.bottomPos();

    (void)high_key;

    return std::make_unique<CnxCursor>(&payload, first, last);
}

void CnxBackend::setTag(const std::string& tag_upper)
{
    const std::string want = upper_copy_ascii_(tag_upper);
    (void)doc_.selectTagByName(want);
    active_tag_upper_ = want;
}

bool CnxBackend::selectTag(const std::string& tag_upper)
{
    const std::string want = upper_copy_ascii_(tag_upper);
    if (!doc_.selectTagByName(want)) return false;
    active_tag_upper_ = want;
    return true;
}

std::string CnxBackend::activeTag() const
{
    if (const CnxTag* t = activeTag_()) {
        return t->tagName();
    }
    return std::string{};
}

std::vector<std::string> CnxBackend::listTags() const
{
    std::vector<std::string> out;
    out.reserve(doc_.tagCount());
    for (const auto& t : doc_.tags()) {
        out.push_back(t.tagName());
    }
    return out;
}

} // namespace xindex