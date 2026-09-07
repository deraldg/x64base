// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

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

    // Metadata flags.
    //
    // CORRECTED 2026-09-06 (AIF-156). This read "UNIQUE / PRIMARY enforcement
    // remains index-backed", which deferred to a mechanism that does not
    // exist: no index writer carries a unique flag and CDX ADDTAG has no
    // UNIQUE keyword. The sentence sent every reader looking for enforcement
    // somewhere else, which is why there was none anywhere.
    //
    // PRIMARY IS NOW ENFORCED HERE, and it needs no index. Owner rulings
    // 2026-09-06: a primary key is never edited, never reused, and minted on
    // creation. Uniqueness is therefore a CONSEQUENCE of those three, not a
    // property to be checked -- so the question is never "does this value
    // already exist" (which would need an index probe) but "is this field the
    // primary key", which is field identity and costs one comparison.
    //
    // UNIQUE-without-PRIMARY is NOT enforced here and is not claimed to be.
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
