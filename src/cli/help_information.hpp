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

namespace dottalk::help {

bool show_information_topic(const std::string& term);
void show_information_overview();

} // namespace dottalk::help
