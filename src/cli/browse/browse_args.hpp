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
#include <sstream>
#include <vector>

namespace dottalk::browse {

struct BrowseArgs {
    bool want_raw=false;
    bool list_all=false;
    bool quiet=false;
    bool interactive=false;
    enum class StartPos { Top, Bottom } start = StartPos::Top;
    int page_size = 20;
    std::string for_expr;
    std::string start_key_literal;
};

// Parse tokens from the command stream into BrowseArgs.
BrowseArgs parse_args(std::istringstream& in);

} // namespace dottalk::browse
