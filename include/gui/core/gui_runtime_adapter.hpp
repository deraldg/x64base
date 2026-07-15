#pragma once
// @dottalk.contract v1
// family: selfdoc.api_contract
// component: gui_runtime_adapter
// role: immutable GUI model projection from runtime-owned table state
// owner: DotTalk++ GUI open-architecture lane
// contract: Runtime adapters may project DbArea state into GUI models, but they must not redefine database semantics or take ownership of engine truth.
// authority: xbase/memo/xindex/xexpr and dottalkpp runtime remain authoritative; adapters are translation seams only.
// gui: frontends should render AreaInfo/TableSnapshot results rather than reading mutable runtime state directly from widgets.
// @dottalk.contract.end

#include "gui/core/model.hpp"

#include <cstdint>
#include <string>

namespace xbase {
class DbArea;
}

namespace dottalk::gui {

AreaInfo gui_area_info_from_dbarea(AreaId area_id,
                                   bool active,
                                   const xbase::DbArea& area,
                                   const std::string& display_name);

TableSnapshot gui_snapshot_from_dbarea(AreaId area_id,
                                       xbase::DbArea& area,
                                       const std::string& display_name,
                                       std::uint64_t first_record,
                                       std::uint32_t max_records);

} // namespace dottalk::gui
