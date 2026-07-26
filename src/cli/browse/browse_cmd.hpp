// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
// Public entrypoint for the refactored BROWSE command.
//
// Keep this signature identical to the old command so callers don't change.
#include <sstream>
namespace xbase { class DbArea; }

namespace dottalk::browse {
void cmd_BROWSE(::xbase::DbArea& area, std::istringstream& in);
} // namespace dottalk::browse
