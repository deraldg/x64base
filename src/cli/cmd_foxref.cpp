// @dottalk.file v1
// subsystem: cli
// layer: reference
// owns: foxref reference catalog (include/foxref.hpp) anchor TU
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: supported

// @dottalk.usage.voluntary v1
// NOT UNDER CONTRACT -- voluntary description, offered not promised.
// Nothing verifies this block and nothing may fail because of it.
// FOXREF is NOT a command: it is the FoxPro/legacy reference-catalog MODULE
// (namespace foxref, catalog() in include/foxref.hpp), mined by CMDHELP/FOXHELP as
// part of the `registry U foxref U dotref U edref` help surface. This TU anchors
// that module and exports no command handler.
// owner: DOT|FOXREF_IMPL
// documents: foxref reference catalog (include/foxref.hpp)
// category: reference-helper
// status: implementation-shim
// noargs: n/a
// effect: none
// mutates: none
// usage-access: owned-by FOXREF/HELP surface
// summary:
//   Translation-unit shim anchoring the foxref reference-catalog module. The
//   catalog and its legacy-facing help surface live in include/foxref.hpp; this
//   file keeps the build graph stable and exports no command.
//
// notes:
//   Do not add command dispatch here. FOXREF is a reference module, not a command.
//
// risk:
//   mutates_table_data: no
//

// src/cli/foxref.cpp
#include "foxref.hpp"
// Intentionally empty ? all implementations are inline in foxref.hpp.



