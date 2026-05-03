#pragma once

#include "xindex/inx_payload.hpp"

#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace xbase { class DbArea; }

namespace xindex {

struct CnxHeader {
    char magic[4]{'C','N','X','1'};
    std::uint16_t version{1};
    std::uint16_t header_size{sizeof(CnxHeader)};

    std::uint32_t flags{0};
    std::uint32_t tag_count{0};
    std::uint32_t active_tag_index{0};

    std::uint32_t directory_offset{0};
    std::uint32_t directory_size{0};

    std::uint32_t record_count_snapshot{0};
    std::uint64_t build_timestamp{0};
};

class CnxTag final {
public:
    struct Meta {
        std::string tag_name;
        std::string expr_token;
        bool ascending{true};

        InxPayload::Format embedded_fmt{InxPayload::Format::Unknown};

        std::uint16_t field_type{0};
        std::uint16_t key_len{0};
        std::uint32_t record_count{0};

        std::uint32_t payload_offset{0};
        std::uint32_t payload_size{0};
    };

    CnxTag() = default;
    CnxTag(Meta meta, InxPayload payload)
        : meta_(std::move(meta)), payload_(std::move(payload)) {}

    void clear() noexcept;
    bool empty() const noexcept;

    const Meta& meta() const noexcept { return meta_; }
    Meta& meta() noexcept { return meta_; }

    const InxPayload& payload() const noexcept { return payload_; }
    InxPayload& payload() noexcept { return payload_; }

    const std::string& tagName() const noexcept { return meta_.tag_name; }
    const std::string& exprToken() const noexcept { return meta_.expr_token; }
    bool ascending() const noexcept { return meta_.ascending; }

private:
    Meta meta_{};
    InxPayload payload_{};
};

class CnxDocument final {
public:
    CnxDocument() = default;

    void clear() noexcept;
    bool empty() const noexcept { return tags_.empty(); }

    bool open(const std::filesystem::path& path, xbase::DbArea& area, std::string* err = nullptr);
    bool save(const std::filesystem::path& path, std::string* err = nullptr) const;

    const CnxHeader& header() const noexcept { return header_; }
    CnxHeader& header() noexcept { return header_; }

    std::size_t tagCount() const noexcept { return tags_.size(); }

    const CnxTag& tagAt(std::size_t i) const;
    CnxTag& tagAt(std::size_t i);

    const std::vector<CnxTag>& tags() const noexcept { return tags_; }
    std::vector<CnxTag>& tags() noexcept { return tags_; }

    bool selectTagByIndex(std::size_t i) noexcept;
    bool selectTagByName(const std::string& tag_name);

    std::size_t activeTagIndex() const noexcept { return active_tag_index_; }

    const CnxTag* activeTag() const noexcept;
    CnxTag* activeTag() noexcept;

private:
    CnxHeader header_{};
    std::vector<CnxTag> tags_{};
    std::size_t active_tag_index_{0};

private:
    static std::string upper_copy_ascii_(std::string s);
};

} // namespace xindex
