// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <sstream>

namespace xbase {
class DbArea;
}

void cmd_QUIT(xbase::DbArea& area, std::istringstream& args);
void cmd_EXIT(xbase::DbArea& area, std::istringstream& args);