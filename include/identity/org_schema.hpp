// @dottalk.file v1
// subsystem: identity
// layer: header
// owns:
// project: project.x64base.runtime
// lane: unclaimed
// owner: member.derald
// status: review-needed

#pragma once
// include/identity/org_schema.hpp
// DBF schema for the org catalog (SYSORG) and the standing vocabulary that rides
// on SYSASSIGN.AKIND. Companion to identity_schema.hpp.
//
// WHY THIS EXISTS -- THE DANGLING SCOPE
// -------------------------------------
// identity_entities.hpp:98-110 declares OrgUnit and OrgUnitType. Nothing ever
// instantiates them: there is no store vector, no table in all_tables(), no CLI
// surface. But the ID is already load-bearing in three persisted columns --
// SYSMEMROLE.ORGSCOPE, SYSOVERRIDE.ORGSCOPE, SYSASSIGN.ORGUNIT -- written at
// identity_dbf_store.cpp:238 and read back at :344/:352/:359, and consulted by
// the resolver's applies() at identity_repository.hpp:71 on EVERY permission
// decision. With no org rows to reference, applies() degenerates to "global
// scope always matches."
//
// So org scoping is built, wired, and inert for want of a table. This header is
// that table. It adds no new mechanism; it lights up one already in the tree.
//
// WHAT IT IS FOR -- PARTNERS, AND WHY NOT A NEW MemberKind
// --------------------------------------------------------
// The driving need is a home for PARTNERS: outside parties whose agents use this
// system. Today "partner" exists only as role.ai_partner (RoleId 6,
// identity_bootstrap.cpp:39) which is a grant of capability -- "read + propose,
// no direct mutate" -- and says nothing about WHO an agent answers to.
// member.ai.claude.cowork and member.ai.grok.xai carry identical roles and are
// indistinguishable as parties.
//
// MemberKind was considered and rejected as the axis. It answers what an actor is
// MADE OF (Human/AI/Service/External), not whose it is; its External value is
// already load-bearing for member.guest at minimum privilege; and SYSPOST.AUTHKIND
// (bbs_schema.hpp:76) freezes the raw ordinal into every historical post, so the
// enum is append-only forever and should not absorb an orthogonal concern.
//
// DESIGN RULE -- IDENTITY HERE, STANDING ON THE ASSIGNMENT
// ---------------------------------------------------------
// This table carries only WHO A PARTY IS. It deliberately does NOT carry whether
// that party is a reviewer, an author, or a bystander in any given matter, because
// standing is RELATIONAL -- a property of (party, matter), not of the party.
// member.ai.grok.xai is a disinterested reviewer on PDR-001 and an interested
// author on its own AIF-098 patches, at the same time. A table of reviewers would
// need a row per matter, at which point it has become an assignment table.
//
// The assignment table already exists, and its classification column is empty.
// SYSASSIGN.AKIND is C(24) (identity_schema.hpp:113), mirrored in
// tools/dbf/schema_registry.py:133, written at identity_dbf_store.cpp:240, read at
// :361, documented in SYSTEM_SCHEMA_MAP_AND_NORMALIZATION_V1.md:57 -- and never
// assigned a non-empty value anywhere in the tree. Fully round-tripping, zero rows.
// Standing goes there. See kStanding below.
//
// The projection is therefore: SYSORG = who you are, AKIND = what you are in this
// matter. Parallel to ruling_schema.hpp's "sheet = argument, table = decision."
//
// STATUS on the M-milestone ladder:
//   schema authored and source-evidenced. NOT built, NOT seeded, NO runtime.
//   Deliberately NOT added to identity_schema.hpp's all_tables() -- doing so would
//   make the store create the table on next load, which is a maintainer's build
//   decision, not a header's. Creation, seeding and the all_tables() fold are a
//   maintainer handoff. See docs/maintenance/PARTNER_AMICUS_STANDING_LANE_V1.md.

#include "identity/identity_schema.hpp"   // Table, FieldSpec, N(), C(), namespace w

#include <cstdint>
#include <string>
#include <vector>

namespace dottalk::identity::schema {

// ---- SYSORG -------------------------------------------------------------
//
// One row per organizational unit. The house is a row (org.house); every outside
// party is a row. Roots have PARENT = 0; org containment is a tree, kept SEPARATE
// from work decomposition (WorkNode), per identity_entities.hpp:97.
//
// OTYPE persists the OrgUnitType ordinal. The enum as declared today is:
//   0 = Organization  1 = Division  2 = Department  3 = Team
//   4 = Committee     5 = Class     6 = Lab
// This header proposes appending ONE value:
//   7 = Partner       an outside party; not the house, not a unit of it
//
// APPEND ONLY, AND ONLY WHILE THE TABLE IS UNSEEDED. Once SYSORG holds rows the
// ordinal is frozen exactly as SYSPOST.AUTHKIND froze MemberKind. Inserting or
// reordering would silently rewrite the meaning of stored rows. Partner takes 7
// because 7 is the next free slot, not because it belongs beside Lab.
//
// Externality is intrinsic and belongs here (xAI is an outside party in every
// matter). Standing is per-matter and does NOT belong here (xAI's agent may
// review one lane and author the next). Do not add a reviewer/author flag to
// this table; that is AKIND's job.
//
// STATUS is EntityStatus: 0 = Active, 1 = Suspended, 2 = Retired.
inline Table sysorg() {
    return {"SYSORG", {
        N("ID", w::ID),          // monotonic row id
        C("OKEY", w::KEY),       // portable key: org.house, org.xai, org.anthropic
        N("PARENT", w::ID),      // parent OrgUnitId; 0 = root
        N("OTYPE", 2),           // OrgUnitType ordinal; see ladder above
        C("NAME", w::NAME),      // display name
        N("STATUS", 2),          // EntityStatus
        N("SORTORD", 6),         // render order within a parent; 0 = unset
        N("VFROM", w::ID),       // bitemporal, parallel to SYSMEMBER
        N("VTHRU", w::ID),
        N("ROWVER", w::ID),
    }};
}

inline std::vector<Table> org_tables() { return {sysorg()}; }

// ---- standing (SYSASSIGN.AKIND values) ----------------------------------
//
// AKIND is C(24) free text, so this ladder is a CONVENTION, not a constraint the
// DBF layer can enforce. Every reader must therefore fail closed on anything it
// does not recognise. Values are lowercase, matching the house key style.
//
// The vocabulary is borrowed from the court the project already half-built.
// ruling_schema.hpp is a docket in all but name -- RULEID, STEWARD, PROPOSEDAT,
// DECIDEDBY, SUPERBY, and a ladder of proposed/ratified/rejected/superseded/
// withdrawn with 0 glossed "filed, no decision." Standing is the piece it was
// missing: WHO may file, and on what footing.
namespace standing {

// A non-party. No stake in the outcome, files findings only, cannot be granted
// relief. This is the amicus curiae posture and the reason partners are worth
// modelling at all: PEER_REVIEW_HEADER_ONLY_FINDINGS_20260813_V1 found that a
// hosted seat with no tree access is not a weaker local seat but the seat that
// audits what local seats assert. That value comes from disinterest, and
// disinterest is only checkable if parties are distinguishable.
inline constexpr const char* kAmicus  = "amicus";

// An interested filer. Seeks a ruling on work it authored or has a stake in --
// paradigmatically an outside AI submitting a change package per
// EXTERNAL_AI_CHANGE_PACKAGE_V1. RECUSED from reviewing its own matter. This is
// the standing that EXTERNAL_AI_CHANGE_PACKAGE_V1 was reaching for when it said
// the contract "does not authorize the outside AI to ... approve its own patch";
// until now nothing in the data could tell you whether a reviewer authored the
// thing under review.
inline constexpr const char* kMovant  = "movant";

// The member who owns the work under review in this matter. A party. Never amicus.
inline constexpr const char* kSteward = "steward";

// Moderates a review session; does not vote. A party, therefore never amicus --
// which is exactly PDR-001 sec 0's conflicted-abstain rule, restated as a
// consequence of standing rather than as a house convention.
inline constexpr const char* kHost    = "host";

// Rules. Redundant with identity_admin.cpp:439 is_owner_member() for enforcement
// purposes; present so a session record can name every seat in one vocabulary.
inline constexpr const char* kOwner   = "owner";

// The legacy / unclassified value. EVERY EXISTING SYSASSIGN ROW HAS THIS, because
// nothing has ever written AKIND. It means NO STANDING ESTABLISHED. It must never
// be read as amicus. Absence of a recorded stake is not evidence of disinterest.
inline constexpr const char* kUnset   = "";

} // namespace standing

// ---- predicates ---------------------------------------------------------
//
// Stated here as doctrine so the eventual implementation and any reviewer agree
// on the semantics. NOT implemented in this header -- this file is pure schema,
// matching identity_schema.hpp's "PURE DATA. No database access here."
//
//   independent(a, b) :=
//       a.ORGUNIT != 0 AND b.ORGUNIT != 0 AND a.ORGUNIT != b.ORGUNIT
//
//     FAIL CLOSED ON ZERO, AND THIS IS THE WHOLE TRAP. ORGUNIT = 0 means "no org
//     recorded," which today is EVERY row in SYSASSIGN. A naive `a != b` would
//     read 0 != 0 as false and accidentally behave, but any row that acquires an
//     org while its counterpart stays 0 would then read as independent on the
//     strength of a missing value. Unset is not a party. Two unknowns are not two
//     different parties.
//
//   recused(member, matter) :=
//       standing_of(member, matter) IN { movant, steward, host }
//
//   amicus_eligible(member, matter) :=
//       standing_of(member, matter) == amicus
//       AND NOT recused(member, matter)
//       AND independent(member, steward_of(matter))
//
//     The recusal clause is redundant against the first conjunct today and is
//     kept deliberately: it survives a future where a member can hold more than
//     one standing in one matter, and it makes the intent legible without
//     reconstructing the ladder.
//
// Note that SYSASSIGN carries ClosePolicy("bitemporal", VTHRU, ROWVER) already
// (schema_registry.py:135). Standing is therefore time-boxed by construction --
// leave to file expires on VTHRU with no extra mechanism, which is the property
// that makes an admitted non-party revocable rather than permanent.

} // namespace dottalk::identity::schema
