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
//
// TOKEN for the 2026-08-23 mutation (class WorkspaceTable, default_table):
// AIF-078 code-quality review, ACCEPTED by the steward in-session -- "do one"
// against a four-item recommendation whose item 1 was "WorkspaceTable as an
// object -- map, current handle, recursion flag; the 26 free functions become
// forwarders over a default_table()." NO SIGNATURE CHANGED and no call site
// moved; this is the same move AIF-078 I1.2 made one level down when the
// relation store became all_relation_stores()[ws] with 29 call sites untouched.

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
// WHY THERE IS A CLASS HERE NOW. The state used to be four function-local
// statics -- the map, the current handle, the recursion flag, and a hidden
// counter inside next_handle_ref_bump() -- reachable only through free
// functions. That is an anemic model: data with no owner, and every rule about
// it enforced by whichever function happened to touch it. Two costs were real
// and neither is hypothetical:
//
//   1. NOTHING COULD HOLD A SECOND TABLE. A test that wants a clean membership
//      table, and the area allocator that stage 2 of the slot lane must hand an
//      explicit table rather than have it reach for a process global, both need
//      an INSTANCE. Four hidden statics cannot be instanced, and the fourth was
//      the trap: a table copied without its handle counter would hand out a
//      handle its twin had already spent.
//   2. THE STORAGE WAS PUBLIC. table(), current_handle_ref() and
//      recursion_enabled_ref() returned mutable references to the statics, so
//      every invariant below -- handle 0 is reserved, DEFAULT is not
//      destroyable, a ws_id is stamped once -- was advisory to anyone holding
//      one. They had zero call sites outside this header (measured 2026-08-23),
//      so they are GONE rather than deprecated, and a call site this file did
//      not know about fails to COMPILE instead of quietly bypassing a rule.
//
// The free functions below are unchanged in name, signature and behaviour, and
// forward to default_table(). Sixty-one call sites did not move.
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

// The recursion guard the owner asked for, "like we did databases in memos."
// The number is a backstop, not a policy: real nesting is single digits, and a
// walk that reaches 32 has found a cycle the structural guard missed.
//
// THE POINT OF THIS CONSTANT IS THAT SOMETHING PRINTS WHEN IT FIRES. The
// relation depth cap (set_relations.cpp) is hardcoded twice and returns
// SILENTLY at the limit, so a truncated traversal is indistinguishable from a
// complete one. Every caller of this cap in stage 3 announces.
inline constexpr int kMaxWorkspaceDepth = 32;

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

    // R131 (owner, 2026-08-29): "Once we have a new named workspace, we switch
    // to it and then we can set the environment etc. before an open."
    // THE ENVIRONMENT ACQUIRES AN OWNER, and this is where it lives.
    //
    // A STAMP, EXACTLY LIKE ws_id ABOVE AND FOR THE SAME REASON. R1 of the
    // identity ladder says derivation runs DOWNWARD ONLY, so this header must
    // not reach up into dottalk::paths -- which is CLI-side, and which xbase
    // cannot see. These are three strings the table HOLDS and cannot RESOLVE.
    // The CLI stamps them and the CLI applies them; a workspace knows its
    // roots because it was told, and it cannot go and find out.
    //
    // WHY THREE STRINGS AND NOT A WORKSPACE-AWARE RESOLVER (R131 sec 11.2):
    // dottalk::paths::get_slot has 102 CALL SITES across thirty-odd files, and
    // most of them are not workspace code at all -- bbs_store, cmd_smtp,
    // cmd_drawio, edu_cobol, fn_string. Handing a workspace to code that has
    // none is a rewrite, not a design option. So the global stays the single
    // resolution authority and SWITCH re-points it; every one of those 102
    // readers is untouched and keeps reading one slot.
    //
    // Q2 IS INHERIT (R131 sec 11.5). A workspace is stamped AT CREATION from
    // whatever is current, so a workspace whose environment is a question with
    // no answer never exists -- the AIF-148 floor, one lane over. EMPTY here
    // therefore means only NOT STAMPED YET, and that is true of exactly one
    // entry: DEFAULT, which exists before any command runs. The CLI stamps it
    // lazily from the INIT slots the first time anything asks.
    std::string dbf_root;
    std::string idx_root;
    std::string lmdb_root;
};

// ---------------------------------------------------------------------------
// The table itself.
//
// Every rule about workspace membership lives on this class and nowhere else.
// The free functions after it are forwarders and hold no logic, so there is one
// place to read a rule and one place to change it -- which is what the I1.3a
// two-resolver defect is: two functions answering one question with different
// answers, neither saying which one you got.
//
// Constructed with DEFAULT already present. There is no state in which handle 1
// does not exist, because invariant I1 has no null workspace to fall back to.
// ---------------------------------------------------------------------------
class WorkspaceTable {
public:
    WorkspaceTable() {
        entries_.emplace(kDefaultHandle, Entry{ kDefaultName, {}, 0, 0 });
    }

    // -- current workspace ---------------------------------------------------

    // The workspace a newly opened area joins. Defaults to DEFAULT and stays
    // there until something sets it, which is why stage 2 changed no observable
    // behaviour: every area still resolves to handle 1, exactly as the constant
    // it replaced did.
    std::uint64_t current_handle() const noexcept { return current_; }

    // REJECTS 0, and AIF-078 I1.2 is why that moved from a call site into the
    // API.
    //
    // 0 is reserved for "no such workspace / no parent" (find_by_name_ci below)
    // and is _ws_handle's value on a CLOSED area (dbarea.cpp). Until I1.2 that
    // reservation was policed only where WORKSPACE SWITCH happens to call this
    // -- so one future caller passing 0 would stamp handle 0 onto every
    // subsequently opened area, and those areas are isOpen(). Harmless while
    // the relation store was one flat map; load-bearing the moment the store is
    // PARTITIONED by this number, because a whole workspace's relations would
    // land in the reserved bucket and read back as belonging to nothing.
    //
    // Returns false rather than throwing or printing: this is a header contract
    // with no output of its own, and every existing caller that discards the
    // result gets the same behaviour it had for a legal handle.
    bool set_current_handle(std::uint64_t h) noexcept {
        if (h == 0) return false;
        current_ = h;
        return true;
    }

    // -- recursion -----------------------------------------------------------

    // SET RECURSION ON | OFF -- owner ruling 2026-08-22: "even with OFF we
    // still allow multiple workspaces, just parallel." So this flag does NOT
    // gate whether nested workspaces may EXIST; it gates whether an operation
    // on a parent DESCENDS into its children. OFF means a close touches exactly
    // the workspace you named and says so.
    bool recursion_enabled() const noexcept { return recursion_; }
    void set_recursion_enabled(bool on) noexcept { recursion_ = on; }

    // -- lookup --------------------------------------------------------------

    const Entry* find(std::uint64_t h) const {
        auto it = entries_.find(h);
        return it == entries_.end() ? nullptr : &it->second;
    }

    std::string name_of(std::uint64_t h) const {
        const Entry* e = find(h);
        return e ? e->name : std::string{};
    }

    // D10 ladder, the durable rung. ws_id_of() is the named upward conversion
    // R1 permits -- session handle -> durable id -- and it can fail, which it
    // reports as 0 rather than by throwing, exactly like find_by_name_ci below.
    std::uint64_t ws_id_of(std::uint64_t h) const {
        const Entry* e = find(h);
        return e ? e->ws_id : 0;
    }

    // R131. Roots move as a SET of three, never one at a time, because a
    // half-stamped workspace resolves its tables under one system and its
    // indexes under another -- which is the exact failure R131 sec 3 measured
    // (MCC's STUDENTS answering under the Cascade LMDB tree). A caller that
    // wants to change one slot reads all three, edits one, and writes all
    // three back; there is deliberately no per-slot setter.
    bool roots_of(std::uint64_t h,
                  std::string& dbf, std::string& idx, std::string& lmdb) const {
        const Entry* e = find(h);
        if (!e) return false;
        dbf = e->dbf_root; idx = e->idx_root; lmdb = e->lmdb_root;
        return true;
    }

    // TRUE only when all three are stamped. A partially stamped entry answers
    // FALSE so the CLI re-stamps it whole rather than completing it piecemeal.
    bool roots_stamped(std::uint64_t h) const {
        const Entry* e = find(h);
        return e && !e->dbf_root.empty() && !e->idx_root.empty()
                 && !e->lmdb_root.empty();
    }

    bool set_roots(std::uint64_t h, const std::string& dbf,
                   const std::string& idx, const std::string& lmdb) {
        auto it = entries_.find(h);
        if (it == entries_.end()) return false;
        it->second.dbf_root  = dbf;
        it->second.idx_root  = idx;
        it->second.lmdb_root = lmdb;
        return true;
    }

    // Stamp a durable identity onto a live handle. Returns false for an unknown
    // handle or a zero id, so a caller cannot quietly mark a workspace durable
    // with nothing. Re-stamping the SAME id is idempotent; re-stamping a
    // DIFFERENT one is refused -- a workspace's durable identity is its chain
    // root and a chain root does not change (D10.2).
    bool set_ws_id(std::uint64_t h, std::uint64_t id) {
        if (id == 0) return false;
        auto it = entries_.find(h);
        if (it == entries_.end()) return false;
        if (it->second.ws_id != 0 && it->second.ws_id != id) return false;
        it->second.ws_id = id;
        return true;
    }

    std::size_t member_count(std::uint64_t h) const {
        const Entry* e = find(h);
        return e ? e->members.size() : 0u;
    }

    std::vector<std::int32_t> members(std::uint64_t h) const {
        const Entry* e = find(h);
        return e ? e->members : std::vector<std::int32_t>{};
    }

    // AIF-078 / 2026-08-29. THE REVERSE OF members(), AND IT LIVES HERE FOR THE
    // REASON EVERY OTHER RULE IN THIS CLASS DOES: an engine slot has exactly one
    // owning workspace (invariant I1), so "who owns this slot" is a fact about
    // the membership table and must have exactly one implementation. DBAREA and
    // GPS both ask it; neither may carry its own scan, because two answers to
    // one question is the shape this lane keeps finding (R112's two resolvers,
    // AIF-137's unscoped parent, the four declarations of a field name).
    //
    // Returns 0 for "no workspace owns this slot". That is a REAL state, not an
    // error: reconcile_unregistered_areas() in cmd_workspace.cpp exists because
    // an area can be open and belong to nothing, and it calls that a defect in
    // registration. A caller that prints 0 as "(none)" is therefore an
    // instrument for it, which is why this returns a sentinel rather than
    // asserting.
    //
    // Linear in workspaces x members. That is the right cost for a display
    // path and the wrong one for a hot loop; if a hot caller ever appears,
    // build an index HERE rather than caching a copy at the call site.
    std::uint64_t owner_of_slot(std::int32_t engine_slot) const {
        if (engine_slot < 0) return 0;
        for (const auto& kv : entries_) {
            for (const auto slot : kv.second.members) {
                if (slot == engine_slot) return kv.first;
            }
        }
        return 0;
    }

    std::vector<std::uint64_t> handles() const {
        std::vector<std::uint64_t> out;
        out.reserve(entries_.size());
        for (const auto& kv : entries_) out.push_back(kv.first);
        return out;
    }

    bool exists(std::uint64_t h) const { return entries_.count(h) != 0; }

    std::uint64_t parent_of(std::uint64_t h) const {
        const Entry* e = find(h);
        return e ? e->parent : 0u;
    }

    // Children of h, ascending. Bounded by the NUMBER OF WORKSPACES, not by
    // MAX_AREA -- design constraint D3 survives. Workspaces are counted in
    // handfuls; areas are counted in hundreds of thousands.
    std::vector<std::uint64_t> children(std::uint64_t h) const {
        std::vector<std::uint64_t> out;
        for (const auto& kv : entries_) {
            if (kv.first != h && kv.second.parent == h) out.push_back(kv.first);
        }
        std::sort(out.begin(), out.end());
        return out;
    }

    // Case-insensitive name lookup. Returns 0 when nothing matches, because 0
    // is not a legal handle -- kDefaultHandle is 1 precisely so that 0 can mean
    // "no such workspace" without a second return channel.
    std::uint64_t find_by_name_ci(const std::string& nm) const {
        auto up = [](std::string v) {
            for (char& c : v) c = static_cast<char>(::toupper(static_cast<unsigned char>(c)));
            return v;
        };
        const std::string want = up(nm);
        for (const auto& kv : entries_) {
            if (up(kv.second.name) == want) return kv.first;
        }
        return 0;
    }

    // Would making p the parent of h close a cycle? Walks UP from p looking for
    // h. This is the STRUCTURAL guard, and it runs at declaration time -- the
    // cheapest possible moment, when the cost is one short walk and nothing has
    // been built on the bad edge yet. The depth cap is the second line, not the
    // first.
    bool would_cycle(std::uint64_t h, std::uint64_t p) const {
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
    int depth_of(std::uint64_t h) const {
        int d = 0;
        for (std::uint64_t up = parent_of(h); up != 0; up = parent_of(up)) {
            if (++d > kMaxWorkspaceDepth) break;
        }
        return d;
    }

    // -- mutation ------------------------------------------------------------

    // Allocate the next free handle. Monotonic within a session; handles are
    // NOT reused after destroy(), because a stale handle held by an area must
    // resolve to "gone" and never to "somebody else."
    //
    // The counter is a MEMBER and not a static, which is the whole reason this
    // class exists rather than a namespace of statics: two tables sharing one
    // counter would hand out a handle the other had already spent, and neither
    // would know.
    std::uint64_t next_handle_ref_bump() {
        for (;;) {
            ++next_;
            if (!exists(next_)) return next_;
        }
    }

    std::uint64_t create(const std::string& nm, std::uint64_t parent = 0) {
        if (parent != 0 && !exists(parent)) return 0;
        const std::uint64_t h = next_handle_ref_bump();
        entries_[h] = Entry{ nm, {}, parent, 0 };
        return h;
    }

    bool set_parent(std::uint64_t h, std::uint64_t p) {
        if (!exists(h)) return false;
        if (p != 0 && !exists(p)) return false;
        if (would_cycle(h, p)) return false;
        entries_[h].parent = p;
        return true;
    }

    // Remove an EMPTY, CHILDLESS workspace. Refuses otherwise rather than
    // cascading, so a destroy can never be the thing that silently orphaned an
    // open area. DEFAULT is not destroyable: invariant I1 says an area belongs
    // to exactly one workspace and there is no null, which needs DEFAULT to
    // outlive every other workspace.
    bool destroy(std::uint64_t h) {
        if (h == kDefaultHandle || !exists(h)) return false;
        if (member_count(h) != 0)   return false;
        if (!children(h).empty())   return false;
        if (current_handle() == h) set_current_handle(kDefaultHandle);
        entries_.erase(h);
        return true;
    }

    // Join, returning the WORKSPACE-LOCAL slot (0..n-1) -- decision D2, rebased
    // 0 by owner ruling 2026-08-22.
    //
    // WHY 0 AND NOT 1. The first cut was 1-based out of xBase habit: dBase and
    // FoxPro number work areas from 1, and FoxPro spends 0 on "the lowest
    // unused work area." But this project is an EVOLUTION of that lineage and
    // not a clone of it, so an inherited convention is only worth keeping when
    // it buys something. Here it bought a second numbering base inside one
    // process -- engine slots 0-based, local slots 1-based -- and the only
    // thing a reader gets from that is an off-by-one to remember. Owner ruling:
    // "0 based costs us nothing to maintain forward in workspaces too."
    //
    // It was free to change because it had no consumers: DbArea::wsLocalSlot()
    // had ZERO readers at the time of the rebase (written in dbf_file.cpp,
    // cleared in dbarea.cpp, read nowhere), and WORKSPACE REGISTRY derived its
    // display number from the vector index rather than from the field. An
    // AIF-079 instance of my own making, caught while answering a question
    // about numbering rather than about dead code.
    //
    // A LOCAL SLOT IS A POSITION, and positions here are 0-based like the
    // engine's. A HANDLE is a KEY -- the runtime twin of the catalog's WS_ID
    // auto-id -- and keys have no base to speak of; handle 0 stays reserved for
    // "no such workspace / no parent" so failure travels in the return value.
    //
    // The LOWEST FREE local slot is reused rather than always appending: a
    // leave would otherwise leave a permanent hole, and renumbering survivors
    // is not an option because a local slot is an address. Bounded by the
    // members of this workspace.
    //
    // Returns -1 if the handle is unknown. The failure sentinel survived the
    // rebase untouched precisely because it is NEGATIVE and not zero -- had it
    // been 0, the first valid slot and "no such workspace" would now be the
    // same value.
    std::int32_t join(std::uint64_t h, std::int32_t engine_slot) {
        // R6 (ruling D10 sec 2a, 2026-08-23): an absent value must not be
        // representable in the space of present ones.
        //
        // A NEGATIVE slot is not a position. It means "this area has no engine
        // slot at all" -- and -1 is ALSO this array's FREE-ENTRY marker, four
        // lines below. Two different absences shared one value, so the
        // idempotence scan matched the first FREE entry, returned its index,
        // and CLAIMED NOTHING. Every slotless DbArea in the tree therefore
        // "joined" as a silent no-op: roughly 47 of them (message_catalog 16,
        // bbs_store 14, cmd_workspace 5, the GUI's session areas, and a dozen
        // more), each one reporting a local slot it did not hold.
        //
        // Refused in the RETURN VALUE and not by printing: this is a membership
        // table, and giving it an output dependency to announce a precondition
        // the caller can check is the wrong trade. R3 -- failure travels in the
        // return.
        if (engine_slot < 0) return -1;
        auto it = entries_.find(h);
        if (it == entries_.end()) return -1;
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
    void leave(std::uint64_t h, std::int32_t engine_slot) {
        // R6, the symmetric half. A negative "leave" would match the first FREE
        // entry for exactly the reason join() did, so it cleared a hole and
        // called it a departure. Nothing that never joined can leave.
        if (engine_slot < 0) return;
        auto it = entries_.find(h);
        if (it == entries_.end()) return;
        auto& m = it->second.members;
        for (auto& slot : m) {
            if (slot == engine_slot) { slot = -1; break; }
        }
        while (!m.empty() && m.back() < 0) m.pop_back();
    }

    // Rename, or create at a CALLER-CHOSEN handle. Stage 3 added create() for
    // the normal path -- reach for this only when the handle is dictated from
    // outside, which is what a catalog restore will need when WS_ID is the
    // authority.
    bool declare(std::uint64_t h, const std::string& nm) {
        if (h == 0) return false;
        entries_[h].name = nm;
        return true;
    }

private:
    std::unordered_map<std::uint64_t, Entry> entries_;
    std::uint64_t current_{kDefaultHandle};
    bool          recursion_{true};

    // Starts AT kDefaultHandle so the first bump yields kDefaultHandle + 1.
    std::uint64_t next_{kDefaultHandle};
};

// The one table the shell runs on. Function-local static so this header still
// needs no translation unit of its own and no CMake edit -- the storage moved
// INSIDE an object, it did not move into a .cpp.
inline WorkspaceTable& default_table() {
    static WorkspaceTable t;
    return t;
}

// ---------------------------------------------------------------------------
// Free-function surface -- UNCHANGED in name, signature and behaviour.
//
// Each one forwards to the identically named WorkspaceTable method on
// default_table(). No rule is enforced here; the rules and the comments that
// explain them live on the class above, so there is exactly one copy of each.
// ---------------------------------------------------------------------------

inline std::uint64_t current_handle() noexcept { return default_table().current_handle(); }
inline bool set_current_handle(std::uint64_t h) noexcept { return default_table().set_current_handle(h); }

inline bool recursion_enabled() noexcept { return default_table().recursion_enabled(); }
inline void set_recursion_enabled(bool on) noexcept { default_table().set_recursion_enabled(on); }

inline const Entry* find(std::uint64_t h) { return default_table().find(h); }
inline std::string  name_of(std::uint64_t h) { return default_table().name_of(h); }
inline std::uint64_t ws_id_of(std::uint64_t h) { return default_table().ws_id_of(h); }
inline bool set_ws_id(std::uint64_t h, std::uint64_t id) { return default_table().set_ws_id(h, id); }

// R131. Forwarders, holding no logic, exactly like the rest of this block.
inline bool roots_of(std::uint64_t h, std::string& dbf, std::string& idx,
                     std::string& lmdb) {
    return default_table().roots_of(h, dbf, idx, lmdb);
}
inline bool roots_stamped(std::uint64_t h) { return default_table().roots_stamped(h); }
inline bool set_roots(std::uint64_t h, const std::string& dbf,
                      const std::string& idx, const std::string& lmdb) {
    return default_table().set_roots(h, dbf, idx, lmdb);
}

inline std::size_t member_count(std::uint64_t h) { return default_table().member_count(h); }
inline std::vector<std::int32_t> members(std::uint64_t h) { return default_table().members(h); }
inline std::uint64_t owner_of_slot(std::int32_t engine_slot) { return default_table().owner_of_slot(engine_slot); }
inline std::vector<std::uint64_t> handles() { return default_table().handles(); }
inline bool exists(std::uint64_t h) { return default_table().exists(h); }

inline std::uint64_t parent_of(std::uint64_t h) { return default_table().parent_of(h); }
inline std::vector<std::uint64_t> children(std::uint64_t h) { return default_table().children(h); }
inline std::uint64_t find_by_name_ci(const std::string& nm) { return default_table().find_by_name_ci(nm); }
inline bool would_cycle(std::uint64_t h, std::uint64_t p) { return default_table().would_cycle(h, p); }
inline int  depth_of(std::uint64_t h) { return default_table().depth_of(h); }

inline std::uint64_t next_handle_ref_bump() { return default_table().next_handle_ref_bump(); }
inline std::uint64_t create(const std::string& nm, std::uint64_t parent = 0) { return default_table().create(nm, parent); }
inline bool set_parent(std::uint64_t h, std::uint64_t p) { return default_table().set_parent(h, p); }
inline bool destroy(std::uint64_t h) { return default_table().destroy(h); }

inline std::int32_t join(std::uint64_t h, std::int32_t engine_slot) { return default_table().join(h, engine_slot); }
inline void leave(std::uint64_t h, std::int32_t engine_slot) { default_table().leave(h, engine_slot); }
inline bool declare(std::uint64_t h, const std::string& nm) { return default_table().declare(h, nm); }

} // namespace xbase::workspace
