// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// @dottalk.usage.voluntary v1
// NOT UNDER CONTRACT -- voluntary description, offered not promised.
// Nothing verifies this block and nothing may fail because of it.
// The binding identity for POLLING is the @dottalk.subusage contract on the
// SET POLLING ladder arm in src/cli/cmd_set.cpp; this file is a behavior-neutral
// placeholder and does not register a top-level POLLING command.
// owner: DOT|POLLING_IMPL
// documents: SET POLLING
// category: integration-stub
// status: placeholder-shim
// noargs: n/a
// effect: none
// mutates: none
// usage-access: not-registered-here
// summary:
//   Behavior-neutral placeholder TU. The live POLLING surface is SET POLLING,
//   routed through cmd_set.cpp's ladder and contracted there via @dottalk.subusage.
//
// notes:
//   Contract marker documents that this file was inspected and intentionally left behavior-neutral.
//
// risk:
//   mutates_table_data: no
//

#include "cmd_polling.hpp"
