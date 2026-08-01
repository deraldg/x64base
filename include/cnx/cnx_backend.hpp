// @dottalk.file v1
// subsystem: cnx
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include "xindex/index_backend.hpp"
#include "xindex/key_common.hpp"
#include "cnx/cnx_document.hpp"
#include "xindex/cdx_backend.hpp"   // <-- REQUIRED (this defines ITagBackend)

#include <cstdint>
#include <filesystem>
#include <memory>
#include <set>
#include <string>
#include <vector>

namespace xbase { class DbArea; }

namespace xindex {

class CnxBackend final : public ITagBackend   // ✅ FIXED
{
public:
    CnxBackend(xbase::DbArea& area, std::string cnx_path = {}, std::string tag_upper = {});
    ~CnxBackend() override = default;

    bool open(const std::string& path) override;
    void close() override;

    void setFingerprint(std::uint32_t fp) override { fingerprint_ = fp; }
    bool wasStale() const override { return stale_; }

    void rebuild() override;

    void upsert(const Key& key, RecNo rec) override;
    void erase (const Key& key, RecNo rec) override;

    // Maintains, as of XIDX-TXN-02 M1 (2026-07-31). Before that these were
    // no-ops that set stale_ and returned normally, and this would have been
    // false. Runtime-proven by regression CNXLIVE: after a REPLACE that moves
    // an indexed value, the ordered traversal is correct with NO rebuild
    // between, and L_T6 asserts the maintained ordering is identical to the one
    // a REBUILD produces -- which is the obligation that comes with claiming
    // true here (see IIndexBackend::maintainsIncrementally).
    //
    // SCOPE: this claim is about maintenance across a mutation, NOT durability.
    // Those are separate axes and CNX is the reason the seam has both: from M1
    // until XIDX-TXN-02 M2 the maintained permutation lived only in memory, so
    // the ordering was right all session and reverted on the next load. M2 adds
    // save() below; a caller reasoning about restart asks THAT, not this.
    bool maintainsIncrementally() const override { return true; }

    // XIDX-TXN-02 M2 -- persist the maintained permutation.
    //
    // Append-and-switch: serialize each mutated tag to a fresh RUN1 block,
    // append it, repoint that tag's root_page_off, then write the tag
    // directory. The directory write is the single commit point, so a failure
    // before it leaves the previous block still referenced and intact. This is
    // shadow paging, and it is the same sequence rebuild() already performs --
    // which is why it is the mechanism rather than temp-plus-rename: it needs
    // no rename primitive, and ramfs has none (it has no truncate either).
    bool save(std::string* err = nullptr) override;

    // Classic CNX stores record numbers in 4 bytes — 32-bit ceiling (RECNO64).
    std::uint64_t maxRecordNumber() const override { return UINT32_MAX; }

    std::unique_ptr<Cursor> seek(const Key& key) const override;
    std::unique_ptr<Cursor> scan(const Key& low, const Key& high) const override;

    // REQUIRED by ITagBackend
    void setTag(const std::string& tag_upper) override;
    std::string activeTag() const override;

    bool selectTag(const std::string& tag_upper);
    std::vector<std::string> listTags() const;

    const std::filesystem::path& path() const noexcept { return cnx_path_; }
    const CnxDocument& document() const noexcept { return doc_; }
    CnxDocument& document() noexcept { return doc_; }

    void invalidate();

private:
    class CnxCursor;

private:
    xbase::DbArea& area_;
    std::filesystem::path cnx_path_{};

    CnxDocument doc_{};
    std::string active_tag_upper_{};

    std::uint32_t fingerprint_{0};
    bool stale_{false};

    // Tags whose in-memory permutation has been mutated since the last load or
    // save. Only these are re-appended, so an untouched tag keeps its existing
    // block and its root_page_off: a save costs the tags that changed, not the
    // container. Empty means save() has nothing to do and returns success
    // without opening the file at all.
    std::set<std::string> dirty_tags_{};

private:
    static std::string upper_copy_ascii_(std::string s);

    const CnxTag* activeTag_() const noexcept;
    CnxTag* activeTag_() noexcept;
};

} // namespace xindex