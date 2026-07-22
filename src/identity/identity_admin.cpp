// src/identity/identity_admin.cpp
// Runtime administration of the identity / RBAC catalog (AIF-045 2c).
// Compiled into dottalkpp via the src glob.

#include "identity/identity_admin.hpp"
#include "identity/identity_bootstrap.hpp"

#include <algorithm>
#include <cstdlib>
#include <string>

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

AdminResult grant_permission_to(const std::string& member_key, const std::string& perm_key,
                                std::uint64_t hours) {
    if (!identity_store_writable()) return AdminResult::fail("store is read-only (degraded startup)");
    InMemoryIdentityStore& s = mutable_identity_store();
    const TeamMember* m = find_member_by_key(s, member_key);
    if (!m) return AdminResult::fail("unknown member '" + member_key + "'");
    const Permission* p = find_permission_by_key(s, perm_key);
    if (!p) return AdminResult::fail("unknown permission '" + perm_key + "'");

    const std::uint64_t now = identity_now();
    if (!has_allow_override(s, m->id, p->id))
        s.overrides.push_back(MemberPermissionOverride{
            m->id, p->id, OverrideEffect::Allow, std::nullopt, std::nullopt});

    AuthorizationGrant g;
    g.id = next_authorization_id();
    g.requested_by = m->id;
    g.granted_to   = m->id;
    g.action_scope = perm_key;
    g.risk = p->risk;
    g.status = GrantStatus::Granted;
    g.granted_at = now;
    g.expires_at = hours ? now + hours * 3600ULL : 0;
    g.reason = "direct owner grant";
    s.grants.push_back(g);

    std::string err;
    if (!persist_identity_store(err)) return AdminResult::fail("granted but not persisted: " + err);
    std::string until = g.expires_at ? (" (+" + std::to_string(hours) + "h)") : " (no expiry)";
    return AdminResult::good("granted " + perm_key + " to " + member_key + until);
}

AdminResult ungrant_permission_from(const std::string& member_key, const std::string& perm_key) {
    if (!identity_store_writable()) return AdminResult::fail("store is read-only (degraded startup)");
    InMemoryIdentityStore& s = mutable_identity_store();
    const TeamMember* m = find_member_by_key(s, member_key);
    if (!m) return AdminResult::fail("unknown member '" + member_key + "'");
    const Permission* p = find_permission_by_key(s, perm_key);
    if (!p) return AdminResult::fail("unknown permission '" + perm_key + "'");

    const TeamMemberId who = m->id;
    const PermissionId pid = p->id;
    s.overrides.erase(std::remove_if(s.overrides.begin(), s.overrides.end(),
        [&](const MemberPermissionOverride& ov) {
            return ov.member == who && ov.permission == pid && ov.effect == OverrideEffect::Allow;
        }), s.overrides.end());
    for (auto& g : s.grants)
        if (g.granted_to == who && g.action_scope == perm_key && g.status == GrantStatus::Granted)
            g.status = GrantStatus::Revoked;

    std::string err;
    if (!persist_identity_store(err)) return AdminResult::fail("ungranted but not persisted: " + err);
    return AdminResult::good("ungranted " + perm_key + " from " + member_key);
}

AdminResult remove_member(const std::string& member_key) {
    if (!identity_store_writable()) return AdminResult::fail("store is read-only (degraded startup)");
    if (is_owner_member(member_key)) return AdminResult::fail("refusing to remove owner-class member '" + member_key + "'");
    InMemoryIdentityStore& s = mutable_identity_store();
    const TeamMember* m = find_member_by_key(s, member_key);
    if (!m) return AdminResult::fail("unknown member '" + member_key + "'");
    const TeamMemberId who = m->id;

    s.member_roles.erase(std::remove_if(s.member_roles.begin(), s.member_roles.end(),
        [&](const MemberRole& mr) { return mr.member == who; }), s.member_roles.end());
    s.overrides.erase(std::remove_if(s.overrides.begin(), s.overrides.end(),
        [&](const MemberPermissionOverride& ov) { return ov.member == who; }), s.overrides.end());
    s.grants.erase(std::remove_if(s.grants.begin(), s.grants.end(),
        [&](const AuthorizationGrant& g) { return g.granted_to == who || g.requested_by == who; }), s.grants.end());
    s.members.erase(std::remove_if(s.members.begin(), s.members.end(),
        [&](const TeamMember& x) { return x.id == who; }), s.members.end());

    std::string err;
    if (!persist_identity_store(err)) return AdminResult::fail("removed but not persisted: " + err);
    return AdminResult::good("removed member '" + member_key + "'");
}

// --- Enforcement bridge (2c-4) -------------------------------------------------

namespace {
std::string g_acting_member;   // empty => resolve default lazily
} // namespace

const std::string& acting_member_key() {
    if (g_acting_member.empty()) {
        const char* e = std::getenv("DOTTALK_ACTING_MEMBER");
        g_acting_member = (e && *e) ? std::string(e) : std::string("member.derald");
    }
    return g_acting_member;
}

void set_acting_member(const std::string& key) {
    g_acting_member = key.empty() ? std::string("member.derald") : key;
}

bool is_owner_member(const std::string& member_key) {
    const InMemoryIdentityStore& s = identity_store();
    const TeamMember* m = find_member_by_key(s, member_key);
    if (!m || !m->default_role) return false;
    const Role* r = find_role_by_id(s, *m->default_role);
    return r && r->key == "role.maintainer";
}

Decision agent_permitted(const std::string& perm_key) {
    identity_refresh_clock();
    const InMemoryIdentityStore& s = identity_store();
    const std::string who = acting_member_key();

    // Owner-class is the ask-for-permission exemption (doctrine: "owner exempt").
    if (is_owner_member(who))
        return Decision{Outcome::Allow, DenyStage::None, "owner exemption (" + who + ")"};

    const Permission* p = find_permission_by_key(s, perm_key);
    if (!p) return Decision{Outcome::Deny, DenyStage::Eligibility, "unknown permission '" + perm_key + "'"};
    const TeamMember* m = find_member_by_key(s, who);
    if (!m) return Decision{Outcome::Deny, DenyStage::Eligibility, "unknown acting member '" + who + "'"};

    RuntimeContext rt;
    rt.session_capable = true;
    if (p->resource_class == "host") {
        const char* v = std::getenv("DOTTALK_ALLOW_HOST_COMMANDS");
        rt.security_policy_allows = v && *v && std::string(v) != "0";
    } else {
        rt.security_policy_allows = true;
    }
    return authorize(s, m->id, *p, Scope{}, rt);
}

} // namespace dottalk::identity
