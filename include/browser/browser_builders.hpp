// @dottalk.file v1
// subsystem: browser
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// include/browser/browser_builders.hpp
#pragma once

#include "xbase.hpp"
#include "browser/browser_snapshot.hpp"

namespace browser
{
    bool build_browser_snapshot(xbase::DbArea& current_area,
                                const BrowserRequest& req,
                                BrowserSnapshot& out);

    bool build_walk_snapshot(xbase::DbArea& current_area,
                             const BrowserRequest& req,
                             WalkSnapshot& out);
}
