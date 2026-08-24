// @dottalk.file v1
// subsystem: xbase
// layer: engine
// owns:
// project: project.x64base.runtime
// lane: application-ui-dsl
// owner: member.derald
// status: supported

// src/xbase/area_alloc.cpp -- see include/xbase/area_alloc.hpp for WHY this
// lives in xbase rather than in cli where it was born. The bodies are the ones
// lifted from cmd_use.cpp on 2026-08-23 (slot lane step 1), unchanged: old and
// new were extracted and diffed, and the only difference was a comment rewrap.

#include "xbase/area_alloc.hpp"

namespace xbase {

bool area_is_open_safe(XBaseEngine* eng, int slot)
{
    if (!eng || slot < 0 || slot >= MAX_AREA) return true;  // unknown is taken
    try { return eng->area(slot).isOpen(); } catch (...) { return true; }
}

int find_free_area_for_workspace(XBaseEngine* eng,
                                 workspace::WorkspaceTable& table,
                                 std::uint64_t handle,
                                 bool& broke_contiguity)
{
    broke_contiguity = false;
    if (!eng) return -1;

    const auto mem = table.members(handle);

    int highest = -1;
    for (const auto slot : mem) {
        if (slot > highest) highest = static_cast<int>(slot);
    }

    // Contiguous growth: the slot immediately after my highest member.
    if (highest >= 0 && highest + 1 < MAX_AREA) {
        if (!area_is_open_safe(eng, highest + 1)) return highest + 1;
    }

    // Fallback. Reached when my block is boxed in, or when this workspace holds
    // nothing yet and is therefore starting one.
    for (int i = 0; i < MAX_AREA; ++i) {
        if (!area_is_open_safe(eng, i)) {
            broke_contiguity = (highest >= 0);
            return i;
        }
    }
    return -1;
}

} // namespace xbase
