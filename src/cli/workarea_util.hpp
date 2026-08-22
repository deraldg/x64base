// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: supported

// src/cli/workarea_util.hpp -- shared work-area lookup and cursor-guard helpers.
//
// AIF-074 P0.2 consolidation: these were duplicated verbatim across the REL
// family (cmd_relations.cpp, rel_enum_engine.cpp, set_relations.cpp). One home
// now serves REL and, later, SQLSEL FROM resolution (open relationship
// platform, ruling R11). Status flipped experimental -> supported at gate G0
// (2026-07-29): build green, REGRESSION ALL green over the consolidated paths.
//
// Nothing here mutates table data; ScopedAreaSelect/ScopedEngineArea mutate
// only the current-area selection and restore it on scope exit.

#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

#include "xbase.hpp"

namespace cli {

// Case-insensitive lookup of an OPEN work area by logical name.
//
// The implementation compares logicalName() and then name(); those are the SAME
// member (xbase.hpp:238 and :288, the latter under "Legacy compatibility"), so
// the second comparison can never match when the first did not. Said here
// rather than left implying two name spaces -- see
// docs/maintenance/AIF120_NAME_SCHEMA_RULING_V1.md sec 1.
//
// FIRST MATCH WINS -- the LOWEST engine slot. That is unchanged behaviour and
// 21 call sites depend on it. What IS new (AIF-120 I1.3a) is that the choice is
// no longer silent: when more than one open area matches, the resolution is
// RECORDED in the ambiguity ledger below and announced once. R112 sec 6a ruled
// that first-wins-plus-warning is admissible only as an INSTRUMENTED migration
// phase whose counter has to reach a measured zero -- so this records, and does
// not merely print.
//
// The optional `site` tags the caller in the ledger. Untagged calls record as
// "unattributed", which the report prints as such rather than as "no site":
// an unattributed hit is a call site nobody has labelled yet, not an absence.
//
// Returns nullptr when no open area matches.
xbase::DbArea* find_open_area_by_name_ci(const std::string& logical_or_name);
xbase::DbArea* find_open_area_by_name_ci(const std::string& logical_or_name,
                                         const char* site);

// EVERY open area whose name matches, ascending by engine slot.
//
// This is the primitive both resolvers are now built on. Singular lookup is
// `front()`; the map builder below indexes `front()` per key. Before this the
// tree builder in set_relations.cpp kept its own map and assigned
// unconditionally, which made it LAST-match-wins -- two functions answering the
// same question with different areas whenever a name repeated. The
// disagreement was invisible because neither said which one it picked.
//
// Does NOT record ambiguity: it returns the candidates, so the caller can see
// them. Recording is the singular resolver's job, where the choice is made.
std::vector<xbase::DbArea*> find_open_areas_by_name_ci(const std::string& logical_or_name);

// UPPER logical name -> the open area that find_open_area_by_name_ci() would
// return for that name. Built with the same rule, so the two AGREE BY
// CONSTRUCTION rather than by inspection.
//
// Cost is one pass over the work-area array, the same pass the singular
// resolver already makes. Callers that look up several names in a row should
// build this once instead of scanning per name -- MAX_AREA is 512 only because
// the test corpus is small.
std::unordered_map<std::string, xbase::DbArea*> build_open_area_index_ci();

// ---- R112 migration instrument ------------------------------------------
//
// The gate for turning first-wins into a hard refusal is a MEASURED ZERO here
// across the .dts corpus, not a date. Read it with WORKSPACE REGISTRY.

struct AmbiguityHit {
    std::string               name;          // the UPPER name that was ambiguous
    std::string               site;          // caller tag, or "unattributed"
    std::vector<int>          engine_slots;  // every candidate, ascending
    std::vector<std::uint64_t> ws_handles;   // owning workspace, parallel to slots
    int                       chosen_slot{-1};
    std::size_t               hits{0};       // times this (name, site) recurred
};

// Number of ambiguous RESOLUTIONS since the last reset (not distinct names).
std::size_t ambiguity_count();

// One entry per distinct (name, site); `hits` carries the recurrence.
const std::vector<AmbiguityHit>& ambiguity_ledger();

// Clears the ledger and the announce latches. Called by WORKSPACE CLOSE ALL so
// a measurement covers one run and not the whole process.
void ambiguity_reset();

// Slot index this area occupies, or -1 if the pointer is null.
//
// AIF-120 I1.1: reads DbArea::engineSlot(), stamped once at engine construction.
// It no longer scans, and it no longer returns -1 for a CLOSED area -- the slot
// is a property of the array position, not of the table open in it. Callers
// that treated -1 as "closed" were relying on a side effect of the old scan;
// ask isOpen() for that.
int slot_of_area(xbase::DbArea* area);

// RAII: select the given area's slot; restore the previous selection on exit.
// No-op (and harmless) when the area is null, unknown, or already current.
class ScopedAreaSelect {
public:
    explicit ScopedAreaSelect(xbase::DbArea* area) noexcept;
    ~ScopedAreaSelect() noexcept;
    ScopedAreaSelect(const ScopedAreaSelect&) = delete;
    ScopedAreaSelect& operator=(const ScopedAreaSelect&) = delete;

private:
    xbase::XBaseEngine* eng_{nullptr};
    int prev_{-1};
    bool active_{false};
};

// RAII: remember the current area on entry; restore it on scope exit.
class ScopedEngineArea {
public:
    ScopedEngineArea() noexcept;
    ~ScopedEngineArea() noexcept;
    ScopedEngineArea(const ScopedEngineArea&) = delete;
    ScopedEngineArea& operator=(const ScopedEngineArea&) = delete;

private:
    xbase::XBaseEngine* eng_{nullptr};
    int prev_{-1};
    bool active_{false};
};

// Split a TUPLE expression list on top-level commas, respecting double-quoted
// strings (with backslash escapes) and parenthesis nesting. Trims each term;
// empty terms are dropped.
std::vector<std::string> split_tuple_expr_csv(const std::string& s);

} // namespace cli
