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
#include "identity/identity_repository.hpp"   // Decision, authorize, RuntimeContext, Scope

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

// Direct owner actions (no request/approve ceremony; deterministic, scriptable):
// grant mints the scoped ALLOW override + a time-boxed Granted authorization; ungrant
// revokes the member's granted authorizations for the permission and drops the override.
AdminResult grant_permission_to(const std::string& member_key, const std::string& perm_key,
                                std::uint64_t hours);
AdminResult ungrant_permission_from(const std::string& member_key, const std::string& perm_key);

// Remove a member and its role bindings / overrides / grants (persisted). Refuses to
// delete an owner-class member.
AdminResult remove_member(const std::string& member_key);

// --- Session authentication (2d) -----------------------------------------------
// A session has a PRINCIPAL (the authenticated identity, set by login) and an ACTING
// member (the effective identity used for every permission check). Boot default is the
// low-privilege member.public, UNAUTHENTICATED — owner powers require USER LOGIN. The
// owner may sudo to another identity via act_as (USER AS); the acting member can only
// become owner-class by authenticating, which closes the escalation hole.
const std::string& principal_key();       // authenticated identity (member.public until login)
bool               session_authenticated();

// Verify <secret> against the member's stored salted credential (SYSUSER.CRED). A member
// whose account has no credential set yet logs in on first use (bootstrap) — set one with
// set_password. AI/service members (no user account) cannot password-login; use owner sudo.
AdminResult login(const std::string& member_key, const std::string& secret);
AdminResult logout();

// Store a salted local-hash credential for a member (persisted). Allowed for the
// authenticated owner, the member itself, or — on a fresh system — for the owner from the
// console. NOTE: the hash is local obfuscation-grade (non-cryptographic), not for hostile
// networks; upgradeable to real crypto later.
AdminResult set_password(const std::string& member_key, const std::string& secret);

// Owner sudo: act as another member for testing. Requires an authenticated owner principal.
AdminResult act_as(const std::string& member_key);

// --- Enforcement bridge (2c-4) -------------------------------------------------
// The acting member is who the engine treats as the current actor for permission checks.
const std::string& acting_member_key();
void               set_acting_member(const std::string& key);   // internal/test setter (ungated)

// Owner-class = a member whose default role is MAINTAINER (the ask-for-permission
// exemption). The console operator defaults to the owner, so existing behavior is
// unchanged until an action runs AS a non-owner agent.
bool is_owner_member(const std::string& member_key);

// The enforcement decision an engine action should consult before acting: resolves
// `perm_key` for the acting member with the live clock and host-shell policy, with
// the owner exempt. This is the single entry that turns 'the resolver says DENY'
// into 'the action is refused'.
Decision agent_permitted(const std::string& perm_key);

} // namespace dottalk::identity
