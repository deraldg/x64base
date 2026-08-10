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
namespace xbase { class DbArea; }

// Match the command registry's expected signature
void cmd_PALETTE(xbase::DbArea& area, std::istringstream& args);


