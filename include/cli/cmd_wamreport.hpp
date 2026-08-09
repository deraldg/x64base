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

// WAMREPORT
// Dev-only bridge verification report for WorkAreaManager <-> XBaseEngine.
// Usage:
//   WAMREPORT
void cmd_WAMREPORT(xbase::DbArea& A, std::istringstream& S);
