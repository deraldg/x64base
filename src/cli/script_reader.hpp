#pragma once

#include <istream>
#include <string>

// Shared logical-command reader for REPL/script use.
// Handles:
//   - trailing # comments outside quotes
//   - line continuation with trailing ';' outside quotes
//   - trimming trailing CR on Windows
bool read_script_command(std::istream& in, std::string& out);

// Overload that also reports how many raw input lines were consumed to form this
// logical command (1 unless ';' line-continuation joined several), so callers can
// keep accurate physical line numbers for tracing. Kept as a separate overload
// (not a defaulted param) so the 2-arg symbol above stays ABI-stable.
bool read_script_command(std::istream& in, std::string& out, int& physical_lines);