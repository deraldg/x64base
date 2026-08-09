// @dottalk.file v1
// subsystem: tv
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

// ---- TVision uses ----
#define Uses_TRect
#define Uses_TStatusLine

#if DOTTALK_TV_AVAILABLE
#include <tvision/tv.h>
#endif

namespace foxtalk {

TStatusLine* buildStatusLine(TRect bounds);

} // namespace foxtalk