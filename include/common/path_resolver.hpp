// @dottalk.file v1
// subsystem: common
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <filesystem>
#include <string>

namespace dottalk::paths {

namespace fs = std::filesystem;

// ---- declarations only ----

fs::path resolve_in_slot(const fs::path& slot_root, const std::string& token);
fs::path ensure_ext(fs::path p, const std::string& ext_with_dot);

fs::path resolve_dbf(const std::string& token);
fs::path resolve_index(const std::string& token);
fs::path resolve_lmdb_root();
fs::path resolve_lmdb_env_for_cdx(const fs::path& public_cdx_path);
fs::path resolve_workspace(const std::string& token);

// AIF-145 R-a step 3. The two remaining private resolvers ERSATZ owned.
// Both search the SAME roots as resolve_workspace / resolve_script; they
// differ only in the extension they default to, which is why they are
// named for the file kind and not for a search strategy.
fs::path resolve_ersatz_profile(const std::string& token);  // .erz, workspace roots
fs::path resolve_ersatz_script(const std::string& token);   // .dot, script roots
fs::path resolve_test(const std::string& token);
fs::path resolve_schema(const std::string& token);
fs::path resolve_script(const std::string& token);
fs::path resolve_project(const std::string& token);

} // namespace dottalk::paths