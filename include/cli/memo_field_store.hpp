#pragma once

// DD-050 shared x64 memo field helper
//
// Shared CLI helper for storing user text into x64 M fields.
// This centralizes the memo object-id conversion that REPLACE already proved
// and DD-048 temporarily duplicated inside IMPORT.
//
// This header is inline-only to avoid CMake/source-list changes in the cleanup pass.

#include <cstdint>
#include <string>
#include <string_view>

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "memo/memo_auto.hpp"
#include "memo/memostore.hpp"

namespace dottalk::cli::memo_field_store {

inline bool is_x64_memo_field(const DbArea& area, int field1)
{
    if (field1 < 1 || field1 > area.fieldCount()) return false;
    if (area.versionByte() != xbase::DBF_VERSION_64) return false;

    const auto& f = area.fields()[static_cast<std::size_t>(field1 - 1)];
    return (f.type == 'M' || f.type == 'm') &&
           f.length == xbase::X64_MEMO_FIELD_LEN;
}

inline std::uint64_t parse_u64_or_zero(const std::string& s)
{
    if (s.empty()) return 0;
    try {
        std::size_t used = 0;
        const unsigned long long v = std::stoull(s, &used, 10);
        if (used != s.size()) return 0;
        return static_cast<std::uint64_t>(v);
    } catch (...) {
        return 0;
    }
}

inline dottalk::memo::MemoStore* memo_store_for_area(DbArea& area) noexcept
{
    auto* backend = cli_memo::memo_backend_for(area);
    if (!backend) return nullptr;
    return dynamic_cast<dottalk::memo::MemoStore*>(backend);
}

inline bool build_x64_memo_stored_value(DbArea& area,
                                         int field1,
                                         const std::string& user_value,
                                         std::string& stored_value_out,
                                         std::string& err_out)
{
    stored_value_out.clear();
    err_out.clear();

    if (!is_x64_memo_field(area, field1)) {
        stored_value_out = user_value;
        return true;
    }

    auto* store = memo_store_for_area(area);
    if (!store) {
        err_out = "memo backend not attached";
        return false;
    }

    std::uint64_t old_object_id = 0;
    try {
        old_object_id = parse_u64_or_zero(area.get(field1));
    } catch (...) {
        old_object_id = 0;
    }

    if (user_value.empty()) {
        stored_value_out.clear();
        return true;
    }

    std::uint64_t new_object_id = 0;
    if (!store->update_text_id(old_object_id,
                               std::string_view(user_value),
                               new_object_id,
                               nullptr))
    {
        err_out = "memo store update failed";
        return false;
    }

    stored_value_out = (new_object_id == 0) ? std::string() : std::to_string(new_object_id);
    return true;
}

inline bool store_user_value(DbArea& area,
                             int field1,
                             const std::string& user_value,
                             std::string& err_out)
{
    std::string stored_value;
    if (!build_x64_memo_stored_value(area, field1, user_value, stored_value, err_out)) {
        return false;
    }

    area.set(field1, stored_value);
    return true;
}

} // namespace dottalk::cli::memo_field_store
