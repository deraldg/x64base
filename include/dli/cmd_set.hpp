// @dottalk.file v1
// subsystem: dli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
// dli/cmd_set.hpp ? Minimal SET router that recognizes "VIEW" and forwards to dli::cmd_SET_VIEW.
// No 'cli' symbols; namespace dli only.
#include <sstream>

namespace xbase { class DbArea; }

namespace dli {
void cmd_SET(xbase::DbArea& db, std::istringstream& args);
} // namespace dli



