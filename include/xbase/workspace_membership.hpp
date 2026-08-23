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
//
// TOKEN for the 2026-08-23 mutation (Entry::ws_id, ws_id_of, set_ws_id):
// AIF-078 D10, ACCEPTED by the steward in-session the same day -- "i want a
// ws_id", then "accept", then "go". See
// docs/maintenance/AIF078_D10_WORKSPACE_IDENTITY_LADDER_RULING_V1.md.

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

#include <algorithm>
#include <cctype>
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

    // AIF-078 stage 3. The owner ruling: "multiple workspaces is just a
    // workspace of workspaces of areas." A workspace therefore has ONE parent
    // (0 = a root), which is the runtime mirror of the catalog's PREV_ID/DEPTH
    // pair. It is a parent pointer and not a child vector on purpose: a child
    // list has two places to forget an edge, and this has one.
    std::uint64_t parent{0};

    // AIF-078 D10.1/D10.2 (steward, 2026-08-23: "i want a ws_id" / "accept").
    // The workspace's DURABLE identity: the ROOT of its PREV_ID chain in
    // WORKSPACES.dbf. 0 means "no durable identity yet", which is a real and
    // legal state for exactly one workspace -- DEFAULT, which exists before
    // any command runs and is allocated LAZILY so that a bare launch never
    // touches the catalog.
    //
    // R1 of the identity ladder says derivation runs DOWNWARD ONLY, so this
    // field is a STAMP and not a lookup: the allocator lives CLI-side with
    // the catalog (cmd_workspace.cpp, ensure_durable_workspace), and this
    // header never reaches up to it. A handle knows its WS_ID because it was
    // told; it cannot go and find out.
    std::uint64_t ws_id{0};
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

// SET RECURSION ON | OFF -- owner ruling 2026-08-22: "even with OFF we still
// allow multiple workspaces, just parallel." So this flag does NOT gate
// whether nested workspaces may EXIST; it gates whether an operation on a
// parent DESCENDS into its children. OFF means a close touches exactly the
// workspace you named and says so.
inline bool& recursion_enabled_ref() { static bool on = true; return on; }
inline bool  recursion_enabled() noexcept { return recursion_enabled_ref(); }
inline void  set_recursion_enabled(bool on) noexcept { recursion_enabled_ref() = on; }

// The recursion guard the owner asked for, "like we did databases in memos."
// The number is a backstop, not a policy: real nesting is single digits, and a
// walk that reaches 32 has found a cycle the structural guard missed.
//
// THE POINT OF THIS CONSTANT IS THAT SOMETHING PRINTS WHEN IT FIRES. The
// relation depth cap (set_relations.cpp) is hardcoded twice and returns
// SILENTLY at the limit, so a truncated traversal is indistinguishable from a
// complete one. Every caller of this cap in stage 3 announces.
inline constexpr int kMaxWorkspaceDepth = 32;

inline const Entry* find(std::uint64_t h) {
    auto it = table().find(h);
    return it == table().end() ? nullptr : &it->second;
}

inline std::string name_of(std::uint64_t h) {
    const Entry* e = find(h);
    return e ? e->name : std::string{};
}

// D10 ladder, the durable rung. ws_id_of() is the named upward conversion
// R1 permits -- session handle -> durable id -- and it can fail, which it
// reports as 0 rather than by throwing, exactly like find_by_name_ci below.
inline std::uint64_t ws_id_of(std::uint64_t h) {
    const Entry* e = find(h);
    return e ? e->ws_id : 0;
}

// Stamp a durable identity onto a live handle. Returns false for an unknown
// handle or a zero id, so a caller cannot quietly mark a workspace durable
// with nothing. Re-stamping the SAME id is idempotent; re-stamping a
// DIFFERENT one is refused -- a workspace's durable identity is its chain
// root and a chain root does not change (D10.2).
inline bool set_ws_id(std::uint64_t h, std::uint64_t id) {
    if (id == 0) return false;
    auto it = table().find(h);
    if (it == table().end()) return false;
    if (it->second.ws_id != 0 && it->second.ws_id != id) return false;
    it->second.ws_id = id;
    return true;
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

inline bool exists(std::uint64_t h) { return table().count(h) != 0; }

inline std::uint64_t parent_of(std::uint64_t h) {
    const Entry* e = find(h);
    return e ? e->parent : 0u;
}

// Children of h, ascending. Bounded by the NUMBER OF WORKSPACES, not by
// MAX_AREA -- design constraint D3 survives. Workspaces are counted in
// handfuls; areas are counted in hundreds of thousands.
inline std::vector<std::uint64_t> children(std::uint64_t h) {
    std::vector<std::uint64_t> out;
    for (const auto& kv : table()) {
        if (kv.first != h && kv.second.parent == h) out.push_back(kv.first);
    }
    std::sort(out.begin(), out.end());
    return out;
}

// Case-insensitive name lookup. Returns 0 when nothing matches, because 0 is
// not a legal handle -- kDefaultHandle is 1 precisely so that 0 can mean "no
// such workspace" without a second return channel.
inline std::uint64_t find_by_name_ci(const std::string& nm) {
    auto up = [](std::string v) {
        for (char& c : v) c = static_cast<char>(::toupper(static_cast<unsigned char>(c)));
        return v;
    };
    const std::string want = up(nm);
    for (const auto& kv : table()) {
        if (up(kv.second.name) == want) return kv.first;
    }
    return 0;
}

// Would making p the parent of h close a cycle? Walks UP from p looking for h.
// This is the STRUCTURAL guard, and it runs at declaration time -- the cheapest
// possible moment, when the cost is one short walk and nothing has been built
// on the bad edge yet. The depth cap is the second line, not the first.
inline bool would_cycle(std::uint64_t h, std::uint64_t p) {
    if (h == 0 || p == 0) return false;
    if (h == p) return true;                       // SELF_REF, refused
    int guard = 0;
    for (std::uint64_t up = p; up != 0; up = parent_of(up)) {
        if (up == h) return true;
        if (++guard > kMaxWorkspaceDepth) return true;   // unreachable if the
    }                                                    // invariant holds
    return false;
}

// Depth of h measured from its root. 0 = a root, matching the catalog's
// "DEPTH 0 = leaf" field being the same integer read from the other end.
inline int depth_of(std::uint64_t h) {
    int d = 0;
    for (std::uint64_t up = parent_of(h); up != 0; up = parent_of(up)) {
        if (++d > kMaxWorkspaceDepth) break;
    }
    return d;
}

// Allocate the next free handle. Monotonic within a session; handles are NOT
// reused after destroy(), because a stale handle held by an area must resolve
// to "gone" and never to "somebody else."
inline std::uint64_t next_handle_ref_bump() {
    static std::uint64_t next = kDefaultHandle;
    for (;;) {
        ++next;
        if (!exists(next)) return next;
    }
}

inline std::uint64_t create(const std::string& nm, std::uint64_t parent = 0) {
    if (parent != 0 && !exists(parent)) return 0;
    const std::uint64_t h = next_handle_ref_bump();
    table()[h] = Entry{ nm, {}, parent };
    return h;
}

inline bool set_parent(std::uint64_t h, std::uint64_t p) {
    if (!exists(h)) return false;
    if (p != 0 && !exists(p)) return false;
    if (would_cycle(h, p)) return false;
    table()[h].parent = p;
    return true;
}

// Remove an EMPTY, CHILDLESS workspace. Refuses otherwise rather than
// cascading, so a destroy can never be the thing that silently orphaned an
// open area. DEFAULT is not destroyable: invariant I1 says an area belongs to
// exactly one workspace and there is no null, which needs DEFAULT to outlive
// every other workspace.
inline bool destroy(std::uint64_t h) {
    if (h == kDefaultHandle || !exists(h)) return false;
    if (member_count(h) != 0)   return false;
    if (!children(h).empty())   return false;
    if (current_handle() == h) set_current_handle(kDefaultHandle);
    table().erase(h);
    return true;
}

// Join, returning the WORKSPACE-LOCAL slot (0..n-1) -- decision D2, rebased
// 0 by owner ruling 2026-08-22.
//
// WHY 0 AND NOT 1. The first cut was 1-based out of xBase habit: dBase and
// FoxPro number work areas from 1, and FoxPro spends 0 on "the lowest unused
// work area." But this project is an EVOLUTION of that lineage and not a clone
// of it, so an inherited convention is only worth keeping when it buys
// something. Here it bought a second numbering base inside one process --
// engine slots 0-based, local slots 1-based -- and the only thing a reader
// gets from that is an off-by-one to remember. Owner ruling: "0 based costs us
// nothing to maintain forward in workspaces too."
//
// It was free to change because it had no consumers: DbArea::wsLocalSlot() had
// ZERO readers at the time of the rebase (written in dbf_file.cpp, cleared in
// dbarea.cpp, read nowhere), and WORKSPACE REGISTRY derived its display number
// from the vector index rather than from the field. An AIF-079 instance of my
// own making, caught while answering a question about numbering rather than
// about dead code.
//
// A LOCAL SLOT IS A POSITION, and positions here are 0-based like the engine's.
// A HANDLE is a KEY -- the runtime twin of the catalog's WS_ID auto-id -- and
// keys have no base to speak of; handle 0 stays reserved for "no such
// workspace / no parent" so failure travels in the return value.
//
// The LOWEST FREE local slot is reused rather than always appending: a leave
// would otherwise leave a permanent hole, and renumbering survivors is not an
// option because a local slot is an address. Bounded by the members of this
// workspace.
//
// Returns -1 if the handle is unknown. The failure sentinel survived the rebase
// untouched precisely because it is NEGATIVE and not zero -- had it been 0, the
// first valid slot and "no such workspace" would now be the same value.
inline std::int32_t join(std::uint64_t h, std::int32_t engine_slot) {
    auto it = table().find(h);
    if (it == table().end()) return -1;
    auto& m = it->second.members;
    for (std::size_t i = 0; i < m.size(); ++i) {
        if (m[i] == engine_slot) return static_cast<std::int32_t>(i);  // idempotent
    }
    for (std::size_t i = 0; i < m.size(); ++i) {
        if (m[i] < 0) { m[i] = engine_slot; return static_cast<std::int32_t>(i); }
    }
    m.push_back(engine_slot);
    return static_cast<std::int32_t>(m.size() - 1);
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

// Rename, or create at a CALLER-CHOSEN handle. Stage 3 added create() for the
// normal path -- reach for this only when the handle is dictated from outside,
// which is what a catalog restore will need when WS_ID is the authority.
inline bool declare(std::uint64_t h, const std::string& nm) {
    if (h == 0) return false;
    table()[h].name = nm;
    return true;
}

} // namespace xbase::workspace
