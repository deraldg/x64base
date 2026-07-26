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

// TABLE buffering (planned). Phase 0: command stubs + help.
// Now includes table_buffer support (auto-init on TABLE ON, COMMIT/ROLLBACK stubs)
void cmd_TABLE_BUFFER(xbase::DbArea& A, std::istringstream& in);
void cmd_COMMIT(xbase::DbArea& A, std::istringstream& in);
void cmd_ROLLBACK(xbase::DbArea& A, std::istringstream& in);