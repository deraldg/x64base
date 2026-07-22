#pragma once
// include/identity/identity_bootstrap.hpp
// Process-wide identity store bootstrap (AIF-045 2b-i).
//
// Seeds an in-memory store from the standard role/permission catalog and the known profile
// homes (default / public / user / derald). This is the interim bootstrap: DBF-backed
// durability is 2b-ii, and a live filesystem scan of dottalkpp/user/* is a fast-follow.

#include "identity/identity_repository.hpp"

#include <string>

namespace dottalk::identity {

// Built once, on first use.
const InMemoryIdentityStore& identity_store();

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
