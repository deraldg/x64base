// src/identity/identity_bootstrap.cpp
// Seeds the process-wide identity store (AIF-045 2b-i). Compiled into dottalkpp via the src glob.
// Interim in-memory seed: the standard role/permission catalog + members/users reflecting the
// known profile homes. DBF-backed durability + live profile scan are 2b-ii / fast-follow.

#include "identity/identity_bootstrap.hpp"
#include "identity/identity_dbf_store.hpp"

#include <algorithm>
#include <ctime>
#include <filesystem>
#include <string>

namespace dottalk::identity {

namespace {

InMemoryIdentityStore build_seed() {
    InMemoryIdentityStore s;

    // --- Roles (Contract §3.3) ---
    const RoleId MAINTAINER{1}, DEVELOPER{2}, REVIEWER{3}, TEACHER{4}, STUDENT{5},
                 AI_PARTNER{6}, PUB_OP{7};
    s.roles = {
        {MAINTAINER, "role.maintainer", "MAINTAINER", "core",     "Full authority (owner-class)", EntityStatus::Active},
        {DEVELOPER,  "role.developer",  "DEVELOPER",  "core",     "Build + propose + local mutate", EntityStatus::Active},
        {REVIEWER,   "role.reviewer",   "REVIEWER",   "core",     "Read + review",                 EntityStatus::Active},
        {TEACHER,    "role.teacher",    "TEACHER",    "campus",   "Lesson author + DB mutate",     EntityStatus::Active},
        {STUDENT,    "role.student",    "STUDENT",    "campus",   "Read-mostly learner",           EntityStatus::Active},
        {AI_PARTNER, "role.ai_partner", "AI_DEVELOPMENT_PARTNER", "ai", "Read + propose; no direct mutate", EntityStatus::Active},
        {PUB_OP,     "role.pub_op",     "PUBLICATION_OPERATOR",   "publication", "Promote/commit/push/publish", EntityStatus::Active},
    };

    // --- Permission catalog (Contract §3.4) ---  key, resource, action, risk, requires_approval
    auto P = [&](std::uint64_t id, const char* key, const char* res, const char* act,
                 RiskClass risk, bool approval) {
        s.permissions.push_back({PermissionId{id}, key, res, act, risk, approval, EntityStatus::Active});
        return PermissionId{id};
    };
    const PermissionId src_read   = P(1,  "source.read",         "source",   "read",    RiskClass::Low,      false);
    const PermissionId src_prop   = P(2,  "source.propose",      "source",   "propose", RiskClass::Low,      false);
    const PermissionId src_mut    = P(3,  "source.mutate",       "source",   "mutate",  RiskClass::High,     true);
    const PermissionId db_read    = P(4,  "database.read",       "database", "read",    RiskClass::Low,      false);
    const PermissionId db_mut     = P(5,  "database.mutate",     "database", "mutate",  RiskClass::Medium,   false);
    const PermissionId promote    = P(6,  "staging.promote",     "staging",  "promote", RiskClass::High,     true);
    const PermissionId git_commit = P(7,  "git.commit",          "git",      "commit",  RiskClass::High,     true);
    const PermissionId git_push   = P(8,  "git.push",            "git",      "push",    RiskClass::High,     true);
    const PermissionId publish    = P(9,  "website.publish",     "website",  "publish", RiskClass::High,     true);
    const PermissionId branch     = P(10, "branch.change",       "branch",   "change",  RiskClass::High,     true);
    const PermissionId user_mgr   = P(11, "user.manage",         "user",     "manage",  RiskClass::High,     true);
    const PermissionId role_asn   = P(12, "role.assign",         "role",     "assign",  RiskClass::Critical, true);
    const PermissionId auth_grant = P(13, "authorization.grant", "authorization", "grant", RiskClass::Critical, true);
    const PermissionId host_shell = P(14, "host.shell",          "host",     "shell",   RiskClass::Critical, true);

    auto grant_role = [&](RoleId r, std::initializer_list<PermissionId> perms) {
        for (PermissionId p : perms) s.role_permissions.push_back({r, p});
    };
    grant_role(MAINTAINER, {src_read, src_prop, src_mut, db_read, db_mut, promote, git_commit,
                            git_push, publish, branch, user_mgr, role_asn, auth_grant, host_shell});
    grant_role(DEVELOPER, {src_read, src_prop, src_mut, db_read, db_mut, git_commit});
    grant_role(REVIEWER,  {src_read, db_read});
    grant_role(TEACHER,   {src_read, db_read, db_mut});
    grant_role(STUDENT,   {src_read, db_read});
    grant_role(AI_PARTNER,{src_read, src_prop, db_read});          // propose, NOT mutate (example B)
    grant_role(PUB_OP,    {promote, git_commit, git_push, publish});

    // --- Users seeded from the known profile homes (Contract §5) ---
    auto U = [&](std::uint64_t id, const char* key, const char* login, const char* disp,
                 const char* home, AuthKind ak) {
        User u; u.id = UserId{id}; u.key = key; u.login_name = login; u.display_name = disp;
        u.profile_home_key = home; u.auth_kind = ak; s.users.push_back(u);
        return UserId{id};
    };
    const UserId U_DERALD  = U(1, "user.derald",  "derald",  "Derald Grimwood", "derald",  AuthKind::LocalTrusted);
    const UserId U_PUBLIC  = U(2, "user.public",  "public",  "Public",          "public",  AuthKind::HumanAsserted);
    const UserId U_DEFAULT = U(3, "user.default", "default", "Default",          "default", AuthKind::LocalTrusted);
    const UserId U_USER    = U(4, "user.user",    "user",    "User",            "user",    AuthKind::LocalTrusted);

    // --- Members (Contract §3.2) — humans bind a USERS row; AI members do not ---
    auto M = [&](std::uint64_t id, const char* key, MemberKind kind, UserId uid, RoleId def_role) {
        TeamMember m; m.id = TeamMemberId{id}; m.key = key; m.kind = kind; m.default_role = def_role;
        if (uid.valid()) m.user_id = uid;
        s.members.push_back(m);
        s.member_roles.push_back({TeamMemberId{id}, def_role, std::nullopt, std::nullopt});
        return TeamMemberId{id};
    };
    const TeamMemberId M_DERALD = M(1, "member.derald",           MemberKind::Human, U_DERALD, MAINTAINER);
    (void)                        M(2, "member.ai.claude.cowork", MemberKind::AI,    UserId{}, AI_PARTNER);
    (void)                        M(3, "member.ai.codex.local",   MemberKind::AI,    UserId{}, AI_PARTNER);
    (void)                        M(4, "member.public",           MemberKind::Human, U_PUBLIC, STUDENT);
    (void)U_DEFAULT; (void)U_USER;

    // --- Owner standing authorization: derald (MAINTAINER) is the ask-for-permission exemption. ---
    AuthorizationGrant owner;
    owner.id = AuthorizationId{1};
    owner.granted_to = M_DERALD;
    owner.requested_by = M_DERALD;
    owner.status = GrantStatus::Granted;
    owner.action_scope = "*";                 // covers every requires-approval permission
    owner.reason = "owner standing authorization (sole ask-for-permission exemption)";
    s.grants = {owner};

    return s;
}

} // namespace

// Load-or-seed boot (2b-iii). Explicit dir so all three paths are testable.
InMemoryIdentityStore boot_identity_store(const std::string& dir,
                                          StoreOrigin& origin, bool& read_only) {
    namespace fs = std::filesystem;
    read_only = false;

    // "Present" = the anchor table exists; a partial/corrupt set still counts as present
    // so we never overwrite a catalog we failed to read.
    const bool present = fs::exists(fs::path(dir) / "SYSUSER.dbf");

    if (present) {
        InMemoryIdentityStore loaded;
        std::string err;
        if (load_identity_tables(dir, loaded, err)) {
            origin = StoreOrigin::Dbf;              // authoritative, writable
            return loaded;
        }
        origin = StoreOrigin::DegradedSeed;         // unreadable -> read-only seed, DBF untouched
        read_only = true;
        return build_seed();
    }

    // Absent -> seed and persist so the next boot is DBF-authoritative.
    InMemoryIdentityStore seed = build_seed();
    std::string werr;
    save_identity_tables(seed, dir, werr);          // best-effort; a write failure still boots seeded
    origin = StoreOrigin::Seed;
    return seed;
}

namespace {
struct BootedStore {
    InMemoryIdentityStore store;
    StoreOrigin           origin = StoreOrigin::Seed;
    bool                  read_only = false;
};
BootedStore& booted() {
    static BootedStore b = [] {
        BootedStore x;
        x.store = boot_identity_store(default_identity_dir(), x.origin, x.read_only);
        return x;
    }();
    return b;
}
} // namespace

const InMemoryIdentityStore& identity_store() { return booted().store; }
InMemoryIdentityStore&       mutable_identity_store() { return booted().store; }
StoreOrigin identity_store_origin()            { return booted().origin; }
bool        identity_store_read_only()          { return booted().read_only; }
bool        identity_store_writable()           { return !booted().read_only; }

const char* store_origin_name(StoreOrigin o) {
    switch (o) {
        case StoreOrigin::Seed:         return "SEED (persisted)";
        case StoreOrigin::Dbf:          return "DBF (authoritative)";
        case StoreOrigin::DegradedSeed: return "DEGRADED (read-only seed)";
    }
    return "UNKNOWN";
}

bool persist_identity_store(std::string& err) {
    if (booted().read_only) { err = "identity store is read-only (degraded startup)"; return false; }
    return save_identity_tables(booted().store, default_identity_dir(), err);
}

TeamMemberId next_member_id() {
    std::uint64_t mx = 0;
    for (const auto& m : booted().store.members) mx = std::max(mx, m.id.value());
    return TeamMemberId{mx + 1};
}

AuthorizationId next_authorization_id() {
    std::uint64_t mx = 0;
    for (const auto& g : booted().store.grants) mx = std::max(mx, g.id.value());
    return AuthorizationId{mx + 1};
}

std::uint64_t identity_now() {
    return static_cast<std::uint64_t>(std::time(nullptr));
}

void identity_refresh_clock() {
    booted().store.now = identity_now();
}

} // namespace dottalk::identity
