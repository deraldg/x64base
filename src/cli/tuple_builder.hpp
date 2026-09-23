// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/tuple_builder.hpp
#pragma once

#include <string>
#include <vector>

#include "tuple_types.hpp"

namespace xbase { class DbArea; }   // PERF-2: build_tuple_for_area worker entry

namespace dottalk {

// Result wrapper so callers can handle errors without printing.
struct TupleBuildResult {
    bool ok = false;
    std::string error;            // if !ok
    TupleRow row;                 // if ok
};

TupleBuildResult build_tuple_from_spec(const std::string& spec, const TupleBuildOptions& opt);
TupleBuildResult build_tuple_default(const TupleBuildOptions& opt);

// PERF-1b (AIF-168, 2026-09-21): compiled row plan.
//
// build_tuple_from_spec re-parses the spec, re-resolves the source area by
// scanning every open work area, and resolves every field name THREE times
// per column (twice in its own body, once more inside getFieldAsString) on
// EVERY call -- all constant answers recomputed per row. In a scan the
// layout never changes; only the values do. compile_tuple_plan does the
// constant work ONCE; build_tuple_from_plan reads the current record's
// values through the precomputed 1-based field indices.
//
// Contract: the plan is valid while the referenced areas remain open with an
// unchanged field layout; row POSITIONING stays the caller's job, exactly as
// with build_tuple_from_spec. Semantics are identical for any spec both
// paths accept -- same refusal texts (emitted at compile time instead of on
// the first row), same overlay and memo behavior, same fragment provenance.
// (Fragment ORDER for multi-area specs was unordered-set iteration before and
// is first-touch order now; it was never specified.)
struct TupleBuildPlan {
    bool ok = false;
    std::string error;            // if !ok, same text the per-row path emits
    TupleBuildOptions opt;
    struct Item {
        int slot = -1;
        int field1 = 0;           // 1-based; 0 => unresolved (non-strict path)
        std::string canonical;    // fallback lookup name when field1 == 0
    };
    std::vector<Item> items;
    TupleRow prototype;           // columns typed + labeled, kinds Present, values EMPTY
    struct FragmentSeed { int slot; std::string note; };
    std::vector<FragmentSeed> fragment_seeds;
};

TupleBuildPlan compile_tuple_plan(const std::string& spec, const TupleBuildOptions& opt);
TupleBuildResult build_tuple_from_plan(const TupleBuildPlan& plan);

// PERF-2 (AIF-168): build a plan's row from an EXPLICIT area instead of the
// global work-area slots. This is the R21 worker entry point: a parallel
// scan worker owns a private DbArea (own file handle, own cursor) and must
// never touch workareas state, so slot resolution is bypassed and every item
// reads from `area`. Only valid for single-source plans (every item the same
// slot); the caller positions the record, exactly as with the other builders.
// Overlay and memo resolution are NOT applied (the parallel scan declines
// memo-bearing plans and runs with overlay off); values are the raw
// rtrim(get(field1)) bytes, identical to the serial scan's opts.
TupleBuildResult build_tuple_for_area(const TupleBuildPlan& plan, xbase::DbArea& area);

// PERF-4 (AIF-168, 2026-09-22): in-place refill -- build ONCE, refill per row.
//
// Why: even with the compiled plan and the thinned decode, build_tuple_from_plan
// constructs a FRESH TupleRow per row -- a deep copy of the full prototype
// columns vector, three vector allocations, and a rebuilt fragment -- before
// the predicate reads one byte. Measured on the host (PIN-PERF1C-002 /
// PIN-PERF3-001): a numeric simple-WHERE that allocates nothing in its
// EVALUATION still pays ~10-12 us/row over bare COUNT, which is this
// construction; under workers those allocations contend on the heap lock,
// the surviving 8-worker cap after PERF-3 removed the unwinder lock.
//
// Contract: `row` MUST be the row produced by the matching build_* call with
// the SAME plan (columns, cell_kinds and fragment count are laid down then
// and not touched here). The refill rewrites ONLY what the record changes:
// every value cell (cleared, then decoded for plan-needed items -- a thinned
// or unresolved item stays empty exactly as a fresh build leaves it) and
// each fragment's recno + deleted flag. Overlay, memo resolution and
// refresh_relations follow plan.opt exactly as the fresh builders do; the
// _for_area variant applies none of them, mirroring build_tuple_for_area.
// Positioning stays the caller's job. A row refilled this way is
// byte-identical to a freshly built one for the same record.
void refill_tuple_from_plan(const TupleBuildPlan& plan, TupleRow& row);
void refill_tuple_for_area(const TupleBuildPlan& plan, xbase::DbArea& area, TupleRow& row);

} // namespace dottalk
