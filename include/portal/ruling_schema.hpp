// ruling_schema.hpp -- DBF schema for AI-portal ruling state (AIF-082).
//
// WHY THIS TABLE EXISTS
// ---------------------
// Owner rulings currently live as prose in docs/maintenance/AIF_*RULING_SHEET*.md,
// with an empty `Ruling` cell and a hand-kept running total in the footer. Two
// consequences, both measured on 2026-07-31:
//
//   1. NO HISTORY. The generated rulings console can render exactly two kinds of
//      dated event -- a group-ratification header and a file mtime -- because no
//      individual ruling carries a dated status transition.
//   2. THE HAND-KEPT TOTAL DRIFTS. The sheet declared `Total open: 20` while
//      parsing found 17, because a footer maintained by hand is not updated every
//      time a row lands.
//
// Both are the AIF-082 thesis applied to the lane's own governance: state that is
// authored drifts, state that is derived cannot. So ruling STATE moves into the
// store the project already dogfoods, and the console derives from it.
//
// DESIGN RULE -- STATE HERE, PROSE IN THE SHEET
// ---------------------------------------------
// This table deliberately does NOT carry the ruling text. A ruling's argument is
// paragraphs long; BODY is C(240) (see bbs_schema.hpp:47, "memo upgrade
// deferred"), and AIF-083 F5 records that the same 240-byte ceiling already fails
// the BBS for the same reason. Rather than make this table a FOURTH claimant on
// the 64-bit memo work (AIF-070 / AIF-082 6.10 / AIF-083 F5), it stores only what
// is short and machine-answerable: which ruling, what status, when, by whom, and
// a one-line note. The prose stays in the markdown sheet, which is good at prose.
//
// The projection is therefore: sheet = argument, table = decision. A row here
// without a matching sheet entry is an orphan; a sheet entry without a row here
// is simply undecided, which is the normal state and needs no row.
//
// STATUS on the M-milestone ladder:
//   schema authored and source-evidenced. NOT built, NOT seeded, NO runtime.
//   The steward cannot execute the engine (measured: sandbox glibc against the
//   binary's requirement), so creation and seeding are a maintainer handoff --
//   see docs/maintenance/RULING_STATE_DOGFOOD_V1.md.
#pragma once

#include <cstdint>
#include <vector>

#include "bbs/bbs_schema.hpp"   // FieldSpec, Table, N(), C(), namespace w

namespace dottalk::portal::schema {

using dottalk::bbs::schema::C;
using dottalk::bbs::schema::FieldSpec;
using dottalk::bbs::schema::N;
using dottalk::bbs::schema::Table;
namespace w = dottalk::bbs::schema::w;

// Widths not already covered by bbs::schema::w. Kept narrow on purpose: every
// field here must be answerable without a memo, or it does not belong (see the
// design rule above).
namespace rw {
inline constexpr std::uint32_t RULEID = 16;   // "6.5a", "R27b.2", "X1"
inline constexpr std::uint32_t LANE   = 12;   // "AIF-082"
inline constexpr std::uint32_t GROUP  = 24;   // "Group A", "Group E"
inline constexpr std::uint32_t NOTE   = 240;  // one line; NOT the argument
} // namespace rw

// STATUS ladder. Deliberately ordered so that a numeric comparison is meaningful
// and an unknown future value sorts last rather than silently reading as 0.
//   0 = proposed    filed, no decision
//   1 = ratified    accepted by the owner
//   2 = rejected    declined, with the reason in NOTE
//   3 = superseded  replaced by another ruling; SUPERBY names it
//   4 = withdrawn   pulled by the steward before a decision
//
// A row is APPEND-ONLY: a status change is a NEW row with a later DECIDEDAT, not
// an update in place. That is what makes history real rather than a snapshot --
// the same reason SYSPOST appends rather than edits. Current status of a ruling
// is the row with the highest DECIDEDAT for that RULEID.
inline Table sysruling() {
    return {"SYSRULING", {
        N("ID",       w::ID),        // monotonic row id
        C("RULEID",   rw::RULEID),   // ruling identifier, unique per LANE
        C("LANE",     rw::LANE),     // owning AIF lane
        C("RULEGROUP", rw::GROUP),   // sheet grouping, for rendering only
        N("STATUS",   2),            // ladder above
        N("DECIDEDAT", w::ID),       // epoch seconds; 0 = not yet decided
        N("DECIDEDBY", w::ID),       // member id (identity SYSMEMBER); 0 = unknown
        N("PROPOSEDAT", w::ID),      // epoch seconds the ruling was first filed
        C("STEWARD",  w::KEY),       // member key of the proposing steward
        C("SUPERBY",  rw::RULEID),   // RULEID that supersedes this one; blank if none
        C("BLOCKS",   w::KEY),       // what this ruling unblocks, e.g. "M4" or "6.6"
        C("NOTE",     rw::NOTE),     // one line: the decision, NOT the argument
        N("ROWVER",   w::ID),        // row version, parallel to SYSBOARD
    }};
}

inline std::vector<Table> tables() { return {sysruling()}; }

} // namespace dottalk::portal::schema
