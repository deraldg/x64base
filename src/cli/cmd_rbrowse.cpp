// @dottalk.usage v1
// owner: DOT|RBROWSE
// command: RBROWSE
// category: browser-alias
// status: compatibility-alias
// noargs: delegate
// effect: launch-ui
// mutates: delegated-to-ERSATZ
// usage-access: delegated-to ERSATZ/RBROWSE help surface
// summary:
//   Compatibility spelling for the ERSATZ relational browser.
//
// usage:
//   RBROWSE [ersatz-browser-options]
//   RBROWSE USAGE is delegated to the ERSATZ browser command surface when supported.
//
// notes:
//   Keep behavior centralized in cmd_ERSATZ so relation browser behavior cannot
//   drift between ERSATZ and RBROWSE.
//   This file should remain a thin wrapper.
//
// risk:
//   launches_ui: delegated
//   mutates_cursor_or_ui_state: delegated
//   mutates_table_data: delegated
//
// related:
//   ERSATZ
//   RELATIONS
//   WORKSPACE
//

// src/cli/cmd_rbrowse.cpp
//
// RBROWSE is the compatibility spelling for the ERSATZ relational browser.
// Keep the behavior centralized in cmd_ERSATZ so smart root/profile inference,
// order-aware navigation, LOAD/SAVE/WLOAD, DELTA, and diagnostics cannot drift
// between two command implementations.

#include "cli/cmd_rbrowse.hpp"

#include <sstream>

#include "xbase.hpp"

void cmd_ERSATZ(xbase::DbArea& area, std::istringstream& iss);

void cmd_RBROWSE(xbase::DbArea& area, std::istringstream& iss)
{
    cmd_ERSATZ(area, iss);
}
