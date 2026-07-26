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
#include "xbase.hpp"

namespace status {
    // Compact single-line order summary used by STATUS header
    std::string format_active_order(const xbase::DbArea& A);
}



