// @dottalk.file v1
// subsystem: browser
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// include/browser/browser_render_console.hpp
#pragma once

#include "browser/browser_snapshot.hpp"

namespace browser
{
    void render_browser_snapshot_console(const BrowserSnapshot& snap);
    void render_walk_snapshot_console(const WalkSnapshot& walk);
}
