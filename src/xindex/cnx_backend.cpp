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

// Was the container left mid-save? CNX_HDRF_DIRTY is raised before the first
// append and cleared by write_tagdir at the commit point, so finding it set at
// open means some process died between the two.
//
// AIF-079: this flag has existed since the format was defined, was written only
// by PACK and ZAP, was cleared unconditionally by write_tagdir, and was read by
// NOBODY. A recovery marker that nothing inspects is not a safety net, it is
// decoration -- and M2 makes it load-bearing, so it had to stop being either
// unset or unread. Only call this on a container already proven openable:
// cnxfile::open CREATES a missing file, so probing a nonexistent path would
// leave a stray empty container behind.
static bool container_is_dirty_(const std::string& path)
{
    cnxfile::CNXHandle* h = nullptr;
    if (!cnxfile::open(path, h) || !h) return false;

    cnxfile::CNXHeader hdr{};
    const bool ok = cnxfile::read_header(h, hdr);
    cnxfile::close(h);

    return ok && (hdr.flags & cnxfile::CNX_HDRF_DIRTY) != 0;
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

    // Recovery, after the document is known to load: an interrupted save left
    // the directory pointing at the PREVIOUS blocks, which are intact, so this
    // is not repairing corruption -- it is discarding an ordering we cannot
    // prove. rebuild() reloads doc_ and clears the flag on its way through.
    if (container_is_dirty_(cnx_path_.string())) {
        std::cout << "[CNX DIRTY] container was not cleanly saved; rebuilding: "
                  << cnx_path_.string() << "\n";
        try {
            rebuild();
        } catch (const std::exception& ex) {
            std::cout << "[CNX DIRTY] rebuild failed: " << ex.what() << "\n";
            return false;
        }
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
    // Save-on-close, one half of the M2 durability trigger (COMMIT is the
    // other). Best-effort by necessity: close() returns void and runs on
    // teardown paths with nowhere to report to. That is acceptable ONLY
    // because a failed save leaves CNX_HDRF_DIRTY set in the container, so the
    // next open rebuilds instead of trusting it. The cost of losing this race
    // is a rebuild, not a wrong answer.
    if (!dirty_tags_.empty()) {
        std::string err;
        if (!save(&err)) {
            std::cout << "[CNX SAVE FAILED] " << err
                      << " (container left dirty; next open will rebuild)\n";
        }
    }

    doc_.clear();
    cnx_path_.clear();
    active_tag_upper_.clear();
    dirty_tags_.clear();
    stale_ = false;
}

void CnxBackend::invalidate()
{
    stale_ = true;
}

// Serialize one tag's ordering as a RUN1 block.
//
// SHARED BY rebuild() AND save() ON PURPOSE. They write the same bytes for the
// same ordering, so the only difference between "rebuilt from the table" and
// "maintained in memory then persisted" is where the recno vector came from --
// never the encoding. This is the same anti-drift argument that made
// derive_sort_entry_/sort_entry_less_ shared: two writers of one format WILL
// diverge, and the divergence shows up as a container that reads back subtly
// wrong long after the change that caused it.
static void build_run1_block_(std::uint32_t tag_id,
                              const std::vector<std::uint32_t>& recnos,
                              std::vector<std::uint8_t>& out)
{
    out.clear();
    out.reserve(32 + recnos.size() * 4);

    out.push_back('R');
    out.push_back('U');
    out.push_back('N');
    out.push_back('1');

    append_u32_le_(out, 1u);       // version
    append_u32_le_(out, tag_id);
    append_u32_le_(out, 0u);       // flags
    append_u32_le_(out, 0u);       // reserved0
    append_u32_le_(out, static_cast<std::uint32_t>(recnos.size()));
    append_u32_le_(out, 0u);       // reserved1

    append_u32_le_(out, static_cast<std::uint32_t>(32u + recnos.size() * 4u));

    for (std::uint32_t r : recnos) {
        append_u32_le_(out, r);
    }
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
            build_run1_block_(static_cast<std::uint32_t>(tag.tag_id), recnos, block);

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

        // A rebuild just wrote every tag from the table, so nothing is owed.
        // Not clearing this would make the next save() re-append blocks
        // identical to the ones rebuild() has already committed.
        dirty_tags_.clear();

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
                dirty_tags_.insert(tag_name);
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

    const std::string tag_name = upper_copy_ascii_(tag->tagName());

    for (std::size_t i = 0; i < entries.size(); ++i) {
        if (entries[i].recno != rec) continue;

        entries.erase(entries.begin() + static_cast<std::ptrdiff_t>(i));
        tag->payload() = InxPayload::fromEntries1Inx(tag_name, entries);
        dirty_tags_.insert(tag_name);
        return;
    }

    // Absent is not a failure: a record that was never indexed, or was already
    // removed, needs no maintenance. Setting stale_ here would warn on every
    // edit to an unindexed record.
}

// XIDX-TXN-02 M2 -- persist the maintained permutation (append-and-switch).
//
// SEQUENCE, and the order is the whole design:
//
//   1. set CNX_HDRF_DIRTY and flush the header  -- container is now suspect
//   2. append a fresh RUN1 block per mutated tag -- old blocks still referenced
//   3. write the tag directory                   -- SINGLE COMMIT POINT; this
//      repoints every changed tag at once and clears CNX_HDRF_DIRTY
//
// Interrupted before step 3, the directory still points at the previous blocks,
// which were never touched, and the dirty flag says so. Interrupted after, the
// new blocks are live. There is no window in which a tag points at a partially
// written block. That is shadow paging, and it is why this needs no temp file
// and no rename -- which matters because ramfs has neither (and does not
// truncate either: ramfs.cpp:259-263 returns an existing RamFile unchanged, so
// an in-place rewrite would leave the tail of a longer previous version).
//
// DURABILITY BOUNDARY, stated rather than implied: this protects against
// PROCESS death, not power loss. cnxfile has no fsync, so step 3 reaching the
// OS before step 2 is prevented only by both going through the same stream in
// order. Power-loss safety needs an fsync barrier between 2 and 3 plus one
// after 3, and that is an addition to the cnxfile I/O layer, not to this
// function. Do not read the dirty flag as more than it is.
//
// WHY NOT CnxDocument::save(). That member exists and is a stub. Writing
// through cnxfile here keeps save() byte-identical to rebuild() by sharing
// build_run1_block_, which is the property worth having; routing through a
// second serializer is how the two would drift. The stub stays a stub, and
// stays on the record as one.
bool CnxBackend::save(std::string* err)
{
    auto fail = [&](const std::string& m) -> bool {
        if (err) *err = m;
        return false;
    };

    // Nothing owed is success, and it costs no file open. See
    // IIndexBackend::save on why this is not reported as a failure.
    if (dirty_tags_.empty()) return true;

    if (cnx_path_.empty()) return fail("CNX save: no container path");

    cnxfile::CNXHandle* h = nullptr;
    if (!cnxfile::open(cnx_path_.string(), h) || !h) {
        return fail("CNX save: unable to open container: " + cnx_path_.string());
    }

    std::vector<cnxfile::TagInfo> tags;
    if (!cnxfile::read_tagdir(h, tags)) {
        cnxfile::close(h);
        return fail("CNX save: read_tagdir failed");
    }

    // Step 1. Publish "suspect" BEFORE touching anything.
    cnxfile::CNXHeader hdr{};
    if (!cnxfile::read_header(h, hdr)) {
        cnxfile::close(h);
        return fail("CNX save: read_header failed");
    }
    hdr.flags |= cnxfile::CNX_HDRF_DIRTY;
    if (!cnxfile::flush_header(h, hdr)) {
        cnxfile::close(h);
        return fail("CNX save: could not mark container dirty");
    }

    try {
        // Step 2. Append one fresh block per mutated tag.
        for (auto& tag : tags) {
            const std::string tag_name = upper_copy_ascii_(tag.name);
            if (dirty_tags_.find(tag_name) == dirty_tags_.end()) continue;

            const CnxTag* src = nullptr;
            for (const auto& t : doc_.tags()) {
                if (upper_copy_ascii_(t.tagName()) == tag_name) { src = &t; break; }
            }

            // Mutated but no longer loaded: leave the existing block alone
            // rather than write an ordering we cannot see. The tag keeps its
            // last good root_page_off.
            if (!src) continue;

            const std::vector<InxEntry>& entries = src->payload().entries();

            std::vector<std::uint32_t> recnos;
            recnos.reserve(entries.size());
            for (const auto& e : entries) {
                recnos.push_back(static_cast<std::uint32_t>(e.recno));
            }

            std::vector<std::uint8_t> block;
            build_run1_block_(static_cast<std::uint32_t>(tag.tag_id), recnos, block);

            std::uint64_t root_off = 0;
            if (!cnxfile::append_bytes(h, block.data(), block.size(), root_off)) {
                throw std::runtime_error("CNX save: append_bytes failed for tag " + tag_name);
            }

            tag.root_page_off = root_off;
            tag.stats_rec     = static_cast<std::uint64_t>(recnos.size());
            tag.updated_ts    = static_cast<std::uint64_t>(std::time(nullptr));

            std::cout << "[CNX SAVE] tag=" << tag_name
                      << " recs=" << recnos.size()
                      << " root=" << root_off << "\n";
        }

        // Step 3. Commit. Unconditional even when nothing was appended, so the
        // dirty flag raised in step 1 is always cleared on a successful pass.
        if (!cnxfile::write_tagdir(h, tags)) {
            throw std::runtime_error("CNX save: write_tagdir failed");
        }
    } catch (const std::exception& ex) {
        cnxfile::close(h);
        // dirty_tags_ deliberately NOT cleared: the work is still owed, and a
        // later save or a rebuild must still do it. The container is left with
        // CNX_HDRF_DIRTY set, which is the correct report.
        return fail(ex.what());
    } catch (...) {
        cnxfile::close(h);
        return fail("CNX save: unknown failure");
    }

    cnxfile::close(h);
    dirty_tags_.clear();
    return true;
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