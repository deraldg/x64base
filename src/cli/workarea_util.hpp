// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: experimental

// src/cli/workarea_util.hpp -- shared work-area lookup and cursor-guard helpers.
//
// AIF-074 P0.2 consolidation: these were duplicated verbatim across the REL
// family (cmd_relations.cpp, rel_enum_engine.cpp, set_relations.cpp). One home
// now serves REL and, later, SQLSEL FROM resolution (open relationship
// platform, ruling R11). Flip status to supported when gate G0 records
// REGRESSION ALL green over this consolidation.
//
// Nothing here mutates table data; ScopedAreaSelect/ScopedEngineArea mutate
// only the current-area selection and restore it on scope exit.

#pragma once

#include <string>
#include <vector>

#include "xbase.hpp"

namespace cli {

// Case-insensitive lookup of an OPEN work area by logicalName() or name().
// Returns nullptr when no open area matches.
xbase::DbArea* find_open_area_by_name_ci(const std::string& logical_or_name);

// Slot index of an area pointer within workareas, or -1 if not present.
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
