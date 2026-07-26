// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// include/cli/cmd_skip.hpp
#pragma once
#include <sstream>
namespace xbase { class DbArea; }
void cmd_SKIP(xbase::DbArea& A, std::istringstream& in);



