// rule_catalog.hpp
// DotTalk++ RULE catalog resolver.
//
// Public term: RULE.
// Internal purpose: resolve reusable validation rules and table field bindings
// into FieldConstraint objects consumed by field_constraints.cpp.
//
// First-pass file layout:
//   dottalkpp/data/SCHEMAS/rules.meta
//   dottalkpp/data/SCHEMAS/tables/<TABLE>.rules
//
// This layer is intentionally read-only and side-effect free.

#pragma once

#include "cli/field_constraints.hpp"
#include "xbase.hpp"

#include <optional>
#include <string>

namespace dottalk::constraints::rules {

// Resolve the rule bound to A.<field1>, if table rule files are present.
// Returns nullopt when no rule binding exists, no catalog exists, or the rule
// is not found. Caller may then fall back to bootstrap rules.
std::optional<FieldConstraint> constraint_for_field(const xbase::DbArea& A,
                                                    int field1);

// Human-readable location helpers for diagnostics / future RULE SHOW commands.
// They do not create files or directories.
std::string rules_catalog_path_for_area(const xbase::DbArea& A);
std::string table_rules_path_for_area(const xbase::DbArea& A);

} // namespace dottalk::constraints::rules
