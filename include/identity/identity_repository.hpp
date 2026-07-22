#pragma once
// include/identity/identity_repository.hpp
// Repository abstraction for the identity / RBAC layer (AIF-045 M2a).
//
// The store owns the entities + crosswalks and MATERIALIZES a ResolutionSnapshot for the pure
// resolver — that materialization (in-scope role permissions, scoped overrides, live
// authorization) is the real bridge between stored data and the §4 pipeline. An in-memory store
// is provided for bootstrap/tests; a DBF / x64base-backed store (M2b) implements the same
// interface, so the resolver and every caller stay storage-agnostic.

#include "identity/identity_entities.hpp"
#include "identity/permission_resolver.hpp"

#include <optional>
#include <vector>

namespace dottalk::identity {

// Runtime inputs the store does NOT own (session + policy verdicts are supplied per call).
struct RuntimeContext {
    bool session_capable        = true;
    bool security_policy_allows = true;
};

struct Scope {
    std::optional<OrgUnitId>  org;
    std::optional<WorkNodeId> work;
};

class IIdentityStore {
public:
    virtual ~IIdentityStore() = default;
    virtual ResolutionSnapshot materialize(TeamMemberId member, const Permission& action,
                                           const Scope& scope) const = 0;
    virtual std::optional<Permission> find_permission(PermissionId id) const = 0;
};

// In-memory bootstrap / test store. A DBF-backed store (M2b) mirrors this behavior over x64base.
class InMemoryIdentityStore : public IIdentityStore {
public:
    std::vector<User>                     users;
    std::vector<TeamMember>               members;
    std::vector<Role>                     roles;
    std::vector<Permission>               permissions;
    std::vector<RolePermission>           role_permissions;
    std::vector<MemberRole>               member_roles;
    std::vector<MemberPermissionOverride> overrides;
    std::vector<TeamAssignment>           assignments;
    std::vector<AuthorizationGrant>       grants;
    std::uint64_t                         now = 0;   // logical clock for grant-expiry checks

    std::optional<Permission> find_permission(PermissionId id) const override {
        for (const auto& p : permissions) if (p.id == id) return p;
        return std::nullopt;
    }

    ResolutionSnapshot materialize(TeamMemberId member, const Permission& action,
                                   const Scope& scope) const override {
        ResolutionSnapshot s;

        // A role/override applies if its scope is unset (global) or matches the requested scope.
        const auto applies = [&](const std::optional<OrgUnitId>& o,
                                 const std::optional<WorkNodeId>& w) {
            const bool org_ok  = !o.has_value() || (scope.org.has_value()  && *o == *scope.org);
            const bool work_ok = !w.has_value() || (scope.work.has_value() && *w == *scope.work);
            return org_ok && work_ok;
        };

        // base = union of permissions from the member's in-scope roles.
        for (const auto& mr : member_roles) {
            if (!(mr.member == member) || !applies(mr.org_scope, mr.work_scope)) continue;
            for (const auto& rp : role_permissions)
                if (rp.role == mr.role) s.base_role_permissions.push_back(rp.permission);
        }

        // scoped ALLOW / DENY overrides.
        for (const auto& ov : overrides) {
            if (!(ov.member == member) || !applies(ov.org_scope, ov.work_scope)) continue;
            if (ov.effect == OverrideEffect::Allow) s.allow_overrides.push_back(ov.permission);
            else                                    s.deny_overrides.push_back(ov.permission);
        }

        // a live (Granted, unexpired) authorization covering this action.
        for (const auto& g : grants) {
            if (!(g.granted_to == member) || g.status != GrantStatus::Granted) continue;
            if (g.expires_at != 0 && g.expires_at <= now) continue;
            if (g.action_scope == action.key || g.action_scope == "*") {
                s.has_live_authorization = true;
                break;
            }
        }
        return s;
    }
};

// Resolve straight through a store: stored data -> snapshot -> pure resolver.
inline Decision authorize(const IIdentityStore& store, TeamMemberId member,
                          const Permission& action, const Scope& scope, const RuntimeContext& rt) {
    ResolutionSnapshot snap = store.materialize(member, action, scope);
    snap.session_capable        = rt.session_capable;
    snap.security_policy_allows  = rt.security_policy_allows;
    return resolve(ResolutionRequest{action.id, action.requires_approval}, snap);
}

} // namespace dottalk::identity
