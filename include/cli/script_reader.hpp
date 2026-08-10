// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <istream>
#include <string>

// Shared logical-command reader for REPL/script use.
// Handles:
//   - trailing # comments outside quotes
//   - line continuation with trailing ';' outside quotes
//   - trimming trailing CR on Windows
bool read_script_command(std::istream& in, std::string& out);