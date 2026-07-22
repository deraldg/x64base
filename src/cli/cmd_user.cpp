// @dottalk.usage v1
// owner: DOT|USER
// command: USER
// category: diagnostics
// status: experimental
// noargs: usage
// effect: report
// mutates: none
// usage-access: USER USAGE
// summary:
//   Inspect the identity / RBAC model (AIF-045): members, roles, the permission catalog, a live
//   effective-permission check that runs the real resolver, and DBF persistence with an APH-5
//   round-trip proof. Read-only against the live store; SAVE/VERIFY write DBF tables only.
//
// usage:
//   USER USAGE
//   USER LIST
//   USER ROLES
//   USER PERMS
//   USER WHOAMI
//   USER CAN <permission.key> [FOR <member.key>]
//   USER STORE           report boot origin (SEED/DBF/DEGRADED), writability, active counts
//   USER ADD <key> [HUMAN|AI|SERVICE] [role.key]           admit a member (persisted)
//   USER REQUEST <permission.key> FOR <member.key> [reason]  agent asks for limited permission
//   USER REQUESTS | GRANTS                                 list pending / all authorizations
//   USER APPROVE <id> [HOURS n] | DENY <id> | REVOKE <id>  owner grant decisions (2c)
//   USER SAVE [dir]      write the identity catalog to DBF (default data/metadata/identity)
//   USER LOAD [dir]      read the identity catalog back from DBF (report only)
//   USER VERIFY [dir]    APH-5 round-trip: save -> reload -> compare counts/keys/decisions
//
// examples:
//   USER CAN git.push FOR member.derald
//   USER CAN source.mutate FOR member.ai.claude.cowork
//   USER CAN host.shell
//
// notes:
//   Backed by the in-memory identity store seeded from the standard role/permission catalog and
//   the known profile homes (default/public/user/derald). CAN resolves eligibility ->
//   deny-precedence -> authorization -> session -> runtime security policy; for host.* it
//   consults the real host-shell gate (DOTTALK_ALLOW_HOST_COMMANDS). No mutation yet.
//
// risk:
//   mutates_table_data: no
//
// related:
//   SECURITY
//   BUILDVECTORS
//

#include "xbase.hpp"
#include "identity/identity_bootstrap.hpp"
#include "identity/identity_dbf_store.hpp"
#include "identity/identity_admin.hpp"

#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

using namespace dottalk::identity;

std::string upcase(std::string s) {
    for (char& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

const char* kind_name(MemberKind k) {
    switch (k) { case MemberKind::Human: return "HUMAN"; case MemberKind::AI: return "AI";
                 case MemberKind::Service: return "SERVICE"; default: return "EXTERNAL"; }
}

void user_usage() {
    std::cout << "Usage:\n"
              << "  USER LIST | ROLES | PERMS | WHOAMI\n"
              << "  USER CAN <permission.key> [FOR <member.key>]\n"
              << "  USER STORE          show boot origin (SEED/DBF/DEGRADED), writability, counts\n"
              << "  USER ADD <key> [HUMAN|AI|SERVICE] [role.key]   admit a member (persisted)\n"
              << "  USER REQUEST <permission.key> FOR <member.key> [reason]   ask for limited permission\n"
              << "  USER REQUESTS | GRANTS                         list pending / all authorizations\n"
              << "  USER APPROVE <id> [HOURS n] | DENY <id> | REVOKE <id>   owner grant decisions\n"
              << "  USER AS [member.key]   act as a member (empty = owner); USER WHOAMI shows it\n"
              << "  USER ENFORCE <permission.key>   enforcement decision for the acting member\n"
              << "  USER SAVE [dir]     write the identity catalog to DBF (default data/metadata/identity)\n"
              << "  USER LOAD [dir]     read the identity catalog back from DBF (report only)\n"
              << "  USER VERIFY [dir]   APH-5 round-trip proof: save -> reload -> compare\n"
              << "Examples:\n"
              << "  USER CAN git.push FOR member.derald\n"
              << "  USER CAN source.mutate FOR member.ai.claude.cowork\n";
}

// --- 2b-ii: DBF persistence surface (round-trip proof; boot path unchanged) ---

void print_counts(const char* label, const InMemoryIdentityStore& s) {
    std::cout << "  " << label
              << ": users="        << s.users.size()
              << " members="       << s.members.size()
              << " roles="         << s.roles.size()
              << " perms="         << s.permissions.size()
              << " role_perms="    << s.role_permissions.size()
              << " member_roles="  << s.member_roles.size()
              << " overrides="     << s.overrides.size()
              << " assignments="   << s.assignments.size()
              << " grants="        << s.grants.size() << "\n";
}

void user_save(const std::string& dir) {
    std::string err;
    if (save_identity_tables(identity_store(), dir, err)) {
        std::cout << "USER SAVE: wrote identity catalog to " << dir << "\n";
        print_counts("seeded", identity_store());
    } else {
        std::cout << "USER SAVE: FAILED: " << err << "\n";
    }
}

void user_load(const std::string& dir) {
    InMemoryIdentityStore loaded;
    std::string err;
    if (load_identity_tables(dir, loaded, err)) {
        std::cout << "USER LOAD: read identity catalog from " << dir << "\n";
        print_counts("loaded", loaded);
    } else {
        std::cout << "USER LOAD: FAILED: " << err << "\n";
    }
}

void user_store() {
    std::cout << "Identity store\n"
              << "  origin   : " << store_origin_name(identity_store_origin()) << "\n"
              << "  writable : " << (identity_store_read_only() ? "no (degraded read-only)" : "yes") << "\n"
              << "  home     : " << default_identity_dir() << "\n";
    print_counts("active", identity_store());
}

// --- 2c: runtime administration (admit agents, grant lifecycle) ---------------

const char* grant_status_name(GrantStatus g) {
    switch (g) {
        case GrantStatus::Requested: return "requested";
        case GrantStatus::Granted:   return "granted";
        case GrantStatus::Denied:    return "denied";
        case GrantStatus::Expired:   return "expired";
        case GrantStatus::Revoked:   return "revoked";
    }
    return "?";
}

void user_add(std::istringstream& iss) {
    std::string key, tok;
    if (!(iss >> key)) { std::cout << "USER ADD <member.key> [HUMAN|AI|SERVICE] [role.key]\n"; return; }
    MemberKind kind = MemberKind::Human;
    std::string role_key;
    while (iss >> tok) {
        const std::string u = upcase(tok);
        if      (u == "HUMAN")    kind = MemberKind::Human;
        else if (u == "AI")       kind = MemberKind::AI;
        else if (u == "SERVICE")  kind = MemberKind::Service;
        else if (u == "EXTERNAL") kind = MemberKind::External;
        else role_key = tok;
    }
    if (role_key.empty()) role_key = (kind == MemberKind::AI) ? "role.ai_partner" : "role.student";
    const Role* r = find_role_by_key(identity_store(), role_key);
    if (!r) { std::cout << "USER ADD: unknown role '" << role_key << "'\n"; return; }
    std::cout << "USER ADD: " << admit_member(key, kind, r->id).message << "\n";
}

void user_request(std::istringstream& iss) {
    std::string perm, kw, member;
    iss >> perm;
    if (iss >> kw) { if (upcase(kw) == "FOR") iss >> member; }
    std::string reason, w;
    while (iss >> w) { if (!reason.empty()) reason += " "; reason += w; }
    if (perm.empty() || member.empty()) {
        std::cout << "USER REQUEST <permission.key> FOR <member.key> [reason]\n"; return;
    }
    AuthorizationId id;
    std::cout << "USER REQUEST: " << request_permission(member, perm, reason, id).message << "\n";
}

void user_grants(const InMemoryIdentityStore& s, bool pending_only) {
    std::cout << (pending_only ? "Pending requests:\n" : "Grants:\n");
    int n = 0;
    for (const auto& g : s.grants) {
        if (pending_only && g.status != GrantStatus::Requested) continue;
        const TeamMember* m = nullptr;
        for (const auto& x : s.members) if (x.id == g.granted_to) { m = &x; break; }
        std::cout << "  #" << g.id.value() << "  " << (m ? m->key : "?")
                  << "  " << g.action_scope << "  [" << grant_status_name(g.status) << "]";
        if (g.expires_at) std::cout << "  expires@" << g.expires_at;
        if (!g.reason.empty()) std::cout << "  \"" << g.reason << "\"";
        std::cout << "\n";
        ++n;
    }
    if (n == 0) std::cout << "  (none)\n";
}

void user_approve(std::istringstream& iss) {
    std::string idtok, kw;
    if (!(iss >> idtok)) { std::cout << "USER APPROVE <grant.id> [HOURS n]\n"; return; }
    std::uint64_t hours = kDefaultGrantHours;
    if (iss >> kw && upcase(kw) == "HOURS") { std::string h; if (iss >> h) hours = std::strtoull(h.c_str(), nullptr, 10); }
    AuthorizationId id{std::strtoull(idtok.c_str(), nullptr, 10)};
    std::cout << "USER APPROVE: " << approve_grant(id, hours).message << "\n";
}

void user_grant_op(std::istringstream& iss, bool deny) {
    std::string idtok;
    if (!(iss >> idtok)) { std::cout << "USER " << (deny ? "DENY" : "REVOKE") << " <grant.id>\n"; return; }
    AuthorizationId id{std::strtoull(idtok.c_str(), nullptr, 10)};
    AdminResult res = deny ? deny_grant(id) : revoke_grant(id);
    std::cout << "USER " << (deny ? "DENY" : "REVOKE") << ": " << res.message << "\n";
}

// --- 2c-4 enforcement surface ---

void user_whoami(const InMemoryIdentityStore& s) {
    const std::string who = acting_member_key();
    const TeamMember* m = find_member_by_key(s, who);
    const Role* r = (m && m->default_role) ? find_role_by_id(s, *m->default_role) : nullptr;
    std::cout << "WHOAMI: acting as " << who;
    if (m) std::cout << "  [" << kind_name(m->kind) << "]  role=" << (r ? r->name : "(none)");
    else   std::cout << "  (unknown member)";
    std::cout << (is_owner_member(who) ? "  OWNER (ask-for-permission exempt)"
                                       : "  (must ask for limited permission)") << "\n";
}

void user_as(std::istringstream& iss) {
    std::string key;
    iss >> key;                       // empty resets to owner
    set_acting_member(key);
    const std::string who = acting_member_key();
    std::cout << "USER AS: acting member = " << who
              << (is_owner_member(who) ? " (owner)" : "") << "\n";
}

void user_enforce(std::istringstream& iss) {
    std::string perm;
    iss >> perm;
    if (perm.empty()) { std::cout << "USER ENFORCE <permission.key>\n"; return; }
    Decision d = agent_permitted(perm);
    std::cout << "ENFORCE " << perm << " as " << acting_member_key() << " : "
              << (d.allowed() ? "ALLOW" : "DENY") << "  (" << d.reason << ")\n";
}

// APH-5 round-trip: save the seed, reload it, and confirm the reloaded store is
// structurally identical (row counts) and resolves every member x permission to
// the same decision. Uses a sibling _verify dir so a real saved catalog is safe.
void user_verify(const std::string& base_dir) {
    const std::string dir = base_dir + "_verify";
    const InMemoryIdentityStore& seed = identity_store();

    std::string err;
    if (!save_identity_tables(seed, dir, err)) {
        std::cout << "USER VERIFY: save FAILED: " << err << "\n";
        return;
    }
    InMemoryIdentityStore back;
    if (!load_identity_tables(dir, back, err)) {
        std::cout << "USER VERIFY: reload FAILED: " << err << "\n";
        return;
    }

    bool ok = true;

    // (1) structural: every vector count matches.
    auto eq = [&](const char* what, std::size_t a, std::size_t b) {
        if (a != b) { ok = false; std::cout << "  MISMATCH " << what << ": " << a << " != " << b << "\n"; }
    };
    eq("users", seed.users.size(), back.users.size());
    eq("members", seed.members.size(), back.members.size());
    eq("roles", seed.roles.size(), back.roles.size());
    eq("permissions", seed.permissions.size(), back.permissions.size());
    eq("role_permissions", seed.role_permissions.size(), back.role_permissions.size());
    eq("member_roles", seed.member_roles.size(), back.member_roles.size());
    eq("overrides", seed.overrides.size(), back.overrides.size());
    eq("assignments", seed.assignments.size(), back.assignments.size());
    eq("grants", seed.grants.size(), back.grants.size());

    // (2) key/id fidelity: each seed user/member id+key survives.
    for (const auto& u : seed.users) {
        const User* b = nullptr;
        for (const auto& x : back.users) if (x.id == u.id) { b = &x; break; }
        if (!b || b->key != u.key || b->profile_home_key != u.profile_home_key) {
            ok = false; std::cout << "  MISMATCH user " << u.key << " id/key/profile not preserved\n";
        }
    }

    // (3) decision fidelity: same authorize() verdict on both stores, for every
    // member x a representative permission set (covers eligible/ineligible/grant).
    RuntimeContext rt; rt.session_capable = true; rt.security_policy_allows = true;
    const char* probe_perms[] = {"git.push", "git.commit", "source.mutate", "database.read", "host.shell"};
    int decisions = 0, agree = 0;
    for (const auto& m : seed.members) {
        for (const char* pk : probe_perms) {
            const Permission* ps = find_permission_by_key(seed, pk);
            const Permission* pb = find_permission_by_key(back, pk);
            if (!ps || !pb) continue;
            Decision ds = authorize(seed, m.id, *ps, Scope{}, rt);
            Decision db = authorize(back, m.id, *pb, Scope{}, rt);
            ++decisions;
            if (ds.allowed() == db.allowed()) ++agree;
            else { ok = false; std::cout << "  MISMATCH decision " << m.key << " / " << pk
                                         << ": seed=" << ds.allowed() << " back=" << db.allowed() << "\n"; }
        }
    }

    std::cout << "USER VERIFY: " << (ok ? "PASS" : "FAIL")
              << "  (dir=" << dir << ", decisions " << agree << "/" << decisions << " agree)\n";
}

void list_members(const InMemoryIdentityStore& s) {
    std::cout << "Members (" << s.members.size() << "):\n";
    for (const auto& m : s.members) {
        const Role* r = m.default_role ? find_role_by_id(s, *m.default_role) : nullptr;
        std::string home = "-";
        if (m.user_id) if (const User* u = find_user_by_id(s, *m.user_id)) home = u->profile_home_key;
        std::cout << "  " << m.key
                  << "   [" << kind_name(m.kind) << "]"
                  << "   role=" << (r ? r->name : "(none)")
                  << "   profile=" << home << "\n";
    }
}

void list_roles(const InMemoryIdentityStore& s) {
    std::cout << "Roles (" << s.roles.size() << "):\n";
    for (const auto& r : s.roles) std::cout << "  " << r.name << "   (" << r.key << ")  " << r.description << "\n";
}

void list_perms(const InMemoryIdentityStore& s) {
    std::cout << "Permissions (" << s.permissions.size() << "):\n";
    for (const auto& p : s.permissions)
        std::cout << "  " << p.key << (p.requires_approval ? "   [requires approval]" : "") << "\n";
}

void user_can(const InMemoryIdentityStore& s, const std::string& perm_key, const std::string& member_key) {
    const Permission* perm = find_permission_by_key(s, perm_key);
    if (!perm) { std::cout << "USER CAN: unknown permission '" << perm_key << "'\n"; return; }

    const std::string mkey = member_key.empty() ? "member.derald" : member_key;
    const TeamMember* m = find_member_by_key(s, mkey);
    if (!m) { std::cout << "USER CAN: unknown member '" << mkey << "'\n"; return; }

    RuntimeContext rt;
    rt.session_capable = true;
    // For host.* the real host-shell gate is the independent last word.
    if (perm->resource_class == "host") {
        const char* v = std::getenv("DOTTALK_ALLOW_HOST_COMMANDS");
        rt.security_policy_allows = v && *v && std::string(v) != "0";
    } else {
        rt.security_policy_allows = true;
    }

    Decision d = authorize(s, m->id, *perm, Scope{}, rt);
    std::cout << "USER CAN " << perm_key << " FOR " << mkey << " : "
              << (d.allowed() ? "ALLOW" : "DENY") << "  (" << d.reason << ")\n";
}

} // namespace

void cmd_USER(xbase::DbArea&, std::istringstream& iss)
{
    const InMemoryIdentityStore& s = identity_store();

    std::string sub;
    if (!(iss >> sub)) { user_usage(); return; }
    const std::string u = upcase(sub);

    if (u == "USAGE" || u == "HELP" || u == "?") { user_usage(); return; }
    if (u == "LIST")   { list_members(s); return; }
    if (u == "ROLES")  { list_roles(s);   return; }
    if (u == "PERMS")  { list_perms(s);   return; }
    if (u == "WHOAMI") { user_whoami(s); return; }
    if (u == "AS")      { user_as(iss); return; }
    if (u == "ENFORCE") { user_enforce(iss); return; }
    if (u == "CAN") {
        std::string perm_key, kw, member_key;
        iss >> perm_key;
        if (iss >> kw) { if (upcase(kw) == "FOR") iss >> member_key; }
        if (perm_key.empty()) { user_usage(); return; }
        user_can(s, perm_key, member_key);
        return;
    }
    if (u == "STORE")    { user_store(); return; }
    if (u == "ADD")      { user_add(iss); return; }
    if (u == "REQUEST")  { user_request(iss); return; }
    if (u == "REQUESTS") { user_grants(s, true);  return; }
    if (u == "GRANTS")   { user_grants(s, false); return; }
    if (u == "APPROVE")  { user_approve(iss); return; }
    if (u == "DENY")     { user_grant_op(iss, true);  return; }
    if (u == "REVOKE")   { user_grant_op(iss, false); return; }
    if (u == "SAVE")   { std::string dir; iss >> dir; user_save(dir.empty() ? default_identity_dir() : dir); return; }
    if (u == "LOAD")   { std::string dir; iss >> dir; user_load(dir.empty() ? default_identity_dir() : dir); return; }
    if (u == "VERIFY") { std::string dir; iss >> dir; user_verify(dir.empty() ? default_identity_dir() : dir); return; }
    user_usage();
}
