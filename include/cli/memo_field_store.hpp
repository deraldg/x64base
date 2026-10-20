// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

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
#include "xbase/x64_memo_slot.hpp"
#include "memo/memo_auto.hpp"
#include "memo/memostore.hpp"

namespace dottalk::cli::memo_field_store {

// ONE OWNER, NOT A SECOND COPY. These two were the shared pair -- and still
// one of ten identical private bodies, because seven TUs did not use them.
// They now NAME the owner in xbase/x64_memo_slot.hpp (R149) rather than
// re-deriving it, so a caller that reaches this header and a caller that
// reaches the owner directly cannot be given different answers.
using xbase::is_x64_memo_field;
using xbase::parse_u64_or_zero;

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
