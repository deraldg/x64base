// @dottalk.usage v1
// owner: DOT|STRUCT_BASIC_IMPL
// command: STRUCT
// category: structure-helper
// status: implementation-shim
// noargs: n/a
// effect: none
// mutates: none
// usage-access: owned-by STRUCT
// summary:
//   Minimal translation unit reserved for future STRUCT helper code.
//
// usage:
//   This file intentionally does not export cmd_STRUCT().
//   STRUCT command behavior and usage are owned by the actual STRUCT command implementation.
//
// notes:
//   Keeping this file minimal avoids duplicate cmd_STRUCT definitions.
//   Future shared STRUCT helpers may live here without adding command dispatch.
//
// risk:
//   mutates_table_data: no
//

// src/cli/cmd_struct_basic.cpp
// Intentionally left minimal to avoid duplicate cmd_STRUCT() definition.
// Any future helpers for STRUCT can live here without exporting cmd_STRUCT().

#include "xbase.hpp"



