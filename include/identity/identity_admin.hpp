#pragma once
// include/identity/identity_admin.hpp
// Runtime administration of the identity / RBAC catalog (AIF-045 2c).
//
// The mutation surface behind USER ADD / REQUEST / APPROVE / DENY / REVOKE. Each op mutates
// the process store and persists it (persist_identity_store). All ops refuse when the store
// booted read-only (degraded startup).
//
// Acceptance model (owner decision 2026-07-22): approving an agent's request MINTS a scoped
// ALLOW override (eligibility) AND a time-boxed authorization grant (this-action approval),
// default 24h. So an approved agent's authorize() flips to ALLOW and expires back to DENY.

#include "identity/identity_entities.hpp"

#include <cstdint>
#include <string>

namespace dottalk::identity {

inline constexpr std::uint64_t kDefaultGrantHours = 24;

struct AdminResult {
    bool        ok = false;
    std::string message;
    static AdminResult fail(std::string m) { return {false, std::move(m)}; }
    static AdminResult good(std::string m) { return {true,  std::move(m)}; }
};

// Admit a new member (persisted). Fails if the key already exists or the store is read-only.
AdminResult admit_member(const std::string& key, MemberKind kind, RoleId default_role);

// An agent asks for a permission: creates a Requested grant (persisted). out_id = grant id.
AdminResult request_permission(const std::string& member_key, const std::string& perm_key,
                               const std::string& reason, AuthorizationId& out_id);

// Owner approves: mints a scoped ALLOW override + a Granted authorization expiring in `hours`.
AdminResult approve_grant(AuthorizationId id, std::uint64_t hours);
AdminResult deny_grant(AuthorizationId id);
AdminResult revoke_grant(AuthorizationId id);   // Revoked + drops the minted override

} // namespace dottalk::identity
