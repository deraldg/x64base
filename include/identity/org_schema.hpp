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
// Standing vocabulary and org doctrine. Companion to identity_schema.hpp.
//
// THE TABLE ITSELF LIVES NEXT DOOR. sysorg() is declared in identity_schema.hpp
// beside the other catalogs and folded into all_tables(); it is NOT redeclared here,
// because two inline definitions of one table in one namespace is a redefinition
// error waiting for the first translation unit that includes both. This header
// carries what the schema file has no room for: why the table exists, what the
// AKIND ladder means, and the predicates that read them.
//
// WHY THIS EXISTS -- THE DANGLING SCOPE
// -------------------------------------
// identity_entities.hpp declares OrgUnit and OrgUnitType. Until this lane nothing
// instantiated them: no store vector, no table, no CLI surface. But the ID was
// already load-bearing in three persisted columns -- SYSMEMROLE.ORGSCOPE,
// SYSOVERRIDE.ORGSCOPE, SYSASSIGN.ORGUNIT -- written and read back by
// identity_dbf_store.cpp, and consulted by the resolver's applies() at
// identity_repository.hpp on EVERY permission decision. With no org rows to
// reference, applies() degenerated to "global scope always matches."
//
// So org scoping was built, wired, and inert for want of a table. This lane adds no
// new mechanism; it lights up one already in the tree.
//
// WHAT IT IS FOR -- PARTNERS, AND WHY NOT A NEW MemberKind
// --------------------------------------------------------
// The driving need is a home for PARTNERS: outside parties whose agents use this
// system. Before this lane "partner" existed only as role.ai_partner (RoleId 6,
// identity_bootstrap.cpp), which grants capability -- "read + propose, no direct
// mutate" -- and says nothing about WHO an agent answers to.
// member.ai.claude.cowork and member.ai.grok.xai carry identical roles and were
// indistinguishable as parties.
//
// MemberKind was considered and rejected as the axis. It answers what an actor is
// MADE OF (Human/AI/Service/External), not whose it is; its External value is already
// load-bearing for member.guest at minimum privilege; and SYSPOST.AUTHKIND
// (bbs_schema.hpp) freezes the raw ordinal into every historical post, so the enum is
// append-only forever and should not absorb an orthogonal concern.
//
// DESIGN RULE -- IDENTITY IN THE TABLE, STANDING ON THE ASSIGNMENT
// ----------------------------------------------------------------
// SYSORG carries only WHO A PARTY IS. It deliberately does NOT carry whether that
// party is a reviewer, an author, or a bystander in any given matter, because
// standing is RELATIONAL -- a property of (party, matter), not of the party.
// member.ai.grok.xai is a disinterested reviewer on PDR-001 and an interested author
// on its own AIF-098 patches, at the same time. A table of reviewers would need a row
// per matter, at which point it has become an assignment table.
//
// The assignment table already existed, and its classification column was empty.
// SYSASSIGN.AKIND is C(24) (identity_schema.hpp), mirrored in
// tools/dbf/schema_registry.py, written and read by identity_dbf_store.cpp,
// documented in SYSTEM_SCHEMA_MAP_AND_NORMALIZATION_V1.md -- and was never assigned a
// non-empty value anywhere in the tree. Standing goes there. See kAmicus below.
//
// The projection is therefore: SYSORG = who you are, AKIND = what you are in this
// matter. Parallel to ruling_schema.hpp's "sheet = argument, table = decision."
//
// STATUS on the M-milestone ladder:
//   source-evidenced, compiles, NOT seeded, NO runtime evidence. No org rows exist
//   and no assignment carries a standing value, so every predicate below is
//   currently vacuous. Seeding and the runtime proof are a maintainer handoff --
//   see docs/maintenance/PARTNER_AMICUS_STANDING_LANE_V1.md.

#include <string>

namespace dottalk::identity::standing {

// ---- SYSASSIGN.AKIND values ---------------------------------------------
//
// AKIND is C(24) free text, so this ladder is a CONVENTION, not a constraint the DBF
// layer can enforce. Every reader must therefore fail closed on anything it does not
// recognise. Values are lowercase, matching the house key style.
//
// The vocabulary is borrowed from the court the project already half-built.
// ruling_schema.hpp is a docket in all but name -- RULEID, STEWARD, PROPOSEDAT,
// DECIDEDBY, SUPERBY, and a ladder of proposed/ratified/rejected/superseded/withdrawn
// with 0 glossed "filed, no decision." Standing is the piece it was missing: WHO may
// file, and on what footing.

// A non-party. No stake in the outcome, files findings only, cannot be granted
// relief. This is the amicus curiae posture and the reason partners are worth
// modelling at all: PEER_REVIEW_HEADER_ONLY_FINDINGS_20260813_V1 found that a hosted
// seat with no tree access is not a weaker local seat but the seat that audits what
// local seats assert. That value comes from disinterest, and disinterest is only
// checkable if parties are distinguishable.
inline constexpr const char* kAmicus  = "amicus";

// An interested filer. Seeks a ruling on work it authored or has a stake in --
// paradigmatically an outside AI submitting a change package per
// EXTERNAL_AI_CHANGE_PACKAGE_V1. RECUSED from reviewing its own matter. This is the
// standing that contract was reaching for when it said it "does not authorize the
// outside AI to ... approve its own patch"; until this lane nothing in the data could
// tell you whether a reviewer authored the thing under review.
inline constexpr const char* kMovant  = "movant";

// The member who owns the work under review in this matter. A party. Never amicus.
inline constexpr const char* kSteward = "steward";

// Moderates a review session; does not vote. A party, therefore never amicus --
// which is exactly PDR-001 sec 0's conflicted-abstain rule, restated as a consequence
// of standing rather than as a house convention.
inline constexpr const char* kHost    = "host";

// Rules. Redundant with identity_admin.cpp's is_owner_member() for enforcement
// purposes; present so a session record can name every seat in one vocabulary.
inline constexpr const char* kOwner   = "owner";

// The legacy / unclassified value. EVERY EXISTING SYSASSIGN ROW HAS THIS, because
// nothing has ever written AKIND. It means NO STANDING ESTABLISHED. It must never be
// read as amicus. Absence of a recorded stake is not evidence of disinterest.
inline constexpr const char* kUnset   = "";

// True only for a value this ladder actually names. Anything else -- empty, legacy,
// a typo, a value from a future ladder this build predates -- is NOT standing.
inline bool is_known(const std::string& v) {
    return v == kAmicus || v == kMovant || v == kSteward || v == kHost || v == kOwner;
}

// A party has a stake in the outcome and is therefore never amicus. Note that an
// UNKNOWN value returns false here: it is not a party, but is_amicus() below will
// also refuse it, so an unrecognised standing can neither review nor be recused. It
// is inert, which is the correct failure direction.
inline bool is_party(const std::string& v) {
    return v == kMovant || v == kSteward || v == kHost;
}

inline bool is_amicus(const std::string& v) { return v == kAmicus; }

} // namespace dottalk::identity::standing

// ---- predicates ---------------------------------------------------------
//
// Stated as doctrine so the eventual call sites and any reviewer agree on semantics.
// Deliberately NOT implemented over the store here: this header has no store
// dependency and should keep none until there is a caller to shape it.
//
//   independent(a, b) :=
//       a.ORGUNIT != 0 AND b.ORGUNIT != 0 AND a.ORGUNIT != b.ORGUNIT
//
//     FAIL CLOSED ON ZERO, AND THIS IS THE WHOLE TRAP. ORGUNIT = 0 means "no org
//     recorded," which today is EVERY row in SYSASSIGN. A naive `a != b` reads
//     0 != 0 as false and appears to behave -- but the moment one row acquires an org
//     while its counterpart stays 0, the pair reads as independent on the strength of
//     a missing value. Unset is not a party. Two unknowns are not two different
//     parties.
//
//   recused(member, matter) := is_party(standing_of(member, matter))
//
//   amicus_eligible(member, matter) :=
//       is_amicus(standing_of(member, matter))
//   AND NOT recused(member, matter)
//   AND independent(member, steward_of(matter))
//
//     The recusal clause is redundant against the first conjunct today and is kept
//     deliberately: it survives a future where a member holds more than one standing
//     in one matter, and it makes the intent legible without reconstructing the ladder.
//
// SYSASSIGN carries ClosePolicy("bitemporal", VTHRU, ROWVER) already. Standing is
// therefore time-boxed by construction -- leave to file expires on VTHRU with no extra
// mechanism, which is the property that makes an admitted non-party revocable rather
// than permanent.
