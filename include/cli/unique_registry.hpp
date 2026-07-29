// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
// Unique field registry (per work area).
// Phase 1: session-scoped in-memory flags; no engine changes required.

#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace xbase { class DbArea; }

namespace unique_reg {

// Return a stable bucket name for the current area (Phase 1 uses "AREA").
// You can later change this to alias/area number without breaking callers.
std::string current_alias_or_area_name(xbase::DbArea& A);

// Register/unregister a field as unique for the current area.
void set_unique_field(xbase::DbArea& A, const std::string& field_name, bool on);

// Query whether a field is marked unique for the current area.
bool is_unique_field(xbase::DbArea& A, const std::string& field_name);
// AIF-074 P1.1: designate a field as the PRIMARY key for the current area's
// table (implies unique; one primary per table, last set wins).
void set_primary_field(xbase::DbArea& A, const std::string& field_name);
// The current table's primary field, or empty when none is designated.
std::string primary_field(xbase::DbArea& A);

// List all unique fields for the current area.
std::vector<std::string> list_unique_fields(xbase::DbArea& A);

// For diagnostics (read-only snapshot of the registry).
const std::unordered_map<std::string, std::unordered_set<std::string>>& snapshot();

} // namespace unique_reg



