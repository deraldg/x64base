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

// THE SAME QUESTION, ASKED INSIDE ONE WORKSPACE (AIF-137, 2026-08-27).
//
// The unscoped resolver above sweeps EVERY open area, so a caller standing in
// one workspace resolves a name to another workspace's table whenever both
// hold it. Measured live: a relation refresh issued inside workspace 3 drove
// workspace 2's child, with an EMPTY relation store, needing no SET RELATION
// to occur. The relation STORE was partitioned by workspace at AIF-078 I1.2;
// the NAMES INSIDE IT WERE NOT.
//
// ABSENT HERE IS ABSENT. This returns nullptr when the name is open only in
// some OTHER workspace -- it does not fall back and it does not diagnose.
// R129 sec 6.2 rules that a name present in the current workspace resolves to
// it and a name absent here but present elsewhere is refused; on an ENGINE
// path a refusal has nobody to tell, so the correct behaviour is to find
// nothing and return. A fallback here would re-create the defect with an
// apology attached.
//
// IT STILL RECORDS, and what it records is now the residue that matters. Two
// areas can share a name INSIDE one workspace -- measured 2026-08-27: CREATE
// opened a second RPCP into DEFAULT with no rename, so `cmd_regression.cpp`'s
// claim that the ledger is "STRUCTURALLY ZERO ... until two workspaces can be
// open at once" is false and has been since before R128. A hit here is that
// case, and it is the number R112 sec 6a's measured zero is actually about.
xbase::DbArea* find_open_area_in_workspace_ci(const std::string& logical_or_name,
                                              std::uint64_t ws,
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

// ---- IN FREE: the shell's spelling ------------------------------------------
//
// THE POLICY ITSELF MOVED TO xbase (include/xbase/area_alloc.hpp, 2026-08-23).
// It was lifted here from cmd_use.cpp earlier the same day and this was the
// wrong home: dottalk_gui_core CANNOT LINK workarea_util. This object needs
// three shell symbols -- cli::cmdout::print_line, workareas::shell_engine and
// ::shell_engine -- none of which exist in the GUI process, and none of which
// the policy uses. They come from the ambiguity ledger and the array walk that
// share this translation unit. The allocator was never stuck because of what it
// does; it was stuck because of its ROOMMATES.
//
// WHAT REMAINS HERE IS THE HALF THAT IS GENUINELY SHELL: shell_engine(), the
// default membership table, the current handle. cmd_use.cpp's single call site
// did not move again.

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

// ---------------------------------------------------------------------------
// R131 -- A WORKSPACE OWNS ITS ENVIRONMENT.
//
// THIS IS THE JOINT, and it is here rather than in cmd_workspace.cpp because
// it has TWO callers in different translation units: the WORKSPACE verbs, and
// SET PATH (cmd_setpath_command.cpp). The AIF-078 precedent is exact --
// find_free_area_for_workspace was lifted out of cmd_use.cpp into this file
// the moment a second opener needed it, for the same reason: a rule with two
// callers and one home cannot drift, and a rule with two callers and two
// homes always does (R5).
//
// The DIVISION OF LABOUR, stated because it is the whole design:
//   xbase::workspace::Entry  HOLDS the three roots and cannot resolve them.
//   These three functions are the ONLY code that moves a value between that
//   stamp and the live dottalk::paths slots, in either direction.
//   Everything else -- all 102 readers of get_slot -- is untouched.

// Stamp <handle>'s roots FROM the live slots. This is the write direction:
// SET PATH and workspace creation use it. Returns false if the handle is not
// in the table.
bool workspace_roots_bind_from_slots(std::uint64_t handle);

// Stamp only if not already stamped. Q2 is INHERIT, so every workspace is
// stamped at creation -- which leaves exactly one entry this exists for:
// DEFAULT, created inside xbase before any command has run and therefore
// before anything could have told it where it lives. Called on the paths that
// could otherwise read an unstamped entry.
bool workspace_roots_ensure_stamped(std::uint64_t handle);

// Apply <handle>'s roots TO the live slots. This is the read direction, and
// the only caller is WORKSPACE SWITCH.
//
// IT ANNOUNCES EVERY SLOT IT MOVES, and that is deliberate rather than
// decorative. SWITCH acquiring the power to re-point path slots is the one
// part of R131 that can change what an EXISTING script does, and this house's
// habit for a state change is to name it (R131 sec 7 records the same
// suggestion for SET PATH). A run where a spec breaks because its slots moved
// under it should say so in its own transcript rather than leaving a reader to
// infer it from a failed open three screens later.
//
// Returns the number of slots actually changed; 0 means the workspace's
// environment already matched the session's, which is the common case and
// prints nothing.
int workspace_roots_apply_to_slots(std::uint64_t handle);

} // namespace cli
