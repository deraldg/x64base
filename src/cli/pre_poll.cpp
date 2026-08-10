// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include <iostream>
#include "cli/output_router.hpp"
#include "pre_poll.hpp"

void pre_poll()
{
    auto& out = cli::OutputRouter::instance().out();
    out << "[POLL PRE]\n";
}
