#pragma once
// user_scope_paths.hpp

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

#include "common/path_state.hpp"

namespace dottalk::userpaths {

namespace fs = std::filesystem;

inline std::string trim_copy(std::string s)
{
    auto is_space = [](unsigned char ch) { return std::isspace(ch) != 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(),
        [&](unsigned char c) { return !is_space(c); }));
    s.erase(std::find_if(s.rbegin(), s.rend(),
        [&](unsigned char c) { return !is_space(c); }).base(), s.end());
    return s;
}

inline std::string current_user_name()
{
    // Replace later with real authenticated user/profile selection.
    return "default";
}

inline fs::path app_root()
{
    return dottalk::paths::state().data_root.parent_path();
}

inline fs::path user_root()
{
    return app_root() / "user";
}

inline fs::path user_profile_root(const std::string& profile_name)
{
    const std::string name = trim_copy(profile_name).empty() ? "default" : trim_copy(profile_name);
    return user_root() / name;
}

inline fs::path current_user_root()
{
    return user_profile_root(current_user_name());
}

inline fs::path public_root()
{
    return user_profile_root("public");
}

inline fs::path default_root()
{
    return user_profile_root("default");
}

inline fs::path user_workspaces_root(const std::string& profile_name)
{
    return user_profile_root(profile_name) / "workspaces";
}

inline fs::path current_user_workspaces_root()
{
    return current_user_root() / "workspaces";
}

inline fs::path public_workspaces_root()
{
    return public_root() / "workspaces";
}

inline fs::path default_workspaces_root()
{
    return default_root() / "workspaces";
}

inline fs::path user_scripts_root(const std::string& profile_name)
{
    return user_profile_root(profile_name) / "scripts";
}

inline fs::path current_user_scripts_root()
{
    return current_user_root() / "scripts";
}

inline fs::path public_scripts_root()
{
    return public_root() / "scripts";
}

inline fs::path default_scripts_root()
{
    return default_root() / "scripts";
}

inline std::vector<fs::path> workspace_search_roots()
{
    return {
        current_user_workspaces_root(),
        public_workspaces_root(),
        default_workspaces_root(),
        dottalk::paths::get_slot(dottalk::paths::Slot::WORKSPACES)
    };
}

inline std::vector<fs::path> script_search_roots()
{
    return {
        current_user_scripts_root(),
        public_scripts_root(),
        default_scripts_root(),
        dottalk::paths::get_slot(dottalk::paths::Slot::SCRIPTS)
    };
}

inline bool file_exists(const fs::path& p)
{
    std::error_code ec;
    return fs::exists(p, ec) && !ec && fs::is_regular_file(p, ec) && !ec;
}

inline fs::path resolve_in_roots(const std::string& target_in,
                                 const std::vector<fs::path>& roots,
                                 const std::string& default_ext)
{
    std::string target = trim_copy(target_in);
    fs::path p(target);

    if (!default_ext.empty() && !p.has_extension())
        p.replace_extension(default_ext);

    if (p.is_absolute() && file_exists(p))
        return fs::absolute(p);

    if (!target.empty()) {
        std::error_code ec;
        if (file_exists(p))
            return fs::absolute(p);

        if (target.find('/') != std::string::npos || target.find('\\') != std::string::npos) {
            const fs::path data_relative = dottalk::paths::state().data_root / p;
            if (file_exists(data_relative))
                return fs::absolute(data_relative);
        }
    }

    for (const auto& root : roots) {
        const fs::path candidate = root / p;
        if (file_exists(candidate))
            return fs::absolute(candidate);
    }

    return {};
}

inline fs::path resolve_workspace_file(const std::string& target_in,
                                       const std::string& ext)
{
    return resolve_in_roots(target_in, workspace_search_roots(), ext);
}

inline fs::path resolve_script_file(const std::string& target_in,
                                    const std::string& ext = ".dot")
{
    return resolve_in_roots(target_in, script_search_roots(), ext);
}

} // namespace dottalk::userpaths