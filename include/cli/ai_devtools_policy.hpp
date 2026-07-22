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

// True if the AI-friendly runtime dev-tools may be used by the current acting member.
//
// As of 2c-4 this consults the real identity resolver (src/cli/ai_devtools_policy.cpp):
//   - the owner (acting member is owner-class) is always permitted;
//   - a non-owner with a live authorization for the dev-tools capability is permitted;
//   - otherwise it stays DORMANT (permits) unless DOTTALK_DEVTOOLS_REQUIRE_PERMISSION is
//     set, in which case it declines and points the caller at USER REQUEST / APPROVE.
// The env grant DOTTALK_DEVTOOLS_GRANT is still honored as a no-rebuild override.
bool devtools_permitted(std::string* why = nullptr);

} // namespace dottalk::devtools
