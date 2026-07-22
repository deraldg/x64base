// src/identity/identity_entities_smoke.cpp
// Standalone smoke proof for the identity domain layer (AIF-045 M1a).
// Self-contained: depends only on the two identity headers + the standard library.
//
//   g++ -std=c++20 -I include src/identity/identity_entities_smoke.cpp -o idsmoke && ./idsmoke
//
// Proves: strong-id type safety (distinct, non-convertible), 0==unset, ordering, and that the
// core entities (User seeded from the derald profile home, human + AI members, role/permission,
// deny override) construct and hold their values.

#include "identity/identity_ids.hpp"
#include "identity/identity_entities.hpp"

#include <cassert>
#include <iostream>
#include <optional>
#include <type_traits>

using namespace dottalk::identity;

int main() {
    // Strong-id type safety — the whole reason for distinct tags.
    static_assert(!std::is_same_v<UserId, RoleId>,          "UserId and RoleId must be distinct types");
    static_assert(!std::is_convertible_v<UserId, RoleId>,   "UserId must not implicitly convert to RoleId");
    static_assert(!std::is_convertible_v<std::uint64_t, UserId>, "raw uint64 must not implicitly become a UserId");

    UserId u{42};
    RoleId r{42};
    assert(u.value() == r.value());   // same underlying value...
    // (u == r) intentionally does NOT compile — different types. That is the point.
    assert(u.valid());
    assert(!UserId{}.valid());        // default-constructed = unset = 0
    assert(UserId{1} < UserId{2});    // ordering via <=>

    // Owner, seeded from the existing dottalkpp/user/derald/ profile home.
    User derald;
    derald.id               = UserId{1};
    derald.key              = "user.derald";
    derald.login_name       = "derald";
    derald.display_name     = "Derald Grimwood";
    derald.auth_kind        = AuthKind::LocalTrusted;   // person at the console == owner (alpha)
    derald.profile_home_key = "derald";                 // -> dottalkpp/user/derald/
    assert(derald.profile_home_key == "derald");
    assert(derald.credential_ref.empty());              // no real credential yet, honestly

    TeamMember m_derald;
    m_derald.id      = TeamMemberId{1};
    m_derald.user_id = derald.id;
    m_derald.key     = "member.derald";
    m_derald.kind    = MemberKind::Human;
    assert(m_derald.user_id.has_value() && m_derald.user_id->value() == 1);

    TeamMember m_ai;
    m_ai.id      = TeamMemberId{2};
    m_ai.user_id = std::nullopt;                        // AI/service actor needs no USERS row
    m_ai.key     = "member.ai.claude.cowork";
    m_ai.kind    = MemberKind::AI;
    assert(!m_ai.user_id.has_value());

    Role maintainer{RoleId{1}, "role.maintainer", "MAINTAINER", "core", "Full authority", EntityStatus::Active};
    Permission git_push{PermissionId{1}, "git.push", "git", "push", RiskClass::High, /*requires_approval=*/true, EntityStatus::Active};
    assert(maintainer.name == "MAINTAINER");
    assert(git_push.requires_approval);                 // high-risk => needs a live grant, not just eligibility

    // AI partner is DENIED source.mutate even if a role would grant it (DENY precedence).
    MemberPermissionOverride deny_mutate{ m_ai.id, PermissionId{2}, OverrideEffect::Deny, std::nullopt, std::nullopt };
    assert(deny_mutate.effect == OverrideEffect::Deny);

    // Reporting lives on the assignment, not the member.
    TeamAssignment a;
    a.id = AssignmentId{1}; a.member = m_derald.id; a.role = maintainer.id;
    a.reports_to = std::nullopt;                        // owner reports to no one
    assert(a.member.value() == 1);

    std::cout << "IDENTITY-M1A-SMOKE:PASS"
              << "  user=" << derald.id.value()
              << "  members=" << m_derald.id.value() << "/" << m_ai.id.value()
              << "  role=" << maintainer.name
              << "  perm=" << git_push.key << "(approval=" << git_push.requires_approval << ")\n";
    return 0;
}
