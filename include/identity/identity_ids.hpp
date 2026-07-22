#pragma once
// include/identity/identity_ids.hpp
// Strong 64-bit ID types for the identity / RBAC layer (AIF-045, Contract v1 §2).
//
// Each ID is a distinct type keyed by a unique tag, so a UserId can never be passed
// where a RoleId is expected. 0 == unset. Portable string keys live on the entities;
// these numeric IDs are the authoritative in-x64base handles.

#include <compare>
#include <cstdint>

namespace dottalk::identity {

template <class Tag>
class StrongId {
public:
    using value_type = std::uint64_t;

    constexpr StrongId() noexcept = default;
    constexpr explicit StrongId(value_type v) noexcept : v_(v) {}

    constexpr value_type value() const noexcept { return v_; }
    constexpr bool       valid() const noexcept { return v_ != 0; }  // 0 = unset

    constexpr bool operator==(const StrongId&) const noexcept = default;
    constexpr auto operator<=>(const StrongId&) const noexcept = default;

private:
    value_type v_{0};
};

struct UserIdTag;          using UserId          = StrongId<UserIdTag>;
struct TeamMemberIdTag;    using TeamMemberId    = StrongId<TeamMemberIdTag>;
struct RoleIdTag;          using RoleId          = StrongId<RoleIdTag>;
struct PermissionIdTag;    using PermissionId    = StrongId<PermissionIdTag>;
struct PermissionSetIdTag; using PermissionSetId = StrongId<PermissionSetIdTag>;
struct AssignmentIdTag;    using AssignmentId    = StrongId<AssignmentIdTag>;
struct AuthorizationIdTag; using AuthorizationId = StrongId<AuthorizationIdTag>;
struct OrgUnitIdTag;       using OrgUnitId       = StrongId<OrgUnitIdTag>;
struct WorkNodeIdTag;      using WorkNodeId      = StrongId<WorkNodeIdTag>;
struct EventIdTag;         using EventId         = StrongId<EventIdTag>;

} // namespace dottalk::identity
