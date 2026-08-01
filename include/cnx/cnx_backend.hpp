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
    // SCOPE: the maintained permutation is IN MEMORY. A disk-resident CNX is
    // correct for the session and reverts to its last rebuilt order after
    // close; persistence is a separate milestone. That does not make this
    // false -- the claim is about maintenance across a mutation, not durability
    // -- but a caller reasoning about restart must not read it as durability.
    bool maintainsIncrementally() const override { return true; }

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

private:
    static std::string upper_copy_ascii_(std::string s);

    const CnxTag* activeTag_() const noexcept;
    CnxTag* activeTag_() noexcept;
};

} // namespace xindex