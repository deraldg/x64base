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

namespace dottalk::doc {

struct CommandDoc {
    std::string name;
    std::string summary;
    std::vector<std::string> syntax;
    std::vector<std::string> samples;
    std::vector<std::string> notes;
    std::vector<std::string> warnings;
};

} // namespace dottalk::doc
