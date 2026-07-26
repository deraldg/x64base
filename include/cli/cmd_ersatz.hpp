// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// include/cli/cmd_ersatz.hpp
#pragma once

#include <sstream>

namespace xbase { class DbArea; }

// ERSATZ command
void cmd_ERSATZ(xbase::DbArea& area, std::istringstream& iss);