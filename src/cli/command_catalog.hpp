// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include "command_doc.hpp"
#include <string>

namespace dottalk::doc {

const CommandDoc* get(const std::string& command);

} // namespace dottalk::doc
