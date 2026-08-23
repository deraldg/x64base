// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_use.cpp
// DotTalk++ USE command (open DBF in a work area) -- duplicate-open guard, NOINDEX, auto-attach

// @dottalk.usage v1
// owner: DOT|USE
// command: USE
// category: workspace
// status: supported
// noargs: usage
// effect: session
// mutates: session area order memo index
// usage-access: USE USAGE
// summary:
//   Open a DBF table into the current work area, with duplicate-open guard,
//   memo auto-attach, optional index auto-attach, and NOINDEX physical-order mode.
//
// usage:
//   USE USAGE
//   USE <table>
//   USE <table.dbf>
//   USE <path\table.dbf>
//   USE <table> NOINDEX
//   USE <table> NOIDX
//   USE <table> AGAIN
//   USE <table> IN <n>
//   USE <table> IN FREE
//
// notes:
//   USE requires a table name or path; no usable argument shows usage.
//   USE REFUSES arguments it does not recognize, by name (AIF-121). It used to
//   ignore them and open into the current area anyway, which destroyed that
//   area's occupant silently -- the reason IN <n> exists here at all.
//   IN <n> opens into area n and does NOT change the current area. IN FREE
//   takes the lowest unoccupied area, and refuses rather than falling back
//   when there is none.
//   The USAGE text rendered by print_use_usage() comes from the message
//   catalog and does not yet list IN; the catalog is owned by the full-stack
//   document push and is OWED this line. The refusal path prints the correct
//   syntax inline meanwhile.
//   Relative logical names resolve through the configured DBF path slot.
//   USE prevents duplicate opens of the same DBF path across work areas,
//   and names the AGAIN arm in the refusal.
//   AGAIN opens a SECOND work area on an already-open DBF (workspace design
//   I5, v1). The second instance is writable -- record locking arbitrates,
//   per the multi-user model -- and opens in PHYSICAL ORDER: index
//   auto-attach is suppressed because a second in-process attach of the same
//   container would double-open one LMDB environment (undefined behaviour).
//   AGAIN is REFUSED on tables carrying memo fields: two sidecar writers
//   would interleave appends. Both relaxations are later, separately-gated
//   arms. Proof: REGRESSION RUN USE_AGAIN.
//   USE clears stale order/tag/container state and closes the current area before opening the new DBF.
//   USE opens the target DBF and populates DbArea metadata.
//   USE auto-attaches memo storage when memo fields are present.
//   USE auto-attaches flavor-appropriate indexes when present, unless NOINDEX/NOIDX is specified.
//   USE prefers the configured INDEXES slot and falls back to the DBF directory.
//   NOINDEX/NOIDX opens the table in physical order and skips index auto-attach.
//   USE is a session/area mutation command; it changes the current work area binding but should not mutate table records.
//
// risk:
//   opens_files: yes
//   closes_current_area: yes
//   clears_order_state: yes
//   attaches_memo: when memo fields are present
//   attaches_index: flavor-appropriate index when present unless NOINDEX/NOIDX
//   duplicate_open_guard: yes
//   writes_dbf_records: no
//   deletes_files: no
//   creates_files: no
//
// related:
//   CLOSE
//   WORKSPACE
//   SETPATH
//   SET ORDER
//   SET INDEX
//   STRUCT
//   DBAREA
//

#include <sstream>
#include <string>
#include <filesystem>
#include <algorithm>
#include <cctype>
#include <type_traits>
#include <vector>

#include "workarea_util.hpp"
#include "xbase.hpp"
#include "xbase/workspace_membership.hpp"   // IN FREE is workspace-scoped (AIF-121)
#include "xbase_64.hpp"
#include "xbase/area_kind_util.hpp"
#include "cli/command_output.hpp"
#include "cli/table_state.hpp"   // crash recovery of the table-buffer .tbj journal
#include "cli/order_state.hpp"
#include "cli/order_hooks.hpp"      // to run reconcile_after_mutation()
#include "cli/cmd_setpath.hpp"
#include "cli/path_resolver.hpp"
#include "help/helpdata_messages.hpp"
#include "memo/memo_auto.hpp"
#if DOTTALK_HAS_XINDEX
#include "xindex/index_manager.hpp"
#include "xindex/attach.hpp"
#include "cdx/cdx.hpp"
#include "cnx/cnx.hpp"              // reporting helper (CNX is deprecated but still supported)
#endif

using namespace xbase;
namespace fs = std::filesystem;

// --- engine access (why: scan all areas to prevent duplicate opens) ---
extern "C" xbase::XBaseEngine* shell_engine();

namespace {

// ----------------------- path & env helpers ---------------------------------

static fs::path find_data_root_guess()
{
    fs::path p = fs::current_path();
    for (int i = 0; i < 14; ++i) {
        fs::path cand = p / "data";
        if (fs::exists(cand) && fs::is_directory(cand)) {
            return fs::absolute(cand);
        }
        if (!p.has_parent_path()) break;
        fs::path parent = p.parent_path();
        if (parent == p) break;
        p = parent;
    }
    return fs::absolute(fs::current_path());
}

static void ensure_setpath_initialized()
{
    using dottalk::paths::state;
    using dottalk::paths::init_defaults;
    using dottalk::paths::Slot;
    using dottalk::paths::get_slot;

    if (state().data_root.empty()) {
        init_defaults(find_data_root_guess());
        return;
    }
    if (get_slot(Slot::DBF).empty() || get_slot(Slot::INDEXES).empty()) {
        init_defaults(state().data_root);
    }
}

static bool looks_explicit_path(const std::string& s)
{
    if (s.find('/')  != std::string::npos) return true;
    if (s.find('\\') != std::string::npos) return true;
    if (s.size() >= 2 && std::isalpha((unsigned char)s[0]) && s[1] == ':') return true;
    if (!s.empty() && s[0] == '.') return true;
    return false;
}

static std::string strip_dbf_ext_if_present(std::string s)
{
    auto up = [](unsigned char c){ return (char)std::toupper(c); };
    if (s.size() >= 4) {
        const char a = up((unsigned char)s[s.size()-4]);
        const char b = up((unsigned char)s[s.size()-3]);
        const char c = up((unsigned char)s[s.size()-2]);
        const char d = up((unsigned char)s[s.size()-1]);
        if (a=='.' && b=='D' && c=='B' && d=='F') {
            s.resize(s.size()-4);
        }
    }
    return s;
}

static std::string up_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return (char)std::toupper(c); });
    return s;
}

// ---------------------------------------------------------------------------
// USE argument parsing (AIF-121).
//
// WHAT THIS REPLACED, AND WHY THE SHAPE MATTERED MORE THAN THE MISSING CHECK.
// This file used to read its tail with THREE independent non-consuming scans --
// contains_noindex, contains_again, parse_alias_clause. Each saved the stream
// position, swept forward looking for its own keyword, and rewound. Nothing
// ever enumerated the tail as a whole, so NO TOKEN WAS EVER UNACCOUNTED FOR.
//
// Unknown arguments were therefore not ignored by oversight. Nothing was in a
// position to notice them. `USE students IN 1` parsed as `USE students` with
// two tokens quietly dropped on the floor, and the table opened into the
// CURRENT area -- destroying whatever occupied it, with no message. Measured
// 2026-08-22: two USE commands, two "Opened" lines, WORKSPACE REGISTRY
// reporting members 1.
//
// So the fix is not a check bolted onto three scanners. It is ONE PASS that
// CONSUMES every token and classifies it, with a final else that refuses by
// name. The gate cannot be forgotten afterwards, because the parser is
// required to account for every token it is handed; a fifth clause added later
// cannot reopen the hole by omission.
//
// This is the house rule stated 2026-08-22 -- "all commands and functions
// should validate field names" -- one level out: validate ARGUMENTS.
struct UseTail {
    bool        again           = false;
    bool        noindex         = false;
    std::string alias;
    bool        alias_malformed = false;

    // IN <n> | IN FREE. `have_in` says the clause appeared at all, which is
    // what separates "not asked for" from "asked for and unusable" -- the
    // distinction parse_alias_clause already had to learn for ALIAS.
    bool        have_in         = false;
    bool        in_free         = false;
    long long   in_area         = -1;

    std::string unknown;    // first unrecognized token, verbatim for the message
    std::string in_problem;  // IN present but its argument missing or unusable
};

static bool token_is_all_digits(const std::string& s) {
    if (s.empty()) return false;
    for (const char c : s) {
        if (c < '0' || c > '9') return false;
    }
    return true;
}

// Consumes the stream to exhaustion. Every token lands in exactly one bucket,
// including the reject bucket -- that totality is the whole point.
static UseTail parse_use_tail(std::istringstream& iss)
{
    UseTail t;
    std::string tok;

    while (iss >> tok) {
        const std::string u = up_copy(tok);

        if (u == "NOINDEX" || u == "NOIDX") { t.noindex = true; continue; }
        if (u == "AGAIN")                   { t.again   = true; continue; }

        if (u == "ALIAS") {
            std::string nm;
            if (iss >> nm) t.alias = nm;
            else           t.alias_malformed = true;
            continue;
        }

        if (u == "IN") {
            t.have_in = true;
            std::string arg;
            if (!(iss >> arg)) {
                t.in_problem = "IN requires an area number or FREE";
                continue;
            }
            const std::string au = up_copy(arg);
            if (au == "FREE") { t.in_free = true; continue; }

            // Digits only, deliberately: std::stoll would accept "3junk" and
            // return 3, which is the same longest-valid-prefix trap that let
            // AIF-116 read pid=16,984 as 16. An area number is either a number
            // or it is a mistake worth naming.
            if (!token_is_all_digits(arg)) {
                t.in_problem = "IN expects an area number or FREE, not '" + arg + "'";
                continue;
            }
            try {
                t.in_area = std::stoll(arg);
            } catch (...) {
                t.in_problem = "IN area number out of range: '" + arg + "'";
            }
            continue;
        }

        // THE LINE THIS WHOLE STRUCTURE EXISTS FOR. Anything unclassified is
        // reported by name rather than dropped. First one wins; naming one
        // token the caller can see beats a count they cannot act on.
        if (t.unknown.empty()) t.unknown = tok;
    }

    return t;
}

static std::string trim_copy_use(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

static bool is_use_usage_request(std::string raw)
{
    std::string t = up_copy(trim_copy_use(std::move(raw)));

    // Most dispatch paths pass only the command tail ("USAGE"), but accept
    // full raw input too ("USE USAGE") so this path remains robust.
    if (t.rfind("USE ", 0) == 0) {
        t = trim_copy_use(t.substr(4));
    }

    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_use_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::UseUsageText);
}


static void clear_order_best_effort(DbArea& a)
{
    // why: ensure physical order if requested or before retargeting area state
    try {
        orderstate::clearOrder(a);
        return;
    } catch (...) {}

    try {
        orderstate::setOrder(a, std::string{});
        return;
    } catch (...) {}
}

// Full per-area reset before opening a new table.
// why:
//   - clear stale order/tag/container state
//   - detach backend/index manager while old DbArea state is still valid
//   - leave the area sterile before opening the next DBF
static void reset_area_runtime_best_effort(DbArea& a)
{
    try {
        clear_order_best_effort(a);
    } catch (...) {}

    try {
        a.close();
    } catch (...) {}
}

// ----------------------- SFINAE setters (optional APIs) ---------------------

template <typename T>
using has_setFilename_t = decltype(std::declval<T&>().setFilename(std::declval<std::string>()));
template <typename T, typename = has_setFilename_t<T>>
static inline void _setFilename(T& a, const std::string& s, int) { a.setFilename(s); }
template <typename T>
static inline void _setFilename(T&, const std::string&, long) {}

template <typename T>
using has_setLogicalName_t = decltype(std::declval<T&>().setLogicalName(std::declval<std::string>()));
template <typename T, typename = has_setLogicalName_t<T>>
static inline void _setLogicalName(T& a, const std::string& s, int) { a.setLogicalName(s); }
template <typename T>
static inline void _setLogicalName(T&, const std::string&, long) {}

template <typename T>
using has_setName_t = decltype(std::declval<T&>().setName(std::declval<std::string>()));
template <typename T, typename = has_setName_t<T>>
static inline void _setLegacyName(T& a, const std::string& s, int) { a.setName(s); }
template <typename T>
static inline void _setLegacyName(T&, const std::string&, long) {}

// ----------------------- area/find helpers ----------------------------------

static inline std::string s8(const fs::path& p) {
#if defined(_WIN32)
    auto u = p.u8string(); return std::string(u.begin(), u.end());
#else
    return p.string();
#endif
}

static fs::path canonicalish(const fs::path& p) {
    try { return fs::weakly_canonical(p); }
    catch (...) { return fs::absolute(p); }
}

static std::string path_key(const fs::path& p) {
    std::string s = s8(canonicalish(p));
#if defined(_WIN32)
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return (char)std::tolower(c); });
#endif
    return s;
}

static int area_slot_of(DbArea& a) {
    // AIF-120 I1.1 sweep completed 2026-08-22 (AIF-078 GUI design sec 8, O5).
    // This was a MAX_AREA pointer-identity scan. The engine stamps the same
    // number into DbArea::_engine_slot once at construction, so the scan
    // recovered a value the area already carried. Body only -- the signature
    // and every call site are unchanged, which is how I1.1 did it.
    return cli::slot_of_area(&a);
}

// The workspace-local slot of an area, 0-based. THE FIRST READER of
// DbArea::_ws_local_slot, which has had three writers and none of these since
// AIF-078 stage 1 landed it five days ago -- my own AIF-079 instance, closed
// here rather than catalogued again.
static int workspace_area_slot_of(const DbArea& a) {
    return a.wsLocalSlot();   // -1 when the area belongs to no workspace
}

static bool area_is_open_safe(xbase::XBaseEngine* eng, int slot) {
    if (!eng || slot < 0 || slot >= xbase::MAX_AREA) return true;  // treat unknown as taken
    try { return eng->area(slot).isOpen(); } catch (...) { return true; }
}

// IN FREE -- an unoccupied area, chosen for THIS WORKSPACE.
//
// NAMED FREE AND NOT NEXT (owner ruling 2026-08-22): NEXT implies forward
// adjacency and this may return a slot BEHIND the cursor. A name that promises
// an order the code does not keep is worse than no name.
//
// WORKSPACE-SCOPED, AND THAT IS THE POINT (owner ruling 2026-08-22, "scoped").
// The first cut swept 0..MAX_AREA globally, which with one workspace open is
// indistinguishable from correct and stops being so the moment there are two:
// a global sweep hands out the lowest free ENGINE slot, and that slot can sit
// INSIDE ANOTHER WORKSPACE'S RUN. The owner's design rule for this lane is
// that a workspace's areas stay contiguous -- "keep the areas contiguous",
// fractal to the same rule for tables under one root -- so an allocator that
// can drop an area into the middle of a neighbour's block is a contiguity
// violation armed and waiting for stage 4.
//
// So: GROW MY OWN BLOCK FIRST. If this workspace already holds areas, the
// slot after its highest member keeps the run unbroken. Only when that is
// taken do we fall back to the lowest free slot anywhere -- and we SAY SO,
// because a silently broken invariant is the shape this whole lane exists to
// remove. `broke_contiguity` carries that fact back to the caller rather than
// printing from down here, so the message lands with the rest of USE's output.
static int find_free_area_for_current_workspace(bool& broke_contiguity) {
    broke_contiguity = false;
    auto* eng = shell_engine(); if (!eng) return -1;

    const std::uint64_t h   = xbase::workspace::current_handle();
    const auto          mem = xbase::workspace::members(h);

    int highest = -1;
    for (const auto slot : mem) {
        if (slot > highest) highest = static_cast<int>(slot);
    }

    // Contiguous growth: the slot immediately after my highest member.
    if (highest >= 0 && highest + 1 < xbase::MAX_AREA) {
        if (!area_is_open_safe(eng, highest + 1)) return highest + 1;
    }

    // Fallback. Reached when my block is boxed in, or when this workspace
    // holds nothing yet and is therefore starting one.
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (!area_is_open_safe(eng, i)) {
            broke_contiguity = (highest >= 0);
            return i;
        }
    }
    return -1;
}

static int find_open_area_for_path(const fs::path& dbf_path) {
    auto* eng = shell_engine(); if (!eng) return -1;
    const std::string target = path_key(dbf_path);
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        try {
            DbArea& A = eng->area(i);
            std::string fn = A.filename();
            if (fn.empty()) continue;
            if (path_key(fn) == target) return i;
        } catch (...) { /* ignore bad slot */ }
    }
    return -1;
}

// `alias` is the name this INSTANCE answers to. Empty means "use the file
// stem", which is the historic behaviour and stays the default.
//
// It lands in _logical_name deliberately: that is the field
// find_open_area_by_name_ci() actually compares (workarea_util.cpp:29), so an
// alias becomes addressable with no change at that function's 18 call sites.
//
// Measured 2026-08-12, and all three are stubs the owner correctly guessed
// were meant for exactly this:
//   _db_name          -- 3 writers (xbase.hpp:297, dbarea.cpp:128,205), ZERO
//                        readers anywhere in the tree. A write-only member.
//   _setLegacyName()  -- DbArea has no setName(), so this SFINAE wrapper
//                        selects its empty fallback and has ALWAYS been a
//                        silent no-op, under a comment reading "legacy alias".
//   AREA's two lines  -- "Logical name" and "Legacy name()" both render
//                        _logical_name, which is why they always agree.
// The table-name-vs-alias split those fields were shaped for needs a setter
// and accessor on DbArea; xbase.hpp is a wide include, so that is priced
// separately rather than smuggled in here.
// An alias must be reachable as a NAME. A purely numeric one would not be:
// SELECT reads a digit string as an AREA NUMBER, so alias "3" would silently
// select slot 3 instead of the table -- addressable in theory, wrong in fact.
static bool alias_is_addressable(const std::string& s)
{
    if (s.empty()) return false;
    for (char c : s) {
        if (!std::isdigit(static_cast<unsigned char>(c))) return true;
    }
    return false;
}

// Slot holding `alias`, ignoring `except_slot` (the area being opened into).
static int find_open_area_by_alias(const std::string& alias, int except_slot)
{
    auto* eng = shell_engine(); if (!eng) return -1;
    const std::string target = up_copy(alias);
    if (target.empty()) return -1;

    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (i == except_slot) continue;
        try {
            DbArea& A = eng->area(i);
            if (!A.isOpen()) continue;
            if (up_copy(A.logicalName()) == target) return i;
        } catch (...) { /* ignore bad slot */ }
    }
    return -1;
}

// STUDENTS taken -> STUDENTS2, STUDENTS3, ... Deterministic and announced;
// never silent. Returns empty if it somehow cannot find a free name, which
// the caller treats as a refusal rather than opening unaddressably.
static std::string derive_distinct_alias(const std::string& stem, int except_slot)
{
    for (int n = 2; n <= 999; ++n) {
        std::string cand = stem + std::to_string(n);
        if (find_open_area_by_alias(cand, except_slot) < 0) return cand;
    }
    return {};
}

static void populate_dbarea_metadata(DbArea& a, const fs::path& dbf_path,
                                     const std::string& alias) {
    const std::string abs = fs::absolute(dbf_path).string();
    const std::string stem = dbf_path.stem().string();
    const std::string addressable = alias.empty() ? stem : alias;
    _setFilename(a, abs, 0);            // SCHEMAS uses filename() as truth
    _setLogicalName(a, addressable, 0); // the name this instance answers to
    _setLegacyName(a, addressable, 0);  // no-op today; see the note above
}

// ----------------------- CNX uniqueness (reporting only) --------------------

#if DOTTALK_HAS_XINDEX
static constexpr uint32_t TAGF_UNIQUE = 0x0001; // adjust if your CNX uses a different bit

static bool cnx_tag_is_unique(const std::string& cnx_path, const std::string& tag_upper)
{
    if (cnx_path.empty() || tag_upper.empty()) return false;

    cnxfile::CNXHandle* h = nullptr;
    if (!cnxfile::open(cnx_path, h)) return false;

    std::vector<cnxfile::TagInfo> tags;
    const bool ok = cnxfile::read_tagdir(h, tags);
    cnxfile::close(h);

    if (!ok) return false;

    for (const auto& t : tags) {
        if (up_copy(t.name) == up_copy(tag_upper)) {
            return (t.flags & TAGF_UNIQUE) != 0;
        }
    }
    return false;
}

static bool cdx_tag_is_unique(const std::string& cdx_path, const std::string& tag_upper)
{
    if (cdx_path.empty() || tag_upper.empty()) return false;

    cdxfile::CDXHandle* h = nullptr;
    if (!cdxfile::open(cdx_path, h)) return false;

    std::vector<cdxfile::TagInfo> tags;
    const bool ok = cdxfile::read_tagdir(h, tags);
    cdxfile::close(h);

    if (!ok) return false;

    for (const auto& t : tags) {
        if (up_copy(t.name) == up_copy(tag_upper)) {
            return (t.flags & TAGF_UNIQUE) != 0;
        }
    }
    return false;
}
#endif

static bool is_v32_area(const DbArea& a)
{
    return a.kind() == AreaKind::V32;
}

static bool is_x64_cdx_area(const DbArea& a)
{
    return a.versionByte() == xbase::DBF_VERSION_64 || a.kind() == AreaKind::V128;
}

static bool is_classic_tag_area(const DbArea& a)
{
    return is_v32_area(a) || (a.kind() == AreaKind::V64 && a.versionByte() != xbase::DBF_VERSION_64);
}

#if DOTTALK_HAS_XINDEX
static bool file_exists_best_effort(const fs::path& p)
{
    std::error_code ec;
    return fs::exists(p, ec) && !ec && fs::is_regular_file(p, ec) && !ec;
}

static std::vector<fs::path> auto_attach_candidates_for(const DbArea& a,
                                                        const fs::path& dbf_path)
{
    std::vector<fs::path> out;

    const fs::path opened_abs = fs::absolute(dbf_path);
    const fs::path dbf_dir = opened_abs.parent_path();
    const fs::path idx_root = dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES);
    const std::string base = opened_abs.stem().string();

    auto add = [&](const fs::path& p) {
        if (!p.empty()) out.push_back(p);
    };

    if (is_x64_cdx_area(a)) {
        add(idx_root / (base + ".cdx"));
        add(dbf_dir / (base + ".cdx"));
        return out;
    }

    if (is_classic_tag_area(a)) {
        add(idx_root / (base + ".cnx"));
        add(idx_root / (base + ".inx"));
        add(dbf_dir / (base + ".cnx"));
        add(dbf_dir / (base + ".inx"));
        return out;
    }

    return out;
}

static bool activate_tag_container_for_use(DbArea& a,
                                           const fs::path& container_path,
                                           std::string& active_tag_out)
{
    active_tag_out.clear();

    try {
        xindex::ensure_manager(a).close();
    } catch (...) {
    }

    orderstate::clearOrder(a);
    orderstate::setOrder(a, container_path.string());
    orderstate::setAscending(a, true);
    orderhooks::reconcile_after_mutation(a);

    active_tag_out = orderstate::activeTag(a);
    if (active_tag_out.empty()) {
        orderstate::clearOrder(a);
        return false;
    }

    std::string err;
    const std::string ext = up_copy(container_path.extension().string());
    bool ok = false;

    if (ext == ".CDX") {
        ok = xindex::ensure_manager(a).openCdx(container_path.string(), active_tag_out, &err);
    } else if (ext == ".CNX") {
        ok = xindex::ensure_manager(a).openCnx(container_path.string(), active_tag_out, &err);
    }

    if (!ok) {
        try {
            xindex::ensure_manager(a).close();
        } catch (...) {
        }
        orderstate::clearOrder(a);
        active_tag_out.clear();
        return false;
    }

    return true;
}
#endif

// ----------------------- flavor / valid-index helpers -----------------------

// Current policy helper.
// If policy changes later (for example LMDB-backed CDX also allowed for v32),
// change this function only.
static const char* valid_index_types_for(const DbArea& a)
{
#if !DOTTALK_HAS_XINDEX
    (void)a;
    return "none (table-only build)";
#else
    // CNX-on-x64 (AIF-099, owner ruling 2026-08-09): explicit CNX is now
    // accepted on x64 tables (advisory path); CDX/LMDB remains preferred.
    if (is_x64_cdx_area(a)) return "CDX, CNX";
    if (is_classic_tag_area(a)) return "CNX, INX";
    switch (a.kind()) {
    case AreaKind::Tup:  return "TUP";
    case AreaKind::Unknown:
    default:             return "(unknown)";
    }
#endif
}

static std::string open_display_name(const DbArea& a, const fs::path& dbf_path)
{
    if (!a.logicalName().empty()) return a.logicalName();
    if (!a.dbfBasename().empty()) return a.dbfBasename();
    return dbf_path.stem().string();
}

} // namespace

// ----------------------- Command entry --------------------------------------

// The parameter is the area the caller is STANDING IN. `a` below is bound to
// the area being OPENED INTO, which are the same thing unless IN <n> says
// otherwise. Binding the old name to the resolved target keeps every line
// downstream -- alias resolution, the duplicate guard, teardown, memo attach,
// order attach, the open report -- correct with no edit, and makes it
// impossible for one of them to be forgotten and quietly keep operating on
// the wrong area. That forgetting is the defect this commit fixes.
void cmd_USE(DbArea& current_area, std::istringstream& iss)
{
    const std::string raw_args = iss.str();
    if (is_use_usage_request(raw_args)) {
        print_use_usage();
        return;
    }

    std::string name;
    iss >> name;

    if (name.empty()) {
        cli::cmdout::print_prefixed_message("USE", dottalk::helpdata::MessageId::UseMissingTableNameText);
        print_use_usage();
        return;
    }

    const UseTail tail = parse_use_tail(iss);

    // REFUSALS FIRST, ALL OF THEM, BEFORE ANY AREA IS TOUCHED. Every branch
    // below returns having opened nothing and changed nothing -- the lesson
    // the memo guard taught this lane by getting it wrong (it refused AFTER
    // resetting the area and opening the file, then printed "Nothing was
    // opened" over the wreckage).
    if (!tail.unknown.empty()) {
        cli::cmdout::print_line(
            "USE: refused -- unrecognized argument '" + tail.unknown + "'.");
        cli::cmdout::print_line(
            "  USE <table> [IN <n>|FREE] [AGAIN] [ALIAS <name>] [NOINDEX|NOIDX]");
        cli::cmdout::print_line(
            "  Nothing was opened. USE used to ignore what it did not understand "
            "and open into the current area anyway (AIF-121).");
        return;
    }
    if (!tail.in_problem.empty()) {
        cli::cmdout::print_line("USE: refused -- " + tail.in_problem + ". Nothing was opened.");
        return;
    }

    const std::string alias_requested = tail.alias;
    if (tail.alias_malformed) {
        cli::cmdout::print_line("USE: ALIAS requires a name (USE <table> [AGAIN] ALIAS <name>).");
        return;
    }
    if (!alias_requested.empty() && !alias_is_addressable(alias_requested)) {
        cli::cmdout::print_line(
            "USE: refused -- alias '" + alias_requested +
            "' is all digits, and SELECT would read it as an area number. "
            "Nothing was opened.");
        return;
    }

    // --- RESOLVE THE TARGET AREA --------------------------------------------
    // IN <n> names the destination; AGAIN carries no placement opinion at all
    // (it only grants permission to duplicate), so there is no interaction
    // rule between them and none is invented here -- owner ruling 2026-08-22.
    // Without IN this is the current area, which is exactly today's behaviour.
    DbArea* target_p = &current_area;
    if (tail.have_in) {
        auto* eng = shell_engine();
        if (!eng) {
            cli::cmdout::print_line("USE: refused -- engine unavailable. Nothing was opened.");
            return;
        }
        long long want = tail.in_area;
        bool broke_contiguity = false;
        if (tail.in_free) {
            const int free_slot = find_free_area_for_current_workspace(broke_contiguity);
            if (free_slot < 0) {
                // Deliberately NOT falling back to the current area. Falling
                // back is the silent-replacement behaviour this lane exists
                // to kill, and it would be at its worst here: the caller who
                // wrote FREE is the one who most clearly did not want it.
                cli::cmdout::print_line(
                    "USE: refused -- IN FREE found no unoccupied area (all " +
                    std::to_string(xbase::MAX_AREA) + " are in use). Nothing was opened.");
                return;
            }
            want = free_slot;
            if (broke_contiguity) {
                cli::cmdout::print_line(
                    "USE IN FREE: workspace '" + xbase::workspace::name_of(xbase::workspace::current_handle()) +
                    "' could not grow contiguously; area " + std::to_string(free_slot) +
                    " is outside its existing run.");
            }
        }
        if (want < 0 || want >= xbase::MAX_AREA) {
            cli::cmdout::print_line(
                "USE: refused -- area " + std::to_string(want) + " is out of range (0.." +
                std::to_string(xbase::MAX_AREA - 1) + "). Nothing was opened.");
            return;
        }
        try {
            target_p = &eng->area(static_cast<int>(want));
        } catch (...) {
            cli::cmdout::print_line(
                "USE: refused -- area " + std::to_string(want) +
                " is unreachable. Nothing was opened.");
            return;
        }
    }

    // From here down, `a` IS the target. Note this does NOT select it: opening
    // into another area leaves the caller standing where they were, which is
    // the FoxPro contract for IN <n> and the reason the clause is useful.
    DbArea& a = *target_p;

    const bool again = tail.again;
    // AGAIN forces physical order in v1, and this is load-bearing, not
    // convenience: index auto-attach would open the SAME container for a
    // second time in this process, and for the LMDB-backed lane that is two
    // mdb_env_open calls on one environment (cdx_backend.cpp:224) -- undefined
    // behaviour by LMDB's own contract. Index attach on a second instance is
    // a later, separately-gated arm.
    const bool noindex = again || tail.noindex;
    ensure_setpath_initialized();

    // Resolve DBF path
    fs::path dbf_path;
    if (looks_explicit_path(name)) {
        // Explicit path: let resolver anchor relative paths and add .dbf if missing.
        dbf_path = dottalk::paths::resolve_dbf(name);
    } else {
        // Logical: "students" or "students.dbf"
        std::string base = strip_dbf_ext_if_present(name);
        dbf_path = dottalk::paths::get_slot(dottalk::paths::Slot::DBF) / (base + ".dbf");
    }

    // Duplicate-open guard. Without AGAIN: no-op by design, with a hint that
    // the AGAIN arm exists. With AGAIN: a second work area opens on the same
    // file (workspace design I5 v1 -- writable, record locking arbitrates per
    // the owner's multi-user model; intra-process lock isolation arrives with
    // the (pid,workspace) owner).
    const int cur_slot = area_slot_of(a);
    const int dup_slot = find_open_area_for_path(dbf_path);
    if (dup_slot >= 0) {
        if (dup_slot == cur_slot) {
            // AGAIN into the area that already holds the file is meaningless;
            // same message either way.
            cli::cmdout::print_prefixed_message(
                "USE",
                dottalk::helpdata::MessageId::UseAlreadyOpenCurrentAreaText,
                {{"file", dbf_path.filename().string()},
                 {"area", std::to_string(cur_slot)}});
            return; // no-op by design
        }
        if (!again) {
            cli::cmdout::print_prefixed_message(
                "USE",
                dottalk::helpdata::MessageId::UseAlreadyOpenOtherAreaText,
                {{"file", dbf_path.filename().string()},
                 {"area", std::to_string(dup_slot)}});
            cli::cmdout::print_line(
                "USE: add AGAIN to open a second work area on the same file "
                "(physical order).");
            return; // no-op by design
        }
        // MEMO REFUSAL, HOISTED (corrected 2026-08-12, found by its own spec).
        // This check used to sit below, after reset_area_runtime_best_effort()
        // and a.open() had already run -- so it printed "Nothing was opened"
        // having opened the file AND destroyed whatever occupied this area.
        // A guard with side effects is not a guard, and the message was a
        // statement about state the code had already contradicted: the exact
        // defect class this arm exists to prevent, inside the prevention.
        //
        // It costs nothing to be correct here. AGAIN means the file is open in
        // dup_slot by definition, so its field list is already in memory --
        // the probe reads that live area and touches no filesystem.
        if (auto* eng = shell_engine(); eng && dup_slot >= 0) {
            bool dupHasMemo = false;
            try {
                for (const auto& f : eng->area(dup_slot).fields()) {
                    if (f.type == 'M' || f.type == 'm') { dupHasMemo = true; break; }
                }
            } catch (...) { /* unreadable slot: fall through to the open path */ }

            if (dupHasMemo) {
                cli::cmdout::print_line(
                    "USE AGAIN: refused -- " + dbf_path.filename().string() +
                    " carries memo fields, and a second sidecar writer would "
                    "interleave appends. Nothing was opened, and area " +
                    std::to_string(cur_slot) + " is untouched.");
                return;
            }
        }

        // NOTE: no announcement here either. The AGAIN banner prints only once
        // the instance is committed, immediately before the open summary, so
        // no path can announce an open it then retracts.
        // fall through: open a second instance into the current area
    }

    // --- ALIAS RESOLUTION, before this area is touched -----------------------
    // Everything below can still refuse, and a refusal must leave the target
    // area exactly as it found it (the lesson the memo guard taught this
    // afternoon by getting it wrong).
    std::string alias_final = alias_requested;
    {
        const std::string stem = dbf_path.stem().string();
        const std::string wanted = alias_final.empty() ? stem : alias_final;
        const int holder = find_open_area_by_alias(wanted, cur_slot);

        if (holder >= 0 && !alias_final.empty()) {
            // Explicit and taken: REFUSE. Silently renaming a name the user
            // typed would defeat the reason they typed it.
            cli::cmdout::print_line(
                "USE: refused -- alias '" + alias_final + "' is already held by area " +
                std::to_string(holder) + ". Choose another, or close that area. "
                "Nothing was opened.");
            return;
        }

        if (holder >= 0) {
            // Derived from the file stem and taken -- the ordinary AGAIN case,
            // and also two same-named files from different directories. Before
            // this arm both instances answered to one name and
            // find_open_area_by_name_ci() returned the lower slot to SET
            // RELATION and every other name-based verb, with no diagnostic:
            // the second instance was open but unreachable by name.
            alias_final = derive_distinct_alias(stem, cur_slot);
            if (alias_final.empty()) {
                cli::cmdout::print_line(
                    "USE: refused -- cannot derive a free alias from '" + stem +
                    "'. Give one explicitly with ALIAS. Nothing was opened.");
                return;
            }
            cli::cmdout::print_line(
                "USE: alias '" + wanted + "' is held by area " + std::to_string(holder) +
                "; this instance is named '" + alias_final +
                "'. Use ALIAS to choose your own.");
        }
    }

    // --- CLEANUP CURRENT AREA BEFORE USE ---
    // why:
    //   - prevent stale CDX/tag/LMDB binding from surviving table switch
    //   - ensure the new table starts in a sterile physical-order state
    reset_area_runtime_best_effort(a);

    // Open DBF
    try {
        a.open(dbf_path.string());
        populate_dbarea_metadata(a, dbf_path, alias_final);
    } catch (const std::exception& ex) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::UseOpenFailedWithReasonText,
            {{"reason", ex.what()}});
        return;
    } catch (...) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::UseOpenFailedText);
        return;
    }

    // Crash recovery: if an interrupted COMMIT left a committed <dbf>.tbj redo
    // log, replay it into the DBF now; an uncommitted one is discarded. No-op if
    // no log is present (the common case).
    if (dottalk::table::recover_table_buffer_journal(a)) {
        cli::cmdout::print_line("USE: recovered a committed table-buffer journal (.tbj).");
    }

    // Memo auto-attach (best-effort, never fatal)
    {
        bool hasMemoFields = false;
        for (const auto& f : a.fields()) {
            if (f.type == 'M' || f.type == 'm') {
                hasMemoFields = true;
                break;
            }
        }

        // The AGAIN + memo refusal USED TO LIVE HERE and has moved UP, into the
        // duplicate-open guard, before this area is reset or the file opened.
        // Reason recorded there: refusing after the damage is not refusing.
        // Nothing replaces it at this point -- reaching here with again==true
        // means the hoisted probe already cleared this file. Two MemoManager
        // instances appending to one sidecar interleave offsets (the AIF-110
        // silent-corruption shape, permanent in the memo store); a second memo
        // attach stays a later, separately-gated arm.

        const std::string openedPath = a.filename().empty()
            ? fs::absolute(dbf_path).string()
            : a.filename();

        std::string memo_err;
        if (!cli_memo::memo_auto_on_use(a, openedPath, hasMemoFields, memo_err)) {
            cli::cmdout::print_prefixed_message(
                "USE",
                dottalk::helpdata::MessageId::UseMemoAttachFailedText,
                {{"reason", memo_err}});
        }
    }

    // AGAIN banner, printed only now: every refusal path above has been
    // cleared, so this announces a second instance that actually exists.
    if (again && dup_slot >= 0) {
        cli::cmdout::print_line(
            "USE AGAIN: second work area on " + dbf_path.filename().string() +
            " (first instance stays in area " + std::to_string(dup_slot) +
            "; physical order).");
    }

    // Standardized open report
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::UseOpenedSummaryText,
        {{"name", open_display_name(a, dbf_path)},
         {"version", xbase::dbf_version_token(a.versionByte())},
         {"count", std::to_string(a.recCount())}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::UseValidIndexesLineText,
        {{"types", valid_index_types_for(a)}});

    // PLACEMENT REPORT -- printed only when IN was used, because that is the
    // one moment a person has asked where the table goes and deserves an
    // answer in BOTH planes at once.
    //
    // This project currently numbers three different things and two of them
    // are positions: engine slots (0-based), workspace-local slots (0-based
    // since the owner ruling this session), and workspace handles (keys, where
    // 0 means "none"). Someone reading `local 2` and typing `SELECT 2` gets a
    // different area, and that collision is a live hazard rather than a
    // theoretical one. Printing both together, side by side, at the moment of
    // placement is the cheapest available inoculation.
    //
    // It is also the FIRST READER of DbArea::_ws_local_slot. Stage 1 gave that
    // field three writers and no consumers; rather than catalogue a fifth
    // AIF-079 instance, this line spends it.
    if (tail.have_in) {
        const int   eng_slot   = area_slot_of(a);
        const int   local_slot = workspace_area_slot_of(a);
        const auto  h          = a.wsHandle();
        std::string where = "USE: opened into engine area " + std::to_string(eng_slot);
        if (local_slot >= 0) {
            where += "  (workspace " + xbase::workspace::name_of(h) +
                     ", local slot " + std::to_string(local_slot) + ")";
        }
        where += ". Current area is unchanged.";
        cli::cmdout::print_line(where);
    }

    // NOINDEX → force physical order; stop
    if (noindex) {
        clear_order_best_effort(a);
        cli::cmdout::print_message(dottalk::helpdata::MessageId::UseNoIndexSkippedText);
        return;
    }

#if DOTTALK_HAS_XINDEX
    // Auto-attach order (best-effort, never fatal).
    // Policy:
    //   - x64/v128: prefer CDX from INDEXES, then DBF directory fallback
    //   - x32: prefer CNX, then INX from INDEXES, then DBF directory fallback
    auto try_set_order = [&](const fs::path& p) {
        try {
            const std::string ext = up_copy(p.extension().string());
            std::string tag;

            if (ext == ".CDX" || ext == ".CNX") {
                if (!activate_tag_container_for_use(a, p, tag)) {
                    return false;
                }
            } else {
                orderstate::setOrder(a, p.string());
                orderstate::setAscending(a, true);
                orderhooks::reconcile_after_mutation(a);
                tag = orderstate::activeTag(a);
            }

            if (!tag.empty() && (orderstate::isCnx(a) || orderstate::isCdx(a))) {
                bool uniq = false;
                if (orderstate::isCnx(a)) {
                    uniq = cnx_tag_is_unique(orderstate::orderName(a), tag);
                } else if (orderstate::isCdx(a)) {
                    uniq = cdx_tag_is_unique(orderstate::orderName(a), tag);
                }

                cli::cmdout::print_message(
                    uniq
                        ? dottalk::helpdata::MessageId::UseAutoAttachedOrderTagUniqueText
                        : dottalk::helpdata::MessageId::UseAutoAttachedOrderTagText,
                    {{"file", p.filename().string()},
                     {"tag", tag}});
            } else {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::UseAutoAttachedOrderText,
                    {{"file", p.filename().string()}});
            }
            return true;
        } catch (...) {
            // best-effort
        }
        return false;
    };

    for (const auto& candidate : auto_attach_candidates_for(a, dbf_path)) {
        if (!file_exists_best_effort(candidate)) {
            continue;
        }
        if (try_set_order(candidate)) {
            break;
        }
    }
#endif
}
