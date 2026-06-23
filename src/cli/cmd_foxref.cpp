// @dottalk.usage v1
// owner: DOT|FOXREF_IMPL
// command: FOXREF
// category: reference-helper
// status: implementation-shim
// noargs: n/a
// effect: none
// mutates: none
// usage-access: owned-by FOXREF/HELP surface
// summary:
//   Empty translation-unit shim for FOXREF inline implementation.
//
// usage:
//   This file does not export a command handler.
//   FOXREF command behavior and usage are owned by the actual FOXREF/help surface.
//
// notes:
//   This file exists to keep the FOXREF implementation layout/build graph stable.
//   Do not add command dispatch behavior here unless the FOXREF architecture changes.
//
// risk:
//   mutates_table_data: no
//

// src/cli/foxref.cpp
#include "foxref.hpp"
// Intentionally empty ? all implementations are inline in foxref.hpp.



