// include/snx/snx_catalog.hpp
#pragma once

#include "snx/snx.hpp"
#include <optional>
#include <string>
#include <vector>

namespace xindex {

struct SnxTagMeta {
    std::string   name;
    std::uint32_t tag_id          = 0;
    std::uint32_t flags           = 0;
    std::uint32_t collation_id    = 0;
    std::uint32_t key_type        = 0;
    std::uint32_t key_len         = 0;
    std::uint64_t root_block_off  = 0;
    std::uint64_t stats_rec_count = 0;
};

struct SnxCatalog {
    snxfile::SNXHeader header{};
    std::optional<snxfile::TableBind> bind{};
    std::vector<SnxTagMeta> tags{};
    std::size_t active_tag_index = 0;

    void clear() noexcept {
        header = {};
        bind.reset();
        tags.clear();
        active_tag_index = 0;
    }

    bool empty() const noexcept {
        return tags.empty();
    }
};

} // namespace xindex