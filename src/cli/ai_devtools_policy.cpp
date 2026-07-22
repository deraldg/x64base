// src/cli/ai_devtools_policy.cpp
// AI-friendly dev-tools permission gate — now identity-aware (AIF-045 2c-4).
//
// Bridges the dormant dev-tools gate to the real permission resolver: the current
// acting member must be the owner, or hold a live authorization for the dev-tools
// capability (mapped to source.mutate), otherwise the gate declines when enforcement
// is requested. Owner-default acting member keeps existing behavior unchanged.

#include "cli/ai_devtools_policy.hpp"
#include "identity/identity_admin.hpp"

#include <string>

namespace dottalk::devtools {

// The catalog permission that represents "may use AI-friendly runtime dev-tools".
// Defining temp commands/functions is a source-mutation-class capability.
static constexpr const char* kDevtoolsPermission = "source.mutate";

bool devtools_permitted(std::string* why) {
    using namespace dottalk::identity;
    const std::string who = acting_member_key();

    // Owner-class is exempt (doctrine: everyone asks for limited permission except the owner).
    if (is_owner_member(who)) return true;

    // A live authorization for the dev-tools capability unlocks it.
    if (agent_permitted(kDevtoolsPermission).allowed()) return true;

    // No identity grant: stay dormant unless the owner has activated enforcement.
    if (!env_flag_set("DOTTALK_DEVTOOLS_REQUIRE_PERMISSION")) return true;

    // Legacy no-rebuild override still honored.
    if (env_flag_set("DOTTALK_DEVTOOLS_GRANT")) return true;

    if (why) {
        *why = "AI-friendly dev-tools require limited permission (acting as " + who +
               "). Ask the owner: USER REQUEST " + kDevtoolsPermission + " FOR " + who +
               " ; then owner USER APPROVE <id>. (see AI_DEV_TOOLS_SECURITY_DOCTRINE_V1)";
    }
    return false;
}

} // namespace dottalk::devtools
