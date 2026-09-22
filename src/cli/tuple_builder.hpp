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

} // namespace dottalk
