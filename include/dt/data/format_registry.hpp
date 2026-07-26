// @dottalk.file v1
// subsystem: dt
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <vector>

#include "dt/data/format_kind.hpp"

namespace dt::data {

std::vector<FormatInfo> supported_formats();

} // namespace dt::data