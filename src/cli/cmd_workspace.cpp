// src/cli/cmd_workspace.cpp
//
// WORKSPACE (legacy DBF areas)
//
// Commands:
//   WORKSPACE                                   : List open areas.
//   WORKSPACE OPEN [<dir>]                      : Open all .dbf in <dir> (non-recursive).
//   WORKSPACE OPEN <dir> recursive              : (STUB) Accepts 'recursive'; falls back to non-recursive.
//   WORKSPACE OPEN <file.dbf>                   : Open a single .dbf into the CURRENT area.
//
//   WORKSPACE OPEN <target> CNX [FALLBACK] [recursive] [TABLE]
//   WORKSPACE OPEN <target> INX [FALLBACK] [recursive] [TABLE]
//   WORKSPACE OPEN <target> CDX [FALLBACK] [recursive] [TABLE]
//
//   NOTE:
//   - If CNX/INX/CDX is NOT specified, WORKSPACE OPEN will NOT attach/open indexes.
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
//   WORKSPACE OPEN <target> CNX [FALLBACK] [recursive] [TABLE]
//   WORKSPACE OPEN <target> INX [FALLBACK] [recursive] [TABLE]
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
//   WORKSPACE CLOSE closes all open work areas and clears relation/session state.
//   WORKSPACE owns live areas, aliases, index/tag bindings, and relation/session layout.
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
#include <fstream>
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
#include "memo/memo_auto.hpp"   // cli_memo::memo_auto_on_close
#include "xindex/index_manager.hpp"
#include "cli/dirty_prompt.hpp"
#include "cli/order_state.hpp"
#include "cli/path_resolver.hpp"
#include "cli/cmd_setpath.hpp"
#include "tuple_builder.hpp"

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

static std::string g_last_loaded_workspace_file;

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
        if (auto* im = a.indexManagerPtr()) return im->activeTag();
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

enum class IndexMode { None = 0, ForceCnx, ForceInx, ForceCdx };

static inline std::optional<IndexMode> parse_index_mode_ci(const std::string& token) {
    if (ci_equal(token, "cnx")) return IndexMode::ForceCnx;
    if (ci_equal(token, "inx")) return IndexMode::ForceInx;
    if (ci_equal(token, "cdx")) return IndexMode::ForceCdx;
    return std::nullopt;
}

static std::optional<fs::path> find_index_for_dbf(const fs::path& dbfPath, IndexMode mode, bool fallback) {
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
        return {
            (baseDir / stem).concat(kCnxPrimaryExt),
            (baseDir / stem).concat(kCnxCompatExt)
        };
    };

    const fs::path sibDir = dbfPath.parent_path().empty() ? fs::current_path() : dbfPath.parent_path();
    const fs::path idxDir = idx_root();

    auto pick_first_existing = [&](const std::vector<fs::path>& cands) -> std::optional<fs::path> {
        for (const auto& p : cands) {
            if (file_ok(p)) return p;
        }
        return std::nullopt;
    };

    auto pick_inx = [&]() -> std::optional<fs::path> {
        if (auto p = pick_first_existing(inx_candidates(sibDir))) return p;
        if (auto p = pick_first_existing(inx_candidates(idxDir))) return p;
        return std::nullopt;
    };

    auto pick_cnx = [&]() -> std::optional<fs::path> {
        if (auto p = pick_first_existing(cnx_candidates(sibDir))) return p;
        if (auto p = pick_first_existing(cnx_candidates(idxDir))) return p;
        return std::nullopt;
    };

    auto pick_cdx = [&](const std::string& stemUpper) -> std::optional<fs::path> {
        fs::path sib_cdx = sibDir / stem;
        sib_cdx.replace_extension(".cdx");

        fs::path idx_cdx = idxDir / stem;
        idx_cdx.replace_extension(".cdx");

        std::vector<fs::path> cdx_candidates = {
            idxDir / (stemUpper + ".cdx"),
            sib_cdx,
            idx_cdx
        };

        for (const auto& p : cdx_candidates) {
            if (fs::exists(p)) return p;
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

// --------- OPEN helpers -----------------------------------------------------

struct OpenResult {
    int area = -1;
    fs::path dbf;
    std::optional<fs::path> indexFile;
    bool opened = false;
    bool indexAttached = false;
    string error;
};

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

        if (mode != IndexMode::None) {
            r.indexFile = find_index_for_dbf(r.dbf, mode, fallback);
        }

        try {
            xbase::DbArea& A = get_area_0based(area0);
            try { orderstate::clearOrder(A); } catch (...) {}
            try { A.close(); } catch (...) {}

            const string dbfStr = s8(r.dbf);
            A.open(dbfStr);
            A.setFilename(dbfStr);

            r.opened = true;

            if (r.indexFile.has_value()) {
                try {
                    orderstate::setOrder(A, s8(*r.indexFile));
                    r.indexAttached = true;
                } catch (...) {
                    r.indexAttached = false;
                }
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
    std::cout << "WORKSPACE OPEN: 'recursive' requested — stubbed; falling back to flat scan.\n";
    return schema_open_directory(dir, mode, fallback);
}

static OpenResult schema_open_single_into_current(xbase::DbArea& current, const fs::path& dbfPath, IndexMode mode, bool fallback) {
    OpenResult r;
    r.dbf = dbfPath;
    r.area = get_area_index(current);

    if (mode != IndexMode::None) {
        r.indexFile = find_index_for_dbf(dbfPath, mode, fallback);
    }

    try {
        try { orderstate::clearOrder(current); } catch (...) {}
        try { current.close(); } catch (...) {}

        const string dbfStr = s8(dbfPath);
        current.open(dbfStr);
        current.setFilename(dbfStr);

        r.opened = true;

        if (r.indexFile.has_value()) {
            try {
                orderstate::setOrder(current, s8(*r.indexFile));
                r.indexAttached = true;
            } catch (...) {
                r.indexAttached = false;
            }
        }
    } catch (const std::exception& ex) {
        r.error = ex.what();
    } catch (...) {
        r.error = "Unknown error.";
    }

    return r;
}

static bool open_into_area(int area0, const fs::path& dbf, const std::optional<fs::path>& index, string* err) {
    try {
        xbase::DbArea& A = get_area_0based(area0);
        try { orderstate::clearOrder(A); } catch (...) {}
        try { A.close(); } catch (...) {}

        const string dbfStr = s8(dbf);
        A.open(dbfStr);
        A.setFilename(dbfStr);

        if (index && !index->empty()) {
            fs::path ip = *index;
            if (!ip.is_absolute()) ip = resolve_relative_to_root(ip);
            if (fs::exists(ip)) {
                try { orderstate::setOrder(A, s8(ip)); } catch (...) {}
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
            const auto* im = A.indexManagerPtr();
            if (im && im->hasBackend()) {
                A.indexManager().close();
            }
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

static void schema_save_to_file(const fs::path& file) {
    fs::path outPath = file;
    const fs::path rootWORKSPACE = WORKSPACE_root();

    if (outPath.is_relative()) outPath = rootWORKSPACE / outPath;
    if (!outPath.has_extension()) outPath.replace_extension(".dtschema");

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

    out << "DTSHEMA 2\n";

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

    out.flush();
    std::cout << "WORKSPACE SAVE: wrote " << s8(outPath) << "\n";
}

static void schema_load_from_file(const fs::path& file) {
    fs::path inPath = file;
    const fs::path rootWORKSPACE = WORKSPACE_root();

    if (!inPath.has_extension()) inPath.replace_extension(".dtschema");

    if (inPath.is_relative()) {
        fs::path candidate = rootWORKSPACE / inPath;
        std::error_code ec;
        if (fs::exists(candidate, ec) && !ec) inPath = candidate;
        else inPath = fs::current_path() / inPath;
    }

    std::ifstream in(inPath, std::ios::binary);
    if (!in.good()) {
        std::cout << "WORKSPACE LOAD: cannot read file: " << s8(inPath) << "\n";
        return;
    }

    auto weak_can = [](const fs::path& p) -> fs::path {
        std::error_code ec;
        fs::path r = fs::weakly_canonical(p, ec);
        return ec ? p : r;
    };

    const fs::path rootDbf = dbf_root();
    const fs::path rootIdx = idx_root();

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
    else {
        std::cout << "WORKSPACE LOAD: bad or unsupported file header.\n";
        return;
    }

    g_last_loaded_workspace_file = s8(inPath);

    schema_close_all();

    std::string line;
    int area_count = 0;
    int relation_count = 0;
    int relation_rejected_count = 0;

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
        } else {
            std::cout << "  ~ Unknown line (ignored): " << t << "\n";
        }
    }

    std::cout << "WORKSPACE LOAD: restored " << area_count << " area(s)";
#if HAVE_RELATIONS
    std::cout << " and " << relation_count << " relation(s)";
    if (relation_rejected_count > 0) {
        std::cout << " (" << relation_rejected_count << " rejected)";
    }
#else
    std::cout << " (relations: stubbed)";
#endif
    std::cout << ".\n";
        // WORKSPACE LOAD is a structural lifecycle operation: areas and
    // optional relations have now been fully restored. Refresh only after
    // the complete load so relation caches do not see a half-built state.
    refresh_relations_if_enabled_safe();
}


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
    std::cout << "  WORKSPACE OPEN <target> CNX [FALLBACK] [recursive] [TABLE]\n";
    std::cout << "  WORKSPACE OPEN <target> INX [FALLBACK] [recursive] [TABLE]\n";
    std::cout << "  WORKSPACE OPEN <target> CDX [FALLBACK] [recursive] [TABLE]   (LMDB)\n";
    std::cout << "  WORKSPACE CLOSE                            (Close all open areas)\n";
    std::cout << "  WORKSPACE CLOSE <n> [m ...]                (Close by area index)\n";
    std::cout << "  WORKSPACE CLOSE <name|file|stem|alias>[,...] (Close by name/alias; case-insensitive)\n";
    std::cout << "  WORKSPACE SAVE <file>                      (Save areas [+relations if available])\n";
    std::cout << "  WORKSPACE LOAD <file>                      (Load areas [+relations]; relative/cross-OS paths supported)\n";
    std::cout << "  WORKSPACE TUPLES [LIMIT <n>] [OFFSET <n>] [AREA <n>]\n";
    std::cout << "Notes:\n";
    std::cout << "  - WORKSPACE with no arguments is a read-only report of open areas.\n";
    std::cout << "  - For OPEN: <target> is always the first argument after OPEN.\n";
    std::cout << "  - Relative targets resolve from SETPATH/INIT slots, primarily DBF.\n";
    std::cout << "  - WORKSPACE OPEN dbf uses the configured DBF slot directly.\n";
    std::cout << "  - Bare stems like WORKSPACE OPEN students try <DBF>/students.dbf.\n";
    std::cout << "  - Without CNX/INX/CDX, no index files will be attached.\n";
}

std::string workspace_last_loaded_file() {
    return g_last_loaded_workspace_file;
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

        } else if (sub_command == "open") {
            auto toks = split_tokens(rest_of_args);

            if (!toks.empty() && (ci_equal(toks[0], "cnx") || ci_equal(toks[0], "inx") ||
                                  ci_equal(toks[0], "idx") || ci_equal(toks[0], "cdx"))) {
                std::cout << "WORKSPACE OPEN: target must come first.\n";
                std::cout << "  Use: WORKSPACE OPEN <target> CNX|INX|CDX [FALLBACK] [recursive] [TABLE]\n";
                return;
            }

            fs::path spec = toks.empty() ? dbf_root() : fs::path(toks[0]);
            bool want_recursive = false;
            bool want_fallback  = false;
            bool want_table     = false;
            IndexMode indexMode = IndexMode::None;

            for (size_t i = 1; i < toks.size(); ++i) {
                const std::string& tok = toks[i];

                if (ci_equal(tok, "idx")) {
                    std::cout << "WORKSPACE OPEN: 'IDX' is not supported. Use CNX, INX, or CDX.\n";
                    return;
                }
                if (parse_recursive_ci(tok)) { want_recursive = true; continue; }
                if (parse_fallback_ci(tok))  { want_fallback  = true; continue; }
                if (parse_table_ci(tok))     { want_table     = true; continue; }

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
                if (indexMode == IndexMode::ForceCnx) return "CNX";
                if (indexMode == IndexMode::ForceInx) return "INX";
                if (indexMode == IndexMode::ForceCdx) return "CDX(LMDB)";
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
                std::cout << "  WORKSPACE OPEN <target> INX [FALLBACK] [recursive] [TABLE]\n";
                std::cout << "  WORKSPACE OPEN <target> CDX [FALLBACK] [recursive] [TABLE]   (LMDB)\n";
                std::cout << "Notes:\n";
                std::cout << "  - <target> is always the first argument after OPEN.\n";
                std::cout << "  - Relative targets resolve from SETPATH/INIT slots, primarily DBF.\n";
                std::cout << "  - WORKSPACE OPEN dbf uses the DBF slot directly.\n";
                std::cout << "  - Bare stems like WORKSPACE OPEN students try <DBF>/students.dbf.\n";
                std::cout << "  - Without CNX/INX/CDX, no index files will be attached.\n";
            }
            // WORKSPACE OPEN performs a structural reset first (schema_close_all),
            // then may open zero, one, or many tables. Refresh after the
            // complete operation, not during partial opens.
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
            fs::path out = rest_of_args.empty() ? fs::path("session") : fs::path(rest_of_args);
            schema_save_to_file(out);

        } else if (sub_command == "load") {
            try {
                auto* eng = shell_engine();
                if (eng && !dottalk::dirty::maybe_prompt_all(*eng, "WORKSPACE LOAD")) {
                    std::cout << "WORKSPACE LOAD canceled.\n";
                    return;
                }
            } catch (...) {}

            if (rest_of_args.empty()) {
                std::cout << "WORKSPACE LOAD: missing file path.\n";
            } else {
                schema_load_from_file(fs::path(rest_of_args));
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
