// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// File: src/cli/set_relations.cpp
// Purpose: Relation graph storage, lookup, and tuple-walk helpers shared by
//          REL, ERSATZ, and workspace restoration flows.
// Boundary: This file maintains in-process relation state; command parsing and
//           user messaging belong in the command layer that calls into it.

#include "set_relations.hpp"

#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
#include "xbase.hpp"
#include "workareas.hpp"
#include "xbase_field_getters.hpp"
#include "db_tuple_stream.hpp"
#include "tuple_types.hpp"
#include "textio.hpp"
#include "workarea_util.hpp"
#include "xbase/workspace_membership.hpp"   // I1.2: the store is partitioned by workspace handle
#include "dottalk/build_vectors.hpp"        // AIF-044: the depth cap is a build vector, not a literal

#include <algorithm>
#include <cctype>
#include <functional>
#include <iostream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {

// Forward declaration
static std::string get_by_index_as_string(xbase::DbArea& db, int field_index_1based);

// ---------------------------
// Internal structures
// ---------------------------

struct JoinField {
    int parent_field; // 1-based
    int child_field;  // 1-based
};

struct Relation {
    std::string child;                         // normalized (UPPER)
    std::vector<JoinField> joins;              // HARD bindings (indices)
    std::vector<std::string> names;            // legacy same-field names
    std::vector<std::string> parent_names;     // parent-side field names
    std::vector<std::string> child_names;      // child-side field names
};

// AIF-078 I1.2 -- THE RELATION STORE IS PARTITIONED BY WORKSPACE.
//
// Until 2026-08-23 this was ONE process-global map, and that single fact was
// what forced WORKSPACE CLOSE's known over-reach: a scoped close had to clear
// EVERY relation, because leaving an edge pointing into an area it had just
// emptied is the dangling-parent shape, and a dangling relation is worse than
// an over-eager clear. The cost was that closing one workspace destroyed the
// relations of workspaces it never touched -- printed, when it could bite, as
// "relations are cleared GLOBALLY ... (AIF-078 stage 3 limitation)."
//
// D9.3 as amended by sec 9a: EACH WORKSPACE OWNS ITS RELATION MAP. The first
// draft of D9 sec 4 proposed a composite RelKey{ws, name} in one flat map; the
// amendment superseded it with the better shape -- THE PARTITION IS THE MAP.
// Same-named parents in two workspaces cannot collide because the key never
// leaves its workspace, and no hash function has to be written to get that.
//
// D10.4 fixes the SPELLING of the partition key: the RUNTIME store keys on the
// interned uint64 handle -- what the engine maintains, what every area already
// carries as _ws_handle, and the only workspace identity any runtime writer in
// this tree produces. The durable WS_ID belongs to the persisted form, which is
// explicitly out of scope here (D8.2: RelationSpec gains no handle).
//
// WHY relations_store() KEEPS ITS SHAPE. It had 29 call sites in this file and
// nowhere else, roughly half of which never see a DbArea at all. Rewriting all
// 29 to thread a handle would have been 29 chances to thread the WRONG one.
// Instead the accessor resolves the current workspace itself, so the call sites
// are unchanged and there is exactly ONE place that decides which partition a
// name lookup means. Callers that must name a DIFFERENT workspace say so, once,
// through relations_store_for().
static std::unordered_map<std::uint64_t,
                          std::unordered_map<std::string, std::vector<Relation>>>&
all_relation_stores() {
    static std::unordered_map<std::uint64_t,
                              std::unordered_map<std::string, std::vector<Relation>>> stores;
    return stores;
}

// The relation map of a NAMED workspace. operator[] default-constructs, which
// is what we want: a workspace with no relations yet has an empty map, not a
// missing one, so every caller reads the same shape.
static std::unordered_map<std::string, std::vector<Relation>>&
relations_store_for(std::uint64_t ws) {
    return all_relation_stores()[ws];
}

// The CURRENT workspace's map. This is what "the relation store" means to every
// existing caller, and the scoping is the whole change.
static std::unordered_map<std::string, std::vector<Relation>>& relations_store() {
    return relations_store_for(xbase::workspace::current_handle());
}

#if DOTTALK_EXTRA_DIAGNOSTICS
static constexpr bool default_relation_verbose = true;
#else
static constexpr bool default_relation_verbose = false;
#endif

bool        g_autorefresh = true;
bool        g_verbose     = default_relation_verbose;
std::size_t g_scan_limit  = 500000;

// THE RELATION GRAPH'S DEPTH CAP, VECTORED 2026-08-30. It was the literal 24,
// written twice, thirty lines apart. Owner: "the 24 is an arbitrary limit we
// surmized for testing safety, it should be metadata like max_areas." It now
// comes from config/build_vectors.cmake beside max_areas, and it is a SEPARATE
// vector from the workspace nesting cap (32) because they bound two different
// graphs over the same areas -- see xbase::workspace::kMaxWorkspaceDepth.
static constexpr int kRelationDepthCap =
    static_cast<int>(dottalk::build::max_relation_depth);

// AIF-074 P1.3 (RDB-06): truncation latch. Warns ONCE per latch cycle so
// cascaded refresh loops cannot spam the transcript.
//
// THE LATCH NOW CARRIES A REASON, AND THAT IS THE REAL REPAIR HERE. This
// subsystem built truncation honesty and then exempted its own depth cap from
// it: note_scan_truncated() fired at three STEP-COUNT sites and at NEITHER
// depth site, both of which returned bare. RELSCAN's registered read rule says
// what that costs -- "an honest incomplete result announces itself, and a
// silent truncation reads exactly like a complete answer." Vectoring the number
// without this would have been worse than leaving it: a cap that can now be
// CHANGED and still says nothing when it fires.
//
// The scan wording is byte-identical to what it has always emitted, because
// RELSCAN T2 asserts that exact line and perturbing a registered assertion to
// close a different gap is how a suite stops meaning what it says.
bool g_scan_truncated = false;
static void note_truncated(const std::string& text) {
    if (!g_scan_truncated) {
        g_scan_truncated = true;
        std::cout << "REL: " << text << "\n";
    }
}
static void note_scan_truncated() {
    note_truncated("scan limit (" + std::to_string(g_scan_limit)
                   + ") reached; results may be incomplete.");
}
// A DEPTH TRIP IS NOT A SCAN TRIP AND MUST NOT BORROW ITS SENTENCE. Both mean
// "this traversal is incomplete", so both set the one latch three consumers
// already poll; they differ in WHY, and a message naming the wrong limiter is
// honest about the incompleteness and wrong about the cause.
static void note_edge_skipped(const std::string& parent, const std::string& child);

static void note_depth_truncated(const char* where) {
    note_truncated("relation depth cap (" + std::to_string(kRelationDepthCap)
                   + ") reached in " + where
                   + "; deeper relations were NOT visited and results may be"
                     " incomplete.");
}

// POSITION MUST STAY COMPUTABLE, AND THAT IS WHY THIS FUNCTION EXISTS.
// Owner 2026-08-30: "one of the main points of our system is we can
// mathematically determine our position." A refresh either moved a child or it
// did not, and after a SILENT skip the operator cannot tell which -- the child
// sits on some row, and nothing distinguishes "it matched there" from "it was
// never visited." That is not an untidy message, it is a LOSS OF DETERMINACY,
// in the one system property this house says it sells. An announced skip keeps
// position computable: you know exactly which edge did not propagate and why.
//
// This is also the answer to the obvious "fix" -- teaching USE to clear
// relations the way CLOSE does. Ruled the same day, and the owner's word for it
// is stronger than "cursor operation": USE IS AN ATOM. "you set your cursor --
// use -- and return if you must", and "it should be the job of the relations
// managers to worry about multiple ws relations." Indivisible: no bookkeeping,
// no conditional side effects, nothing the operator cannot predict from the
// command alone. THAT IS WHAT MAKES POSITION COMPUTABLE AT THIS END -- an atom
// whose effect depended on graph state the operator cannot see from the command
// would cost the determinacy this latch is protecting at the other end. So the
// state is legitimate, the announcement is the whole treatment, and the concern
// belongs to the relation managers rather than to USE.
//
// A SKIPPED EDGE IS NEITHER A DEPTH TRIP NOR A SCAN TRIP: it is a child the
// SCOPED resolver could not see. It trips the same latch because it means the
// same thing about the result, and it draws the same distinction add_relation
// now draws -- absent, or present elsewhere. Naming the workspace is the whole
// point: it turns "nothing happened" into "the boundary is here."
static void note_edge_skipped(const std::string& parent, const std::string& child) {
    const xbase::DbArea* elsewhere = cli::find_open_area_by_name_ci(child);
    const std::string edge = "relation " + parent + " -> " + child
                           + " was NOT refreshed: ";
    if (elsewhere) {
        const std::uint64_t h = elsewhere->wsHandle();
        note_truncated(edge + child + " is open in workspace "
                       + (h ? xbase::workspace::name_of(h) : std::string("(none)"))
                       + ", not the current one; results may be incomplete.");
    } else {
        note_truncated(edge + child + " is not open; results may be incomplete.");
    }
}

xbase::XBaseEngine* g_engine = nullptr;

// Optional override anchor. IMPORTANT:
// - We DO NOT auto-set this during ADD.
// - If empty, we always anchor to the CURRENT workarea (selected area).
static std::string& current_parent_override() {
    static std::string parent_name;
    return parent_name;
}

static inline void emit_rel_diag(
    dottalk::helpdata::MessageId id,
    const std::unordered_map<std::string, std::string>& vars = {})
{
    if (!g_verbose) return;
    cli::cmdout::print_prefixed_message("REL", id, vars);
}

// A REFUSAL IS NOT A DIAGNOSTIC, AND THE DIFFERENCE WAS PROFILE-DEPENDENT.
// Measured 2026-08-30 by reading CMakeLists.txt:172-177 and the gate above:
// `g_verbose` defaults to DOTTALK_EXTRA_DIAGNOSTICS, which is ON under
// DOTTALK_PROFILE=DEV and OFF under PROD. Every add-failure path in
// add_relation() reported through emit_rel_diag, and the caller
// (cmd_relations.cpp:500) is a bare `if (!add_relation(...)) return;`. So on a
// PROD build SET RELATION could fail and print NOTHING AT ALL -- no reason, no
// refusal, only the absence of the OK line. That is the same shape as the AIF
// allocator's locale-dependent collapse fixed the same morning: a failure that
// speaks on the developer's build and goes mute on the shipped one.
//
// LIMIT, STATED: read from the build files and the compile-time gate. A PROD
// build has NOT been produced or run to observe it.
//
// A trace may be verbosity-gated. The answer to what someone asked may not.
static inline void emit_rel_refusal(
    dottalk::helpdata::MessageId id,
    const std::unordered_map<std::string, std::string>& vars = {})
{
    cli::cmdout::print_prefixed_message("REL", id, vars);
}

// ---------------------------
// Helpers
// ---------------------------

static std::string up_copy(std::string s) { return textio::up(std::move(s)); }

static std::string infer_parent_from_workarea() {
    try {
        const xbase::DbArea* A = workareas::db(workareas::current_slot());
        if (!A) return {};
        const std::string ln = A->logicalName();
        if (!ln.empty()) return up_copy(ln);
        return up_copy(A->name());
    } catch (...) { return {}; }
}

static std::string naked_field(std::string s) {
    auto dot = s.find('.');
    if (dot != std::string::npos) s = s.substr(dot + 1);
    return textio::trim(std::move(s));
}

static bool same_field_lists(const std::vector<std::string>& a,
                             const std::vector<std::string>& b) {
    if (a.size() != b.size()) return false;
    for (std::size_t i = 0; i < a.size(); ++i) {
        if (up_copy(naked_field(a[i])) != up_copy(naked_field(b[i]))) return false;
    }
    return true;
}

static std::string join_names_csv(const std::vector<std::string>& names) {
    std::string out;
    for (std::size_t i = 0; i < names.size(); ++i) {
        if (i) out += ",";
        out += names[i];
    }
    return out;
}

static std::string ltrim_copy(std::string s) {
    std::size_t i = 0;
    while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) ++i;
    if (i) s.erase(0, i);
    return s;
}

static bool is_numeric_literal(const std::string& s) {
    const std::string t = ltrim_copy(textio::trim(s));
    if (t.empty()) return false;
    std::size_t i = 0;
    if (t[i] == '+' || t[i] == '-') ++i;
    bool any_digit = false;
    bool any_dot = false;
    for (; i < t.size(); ++i) {
        const unsigned char ch = static_cast<unsigned char>(t[i]);
        if (std::isdigit(ch)) { any_digit = true; continue; }
        if (t[i] == '.' && !any_dot) { any_dot = true; continue; }
        return false;
    }
    return any_digit;
}

// AIF-074 P0.2: find_open_area_by_name_ci moved to the shared home in
// workarea_util.{hpp,cpp}; behavior unchanged.
using cli::find_open_area_by_name_ci;
using cli::find_open_area_in_workspace_ci;   // AIF-137, scoped variant

// AIF-078 D8 sec 7, 2026-08-22. A file-local slot_of_area_ptr() used to live
// here: a linear scan over workareas::count() -- which returns the CONFIGURED
// MAXIMUM, not the number of open areas -- reached from ScopedEngineSelect's
// ctor, and so from inside goto_first_match()'s per-record loop below. It was a
// LEFTOVER: AIF-120 I1.1 had already replaced that scan with an O(1) member
// read in cli::slot_of_area (workarea_util.cpp), whose sibling import sits
// directly above this comment, and the sweep missed this copy. Deleted rather than rewritten, because a second spelling of
// one question is the defect I1.3a spent a day closing one layer down.
//
// It was not merely slower. I1.1's note records that the shared version answers
// correctly for a CLOSED area, where the scan returned -1, because
// workareas::db(i) walks only what is currently bound. Every ScopedEngineSelect
// here guards `slot < 0`, so the old copy silently declined to select for a
// closed area; the shared one selects the real slot. Behaviour for an OPEN area
// -- which is every call site in this file -- is identical.
using cli::slot_of_area;

class ScopedEngineSelect {
public:
    explicit ScopedEngineSelect(const xbase::DbArea* area) noexcept {
        if (!g_engine || !area) return;
        const int slot = slot_of_area(area);
        if (slot < 0) return;
        try {
            prev_ = g_engine->currentArea();
            if (prev_ != slot) {
                g_engine->selectArea(slot);
                active_ = true;
            }
        } catch (...) { active_ = false; }
    }

    ~ScopedEngineSelect() noexcept {
        if (!active_ || !g_engine) return;
        try { g_engine->selectArea(prev_); } catch (...) {}
    }

    ScopedEngineSelect(const ScopedEngineSelect&) = delete;
    ScopedEngineSelect& operator=(const ScopedEngineSelect&) = delete;

private:
    int prev_{-1};
    bool active_{false};
};

// ---------------------------------------------------------------------------
// Work-area state preservation
//
// REL inspection/enumeration commands should not change the user's current
// work-area selection or record pointers. During enumeration we necessarily
// reposition areas (TOP/SKIP/GOTO) to follow relations. This helper snapshots
// all open areas' record numbers and restores them on scope exit (best-effort).
// ---------------------------------------------------------------------------
class WorkAreaStateGuard {
public:
    explicit WorkAreaStateGuard() noexcept
        : eng_(g_engine)
        , prev_area_(g_engine ? g_engine->currentArea() : -1)
    {
        const std::size_t n = workareas::count();
        saved_.reserve(n);
        for (std::size_t i = 0; i < n; ++i) {
            xbase::DbArea* a = workareas::db(i);
            if (!a || !a->isOpen()) continue;
            Saved s{};
            s.slot  = static_cast<int>(i);
            s.recno = a->recno();
            saved_.push_back(s);
        }
    }

    ~WorkAreaStateGuard() noexcept {
        // Restore record pointers first...
        for (const auto& s : saved_) {
            xbase::DbArea* a = workareas::db(static_cast<std::size_t>(s.slot));
            if (!a || !a->isOpen()) continue;
            try {
                const int32_t total = a->recCount();
                if (s.recno >= 1 && s.recno <= total) {
                    (void)a->gotoRec(s.recno);
                    (void)a->readCurrent();
                } else if (total > 0) {
                    a->top();
                    (void)a->readCurrent();
                }
            } catch (...) {
                // best-effort
            }
        }

        // ...then restore user's current area selection.
        if (eng_ && prev_area_ >= 0) {
            try { eng_->selectArea(prev_area_); } catch (...) {}
        }

        // If live-follow is enabled, re-sync children to the restored parent.
        // (No-op when follow is off.)
        try { relations_api::refresh_if_enabled(); } catch (...) {}
    }

    WorkAreaStateGuard(const WorkAreaStateGuard&) = delete;
    WorkAreaStateGuard& operator=(const WorkAreaStateGuard&) = delete;

private:
    struct Saved {
        int slot{-1};
        int32_t recno{0};
    };

    xbase::XBaseEngine* eng_{nullptr};
    int prev_area_{-1};
    std::vector<Saved> saved_{};
};

static int find_field_index_ci(const xbase::DbArea& db, const std::string& name) {
    const std::string target = up_copy(textio::trim(name));
    int idx = 1;
    for (const auto& fd : db.fields()) {
        if (up_copy(textio::trim(fd.name)) == target) return idx;
        ++idx;
    }
    return -1;
}

static const xbase::FieldDef* find_field_def_ci(const xbase::DbArea& db, const std::string& name) {
    const std::string target = up_copy(textio::trim(name));
    for (const auto& fd : db.fields()) {
        if (up_copy(textio::trim(fd.name)) == target) return &fd;
    }
    return nullptr;
}

static std::string get_by_index_as_string(xbase::DbArea& db, int field_index_1based) {
    if (field_index_1based <= 0) return {};
    const auto& fds = db.fields();
    const std::size_t idx0 = static_cast<std::size_t>(field_index_1based - 1);
    if (idx0 >= fds.size()) return {};
    ScopedEngineSelect focus(&db);
    return xfg::getFieldAsString(db, fds[idx0].name);
}

// kv for scan: (child_field_index, expected_value)
static std::vector<std::pair<int, std::string>>
parent_values(const xbase::DbArea& parent, const std::vector<JoinField>& joins) {
    std::vector<std::pair<int, std::string>> out;
    out.reserve(joins.size());
    xbase::DbArea& P = const_cast<xbase::DbArea&>(parent);
    for (const auto& j : joins) {
        out.emplace_back(j.child_field, get_by_index_as_string(P, j.parent_field));
    }
    return out;
}

// Numeric compare when both parse as numeric.
static bool values_match(xbase::DbArea& child,
                         const std::vector<std::pair<int, std::string>>& kv) {
    for (const auto& [child_field_index, expected_raw] : kv) {
        const std::string expected = textio::trim(expected_raw);

        const std::string actual = textio::trim(get_by_index_as_string(child, child_field_index));

        // AIF-074 P1.4 (typed equality, closes RDB-03): numeric comparison
        // applies when BOTH sides are numeric literals, regardless of which
        // side's field is declared numeric -- previously only a numeric CHILD
        // field got numeric compare, so a char child holding "1" failed
        // against a numeric parent's "1.00". Blank-is-a-value (R16a) is
        // preserved: empty values take the exact string path.
        if (!expected.empty() && !actual.empty()
            && is_numeric_literal(expected) && is_numeric_literal(actual)) {
            try {
                const double e = std::stod(expected);
                const double a = std::stod(actual);
                if (e != a) return false;
            } catch (...) {
                if (actual != expected) return false;
            }
        } else {
            if (actual != expected) return false;
        }
    }
    return true;
}

static bool goto_first_match(xbase::DbArea& child,
                             const std::vector<std::pair<int, std::string>>& kv,
                             std::size_t scan_limit) {
    if (!child.isOpen()) return false;

    const int32_t rec_count = child.recCount();
    if (rec_count <= 0) return false;

    {
        ScopedEngineSelect focus(&child);
        if (!child.top()) return false;
        try { if (!child.readCurrent()) return false; } catch (...) { return false; }
    }

    if (child.recno() <= 0 || child.recno() > rec_count) return false;

    std::size_t scanned = 0;
    for (;;) {
        {
            ScopedEngineSelect focus(&child);
            try { child.readCurrent(); } catch (...) {}
            if (!child.isDeleted() && values_match(child, kv)) return true;

            if (++scanned >= scan_limit) { note_scan_truncated(); return false; }

            const int prev = child.recno();
            if (!child.skip(1)) return false;
            const int next = child.recno();
            if (next <= prev) return false;
            if (next > rec_count) return false;
            try { if (!child.readCurrent()) return false; } catch (...) { return false; }
            const int post = child.recno();
            if (post <= prev) return false;
            if (post > rec_count) return false;
        }
    }
}

static void clear_subtree_to_top(const std::string& parent_name,
                                 std::unordered_set<std::string>& seen,
                                 int depth) {
    if (depth > kRelationDepthCap) {
        note_depth_truncated("clear_subtree_to_top");
        return;
    }
    const std::string key = up_copy(parent_name);
    if (!seen.insert(key).second) return;

    auto it = relations_store().find(key);
    if (it == relations_store().end()) return;

    for (const auto& r : it->second) {
        if (xbase::DbArea* child = find_open_area_in_workspace_ci(
                r.child, xbase::workspace::current_handle(), "REL clear_subtree")) {
            try { child->top(); child->readCurrent(); } catch (...) {}
        }
        clear_subtree_to_top(r.child, seen, depth + 1);
    }
}

// AIF-137, 2026-08-27. EVERY name resolution on the relation path is now
// scoped to the CURRENT workspace.
//
// The store has been partitioned since AIF-078 I1.2 (`relations_store_for`,
// above). The NAMES INSIDE IT WERE NOT, so a refresh standing in one workspace
// resolved its parent -- and its child -- to whichever workspace happened to
// hold the lowest engine slot. Measured live with an EMPTY relation store, so
// it needed no SET RELATION to occur: `infer_parent_from_workarea()` HOLDS the
// area and returns its NAME, and the caller then searched the process and
// found a different one. The round trip lost identity.
//
// ELEVEN SITES, not the two the first reading found and not the six the
// spec drove. COUNTED, after the first draft of this comment said twelve. `REL ADD` resolves both ends
// (:579, :580) and validated against the wrong workspace's areas; the subtree
// walker (:450) and the parent-override reader (:711) do the same. They were
// enumerated by running the spec, which printed a distinct ledger tag for each.
// A grep of this file AFTER those six were scoped found FIVE MORE the spec never
// exercised -- REL matchcount parent/child, REL preview child, REL enum
// parent/child -- all on REPORTING paths. Those are THE COUNT DISCIPLINE: a
// number taken from an authority holding more than one KIND with no
// discriminator applied. They are scoped here too, and they have NO ARM. The
// spec covers ADD, REFRESH and CLEAR only; a future edit could unscope any of
// the reporting five and the suite would stay green. Said plainly rather than
// implied by their absence.
//
// AND ONE MORE THAT IS *NOT* FIXED HERE: `REL LIST ALL` does not use the
// singular resolver at all. It builds a whole map through
// `cli::build_open_area_index_ci()` (see the block above that function's
// former home), which is built on the same UNSCOPED primitive, so a tree
// listing can still walk into another workspace's areas. Scoping an INDEX is a
// different change from scoping a LOOKUP -- the index has no single site to
// filter and its callers expect a complete map -- so it is named here and left.
// It belongs with the wider split, not with this fix.
//
// WHAT IS NOT FIXED HERE, AND IS NAMED RATHER THAN LEFT: the recursion below
// still passes `rel.child` as a STRING after holding the child's `DbArea*` two
// lines earlier, so the next frame resolves the same name again. That is now
// REDUNDANT rather than WRONG -- the scoped resolver returns the same area --
// but not lowering it at all is the deeper fix, and it belongs with the wider
// split of `find_open_area_by_name_ci` into scoped / given-handle /
// explicit-cross across its 36 call sites. That is its own lane.
static void refresh_from_parent_name(const std::string& parent_name,
                                     std::unordered_set<std::string>& seen,
                                     int depth) {
    if (depth > kRelationDepthCap) {
        note_depth_truncated("refresh_from_parent_name");
        return;
    }
    const std::string key = up_copy(parent_name);
    if (!seen.insert(key).second) return;

    xbase::DbArea* parent = find_open_area_in_workspace_ci(
        parent_name, xbase::workspace::current_handle(), "REL refresh parent");
    if (!parent || parent->recno() <= 0) return;

    try { parent->readCurrent(); } catch (...) {}

    auto it = relations_store().find(key);
    if (it == relations_store().end()) return;

    for (const auto& rel : it->second) {
        xbase::DbArea* child = find_open_area_in_workspace_ci(
            rel.child, xbase::workspace::current_handle(), "REL refresh child");
        if (!child) {
            // AIF-149's second silence. An edge whose child the scoped resolver
            // cannot see was skipped with a bare `continue`, so a refresh that
            // propagated down NONE of its edges printed exactly what a complete
            // one printed. Same latch as the caps: all three mean "this
            // traversal is incomplete", they differ only in why.
            note_edge_skipped(key, rel.child);
            continue;
        }

        const auto kv = parent_values(*parent, rel.joins);

        bool found = false;
        try { found = goto_first_match(*child, kv, g_scan_limit); } catch (...) { found = false; }

        if (!found) {
            try { child->top(); child->readCurrent(); } catch (...) {}
            std::unordered_set<std::string> sub_seen;
            clear_subtree_to_top(rel.child, sub_seen, depth + 1);
            continue;
        }

        refresh_from_parent_name(rel.child, seen, depth + 1);
    }
}

// Build FOR expr remains name-based (DbTupleStream uses expressions).
static std::string build_for_expr(const xbase::DbArea* child_db,
                                  const std::vector<std::pair<std::string, std::string>>& kv) {
    std::string expr;
    for (std::size_t i = 0; i < kv.size(); ++i) {
        if (i) expr += " AND ";
        expr += kv[i].first;
        expr += " = ";

        const std::string val = textio::trim(kv[i].second);
        const xbase::FieldDef* fd = child_db ? find_field_def_ci(*child_db, kv[i].first) : nullptr;
        const bool numeric_field = fd && fd->type == 'N';

        if (numeric_field && !val.empty() && is_numeric_literal(val)) {
            expr += val;
        } else {
            expr.push_back('"');
            for (char c : val) {
                if (c == '"') expr += "\"\"";
                else expr.push_back(c);
            }
            expr.push_back('"');
        }
    }
    return expr;
}

// Used ONLY for match_count / preview: derive parent kv as (field_name, value) from HARD bindings.
static std::vector<std::pair<std::string, std::string>>
parent_field_values_names(const xbase::DbArea& parent, const Relation& rel) {
    std::vector<std::pair<std::string, std::string>> out;
    out.reserve(rel.joins.size());
    xbase::DbArea& P = const_cast<xbase::DbArea&>(parent);

    for (std::size_t i = 0; i < rel.joins.size(); ++i) {
        std::string child_field_name;
        if (i < rel.child_names.size()) child_field_name = naked_field(rel.child_names[i]);
        else if (i < rel.names.size()) child_field_name = naked_field(rel.names[i]);
        if (child_field_name.empty()) continue;

        const std::string val = get_by_index_as_string(P, rel.joins[i].parent_field);
        out.emplace_back(child_field_name, val);
    }
    return out;
}

} // namespace

// ==============================
// Public API
// ==============================

namespace relations_api {

void attach_engine(xbase::XBaseEngine* eng) noexcept { g_engine = eng; }

void set_autorefresh(bool on) noexcept { g_autorefresh = on; }
void set_verbose(bool on) noexcept { g_verbose = on; }
void set_scan_limit(std::size_t max_steps) noexcept { g_scan_limit = max_steps ? max_steps : 1; }

// AIF-074 P1.3 (RDB-06 truncation honesty).
void clear_scan_truncated() noexcept { g_scan_truncated = false; }
bool scan_truncated() noexcept { return g_scan_truncated; }
std::size_t scan_limit() noexcept { return g_scan_limit; }

bool add_relation(const std::string& parent_area,
                  const std::string& child_area,
                  const std::vector<std::string>& tuple_fields) {
    return add_relation(parent_area, child_area, tuple_fields, tuple_fields);
}

bool add_relation(const std::string& parent_area,
                  const std::string& child_area,
                  const std::vector<std::string>& parent_fields,
                  const std::vector<std::string>& child_fields) {
    const std::string parent = up_copy(parent_area);
    const std::string child  = up_copy(child_area);

    if (parent_fields.empty() || child_fields.empty()) {
        emit_rel_refusal(dottalk::helpdata::MessageId::RelDiagAddFailedNoFieldsText);
        return false;
    }
    if (parent_fields.size() != child_fields.size()) {
        emit_rel_refusal(dottalk::helpdata::MessageId::RelDiagAddFailedFieldCountMismatchText);
        return false;
    }

    xbase::DbArea* P = find_open_area_in_workspace_ci(
        parent, xbase::workspace::current_handle(), "REL add parent");
    xbase::DbArea* C = find_open_area_in_workspace_ci(
        child, xbase::workspace::current_handle(), "REL add child");
    if (!P || !C) {
        // AIF-149. THE RESOLVER IS SCOPED, SO AN AREA OPEN IN ANOTHER WORKSPACE
        // IS NOT REFUSED -- IT IS INVISIBLE, and this refusal used to report
        // invisibility as absence. Nothing decided that a relation may not cross
        // a workspace; the lookup is scoped and the message inherited its blind
        // spot. Owner 2026-08-30: "I don't think we are saying relations can't
        // exist outside of workspace, even nested, I think we mean we haven't
        // developed it yet." The FEATURE is parked and the gate stays open; this
        // is the hardening half, and it is true whichever way that lands --
        // saying where the boundary is costs nothing and asserts nothing.
        // THIS UNSCOPED LOOKUP REPORTS; IT MUST NEVER RESOLVE. Only wsHandle()
        // is read from it, and the function returns false either way. Using
        // `elsewhere` AS the endpoint would implement the parked feature by
        // accident and would re-open AIF-137, which
        // relation_parent_workspace_crossing.dts exists to keep shut: the
        // relation resolvers were name-addressed and unscoped, so a refresh in
        // one workspace drove another workspace's child. That was fixed by
        // scoping them. Reporting where an area is and reaching it are
        // different acts, and only the first one is safe here.
        const std::string& missing = !P ? parent : child;
        const xbase::DbArea* elsewhere = cli::find_open_area_by_name_ci(missing);
        if (elsewhere) {
            const std::uint64_t h = elsewhere->wsHandle();
            emit_rel_refusal(
                dottalk::helpdata::MessageId::RelDiagAddFailedOpenElsewhereText,
                {{"area", missing},
                 {"workspace", h ? xbase::workspace::name_of(h)
                                 : std::string("(none)")}});
        } else {
            emit_rel_refusal(dottalk::helpdata::MessageId::RelDiagAddFailedNotOpenText);
        }
        return false;
    }

    Relation r;
    r.child = child;
    r.parent_names = parent_fields;
    r.child_names = child_fields;
    if (same_field_lists(parent_fields, child_fields)) r.names = parent_fields;
    r.joins.clear();
    r.joins.reserve(parent_fields.size());

    for (std::size_t i = 0; i < parent_fields.size(); ++i) {
        const std::string pf_name = naked_field(parent_fields[i]);
        const std::string cf_name = naked_field(child_fields[i]);
        const int pf = find_field_index_ci(*P, pf_name);
        const int cf = find_field_index_ci(*C, cf_name);
        if (pf <= 0) {
            emit_rel_refusal(
                dottalk::helpdata::MessageId::RelDiagParentFieldNotFoundText,
                {{"field", pf_name}});
            return false;
        }
        if (cf <= 0) {
            emit_rel_refusal(
                dottalk::helpdata::MessageId::RelDiagChildFieldNotFoundText,
                {{"field", cf_name}});
            return false;
        }
        r.joins.push_back(JoinField{pf, cf});
    }

    auto& v = relations_store()[parent];
    auto it = std::find_if(v.begin(), v.end(), [&](const Relation& x){ return x.child == child; });
    if (it == v.end()) v.push_back(std::move(r));
    else *it = std::move(r);

    const std::string relation_fields =
        same_field_lists(parent_fields, child_fields)
            ? join_names_csv(parent_fields)
            : join_names_csv(parent_fields) + " TO " + join_names_csv(child_fields);
    emit_rel_diag(
        dottalk::helpdata::MessageId::RelDiagAddedText,
        {{"parent", parent}, {"child", child}, {"fields", relation_fields}});

    return true;
}

bool remove_relation(const std::string& parent_area,
                     const std::string& child_area) {
    const std::string parent = up_copy(parent_area);
    const std::string child  = up_copy(child_area);

    auto it = relations_store().find(parent);
    if (it == relations_store().end()) {
        emit_rel_diag(
            dottalk::helpdata::MessageId::RelDiagNoRelationsDefinedText,
            {{"parent", parent}});
        return false;
    }

    auto& vec = it->second;
    const auto old_size = vec.size();

    vec.erase(
        std::remove_if(vec.begin(), vec.end(),
            [&](const Relation& rel) {
                return up_copy(rel.child) == child;
            }),
        vec.end());

    if (vec.size() == old_size) {
        emit_rel_diag(
            dottalk::helpdata::MessageId::RelDiagRelationNotFoundText,
            {{"parent", parent}, {"child", child}});
        return false;
    }

    if (vec.empty()) {
        relations_store().erase(it);
    }

    emit_rel_diag(
        dottalk::helpdata::MessageId::RelDiagRemovedText,
        {{"parent", parent}, {"child", child}});

    return true;
}

void clear_relations(const std::string& parent_area) {
    relations_store().erase(up_copy(parent_area));
    emit_rel_diag(
        dottalk::helpdata::MessageId::RelDiagClearedForText,
        {{"parent", up_copy(parent_area)}});
}

// SCOPED as of I1.2: this clears the CURRENT workspace's relations and leaves
// every other workspace's alone. That is what REL CLEAR ALL has always meant to
// a person -- "clear my relations" -- and before the partition existed there was
// only one workspace for it to mean.
void clear_all_relations() {
    relations_store().clear();
    current_parent_override().clear();
    emit_rel_diag(dottalk::helpdata::MessageId::RelDiagClearedAllText);
}

// Clear ONE named workspace's relations. The close path uses this to clear
// exactly the workspaces it actually closed, instead of clearing the world and
// printing an apology for it.
void clear_all_relations_for(std::uint64_t ws) {
    relations_store_for(ws).clear();
    if (ws == xbase::workspace::current_handle()) current_parent_override().clear();
}

// EVERY workspace. This is what CLOSE ALL and the structural reset paths mean --
// leave nothing anywhere -- and it is now a DELIBERATE choice at those call
// sites rather than the only behaviour available.
void clear_all_relations_everywhere() {
    all_relation_stores().clear();
    current_parent_override().clear();
    emit_rel_diag(dottalk::helpdata::MessageId::RelDiagClearedAllText);
}

void set_current_parent_name(const std::string& logical_name) noexcept {
    current_parent_override() = up_copy(logical_name);
}

std::string current_parent_name() {
    if (!current_parent_override().empty()) {
        if (find_open_area_in_workspace_ci(current_parent_override(),
                                          xbase::workspace::current_handle(),
                                          "REL current parent")) {
            return current_parent_override();
        }
        current_parent_override().clear();
    }
    return infer_parent_from_workarea();
}

void refresh_for_current_parent() noexcept {
    try {
        const std::string parent = current_parent_name();
        if (parent.empty()) return;
        std::unordered_set<std::string> seen;
        refresh_from_parent_name(parent, seen, 0);
    } catch (...) {}
}

void refresh_if_enabled() noexcept { if (g_autorefresh) refresh_for_current_parent(); }

std::vector<std::string> child_areas_for_current_parent() {
    std::vector<std::string> out;
    const auto parent = current_parent_name();
    if (parent.empty()) return out;

    auto it = relations_store().find(up_copy(parent));
    if (it == relations_store().end()) return out;

    out.reserve(it->second.size());
    for (const auto& r : it->second) out.push_back(r.child);
    return out;
}

int match_count_for_child(const std::string& child_area) {
    try {
        const std::string parent = current_parent_name();
        if (parent.empty()) return 0;

        xbase::DbArea* parent_db = find_open_area_in_workspace_ci(
            parent, xbase::workspace::current_handle(), "REL matchcount parent");
        if (!parent_db || parent_db->recno() <= 0) return 0;

        auto it = relations_store().find(up_copy(parent));
        if (it == relations_store().end()) return 0;

        const std::string child = up_copy(child_area);
        auto rit = std::find_if(it->second.begin(), it->second.end(),
                                [&](const Relation& r){ return r.child == child; });
        if (rit == it->second.end()) return 0;

        xbase::DbArea* child_db = find_open_area_in_workspace_ci(
            child, xbase::workspace::current_handle(), "REL matchcount child");
        if (!child_db || !child_db->isOpen()) return 0;

        const int parent_recno = parent_db->recno();
        const int child_start_recno = child_db->recno();

        {
            ScopedEngineSelect focus(parent_db);
            try { parent_db->readCurrent(); } catch (...) {}
        }
        const auto kv = parent_values(*parent_db, rit->joins);

        const int32_t rec_count = child_db->recCount();
        if (rec_count <= 0) return 0;

        int count = 0;
        std::size_t scanned = 0;

        {
            ScopedEngineSelect focus(child_db);
            try { child_db->top(); } catch (...) {}
            try { child_db->readCurrent(); } catch (...) {}

            for (;;) {
                const int cur = child_db->recno();
                if (cur <= 0 || cur > rec_count) break;

                try { child_db->readCurrent(); } catch (...) {}
                if (!child_db->isDeleted() && values_match(*child_db, kv)) ++count;

                if (++scanned >= g_scan_limit) { note_scan_truncated(); break; }

                const int prev = child_db->recno();
                if (!child_db->skip(1)) break;
                const int next = child_db->recno();
                if (next <= prev) break;
                if (next > rec_count) break;
                try { if (!child_db->readCurrent()) break; } catch (...) { break; }
                const int post = child_db->recno();
                if (post <= prev) break;
                if (post > rec_count) break;
            }

            try {
                if (child_start_recno > 0 && child_start_recno <= rec_count) {
                    child_db->gotoRec(child_start_recno);
                    child_db->readCurrent();
                }
            } catch (...) {}
        }

        {
            ScopedEngineSelect focus(parent_db);
            try {
                if (parent_recno > 0) {
                    parent_db->gotoRec(parent_recno);
                    parent_db->readCurrent();
                }
            } catch (...) {}
        }

        return count;
    } catch (...) { return 0; }
}

std::vector<RelationSpec> export_relations() {
    std::vector<RelationSpec> out;
    for (const auto& kv : relations_store()) {
        const std::string& parent = kv.first;
        for (const auto& rel : kv.second) {
            RelationSpec spec;
            spec.parent = parent;
            spec.child = rel.child;
            spec.parent_fields = rel.parent_names;
            spec.child_fields = rel.child_names;
            if (same_field_lists(spec.parent_fields, spec.child_fields)) {
                spec.fields = spec.parent_fields;
            }
            out.push_back(std::move(spec));
        }
    }
    return out;
}

void import_relations(const std::vector<RelationSpec>& specs, bool clear_existing) {
    if (clear_existing) relations_store().clear();
    for (const auto& s : specs) {
        if (!s.parent_fields.empty() || !s.child_fields.empty()) {
            add_relation(s.parent, s.child, s.parent_fields, s.child_fields);
        } else {
            add_relation(s.parent, s.child, s.fields);
        }
    }
}

// ---- Accurate REL LIST ALL support helpers (internal) ----

// AIF-120 I1.3a: DELETED, and deliberately not replaced in kind.
//
// This function built its own UPPER-name -> area map with `out[key] = a`, an
// unconditional assign, which made it LAST-match-wins: with two open areas
// named STUDENTS it handed back the HIGHER slot, while
// find_open_area_by_name_ci() -- then the resolver every other REL path used,
// and since AIF-137 replaced on this path by its workspace-scoped variant --
// returned the LOWER one. Two resolvers, one question, different answers, and
// neither said which area it had picked. R112 sec 3 measured twelve basenames
// shared across the x64/x32/vfp roots, so the collision is the demo corpus,
// not a corner case.
//
// The map now comes from cli::build_open_area_index_ci(), which is built on the
// same primitive as the singular resolver. They agree by construction. Anyone
// re-adding a local index here re-opens the divergence.

static std::vector<std::string> infer_unique_child_chain(const std::string& root_up, int max_depth) {
    std::vector<std::string> chain;
    if (max_depth <= 0) return chain;

    std::unordered_set<std::string> seen;
    seen.insert(root_up);

    std::string cur = root_up;
    for (int depth = 1; depth <= max_depth; ++depth) {
        auto it = relations_store().find(cur);
        if (it == relations_store().end() || it->second.empty()) break;

        if (it->second.size() != 1) break;

        const std::string child = up_copy(it->second.front().child);
        if (child.empty() || seen.count(child)) break;

        chain.push_back(child);
        seen.insert(child);
        cur = child;
    }

    return chain;
}

static std::string format_on_fields(const Relation& rel) {
    if (!rel.parent_names.empty() && !rel.child_names.empty()) {
        std::string s = " ON ";
        s += join_names_csv(rel.parent_names);
        if (!same_field_lists(rel.parent_names, rel.child_names)) {
            s += " TO ";
            s += join_names_csv(rel.child_names);
        }
        return s;
    }

    if (!rel.names.empty()) {
        std::string s = " ON ";
        s += join_names_csv(rel.names);
        return s;
    }
    return {};
}

// ---- SURGICALLY REPLACED: list_tree_for_current_parent ----

std::vector<PreviewRow> list_tree_for_current_parent(bool recursive, int max_depth) {
    std::vector<PreviewRow> out;

    const std::string root = up_copy(current_parent_name());
    if (root.empty()) return out;

    out.push_back(PreviewRow{root});

    if (!recursive || max_depth <= 0) {
        auto it = relations_store().find(root);
        if (it == relations_store().end()) return out;

        for (const auto& rel : it->second) {
            std::string line(2u, ' ');
            line += "-> ";
            line += rel.child;
            line += format_on_fields(rel);

            int cnt = 0;
            try { cnt = match_count_for_child(rel.child); } catch (...) {}
            line += "  (matches: ";
            line += std::to_string(cnt);
            line += ")";

            out.push_back(PreviewRow{std::move(line)});
        }
        return out;
    }

    const auto area_by = cli::build_open_area_index_ci();
    const auto chain_children = infer_unique_child_chain(root, max_depth);

    std::vector<std::string> chain_names;
    chain_names.reserve(1 + chain_children.size());
    chain_names.push_back(root);
    for (const auto& c : chain_children) chain_names.push_back(c);

    std::unordered_map<std::string, std::unordered_set<int32_t>> distinct_recnos;
    distinct_recnos.reserve(chain_names.size() * 2);

    if (auto itA = area_by.find(root); itA != area_by.end() && itA->second && itA->second->isOpen()) {
        distinct_recnos[root].insert(itA->second->recno());
    }

    (void)enum_emit_for_current_parent(
        chain_children,
        0,
        [&] {
            for (const auto& nm : chain_names) {
                auto it = area_by.find(nm);
                if (it == area_by.end()) continue;
                xbase::DbArea* a = it->second;
                if (!a || !a->isOpen()) continue;
                distinct_recnos[nm].insert(a->recno());
            }
        },
        nullptr
    );

    auto get_distinct_count = [&](const std::string& up_name) -> int {
        auto it = distinct_recnos.find(up_name);
        if (it == distinct_recnos.end()) return -1;
        return static_cast<int>(it->second.size());
    };

    std::unordered_set<std::string> path;
    path.insert(root);

    std::function<void(const std::string&, int)> dfs;
    dfs = [&](const std::string& parent_up, int depth) {
        if (depth > max_depth) return;

        auto it = relations_store().find(parent_up);
        if (it == relations_store().end() || it->second.empty()) return;

        for (const auto& rel : it->second) {
            const std::string child_up = up_copy(rel.child);

            std::string line(static_cast<std::size_t>(depth) * 2u, ' ');
            line += "-> ";
            line += rel.child;
            line += format_on_fields(rel);

            int cnt = get_distinct_count(child_up);
            if (cnt >= 0) {
                line += "  (matches: ";
                line += std::to_string(cnt);
                line += ")";
            } else if (depth == 1) {
                int c1 = 0;
                try { c1 = match_count_for_child(rel.child); } catch (...) {}
                line += "  (matches: ";
                line += std::to_string(c1);
                line += ")";
            } else {
                line += "  (matches: n/a)";
            }

            out.push_back(PreviewRow{std::move(line)});

            if (child_up.empty() || path.count(child_up)) continue;
            path.insert(child_up);
            dfs(child_up, depth + 1);
            path.erase(child_up);
        }
    };

    dfs(root, 1);
    return out;
}

std::vector<relations_api::PreviewRow> preview_child(const std::string& child_area, int limit) {
    if (limit <= 0) return {};
    std::vector<PreviewRow> out;
    try {
        const auto parent = current_parent_name();
        if (parent.empty()) return out;

        const xbase::DbArea* A = workareas::db(workareas::current_slot());
        if (!A || A->recno() <= 0) return out;

        try { const_cast<xbase::DbArea*>(A)->readCurrent(); } catch (...) {}

        auto it = relations_store().find(up_copy(parent));
        if (it == relations_store().end()) return out;

        const std::string child = up_copy(child_area);
        auto rit = std::find_if(it->second.begin(), it->second.end(),
                                [&](const Relation& r){ return r.child == child; });
        if (rit == it->second.end()) return out;

        const xbase::DbArea* child_db = find_open_area_in_workspace_ci(
            child, xbase::workspace::current_handle(), "REL preview child");

        auto kv = parent_field_values_names(*A, *rit);
        const std::string for_expr = build_for_expr(child_db, kv);

        dottalk::DbTupleStream ts(child + ".*", "");
        ts.set_filter_for(for_expr);
        ts.top();

        const auto tuples = ts.next_page(static_cast<std::size_t>(limit));
        for (const auto& tr : tuples) {
            std::string line;
            for (std::size_t i = 0; i < tr.columns.size() && i < tr.values.size(); ++i) {
                if (i) line += " | ";
                line += tr.columns[i].name;
                line += "=";
                line += tr.values[i].empty() ? "\"\"" : tr.values[i];
            }
            out.push_back(PreviewRow{ std::move(line) });
        }
    } catch (...) {}
    return out;
}

namespace {

static std::vector<std::string> infer_unique_chain_from_parent(const std::string& parent_up) {
    std::vector<std::string> chain;
    std::string cur = parent_up;
    for (int depth = 0; depth < 32; ++depth) {
        auto it = relations_store().find(cur);
        if (it == relations_store().end()) break;
        if (it->second.empty()) break;
        if (it->second.size() != 1) return {};
        const std::string& child = it->second[0].child;
        chain.push_back(child);
        cur = child;
    }
    return chain;
}

static bool enum_chain_dfs(
    const std::vector<std::string>& chain_children,
    std::size_t idx,
    const std::function<void()>& emit,
    std::size_t max_rows,
    std::size_t* emitted,
    const std::string& parent_up) {

    if (!emitted) return false;
    if (idx >= chain_children.size()) {
        emit();
        ++(*emitted);
        return true;
    }

    xbase::DbArea* parent_db = find_open_area_in_workspace_ci(
        parent_up, xbase::workspace::current_handle(), "REL enum parent");
    const std::string child_up = up_copy(chain_children[idx]);
    xbase::DbArea* child_db = find_open_area_in_workspace_ci(
        child_up, xbase::workspace::current_handle(), "REL enum child");
    if (!parent_db || !child_db) return false;

    auto it = relations_store().find(parent_up);
    if (it == relations_store().end()) return false;
    auto rit = std::find_if(it->second.begin(), it->second.end(),
                            [&](const Relation& r){ return r.child == child_up; });
    if (rit == it->second.end()) return false;

    {
        ScopedEngineSelect focus(parent_db);
        try { parent_db->readCurrent(); } catch (...) {}
    }

    const auto kv = parent_values(*parent_db, rit->joins);

    const int32_t rec_count = child_db->recCount();
    if (rec_count <= 0) return true;

    {
        ScopedEngineSelect focus(child_db);
        try { child_db->top(); } catch (...) { return false; }
        try { child_db->readCurrent(); } catch (...) {}
    }

    if (child_db->recno() <= 0 || child_db->recno() > rec_count) return true;

    std::size_t scanned = 0;
    for (; scanned < g_scan_limit; ++scanned) {
        ScopedEngineSelect focus(child_db);

        const int cur = child_db->recno();
        if (cur <= 0 || cur > rec_count) break;

        try { child_db->readCurrent(); } catch (...) {}

        const bool matched = (!child_db->isDeleted() && values_match(*child_db, kv));
        const int match_recno = child_db->recno();

        if (matched) {
            if (!enum_chain_dfs(chain_children, idx + 1, emit, max_rows, emitted, child_up)) {
                return false;
            }
            if (max_rows != 0 && *emitted >= max_rows) return true;

            try {
                child_db->gotoRec(match_recno);
                child_db->readCurrent();
            } catch (...) {}
        }

        const int prev_recno = child_db->recno();
        if (!child_db->skip(1)) break;

        const int next_recno = child_db->recno();
        if (next_recno <= prev_recno) break;
        if (next_recno > rec_count) break;

        try { if (!child_db->readCurrent()) break; } catch (...) { break; }
        const int post_read_recno = child_db->recno();
        if (post_read_recno <= prev_recno) break;
        if (post_read_recno > rec_count) break;
    }

    // AIF-074 P1.3 (RDB-06): natural loop exit means the scan limit stopped
    // the enumeration, not end-of-table -- say so.
    if (scanned >= g_scan_limit) note_scan_truncated();

    return true;
}

} // anonymous namespace

bool enum_emit_for_current_parent(const std::vector<std::string>& path_children,
                                  std::size_t max_rows,
                                  const std::function<void()>& emit,
                                  std::size_t* rows_emitted) {
    if (rows_emitted) *rows_emitted = 0;

    // Non-invasive: enumeration should not disturb current record pointers.
    // We snapshot all open work areas and restore them on exit.
    WorkAreaStateGuard preserve;

    try {
        const std::string parent = current_parent_name();
        if (parent.empty()) return false;

        const std::string parent_up = up_copy(parent);
        std::vector<std::string> chain = path_children;
        if (chain.empty()) {
            chain = infer_unique_chain_from_parent(parent_up);
            if (chain.empty()) {
                return false;
            }
        }

        std::size_t emitted = 0;
        if (!enum_chain_dfs(chain, 0, emit, max_rows, &emitted, parent_up)) {
            if (rows_emitted) *rows_emitted = emitted;
            return false;
        }
        if (rows_emitted) *rows_emitted = emitted;
        return true;
    } catch (...) {
        return false;
    }
}

} // namespace relations_api
