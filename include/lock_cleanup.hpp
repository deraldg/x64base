// @dottalk.file v1
// subsystem: include
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <filesystem>
#include <string>

namespace dottalk::locks {

void cleanup_stale_locks(const std::filesystem::path& dbf_root);
void cleanup_owned_locks(const std::filesystem::path& dbf_root);

}