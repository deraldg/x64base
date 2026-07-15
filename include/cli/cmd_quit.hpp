#pragma once

#include <sstream>

namespace xbase {
class DbArea;
}

void cmd_QUIT(xbase::DbArea& area, std::istringstream& args);
void cmd_EXIT(xbase::DbArea& area, std::istringstream& args);