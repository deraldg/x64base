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

// Render BETA checklist or detail.
//  - term empty => full checklist
//  - term like "BETA-3.1" => details for that item
void show_beta(const std::string& term_upper_or_raw);

} // namespace dottalk::help
