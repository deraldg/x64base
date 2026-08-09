// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <string>
#include "xbase_error_codes.hpp"

namespace dottalk::help {

bool show_warning_topic(const std::string& term);
void print_warning_help(xbase::error::code ec);

} // namespace dottalk::help
