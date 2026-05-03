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