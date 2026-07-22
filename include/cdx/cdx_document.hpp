#pragma once
//
// CdxDocument — native CDX (V64) in-memory index document.
//
// Twin of CnxDocument, but reads 8-byte-recno "RUN8" payloads from a .cdx
// container (via the ramfs-routable cdxfile:: layer) — a uint64 native index
// ("build for big"; CNX/RUN1 at uint32 is the small fallback). It reuses the
// generic in-memory tag/header structures from CnxDocument (aliased below as
// CdxTag/CdxHeader) and InxPayload, which carries uint64 recnos as of V4a.

#include "cnx/cnx_document.hpp"   // xindex::CnxTag, CnxHeader, InxPayload

#include <cstddef>
#include <filesystem>
#include <string>
#include <vector>

namespace xindex {

// The native container tag/header model is format-neutral; CDX reuses it.
using CdxHeader = CnxHeader;
using CdxTag    = CnxTag;

class CdxDocument final {
public:
    CdxDocument() = default;

    void clear() noexcept;
    bool empty() const noexcept { return tags_.empty(); }

    // Load tag directory + RUN8 payloads from a .cdx (disk or ramfs).
    bool open(const std::filesystem::path& path, std::string* err = nullptr);

    const CdxHeader& header() const noexcept { return header_; }
    CdxHeader& header() noexcept { return header_; }

    std::size_t tagCount() const noexcept { return tags_.size(); }

    const CdxTag& tagAt(std::size_t i) const { return tags_.at(i); }
    CdxTag& tagAt(std::size_t i) { return tags_.at(i); }

    const std::vector<CdxTag>& tags() const noexcept { return tags_; }
    std::vector<CdxTag>& tags() noexcept { return tags_; }

    bool selectTagByIndex(std::size_t i) noexcept;
    bool selectTagByName(const std::string& tag_name);

    std::size_t activeTagIndex() const noexcept { return active_tag_index_; }

    const CdxTag* activeTag() const noexcept;
    CdxTag* activeTag() noexcept;

private:
    CdxHeader header_{};
    std::vector<CdxTag> tags_{};
    std::size_t active_tag_index_{0};

    static std::string upper_copy_ascii_(std::string s);
};

} // namespace xindex
