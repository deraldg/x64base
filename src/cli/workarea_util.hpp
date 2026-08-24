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
#include "xbase/workspace_membership.hpp"

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
int slot_of_area(const xbase::DbArea* area);

// ---- IN FREE: the free-slot policy -----------------------------------------
//
// Lifted OUT of cmd_use.cpp (AIF-078 slot lane, step 1) with no behaviour
// change and its CLI call site unchanged. It moved because a SECOND consumer is
// coming: session-owned areas take real engine slots, and the Workbench must
// reuse this policy rather than re-derive it. Two free-slot policies for one
// array is R5's defect exactly, and the last one cost a ten-site sweep
// (AIF-120 I1.1).
//
// It sits beside slot_of_area() because both answer questions about POSITIONS
// IN THE ENGINE ARRAY, which is what this unit is for.

// Is engine slot `slot` occupied? UNKNOWN COUNTS AS TAKEN -- a null engine, an
// out-of-range index, or a throwing area() all answer true, so an allocator
// built on this can never hand out a slot it failed to inspect. That bias is
// the whole point of the name: it is not "is open", it is "is open, safely".
bool area_is_open_safe(xbase::XBaseEngine* eng, int slot);

// IN FREE -- an unoccupied area, chosen for the workspace `handle` names.
//
// NAMED FREE AND NOT NEXT (owner ruling 2026-08-22): NEXT implies forward
// adjacency and this may return a slot BEHIND the cursor. A name that promises
// an order the code does not keep is worse than no name.
//
// WORKSPACE-SCOPED, AND THAT IS THE POINT (owner ruling 2026-08-22, "scoped").
// The first cut swept 0..MAX_AREA globally, which with one workspace open is
// indistinguishable from correct and stops being so the moment there are two:
// a global sweep hands out the lowest free ENGINE slot, and that slot can sit
// INSIDE ANOTHER WORKSPACE'S RUN. The owner's design rule for this lane is
// that a workspace's areas stay contiguous -- "keep the areas contiguous",
// fractal to the same rule for tables under one root -- so an allocator that
// can drop an area into the middle of a neighbour's block is a contiguity
// violation armed and waiting.
//
// So: GROW MY OWN BLOCK FIRST. If this workspace already holds areas, the slot
// after its highest member keeps the run unbroken. Only when that is taken do
// we fall back to the lowest free slot anywhere -- and we SAY SO, because a
// silently broken invariant is the shape this whole lane exists to remove.
// `broke_contiguity` carries that fact back to the caller rather than printing
// from down here, so the message lands with the rest of the caller's output.
//
// THE ENGINE AND THE TABLE ARE PARAMETERS, not things this function reaches for.
// It used to call shell_engine() and the process-global membership table, which
// is exactly what made it unreachable from a second process-local runtime and
// untestable without a live shell. Returns -1 when nothing is free.
int find_free_area_for_workspace(xbase::XBaseEngine* eng,
                                 xbase::workspace::WorkspaceTable& table,
                                 std::uint64_t handle,
                                 bool& broke_contiguity);

// The shell's spelling: the shell engine, the default membership table, the
// current handle. This is the signature cmd_use.cpp has always called, kept so
// the lift moved no call site.
int find_free_area_for_current_workspace(bool& broke_contiguity);

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
