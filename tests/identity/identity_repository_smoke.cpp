// src/identity/identity_repository_smoke.cpp
// Standalone proof for the identity repository + snapshot materialization (AIF-045 M2a).
// Builds a small org and resolves through the store: stored entities -> materialized
// ResolutionSnapshot -> pure resolver. Proves the full stack end to end (still no engine).
//
//   g++ -std=c++20 -I include src/identity/identity_repository_smoke.cpp -o idrepo && ./idrepo

#include "identity/identity_repository.hpp"

#include <cassert>
#include <iostream>

using namespace dottalk::identity;

int main() {
    // --- Permissions ---
    Permission git_push     {PermissionId{1},  "git.push",       "git",      "push",   RiskClass::High, true,  EntityStatus::Active};
    Permission git_commit   {PermissionId{2},  "git.commit",     "git",      "commit", RiskClass::High, true,  EntityStatus::Active};
    Permission source_mutate{PermissionId{10}, "source.mutate",  "source",   "mutate", RiskClass::High, false, EntityStatus::Active};
    Permission source_prop  {PermissionId{11}, "source.propose", "source",   "propose",RiskClass::Low,  false, EntityStatus::Active};
    Permission db_mutate    {PermissionId{20}, "database.mutate","database",  "mutate", RiskClass::Medium,false,EntityStatus::Active};
    Permission host_shell   {PermissionId{30}, "host.shell",     "host",     "shell",  RiskClass::Critical,false,EntityStatus::Active};

    // --- Roles ---
    const RoleId MAINTAINER{1}, AI_PARTNER{2}, STUDENT{3};

    // --- Members ---
    const TeamMemberId DERALD{1}, AI{2}, STUDENTM{3};

    // --- Work scopes ---
    const WorkNodeId W1{100}, W2{200};

    InMemoryIdentityStore store;
    store.permissions = {git_push, git_commit, source_mutate, source_prop, db_mutate, host_shell};

    store.role_permissions = {
        {MAINTAINER, git_push.id}, {MAINTAINER, git_commit.id}, {MAINTAINER, source_mutate.id},
        {MAINTAINER, source_prop.id}, {MAINTAINER, host_shell.id},
        {AI_PARTNER, source_prop.id}, {AI_PARTNER, git_commit.id},   // partner is *eligible* for git.commit
    };
    store.member_roles = {
        {DERALD,   MAINTAINER, std::nullopt, std::nullopt},
        {AI,       AI_PARTNER, std::nullopt, std::nullopt},
        {STUDENTM, STUDENT,    std::nullopt, std::nullopt},
    };
    // student gets a scoped ALLOW for database.mutate on work node W1 only.
    store.overrides = {
        {STUDENTM, db_mutate.id, OverrideEffect::Allow, std::nullopt, W1},
    };
    // derald has a live grant for git.push (a requires-approval permission).
    AuthorizationGrant g_push;
    g_push.id = AuthorizationId{1}; g_push.granted_to = DERALD;
    g_push.status = GrantStatus::Granted; g_push.action_scope = "git.push";
    store.grants = {g_push};

    const RuntimeContext ok{true, true};
    const RuntimeContext policy_off{true, false};
    const Scope any{std::nullopt, std::nullopt};

    // A) derald / MAINTAINER git.push (needs approval; has role perm + live grant) -> ALLOW
    assert(authorize(store, DERALD, git_push, any, ok).allowed());

    // B) AI source.mutate: not eligible (partner has propose, not mutate) -> DENY (Eligibility)
    {
        auto d = authorize(store, AI, source_mutate, any, ok);
        assert(!d.allowed() && d.stage == DenyStage::Eligibility);
    }

    // C) AI source.propose (no approval) -> ALLOW ; AI git.commit (eligible but no grant) -> DENY (Authorization)
    assert(authorize(store, AI, source_prop, any, ok).allowed());
    {
        auto d = authorize(store, AI, git_commit, any, ok);
        assert(!d.allowed() && d.stage == DenyStage::Authorization);
    }

    // D) student database.mutate: in scope W1 (override applies) -> ALLOW ; scope W2 -> DENY (Eligibility)
    assert(authorize(store, STUDENTM, db_mutate, Scope{std::nullopt, W1}, ok).allowed());
    {
        auto d = authorize(store, STUDENTM, db_mutate, Scope{std::nullopt, W2}, ok);
        assert(!d.allowed() && d.stage == DenyStage::Eligibility);
    }

    // E) derald host.shell but runtime security policy OFF -> DENY (SecurityPolicy, the last word)
    {
        auto d = authorize(store, DERALD, host_shell, any, policy_off);
        assert(!d.allowed() && d.stage == DenyStage::SecurityPolicy);
    }

    // F) DENY precedence via a scoped DENY override even though a role grants eligibility.
    store.overrides.push_back({AI, source_prop.id, OverrideEffect::Deny, std::nullopt, std::nullopt});
    {
        auto d = authorize(store, AI, source_prop, any, ok);
        assert(!d.allowed() && d.stage == DenyStage::Denial);
    }

    std::cout << "IDENTITY-M2A-REPO-SMOKE:PASS"
              << "  (entities->store->materialize->resolver end to end; A-F drive off real data)\n";
    return 0;
}
