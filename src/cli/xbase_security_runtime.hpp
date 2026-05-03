#pragma once
// xbase_security_runtime.hpp
// Canonical runtime enforcement layer for xBase_64.
// Applies security policy rules at DBF_64/FPT64 open/close boundaries,
// validates headers, enforces atomic writes, and prevents unsafe operations.

#include <filesystem>
#include <stdexcept>
#include <string>
#include <utility>

#include "xbase_security.hpp"
#include "xbase_security_policy.hpp"
#include "common/path_state.hpp"

namespace xbase {
namespace security {
namespace runtime {

using policy::config;
using policy::enforce;
using policy::enforce_atomic_writes;
using policy::enforce_header_validation;
using policy::enforce_no_elevated_writes;
using policy::enforce_no_plaintext_secrets;
using policy::enforce_no_unsafe_paths;

namespace fs = std::filesystem;

// ------------------------------------------------------------
// Path helpers
// ------------------------------------------------------------
inline std::string join_path(std::string base, const std::string& child)
{
    if (base.empty())
        return child;

    const char last = base.back();
    if (last != '\\' && last != '/')
        base.push_back('\\');

    return base + child;
}

// ------------------------------------------------------------
// App-local user/profile roots
// ------------------------------------------------------------
inline std::string app_root()
{
    const fs::path data_root = dottalk::paths::state().data_root;
    const fs::path root = data_root.parent_path();
    return root.string();
}

inline std::string app_user_root_base()
{
    return (fs::path(app_root()) / "user").string();
}

inline std::string app_user_profile_root(const std::string& profile_name)
{
    const std::string profile = profile_name.empty() ? "default" : profile_name;
    return (fs::path(app_user_root_base()) / profile).string();
}

inline std::string app_user_public_root()
{
    return app_user_profile_root("public");
}

inline std::string app_user_default_root()
{
    return app_user_profile_root("default");
}

// ------------------------------------------------------------
// OS-local user/profile roots
// ------------------------------------------------------------
inline std::string os_user_root_base()
{
    return security::user_data_dir("");
}

inline std::string os_user_profile_root(const std::string& profile_name)
{
    const std::string profile = profile_name.empty() ? "default" : profile_name;
    return join_path(os_user_root_base(), profile);
}

inline std::string os_user_public_root()
{
    return os_user_profile_root("public");
}

inline std::string os_user_default_root()
{
    return os_user_profile_root("default");
}

// ------------------------------------------------------------
// Runtime Context
// ------------------------------------------------------------
struct context
{
    config policy;
    bool is_elevated = false;

    std::string profile_name;

    std::string app_user_root;
    std::string app_public_root;
    std::string app_default_root;

    std::string os_user_root;
    std::string os_public_root;
    std::string os_default_root;

    explicit context(const config& cfg,
                     std::string active_profile = "default")
        : policy(cfg),
          is_elevated(security::is_elevated()),
          profile_name(active_profile.empty() ? "default" : std::move(active_profile)),
          app_user_root(app_user_profile_root(profile_name)),
          app_public_root(app_user_public_root()),
          app_default_root(app_user_default_root()),
          os_user_root(os_user_profile_root(profile_name)),
          os_public_root(os_user_public_root()),
          os_default_root(os_user_default_root())
    {}
};

// ------------------------------------------------------------
// DBF/FPT Header Validation Hook
// ------------------------------------------------------------
inline void validate_header(const context& ctx, bool header_ok)
{
    enforce_header_validation(ctx.policy);
    enforce(header_ok, "DBF_64/FPT64 header failed validation.");
}

// ------------------------------------------------------------
// Path Safety Hook
// ------------------------------------------------------------
inline std::string secure_path(const context& ctx, const std::string& path)
{
    (void)ctx;
    enforce_no_unsafe_paths(ctx.policy);
    return security::canonicalize(path);
}

// ------------------------------------------------------------
// Elevated Write Protection
// ------------------------------------------------------------
inline void check_write_permissions(const context& ctx)
{
    enforce_no_elevated_writes(ctx.policy, ctx.is_elevated);
}

// ------------------------------------------------------------
// Atomic Write Enforcement
// ------------------------------------------------------------
inline void require_atomic(const context& ctx)
{
    enforce_atomic_writes(ctx.policy);
}

// ------------------------------------------------------------
// Secret Handling Enforcement
// ------------------------------------------------------------
inline void require_secure_secrets(const context& ctx)
{
    enforce_no_plaintext_secrets(ctx.policy);
}

// ------------------------------------------------------------
// High-Level Open/Close Wrappers
// ------------------------------------------------------------
inline void on_open_begin(const context& ctx, const std::string& path)
{
    (void)secure_path(ctx, path);
}

inline void on_open_end(const context& ctx, bool header_ok)
{
    validate_header(ctx, header_ok);
}

inline void on_write_begin(const context& ctx)
{
    check_write_permissions(ctx);
    require_atomic(ctx);
}

inline void on_store_secret(const context& ctx)
{
    require_secure_secrets(ctx);
}

} // namespace runtime
} // namespace security
} // namespace xbase