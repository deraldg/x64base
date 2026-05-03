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
