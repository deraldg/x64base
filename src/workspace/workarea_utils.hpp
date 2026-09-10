// @dottalk.file v1
// subsystem: workspace
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <cstddef>
#include <string>

namespace workareas {

// DECLARED HERE, DEFINED IN src/cli/workareas.hpp (inline). The definitions
// moved 2026 and this file kept the documentation -- see workarea_utils.cpp,
// which is now a tombstone recording the move. THE FOUR EXAMPLES BELOW ARE THE
// CONTRACT AND THE IMPLEMENTATION DID NOT MEET THEM until 2026-09-11: it
// printed `{front..back}`, a range over a set, so {0,3} rendered `{0..3}`.
// Repaired against these lines. Keep the spec and the code in sight of each
// other, or move both.

// Returns compressed occupied-slot description like:
//   {}
//   {5}
//   {0..16}
//   {0..19,50..54}
std::string occupied_desc();

// Returns count of open slots.
std::size_t open_count();

} // namespace workareas
