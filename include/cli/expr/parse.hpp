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
#include <vector>
#include "scan_options.hpp"

struct ParseResult {
    bool ok{false};
    ScanOptions opt{};
    std::string err;
};

std::vector<std::string> cli_tokenize(const std::string& s);
ParseResult parse_scan_options(std::istringstream& S, const std::string& verb);



