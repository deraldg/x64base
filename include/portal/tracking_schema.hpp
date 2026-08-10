// @dottalk.file v1
// subsystem: portal
// layer: header
// owns:
// project: project.x64base.runtime
// lane: AIF-086
// owner: member.derald
// status: experimental

// tracking_schema.hpp -- DBF schema for the AI-Portal document/task/project/lane
// tracking layer (AIF-086 M1; TRACKING_STATE_DOGFOOD_LANE_V1.md).
//
// WHY: the tracking layer (lanes, runs, proofs, tasks) currently lives as authored
// YAML/Markdown that DRIFTS -- stale reports, missing run rows, hand-kept totals.
// Identity (SYSMEMBER...), the BBS (SYSBOARD...), and rulings (SYSRULING) already
// persist as DBF and DERIVE their reports. These tables turn the same move on the
// project's own governance: state that is authored drifts, state that is derived
// cannot.
//
// DESIGN RULE (carried from ruling_schema.hpp): TABLE = STATE, MARKDOWN = ARGUMENT.
// Only short, machine-answerable fields live here; the long prose stays in the
// markdown it is good at. So these tables take NO dependency on the deferred 64-bit
// memo work (AIF-070 / 082 6.10 / 083 F5).
//
// KEY-FK DECISION (v1): attribution and cross-refs use NATURAL KEYS (member.mkey,
// lane LKEY, run RKEY) as string FKs, NOT numeric SYSMEMBER/SYSLANE ids. Reason:
// these tables are seeded from EXTERNAL authored data that has no engine ids, so a
// key column loads 1:1 from CSV (IMPORT maps by column name) with no untestable
// key->id resolution step. Keys are stable and classic-browsable; reports resolve
// member details by joining SYSMEMBER on MKEY at read time. Numeric *ID columns are
// a later enrichment once seeding is proven.
//
// Conventions mirror identity/bbs/ruling schema: physical names <= 10 chars; 64-bit
// ids/epochs N(20,0) decimal text with 0 = unset; enums small N; bools L. Namespace
// dottalk::portal::schema (alongside SYSRULING); stored under data/metadata/portal/.
//
// STATUS on the M ladder: schema authored + source-evidenced. NOT built, NOT
// seeded, NO runtime -- a maintainer handoff (the steward's sandbox glibc cannot
// run the engine; measured 2026-08-04). Append-only where history matters (SYSRUN
// and status transitions): current state = highest ID/timestamp per key.
#pragma once

#include <cstdint>
#include <vector>

#include "bbs/bbs_schema.hpp"   // FieldSpec, Table, N(), C(), L(), namespace w

namespace dottalk::portal::schema {

using dottalk::bbs::schema::C;
using dottalk::bbs::schema::FieldSpec;
using dottalk::bbs::schema::L;
using dottalk::bbs::schema::N;
using dottalk::bbs::schema::Table;
namespace w = dottalk::bbs::schema::w;

// Widths not covered by bbs::schema::w. Kept narrow on purpose.
namespace tw {
inline constexpr std::uint32_t LKEY = 16;   // lane key, "AIF-087"
inline constexpr std::uint32_t CLS  = 24;   // sdlc lane / state class / channel
} // namespace tw

// SYSLANE -- the AIF lanes (from the intake queue + claim files).
// STATUS: 0 proposed 1 active 2 partial 3 landed 4 closed 5 retired.
inline Table syslane() {
    return {"SYSLANE", {
        N("ID", w::ID), C("LKEY", tw::LKEY), C("TITLE", w::SUBJ),
        C("OWNERKEY", w::KEY), C("STEWARDKEY", w::KEY), C("PROJECT", w::NAME),
        C("SDLCLANE", tw::CLS), N("STATUS", 2), L("CLAIMED"), C("ANCHOR", w::SUBJ),
        N("OPENAT", w::ID), N("CLOSEAT", w::ID), N("ROWVER", w::ID),
    }};
}

// SYSRUN -- five-role run records (AIF-050). STATUS: 0 active 1 closed. Append-only.
// REPORT holds the ai_report_audit report_id string (e.g. AIPR-20260804-004).
inline Table sysrun() {
    return {"SYSRUN", {
        N("ID", w::ID), C("RKEY", w::NAME), C("MEMBERKEY", w::KEY), C("ROLE", tw::CLS),
        C("OWNERKEY", w::KEY), C("COMMITKEY", w::KEY), C("AUTHORKEY", w::KEY), C("PLANKEY", w::KEY),
        C("PROJECT", w::NAME), N("STATUS", 2), N("STARTAT", w::ID),
        C("BRANCH", w::NAME), C("HANDLE", w::NAME), C("REPORT", w::NAME), N("ROWVER", w::ID),
    }};
}

// SYSRUNLANE -- run <-> lane crosswalk (a run touches many lanes). Mirror SYSROLEPERM.
// current_by_lane becomes a derived query: newest SYSRUN per SYSLANE via this table.
inline Table sysrunlane() {
    return {"SYSRUNLANE", {
        C("RUNKEY", w::NAME), C("LANEKEY", tw::LKEY),
    }};
}

// SYSPROOF -- the proof ledger (from proofs.yaml).
// STATE: runtime_observed / source_defined / validated / design_intended.
inline Table sysproof() {
    return {"SYSPROOF", {
        N("ID", w::ID), C("PKEY", w::KEY), C("LABEL", w::SUBJ), C("STATE", tw::CLS),
        C("LANEKEY", tw::LKEY), C("SOURCE", w::SUBJ), N("OBSAT", w::ID), N("ROWVER", w::ID),
    }};
}

// SYSTASK -- operational tasks (from ai_portal_tasks.yaml).
// STATUS: 0 open 1 in_progress 2 done 3 returned 4 parked.
inline Table systask() {
    return {"SYSTASK", {
        N("ID", w::ID), C("TKEY", w::NAME), C("TITLE", w::SUBJ), C("ASSIGNKEY", w::KEY),
        N("STATUS", 2), C("CHANNEL", tw::CLS), C("LANEKEY", tw::LKEY),
        N("DUEAT", w::ID), N("DONEAT", w::ID), N("ROWVER", w::ID),
    }};
}

// Load-safe order: lanes, runs, crosswalk, proofs, tasks.
inline std::vector<Table> tracking_tables() {
    return { syslane(), sysrun(), sysrunlane(), sysproof(), systask() };
}

} // namespace dottalk::portal::schema
