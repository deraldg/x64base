#pragma once
// include/identity/permission_resolver.hpp
// Effective-permission resolver for the identity / RBAC layer (AIF-045, Contract v1 §4).
//
// A PURE function over a resolved snapshot — no I/O, no database access, no clock. A service
// (M2+) materializes the ResolutionSnapshot from x64base tables (in-scope role permissions,
// scoped overrides, live authorization, session capabilities, security-policy verdict); this
// function only decides. That makes it unit-testable and reproducible, and it doubles as the
// APH-6 teaching artifact.
//
//   effective(action) = base ∪ allow-overrides − deny-overrides
//                       ∩ authorization (if the permission requires approval)
//                       ∩ session capabilities
//                       ∩ runtime security policy            (independent, final)

#include "identity/identity_entities.hpp"

#include <string>
#include <vector>

namespace dottalk::identity {

enum class Outcome : std::uint8_t { Allow, Deny };

// Which pipeline stage produced a Deny (None when Allowed).
enum class DenyStage : std::uint8_t {
    None,
    Eligibility,        // no role permission and no ALLOW override
    Denial,             // explicit DENY override (precedence)
    Authorization,      // requires approval but no live authorization grant
    SessionCapability,  // outside active session capabilities
    SecurityPolicy      // runtime security policy (final, independent)
};

struct Decision {
    Outcome     outcome = Outcome::Deny;
    DenyStage   stage   = DenyStage::None;
    std::string reason;
    constexpr bool allowed() const noexcept { return outcome == Outcome::Allow; }
};

// Everything the pure resolver needs, already resolved for THIS (action, member, scope).
struct ResolutionSnapshot {
    std::vector<PermissionId> base_role_permissions;  // union of in-scope role perms for the member
    std::vector<PermissionId> allow_overrides;        // scoped ALLOW overrides
    std::vector<PermissionId> deny_overrides;         // scoped DENY overrides (take precedence)
    bool has_live_authorization = false;              // an unexpired grant covers (action, scope)
    bool session_capable        = true;               // action within active session capabilities
    bool security_policy_allows = true;               // runtime policy (independent, final word)
};

struct ResolutionRequest {
    PermissionId action;
    bool         action_requires_approval = false;    // Permission.requires_approval for `action`
};

inline bool contains(const std::vector<PermissionId>& v, PermissionId p) noexcept {
    for (PermissionId x : v) if (x == p) return true;
    return false;
}

inline Decision resolve(const ResolutionRequest& req, const ResolutionSnapshot& snap) {
    // 1. Eligibility: role permission OR an ALLOW override.
    const bool eligible = contains(snap.base_role_permissions, req.action)
                       || contains(snap.allow_overrides, req.action);
    if (!eligible)
        return {Outcome::Deny, DenyStage::Eligibility,
                "not eligible: no in-scope role permission or ALLOW override"};

    // 2. DENY precedence.
    if (contains(snap.deny_overrides, req.action))
        return {Outcome::Deny, DenyStage::Denial, "explicit DENY override (precedence)"};

    // 3. Approval: a permission marked requires_approval needs a live authorization grant.
    //    Eligibility is necessary but not sufficient.
    if (req.action_requires_approval && !snap.has_live_authorization)
        return {Outcome::Deny, DenyStage::Authorization,
                "requires approval: no live authorization grant"};

    // 4. Session capabilities.
    if (!snap.session_capable)
        return {Outcome::Deny, DenyStage::SessionCapability, "outside active session capabilities"};

    // 5. Runtime security policy — the last word, independent of RBAC.
    if (!snap.security_policy_allows)
        return {Outcome::Deny, DenyStage::SecurityPolicy, "denied by runtime security policy (final)"};

    return {Outcome::Allow, DenyStage::None, "allowed"};
}

} // namespace dottalk::identity
