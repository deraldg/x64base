// src/cli/cmd_dbarea.hpp
#pragma once

#include <sstream>

namespace xbase { class DbArea; }

// DBAREA
//  - DBAREA                 (current slot read-only report)
//  - DBAREA USAGE           (usage/help access path; dispatcher support may be external)
// Notes:
//  - DBAREA is the canonical single-area report.
//  - DBAREAS owns optional slot/all/relation report forms:
//      DBAREAS <n>
//      DBAREAS ALL
//      DBAREAS REL
void cmd_DBAREA(xbase::DbArea& A, std::istringstream& S);
