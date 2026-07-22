// src/identity/identity_admin.cpp
// Runtime administration of the identity / RBAC catalog (AIF-045 2c).
// Compiled into dottalkpp via the src glob.

#include "identity/identity_admin.hpp"
#include "identity/identity_bootstrap.hpp"

#include <algorithm>

namespace dottalk::identity {

namespace {

AuthorizationGrant* find_grant(InMemoryIdentityStore& s, AuthorizationId id) {
    for (auto& g : s.grants) if (g.id == id) return &g;
    return nullptr;
}

// The permission a grant's action_scope names ("*" grants cover everything, no single perm).
const Permission* perm_of_scope(const InMemoryIdentityStore& s, const std::string& scope) {
    return find_permission_by_key(s, scope);
}

bool has_allow_override(const InMemoryIdentityStore& s, TeamMemberId m, PermissionId p) {
    for (const auto& ov : s.overrides)
        if (ov.member == m && ov.permission == p && ov.effect == OverrideEffect::Allow) return true;
    return false;
}

} // namespace

AdminResult admit_member(const std::string& key, MemberKind kind, RoleId default_role) {
    if (!identity_store_writable()) return AdminResult::fail("store is read-only (degraded startup)");
    InMemoryIdentityStore& s = mutable_identity_store();
    if (find_member_by_key(s, key)) return AdminResult::fail("member '" + key + "' already exists");

    TeamMember m;
    m.id = next_member_id();
    m.key = key;
    m.kind = kind;
    m.default_role = default_role;
    m.stamp.valid_from = identity_now();
    s.members.push_back(m);
    s.member_roles.push_back(MemberRole{m.id, default_role, std::nullopt, std::nullopt});

    std::string err;
    if (!persist_identity_store(err)) return AdminResult::fail("admitted but not persisted: " + err);
    return AdminResult::good("admitted member '" + key + "' (id " + std::to_string(m.id.value()) + ")");
}

AdminResult request_permission(const std::string& member_key, const std::string& perm_key,
                               const std::string& reason, AuthorizationId& out_id) {
    out_id = AuthorizationId{};
    if (!identity_store_writable()) return AdminResult::fail("store is read-only (degraded startup)");
    InMemoryIdentityStore& s = mutable_identity_store();

    const TeamMember* m = find_member_by_key(s, member_key);
    if (!m) return AdminResult::fail("unknown member '" + member_key + "'");
    const Permission* p = find_permission_by_key(s, perm_key);
    if (!p) return AdminResult::fail("unknown permission '" + perm_key + "'");

    AuthorizationGrant g;
    g.id = next_authorization_id();
    g.requested_by = m->id;
    g.granted_to   = m->id;
    g.action_scope = perm_key;
    g.risk = p->risk;
    g.status = GrantStatus::Requested;
    g.reason = reason;
    s.grants.push_back(g);
    out_id = g.id;

    std::string err;
    if (!persist_identity_store(err)) return AdminResult::fail("requested but not persisted: " + err);
    return AdminResult::good("request " + std::to_string(g.id.value()) + ": " + member_key +
                             " asks for " + perm_key);
}

AdminResult approve_grant(AuthorizationId id, std::uint64_t hours) {
    if (!identity_store_writable()) return AdminResult::fail("store is read-only (degraded startup)");
    InMemoryIdentityStore& s = mutable_identity_store();

    AuthorizationGrant* g = find_grant(s, id);
    if (!g) return AdminResult::fail("no grant #" + std::to_string(id.value()));
    if (g->status != GrantStatus::Requested)
        return AdminResult::fail("grant #" + std::to_string(id.value()) + " is not pending");

    const std::uint64_t now = identity_now();
    g->status     = GrantStatus::Granted;
    g->granted_at = now;
    g->expires_at = hours ? now + hours * 3600ULL : 0;   // 0 = no expiry

    // Mint the eligibility override for the named permission (skip "*" wildcard grants).
    if (const Permission* p = perm_of_scope(s, g->action_scope)) {
        if (!has_allow_override(s, g->granted_to, p->id))
            s.overrides.push_back(MemberPermissionOverride{
                g->granted_to, p->id, OverrideEffect::Allow, std::nullopt, std::nullopt});
    }

    std::string err;
    if (!persist_identity_store(err)) return AdminResult::fail("approved but not persisted: " + err);
    std::string until = g->expires_at ? (" until +" + std::to_string(hours) + "h") : " (no expiry)";
    return AdminResult::good("approved grant #" + std::to_string(id.value()) + until);
}

AdminResult deny_grant(AuthorizationId id) {
    if (!identity_store_writable()) return AdminResult::fail("store is read-only (degraded startup)");
    InMemoryIdentityStore& s = mutable_identity_store();
    AuthorizationGrant* g = find_grant(s, id);
    if (!g) return AdminResult::fail("no grant #" + std::to_string(id.value()));
    g->status = GrantStatus::Denied;
    std::string err;
    if (!persist_identity_store(err)) return AdminResult::fail("denied but not persisted: " + err);
    return AdminResult::good("denied grant #" + std::to_string(id.value()));
}

AdminResult revoke_grant(AuthorizationId id) {
    if (!identity_store_writable()) return AdminResult::fail("store is read-only (degraded startup)");
    InMemoryIdentityStore& s = mutable_identity_store();
    AuthorizationGrant* g = find_grant(s, id);
    if (!g) return AdminResult::fail("no grant #" + std::to_string(id.value()));

    g->status = GrantStatus::Revoked;
    // Drop the minted eligibility override so the capability is fully withdrawn.
    if (const Permission* p = perm_of_scope(s, g->action_scope)) {
        const TeamMemberId who = g->granted_to;
        const PermissionId pid = p->id;
        s.overrides.erase(std::remove_if(s.overrides.begin(), s.overrides.end(),
            [&](const MemberPermissionOverride& ov) {
                return ov.member == who && ov.permission == pid && ov.effect == OverrideEffect::Allow;
            }), s.overrides.end());
    }

    std::string err;
    if (!persist_identity_store(err)) return AdminResult::fail("revoked but not persisted: " + err);
    return AdminResult::good("revoked grant #" + std::to_string(id.value()));
}

} // namespace dottalk::identity
