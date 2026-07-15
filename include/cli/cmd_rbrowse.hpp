// include/cli/cmd_ersatz.hpp
#pragma once

#include <sstream>

namespace xbase { class DbArea; }

// ERSATZ command (internal RBROWSE relational browser)
void cmd_ERSATZ(xbase::DbArea& area, std::istringstream& iss);