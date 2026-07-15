// File: include/csv.hpp
// Purpose: Small CSV helpers shared by import/export and script-facing data paths.
// Boundary: Keep this header dependency-light and format-focused; command syntax,
//           messaging, and table mutation policy belong in higher CLI layers.

#pragma once
#include <iosfwd>
#include <string>
#include <vector>

namespace csv {

std::vector<std::string> split_line(const std::string& line);
bool read_record(std::istream& in, std::string& record);
std::string escape(const std::string& s);

} // namespace csv



