#pragma once
// include/cli/ai_devtools_policy.hpp
//
// AI-friendly dev-tools permission gate — SHIPPED DORMANT BY DESIGN.
// See docs/maintenance/AI_DEV_TOOLS_SECURITY_DOCTRINE_V1.md.
//
// Protocol (governance): any agent — AI or human — must obtain *limited*, scoped
// permission before using the AI-friendly runtime dev-tools (DEFCMD / UNDEFCMD /
// DEFFN / UNDEFFN, and future DEF-family surfaces). The project owner is exempt.
//
// This function is the single technical chokepoint for that protocol, but it is
// DORMANT: it permits by default, so current behavior is unchanged and nothing is
// blocked today. The owner may activate enforcement WITHOUT a rebuild:
//
//   - Activate:  set  DOTTALK_DEVTOOLS_REQUIRE_PERMISSION=1
//   - Grant:     set  DOTTALK_DEVTOOLS_GRANT=1   (a scoped, out-of-band grant)
//
// With enforcement active and no grant present, the dev-tools decline and point the
// caller at the doctrine. The gate mirrors the existing host-shell control
// (DOTTALK_ALLOW_HOST_COMMANDS) in spirit: capability announced, off-by-request.

#include <cstdlib>
#include <string>

namespace dottalk::devtools {

inline bool env_flag_set(const char* name) {
    const char* v = std::getenv(name);
    return v && *v && std::string(v) != "0";
}

// True if the AI-friendly runtime dev-tools may be used. Dormant default: true.
inline bool devtools_permitted(std::string* why = nullptr) {
    // Dormant: enforcement not requested -> permitted (shipped default).
    if (!env_flag_set("DOTTALK_DEVTOOLS_REQUIRE_PERMISSION")) {
        return true;
    }
    // Enforcement active: a limited, scoped grant must be present.
    if (env_flag_set("DOTTALK_DEVTOOLS_GRANT")) {
        return true;
    }
    if (why) {
        *why = "AI-friendly dev-tools require limited permission. Ask the owner for a "
               "scoped grant (see AI_DEV_TOOLS_SECURITY_DOCTRINE_V1).";
    }
    return false;
}

} // namespace dottalk::devtools
