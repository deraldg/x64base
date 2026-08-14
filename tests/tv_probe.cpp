// @dottalk.file v1
// subsystem: tests
// layer: smoke
// owns:
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: experimental

// tests/tv_probe.cpp
#include <tvision/tv.h>

int main() {
    TRect r(0, 0, 1, 1);
    TEvent ev{};
    (void)r; (void)ev;
    return 0;
}
