// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <string>
#include <vector>
#include <sstream>

namespace dottalk::browse::util {

std::string up(std::string s);
bool ieq(const std::string& a, const std::string& b);
bool parse_int(const std::string& s, int& out);
std::vector<std::string> tokenize(std::istringstream& in);
std::string extract_for_expr(const std::vector<std::string>& t);
std::string extract_start_key(const std::vector<std::string>& t);

} // namespace dottalk::browse::util
