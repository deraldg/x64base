// @dottalk.file v1
// subsystem: xbase
// layer: header
// owns:
// project: project.x64base.runtime
// lane: application-ui-dsl
// owner: member.derald
// status: supported

#pragma once
// @dottalk.contract
// file: include/xbase/workspace_membership.hpp
// subsystem: xbase
// role: Runtime workspace membership -- which areas belong to which workspace
// authority: canonical-header-contract
// mutation: token-authorized

// AIF-078 stage 2. The RUNTIME half of workspace identity.
//
// WHAT THIS IS NOT. The workspace CATALOG (WORKSPACES.dbf, catalog v2) is the
// persistence authority: WS_ID allocates identity, WS_NAME is the key, and a
// saved posture's AREA lines are the child list AT REST. None of that answers
// "which areas are open in which workspace RIGHT NOW", and a workspace can be
// open having never been saved. That is session state, and this is where it
// lives.
//
// WHY IT LIVES IN xbase AND NOT IN cli. DbArea::open() and DbArea::close() are
// the only two points in the tree where an area joins or leaves a workspace,
// and the engine already maintains _ws_handle at exactly those two points.
// DbArea::open() is reached from EIGHT distinct call sites in src/cli alone
// (cmd_use, cmd_workspace x3, cmd_create, cmd_copy, cmd_ddl, cmd_autodbf,
// cmd_refresh), so stamping from the CLI would need eight edits and would
// silently skip the ninth. That is the enumeration-by-convention trap
// WORKSPACE WRITEBACK already paid for: "a count is a fact about a loop until
// something declares what it SHOULD be." Registering at the choke point the
// engine already owns cannot be skipped.
//
// It is deliberately NOT a callback. include/../xbase/cursor_hook.hpp is the
// house's cautionary example: a hook whose notify() has zero call sites, whose
// callback is installed and never fires, and on whose strength the manual
// fallback was deleted (AIF-120 R117). A plain value the engine reads is not
// capable of that failure.
//
// DESIGN CONSTRAINT D3: no operation here is O(MAX_AREA). Every walk is
// bounded by the members of ONE workspace.
//
// NOT thread-safe, matching xbase::ramfs and the rest of this layer: the shell
// is single-threaded and the Workbench reaches the CLI through a child process.

#include <cstddef>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace xbase::workspace {

// The implicit, always-present workspace. Design invariant I1: an area belongs
// to exactly ONE workspace and there is NO NULL -- a bare USE outside any
// workspace opens into DEFAULT, which behaves like every other workspace.
inline constexpr std::uint64_t kDefaultHandle = 1;
inline constexpr const char*   kDefaultName   = "DEFAULT";

struct Entry {
    std::string               name;
    std::vector<std::int32_t> members;   // engine slots, ascending by local slot
};

// One instance per process. Function-local static so this header needs no
// translation unit of its own and no CMake edit.
inline std::unordered_map<std::uint64_t, Entry>& table() {
    static std::unordered_map<std::uint64_t, Entry> t{
        { kDefaultHandle, Entry{ kDefaultName, {} } }
    };
    return t;
}

inline std::uint64_t& current_handle_ref() {
    static std::uint64_t h = kDefaultHandle;
    return h;
}

// The workspace a newly opened area joins. Defaults to DEFAULT and stays there
// until something sets it, which is why stage 2 changes no observable
// behaviour: every area still resolves to handle 1, exactly as the constant it
// replaces did.
inline std::uint64_t current_handle() noexcept { return current_handle_ref(); }
inline void set_current_handle(std::uint64_t h) noexcept { current_handle_ref() = h; }

inline const Entry* find(std::uint64_t h) {
    auto it = table().find(h);
    return it == table().end() ? nullptr : &it->second;
}

inline std::string name_of(std::uint64_t h) {
    const Entry* e = find(h);
    return e ? e->name : std::string{};
}

inline std::size_t member_count(std::uint64_t h) {
    const Entry* e = find(h);
    return e ? e->members.size() : 0u;
}

inline std::vector<std::int32_t> members(std::uint64_t h) {
    const Entry* e = find(h);
    return e ? e->members : std::vector<std::int32_t>{};
}

inline std::vector<std::uint64_t> handles() {
    std::vector<std::uint64_t> out;
    out.reserve(table().size());
    for (const auto& kv : table()) out.push_back(kv.first);
    return out;
}

// Join, returning the WORKSPACE-LOCAL slot (1..n) -- decision D2. The LOWEST
// FREE local slot is reused rather than always appending: a leave would
// otherwise leave a permanent hole, and renumbering survivors is not an option
// because a local slot is an address. Bounded by the members of this workspace.
// Returns -1 if the handle is unknown; the caller keeps its previous value.
inline std::int32_t join(std::uint64_t h, std::int32_t engine_slot) {
    auto it = table().find(h);
    if (it == table().end()) return -1;
    auto& m = it->second.members;
    for (std::size_t i = 0; i < m.size(); ++i) {
        if (m[i] == engine_slot) return static_cast<std::int32_t>(i + 1);  // idempotent
    }
    for (std::size_t i = 0; i < m.size(); ++i) {
        if (m[i] < 0) { m[i] = engine_slot; return static_cast<std::int32_t>(i + 1); }
    }
    m.push_back(engine_slot);
    return static_cast<std::int32_t>(m.size());
}

// Leave. The member's local slot becomes free for the next join rather than
// shifting everything after it, because shifting would silently re-address
// live members.
inline void leave(std::uint64_t h, std::int32_t engine_slot) {
    auto it = table().find(h);
    if (it == table().end()) return;
    auto& m = it->second.members;
    for (auto& slot : m) {
        if (slot == engine_slot) { slot = -1; break; }
    }
    while (!m.empty() && m.back() < 0) m.pop_back();
}

// Create or rename. Stage 2 seeds only DEFAULT; this exists so stage 4 has
// somewhere to put the second workspace without reopening this header.
inline bool declare(std::uint64_t h, const std::string& nm) {
    if (h == 0) return false;
    table()[h].name = nm;
    return true;
}

} // namespace xbase::workspace
