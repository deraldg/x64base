#pragma once
#include <iosfwd>
#include <string>
#include <vector>

namespace csv {

std::vector<std::string> split_line(const std::string& line);
bool read_record(std::istream& in, std::string& record);
std::string escape(const std::string& s);

} // namespace csv



