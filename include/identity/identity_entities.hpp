#pragma once
// include/identity/identity_entities.hpp
// Domain entities for the identity / RBAC layer (AIF-045, Contract v1 §3).
//
// PURE DATA. No database access and no permission computation live here — resolving
// effective permissions is a separate service (M1b), per the entity-vs-service split.

#include "identity/identity_ids.hpp"

#include <cstdint>
#include <optional>
#include <string>

namespace dottalk::identity {

enum class MemberKind     : std::uint8_t { Human, AI, Service, External };
enum class EntityStatus   : std::uint8_t { Active, Suspended, Retired };
enum class AuthKind       : std::uint8_t { LocalTrusted, OsBound, Password, Token, HumanAsserted };
enum class OverrideEffect : std::uint8_t { Allow, Deny };
enum class RiskClass      : std::uint8_t { Low, Medium, High, Critical };

// Bi-temporal validity + optimistic-concurrency stamp on managed rows.
struct RowStamp {
    std::uint64_t valid_from    = 0;
    std::uint64_t valid_through = 0;   // 0 = open
    std::uint64_t row_version   = 0;
};

// §3.1 identity / account. Owns identity only — never role/project/permission/session.
struct User {
    UserId       id;
    std::string  key;               // user.derald
    std::string  login_name;
    std::string  display_name;
    AuthKind     auth_kind = AuthKind::LocalTrusted;
    std::string  credential_ref;    // opaque ref; empty until real auth; never a plaintext secret
    EntityStatus status = EntityStatus::Active;
    std::string  profile_home_key;  // binds to dottalkpp/user/<key>/  (Contract §5)
    RowStamp     stamp;
};

// §3.2 participation (durable org/project actor). Context (manager/project/permissions/session)
// deliberately lives in assignments/authorizations, NOT here.
struct TeamMember {
    TeamMemberId                   id;
    std::optional<UserId>          user_id;                 // NULL for pure SERVICE identities
    std::string                    key;                     // member.derald / member.ai.claude.cowork
    MemberKind                     kind = MemberKind::Human;
    std::optional<RoleId>          default_role;
    std::optional<PermissionSetId> default_permission_set;
    EntityStatus                   status = EntityStatus::Active;
    RowStamp                       stamp;
};

// §3.3 function
struct Role {
    RoleId       id;
    std::string  key, name, kind, description;
    EntityStatus status = EntityStatus::Active;
};

// §3.4 eligibility
struct Permission {
    PermissionId id;
    std::string  key;               // source.mutate
    std::string  resource_class, action;
    RiskClass    risk = RiskClass::Low;
    bool         requires_approval = false;
    EntityStatus status = EntityStatus::Active;
};

// §3.5 crosswalks (scoped; DENY overrides ALLOW in resolution)
struct RolePermission { RoleId role; PermissionId permission; };
struct MemberRole {
    TeamMemberId             member;
    RoleId                   role;
    std::optional<OrgUnitId> org_scope;
    std::optional<WorkNodeId> work_scope;
};
struct MemberPermissionOverride {
    TeamMemberId              member;
    PermissionId             permission;
    OverrideEffect           effect;
    std::optional<OrgUnitId> org_scope;
    std::optional<WorkNodeId> work_scope;
};

// §3.6 two SEPARATE hierarchies — org containment vs work decomposition.
enum class OrgUnitType  : std::uint8_t { Organization, Division, Department, Team, Committee, Class, Lab };
enum class WorkNodeType : std::uint8_t { Project, Lane, Gate, Milestone, Epic, Task, Proof, Publication };

struct OrgUnit {
    OrgUnitId                id;
    std::string              key;
    std::optional<OrgUnitId> parent;
    OrgUnitType              type = OrgUnitType::Team;
    std::string              name;
    EntityStatus             status = EntityStatus::Active;
    int                      sort_order = 0;
    RowStamp                 stamp;
};

struct WorkNode {
    WorkNodeId                  id;
    std::string                 key;
    std::optional<WorkNodeId>   parent;
    WorkNodeType                type = WorkNodeType::Task;
    std::string                 project_key, title;
    std::string                 status;
    int                         priority = 0;
    std::optional<AssignmentId> owner_assignment;
    std::string                 next_gate, truth_state, proof_state;
    RiskClass                   risk = RiskClass::Low;
    int                         sort_order = 0;
    RowStamp                    stamp;
};

// §3.7 central crosswalk. Reporting lives on the ASSIGNMENT, not the member.
struct TeamAssignment {
    AssignmentId                   id;
    TeamMemberId                   member;
    std::optional<OrgUnitId>       org_unit;
    std::optional<WorkNodeId>      work;
    std::optional<RoleId>          role;
    std::optional<PermissionSetId> permission_set;
    std::optional<AssignmentId>    reports_to;
    std::string                    assignment_kind;
    EntityStatus                   status = EntityStatus::Active;
    RowStamp                       stamp;
};

// §3.8 durable approval
enum class GrantStatus : std::uint8_t { Requested, Granted, Denied, Expired, Revoked };
struct AuthorizationGrant {
    AuthorizationId             id;
    TeamMemberId                requested_by, granted_to;
    std::optional<AssignmentId> role_assignment;
    std::optional<WorkNodeId>   work;
    std::string                 resource_scope, action_scope;
    RiskClass                   risk = RiskClass::Low;
    std::uint64_t               granted_at = 0, expires_at = 0;  // 0 = no expiry
    GrantStatus                 status = GrantStatus::Requested;
    std::string                 reason, source_report_id;
};

} // namespace dottalk::identity
