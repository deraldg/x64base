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

namespace dottalk::foxstd {

std::string render_doc(const std::string& command);
std::string render_topic_list();

} // namespace dottalk::foxstd
