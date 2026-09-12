// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "shell_buffer_utils.hpp"

#include "scan_state.hpp"
#include "loop_state.hpp"
#include "cli/command_registry.hpp"

// WHILE and UNTIL each use their own private buffer/state, in cmd_while.cpp
// and cmd_until.cpp. Neither rides the shared loopblock buffer.
extern "C" bool while_is_active();
extern "C" bool until_is_active();

namespace dottalk {

bool handle_buffers_if_active(xbase::XBaseEngine& eng,
                              const std::string& U,
                              const std::string& line_for_scan,
                              const std::string& line_for_loop)
{
    using namespace dli;

    xbase::DbArea& curCap = eng.area(eng.currentArea());

    // SCAN has its own buffer command.
    if (scanblock::state().active && !is_match(U, "ENDSCAN", "END SCAN")) {
        std::istringstream cap(line_for_scan);
        registry().run(curCap, "SCAN_BUFFER", cap);
        return true;
    }

    // WHILE uses its own private state/body buffer in cmd_while.cpp.
    if (while_is_active() &&
        !is_match(U, "ENDWHILE", "END WHILE")) {
        std::istringstream cap(line_for_loop);
        registry().run(curCap, "WHILE_BUFFER", cap);
        return true;
    }

    // UNTIL, like WHILE, has its own private state and its own buffer command.
    //
    // THIS BRANCH WAS MISSING AND THE COMMENT BELOW IS WHY. It used to read
    // "LOOP / UNTIL continue to use the shared loopblock buffer", which is not
    // true -- cmd_until.cpp:81 declares untilstate, :92 exposes
    // until_is_active() with the note "Expose capture flag so shell can route
    // lines into UNTIL_BUFFER", and :210 implements cmd_UNTIL_BUFFER. The
    // absent branch followed from believing the comment instead of the file it
    // described.
    //
    // MEASURED 2026-09-01 by loop_while_until_buffer_probe.dts, which caught it
    // on its first run: ENDLOOP reported "2 buffered line(s)" and ENDWHILE
    // "over 1 line(s)" while ENDUNTIL reported "over 0 line(s)" -- the body had
    // leaked and executed once, immediately, against the parked record.
    if (until_is_active() &&
        !is_match(U, "ENDUNTIL", "END UNTIL")) {
        std::istringstream cap(line_for_loop);
        registry().run(curCap, "UNTIL_BUFFER", cap);
        return true;
    }

    // LOOP uses the shared loopblock buffer.
    if (loopblock::state().active &&
        !is_match(U, "ENDLOOP", "END LOOP") &&
        !is_match(U, "ENDWHILE", "END WHILE") &&
        !is_match(U, "ENDUNTIL", "END UNTIL")) {
        std::istringstream cap(line_for_loop);
        registry().run(curCap, "LOOP_BUFFER", cap);
        return true;
    }

    return false;
}

} // namespace dottalk