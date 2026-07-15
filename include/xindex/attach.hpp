#pragma once
#include "xindex/index_manager.hpp" // brings in forward decl for xbase::DbArea via index_manager.hpp

namespace xindex {
IndexManager& ensure_manager(xbase::DbArea& area);
IndexManager* manager_if_attached(xbase::DbArea& area) noexcept;
const IndexManager* manager_if_attached(const xbase::DbArea& area) noexcept;
void detach_manager(xbase::DbArea& area) noexcept;
void install_xbase_index_hooks() noexcept;
} // namespace xindex

