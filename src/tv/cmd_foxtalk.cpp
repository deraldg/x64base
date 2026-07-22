// @dottalk.usage v1
// owner: UI|ARCTICTALK
// command: ARCTICTALK
// aliases: FOXTALK
// category: turbo-vision-ui
// status: supported-conditional
// noargs: interactive-launch
// effect: interactive
// mutates: ui-and-cursor-state
// usage-access: HELP ARCTICTALK; HELP FOXTALK
// summary:
//   Launch the ArcticTalk Turbo Vision shell when TV support is available.
// usage:
//   ARCTICTALK
//   FOXTALK
// notes:
//   FOXTALK is the legacy alias. Direct invocation launches the UI; there is no command-local usage branch.
// related:
//   TVISION, FOXPRO
//
#include <iostream>
#include <sstream>

#include "cli/shell_exit_request.hpp"
#include "tv/foxtalk_app.hpp"
#include "xbase.hpp"

void cmd_FOXTALK(xbase::DbArea&, std::istringstream&)
{
#if defined(DOTTALK_WITH_TV) || defined(DOTTALK_TV_AVAILABLE)
    foxtalk::TFoxtalkApp app;
    std::cout << "Launching ArcticTalk UI...\n";
    app.run();
    xbase::clear_shell_exit_request();
#else
    std::cout << "TVISION is not available in this build.\n";
#endif
}
