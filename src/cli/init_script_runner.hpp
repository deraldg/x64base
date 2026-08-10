// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <filesystem>
#include <string>

namespace xbase { class DbArea; }

namespace dottalk::startup {

std::filesystem::path get_executable_dir();
void run_script_file(xbase::DbArea& current, const std::filesystem::path& file_path);

} // namespace dottalk::startup