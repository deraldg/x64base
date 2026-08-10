// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// Compatibility unit: ArcticTalk shell bridge lives in src/tv.
// Keep this path buildable for stale local project files without duplicating logic.
#include "../tv/foxtalk_shell_bridge.cpp"
