// @dottalk.file v1
// subsystem: xexpr
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <string>
#include <vector>

#include "xexpr/value.hpp"

namespace xexpr {

struct FunctionInfo {
    std::string name;
    std::string category;
    int min_args = 0;
    int max_args = 0;
    ValueKind nominal_return = ValueKind::None;
    std::string syntax;
    std::vector<std::string> examples;
    std::vector<std::string> notes;
    std::vector<std::string> warnings;
};

const FunctionInfo* find_function(const std::string& name);
std::vector<FunctionInfo> list_functions();

} // namespace xexpr
