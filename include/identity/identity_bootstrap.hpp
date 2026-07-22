#pragma once
// include/identity/identity_bootstrap.hpp
// Process-wide identity store bootstrap (AIF-045 2b-i / 2b-iii).
//
// The store is now DBF-authoritative (2b-iii boot adoption): on first use the engine
// loads the identity catalog from data/metadata/identity if present; if the tables are
// absent it seeds from the standard role/permission catalog and PERSISTS them; if the
// tables are present but cannot be read it falls back to a READ-ONLY seed (degraded
// startup) rather than overwriting a corrupt catalog. This is the APH-5 self-hosting path.

#include "identity/identity_repository.hpp"

#include <string>

namespace dottalk::identity {

// How the process-wide store was populated at boot.
enum class StoreOrigin {
    Seed,          // tables absent -> seeded from catalog and persisted to DBF (writable)
    Dbf,           // tables present and loaded from DBF (authoritative, writable)
    DegradedSeed,  // tables present but unreadable -> read-only seed, DBF left untouched
};

// Load-or-seed boot logic against an explicit directory (testable, no singleton).
// origin/read_only report which path was taken.
InMemoryIdentityStore boot_identity_store(const std::string& dir,
                                          StoreOrigin& origin, bool& read_only);

// Built once, on first use (boots against data/metadata/identity).
const InMemoryIdentityStore& identity_store();

// Boot provenance of the process-wide store.
StoreOrigin identity_store_origin();
bool        identity_store_read_only();
const char* store_origin_name(StoreOrigin o);

// Portable-key lookups (return nullptr if absent).
inline const TeamMember* find_member_by_key(const InMemoryIdentityStore& s, const std::string& key) {
    for (const auto& m : s.members) if (m.key == key) return &m;
    return nullptr;
}
inline const Permission* find_permission_by_key(const InMemoryIdentityStore& s, const std::string& key) {
    for (const auto& p : s.permissions) if (p.key == key) return &p;
    return nullptr;
}
inline const User* find_user_by_id(const InMemoryIdentityStore& s, UserId id) {
    for (const auto& u : s.users) if (u.id == id) return &u;
    return nullptr;
}
inline const Role* find_role_by_id(const InMemoryIdentityStore& s, RoleId id) {
    for (const auto& r : s.roles) if (r.id == id) return &r;
    return nullptr;
}

} // namespace dottalk::identity
