// @dottalk.file v1
// subsystem: tv
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <string>

// ---- TVision uses ----
#define Uses_TWindow
#define Uses_TRect

#if DOTTALK_TV_AVAILABLE
#include <tvision/tv.h>
#endif

namespace foxtalk {

class FoxtalkLogView;

class FoxtalkOutputWindow : public TWindow {
public:
    FoxtalkOutputWindow(const TRect& bounds, const char* title, ushort number = 0);

    FoxtalkLogView* logView() const;

private:
    FoxtalkLogView* logView_{nullptr};
};

} // namespace foxtalk