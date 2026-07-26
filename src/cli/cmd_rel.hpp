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

// Wrapper for the REL family (subcommand dispatcher).
void cmd_REL(xbase::DbArea& area, std::istringstream& in);
