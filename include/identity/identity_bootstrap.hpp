// @dottalk.file v1
// subsystem: identity
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: AIF-045
// owner: member.derald
// status: supported

#pragma once
// include/identity/identity_bootstrap.hpp
// Process-wide identity store bootstrap (AIF-045 2b-i / 2b-iii).
//
// The store is now DBF-authoritative (2b-iii boot adoption): on first use the engine
// loads the identity catalog from data/metadata/identity if present; if the tables are
// absent it seeds from the standard role/permission catalog and PERSISTS them; if the
// tables are present but cannot be read it falls back to a READ-ONLY seed (degraded
// startup) rather than overwriting a corrupt catalog. This is the APH-5 self-hosting path.

#include "identity/identity_repository.hpp"

#include <string>

namespace dottalk::identity {

// How the process-wide store was populated at boot.
enum class StoreOrigin {
    Seed,          // tables absent -> seeded from catalog and persisted to DBF (writable)
    Dbf,           // tables present and loaded from DBF (authoritative, writable)
    DegradedSeed,  // tables present but unreadable -> read-only seed, DBF left untouched
};

// Load-or-seed boot logic against an explicit directory (testable, no singleton).
// origin/read_only report which path was taken.
InMemoryIdentityStore boot_identity_store(const std::string& dir,
                                          StoreOrigin& origin, bool& read_only);

// Built once, on first use (boots against data/metadata/identity).
const InMemoryIdentityStore& identity_store();

// Boot provenance of the process-wide store.
StoreOrigin identity_store_origin();
bool        identity_store_read_only();
const char* store_origin_name(StoreOrigin o);

// --- Runtime mutation surface (2c) ---------------------------------------------
// The mutable process store. Mutations must be followed by persist_identity_store().
// Refused paths should first check identity_store_writable() (false when degraded).
InMemoryIdentityStore& mutable_identity_store();
bool identity_store_writable();

// Persist the active store to its DBF home. Returns false + err when read-only or on I/O error.
bool persist_identity_store(std::string& err);

// ID allocation (max existing id + 1), for new members / grants / users.
TeamMemberId    next_member_id();
AuthorizationId next_authorization_id();
UserId          next_user_id();

// Wall clock (epoch seconds) for grant expiry; refresh sets store.now for the resolver.
std::uint64_t identity_now();
void          identity_refresh_clock();

// Portable-key lookups (return nullptr if absent).
inline const TeamMember* find_member_by_key(const InMemoryIdentityStore& s, const std::string& key) {
    for (const auto& m : s.members) if (m.key == key) return &m;
    return nullptr;
}
inline const Permission* find_permission_by_key(const InMemoryIdentityStore& s, const std::string& key) {
    for (const auto& p : s.permissions) if (p.key == key) return &p;
    return nullptr;
}
inline const User* find_user_by_id(const InMemoryIdentityStore& s, UserId id) {
    for (const auto& u : s.users) if (u.id == id) return &u;
    return nullptr;
}
inline const Role* find_role_by_id(const InMemoryIdentityStore& s, RoleId id) {
    for (const auto& r : s.roles) if (r.id == id) return &r;
    return nullptr;
}
inline const Role* find_role_by_key(const InMemoryIdentityStore& s, const std::string& key) {
    for (const auto& r : s.roles) if (r.key == key) return &r;
    return nullptr;
}
inline const OrgUnit* find_org_by_key(const InMemoryIdentityStore& s, const std::string& key) {
    for (const auto& o : s.org_units) if (o.key == key) return &o;
    return nullptr;
}

// --- Org roster (partner lane) --------------------------------------------------
// The standard org roster, applied IDEMPOTENTLY BY KEY: existing rows keep their ids
// and are never rewritten, missing rows are appended. ONE function so build_seed()
// (fresh install) and USER ORG BACKFILL (existing catalog) cannot drift apart --
// boot_identity_store only seeds when SYSUSER.dbf is ABSENT, so a store that already
// exists will never see build_seed() and needs the backfill path instead.
//
// Operates on the passed store and allocates ids from it, so it is safe to call
// during build_seed() before the process singleton exists. Returns rows added.
//
// It creates MEMBERSHIP assignments only: org_unit set, work unset, AKIND empty.
// Per-matter standing rows (amicus/movant/...) need the work axis, and WorkNode is
// still a dead declaration -- see PARTNER_AMICUS_STANDING_LANE_V1.md.
//
// It deliberately does NOT touch MemberRole::org_scope. Setting that would NARROW an
// existing role binding to one org and could start denying permissions that resolve
// today, which is not a thing a backfill gets to do.
int apply_standard_orgs(InMemoryIdentityStore& s);

} // namespace dottalk::identity
