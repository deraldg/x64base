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
