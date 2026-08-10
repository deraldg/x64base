// src/identity/permission_resolver_smoke.cpp
// Standalone proof for the effective-permission resolver (AIF-045 M1b, Contract v1 §4).
// Encodes the five worked examples from Contract §4.1 as assertions.
//
//   g++ -std=c++20 -I include src/identity/permission_resolver_smoke.cpp -o presolve && ./presolve

#include "identity/permission_resolver.hpp"

#include <cassert>
#include <iostream>

using namespace dottalk::identity;

// Stable permission ids for the examples.
static constexpr PermissionId GIT_PUSH{1};
static constexpr PermissionId GIT_COMMIT{2};
static constexpr PermissionId SOURCE_MUTATE{10};
static constexpr PermissionId SOURCE_PROPOSE{11};
static constexpr PermissionId DATABASE_MUTATE{20};
static constexpr PermissionId HOST_SHELL{30};

int main() {
    // A) derald / MAINTAINER, git.push (requires approval): has the perm, a live grant, policy allows.
    {
        ResolutionRequest req{GIT_PUSH, /*requires_approval=*/true};
        ResolutionSnapshot s;
        s.base_role_permissions = {GIT_PUSH, GIT_COMMIT, SOURCE_MUTATE, SOURCE_PROPOSE};
        s.has_live_authorization = true;
        Decision d = resolve(req, s);
        assert(d.allowed());
        std::cout << "A MAINTAINER git.push            -> " << (d.allowed() ? "ALLOW" : "DENY") << "\n";
    }

    // B) AI partner, source.mutate: not in base, no ALLOW override -> DENY at Eligibility.
    {
        ResolutionRequest req{SOURCE_MUTATE, false};
        ResolutionSnapshot s;
        s.base_role_permissions = {SOURCE_PROPOSE};   // partner may propose, not mutate
        Decision d = resolve(req, s);
        assert(!d.allowed() && d.stage == DenyStage::Eligibility);
        std::cout << "B AI source.mutate               -> DENY (" << d.reason << ")\n";
    }

    // C) AI partner, source.propose (no approval): eligible, no grant needed -> ALLOW.
    //    Follow-up git.commit (requires approval), no grant -> DENY at Authorization.
    {
        ResolutionSnapshot s;
        s.base_role_permissions = {SOURCE_PROPOSE, GIT_COMMIT};
        s.has_live_authorization = false;

        Decision propose = resolve({SOURCE_PROPOSE, false}, s);
        assert(propose.allowed());

        Decision commit = resolve({GIT_COMMIT, /*requires_approval=*/true}, s);
        assert(!commit.allowed() && commit.stage == DenyStage::Authorization);
        std::cout << "C AI source.propose / git.commit -> " << (propose.allowed() ? "ALLOW" : "DENY")
                  << " / DENY(" << commit.reason << ")\n";
    }

    // D) student, database.mutate: not in base, but a SCOPED ALLOW override for this one work node.
    //    In scope -> ALLOW; out of scope (no override in the resolved snapshot) -> DENY.
    {
        ResolutionSnapshot in_scope;
        in_scope.base_role_permissions = {};                 // STUDENT lacks database.mutate
        in_scope.allow_overrides       = {DATABASE_MUTATE};  // granted for this lesson DB only
        Decision d_in = resolve({DATABASE_MUTATE, false}, in_scope);
        assert(d_in.allowed());

        ResolutionSnapshot out_scope;                        // different work node: no override materialized
        Decision d_out = resolve({DATABASE_MUTATE, false}, out_scope);
        assert(!d_out.allowed() && d_out.stage == DenyStage::Eligibility);
        std::cout << "D student database.mutate        -> in-scope ALLOW / out-of-scope DENY\n";
    }

    // E) host shell: base + grant + session all allow, but security policy is OFF -> DENY (last word).
    {
        ResolutionRequest req{HOST_SHELL, false};
        ResolutionSnapshot s;
        s.base_role_permissions   = {HOST_SHELL};
        s.has_live_authorization  = true;
        s.session_capable         = true;
        s.security_policy_allows  = false;                   // DOTTALK_ALLOW_HOST_COMMANDS off
        Decision d = resolve(req, s);
        assert(!d.allowed() && d.stage == DenyStage::SecurityPolicy);
        std::cout << "E host shell (policy off)        -> DENY (" << d.reason << ")\n";
    }

    // DENY precedence: eligible via role AND explicitly denied -> DENY at Denial stage.
    {
        ResolutionSnapshot s;
        s.base_role_permissions = {SOURCE_MUTATE};
        s.deny_overrides        = {SOURCE_MUTATE};
        Decision d = resolve({SOURCE_MUTATE, false}, s);
        assert(!d.allowed() && d.stage == DenyStage::Denial);
        std::cout << "F deny-precedence                -> DENY (" << d.reason << ")\n";
    }

    std::cout << "IDENTITY-M1B-RESOLVER-SMOKE:PASS  (A-F all as specified in Contract v1 4.1)\n";
    return 0;
}
