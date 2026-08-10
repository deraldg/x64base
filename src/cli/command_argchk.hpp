// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_cmdargchk.hpp
#pragma once
#include <sstream>
namespace xbase { class DbArea; }
void cmd_CMDARGCHK(xbase::DbArea&, std::istringstream&);



