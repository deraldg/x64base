// xbase_cli.hpp
// CLI / shell integration extensions for xbase.
// This header must not be included by non-CLI consumers such as pydottalk
// unless they intentionally provide compatible implementations.

#pragma once

#include <string>
#include "xbase.hpp"

namespace xbase::cli {

// Buffered/shell-aware replace entry point.
// Contract:
// - field1 is 1-based and already resolved by caller
// - stored_value is already normalized into on-disk form
// - in TABLE ON mode, this buffers only and does not lock/write
// - in TABLE OFF mode, this delegates to DbArea::replaceFieldStored()
// - may update CLI-side dirty/stale state
// - may use shell/work-area context if needed
bool replaceFieldStored(DbArea& area, int field1, const std::string& stored_value, std::string* err = nullptr);

// Optional helper for CLI-side stale-field marking after a core mutation.
// Safe to call from command code; non-CLI consumers should not depend on it.
void mark_all_fields_stale_best_effort(DbArea& area, int area0);

// Optional helper for CLI-side area resolution when shell work-area context exists.
// Returns -1 when unavailable.
int resolve_current_index(DbArea& area);

} // namespace xbase::cli