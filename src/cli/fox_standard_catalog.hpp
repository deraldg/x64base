// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include "fox_standard_doc.hpp"

#include <string>
#include <vector>

namespace dottalk::foxstd {

const FoxStandardDoc* get(const std::string& command);
std::vector<std::string> list_topics();

} // namespace dottalk::foxstd
