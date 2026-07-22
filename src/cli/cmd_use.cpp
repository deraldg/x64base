// src/cli/cmd_use.cpp
// DotTalk++ USE command (open DBF in a work area) — duplicate-open guard, NOINDEX, auto-attach

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
//
// notes:
//   USE requires a table name or path; no usable argument shows usage.
//   Relative logical names resolve through the configured DBF path slot.
//   USE prevents duplicate opens of the same DBF path across work areas.
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

static void populate_dbarea_metadata(DbArea& a, const fs::path& dbf_path) {
    const std::string abs = fs::absolute(dbf_path).string();
    const std::string stem = dbf_path.stem().string();
    _setFilename(a, abs, 0);     // SCHEMAS uses filename() as truth
    _setLogicalName(a, stem, 0); // optional alias
    _setLegacyName(a, stem, 0);  // legacy alias
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
    if (is_x64_cdx_area(a)) return "CDX";
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

    const bool noindex = contains_noindex(iss);
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

    // Duplicate-open guard (no-op if already open anywhere)
    const int cur_slot = area_slot_of(a);
    const int dup_slot = find_open_area_for_path(dbf_path);
    if (dup_slot >= 0) {
        if (dup_slot == cur_slot) {
            cli::cmdout::print_prefixed_message(
                "USE",
                dottalk::helpdata::MessageId::UseAlreadyOpenCurrentAreaText,
                {{"file", dbf_path.filename().string()},
                 {"area", std::to_string(cur_slot)}});
        } else {
            cli::cmdout::print_prefixed_message(
                "USE",
                dottalk::helpdata::MessageId::UseAlreadyOpenOtherAreaText,
                {{"file", dbf_path.filename().string()},
                 {"area", std::to_string(dup_slot)}});
        }
        return; // no-op by design
    }

    // --- CLEANUP CURRENT AREA BEFORE USE ---
    // why:
    //   - prevent stale CDX/tag/LMDB binding from surviving table switch
    //   - ensure the new table starts in a sterile physical-order state
    reset_area_runtime_best_effort(a);

    // Open DBF
    try {
        a.open(dbf_path.string());
        populate_dbarea_metadata(a, dbf_path);
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
