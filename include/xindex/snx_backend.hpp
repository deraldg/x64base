// include/xindex/snx_backend.hpp
#pragma once

#include "xindex/index_backend.hpp"
#include "snx/snx_catalog.hpp"

#include <cstdint>
#include <filesystem>
#include <memory>
#include <string>
#include <vector>

namespace xbase { class DbArea; }

namespace xindex {

class SnxBackend final : public IIndexBackend {
public:
    SnxBackend(xbase::DbArea& area,
               std::string snx_path = {},
               std::string tag_upper = {});
    ~SnxBackend() override = default;

    bool open(const std::string& path) override;
    void close() override;

    void setFingerprint(std::uint32_t fp) override { fingerprint_ = fp; }
    bool wasStale() const override { return stale_; }

    void rebuild() override;

    void upsert(const Key& key, RecNo rec) override;
    void erase(const Key& key, RecNo rec) override;

    std::unique_ptr<Cursor> seek(const Key& key) const override;
    std::unique_ptr<Cursor> scan(const Key& low, const Key& high) const override;

    bool selectTag(const std::string& tag_upper);
    std::string activeTag() const;
    std::vector<std::string> listTags() const;

    const std::filesystem::path& path() const noexcept { return snx_path_; }
    const SnxCatalog& catalog() const noexcept { return catalog_; }
    SnxCatalog& catalog() noexcept { return catalog_; }

    void invalidate();

private:
    class SnxCursor;

    xbase::DbArea& area_;
    std::filesystem::path snx_path_{};

    SnxCatalog catalog_{};
    std::string active_tag_upper_{};

    std::uint32_t fingerprint_{0};
    bool stale_{false};

private:
    static std::string upper_copy_ascii_(std::string s);

    const SnxTagMeta* activeTag_() const noexcept;
    SnxTagMeta* activeTag_() noexcept;
};

} // namespace xindex