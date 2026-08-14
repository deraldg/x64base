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
//
// notes:
//   USE requires a table name or path; no usable argument shows usage.
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

#include "xbase.hpp"
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

static bool contains_noindex(std::istringstream& iss)
{
    std::streampos pos = iss.tellg();
    if (pos == std::streampos(-1)) {
        return false;
    }

    bool found = false;
    std::string tok;
    while (iss >> tok) {
        const std::string u = up_copy(tok);
        if (u == "NOINDEX" || u == "NOIDX") {
            found = true;
            break;
        }
    }

    iss.clear();
    iss.seekg(pos);
    return found;
}

// USE ... AGAIN (workspace design I5, v1 arm). Non-consuming scan, same
// pattern as contains_noindex: the flag may appear anywhere after the name.
static bool contains_again(std::istringstream& iss)
{
    std::streampos pos = iss.tellg();
    if (pos == std::streampos(-1)) {
        return false;
    }

    bool found = false;
    std::string tok;
    while (iss >> tok) {
        if (up_copy(tok) == "AGAIN") {
            found = true;
            break;
        }
    }

    iss.clear();
    iss.seekg(pos);
    return found;
}

// USE ... ALIAS <name> (owner 'fix the use command', 2026-08-12). Same
// non-consuming scan. Returns the token AFTER the keyword; sets `malformed`
// when ALIAS is present with nothing following it, so a typo is reported
// rather than silently treated as "no alias given" -- the difference between
// those two is a table that opens under the wrong name.
static std::string parse_alias_clause(std::istringstream& iss, bool& malformed)
{
    malformed = false;
    std::streampos pos = iss.tellg();
    if (pos == std::streampos(-1)) {
        return {};
    }

    std::string out;
    std::string tok;
    while (iss >> tok) {
        if (up_copy(tok) == "ALIAS") {
            if (iss >> tok) out = tok;
            else            malformed = true;
            break;
        }
    }

    iss.clear();
    iss.seekg(pos);
    return out;
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
    auto* eng = shell_engine(); if (!eng) return -1;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (&eng->area(i) == &a) return i;
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

void cmd_USE(DbArea& a, std::istringstream& iss)
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

    bool alias_malformed = false;
    const std::string alias_requested = parse_alias_clause(iss, alias_malformed);
    if (alias_malformed) {
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

    const bool again = contains_again(iss);
    // AGAIN forces physical order in v1, and this is load-bearing, not
    // convenience: index auto-attach would open the SAME container for a
    // second time in this process, and for the LMDB-backed lane that is two
    // mdb_env_open calls on one environment (cdx_backend.cpp:224) -- undefined
    // behaviour by LMDB's own contract. Index attach on a second instance is
    // a later, separately-gated arm.
    const bool noindex = again || contains_noindex(iss);
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
