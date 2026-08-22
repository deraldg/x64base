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

#include <string>
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
// FIRST MATCH WINS and no ambiguity is reported. Nothing keeps a logical name
// unique, so two open areas can carry the same one; the ruling above governs
// what should happen and is not implemented here yet.
//
// Returns nullptr when no open area matches.
xbase::DbArea* find_open_area_by_name_ci(const std::string& logical_or_name);

// Slot index this area occupies, or -1 if the pointer is null.
//
// AIF-120 I1.1: reads DbArea::wsSlot(), stamped once at engine construction.
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
