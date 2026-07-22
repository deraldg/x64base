#pragma once
//
// CdxNativeBackend — native CDX (V64) key backend, LMDB-free.
//
// Twin of CnxBackend, but serves a uint64 index: it collects recnos via
// DbArea::recno64(), encodes 8-byte-recno "RUN8" blocks into a .cdx container
// (through the ramfs-routable cdxfile:: layer), and reads them back via
// CdxDocument. This is the "build for big" native index — maxRecordNumber() is
// the full 64-bit range (CNX/uint32 remains the small fallback).
//
// Distinct from xindex::CdxBackend (the CDX-over-LMDB backend); this one is the
// standalone native key store that never touches LMDB.

#include "xindex/index_backend.hpp"
#include "xindex/key_common.hpp"
#include "cdx/cdx_document.hpp"
#include "xindex/cdx_backend.hpp"   // defines ITagBackend

#include <cstdint>
#include <filesystem>
#include <memory>
#include <string>
#include <vector>

namespace xbase { class DbArea; }

namespace xindex {

class CdxNativeBackend final : public ITagBackend
{
public:
    CdxNativeBackend(xbase::DbArea& area, std::string cdx_path = {}, std::string tag_upper = {});
    ~CdxNativeBackend() override = default;

    bool open(const std::string& path) override;
    void close() override;

    void setFingerprint(std::uint32_t fp) override { fingerprint_ = fp; }
    bool wasStale() const override { return stale_; }

    void rebuild() override;

    void upsert(const Key& key, RecNo rec) override;
    void erase (const Key& key, RecNo rec) override;

    // Native CDX V64: full 64-bit recno index ("build for big").
    std::uint64_t maxRecordNumber() const override { return UINT64_MAX; }

    std::unique_ptr<Cursor> seek(const Key& key) const override;
    std::unique_ptr<Cursor> scan(const Key& low, const Key& high) const override;

    // ITagBackend
    void setTag(const std::string& tag_upper) override;
    std::string activeTag() const override;

    bool selectTag(const std::string& tag_upper);
    std::vector<std::string> listTags() const;

    const std::filesystem::path& path() const noexcept { return cdx_path_; }
    const CdxDocument& document() const noexcept { return doc_; }
    CdxDocument& document() noexcept { return doc_; }

    void invalidate();

private:
    class CdxCursor;

private:
    xbase::DbArea& area_;
    std::filesystem::path cdx_path_{};

    CdxDocument doc_{};
    std::string active_tag_upper_{};

    std::uint32_t fingerprint_{0};
    bool stale_{false};

private:
    static std::string upper_copy_ascii_(std::string s);

    const CdxTag* activeTag_() const noexcept;
    CdxTag* activeTag_() noexcept;
};

} // namespace xindex
