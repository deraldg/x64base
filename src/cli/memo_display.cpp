// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "cli/memo_display.hpp"

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "xbase/x64_memo_slot.hpp"
#include "memo/memo_auto.hpp"
#include "memo/memostore.hpp"

#include <cstdint>
#include <string>

namespace cli_memo
{
namespace
{

// THE PREDICATE AND THE PARSER HAVE ONE OWNER -- xbase/x64_memo_slot.hpp (R149).
// What stood here were two of ten identical private bodies. Deleting them is
// the point: this predicate decides what a field READ returns, whether a value
// may be treated as an object id, and whether a WRITE lays down raw bytes --
// three layers that must not be able to disagree.
using xbase::is_x64_memo_field;
using xbase::parse_u64_or_zero;

static dottalk::memo::MemoStore* memo_store_for_area(xbase::DbArea& area) noexcept
{
    auto* backend = cli_memo::memo_backend_for(area);
    if (!backend) return nullptr;
    return dynamic_cast<dottalk::memo::MemoStore*>(backend);
}

} // namespace

std::string resolve_display_value(xbase::DbArea& area,
                                  int field1,
                                  const std::string& raw_value)
{
    if (!is_x64_memo_field(area, field1))
        return raw_value;

    const std::uint64_t object_id = parse_u64_or_zero(raw_value);
    if (object_id == 0)
        return std::string{};

    auto* store = memo_store_for_area(area);
    if (!store)
        return raw_value;

    std::string text;
    if (!store->get_text_id(object_id, text, nullptr))
        return raw_value;

    return text;
}

} // namespace cli_memo