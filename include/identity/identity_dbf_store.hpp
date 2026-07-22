#pragma once
// include/identity/identity_dbf_store.hpp
// DBF / x64base persistence for the identity / RBAC catalog (AIF-045 2b-ii, APH-5).
//
// Serializes the nine InMemoryIdentityStore vectors to the nine SYS* identity
// tables (identity_schema.hpp) and reads them back, preserving the authoritative
// 64-bit IDs AND the portable string keys (Contract v1 Invariant 5). This is the
// self-hosting round-trip: x64base -> reload -> x64base with identity unchanged.
//
// This milestone (2b-ii M2/M3) provides explicit save/load/verify; it does NOT
// change the boot path — the static seed in identity_bootstrap.cpp stays the
// authority until the round-trip is proven and boot-from-DBF is deliberately
// adopted (with degraded read-only fallback) in a follow-on.

#include "identity/identity_repository.hpp"

#include <string>

namespace dottalk::identity {

// Default on-disk home: <data>/metadata/identity  (system-catalog convention).
std::string default_identity_dir();

// Create (overwriting) the nine SYS* tables under <dir> and populate them from
// the store's vectors. Returns false + err on any create/append failure.
bool save_identity_tables(const InMemoryIdentityStore& store,
                          const std::string& dir, std::string& err);

// Load the nine SYS* tables from <dir> into `out` (cleared first). Returns false
// + err if any table is missing or cannot be opened (the caller decides whether
// to fall back to the seed for degraded read-only startup).
bool load_identity_tables(const std::string& dir,
                          InMemoryIdentityStore& out, std::string& err);

} // namespace dottalk::identity
