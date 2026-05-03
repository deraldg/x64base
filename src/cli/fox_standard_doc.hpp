#pragma once

#include <string>
#include <vector>

namespace dottalk::foxstd {

struct FoxStandardDoc {
    std::string command;
    std::string summary;
    std::vector<std::string> syntax;
    std::vector<std::string> examples;
    std::vector<std::string> notes;
    std::vector<std::string> aliases;
    std::vector<std::string> versions;
};

} // namespace dottalk::foxstd
