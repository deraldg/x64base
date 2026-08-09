// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// include/cli/cmd_calc.hpp
#pragma once
#include <sstream>

namespace xbase { class DbArea; }

// Canonical CALC command signature used across the CLI.
void cmd_CALC(xbase::DbArea& area, std::istringstream& args);



