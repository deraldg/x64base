// @dottalk.file v1
// subsystem: gui
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <cstdint>
#include <filesystem>
#include <string>

namespace dottalk::gui {

// AIF-120. EVERY member carries a default member initializer, including the
// ones whose default is simply empty. Three of these did not, and the three
// that did not were exactly the three gcc warned about at every call site
// (-Wmissing-field-initializers) -- because a member with an NSDMI is not
// "missing" when an aggregate initializer stops short of it, and a member
// without one is.
//
// The warning was the small cost. The real one is that this struct has grown
// members over time and is aggregate-initialized by callers. When AreaInfo
// gained a member in the middle, a positional init slid a bool onto a
// std::string and only failed loudly because bool will not convert. Here
// std::string converts to std::filesystem::path, so the same mistake would be
// silent. Uniform NSDMIs plus designated initializers at the call sites mean a
// caller names what it sets and inherits the rest by declaration, not position.
struct RuntimeCliRequest {
    std::string command {};
    std::filesystem::path active_table_path {};
    std::uint64_t active_record_number = 0;
    std::filesystem::path active_index_container {};
    std::string active_index_tag {};
    bool active_index_ascending = true;
};

struct RuntimeCliResult {
    bool attempted = false;
    bool ok = false;
    int exit_code = -1;
    std::filesystem::path executable;
    std::string output;
    std::string detail;
};

RuntimeCliResult run_runtime_cli_command(const RuntimeCliRequest& request);
std::filesystem::path find_runtime_cli_executable();

} // namespace dottalk::gui
