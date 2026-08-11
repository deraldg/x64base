// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_workspace.cpp
//
// WORKSPACE (legacy DBF areas)
//
// Commands:
//   WORKSPACE                                   : List open areas.
//   WORKSPACE OPEN [<dir>]                      : Open all .dbf in <dir> (non-recursive).
//   WORKSPACE OPEN <dir> recursive              : (STUB) Accepts 'recursive'; falls back to non-recursive.
//   WORKSPACE OPEN <file.dbf>                   : Open a single .dbf into the CURRENT area.
//   WORKSPACE ADD <file.dbf>                    : Add one .dbf into the first free area without closing others.
//
//   WORKSPACE OPEN <target> CNX [FALLBACK] [recursive] [TABLE]
//   WORKSPACE OPEN <target> INX [FALLBACK] [recursive] [TABLE]
//   WORKSPACE OPEN <target> CDX [FALLBACK] [recursive] [TABLE]
//   WORKSPACE ADD <target> AUTO|CNX|INX|IDX|CDX|NOINDEX [FALLBACK] [TABLE]
//
//   NOTE:
//   - If CNX/INX/CDX is NOT specified, WORKSPACE OPEN uses the table flavor:
//     true x64/v128 -> CDX(LMDB), classic VFP/v32 -> CNX. Use NOINDEX to suppress this.
//     (DBF sidecars like memo are handled by the DBF open path, not by WORKSPACE.)
//   - TABLE flag will TABLE-ON each opened workarea (open DBF areas only).
//
//   WORKSPACE CLOSE                             : Close all.
//   WORKSPACE CLOSE <n> [m ...]                 : Close by area index(es).
//   WORKSPACE CLOSE <name|file|stem|alias>[,...]: Close by name(s)/alias(es); case-insensitive.
//   WORKSPACE SAVE <file>                       : Save layout (+relations if available), including index type + active tag.
//   WORKSPACE LOAD <file>                       : Close all, load layout (+relations), resolve relative/cross-OS paths, and restore tags.
//   WORKSPACE TUPLES [LIMIT n] [OFFSET n] [AREA n] : Print ordered tuple rows from an open area.
//
// Notes:
// - filename() is treated as "open" truth; we set it on open so LIST/CLOSE work uniformly.
// - Alias is optional; we only read/write/set it if DbArea exposes the API.
// - OPEN resolves indexes like LOAD: sibling first, then INDEXES slot.
// - CNX resolves .cnx first, then .cdx for compatibility.
// - Relations integration is optional and zero-cost when headers absent.
//
// IMPORTANT SYNTAX RULE:
// - The directory/target is always the first argument after OPEN.
//   Examples:
//     WORKSPACE OPEN dbf TABLE
//     WORKSPACE OPEN dbf CNX TABLE
//     WORKSPACE OPEN table TABLE
//     WORKSPACE OPEN DBF CNX TABLE
//
// PATH RULE:
// - Relative OPEN targets are resolved against the configured path slots,
//   primarily the DBF slot established by INIT / SETPATH.
// - Common shorthand such as `WORKSPACE OPEN dbf` and `WORKSPACE OPEN students`
//   are treated as DBF-slot-relative requests.
//
// @dottalk.usage v1
// owner: DOT|WORKSPACE
// command: WORKSPACE
// category: workspace
// status: supported
// noargs: report
// effect: session
// mutates: session
// usage-access: WORKSPACE USAGE
// summary:
//   Report and manage live work-area/session layout.
//
// usage:
//   WORKSPACE
//   WORKSPACE USAGE
//   WORKSPACE ALL
//   WORKSPACE OPEN DBF
//   WORKSPACE OPEN <dir>
//   WORKSPACE OPEN <file.dbf>
//   WORKSPACE ADD <file.dbf>
//   WORKSPACE ADD <target> CNX [FALLBACK] [TABLE]
//   WORKSPACE ADD <target> INX|IDX [FALLBACK] [TABLE]
//   WORKSPACE ADD <target> CDX [FALLBACK] [TABLE]
//   WORKSPACE OPEN <target> CNX [FALLBACK] [recursive] [TABLE]
//   WORKSPACE OPEN <target> INX|IDX [FALLBACK] [recursive] [TABLE]
//   WORKSPACE OPEN <target> CDX [FALLBACK] [recursive] [TABLE]
//   WORKSPACE CLOSE
//   WORKSPACE CLOSE <n> [m ...]
//   WORKSPACE CLOSE <name|file|stem|alias>[,...]
//   WORKSPACE SAVE <file>
//   WORKSPACE LOAD <file>
//   WORKSPACE TUPLES [LIMIT <n>] [OFFSET <n>] [AREA <n>]
//
// notes:
//   WORKSPACE with no arguments is a report: it lists current open work areas.
//   WORKSPACE ALL lists all area slots, including closed slots.
//   WORKSPACE OPEN DBF scans the configured DBF path slot and opens tables into work areas.
//   WORKSPACE OPEN <dir> scans a specific directory and opens DBFs into work areas.
//   WORKSPACE OPEN <file.dbf> opens a single table into the current work area.
//   WORKSPACE ADD <file.dbf> opens one table into the first free work area without closing existing areas.
//   WORKSPACE OPEN is replacement-style and resets area membership before opening.
//   WORKSPACE ADD is additive and preserves existing open areas.
//   WORKSPACE CLOSE closes all open work areas and clears relation/session state.
//   WORKSPACE owns live areas, aliases, index/tag bindings, and relation/session layout.
//   Default index policy is flavor-aware: true x64/v128 uses CDX(LMDB), classic VFP/v32 uses CNX.
//   DDL owns schema/definition work; WORKSPACE owns live session/work-area state.
//
// related:
//   DBAREA
//   DBAREAS
//   DDL
//   REL
//   STATUS
//
#include <algorithm>
#include <cctype>
#include <climits>
#include <cstdlib>
#include <filesystem>
#include <chrono>
#include <fstream>
#include "xbase/ramfs.hpp"
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <sstream>
#include <string>
#include <type_traits>
#include <unordered_set>
#include <vector>

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "memo/memo_auto.hpp"   // cli_memo::memo_auto_on_use / memo_auto_on_close
// AIF-070 M2 (memo carrier) dependencies:
#include "xbase/dbf_create.hpp"          // create the WORKSPACES catalog (X64, memo field)
#include "xbase/field_name_policy.hpp"   // descriptor-name planning (two name planes)
#include "xbase/fields.hpp"              // fields::findFieldCI (public; DbArea's member is private)
#include "xbase_locks.hpp"               // cooperative FLOCK for catalog appends
#include "identity/identity_admin.hpp"   // AIF-075: current_member attribution
#include <ctime>
#if DOTTALK_HAS_XINDEX
#include "xindex/index_manager.hpp"
#include "xindex/attach.hpp"
#endif
#include "cli/dirty_prompt.hpp"
#include "cli/order_state.hpp"
#include "cli/path_resolver.hpp"
#include "cli/cmd_setpath.hpp"
#include "relations_boot.hpp"
#include "tuple_builder.hpp"
#include "cli/unique_registry.hpp"
#include "workarea_util.hpp"

#define HAVE_PATHS 1

#if __has_include("set_relations.hpp")
  #include "set_relations.hpp"
  #define HAVE_RELATIONS 1
#else
  #define HAVE_RELATIONS 0
#endif

#if __has_include("cli/table_state.hpp")
  #include "cli/table_state.hpp"
  #define HAVE_TABLE 1
#else
  #define HAVE_TABLE 0
#endif

#if __has_include("cli/order_iterator.hpp")
  #include "cli/order_iterator.hpp"
  #define HAVE_ORDER_ITERATOR 1
#else
  #define HAVE_ORDER_ITERATOR 0
#endif

namespace fs = std::filesystem;
using std::string;

static std::string& last_loaded_workspace_file() {
    static std::string path;
    return path;
}

// CNX (compound) extensions
static constexpr const char* kCnxPrimaryExt = ".cnx";
static constexpr const char* kCnxCompatExt  = ".cdx";

// --------- Utilities --------------------------------------------------------

static inline string trim_copy(string s) {
    auto is_space = [](unsigned char ch){ return std::isspace(ch) != 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [&](unsigned char c){ return !is_space(c); }));
    s.erase(std::find_if(s.rbegin(), s.rend(), [&](unsigned char c){ return !is_space(c); }).base(), s.end());
    return s;
}

static inline string to_lower(string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return std::tolower(c); });
    return s;
}

static inline string to_upper(string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return std::toupper(c); });
    return s;
}

static inline bool ci_equal(const string& a, const string& b) {
    if (a.size() != b.size()) return false;
    for (size_t i = 0; i < a.size(); ++i) {
        if (std::tolower(static_cast<unsigned char>(a[i])) !=
            std::tolower(static_cast<unsigned char>(b[i]))) return false;
    }
    return true;
}

static inline std::string s8(const fs::path& p) {
#if defined(_WIN32)
    auto u = p.u8string();
    return std::string(u.begin(), u.end());
#else
    return p.string();
#endif
}

static inline bool ieq_ext(const fs::path& p, const char* extDotLower) {
    std::string e = p.extension().string();
    const size_t nRef = std::char_traits<char>::length(extDotLower);
    if (e.size() != nRef) return false;
    for (size_t i = 0; i < nRef; ++i) {
        unsigned char A = static_cast<unsigned char>(e[i]);
        unsigned char B = static_cast<unsigned char>(extDotLower[i]);
        if (std::tolower(A) != std::tolower(B)) return false;
    }
    return true;
}

static inline bool is_dbf(const fs::directory_entry& de) {
    return de.is_regular_file() && ieq_ext(de.path(), ".dbf");
}

static inline bool try_parse_int(const string& s, int& out) {
    if (s.empty()) return false;
    char* end = nullptr;
    long v = std::strtol(s.c_str(), &end, 10);
    if (end == s.c_str() || *end != '\0') return false;
    if (v < INT_MIN || v > INT_MAX) return false;
    out = static_cast<int>(v);
    return true;
}

static std::vector<string> split_tokens(const string& s) {
    std::vector<string> out;
    string cur;
    for (char c : s) {
        if (c == ',' || std::isspace(static_cast<unsigned char>(c))) {
            if (!cur.empty()) {
                out.push_back(cur);
                cur.clear();
            }
        } else {
            cur.push_back(c);
        }
    }
    if (!cur.empty()) out.push_back(cur);
    for (auto& t : out) t = trim_copy(t);
    out.erase(std::remove_if(out.begin(), out.end(), [](const string& t){ return t.empty(); }), out.end());
    return out;
}

static inline bool parse_fallback_ci(const std::string& token) {
    return ci_equal(token, "fallback") || ci_equal(token, "--fallback");
}

static inline bool parse_recursive_ci(const std::string& token) {
    return ci_equal(token, "recursive") || ci_equal(token, "--recursive") || ci_equal(token, "-r");
}

static inline bool parse_table_ci(const std::string& token) {
    return ci_equal(token, "table") || ci_equal(token, "--table");
}

// Cross-OS path recognition / translation for LOAD.
static bool looks_like_windows_abs(const fs::path& p) {
    const std::string s = s8(p);
    return s.size() >= 3 &&
           std::isalpha(static_cast<unsigned char>(s[0])) &&
           s[1] == ':' &&
           (s[2] == '\\' || s[2] == '/');
}

static bool looks_like_posix_abs(const fs::path& p) {
    const std::string s = s8(p);
    return !s.empty() && s[0] == '/';
}

static fs::path translate_cross_os_absolute(const fs::path& p) {
    const std::string s = s8(p);

#if defined(_WIN32)
    // /mnt/x/... -> X:\...
    if (s.size() >= 7 &&
        s[0] == '/' && s[1] == 'm' && s[2] == 'n' && s[3] == 't' && s[4] == '/' &&
        std::isalpha(static_cast<unsigned char>(s[5])) &&
        s[6] == '/') {
        char drive = static_cast<char>(std::toupper(static_cast<unsigned char>(s[5])));
        std::string tail = s.substr(7);
        std::replace(tail.begin(), tail.end(), '/', '\\');
        return fs::path(std::string(1, drive) + ":\\" + tail);
    }
    return p;
#else
    // X:\... -> /mnt/x/...
    if (looks_like_windows_abs(p)) {
        char drive = static_cast<char>(std::tolower(static_cast<unsigned char>(s[0])));
        std::string tail = s.substr(2);
        while (!tail.empty() && (tail[0] == '\\' || tail[0] == '/')) {
            tail.erase(tail.begin());
        }
        std::replace(tail.begin(), tail.end(), '\\', '/');
        return fs::path("/mnt") / std::string(1, drive) / tail;
    }
    return p;
#endif
}

// Engine access
extern "C" xbase::XBaseEngine* shell_engine();

static xbase::DbArea& get_area_0based(int slot0) {
    auto* eng = shell_engine();
    if (!eng) throw std::runtime_error("WORKSPACE: engine not available");
    if (slot0 < 0 || slot0 >= xbase::MAX_AREA) throw std::out_of_range("WORKSPACE: area out of range");
    return eng->area(slot0);
}

static int get_area_index(xbase::DbArea& areaRef) {
    auto* eng = shell_engine();
    if (!eng) return -1;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (&eng->area(i) == &areaRef) return i;
    }
    return -1;
}

static bool select_engine_area(int slot0) {
    auto* eng = shell_engine();
    if (!eng) return false;
    if (slot0 < 0 || slot0 >= xbase::MAX_AREA) return false;
    try {
        eng->selectArea(slot0);
        return true;
    } catch (...) {
        return false;
    }
}

static int first_open_area_index() {
    auto* eng = shell_engine();
    if (!eng) return -1;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        try {
            if (!eng->area(i).filename().empty()) return i;
        } catch (...) {}
    }
    return -1;
}

static int first_closed_area_index() {
    auto* eng = shell_engine();
    if (!eng) return -1;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        try {
            if (eng->area(i).filename().empty()) return i;
        } catch (...) {}
    }
    return -1;
}

static bool same_path_best_effort(const fs::path& a, const fs::path& b) {
    auto normalize = [](const fs::path& p) {
        std::error_code ec;
        fs::path out = fs::weakly_canonical(p, ec);
        if (ec) {
            ec.clear();
            out = fs::absolute(p, ec);
        }
        if (ec) out = p;
#if defined(_WIN32)
        auto u = out.u8string();
        return std::string(u.begin(), u.end());
#else
        return out.string();
#endif
    };
    std::string sa = normalize(a);
    std::string sb = normalize(b);
#if defined(_WIN32)
    return ci_equal(sa, sb);
#else
    return sa == sb;
#endif
}

static int find_open_area_for_path(const fs::path& dbf_path) {
    auto* eng = shell_engine();
    if (!eng) return -1;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        try {
            const std::string filename = eng->area(i).filename();
            if (!filename.empty() && same_path_best_effort(fs::path(filename), dbf_path)) {
                return i;
            }
        } catch (...) {}
    }
    return -1;
}

static void normalize_selected_area_after_workspace_change(int preferred_area0 = -1) {
    if (preferred_area0 >= 0 && preferred_area0 < xbase::MAX_AREA) {
        try {
            xbase::DbArea& preferred = get_area_0based(preferred_area0);
            if (!preferred.filename().empty()) {
                (void)select_engine_area(preferred_area0);
                return;
            }
        } catch (...) {}
    }

    const int first_open = first_open_area_index();
    if (first_open >= 0) {
        (void)select_engine_area(first_open);
        return;
    }

    (void)select_engine_area(0);
}

// Optional alias support
template <typename T>
using has_setLogicalName_t = decltype(std::declval<T&>().setLogicalName(std::declval<std::string>()));

template <typename T, typename = has_setLogicalName_t<T>>
static inline void setLogicalNameIf(T& a, const std::string& s, int) { a.setLogicalName(s); }

template <typename T>
static inline void setLogicalNameIf(T&, const std::string&, long) {}

template <typename T>
using has_setName_t = decltype(std::declval<T&>().setName(std::declval<std::string>()));

template <typename T, typename = has_setName_t<T>>
static inline void setLegacyNameIf(T& a, const std::string& s, int) { a.setName(s); }

template <typename T>
static inline void setLegacyNameIf(T&, const std::string&, long) {}

template <typename T>
using has_name_t = decltype(std::declval<T&>().name());

template <typename T, typename = has_name_t<T>>
static inline std::string getNameIf(T& a, int) { return a.name(); }

template <typename T>
static inline std::string getNameIf(T&, long) { return {}; }

// Optional order/tag support
template <typename Area>
static inline std::string getOrderNameSafe(Area& a) {
    try { return orderstate::orderName(a); } catch (...) { return {}; }
}

template <typename Area>
static inline std::string getActiveTagSafe(Area& a) {
    if constexpr (requires(Area& aa) { orderstate::activeTag(aa); }) {
        try { return orderstate::activeTag(a); } catch (...) {}
    }
    try {
#if DOTTALK_HAS_XINDEX
        if (auto* im = xindex::manager_if_attached(a)) return im->activeTag();
#endif
    } catch (...) {}
    return {};
}

template <typename Area>
static inline bool setActiveTagSafe(Area& a, const std::string& tag) {
    if (tag.empty() || ci_equal(tag, "none")) return true;
    if constexpr (requires(Area& aa, const std::string& s) { orderstate::setActiveTag(aa, s); }) {
        try { orderstate::setActiveTag(a, tag); return true; } catch (...) {}
    }
    return false;
}

static inline std::string infer_index_type_from_path(const std::string& path) {
    if (path.empty() || ci_equal(path, "none")) return "NONE";
    fs::path p(path);
    if (ieq_ext(p, ".inx")) return "INX";
    if (ieq_ext(p, ".cnx")) return "CNX";
    if (ieq_ext(p, ".cdx")) return "CDX";
    return "UNKNOWN";
}

// Paths helpers
namespace paths = dottalk::paths;

static inline fs::path dbf_root()       { return paths::get_slot(paths::Slot::DBF); }
static inline fs::path idx_root()       { return paths::get_slot(paths::Slot::INDEXES); }
static inline fs::path data_root()      { return paths::get_slot(paths::Slot::DATA); }
static inline fs::path WORKSPACE_root()   { return paths::get_slot(paths::Slot::WORKSPACES); }

static inline fs::path resolve_relative_to_root(const fs::path& p) {
    if (p.is_absolute()) return p;
    return fs::weakly_canonical(dbf_root() / p);
}

static inline bool area_open(xbase::DbArea& A) {
    return !A.filename().empty();
}

static fs::path resolve_workspace_file_path(const fs::path& file, bool for_save) {
    fs::path p = file;
    const fs::path rootWORKSPACE = WORKSPACE_root();

    auto make_candidate = [&](const fs::path& candidate) -> fs::path {
        if (candidate.is_relative()) return rootWORKSPACE / candidate;
        return candidate;
    };

    auto existing_candidate = [&](const fs::path& candidate) -> fs::path {
        std::error_code ec;
        if (fs::exists(candidate, ec) && !ec) return candidate;
        return {};
    };

    if (for_save) {
        if (p.is_relative()) p = rootWORKSPACE / p;
        if (!p.has_extension()) p.replace_extension(".dtschema");
        return p;
    }

    if (p.has_extension()) {
        if (p.is_relative()) {
            fs::path candidate = rootWORKSPACE / p;
            std::error_code ec;
            if (fs::exists(candidate, ec) && !ec) return candidate;
            return fs::current_path() / p;
        }
        return p;
    }

    const std::vector<std::string> exts = {".dtschema", ".dtschemas"};
    for (const auto& ext : exts) {
        fs::path probe = p;
        probe.replace_extension(ext);

        if (fs::path hit = existing_candidate(make_candidate(probe)); !hit.empty()) return hit;
        if (fs::path hit = existing_candidate(fs::current_path() / probe); !hit.empty()) return hit;
        if (fs::path hit = existing_candidate(probe); !hit.empty()) return hit;
    }

    p.replace_extension(".dtschema");
    if (p.is_relative()) {
        fs::path candidate = rootWORKSPACE / p;
        std::error_code ec;
        if (fs::exists(candidate, ec) && !ec) return candidate;
        return fs::current_path() / p;
    }
    return p;
}

// --------- OPEN target resolution ------------------------------------------

static bool file_exists(const fs::path& p) {
    std::error_code ec;
    return fs::exists(p, ec) && !ec && fs::is_regular_file(p, ec) && !ec;
}

static bool dir_exists(const fs::path& p) {
    std::error_code ec;
    return fs::exists(p, ec) && !ec && fs::is_directory(p, ec) && !ec;
}

static fs::path resolve_open_target(const fs::path& raw) {
    if (raw.empty()) return dbf_root();

    if (raw.is_absolute()) return raw;

    const std::string rawStr = s8(raw);
    const std::string rawLow = to_lower(rawStr);
    const fs::path dbfRoot = dbf_root();

    // Slot shorthand must win before testing an existing relative path.
    //
    // WORKSPACE OPEN DBF is a command-level request for the configured DBF
    // slot, not for a literal relative directory named "dbf" under the current
    // process working directory.  This preserves the traditional SETPATH/DO
    // workflow:
    //
    //   DO X64      -> SETPATH DBF ...\DBF\x64
    //   WORKSPACE OPEN DBF
    //
    // and likewise for SANDBOX/X32/etc.  Explicit relative paths still work
    // below for non-slot names such as DBF/X64 or some/custom/path.
    if (rawLow == "dbf")        return dbfRoot;
    if (rawLow == "data")       return data_root();
    if (rawLow == "indexes")    return idx_root();
    if (rawLow == "schemas")    return paths::get_slot(paths::Slot::SCHEMAS);
    if (rawLow == "scripts")    return paths::get_slot(paths::Slot::SCRIPTS);
    if (rawLow == "tests")      return paths::get_slot(paths::Slot::TESTS);
    if (rawLow == "help")       return paths::get_slot(paths::Slot::HELP);
    if (rawLow == "logs")       return paths::get_slot(paths::Slot::LOGS);
    if (rawLow == "tmp")        return paths::get_slot(paths::Slot::TMP);
    if (rawLow == "workspaces") return paths::get_slot(paths::Slot::WORKSPACES);

    // Existing explicit relative path.  This intentionally comes after known
    // slot shorthand so that DBF/INDEXES/etc. keep their configured meaning.
    if (dir_exists(raw) || file_exists(raw)) return raw;

    // DBF slot-relative directory/file.
    {
        fs::path cand = dbfRoot / raw;
        if (dir_exists(cand) || file_exists(cand)) return cand;
    }

    // If user passed an index filename, map to DBF stem.
    if (ieq_ext(raw, ".inx") || ieq_ext(raw, ".cnx") || ieq_ext(raw, ".cdx")) {
        fs::path stem = raw.stem();
        fs::path cand = (dbfRoot / stem).concat(".dbf");
        if (file_exists(cand)) return cand;
    }

    // Bare stem conveniences:
    //   <DBF>/<stem>.dbf
    //   <DBF>/<stem>/<stem>.dbf
    if (!raw.has_extension()) {
        fs::path cand1 = (dbfRoot / raw).concat(".dbf");
        if (file_exists(cand1)) return cand1;

        fs::path inner = raw.filename();
        inner.replace_extension(".dbf");
        fs::path cand2 = dbfRoot / raw / inner;
        if (file_exists(cand2)) return cand2;

        fs::path candDir = dbfRoot / raw;
        if (dir_exists(candDir)) return candDir;
    }

    // Final fallback: DBF-slot-relative.
    return dbfRoot / raw;
}

// --------- Index selection --------------------------------------------------

enum class IndexMode { None = 0, Auto, ForceCnx, ForceInx, ForceCdx };

static inline std::optional<IndexMode> parse_index_mode_ci(const std::string& token) {
    if (ci_equal(token, "auto")) return IndexMode::Auto;
    if (ci_equal(token, "cnx")) return IndexMode::ForceCnx;
    if (ci_equal(token, "inx")) return IndexMode::ForceInx;
    if (ci_equal(token, "idx")) return IndexMode::ForceInx;
    if (ci_equal(token, "cdx")) return IndexMode::ForceCdx;
    return std::nullopt;
}

static inline bool parse_noindex_ci(const std::string& token) {
    return ci_equal(token, "noindex") || ci_equal(token, "noindexes") ||
           ci_equal(token, "none") || ci_equal(token, "physical");
}

static bool area_prefers_cdx_auto_index(const xbase::DbArea& A) {
    return A.versionByte() == xbase::DBF_VERSION_64 || A.kind() == xbase::AreaKind::V128;
}

static IndexMode default_index_mode_for_area(const xbase::DbArea& A) {
    if (area_prefers_cdx_auto_index(A)) return IndexMode::ForceCdx;

    switch (A.kind()) {
    case xbase::AreaKind::V32:
    case xbase::AreaKind::V64:   // classic VFP stays in the CNX/INX lane
        return IndexMode::ForceCnx;
    case xbase::AreaKind::V128:
        return IndexMode::ForceCdx;
    case xbase::AreaKind::Tup:
    case xbase::AreaKind::Unknown:
    default:
        return IndexMode::None;
    }
}

static IndexMode effective_index_mode_for_area(const xbase::DbArea& A, IndexMode requested) {
    if (requested == IndexMode::Auto) return default_index_mode_for_area(A);
    return requested;
}

static std::optional<fs::path> find_index_for_dbf(const fs::path& dbfPath,
                                                  IndexMode mode,
                                                  bool fallback,
                                                  bool allow_cnx_cdx_compat = true) {
    auto file_ok = [](const fs::path& p) {
        std::error_code ec;
        return fs::exists(p, ec) && !ec && fs::is_regular_file(p, ec) && !ec;
    };

    const fs::path stem = fs::path(dbfPath).stem();
    std::string stem_upper = s8(stem);
    for (auto& ch : stem_upper) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));

    auto inx_candidates = [&](const fs::path& baseDir) -> std::vector<fs::path> {
        return { (baseDir / stem).concat(".inx") };
    };

    auto cnx_candidates = [&](const fs::path& baseDir) -> std::vector<fs::path> {
        std::vector<fs::path> out{(baseDir / stem).concat(kCnxPrimaryExt)};
        if (allow_cnx_cdx_compat) {
            out.push_back((baseDir / stem).concat(kCnxCompatExt));
        }
        return out;
    };

    const fs::path sibDir = dbfPath.parent_path().empty() ? fs::current_path() : dbfPath.parent_path();
    const fs::path idxDir = idx_root();
    const fs::path idxX32Dir = paths::get_slot(paths::Slot::INDEXES_X32);
    const fs::path idxX64Dir = paths::get_slot(paths::Slot::INDEXES_X64);

    auto append_unique_dir = [](std::vector<fs::path>& dirs, fs::path dir) {
        if (dir.empty()) return;
        const auto found = std::find_if(dirs.begin(), dirs.end(), [&](const fs::path& existing) {
            std::error_code ec1;
            std::error_code ec2;
            const fs::path a = fs::weakly_canonical(existing, ec1);
            const fs::path b = fs::weakly_canonical(dir, ec2);
            if (!ec1 && !ec2) return a == b;
            return existing == dir;
        });
        if (found == dirs.end()) dirs.push_back(std::move(dir));
    };

    auto dirs_for_mode = [&](IndexMode wanted) {
        std::vector<fs::path> dirs;
        append_unique_dir(dirs, sibDir);
        // AIF-099 cross-slot fix (owner-caught live, 2026-08-09): the CONFIGURED
        // INDEXES slot outranks the hard-coded flavor slots. The old order
        // searched INDEXES_X32 before the configured slot whenever CNX was
        // wanted -- a leftover of the "CNX is an x32 thing" policy -- so an x64
        // table in an x64 workspace could attach the x32 twin's same-stem .cnx
        // (a FOREIGN container built over a different table). Observed:
        // dbf/x64/STUDENTS.dbf wearing indexes/x32/STUDENTS.cnx. Flavor slots
        // remain as LAST-RESORT fallbacks only. Proof: INDEX_X64_CNX Scope E
        // (decoy in the x32 slot must lose to the configured slot).
        append_unique_dir(dirs, idxDir);
        if (wanted == IndexMode::ForceCdx) append_unique_dir(dirs, idxX64Dir);
        if (wanted == IndexMode::ForceCnx || wanted == IndexMode::ForceInx) append_unique_dir(dirs, idxX32Dir);
        return dirs;
    };

    auto pick_first_existing = [&](const std::vector<fs::path>& cands) -> std::optional<fs::path> {
        for (const auto& p : cands) {
            if (file_ok(p)) return p;
        }
        return std::nullopt;
    };

    auto pick_inx = [&]() -> std::optional<fs::path> {
        for (const auto& dir : dirs_for_mode(IndexMode::ForceInx)) {
            if (auto p = pick_first_existing(inx_candidates(dir))) return p;
        }
        return std::nullopt;
    };

    auto pick_cnx = [&]() -> std::optional<fs::path> {
        for (const auto& dir : dirs_for_mode(IndexMode::ForceCnx)) {
            if (auto p = pick_first_existing(cnx_candidates(dir))) return p;
        }
        return std::nullopt;
    };

    auto pick_cdx = [&](const std::string& stemUpper) -> std::optional<fs::path> {
        for (const auto& dir : dirs_for_mode(IndexMode::ForceCdx)) {
            fs::path stem_cdx = dir / stem;
            stem_cdx.replace_extension(".cdx");

            const std::vector<fs::path> cdx_candidates = {
                dir / (stemUpper + ".cdx"),
                stem_cdx
            };
            for (const auto& p : cdx_candidates) {
                if (file_ok(p)) return p;
            }
        }
        return std::nullopt;
    };

    if (mode == IndexMode::ForceCdx) {
        if (auto p = pick_cdx(stem_upper)) return p;
        if (fallback) {
            if (auto q = pick_cnx()) return q;
            return pick_inx();
        }
        return std::nullopt;
    }

    if (mode == IndexMode::ForceInx) {
        if (auto p = pick_inx()) return p;
        if (fallback) return pick_cnx();
        return std::nullopt;
    }

    if (mode == IndexMode::ForceCnx) {
        if (auto p = pick_cnx()) return p;
        if (fallback) return pick_inx();
        return std::nullopt;
    }

    return std::nullopt;
}

static std::optional<fs::path> find_index_for_open_area(const xbase::DbArea& A,
                                                        const fs::path& dbfPath,
                                                        IndexMode requested,
                                                        bool fallback) {
    const IndexMode effective = effective_index_mode_for_area(A, requested);
    if (effective == IndexMode::None || effective == IndexMode::Auto) return std::nullopt;
    const bool allow_cnx_cdx_compat = (requested != IndexMode::Auto);
    return find_index_for_dbf(dbfPath, effective, fallback, allow_cnx_cdx_compat);
}

static bool attach_workspace_index(xbase::DbArea& A,
                                   const fs::path& indexPath,
                                   std::string& err) {
#if !DOTTALK_HAS_XINDEX
    (void)A;
    (void)indexPath;
    err = "index engine not compiled in this table-only build";
    return false;
#else
    err.clear();

    fs::path ip = indexPath;
    if (!ip.is_absolute()) ip = resolve_relative_to_root(ip);

    std::error_code ec;
    if (!fs::exists(ip, ec) || ec) {
        err = "index file not found: " + s8(ip);
        return false;
    }

    std::string backend_err;
    const std::string path = s8(ip);
    const std::string ext = to_lower(ip.extension().string());

    try { xindex::ensure_manager(A).close(); } catch (...) {}
    try { orderstate::clearOrder(A); } catch (...) {}

    try {
        orderstate::setOrder(A, path);
        orderstate::setAscending(A, true);
        orderstate::setActiveTag(A, "");
    } catch (const std::exception& ex) {
        err = ex.what();
        return false;
    } catch (...) {
        err = "failed to seed order state";
        return false;
    }

    bool opened = false;
    if (ext == ".cdx") {
        opened = xindex::ensure_manager(A).openCdx(path, {}, &backend_err);
    } else if (ext == ".cnx") {
        opened = xindex::ensure_manager(A).openCnx(path, {}, &backend_err);
    } else if (ext == ".inx") {
        opened = xindex::ensure_manager(A).load_json(path);
        if (!opened) backend_err = "load_json failed for INX sidecar";
    } else {
        backend_err = "unsupported index extension: " + ext;
    }

    if (!opened) {
        try { xindex::ensure_manager(A).close(); } catch (...) {}
        try { orderstate::clearOrder(A); } catch (...) {}
        err = backend_err.empty() ? "index backend open failed" : backend_err;
        return false;
    }

    try {
        const std::string active = xindex::ensure_manager(A).activeTag();
        if (!active.empty()) orderstate::setActiveTag(A, active);
    } catch (...) {}

    return true;
#endif
}

// --------- OPEN helpers -----------------------------------------------------

struct OpenResult {
    int area = -1;
    fs::path dbf;
    std::optional<fs::path> indexFile;
    bool opened = false;
    bool indexAttached = false;
    string error;
    string indexError;
};

// Workspace opens DBFs through several helper paths instead of cmd_USE.
// Keep memo sidecar attach/close centralized here so x64 DTX memo fields do
// not fall back to raw memo pointer display after WORKSPACE OPEN/LOAD.
static bool workspace_area_has_memo_fields(xbase::DbArea& A) {
    for (const auto& f : A.fields()) {
        if (f.type == 'M' || f.type == 'm') return true;
    }
    return false;
}

static void workspace_memo_auto_close_before_dbf_close(xbase::DbArea& A) {
    try { cli_memo::memo_auto_on_close(A); } catch (...) {}
}

static void workspace_memo_auto_attach_after_dbf_open(xbase::DbArea& A,
                                                      const fs::path& dbf,
                                                      const char* context) {
    const bool hasMemoFields = workspace_area_has_memo_fields(A);
    if (!hasMemoFields) return;

    const std::string openedPath = A.filename().empty()
        ? fs::absolute(dbf).string()
        : A.filename();

    std::string memo_err;
    if (!cli_memo::memo_auto_on_use(A, openedPath, true, memo_err)) {
        std::cout << (context ? context : "WORKSPACE")
                  << ": memo attach failed for "
                  << s8(dbf.filename())
                  << ": " << memo_err << "\n";
    }
}

#if HAVE_TABLE
static void table_enable_for_area_if_open(int area0) {
    if (area0 < 0 || area0 >= xbase::MAX_AREA) return;
    try {
        auto* eng = shell_engine();
        if (!eng) return;
        if (eng->area(area0).filename().empty()) return;
        dottalk::table::set_enabled(area0, true);
        dottalk::table::set_dirty(area0, false);
        dottalk::table::set_stale(area0, false);
    } catch (...) {}
}

static int table_enable_for_results(const std::vector<OpenResult>& results) {
    int n = 0;
    for (const auto& r : results) {
        if (r.area >= 0 && r.opened) {
            table_enable_for_area_if_open(r.area);
            ++n;
        }
    }
    return n;
}
#endif

static std::vector<OpenResult> schema_open_directory(const fs::path& dir, IndexMode mode, bool fallback) {
    std::vector<OpenResult> results;

    if (!fs::exists(dir) || !fs::is_directory(dir)) {
        OpenResult r;
        r.error = "Not a directory: " + s8(dir);
        results.push_back(std::move(r));
        return results;
    }

    std::vector<fs::directory_entry> dbfs;
    for (const auto& de : fs::directory_iterator(dir)) {
        if (is_dbf(de)) dbfs.push_back(de);
    }

    std::sort(dbfs.begin(), dbfs.end(), [](const fs::directory_entry& a, const fs::directory_entry& b){
        auto sa = s8(a.path().filename());
        auto sb = s8(b.path().filename());
        std::transform(sa.begin(), sa.end(), sa.begin(), [](unsigned char c){ return std::tolower(c); });
        std::transform(sb.begin(), sb.end(), sb.begin(), [](unsigned char c){ return std::tolower(c); });
        return sa < sb;
    });

    const int capacity = xbase::MAX_AREA;
    const int toOpen   = static_cast<int>(std::min<size_t>(dbfs.size(), static_cast<size_t>(capacity)));
    const bool overflow = static_cast<int>(dbfs.size()) > capacity;

    for (int area0 = 0; area0 < toOpen; ++area0) {
        const auto& de = dbfs[area0];

        OpenResult r;
        r.area = area0;
        r.dbf = de.path();

        try {
            xbase::DbArea& A = get_area_0based(area0);
            try { orderstate::clearOrder(A); } catch (...) {}
            workspace_memo_auto_close_before_dbf_close(A);
            try { A.close(); } catch (...) {}

            const string dbfStr = s8(r.dbf);
            A.open(dbfStr);
            A.setFilename(dbfStr);
            workspace_memo_auto_attach_after_dbf_open(A, r.dbf, "WORKSPACE OPEN");

            r.opened = true;

            r.indexFile = find_index_for_open_area(A, r.dbf, mode, fallback);
            if (r.indexFile.has_value()) {
                r.indexAttached = attach_workspace_index(A, *r.indexFile, r.indexError);
            }
        } catch (const std::exception& ex) {
            r.error = ex.what();
        } catch (...) {
            r.error = "Unknown error.";
        }

        results.push_back(std::move(r));
    }

    if (overflow) {
        OpenResult r;
        r.area = -1;
        const int skipped = static_cast<int>(dbfs.size()) - capacity;
        r.error = "Exceeded MAX_AREA (" + std::to_string(capacity) + "). Only first " +
                  std::to_string(capacity) + " table(s) opened; " +
                  std::to_string(skipped) + " additional table(s) were skipped.";
        results.push_back(std::move(r));
    }

    return results;
}

static std::vector<OpenResult> schema_open_directory_recursive(const fs::path& dir, IndexMode mode, bool fallback) {
    std::cout << "WORKSPACE OPEN: 'recursive' requested -- stubbed; falling back to flat scan.\n";
    return schema_open_directory(dir, mode, fallback);
}

static OpenResult schema_open_single_into_current(xbase::DbArea& current, const fs::path& dbfPath, IndexMode mode, bool fallback) {
    OpenResult r;
    r.dbf = dbfPath;
    r.area = get_area_index(current);

    try {
        try { orderstate::clearOrder(current); } catch (...) {}
        workspace_memo_auto_close_before_dbf_close(current);
        try { current.close(); } catch (...) {}

        const string dbfStr = s8(dbfPath);
        current.open(dbfStr);
        current.setFilename(dbfStr);
        workspace_memo_auto_attach_after_dbf_open(current, dbfPath, "WORKSPACE OPEN");

        r.opened = true;

        r.indexFile = find_index_for_open_area(current, dbfPath, mode, fallback);
        if (r.indexFile.has_value()) {
            r.indexAttached = attach_workspace_index(current, *r.indexFile, r.indexError);
        }
    } catch (const std::exception& ex) {
        r.error = ex.what();
    } catch (...) {
        r.error = "Unknown error.";
    }

    return r;
}

static bool open_into_area(int area0,
                           const fs::path& dbf,
                           const std::optional<fs::path>& index,
                           string* err,
                           bool* index_attached = nullptr,
                           string* index_error = nullptr,
                           const char* context = "WORKSPACE LOAD") {
    if (index_attached) *index_attached = false;
    if (index_error) index_error->clear();
    try {
        xbase::DbArea& A = get_area_0based(area0);
        try { orderstate::clearOrder(A); } catch (...) {}
        workspace_memo_auto_close_before_dbf_close(A);
        try { A.close(); } catch (...) {}

        const string dbfStr = s8(dbf);
        A.open(dbfStr);
        A.setFilename(dbfStr);
        workspace_memo_auto_attach_after_dbf_open(A, dbf, context);

        if (index && !index->empty()) {
            fs::path ip = *index;
            if (!ip.is_absolute()) ip = resolve_relative_to_root(ip);
            if (fs::exists(ip)) {
                std::string attach_err;
                const bool attached = attach_workspace_index(A, ip, attach_err);
                if (index_attached) *index_attached = attached;
                if (index_error && !attached) *index_error = attach_err;
            } else if (index_error) {
                *index_error = "index file not found: " + s8(ip);
            }
        }
        return true;
    } catch (const std::exception& ex) {
        if (err) *err = ex.what();
        return false;
    } catch (...) {
        if (err) *err = "Unknown error.";
        return false;
    }
}

// --------- Printing / List --------------------------------------------------

static void print_open_results(const std::vector<OpenResult>& results) {
    int openedCount = 0;
    int first = -1;
    int last = -1;

    for (const auto& r : results) {
        if (r.area < 0 && !r.error.empty()) {
            std::cout << "  ! " << r.error << "\n";
            continue;
        }

        std::cout << "  Area " << r.area << ": ";
        if (!r.opened) {
            std::cout << "FAILED to open '" << s8(r.dbf.filename()) << "'";
            if (!r.error.empty()) std::cout << " (" << r.error << ")";
            std::cout << "\n";
            continue;
        }

        if (first < 0) first = r.area;
        last = r.area;
        ++openedCount;

        std::cout << "opened '" << s8(r.dbf.filename()) << "'";
        if (r.indexFile.has_value()) {
            std::cout << "  [index: " << s8(r.indexFile->filename())
                      << (r.indexAttached ? ", attached" : ", found (not attached)") << "]";
            if (!r.indexAttached && !r.indexError.empty()) {
                std::cout << " (" << r.indexError << ")";
            }
        }
        std::cout << "\n";
    }

    std::cout << "WORKSPACE: " << openedCount << " table(s) opened";
    if (openedCount > 0) std::cout << " into area(s) " << first << ".." << last;
    const int capacity = xbase::MAX_AREA;
    if (openedCount >= capacity) std::cout << " (capped at MAX_AREA=" << capacity << ")";
    std::cout << ".\n";
}

static void schema_list_open(bool show_all) {
    std::cout << "WORKSPACE: Listing open work areas...\n";

    int open_count = 0;
    for (int area0 = 0; area0 < xbase::MAX_AREA; ++area0) {
        xbase::DbArea& A = get_area_0based(area0);
        if (!A.isOpen()) {
            if (show_all) {
                std::cout << "  Area " << area0 << ": --- closed ---\n";
            }
            continue;
        }
        ++open_count;
        std::cout << "  Area " << area0 << ": " << A.filename() << "\n";
    }

    if (show_all) {
        std::cout << "WORKSPACE: " << open_count << " of " << xbase::MAX_AREA << " area(s) in use.\n";
    } else {
        std::cout << "WORKSPACE: " << open_count << " area(s) open.\n";
    }
}

#if HAVE_RELATIONS
static inline void clear_relations_all_safe() {
    try { relations_api::clear_all_relations(); } catch (...) {}
    try { relations_api::set_current_parent_name(""); } catch (...) {}
}
#else
static inline void clear_relations_all_safe() {}
#endif

#if HAVE_RELATIONS
static inline void refresh_relations_if_enabled_safe() {
    try { relations_api::refresh_if_enabled(); } catch (...) {}
}
#else
static inline void refresh_relations_if_enabled_safe() {}
#endif

// --------- CLOSE helpers ----------------------------------------------------

static bool close_area_if_open(int area0) {
    try {
        xbase::DbArea& A = get_area_0based(area0);
        if (!area_open(A)) return false;

        try { orderstate::clearOrder(A); } catch (...) {}

        try {
#if DOTTALK_HAS_XINDEX
            const auto* im = xindex::manager_if_attached(A);
            if (im && im->hasBackend()) {
                xindex::ensure_manager(A).close();
            }
#endif
        } catch (...) {}

        // Close DTX memo sidecar backend owned by memo_auto.cpp before
        // DbArea::close() clears runtime identity. This prevents .dtx files
        // from remaining locked after WORKSPACE CLOSE / reload cycles.
        try { cli_memo::memo_auto_on_close(A); } catch (...) {}

        try { A.close(); } catch (...) {}
        try { A.setFilename(""); } catch (...) {}

#if HAVE_TABLE
        try {
            dottalk::table::set_enabled(area0, false);
            dottalk::table::set_dirty(area0, false);
            dottalk::table::set_stale(area0, false);
        } catch (...) {}
#endif
        return true;
    } catch (...) {
        return false;
    }
}

static void schema_close_all() {
    std::cout << "WORKSPACE CLOSE: Closing all work areas...\n";
    int close_count = 0;
    for (int area0 = 0; area0 < xbase::MAX_AREA; ++area0) {
        if (close_area_if_open(area0)) close_count++;
    }

#if HAVE_RELATIONS
    clear_relations_all_safe();
#endif

#if HAVE_TABLE
    try { dottalk::table::reset_all(); } catch (...) {}
#endif

    normalize_selected_area_after_workspace_change(0);

    std::cout << "WORKSPACE: " << close_count << " area(s) closed.\n";
}

static int schema_close_matching_token(const string& token) {
    const string t = to_lower(token);
    int close_count = 0;

    for (int area0 = 0; area0 < xbase::MAX_AREA; ++area0) {
        try {
            xbase::DbArea& A = get_area_0based(area0);
            if (!area_open(A)) continue;

            fs::path p = fs::path(A.filename());
            const string full  = to_lower(s8(p));
            const string base  = to_lower(s8(p.filename()));
            const string stem  = to_lower(s8(p.stem()));
            const string alias = to_lower(getNameIf(A, 0));

            if (full == t || base == t || stem == t || (!alias.empty() && alias == t)) {
                if (close_area_if_open(area0)) close_count++;
            }
        } catch (...) {}
    }
    return close_count;
}

// --------- RELATIONS IO (optional) ------------------------------------------

#if HAVE_RELATIONS
static bool same_field_list_ci(const std::vector<std::string>& a,
                               const std::vector<std::string>& b) {
    if (a.size() != b.size()) return false;
    auto naked = [](std::string s) {
        auto dot = s.find('.');
        if (dot != std::string::npos) s = s.substr(dot + 1);
        return to_upper(trim_copy(std::move(s)));
    };
    for (std::size_t i = 0; i < a.size(); ++i) {
        if (naked(a[i]) != naked(b[i])) return false;
    }
    return true;
}

static std::string join_csv(const std::vector<std::string>& fields) {
    std::ostringstream oss;
    for (std::size_t i = 0; i < fields.size(); ++i) {
        if (i) oss << ",";
        oss << fields[i];
    }
    return oss.str();
}

static std::vector<string> export_relations_lines() {
    std::vector<string> lines;
    try {
        for (const auto& rs : relations_api::export_relations()) {
            const std::vector<std::string>& parent_fields =
                !rs.parent_fields.empty() ? rs.parent_fields : rs.fields;
            const std::vector<std::string>& child_fields =
                !rs.child_fields.empty() ? rs.child_fields : rs.fields;

            std::ostringstream oss;
            oss << rs.parent << " " << rs.child << " ON " << join_csv(parent_fields);
            if (!child_fields.empty() && !same_field_list_ci(parent_fields, child_fields)) {
                oss << " TO " << join_csv(child_fields);
            }
            lines.push_back(oss.str());
        }
    } catch (...) {}
    return lines;
}
#else
static std::vector<string> export_relations_lines() { return {}; }
#endif

static bool apply_relation_line(const std::string& body) {
#if HAVE_RELATIONS
    auto trim_copy_local = [](std::string s) {
        auto is_space = [](unsigned char ch){ return std::isspace(ch) != 0; };
        s.erase(s.begin(), std::find_if(s.begin(), s.end(), [&](unsigned char c){ return !is_space(c); }));
        s.erase(std::find_if(s.rbegin(), s.rend(), [&](unsigned char c){ return !is_space(c); }).base(), s.end());
        return s;
    };

    auto up_token = [](std::string s) {
        for (auto& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        return s;
    };

    std::istringstream rss(body);
    std::string parent, child, on;
    rss >> parent >> child >> on;

    if (parent.empty() || child.empty() || up_token(on) != "ON") {
        std::cout << "  ! RELATION skipped (bad syntax): " << body << "\n";
        return false;
    }

    std::string rest;
    std::getline(rss, rest);
    rest = trim_copy_local(rest);
    if (rest.empty()) {
        std::cout << "  ! RELATION skipped (no fields): " << body << "\n";
        return false;
    }

    // Workspace relation lines support both legacy same-field form:
    //   RELATION PARENT CHILD ON FIELD1,FIELD2
    // and asymmetric metadata/system-dictionary form:
    //   RELATION PARENT CHILD ON PARENT_FIELD TO CHILD_FIELD
    std::string parent_csv;
    std::string child_csv;
    bool saw_to = false;
    {
        std::istringstream toks(rest);
        std::string tok;
        while (toks >> tok) {
            if (up_token(tok) == "TO") {
                saw_to = true;
                continue;
            }
            std::string& dest = saw_to ? child_csv : parent_csv;
            if (!dest.empty()) dest += ' ';
            dest += tok;
        }
    }

    std::vector<std::string> parent_fields = split_tokens(parent_csv);
    std::vector<std::string> child_fields  = saw_to ? split_tokens(child_csv) : parent_fields;

    if (parent_fields.empty() || child_fields.empty()) {
        std::cout << "  ! RELATION skipped (no fields): " << body << "\n";
        return false;
    }

    bool ok = false;
    if (saw_to) {
        ok = relations_api::add_relation(parent, child, parent_fields, child_fields);
    } else {
        ok = relations_api::add_relation(parent, child, parent_fields);
    }

    if (!ok) {
        std::cout << "  ! RELATION rejected by engine: " << body << "\n";
        return false;
    }

    return true;
#else
    (void)body;
    return false;
#endif
}

// --------- SAVE / LOAD ------------------------------------------------------

// AIF-070 M1: serialization split from file I/O -- one format, two carriers.
// schema_save_to_string() is the SINGLE serializer; the file writer below
// (and the future memo carrier, M2) are thin shells around it. The returned
// text is the byte-exact .dtschema payload (LF line endings, as the binary
// file writer has always produced). Behavior of WORKSPACE SAVE: unchanged.
static std::string measure_open_flavor();  // defined below (carrier section)

// version: 2 = the proven format (default, untouched); 3 = owner-chartered
// 2026-08-11, valid for all flavors -- SAME body as 2 plus declarative lines
// (FLAVOR now; residence/TARGET arrives with the hydration step that gives it
// semantics -- a line with no consumer is a paper claim). Coexistence rule:
// v3 is opt-in per save; every v2 producer and consumer keeps working.
static std::string schema_save_to_string(int version = 2) {
    std::ostringstream out;

    auto weak_can = [](const fs::path& p) -> fs::path {
        std::error_code ec;
        fs::path r = fs::weakly_canonical(p, ec);
        return ec ? p : r;
    };

    auto comp_eq = [](const fs::path& a, const fs::path& b) -> bool {
#if defined(_WIN32)
        return ci_equal(s8(a), s8(b));
#else
        return s8(a) == s8(b);
#endif
    };

    auto is_under = [&](const fs::path& absP, const fs::path& root) -> bool {
        fs::path p = absP;
        fs::path r = root;
        auto pit = p.begin();
        auto rit = r.begin();
        for (; rit != r.end(); ++rit, ++pit) {
            if (pit == p.end()) return false;
            if (!comp_eq(*pit, *rit)) return false;
        }
        return true;
    };

    auto rel_if_under = [&](const fs::path& pIn, const fs::path& root) -> std::string {
        fs::path p = weak_can(pIn);
        fs::path r = weak_can(root);
        if (!r.empty() && p.is_absolute() && is_under(p, r)) {
            fs::path rel = p.lexically_relative(r);
            if (!rel.empty() && rel.native() != p.native()) return s8(rel);
        }
        return s8(p);
    };

    const fs::path rootDbf = dbf_root();
    const fs::path rootIdx = idx_root();

    out << "DTSHEMA " << (version == 3 ? 3 : 2) << "\n";
    if (version == 3) {
        // v3 declarative lines (owner-chartered 2026-08-11). Roots make the
        // posture SELF-LOCATING: the v3 loader resolves relative dbf/index
        // entries against these instead of demanding a pre-set environment.
        // LMDB root is recorded for disk residence; RAM lmdb is per-mount and
        // transient, so its application stays chartered (owner: "lmdb only
        // for disks").
        const std::string fl = measure_open_flavor();
        if (!fl.empty()) out << "FLAVOR " << fl << "\n";
        out << "DBFROOT " << s8(rootDbf) << "\n";
        out << "IDXROOT " << s8(rootIdx) << "\n";
        out << "LMDBROOT " << s8(paths::get_slot(paths::Slot::LMDB)) << "\n";
    }

    for (int area0 = 0; area0 < xbase::MAX_AREA; ++area0) {
        try {
            xbase::DbArea& A = get_area_0based(area0);
            if (!area_open(A)) continue;

            fs::path dbfPath = fs::path(A.filename());
            std::string index = getOrderNameSafe(A);
            std::string tag   = getActiveTagSafe(A);
            std::string indexType = infer_index_type_from_path(index);
            const std::string alias = getNameIf(A, 0);

            std::string dbfOut = rel_if_under(dbfPath, rootDbf);
            std::string idxOut = index.empty() ? "none" : rel_if_under(fs::path(index), rootIdx);

            out << "AREA " << area0
                << " | dbf="       << dbfOut
                << " | index="     << (idxOut.empty() ? "none" : idxOut)
                << " | indextype=" << (indexType.empty() ? "NONE" : indexType)
                << " | tag="       << (tag.empty() ? "none" : tag);

            if (!alias.empty()) out << " | alias=" << alias;
            out << "\n";
        } catch (...) {}
    }

    for (const auto& rline : export_relations_lines()) {
        out << "RELATION " << rline << "\n";
    }

    // AIF-074 P1.1: persist unique/primary key declarations (unique_reg Phase 2).
    // KEY <table> <field> UNIQUE|PRIMARY -- older loaders skip unknown line kinds.
    for (int area0 = 0; area0 < xbase::MAX_AREA; ++area0) {
        try {
            xbase::DbArea& A = get_area_0based(area0);
            if (!area_open(A)) continue;
            const std::string tname = getNameIf(A, 0);
            if (tname.empty()) continue;
            const std::string prim = unique_reg::primary_field(A);
            for (const auto& f : unique_reg::list_unique_fields(A)) {
                out << "KEY " << tname << " " << f
                    << (f == prim ? " PRIMARY" : " UNIQUE") << "\n";
            }
        } catch (...) {}
    }

    if (version == 3) {
        // Session state (owner requirement 2026-08-11): cursor positions and
        // the selected area, so a restore resumes EXACTLY where the session
        // stood -- not at row 1. PHYSICAL recno is recorded (the GPS prior
        // art: physical is the anchor, logical row is derived from it under
        // the active order); GPS is the natural post-restore verifier.
        for (int area0 = 0; area0 < xbase::MAX_AREA; ++area0) {
            try {
                xbase::DbArea& A = get_area_0based(area0);
                if (!area_open(A)) continue;
                const std::uint64_t rn = A.recno64();
                if (rn > 0) out << "CURSOR " << area0 << " " << rn << "\n";
            } catch (...) {}
        }
        try {
            auto* eng = shell_engine();
            if (eng) out << "CURRENT " << eng->currentArea() << "\n";
        } catch (...) {}
    }

    return out.str();
}

// Instance identity (owner rule 2026-08-11): every serialized posture carries
// a unique WSID line whose PREFIX is its carrier flavor -- F<utc-stamp> for
// file/RAM saves, M<catalog ws_id> for memo saves. This does NOT replace the
// format version line (DTSHEMA 2 stays). The FORMAT is identical across
// carriers; the INSTANCE is identified. Old loaders skip the line unharmed
// (the KEY-line tolerance precedent); the current loader echoes it.
static std::string stamp_ws_id(std::string payload, const std::string& id) {
    const auto nl = payload.find('\n');
    if (nl == std::string::npos) return payload;
    payload.insert(nl + 1, "WSID " + id + "\n");
    return payload;
}

// FLAVOR is MEASURED from the open areas at save time, never declared
// (owner nod 2026-08-11). versionByte 0x64 / kind V128 = X64; version
// 0x30-0x32 = VFP; kind V32 (0x03/0x83/0xF5) = X32. All areas agree ->
// that flavor; disagree -> MIXED; nothing open -> empty (claim withheld).
static std::string measure_open_flavor() {
    std::string fl;
    for (int area0 = 0; area0 < xbase::MAX_AREA; ++area0) {
        try {
            xbase::DbArea& A = get_area_0based(area0);
            if (!area_open(A)) continue;
            std::string f = "OTHER";
            const std::uint8_t vb = A.versionByte();
            if (vb == xbase::DBF_VERSION_64 || A.kind() == xbase::AreaKind::V128) f = "X64";
            else if (vb == 0x30 || vb == 0x31 || vb == 0x32) f = "VFP";
            else if (A.kind() == xbase::AreaKind::V32) f = "X32";
            if (fl.empty()) fl = f;
            else if (fl != f) return "MIXED";
        } catch (...) {}
    }
    return fl;
}

static std::string file_carrier_wsid() {
    std::time_t t = std::time(nullptr);
    char buf[20] = {0};
    std::tm tmv{};
#if defined(_WIN32)
    gmtime_s(&tmv, &t);
#else
    gmtime_r(&t, &tmv);
#endif
    std::strftime(buf, sizeof(buf), "%Y%m%dT%H%M%SZ", &tmv);
    return std::string("F") + buf;
}

static void schema_save_to_file(const fs::path& file, int version = 2) {
    fs::path outPath = resolve_workspace_file_path(file, true);

    {
        std::error_code ec;
        if (outPath.has_parent_path() && !outPath.parent_path().empty()) {
            fs::create_directories(outPath.parent_path(), ec);
        }
    }

    std::ofstream out(outPath, std::ios::binary);
    if (!out.good()) {
        std::cout << "WORKSPACE SAVE: cannot write file: " << s8(outPath) << "\n";
        return;
    }

    out << stamp_ws_id(schema_save_to_string(version), file_carrier_wsid());
    out.flush();
    std::cout << "WORKSPACE SAVE: wrote " << s8(outPath) << "\n";
}

// AIF-070 M1: loader split from file I/O. schema_load_from_stream() is the
// SINGLE parser; the file loader below (and the future memo carrier, M3)
// feed it an open stream plus a source label used for messages and the
// last-loaded-workspace state. Behavior of WORKSPACE LOAD: unchanged.
static void schema_load_from_stream(std::istream& in, const std::string& sourceLabel) {

    auto weak_can = [](const fs::path& p) -> fs::path {
        std::error_code ec;
        fs::path r = fs::weakly_canonical(p, ec);
        return ec ? p : r;
    };

    // Non-const: a v3 posture's DBFROOT/IDXROOT lines re-point these for this
    // load only (self-locating posture); the resolve lambdas capture by
    // reference, so later AREA lines resolve against the payload's roots.
    // Global SETPATH slots are never mutated.
    fs::path rootDbf = dbf_root();
    fs::path rootIdx = idx_root();

    auto resolve_dbf = [&](const fs::path& p) -> fs::path {
        fs::path q = translate_cross_os_absolute(p);
        if (q.is_absolute() || looks_like_windows_abs(q) || looks_like_posix_abs(q)) {
            return weak_can(q);
        }
        return weak_can(rootDbf / q);
    };

    auto resolve_index = [&](const fs::path& p) -> fs::path {
        fs::path q = translate_cross_os_absolute(p);
        if (q.is_absolute() || looks_like_windows_abs(q) || looks_like_posix_abs(q)) {
            return weak_can(q);
        }

        fs::path cand = rootIdx / q;
        std::error_code ec;
        if (fs::exists(cand, ec) && !ec) return weak_can(cand);

        return weak_can(rootDbf / q);
    };

    std::string header;
    std::getline(in, header);
    const std::string headerNorm = to_lower(trim_copy(header));

    int schemaVersion = 0;
    if (headerNorm == "dtshema 1") schemaVersion = 1;
    else if (headerNorm == "dtshema 2") schemaVersion = 2;
    else if (headerNorm == "dtshema 3") schemaVersion = 3;  // superset of 2; extra declarative lines
    else {
        std::cout << "WORKSPACE LOAD: bad or unsupported file header.\n";
        return;
    }

    last_loaded_workspace_file() = sourceLabel;

    schema_close_all();

    std::string line;
    int area_count = 0;
    int relation_count = 0;
    int relation_rejected_count = 0;
    int cursor_count = 0;       // v3 session state
    int pending_current = -1;   // v3 selected area; applied after the loop

    while (std::getline(in, line)) {
        std::string t = trim_copy(line);
        if (t.empty()) continue;

        if (to_lower(t).rfind("area ", 0) == 0) {
            int n = -1;
            {
                std::istringstream ss(t.substr(5));
                ss >> n;
            }

            if (n < 0 || n >= xbase::MAX_AREA) {
                std::cout << "  ! Skip AREA out of range: " << n << "\n";
                continue;
            }

            auto get_field = [&](const char* key) -> std::string {
                auto pos = t.find(std::string(key));
                if (pos == std::string::npos) return {};
                pos += std::char_traits<char>::length(key);
                auto end = t.find('|', pos);
                std::string v = (end == std::string::npos) ? t.substr(pos) : t.substr(pos, end - pos);
                return trim_copy(v);
            };

            fs::path dbf = get_field("dbf=");
            std::string idx = get_field("index=");
            std::string indexType = get_field("indextype=");
            std::string tag = get_field("tag=");
            std::string alias = get_field("alias=");

            if (dbf.empty()) {
                std::cout << "  ! AREA " << n << ": missing dbf path, skipping.\n";
                continue;
            }

            fs::path dbf_resolved = resolve_dbf(dbf);
            std::optional<fs::path> indexPath;
            if (!idx.empty() && to_lower(idx) != "none") {
                indexPath = resolve_index(fs::path(idx));
            }
            if (indexType.empty() && indexPath.has_value()) {
                indexType = infer_index_type_from_path(indexPath->string());
            }
            if (schemaVersion < 2) tag.clear();

            std::string err;
            bool ok = open_into_area(n, dbf_resolved, indexPath, &err);
            if (!ok) {
                std::cout << "  ! AREA " << n << ": open failed (" << err << ")\n";
            } else {
                try {
                    xbase::DbArea& A = get_area_0based(n);
                    if (!alias.empty() && to_lower(alias) != "none") {
                        setLogicalNameIf(A, alias, 0);
                        setLegacyNameIf(A, alias, 0);
                    }
                    if (!tag.empty() && to_lower(tag) != "none") {
                        if (!setActiveTagSafe(A, tag)) {
                            std::cout << "  ! AREA " << n << ": tag '" << tag
                                      << "' could not be activated";
                            if (!indexType.empty()) std::cout << " (type=" << indexType << ")";
                            std::cout << ".\n";
                        }
                    }
                } catch (...) {}
                ++area_count;
            }

        } else if (to_lower(t).rfind("relation ", 0) == 0) {
            std::string body = trim_copy(t.substr(9));
#if HAVE_RELATIONS
            if (apply_relation_line(body)) {
                ++relation_count;
            } else {
                ++relation_rejected_count;
            }
#else
            std::cout << "  ~ RELATION ignored (relations module not present): " << body << "\n";
#endif
        } else if (to_lower(t).rfind("flavor ", 0) == 0) {
            // v3 declarative line: flavor the posture was measured as at save.
            // Informational on load today; admission checks may consume later.
            std::cout << "  FLAVOR: " << trim_copy(t.substr(7)) << "\n";
        } else if (to_lower(t).rfind("dbfroot ", 0) == 0) {
            // v3 self-locating roots (owner suggestion 2026-08-11): the
            // posture carries where its tables live. Applied to THIS load's
            // resolution only -- global SETPATH slots are never mutated.
            rootDbf = fs::path(trim_copy(t.substr(8)));
            std::cout << "  DBFROOT: " << s8(rootDbf) << "\n";
        } else if (to_lower(t).rfind("idxroot ", 0) == 0) {
            rootIdx = fs::path(trim_copy(t.substr(8)));
            std::cout << "  IDXROOT: " << s8(rootIdx) << "\n";
        } else if (to_lower(t).rfind("lmdbroot ", 0) == 0) {
            // Recorded + echoed; application is chartered (disk-only rule).
            std::cout << "  LMDBROOT: " << trim_copy(t.substr(9)) << " (recorded, not applied)\n";
        } else if (to_lower(t).rfind("wsid ", 0) == 0) {
            // Instance identity line (owner rule 2026-08-11): carrier-flavored
            // unique id. Informational on load; the version line above still
            // governs parsing.
            std::cout << "  WSID: " << trim_copy(t.substr(5)) << "\n";
        } else if (to_lower(t).rfind("cursor ", 0) == 0) {
            // v3 session state: restore the physical recno (GPS anchor).
            // Emitted after AREA/REL lines, so the area is already open.
            int n = -1; std::uint64_t rn = 0;
            std::istringstream cs(t.substr(7)); cs >> n >> rn;
            if (n >= 0 && n < xbase::MAX_AREA && rn > 0) {
                try {
                    xbase::DbArea& A = get_area_0based(n);
                    if (area_open(A) && A.gotoRec64(rn)) { A.readCurrent(); ++cursor_count; }
                } catch (...) {}
            }
        } else if (to_lower(t).rfind("current ", 0) == 0) {
            // v3 session state: the selected area, applied after the loop.
            int n = -1;
            std::istringstream cs(t.substr(8)); cs >> n;
            if (n >= 0 && n < xbase::MAX_AREA) pending_current = n;
        } else if (to_lower(t).rfind("key ", 0) == 0) {
            // AIF-074 P1.1: KEY <table> <field> UNIQUE|PRIMARY -> unique_reg.
            std::string body = trim_copy(t.substr(4));
            std::istringstream ks(body);
            std::string tbl, fld, kind;
            ks >> tbl >> fld >> kind;
            if (tbl.empty() || fld.empty()) {
                std::cout << "  ! KEY skipped (bad syntax): " << body << "\n";
            } else if (xbase::DbArea* ka = cli::find_open_area_by_name_ci(tbl)) {
                const bool is_primary = (to_lower(kind) == "primary");
                unique_reg::set_unique_field(*ka, fld, true);
                if (is_primary) unique_reg::set_primary_field(*ka, fld);
                std::cout << "  KEY: " << tbl << "." << fld
                          << (is_primary ? " PRIMARY" : " UNIQUE") << "\n";
            } else {
                std::cout << "  ! KEY skipped (table not open): " << tbl << "\n";
            }
        } else {
            std::cout << "  ~ Unknown line (ignored): " << t << "\n";
        }
    }

    // v3 session state: the saved selection outranks normalization; the
    // final refresh below then slaves children to the RESTORED parents
    // (refresh-driven house semantic), completing "resume exactly here".
    if (pending_current >= 0) (void)select_engine_area(pending_current);
    else normalize_selected_area_after_workspace_change();

    std::cout << "WORKSPACE LOAD: restored " << area_count << " area(s)";
#if HAVE_RELATIONS
    std::cout << " and " << relation_count << " relation(s)";
    if (relation_rejected_count > 0) {
        std::cout << " (" << relation_rejected_count << " rejected)";
    }
#else
    std::cout << " (relations: stubbed)";
#endif
    if (cursor_count > 0) std::cout << " (+ " << cursor_count << " cursor(s))";
    std::cout << ".\n";
    // WORKSPACE LOAD is a structural lifecycle operation: areas and
    // optional relations have now been fully restored. Refresh only after
    // the complete load so relation caches do not see a half-built state.
    relations_boot::retry_pending_autoload();
    refresh_relations_if_enabled_safe();
}

static void schema_load_from_file(const fs::path& file) {
    fs::path inPath = resolve_workspace_file_path(file, false);

    std::ifstream in(inPath, std::ios::binary);
    if (!in.good()) {
        std::cout << "WORKSPACE LOAD: cannot read file: " << s8(inPath) << "\n";
        return;
    }

    schema_load_from_stream(in, s8(inPath));
}

// ===================== AIF-070 M2: the memo carrier =========================
// One format, two carriers: the .dtschema text from schema_save_to_string()
// is stored byte-exact in a memo field of the WORKSPACES catalog (X64 table
// in the workspaces root, standalone DbArea -- deliberately OUTSIDE the work
// areas so saving never disturbs the state being saved; the bbs_store
// pattern). Oracle gate: every memo save is immediately read back and
// byte-compared against the serialized string -- mismatch is a loud hard
// fail. History is append-only (owner ruling D4): a re-save marks the prior
// live row SUPERSEDED=1 and appends a fresh row. Attribution is mandatory
// (AIF-075): AUTHOR records current_member id/kind. DBF_ROOT/IDX_ROOT record
// the SET PATH env active at save time, because .dtschema payloads are
// root-relative by design -- a snapshot declares its own preconditions
// (lesson measured 2026-08-11: a load under the wrong roots resolves 0/58).

namespace ws_memo {

static fs::path catalog_dir() {
    // The same root WORKSPACE SAVE files land in (owner ruling D2).
    return resolve_workspace_file_path(fs::path("_probe"), true).parent_path();
}
static fs::path catalog_path() { return catalog_dir() / "WORKSPACES.dbf"; }

// RAII whole-table lock; the bbs_store idiom (cross-process FLOCK,
// pid-stamped, stale-owner recovering). Appends grow the header, so
// whole-table granularity is correct.
struct WsLock {
    xbase::DbArea& a; bool held = false;
    WsLock(xbase::DbArea& area, std::string& err) : a(area) {
        std::string lerr;
        held = xbase::locks::try_lock_table(a, &lerr);
        if (!held && err.empty())
            err = "WORKSPACE MEMO: catalog busy (locked by another process)"
                  + (lerr.empty() ? std::string() : ": " + lerr);
    }
    ~WsLock() { if (held) xbase::locks::unlock_table(a); }
    explicit operator bool() const { return held; }
    WsLock(const WsLock&) = delete;
    WsLock& operator=(const WsLock&) = delete;
};

static bool set_by_name(xbase::DbArea& a, const char* col, const std::string& v, std::string& err) {
    const int i = fields::findFieldCI(a, col);   // 0-based; -1 = missing
    if (i < 0) { err = std::string("WORKSPACE MEMO: catalog missing column ") + col; return false; }
    if (!a.set(i + 1, v)) { err = std::string("WORKSPACE MEMO: cannot set ") + col; return false; }
    return true;
}
static std::string get_by_name(const xbase::DbArea& a, const char* col) {
    const int i = fields::findFieldCI(a, col);
    return i >= 0 ? a.get(i + 1) : std::string();
}

static std::string now_stamp() {
    std::time_t t = std::time(nullptr);
    char buf[20] = {0};
    std::tm tmv{};
#if defined(_WIN32)
    localtime_s(&tmv, &t);
#else
    localtime_r(&t, &tmv);
#endif
    std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &tmv);
    return buf;
}

static std::string author_stamp() {
    std::uint64_t id = 0; int kind = 0;
    try { dottalk::identity::current_member(id, kind); } catch (...) {}
    return "member#" + std::to_string(id) + "/kind" + std::to_string(kind);
}

static bool ensure_catalog(std::string& err) {
    std::error_code ec;
    if (fs::exists(catalog_path(), ec)) return true;
    fs::create_directories(catalog_dir(), ec);

    // Catalog v2 (owner design session 2026-08-11): single-key identity
    // (WS_NAME is the human handle -- NO composite keys, owner ruling),
    // WS_ID surrogate for machine identity + PREV_ID lineage chains,
    // dimensions as queryable attributes, FMT for future payload kinds
    // (DTSHEMA 2 today, MINIDB later), DEPTH/SELF_REF as the recursion
    // guard's declaration half, budget fields for hydration admission.
    // PAYLOAD_SHA / EST_HYD_B / VERIFIED_AT / dimension fields are created
    // now and populated by later milestones -- an empty column is a
    // chartered claim, same rule as the public status board.
    std::vector<xbase::dbf_create::FieldSpec> f;
    auto C = [&](const char* n, std::uint32_t len) {
        xbase::dbf_create::FieldSpec s; s.name = n; s.type = 'C'; s.len = len; s.dec = 0;
        f.push_back(s);
    };
    auto N = [&](const char* n, std::uint32_t len) {
        xbase::dbf_create::FieldSpec s; s.name = n; s.type = 'N'; s.len = len; s.dec = 0;
        f.push_back(s);
    };
    N("WS_ID", 10);        // unique auto-id (see allocation note in save_to_memo)
    C("WS_NAME", 32);      // THE key: the human handle you load by
    C("SCHEMA_NAME", 64);  // dimension: "My Community College" (M2 populates)
    C("FLAVOR", 8);        // dimension: X64/X32/VFP/REF (M2 populates)
    C("OS_COMPAT", 8);     // dimension: ALL/WIN/POSIX/MAC -- a CLAIM, not a partition
    C("FMT", 12);          // payload format tag: "DTSHEMA 2" now, "MINIDB n" later
    C("PAYLOAD_SHA", 64);  // integrity + cycle-detection material (chartered)
    N("SIZE_B", 12);       // payload bytes (populated now)
    N("EST_HYD_B", 12);    // estimated hydrated bytes (chartered; budget input)
    N("MAX_AREAS", 4);     // areas the posture opens (populated now; admission input)
    N("DEPTH", 2);         // MANDATORY recursion declaration: 0 = leaf posture
    C("SELF_REF", 1);      // payload references a workspace catalog (T/F)
    N("PREV_ID", 10);      // lineage: WS_ID of the row this save superseded (0 = first)
    C("SUPERSEDED", 1);
    C("SAVED_AT", 19); C("AUTHOR", 48);
    C("DBF_ROOT", 180); C("IDX_ROOT", 180);
    C("VERIFIED_AT", 19);  // last oracle re-verification (chartered; WORKSPACE VERIFY)
    // Memo token field: the canonical x64/DTX token is 16-char hex
    // (src/memo/memo_ref.cpp). len=10 (classic dBASE convention) TRUNCATED
    // the token and broke fresh-session reads -- measured 2026-08-11.
    { xbase::dbf_create::FieldSpec m; m.name = "SNAPSHOT"; m.type = 'M'; m.len = 16; m.dec = 0; f.push_back(m); }

    // Two name planes: physical descriptors planned like every x64 create.
    std::vector<std::string> names; names.reserve(f.size());
    for (const auto& s : f) names.push_back(s.name);
    const auto plans = xbase::field_name_policy::plan_x64_unique_fallback(names);
    for (std::size_t k = 0; k < f.size() && k < plans.size(); ++k)
        f[k].descriptor_name = plans[k].descriptor_name;

    return xbase::dbf_create::create_dbf(s8(catalog_path()), f,
                                         xbase::dbf_create::Flavor::X64, err);
}

static bool open_catalog(xbase::DbArea& a, std::string& err) {
    if (!ensure_catalog(err)) return false;
    try { a.open(s8(catalog_path())); }
    catch (const std::exception& e) { err = std::string("WORKSPACE MEMO: cannot open catalog: ") + e.what(); return false; }

    // v1-catalog guard: a WORKSPACES.dbf without WS_ID predates the v2
    // schema (2026-08-11). Refuse LOUDLY rather than mis-populate -- the
    // no-ALTER-add-field gap means we cannot upgrade in place yet.
    if (fields::findFieldCI(a, "WS_ID") < 0) {
        err = "WORKSPACE MEMO: catalog at " + s8(catalog_path()) +
              " is pre-v2 (no WS_ID). Remove WORKSPACES.* in the workspaces "
              "root and re-save; the catalog self-creates with the v2 schema.";
        a.close();
        return false;
    }

    // Declaration half of "use unique auto-id" (owner pointer: see
    // cmd_setunique.cpp): register WS_ID as the PRIMARY unique field in the
    // house uniqueness registry. VALIDATE UNIQUE can then police the catalog
    // like any other table, and the workspace serializer emits it as a
    // KEY line automatically. Generation half lives in save_to_memo.
    unique_reg::set_unique_field(a, "WS_ID", true);
    unique_reg::set_primary_field(a, "WS_ID");

    std::string merr;
    if (!cli_memo::memo_auto_on_use(a, s8(catalog_path()), true, merr)) {
        err = "WORKSPACE MEMO: memo sidecar: " + merr;
        a.close();
        return false;
    }
    return true;
}

static void save_to_memo(const std::string& name, int version = 2) {
    const std::string base = schema_save_to_string(version);

    std::string err;
    xbase::DbArea a;
    if (!open_catalog(a, err)) { std::cout << err << "\n"; return; }

    {
        WsLock lk(a, err);
        if (!lk) { std::cout << err << "\n"; cli_memo::memo_auto_on_close(a); a.close(); return; }

        // One scan, two jobs (under the FLOCK):
        //  - D4 append-history: supersede any prior live row of this name,
        //    remembering its WS_ID as this save's PREV_ID lineage.
        //  - WS_ID allocation, generation half of "use unique auto-id"
        //    (owner ruling 2026-08-11). Measured that day: the x64 header
        //    slot autoq_next EXISTS (xbase_64.hpp:52; init=1 at create;
        //    hydrated into the area at open, xbase_64.hpp:530) but is
        //    LOAD-ONLY -- no APPEND consumer, no increment, no store path
        //    back to the header. Wiring those three is a chartered engine
        //    lane. Until it lands: max(WS_ID)+1 under this FLOCK -- the
        //    proven bbs_store next_id pattern, self-healing after any
        //    manual edit and forward-compatible with the autoq wiring.
        std::uint64_t maxId = 0, prevId = 0;
        const std::uint64_t n = a.recCount64();
        for (std::uint64_t r = 1; r <= n; ++r) {
            try {
                a.gotoRec(static_cast<int32_t>(r)); a.readCurrent();
                const std::uint64_t rid =
                    std::strtoull(trim_copy(get_by_name(a, "WS_ID")).c_str(), nullptr, 10);
                if (rid > maxId) maxId = rid;
                if (get_by_name(a, "WS_NAME") == name && get_by_name(a, "SUPERSEDED") != "1") {
                    prevId = rid;
                    if (!set_by_name(a, "SUPERSEDED", "1", err)) { std::cout << err << "\n"; }
                    else a.writeCurrent();
                }
            } catch (...) {}
        }
        const std::uint64_t newId = maxId + 1;

        // Instance identity (owner rule 2026-08-11): memo-carried postures
        // stamp a memo-flavored unique id -- M<ws_id> -- as a WSID line
        // after the DTSHEMA 2 header (version line untouched). The catalog
        // row and the payload now name each other.
        const std::string payload = stamp_ws_id(base, "M" + std::to_string(newId));

        // Derived metadata, measured from the payload itself.
        std::size_t areaCount = 0;
        for (std::size_t p = payload.find("\nAREA "); p != std::string::npos;
             p = payload.find("\nAREA ", p + 6)) ++areaCount;
        // SELF_REF heuristic: does the posture open the workspace catalog
        // family? Declaration only -- enforcement is the hydration stack.
        const bool selfRef = payload.find("WORKSPACES") != std::string::npos;

        // Fresh row + memo payload.
        auto* store = cli_memo::memo_store_for(a);
        if (!store || !store->is_open()) {
            std::cout << "WORKSPACE MEMO: memo backend not attached.\n";
            cli_memo::memo_auto_on_close(a); a.close(); return;
        }
        dottalk::memo::MemoPutResult mr = store->put_text(payload);
        if (!mr.ok) {
            std::cout << "WORKSPACE MEMO: memo write failed"
                      << (mr.error.empty() ? "" : (": " + mr.error)) << "\n";
            cli_memo::memo_auto_on_close(a); a.close(); return;
        }

        a.appendBlank();
        bool ok = set_by_name(a, "WS_ID", std::to_string(newId), err)
               && set_by_name(a, "WS_NAME", name, err)
               && set_by_name(a, "SCHEMA_NAME", name, err)   // display name; defaults to handle until owner supplies one
               && set_by_name(a, "FLAVOR", measure_open_flavor(), err)
               && set_by_name(a, "OS_COMPAT", "ALL", err)    // a CLAIM column, not a measurement
               && set_by_name(a, "FMT", version == 3 ? "DTSHEMA 3" : "DTSHEMA 2", err)
               && set_by_name(a, "SIZE_B", std::to_string(payload.size()), err)
               && set_by_name(a, "MAX_AREAS", std::to_string(areaCount), err)
               && set_by_name(a, "DEPTH", "0", err)          // leaf until hydration says otherwise
               && set_by_name(a, "SELF_REF", selfRef ? "T" : "F", err)
               && set_by_name(a, "PREV_ID", std::to_string(prevId), err)
               && set_by_name(a, "SAVED_AT", now_stamp(), err)
               && set_by_name(a, "AUTHOR", author_stamp(), err)
               && set_by_name(a, "SUPERSEDED", "0", err)
               && set_by_name(a, "DBF_ROOT", s8(dbf_root()), err)
               && set_by_name(a, "IDX_ROOT", s8(idx_root()), err)
               && set_by_name(a, "SNAPSHOT", mr.ref.token, err);
        // PAYLOAD_SHA / EST_HYD_B / VERIFIED_AT remain chartered columns.
        if (!ok) { std::cout << err << "\n"; cli_memo::memo_auto_on_close(a); a.close(); return; }
        a.writeCurrent();

        // ORACLE GATE: read the memo back and byte-compare. Loudly. The ref
        // comes FROM THE FIELD, not from memory -- the field is what a fresh
        // session will read, and a field-width truncation already slipped
        // past a memory-ref oracle once (2026-08-11).
        dottalk::memo::MemoRef ref{}; ref.token = trim_copy(get_by_name(a, "SNAPSHOT"));
        dottalk::memo::MemoGetResult back = store->get_text(ref);
        if (!back.ok || back.text != payload) {
            std::cout << "WORKSPACE MEMO: ORACLE FAIL -- readback "
                      << (back.ok ? "differs from serialized payload" : ("failed: " + back.error))
                      << " (" << payload.size() << " B written, "
                      << (back.ok ? std::to_string(back.text.size()) : std::string("?"))
                      << " B read). Row appended but NOT trustworthy.\n";
        } else {
            std::cout << "WORKSPACE SAVE: wrote memo '" << name << "' ("
                      << payload.size() << " B, oracle byte-compare OK) to "
                      << s8(catalog_path()) << "\n";
        }
    } // release FLOCK while area still open

    cli_memo::memo_auto_on_close(a);
    a.close();
}

// Shared payload fetch: last live row wins (append-history). Returns the
// payload text plus the row's recorded roots -- the v2 source-location
// fallback when the payload carries no DBFROOT/IDXROOT lines of its own.
struct MemoFetch {
    bool ok = false;
    std::string text, saved_at, dbf_root, idx_root, error;
};
static MemoFetch fetch_memo_payload(const std::string& name) {
    MemoFetch out;
    std::string err;
    xbase::DbArea a;
    if (!open_catalog(a, err)) { out.error = err; return out; }

    std::string token;
    const std::uint64_t n = a.recCount64();
    for (std::uint64_t r = 1; r <= n; ++r) {
        try {
            a.gotoRec(static_cast<int32_t>(r)); a.readCurrent();
            if (get_by_name(a, "WS_NAME") == name && get_by_name(a, "SUPERSEDED") != "1") {
                token        = trim_copy(get_by_name(a, "SNAPSHOT"));
                out.saved_at = get_by_name(a, "SAVED_AT");
                out.dbf_root = trim_copy(get_by_name(a, "DBF_ROOT"));
                out.idx_root = trim_copy(get_by_name(a, "IDX_ROOT"));
            }
        } catch (...) {}
    }

    if (token.empty()) {
        out.error = "WORKSPACE LOAD: no live memo workspace named '" + name + "'.";
        cli_memo::memo_auto_on_close(a); a.close(); return out;
    }

    auto* store = cli_memo::memo_store_for(a);
    if (!store || !store->is_open()) {
        out.error = "WORKSPACE MEMO: memo backend not attached.";
        cli_memo::memo_auto_on_close(a); a.close(); return out;
    }
    dottalk::memo::MemoRef ref{}; ref.token = token;
    dottalk::memo::MemoGetResult got = store->get_text(ref);
    cli_memo::memo_auto_on_close(a);
    a.close();

    if (!got.ok) {
        out.error = "WORKSPACE MEMO: memo read failed" +
                    (got.error.empty() ? std::string() : (": " + got.error));
        return out;
    }
    out.ok = true;
    out.text = std::move(got.text);
    return out;
}

static void load_from_memo(const std::string& name) {
    MemoFetch f = fetch_memo_payload(name);
    if (!f.ok) { std::cout << f.error << "\n"; return; }

    std::cout << "WORKSPACE LOAD: memo '" << name << "' (saved " << f.saved_at
              << ", " << f.text.size() << " B)\n";
    std::istringstream in(f.text);
    schema_load_from_stream(in, "memo:" + name);
}

// ---- memo -> RAM hydration (owner lane, step 2, 2026-08-11) ----------------
// Copy the posture's tables (and native index files) from their DISK homes
// into the mounted RAM VFS, then load the posture with its roots re-pointed
// at RAM -- the self-location mechanism from DTSHEMA 3 step 1, reused as the
// hydration vehicle. The copy goes through xbase::ramfs streams, NEVER
// std::filesystem: the VFS is in-process, and an OS-level copy would land on
// real disk while claiming RAM (a false hydration). LMDB is not hydrated --
// owner rule "lmdb only for disks", grounded in ramfs.hpp's own contract
// (LMDB must mmap a real OS file). Memo sidecars: no MCC table carries a
// memo field until the Part B regeneration lands; sidecar hydration is
// chartered WITH that lane. The hydration is TIMED and reports a number,
// not an adjective.
static void hydrate_to_ram(const std::string& name) {
    const fs::path ramRoot = paths::get_slot(paths::Slot::RAM);
    if (ramRoot.empty() || !xbase::ramfs::mounted(s8(ramRoot))) {
        std::cout << "WORKSPACE LOAD RAM: VDISK is not mounted -- run VDISK MOUNT "
                     "(or DO mem) first.\n";
        return;
    }

    MemoFetch f = fetch_memo_payload(name);
    if (!f.ok) { std::cout << f.error << "\n"; return; }

    // Source roots: payload DBFROOT/IDXROOT (v3) outrank the catalog row's
    // recorded roots (the v2 fallback).
    fs::path srcDbf = f.dbf_root.empty() ? dbf_root() : fs::path(f.dbf_root);
    fs::path srcIdx = f.idx_root.empty() ? idx_root() : fs::path(f.idx_root);
    struct Entry { std::string dbf, idx; };
    std::vector<Entry> entries;
    {
        std::istringstream scan(f.text);
        std::string line;
        while (std::getline(scan, line)) {
            const std::string t = trim_copy(line);
            const std::string low = to_lower(t);
            if (low.rfind("dbfroot ", 0) == 0)      srcDbf = fs::path(trim_copy(t.substr(8)));
            else if (low.rfind("idxroot ", 0) == 0) srcIdx = fs::path(trim_copy(t.substr(8)));
            else if (low.rfind("area ", 0) == 0) {
                auto field = [&](const char* key) -> std::string {
                    auto pos = t.find(key);
                    if (pos == std::string::npos) return {};
                    pos += std::char_traits<char>::length(key);
                    auto end = t.find('|', pos);
                    return trim_copy(end == std::string::npos ? t.substr(pos)
                                                             : t.substr(pos, end - pos));
                };
                Entry e; e.dbf = field("dbf="); e.idx = field("index=");
                if (!e.dbf.empty()) entries.push_back(e);
            }
        }
    }
    if (entries.empty()) {
        std::cout << "WORKSPACE LOAD RAM: payload has no AREA entries.\n";
        return;
    }

    const fs::path ramIdx = ramRoot / "indexes";   // the VDISK mount convention
    auto copy_into_ram = [&](const fs::path& src, const fs::path& dst,
                             std::uint64_t& bytes) -> bool {
        std::ifstream in(src, std::ios::binary);
        if (!in.good()) return false;
        auto out = xbase::ramfs::open(s8(dst), /*create*/true);
        if (!out) return false;
        char buf[1 << 16];
        while (in.read(buf, sizeof(buf)) || in.gcount() > 0) {
            out->write(buf, in.gcount());
            bytes += static_cast<std::uint64_t>(in.gcount());
        }
        out->flush();
        return true;
    };

    const auto t0 = std::chrono::steady_clock::now();
    std::uint64_t bytes = 0;
    int copied = 0, missing = 0;
    for (const auto& e : entries) {
        const fs::path srcTable = fs::path(e.dbf).is_absolute() ? fs::path(e.dbf)
                                                                : srcDbf / e.dbf;
        if (copy_into_ram(srcTable, ramRoot / fs::path(e.dbf).filename(), bytes)) ++copied;
        else { ++missing; std::cout << "  ! hydrate: missing source " << s8(srcTable) << "\n"; }

        if (!e.idx.empty() && to_lower(e.idx) != "none") {
            const fs::path srcIndex = fs::path(e.idx).is_absolute() ? fs::path(e.idx)
                                                                    : srcIdx / e.idx;
            if (copy_into_ram(srcIndex, ramIdx / fs::path(e.idx).filename(), bytes)) ++copied;
            // A missing index is not fatal: the loader already degrades loudly.
        }
    }

    // Re-point the payload at RAM and load through the standard v3 mechanism:
    // strip any root lines, inject RAM roots after the header.
    std::string hydrated;
    {
        std::istringstream scan(f.text);
        std::string line;
        bool first = true;
        while (std::getline(scan, line)) {
            const std::string low = to_lower(trim_copy(line));
            if (low.rfind("dbfroot ", 0) == 0 || low.rfind("idxroot ", 0) == 0 ||
                low.rfind("lmdbroot ", 0) == 0) continue;
            hydrated += line; hydrated += "\n";
            if (first) {
                hydrated += "DBFROOT " + s8(ramRoot) + "\n";
                hydrated += "IDXROOT " + s8(ramIdx) + "\n";
                first = false;
            }
        }
    }
    std::istringstream in(hydrated);
    schema_load_from_stream(in, "ram-memo:" + name);

    const auto t1 = std::chrono::steady_clock::now();
    const double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    std::cout << "WORKSPACE HYDRATE: memo '" << name << "' -> RAM: " << copied
              << " file(s), " << bytes << " B in " << ms << " ms"
              << (missing ? (" (" + std::to_string(missing) + " source(s) missing)") : "")
              << "\n";
}

} // namespace ws_memo


// --------- Tuple / Ordered Row View -----------------------------------------

struct WorkspaceTupleOptions {
    int area = -1;          // -1 = current area
    int limit = 25;
    int offset = 0;         // zero-based logical offset
};

static WorkspaceTupleOptions parse_tuple_options(const std::string& args) {
    WorkspaceTupleOptions opt{};
    auto toks = split_tokens(args);

    for (size_t i = 0; i < toks.size(); ++i) {
        const std::string tok = to_lower(toks[i]);

        if ((tok == "limit" || tok == "top" || tok == "first") && i + 1 < toks.size()) {
            int n = 0;
            if (try_parse_int(toks[++i], n) && n > 0) opt.limit = n;
            continue;
        }

        if ((tok == "offset" || tok == "skip") && i + 1 < toks.size()) {
            int n = 0;
            if (try_parse_int(toks[++i], n) && n >= 0) opt.offset = n;
            continue;
        }

        if (tok == "area" && i + 1 < toks.size()) {
            int n = -1;
            if (try_parse_int(toks[++i], n)) opt.area = n;
            continue;
        }

        // Convenience: WORKSPACE TUPLES 20
        int n = 0;
        if (i == 0 && try_parse_int(toks[i], n) && n > 0) {
            opt.limit = n;
            continue;
        }
    }

    if (opt.limit < 1) opt.limit = 1;
    if (opt.limit > 1000) opt.limit = 1000;
    if (opt.offset < 0) opt.offset = 0;
    return opt;
}

static std::string tuple_safe_value(std::string s) {
    for (char& c : s) {
        if (c == '\r' || c == '\n' || c == '\t') c = ' ';
        else if (c == '|') c = '/';
    }
    return trim_copy(s);
}

static bool collect_workspace_recnos_asc(xbase::DbArea& A,
                                         std::vector<uint64_t>& recnos,
                                         std::string& err) {
    recnos.clear();
    err.clear();

#if HAVE_ORDER_ITERATOR
    try {
        if (cli::order_collect_recnos_asc(A, recnos, nullptr, &err)) {
            return true;
        }
    } catch (const std::exception& ex) {
        err = ex.what();
    } catch (...) {
        err = "unknown order iterator failure";
    }
#else
    err = "cli/order_iterator.hpp not available; using physical order";
#endif

    // Safe fallback: physical order. This keeps WORKSPACE useful even if the
    // optional order iterator has not been linked into this build yet.
    const uint64_t n = A.recCount64();
    recnos.reserve(static_cast<size_t>(std::min<uint64_t>(n, 1000000ull)));
    for (uint64_t rn = 1; rn <= n; ++rn) recnos.push_back(rn);
    return !recnos.empty() || n == 0;
}

static std::string workspace_area_label(xbase::DbArea& A) {
    try {
        if (!A.logicalName().empty()) return A.logicalName();
    } catch (...) {}
    try {
        if (!A.dbfBasename().empty()) return A.dbfBasename();
    } catch (...) {}
    try {
        if (!A.name().empty()) return A.name();
    } catch (...) {}
    return "(unknown)";
}

static void print_workspace_tuple_row(xbase::DbArea& A,
                                      int areaIndex,
                                      uint64_t logicalRow,
                                      uint64_t recno) {
    if (recno == 0 || recno > static_cast<uint64_t>(std::numeric_limits<int32_t>::max())) {
        std::cout << "; TUPLE " << logicalRow << " | RECNO=" << recno
                  << " | (recno out of 32-bit navigation range)\n";
        return;
    }

    if (!A.gotoRec(static_cast<int32_t>(recno))) {
        std::cout << "; TUPLE " << logicalRow << " | RECNO=" << recno
                  << " | (goto failed)\n";
        return;
    }

    try { (void)A.readCurrent(); } catch (...) {}

    // Tuple bridge: use the shared tuple builder instead of hand-reading
    // DbArea fields here. The explicit #<area>.* form avoids depending on
    // whichever workarea the shell currently marks as selected. This keeps
    // WORKSPACE as a consumer of tuple rows rather than a second tuple
    // implementation.
    dottalk::TupleBuildOptions buildOpt;
    buildOpt.refresh_relations  = true;
    buildOpt.header_area_prefix = false;
    buildOpt.strict_fields      = false;

    std::string spec = "*";
    if (areaIndex >= 0) spec = "#" + std::to_string(areaIndex) + ".*";

    const auto built = dottalk::build_tuple_from_spec(spec, buildOpt);
    if (!built.ok) {
        std::cout << "; TUPLE " << logicalRow << " | RECNO=" << recno
                  << " | (tuple build failed: " << built.error << ")\n";
        return;
    }

    std::cout << "; TUPLE " << logicalRow << " | RECNO=" << recno;
    const dottalk::TupleRow& row = built.row;
    const std::size_t n = std::min(row.columns.size(), row.values.size());
    for (std::size_t i = 0; i < n; ++i) {
        std::string name = row.columns[i].name.empty() ? row.columns[i].field : row.columns[i].name;
        if (name.empty()) name = "COL" + std::to_string(i + 1);
        std::cout << " | " << name << "=" << tuple_safe_value(row.values[i]);
    }
    std::cout << "\n";
}

static void workspace_print_tuples(xbase::DbArea& current,
                                   const std::string& args) {
    const WorkspaceTupleOptions opt = parse_tuple_options(args);

    xbase::DbArea* area = &current;
    int areaIndex = get_area_index(current);

    if (opt.area >= 0) {
        if (opt.area >= xbase::MAX_AREA) {
            std::cout << "WORKSPACE TUPLES: Area out of range: " << opt.area
                      << " (0.." << (xbase::MAX_AREA - 1) << ")\n";
            return;
        }
        try {
            area = &get_area_0based(opt.area);
            areaIndex = opt.area;
        } catch (const std::exception& ex) {
            std::cout << "WORKSPACE TUPLES: " << ex.what() << "\n";
            return;
        }
    }

    if (!area || !area_open(*area)) {
        std::cout << "WORKSPACE TUPLES: no table open";
        if (areaIndex >= 0) std::cout << " in area " << areaIndex;
        std::cout << ".\n";
        return;
    }

    const int32_t savedRecno = area->recno();

    bool hasOrder = false;
    bool descending = false;
    std::string orderName;
    std::string tag;
    try {
        hasOrder = orderstate::hasOrder(*area);
        descending = hasOrder && !orderstate::isAscending(*area);
        orderName = orderstate::orderName(*area);
        tag = orderstate::activeTag(*area);
    } catch (...) {}

    std::vector<uint64_t> recnos;
    std::string err;
    if (!collect_workspace_recnos_asc(*area, recnos, err)) {
        std::cout << "WORKSPACE TUPLES: could not collect record order";
        if (!err.empty()) std::cout << " (" << err << ")";
        std::cout << ".\n";
        if (savedRecno > 0) {
            try { area->gotoRec(savedRecno); (void)area->readCurrent(); } catch (...) {}
        }
        return;
    }

    const uint64_t total = static_cast<uint64_t>(recnos.size());
    uint64_t start = static_cast<uint64_t>(opt.offset);
    if (start > total) start = total;

    uint64_t available = total - start;
    uint64_t take = static_cast<uint64_t>(opt.limit);
    if (take > available) take = available;

    std::cout << "; WORKSPACE TUPLES";
    if (areaIndex >= 0) std::cout << " AREA=" << areaIndex;
    std::cout << " TABLE=" << workspace_area_label(*area)
              << " RECS=" << area->recCount64()
              << " ORDER=" << (hasOrder ? (descending ? "DESC" : "ASC") : "PHYSICAL")
              << " LIMIT=" << opt.limit
              << " OFFSET=" << opt.offset;
    if (hasOrder) {
        if (!tag.empty()) std::cout << " TAG=" << tag;
        if (!orderName.empty()) std::cout << " INDEX=" << orderName;
    }
    if (!err.empty() && !hasOrder) std::cout << " NOTE=" << err;
    std::cout << "\n";

    for (uint64_t i = 0; i < take; ++i) {
        const uint64_t logicalRow = start + i + 1;
        uint64_t rn = 0;
        if (descending) {
            const uint64_t ascIndex = total - 1 - (start + i);
            rn = recnos[static_cast<size_t>(ascIndex)];
        } else {
            rn = recnos[static_cast<size_t>(start + i)];
        }
        print_workspace_tuple_row(*area, areaIndex, logicalRow, rn);
    }

    if (take == 0) {
        std::cout << "; WORKSPACE TUPLES: no rows in requested range.\n";
    }

    if (savedRecno > 0) {
        try { area->gotoRec(savedRecno); (void)area->readCurrent(); } catch (...) {}
    }

    uint64_t logicalSaved = 0;
    if (savedRecno > 0) {
        for (uint64_t i = 0; i < total; ++i) {
            const uint64_t idx = descending ? (total - 1 - i) : i;
            if (recnos[static_cast<size_t>(idx)] == static_cast<uint64_t>(savedRecno)) {
                logicalSaved = i + 1;
                break;
            }
        }
    }

    std::cout << "; CURSOR: Physical Recno " << savedRecno;
    if (logicalSaved > 0) std::cout << ", Logical Row " << logicalSaved;
    std::cout << "\n";
}

// --------- Command Entry ----------------------------------------------------

static void workspace_print_usage() {
    std::cout << "Usage:\n";
    std::cout << "  WORKSPACE                                   (List open areas)\n";
    std::cout << "  WORKSPACE USAGE                            (Show this usage)\n";
    std::cout << "  WORKSPACE ALL                              (List all areas, including closed slots)\n";
    std::cout << "  WORKSPACE OPEN DBF                         (Open tables from configured DBF slot)\n";
    std::cout << "  WORKSPACE OPEN [<dir>]                     (Open all tables in dir)\n";
    std::cout << "  WORKSPACE OPEN <dir> recursive             (STUB: accepts flag; non-recursive for now)\n";
    std::cout << "  WORKSPACE OPEN <file.dbf>                  (Open single table in current area)\n";
    std::cout << "  WORKSPACE ADD <file.dbf>                   (Add single table to first free area)\n";
    std::cout << "  WORKSPACE ADD <target> AUTO|CNX|INX|IDX|CDX|NOINDEX [FALLBACK] [TABLE]\n";
    std::cout << "  WORKSPACE OPEN <target> CNX [FALLBACK] [recursive] [TABLE]\n";
    std::cout << "  WORKSPACE OPEN <target> INX|IDX [FALLBACK] [recursive] [TABLE]\n";
    std::cout << "  WORKSPACE OPEN <target> CDX [FALLBACK] [recursive] [TABLE]   (LMDB)\n";
    std::cout << "  WORKSPACE OPEN <target> NOINDEX [recursive] [TABLE]\n";
    std::cout << "  WORKSPACE CLOSE                            (Close all open areas)\n";
    std::cout << "  WORKSPACE CLOSE <n> [m ...]                (Close by area index)\n";
    std::cout << "  WORKSPACE CLOSE <name|file|stem|alias>[,...] (Close by name/alias; case-insensitive)\n";
    std::cout << "  WORKSPACE SAVE <file>                      (Save areas [+relations if available])\n";
    std::cout << "  WORKSPACE LOAD <file>                      (Load areas [+relations]; relative/cross-OS paths supported)\n";
    std::cout << "  WORKSPACE TUPLES [LIMIT <n>] [OFFSET <n>] [AREA <n>]\n";
    std::cout << "Notes:\n";
    std::cout << "  - WORKSPACE with no arguments is a read-only report of open areas.\n";
    std::cout << "  - For OPEN: <target> is always the first argument after OPEN.\n";
    std::cout << "  - WORKSPACE OPEN replaces the current workspace contents; WORKSPACE ADD is additive.\n";
    std::cout << "  - Relative targets resolve from SETPATH/INIT slots, primarily DBF.\n";
    std::cout << "  - WORKSPACE OPEN dbf uses the configured DBF slot directly.\n";
    std::cout << "  - Bare stems like WORKSPACE OPEN students try <DBF>/students.dbf.\n";
    std::cout << "  - Without CNX/INX/CDX, index files are chosen by DBF flavor: true x64/v128 CDX, classic VFP/v32 CNX.\n";
}

std::string workspace_last_loaded_file() {
    return last_loaded_workspace_file();
}

void cmd_WORKSPACE(xbase::DbArea& current, std::istringstream& in) {
    string arg_line;
    std::getline(in, arg_line);
    string args = trim_copy(arg_line);

    string sub_command, rest_of_args;
    if (args.empty()) {
        sub_command.clear();
        rest_of_args.clear();
    } else {
        auto first_space = args.find_first_of(" \t");
        if (first_space == string::npos) {
            sub_command = trim_copy(args);
            rest_of_args.clear();
        } else {
            sub_command  = trim_copy(args.substr(0, first_space));
            rest_of_args = trim_copy(args.substr(first_space + 1));
        }
    }

    sub_command = to_lower(trim_copy(sub_command));
    rest_of_args = trim_copy(rest_of_args);

    try {
        if (sub_command == "usage" || sub_command == "help" || sub_command == "?") {
            workspace_print_usage();

        } else if (sub_command == "add") {
            auto toks = split_tokens(rest_of_args);

            if (toks.empty()) {
                std::cout << "WORKSPACE ADD: missing DBF target.\n";
                std::cout << "  Use: WORKSPACE ADD <file.dbf> [AUTO|CNX|INX|IDX|CDX|NOINDEX] [FALLBACK] [TABLE]\n";
                return;
            }

            if (ci_equal(toks[0], "cnx") || ci_equal(toks[0], "inx") ||
                ci_equal(toks[0], "idx") || ci_equal(toks[0], "cdx") ||
                ci_equal(toks[0], "auto") || parse_noindex_ci(toks[0])) {
                std::cout << "WORKSPACE ADD: target must come first.\n";
                std::cout << "  Use: WORKSPACE ADD <target> [AUTO|CNX|INX|IDX|CDX|NOINDEX] [FALLBACK] [TABLE]\n";
                return;
            }

            fs::path spec = fs::path(toks[0]);
            bool want_fallback = false;
            bool want_table = false;
            IndexMode indexMode = IndexMode::Auto;

            for (size_t i = 1; i < toks.size(); ++i) {
                const std::string& tok = toks[i];

                if (parse_recursive_ci(tok)) {
                    std::cout << "WORKSPACE ADD: recursive is not supported for single-table add.\n";
                    return;
                }
                if (parse_fallback_ci(tok)) { want_fallback = true; continue; }
                if (parse_table_ci(tok)) { want_table = true; continue; }
                if (parse_noindex_ci(tok)) { indexMode = IndexMode::None; continue; }

                if (auto m = parse_index_mode_ci(tok)) {
                    indexMode = *m;
                    continue;
                }

                std::cout << "WORKSPACE ADD: unknown option '" << tok << "' (ignored).\n";
            }

            if (want_fallback && indexMode == IndexMode::None) {
                std::cout << "WORKSPACE ADD: FALLBACK ignored (CNX/INX/CDX not specified).\n";
                want_fallback = false;
            }

            spec = resolve_open_target(spec);
            if (!fs::exists(spec) || !fs::is_regular_file(spec) || !ieq_ext(spec, ".dbf")) {
                std::cout << "WORKSPACE ADD: Path not found or unsupported: " << s8(spec) << "\n";
                std::cout << "  Use: WORKSPACE ADD <file.dbf> [AUTO|CNX|INX|IDX|CDX|NOINDEX] [FALLBACK] [TABLE]\n";
                return;
            }

            const int dup_area = find_open_area_for_path(spec);
            if (dup_area >= 0) {
                std::cout << "WORKSPACE ADD: table already open in area " << dup_area
                          << ": " << s8(spec) << "\n";
                (void)select_engine_area(dup_area);
                return;
            }

            const int area0 = first_closed_area_index();
            if (area0 < 0) {
                std::cout << "WORKSPACE ADD: no free work area is available"
                          << " (MAX_AREA=" << xbase::MAX_AREA << ").\n";
                return;
            }

            OpenResult r;
            r.area = area0;
            r.dbf = spec;

            std::string err;
            bool attached = false;
            r.opened = open_into_area(area0, spec, std::nullopt, &err, &attached, &r.indexError, "WORKSPACE ADD");
            r.indexAttached = attached;
            r.error = err;
            if (r.opened) {
                try {
                    xbase::DbArea& A = get_area_0based(area0);
                    r.indexFile = find_index_for_open_area(A, spec, indexMode, want_fallback);
                    if (r.indexFile.has_value()) {
                        r.indexAttached = attach_workspace_index(A, *r.indexFile, r.indexError);
                    }
                } catch (const std::exception& ex) {
                    r.indexError = ex.what();
                } catch (...) {
                    r.indexError = "unknown index attach error";
                }
            }

            std::cout << "WORKSPACE ADD: opening single table into area " << area0
                      << ": " << s8(spec)
                      << (want_table ? " [TABLE]" : "")
                      << "\n";
            print_open_results(std::vector<OpenResult>{r});

            if (r.opened) {
                (void)select_engine_area(area0);
#if HAVE_TABLE
                if (want_table) {
                    table_enable_for_area_if_open(area0);
                    std::cout << "WORKSPACE ADD: TABLE enabled for area " << area0 << ".\n";
                }
#else
                if (want_table) {
                    std::cout << "WORKSPACE ADD: TABLE requested but table_state module not present.\n";
                }
#endif
                refresh_relations_if_enabled_safe();
            }

        } else if (sub_command == "open") {
            auto toks = split_tokens(rest_of_args);

            if (!toks.empty() && (ci_equal(toks[0], "cnx") || ci_equal(toks[0], "inx") ||
                                  ci_equal(toks[0], "idx") || ci_equal(toks[0], "cdx") ||
                                  ci_equal(toks[0], "auto") || parse_noindex_ci(toks[0]))) {
                std::cout << "WORKSPACE OPEN: target must come first.\n";
                std::cout << "  Use: WORKSPACE OPEN <target> [AUTO|CNX|INX|IDX|CDX|NOINDEX] [FALLBACK] [recursive] [TABLE]\n";
                return;
            }

            fs::path spec = toks.empty() ? dbf_root() : fs::path(toks[0]);
            bool want_recursive = false;
            bool want_fallback  = false;
            bool want_table     = false;
            IndexMode indexMode = IndexMode::Auto;

            for (size_t i = 1; i < toks.size(); ++i) {
                const std::string& tok = toks[i];

                if (parse_recursive_ci(tok)) { want_recursive = true; continue; }
                if (parse_fallback_ci(tok))  { want_fallback  = true; continue; }
                if (parse_table_ci(tok))     { want_table     = true; continue; }
                if (parse_noindex_ci(tok))   { indexMode = IndexMode::None; continue; }

                if (auto m = parse_index_mode_ci(tok)) {
                    indexMode = *m;
                    continue;
                }

                std::cout << "WORKSPACE OPEN: unknown option '" << tok << "' (ignored).\n";
            }

            if (want_fallback && indexMode == IndexMode::None) {
                std::cout << "WORKSPACE OPEN: FALLBACK ignored (CNX/INX/CDX not specified).\n";
                want_fallback = false;
            }

            try {
                auto* eng = shell_engine();
                if (eng && !dottalk::dirty::maybe_prompt_all(*eng, "WORKSPACE OPEN")) {
                    std::cout << "WORKSPACE OPEN canceled.\n";
                    return;
                }
            } catch (...) {}

            schema_close_all();
            spec = resolve_open_target(spec);

            auto mode_tag = [&]() -> const char* {
                if (indexMode == IndexMode::Auto) return "AUTO INDEX";
                if (indexMode == IndexMode::ForceCnx) return "CNX";
                if (indexMode == IndexMode::ForceInx) return "INX/IDX";
                if (indexMode == IndexMode::ForceCdx) return "CDX(LMDB)";
                if (indexMode == IndexMode::None) return "NOINDEX";
                return nullptr;
            };

            if (fs::exists(spec) && fs::is_directory(spec)) {
                std::cout << "WORKSPACE OPEN: scanning directory: " << s8(spec)
                          << (want_recursive ? " (recursive=stub)" : "")
                          << (mode_tag() ? (string(" [") + mode_tag() + "]") : "")
                          << (want_fallback && mode_tag() ? " [FALLBACK]" : "")
                          << (want_table ? " [TABLE]" : "")
                          << "\n";

                auto results = want_recursive
                    ? schema_open_directory_recursive(spec, indexMode, want_fallback)
                    : schema_open_directory(spec, indexMode, want_fallback);

                print_open_results(results);

#if HAVE_TABLE
                if (want_table) {
                    const int n = table_enable_for_results(results);
                    std::cout << "WORKSPACE OPEN: TABLE enabled for " << n << " opened area(s).\n";
                }
#else
                if (want_table) {
                    std::cout << "WORKSPACE OPEN: TABLE requested but table_state module not present.\n";
                }
#endif

            } else if (fs::exists(spec) && fs::is_regular_file(spec) && ieq_ext(spec, ".dbf")) {
                std::cout << "WORKSPACE OPEN: opening single table into current area"
                          << (get_area_index(current) >= 0 ? (" " + std::to_string(get_area_index(current))) : "")
                          << ": " << s8(spec)
                          << (mode_tag() ? (string(" [") + mode_tag() + "]") : "")
                          << (want_fallback && mode_tag() ? " [FALLBACK]" : "")
                          << (want_table ? " [TABLE]" : "")
                          << "\n";

                OpenResult r = schema_open_single_into_current(current, spec, indexMode, want_fallback);
                print_open_results(std::vector<OpenResult>{r});

#if HAVE_TABLE
                if (want_table && r.opened && r.area >= 0) {
                    table_enable_for_area_if_open(r.area);
                    std::cout << "WORKSPACE OPEN: TABLE enabled for area " << r.area << ".\n";
                }
#else
                if (want_table) {
                    std::cout << "WORKSPACE OPEN: TABLE requested but table_state module not present.\n";
                }
#endif

            } else {
                std::cout << "WORKSPACE OPEN: Path not found or unsupported: " << s8(spec) << "\n";
                std::cout << "Usage:\n";
                std::cout << "  WORKSPACE OPEN [<dir>]                      (Open all tables in dir)\n";
                std::cout << "  WORKSPACE OPEN <dir> recursive             (STUB)\n";
                std::cout << "  WORKSPACE OPEN <file.dbf>                  (Open single table in current area)\n";
                std::cout << "  WORKSPACE OPEN <target> CNX [FALLBACK] [recursive] [TABLE]\n";
                std::cout << "  WORKSPACE OPEN <target> INX|IDX [FALLBACK] [recursive] [TABLE]\n";
                std::cout << "  WORKSPACE OPEN <target> CDX [FALLBACK] [recursive] [TABLE]   (LMDB)\n";
                std::cout << "  WORKSPACE OPEN <target> NOINDEX [recursive] [TABLE]\n";
                std::cout << "Notes:\n";
                std::cout << "  - <target> is always the first argument after OPEN.\n";
                std::cout << "  - Relative targets resolve from SETPATH/INIT slots, primarily DBF.\n";
                std::cout << "  - WORKSPACE OPEN dbf uses the DBF slot directly.\n";
                std::cout << "  - Bare stems like WORKSPACE OPEN students try <DBF>/students.dbf.\n";
                std::cout << "  - Without CNX/INX/CDX, indexes are chosen by DBF flavor: true x64/v128 CDX, classic VFP/v32 CNX.\n";
            }
            // WORKSPACE OPEN performs a structural reset first (schema_close_all),
            // then may open zero, one, or many tables. Refresh after the
            // complete operation, not during partial opens.
            relations_boot::retry_pending_autoload();
            refresh_relations_if_enabled_safe();

        } else if (sub_command == "close") {
            try {
                auto* eng = shell_engine();
                if (eng && !dottalk::dirty::maybe_prompt_all(*eng, "WORKSPACE CLOSE")) {
                    std::cout << "WORKSPACE CLOSE canceled.\n";
                    return;
                }
            } catch (...) {}

            string tokline = trim_copy(rest_of_args);
            if (tokline.empty()) {
                schema_close_all();
            } else {
                auto tokens = split_tokens(tokline);
                std::unordered_set<int> closed_by_index;
                int total_closed = 0;

                for (const auto& tok : tokens) {
                    int n;
                    if (try_parse_int(tok, n)) {
                        if (n >= 0 && n < xbase::MAX_AREA) {
                            if (!closed_by_index.count(n)) {
                                if (close_area_if_open(n)) {
                                    total_closed++;
                                    closed_by_index.insert(n);
                                }
                            }
                        } else {
                            std::cout << "WORKSPACE CLOSE: Area out of range: " << n
                                      << " (0.." << (xbase::MAX_AREA - 1) << ")\n";
                        }
                    } else {
                        total_closed += schema_close_matching_token(tok);
                    }
                }

#if HAVE_RELATIONS
                if (total_closed > 0) clear_relations_all_safe();
#endif

                if (total_closed == 0) std::cout << "WORKSPACE: No matching open areas to close.\n";
                else std::cout << "WORKSPACE: " << total_closed << " area(s) closed.\n";
            }

            // WORKSPACE CLOSE invalidates area membership and relation anchors.
            // Refresh after all requested closes have completed.
            refresh_relations_if_enabled_safe();
        } else if (sub_command == "save") {
            // AIF-070 M2 (owner ruling D1): a trailing MEMO keyword selects the
            // memo carrier -- WORKSPACE SAVE <name> MEMO. File remains default.
            // DTSHEMA 3 (owner-chartered 2026-08-11): a trailing V3 keyword
            // opts this save into version 3; v2 stays the default so every
            // proven path is untouched. Keywords combine in either order.
            std::string wsargs = trim_copy(rest_of_args);
            bool to_memo = false;
            int  ver = 2;
            for (;;) {
                const auto sp = wsargs.find_last_of(" \t");
                if (sp == std::string::npos) break;
                const std::string last = to_lower(trim_copy(wsargs.substr(sp + 1)));
                if (last == "memo" && !to_memo)      { to_memo = true; wsargs = trim_copy(wsargs.substr(0, sp)); }
                else if (last == "v3" && ver == 2)   { ver = 3;        wsargs = trim_copy(wsargs.substr(0, sp)); }
                else break;
            }
            if (to_memo) {
                if (wsargs.empty()) std::cout << "WORKSPACE SAVE: missing workspace name before MEMO.\n";
                else ws_memo::save_to_memo(wsargs, ver);
            } else {
                fs::path out = wsargs.empty() ? fs::path("session") : fs::path(wsargs);
                schema_save_to_file(out, ver);
            }

        } else if (sub_command == "load") {
            try {
                auto* eng = shell_engine();
                if (eng && !dottalk::dirty::maybe_prompt_all(*eng, "WORKSPACE LOAD")) {
                    std::cout << "WORKSPACE LOAD canceled.\n";
                    return;
                }
            } catch (...) {}

            // AIF-070 M2: WORKSPACE LOAD <name> MEMO loads from the catalog.
            // Step 2 (2026-08-11): trailing RAM hydrates the posture's files
            // into the mounted VDISK first (memo carrier only today) --
            // WORKSPACE LOAD <name> MEMO RAM, keywords in either order.
            std::string wsargs = trim_copy(rest_of_args);
            bool from_memo = false;
            bool to_ram = false;
            for (;;) {
                const auto sp = wsargs.find_last_of(" \t");
                if (sp == std::string::npos) break;
                const std::string last = to_lower(trim_copy(wsargs.substr(sp + 1)));
                if (last == "memo" && !from_memo) {
                    from_memo = true;
                    wsargs = trim_copy(wsargs.substr(0, sp));
                } else if (last == "ram" && !to_ram) {
                    to_ram = true;
                    wsargs = trim_copy(wsargs.substr(0, sp));
                } else break;
            }
            if (to_ram && !from_memo) {
                std::cout << "WORKSPACE LOAD: RAM hydration is memo-carrier only today "
                             "(WORKSPACE LOAD <name> MEMO RAM).\n";
            } else if (from_memo) {
                if (wsargs.empty()) std::cout << "WORKSPACE LOAD: missing workspace name before MEMO.\n";
                else if (to_ram)   ws_memo::hydrate_to_ram(wsargs);
                else               ws_memo::load_from_memo(wsargs);
            } else if (wsargs.empty()) {
                std::cout << "WORKSPACE LOAD: missing file path.\n";
            } else {
                schema_load_from_file(fs::path(wsargs));
            }

        } else if (sub_command == "tuples" || sub_command == "tuple" ||
                   sub_command == "view" || sub_command == "rows") {
            workspace_print_tuples(current, rest_of_args);

        } else if (sub_command == "all") {
            schema_list_open(true);

        } else if (sub_command.empty()) {
            schema_list_open(false);

        } else {
            std::cout << "WORKSPACE: Unknown subcommand '" << sub_command << "'.\n";
            workspace_print_usage();
        }
    } catch (const std::exception& ex) {
        std::cout << "WORKSPACE: Error: " << ex.what() << "\n";
    } catch (...) {
        std::cout << "WORKSPACE: Unknown error.\n";
    }
}
