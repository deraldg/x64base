// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <sstream>
#include <string>

namespace xbase { class DbArea; }

// Unified HELP entrypoint (router).
// Registers as the handler for "HELP".
void cmd_HELP(xbase::DbArea& area, std::istringstream& args);

namespace dottalk::help_grouped {

// Show the grouped function index used by HELP FUNCTIONS.
void show_function_index_grouped();

// Show a specific grouped function category such as NUMERIC, DATE, STRING.
// Returns true if the category token was recognized and displayed.
bool try_show_function_category(const std::string& token);

} // namespace dottalk::help_grouped
