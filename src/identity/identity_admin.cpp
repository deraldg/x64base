// src/identity/identity_admin.cpp
// Runtime administration of the identity / RBAC catalog (AIF-045 2c).
// Compiled into dottalkpp via the src glob.

#include "identity/identity_admin.hpp"
#include "identity/identity_bootstrap.hpp"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <random>
#include <string>

namespace dottalk::identity {

namespace {

// Forward declarations; definitions live in the session-auth section below.
std::string service_user_key(const std::string& member_key);
std::string make_credential(const std::string& secret);
std::string gen_token();

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

// Owner-only admin gate (2d): mutating identity administration requires an authenticated
// owner principal. Returns an ok result when permitted.
AdminResult require_owner() {
    if (!(session_authenticated() && is_owner_member(principal_key())))
        return AdminResult::fail("requires an authenticated owner (USER LOGIN first)");
    return AdminResult::good("");
}

} // namespace

AdminResult admit_member(const std::string& key, MemberKind kind, RoleId default_role) {
    if (auto r = require_owner(); !r.ok) return r;
    if (!identity_store_writable()) return AdminResult::fail("store is read-only (degraded startup)");
    InMemoryIdentityStore& s = mutable_identity_store();
    if (find_member_by_key(s, key)) return AdminResult::fail("member '" + key + "' already exists");

    TeamMember m;
    m.id = next_member_id();
    m.key = key;
    m.kind = kind;
    m.default_role = default_role;
    m.stamp.valid_from = identity_now();

    // AI / service members get a token-based service-User (their credential home).
    if (kind == MemberKind::AI || kind == MemberKind::Service) {
        User su;
        su.id = next_user_id();
        su.key = service_user_key(key);
        su.login_name = key;
        su.display_name = key;
        su.auth_kind = AuthKind::Token;
        su.status = EntityStatus::Active;
        su.stamp.valid_from = identity_now();
        s.users.push_back(su);
        m.user_id = su.id;
    }

    s.members.push_back(m);
    s.member_roles.push_back(MemberRole{m.id, default_role, std::nullopt, std::nullopt});

    std::string err;
    if (!persist_identity_store(err)) return AdminResult::fail("admitted but not persisted: " + err);
    return AdminResult::good("admitted member '" + key + "' (id " + std::to_string(m.id.value()) + ")");
}

AdminResult request_permission(const std::string& member_key, const std::string& perm_key,
                               const std::string& reason, AuthorizationId& out_id) {
    out_id = AuthorizationId{};
    // A request may be filed by the authenticated owner (on behalf) or the member itself.
    if (!(session_authenticated() && (is_owner_member(principal_key()) || principal_key() == member_key)))
        return AdminResult::fail("USER REQUEST requires authentication as the owner or the member");
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
    if (auto r = require_owner(); !r.ok) return r;
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
    if (auto r = require_owner(); !r.ok) return r;
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
    if (auto r = require_owner(); !r.ok) return r;
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
    if (auto r = require_owner(); !r.ok) return r;
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
    if (auto r = require_owner(); !r.ok) return r;
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

AdminResult issue_token(const std::string& member_key, std::string& out_token) {
    out_token.clear();
    if (auto r = require_owner(); !r.ok) return r;
    if (!identity_store_writable()) return AdminResult::fail("store is read-only (degraded startup)");
    InMemoryIdentityStore& s = mutable_identity_store();
    const TeamMember* m = find_member_by_key(s, member_key);
    if (!m) return AdminResult::fail("unknown member '" + member_key + "'");

    // Ensure a credential-home User exists (older AI members admitted before service users).
    UserId uid;
    if (m->user_id) {
        uid = *m->user_id;
    } else {
        User su;
        su.id = next_user_id();
        su.key = service_user_key(member_key);
        su.login_name = member_key;
        su.display_name = member_key;
        su.auth_kind = AuthKind::Token;
        su.status = EntityStatus::Active;
        su.stamp.valid_from = identity_now();
        uid = su.id;
        s.users.push_back(su);
        for (auto& mm : s.members) if (mm.id == m->id) mm.user_id = uid;
    }

    const std::string token = gen_token();
    for (auto& uu : s.users) if (uu.id == uid) uu.credential_ref = make_credential(token);

    std::string err;
    if (!persist_identity_store(err)) return AdminResult::fail("issued but not persisted: " + err);
    out_token = token;
    return AdminResult::good("issued token for '" + member_key + "' (store it now; it is shown only once)");
}

AdminResult remove_member(const std::string& member_key) {
    if (auto r = require_owner(); !r.ok) return r;
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

// --- Session authentication (2d) -----------------------------------------------

namespace {

constexpr const char* kAnon = "member.public";   // low-privilege boot identity

std::string g_principal    = kAnon;
std::string g_acting       = kAnon;
bool        g_authenticated = false;

// Non-cryptographic salted local hash (FNV-1a-64). Honest obfuscation-grade only.
std::string fnv_hex(const std::string& salt, const std::string& secret) {
    std::uint64_t h = 1469598103934665603ULL;
    for (unsigned char c : salt)   { h ^= c; h *= 1099511628211ULL; }
    for (unsigned char c : secret) { h ^= c; h *= 1099511628211ULL; }
    char buf[17];
    std::snprintf(buf, sizeof buf, "%016llx", static_cast<unsigned long long>(h));
    return std::string(buf);
}

std::string make_credential(const std::string& secret) {
    static std::mt19937_64 rng{std::random_device{}() ^ static_cast<std::uint64_t>(std::time(nullptr))};
    char salt[9];
    std::snprintf(salt, sizeof salt, "%08x", static_cast<unsigned>(rng() & 0xffffffffu));
    return std::string(salt) + "$" + fnv_hex(salt, secret);
}

bool verify_credential(const std::string& stored, const std::string& secret) {
    const auto pos = stored.find('$');
    if (pos == std::string::npos) return false;
    return fnv_hex(stored.substr(0, pos), secret) == stored.substr(pos + 1);
}

// A random 64-bit opaque token, hex-encoded (for owner-issued agent credentials).
std::string gen_token() {
    static std::mt19937_64 rng{std::random_device{}() ^ static_cast<std::uint64_t>(std::time(nullptr)) ^ 0x9e3779b97f4a7c15ULL};
    char buf[17];
    std::snprintf(buf, sizeof buf, "%016llx", static_cast<unsigned long long>(rng()));
    return std::string(buf);
}

// Derive a service-user key from a member key: member.ai.foo -> user.ai.foo.
std::string service_user_key(const std::string& member_key) {
    if (member_key.rfind("member.", 0) == 0) return "user." + member_key.substr(7);
    return "user." + member_key;
}

// The User account (credential home) behind a member, or nullptr for AI/service members.
const User* user_of_member(const InMemoryIdentityStore& s, const std::string& member_key) {
    const TeamMember* m = find_member_by_key(s, member_key);
    if (!m || !m->user_id) return nullptr;
    return find_user_by_id(s, *m->user_id);
}

bool any_credential_set(const InMemoryIdentityStore& s) {
    for (const auto& u : s.users) if (!u.credential_ref.empty()) return true;
    return false;
}

} // namespace

const std::string& principal_key()   { return g_principal; }
bool session_authenticated()         { return g_authenticated; }

const std::string& acting_member_key() { return g_acting; }
void set_acting_member(const std::string& key) { g_acting = key.empty() ? std::string(kAnon) : key; }

AdminResult login(const std::string& member_key, const std::string& secret) {
    const InMemoryIdentityStore& s = identity_store();
    const TeamMember* m = find_member_by_key(s, member_key);
    if (!m) return AdminResult::fail("unknown member '" + member_key + "'");
    if (!m->user_id) return AdminResult::fail("'" + member_key + "' has no login account (AI/service) — owner may USER AS it");
    const User* u = find_user_by_id(s, *m->user_id);
    if (!u) return AdminResult::fail("no user account for '" + member_key + "'");

    if (u->credential_ref.empty()) {
        // Bootstrap (credential-less) login is owner-only (first-run local trust). A
        // non-owner — including an AI service account — needs an owner-issued credential.
        if (!is_owner_member(member_key))
            return AdminResult::fail("'" + member_key + "' has no credential set — the owner must set one "
                                     "(USER PASSWD for humans, USER TOKEN for agents)");
        g_principal = g_acting = member_key; g_authenticated = true;
        return AdminResult::good("logged in as " + member_key + " (bootstrap: no password set — run USER PASSWD to secure)");
    }
    if (!verify_credential(u->credential_ref, secret))
        return AdminResult::fail("authentication failed for '" + member_key + "'");
    g_principal = g_acting = member_key; g_authenticated = true;
    return AdminResult::good("logged in as " + member_key);
}

AdminResult logout() {
    g_principal = g_acting = kAnon; g_authenticated = false;
    return AdminResult::good("logged out (now " + std::string(kAnon) + ")");
}

AdminResult set_password(const std::string& member_key, const std::string& secret) {
    if (!identity_store_writable()) return AdminResult::fail("store is read-only (degraded startup)");
    InMemoryIdentityStore& s = mutable_identity_store();
    const User* u = user_of_member(s, member_key);
    if (!u) return AdminResult::fail("'" + member_key + "' has no user account to hold a credential");

    // Authorization: authenticated owner, authenticated self, or fresh-system bootstrap
    // (no credential anywhere yet + setting an owner-class account from the console).
    const bool by_owner = g_authenticated && is_owner_member(g_principal);
    const bool by_self  = g_authenticated && g_principal == member_key;
    const bool bootstrap = !any_credential_set(s) && is_owner_member(member_key);
    if (!(by_owner || by_self || bootstrap))
        return AdminResult::fail("not authorized to set the credential for '" + member_key + "'");

    for (auto& uu : s.users) if (uu.id == u->id) { uu.credential_ref = make_credential(secret); break; }
    std::string err;
    if (!persist_identity_store(err)) return AdminResult::fail("set but not persisted: " + err);
    return AdminResult::good("password set for '" + member_key + "'");
}

AdminResult act_as(const std::string& member_key) {
    if (member_key.empty() || member_key == g_principal) { g_acting = g_principal; return AdminResult::good("acting as " + g_acting); }
    if (!(g_authenticated && is_owner_member(g_principal)))
        return AdminResult::fail("USER AS requires an authenticated owner (login first)");
    if (!find_member_by_key(identity_store(), member_key))
        return AdminResult::fail("unknown member '" + member_key + "'");
    g_acting = member_key;
    return AdminResult::good("acting as " + member_key + " (owner sudo; principal " + g_principal + ")");
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
