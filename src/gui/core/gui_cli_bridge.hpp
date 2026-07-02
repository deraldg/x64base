#pragma once

#include <cstdint>
#include <filesystem>
#include <string>

namespace dottalk::gui {

struct RuntimeCliRequest {
    std::string command;
    std::filesystem::path active_table_path;
    std::uint64_t active_record_number = 0;
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
