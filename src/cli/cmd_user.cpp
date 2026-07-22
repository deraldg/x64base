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
//   Inspect the identity / RBAC model (AIF-045): members, roles, the permission catalog, and
//   a live effective-permission check that runs the real resolver. Read-only in 2b-i.
//
// usage:
//   USER USAGE
//   USER LIST
//   USER ROLES
//   USER PERMS
//   USER WHOAMI
//   USER CAN <permission.key> [FOR <member.key>]
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

#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>

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
              << "Examples:\n"
              << "  USER CAN git.push FOR member.derald\n"
              << "  USER CAN source.mutate FOR member.ai.claude.cowork\n";
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
    if (u == "WHOAMI") {
        // 2b-i: the console operator is the owner (LOCAL_TRUSTED) until real auth lands.
        std::cout << "WHOAMI: member.derald  [HUMAN]  role=MAINTAINER  (LOCAL_TRUSTED; authenticated=false)\n";
        return;
    }
    if (u == "CAN") {
        std::string perm_key, kw, member_key;
        iss >> perm_key;
        if (iss >> kw) { if (upcase(kw) == "FOR") iss >> member_key; }
        if (perm_key.empty()) { user_usage(); return; }
        user_can(s, perm_key, member_key);
        return;
    }
    user_usage();
}
