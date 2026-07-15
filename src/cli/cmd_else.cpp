// @dottalk.usage v1
// owner: DOT|ELSE_IMPL
// command: ELSE
// category: script-flow-helper
// status: implementation-shim
// noargs: n/a
// effect: none
// mutates: none
// usage-access: owned-by IF/ELSE/ENDIF handler
// summary:
//   Empty translation-unit shim for ELSE command ownership.
//
// usage:
//   ELSE usage is owned by the IF/ELSE/ENDIF command implementation.
//   This file intentionally exports no command handler.
//
// notes:
//   This file exists only because ELSE has a cmd_*.cpp translation unit in the
//   build tree. Do not add a second ELSE implementation here.
//
// risk:
//   mutates_table_data: no
//
