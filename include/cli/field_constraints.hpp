// field_constraints.hpp
// DotTalk++ first-pass field value constraint layer.
//
// Scope:
//   - Engine-neutral validation service for already-normalized store values.
//   - Intended call sites: REPLACE, REPLACE_MULTI Pass 1, APPEND finalization.
//   - Does not own DBF storage, TABLE buffering, memo payloads, or index updates.
//
// Current rule source:
//   - Small in-memory bootstrap catalog in field_constraints.cpp.
//   - Later replacement point: CDX/schema metadata loader.

#pragma once

#include "xbase.hpp"

#include <optional>
#include <string>
#include <vector>

namespace dottalk::constraints {

struct FieldConstraint {
    bool required{false};

    // Stored as strings so the same structure can describe numeric, currency,
    // date, and text constraints. Validation interprets these by field type.
    std::optional<std::string> min_value;
    std::optional<std::string> max_value;

    std::vector<std::string> enum_values;

    // Regex pattern. First-pass rule: apply only to character fields.
    std::optional<std::string> pattern;

    // Metadata flags. UNIQUE / PRIMARY enforcement remains index-backed.
    bool unique{false};
    bool primary{false};

    std::optional<std::string> default_value;
    std::string message;
};

struct ConstraintResult {
    bool ok{true};
    std::string message;
};

// Return the current bootstrap constraint for a field, if any.
// External rule addressing is field-name based; callers still pass field1 so
// command code can resolve once and avoid repeated name lookup.
std::optional<FieldConstraint> constraint_for_field(const xbase::DbArea& A,
                                                    int field1);

// Validate one already-normalized store value against field-level constraints.
// This does NOT replace existing type/storage validation. Call it after the
// current normalize/validate step, before A.set(), buffer staging, or writeCurrent().
bool validate_field_constraint_for_store(const xbase::DbArea& A,
                                         int field1,
                                         const std::string& stored_value,
                                         std::string& err_out);

// Validate the current in-memory record image. Intended for APPEND finalization
// after autokey/default generation and before the final writeCurrent().
bool validate_current_record_constraints(const xbase::DbArea& A,
                                         std::string& err_out);

} // namespace dottalk::constraints
