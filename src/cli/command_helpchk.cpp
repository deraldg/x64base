// ============================================================================
// File: src/cli/command_helpchk.cpp
// @dottalk.usage v1
// owner: DOT|CMDHELPCHK
// command: CMDHELPCHK
// category: help-diagnostics
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: CMDHELPCHK USAGE
// summary:
//   Validate HELP/catalog artifacts and reflection metadata against command
//   registry expectations, legacy HELP DBF rows, and HELP DATA v2 artifacts.
//
// usage:
//   CMDHELPCHK
//   CMDHELPCHK USAGE
//   CMDHELPCHK REF
//   CMDHELPCHK REFLECT
//   CMDHELPCHK ARTIFACTS
//   CMDHELPCHK ARTIFACTS <dir>
//   CMDHELPCHK ARTIFACTS <dir> <limit>
//   CMDHELPCHK V2 <dir> <limit>
//   CMDHELPCHK <dir> [limit]
//
// notes:
//   CMDHELPCHK with no arguments runs reflection-system validation.
//   REF and REFLECT are explicit names for the reflection validation mode.
//   ARTIFACTS and V2 validate HELP DATA v2 help_artifacts.dbf/.dbt.
//   A directory argument without a mode runs the legacy commands.dbf/.dbt check.
//   CMDHELPCHK reads HELP/catalog files but does not mutate table data.
//   CMDHELPCHK v2 external scanner remains separate from this runtime command.
//
// risk:
//   reads_help_dbf_dbt: yes
//   reads_reflection_metadata: yes
//   mutates_table_data: no
//   mutates_cursor: no
//
// related:
//   HELP
//   CMDHELP
//   HELP DATA
//
// Robust validator for commands.dbf/.dbt produced by CMDHELP.
// Adds HELP DATA v2 artifact validation for help_artifacts.dbf/.dbt.
// Plus reflection-system audit mode.
// ============================================================================
#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#include "xbase.hpp"
#include "help/reference_collection.hpp"

// Optional setpath-aware slot resolving (HELP slot).
#if __has_include("cli/path_resolver.hpp") && __has_include("cli/cmd_setpath.hpp")
  #include "cli/path_resolver.hpp"
  #include "cli/cmd_setpath.hpp"
  #define HAVE_PATHS 1
#else
  #define HAVE_PATHS 0
#endif

using xbase::DbArea;
namespace fs = std::filesystem;

namespace {

static fs::path help_root_dir()
{
#if HAVE_PATHS
    try {
        namespace paths = dottalk::paths;
        return paths::get_slot(paths::Slot::HELP);
    } catch (...) {}
#endif
    std::error_code ec;
    fs::path cand = fs::current_path(ec) / "help";
    if (!ec && fs::exists(cand, ec) && fs::is_directory(cand, ec)) {
        return cand;
    }
    fs::path cwd = fs::current_path(ec);
    return ec ? fs::path{} : cwd;
}

static fs::path resolve_help_dir_arg(const std::string& argRaw)
{
    std::string a = argRaw;
    while (!a.empty() && std::isspace(static_cast<unsigned char>(a.front()))) {
        a.erase(a.begin());
    }
    while (!a.empty() && std::isspace(static_cast<unsigned char>(a.back()))) {
        a.pop_back();
    }

    if (a.empty() || a == ".") {
        return help_root_dir();
    }

    fs::path p(a);
    if (p.is_absolute()) {
        return p;
    }
    return fs::weakly_canonical(help_root_dir() / p);
}

static std::string trim_copy(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

static std::vector<std::string> split_words(const std::string& s)
{
    std::vector<std::string> words;
    std::istringstream in(s);
    std::string w;
    while (in >> w) {
        words.push_back(w);
    }
    return words;
}

#pragma pack(push,1)
struct DbfHeader {
    uint8_t  version;
    uint8_t  y, m, d;
    uint32_t nrecs;
    uint16_t header_len;
    uint16_t rec_len;
    uint8_t  reserved[20];
};

struct DbfField {
    char     name[11];
    char     type;      // 'C','L','N','M'
    uint32_t data_addr;
    uint8_t  length;
    uint8_t  decimals;
    uint8_t  reserved[14];
};
#pragma pack(pop)

static std::string dbf_field_name_11(const char raw[11])
{
    size_t n = 0;
    while (n < 11 && raw[n] != '\0') {
        ++n;
    }

    std::string s(raw, raw + n);

    while (!s.empty() &&
           (s.back() == '\0' ||
            std::isspace(static_cast<unsigned char>(s.back())))) {
        s.pop_back();
    }

    return s;
}

struct Col {
    std::string name;
    char        type{};
    uint8_t     len{};
    size_t      offset{};
};

static std::string trimr(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

static std::string triml(std::string s)
{
    size_t i = 0;
    while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) {
        ++i;
    }
    return s.substr(i);
}

static std::string upper(std::string s)
{
    std::transform(
        s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return char(std::toupper(c)); });
    return s;
}

static std::string compact_token(std::string s)
{
    s = upper(std::move(s));
    s.erase(std::remove_if(s.begin(), s.end(),
                           [](unsigned char ch) {
                               return std::isspace(ch) != 0 || ch == '_' || ch == '-';
                           }),
            s.end());
    return s;
}

static bool has_space(const std::string& s)
{
    return std::any_of(s.begin(), s.end(),
                       [](unsigned char ch) { return std::isspace(ch) != 0; });
}

static std::string compact_set_family_target(const std::string& token)
{
    // Artifact validation should flag compact DOT SET-family keys such as
    // DOT|SETORDER, not already-canonical keys such as DOT|SET ORDER.
    if (has_space(token)) {
        return {};
    }

    static const std::map<std::string, std::string> kMap = {
        {"SETORDER",  "SET ORDER"},
        {"SETINDEX",  "SET INDEX"},
        {"SETFILTER", "SET FILTER"},
        {"SETCASE",   "SET CASE"},
        {"SETPATH",   "SET PATH"},
        {"SETCNX",    "SET CNX"},
        {"SETCDX",    "SET CDX"},
        {"SETLMDB",   "SET LMDB"},
        {"SETNEAR",   "SET NEAR"},
        {"SETUNIQUE", "SET UNIQUE"}
    };

    const auto it = kMap.find(compact_token(token));
    return it == kMap.end() ? std::string{} : it->second;
}

static bool split_cmdkey(const std::string& key,
                         std::string& catalog,
                         std::string& command)
{
    const std::string k = upper(trim_copy(key));
    const auto bar = k.find('|');
    if (bar == std::string::npos) {
        catalog.clear();
        command = k;
        return !command.empty();
    }
    catalog = k.substr(0, bar);
    command = k.substr(bar + 1);
    return !catalog.empty() || !command.empty();
}

static bool is_compact_dot_set_family_cmdkey(const std::string& key,
                                             std::string* expected = nullptr)
{
    std::string catalog;
    std::string command;
    if (!split_cmdkey(key, catalog, command)) {
        return false;
    }
    if (catalog != "DOT") {
        return false;
    }
    const std::string canon = compact_set_family_target(command);
    if (canon.empty()) {
        return false;
    }
    if (expected) {
        *expected = "DOT|" + canon;
    }
    return true;
}

static bool is_set_family_alias_row(const std::string& kind,
                                    const std::string& name,
                                    const std::string& text)
{
    const std::string k = upper(trim_copy(kind));
    if (k != "ALIAS" && k != "VARIANT") {
        return false;
    }
    return !compact_set_family_target(name).empty() ||
           !compact_set_family_target(text).empty();
}

static bool read_exact(std::ifstream& in, void* buf, size_t n)
{
    in.read(reinterpret_cast<char*>(buf), static_cast<std::streamsize>(n));
    return static_cast<size_t>(in.gcount()) == n;
}

struct Dbf {
    DbfHeader        hdr{};
    std::vector<Col> cols;
    std::ifstream    in;
    size_t           rec0{};
};

static Dbf open_dbf(const fs::path& p)
{
    Dbf dbf;
    dbf.in.open(p, std::ios::binary);
    if (!dbf.in) {
        throw std::runtime_error("cannot open " + p.string());
    }
    if (!read_exact(dbf.in, &dbf.hdr, sizeof(dbf.hdr))) {
        throw std::runtime_error("short read header");
    }

    while (true) {
        char c;
        if (!dbf.in.read(&c, 1)) {
            throw std::runtime_error("short read fields");
        }
        if (static_cast<unsigned char>(c) == 0x0D) {
            break;
        }

        DbfField f{};
        f.name[0] = c;
        if (!read_exact(dbf.in, reinterpret_cast<char*>(&f) + 1, sizeof(DbfField) - 1)) {
            throw std::runtime_error("short read field");
        }

        Col col;
        col.name = dbf_field_name_11(f.name);
        col.type = f.type;
        col.len  = f.length;
        dbf.cols.push_back(col);
    }

    size_t off = 1;
    for (auto& c : dbf.cols) {
        c.offset = off;
        off += c.len;
    }
    dbf.rec0 = static_cast<size_t>(dbf.hdr.header_len);
    return dbf;
}

static int col_index(const Dbf& dbf, const std::string& name)
{
    const std::string want = upper(name);
    for (int i = 0; i < static_cast<int>(dbf.cols.size()); ++i) {
        if (upper(dbf.cols[i].name) == want) {
            return i;
        }
    }
    return -1;
}

static std::string memo_preview(const fs::path& dbt_path,
                                uint32_t start_block,
                                size_t& out_len,
                                size_t max_chars = 240)
{
    out_len = 0;
    if (start_block == 0) {
        return {};
    }

    std::ifstream dbt(dbt_path, std::ios::binary);
    if (!dbt) {
        return {};
    }

    const uint64_t base = uint64_t(start_block) * 512ull;
    dbt.seekg(static_cast<std::streamoff>(base), std::ios::beg);

    uint8_t lenbuf[4]{};
    if (!dbt.read(reinterpret_cast<char*>(lenbuf), 4)) {
        return {};
    }

    const uint32_t len = (uint32_t(lenbuf[0]) |
                          (uint32_t(lenbuf[1]) << 8) |
                          (uint32_t(lenbuf[2]) << 16) |
                          (uint32_t(lenbuf[3]) << 24));
    out_len = len;

    std::string s;
    s.resize(std::min<size_t>(len, max_chars));
    if (!dbt.read(&s[0], static_cast<std::streamsize>(s.size()))) {
        s.clear();
    }

    for (auto& ch : s) {
        if ((unsigned char)ch < 0x20 && ch != '\n' && ch != '\r' && ch != '\t') {
            ch = ' ';
        }
    }
    return s;
}

static std::string read_char(const std::vector<char>& rec, const Col& c)
{
    std::string s(rec.data() + c.offset, rec.data() + c.offset + c.len);
    return trimr(s);
}

static uint32_t read_mptr(const std::vector<char>& rec, const Col& c)
{
    std::string s(rec.data() + c.offset, rec.data() + c.offset + c.len);
    s = triml(trimr(s));
    if (s.empty()) {
        return 0;
    }
    return static_cast<uint32_t>(std::strtoul(s.c_str(), nullptr, 10));
}

static std::string read_cell(const std::vector<char>& rec,
                             const Dbf& dbf,
                             int ix,
                             const fs::path& dbt_path,
                             size_t* memo_len = nullptr,
                             size_t max_memo_chars = 240)
{
    if (memo_len) {
        *memo_len = 0;
    }
    if (ix < 0 || ix >= static_cast<int>(dbf.cols.size())) {
        return {};
    }

    const Col& c = dbf.cols[ix];
    if (c.type == 'M') {
        const uint32_t blk = read_mptr(rec, c);
        size_t len = 0;
        std::string s = memo_preview(dbt_path, blk, len, max_memo_chars);
        if (memo_len) {
            *memo_len = len;
        }
        return s;
    }
    return read_char(rec, c);
}

static std::pair<fs::path, fs::path> resolve_paths(const fs::path& outdir)
{
    fs::path p1 = outdir / "commands.dbf";
    if (fs::exists(p1)) {
        return {p1, outdir / "commands.dbt"};
    }

    fs::path p2 = outdir / "data" / "commands.dbf";
    if (fs::exists(p2)) {
        return {p2, outdir / "data" / "commands.dbt"};
    }

    throw std::runtime_error(
        "commands.dbf not found in '" + outdir.string() +
        "' or '" + (outdir / "data").string() + "'");
}

static std::pair<fs::path, fs::path> resolve_artifact_paths(const fs::path& outdir)
{
    fs::path p1 = outdir / "help_artifacts.dbf";
    if (fs::exists(p1)) {
        return {p1, outdir / "help_artifacts.dbt"};
    }

    fs::path p2 = outdir / "data" / "help_artifacts.dbf";
    if (fs::exists(p2)) {
        return {p2, outdir / "data" / "help_artifacts.dbt"};
    }

    throw std::runtime_error(
        "help_artifacts.dbf not found in '" + outdir.string() +
        "' or '" + (outdir / "data").string() + "'");
}

static std::unordered_set<std::string> load_command_keys(const fs::path& outdir)
{
    std::unordered_set<std::string> keys;

    try {
        auto [dbf_path, dbt_path] = resolve_paths(outdir);
        (void)dbt_path;
        auto dbf = open_dbf(dbf_path);

        const int ix_cat = col_index(dbf, "CATALOG");
        const int ix_cmd = col_index(dbf, "COMMAND");
        const int ix_key = col_index(dbf, "CMDKEY");
        if ((ix_cat < 0 || ix_cmd < 0) && ix_key < 0) {
            return keys;
        }

        dbf.in.seekg(static_cast<std::streamoff>(dbf.rec0), std::ios::beg);
        std::vector<char> rec(dbf.hdr.rec_len);

        for (uint32_t r = 0; r < dbf.hdr.nrecs; ++r) {
            if (!read_exact(dbf.in, rec.data(), rec.size())) {
                break;
            }
            if (!rec.empty() && rec[0] == '*') {
                continue;
            }

            std::string key;
            if (ix_key >= 0) {
                key = upper(trim_copy(read_char(rec, dbf.cols[ix_key])));
            }
            if (key.empty() && ix_cat >= 0 && ix_cmd >= 0) {
                key = upper(trim_copy(read_char(rec, dbf.cols[ix_cat]))) + "|" +
                      upper(trim_copy(read_char(rec, dbf.cols[ix_cmd])));
            }
            if (!key.empty()) {
                keys.insert(key);
            }
        }
    } catch (...) {
    }

    return keys;
}

static std::vector<std::string> compact_set_family_command_keys(const std::unordered_set<std::string>& keys)
{
    std::vector<std::string> out;
    for (const auto& key : keys) {
        if (is_compact_dot_set_family_cmdkey(key)) {
            out.push_back(key);
        }
    }
    std::sort(out.begin(), out.end());
    return out;
}

static void print_map(const char* title, const std::map<std::string, int>& counts)
{
    std::cout << title << "\n";
    if (counts.empty()) {
        std::cout << "  (none)\n";
        return;
    }
    for (const auto& kv : counts) {
        std::cout << "  " << std::left << std::setw(18) << kv.first << " " << kv.second << "\n";
    }
}

static void run_artifacts_check(const std::string& dir_arg, int limit)
{
    fs::path outdir = resolve_help_dir_arg(dir_arg);

    auto [dbf_path, dbt_path] = resolve_artifact_paths(outdir);
    auto dbf = open_dbf(dbf_path);

    const int ix_id       = col_index(dbf, "ID");
    const int ix_catalog  = col_index(dbf, "CATALOG");
    const int ix_command  = col_index(dbf, "COMMAND");
    const int ix_cmdkey   = col_index(dbf, "CMDKEY");
    const int ix_owner    = col_index(dbf, "OWNER");
    const int ix_kind     = col_index(dbf, "KIND");
    const int ix_source   = col_index(dbf, "SOURCE");
    const int ix_confid   = col_index(dbf, "CONFID");
    const int ix_severity = col_index(dbf, "SEVERITY");
    const int ix_name     = col_index(dbf, "NAME");
    const int ix_text     = col_index(dbf, "TEXT");
    const int ix_detail   = col_index(dbf, "DETAIL");
    const int ix_evidence = col_index(dbf, "EVIDENCE");
    (void)ix_catalog;
    (void)ix_command;
    (void)ix_owner;
    (void)ix_detail;
    (void)ix_evidence;

    std::cout << "Opened " << dbf_path.string()
              << " (" << dbf.hdr.nrecs << " artifact rows)\n";

    std::cout << "Columns:";
    for (const auto& c : dbf.cols) {
        std::cout << " [" << c.name << ":" << c.type << "," << int(c.len) << "]";
    }
    std::cout << "\n";

    if (ix_kind < 0 || ix_source < 0 || ix_confid < 0) {
        std::cout << "Missing expected HELP DATA v2 columns; need at least KIND, SOURCE, CONFID.\n";
        return;
    }

    const auto valid_keys = load_command_keys(outdir);

    std::map<std::string, int> by_kind;
    std::map<std::string, int> by_source;
    std::map<std::string, int> by_confid;
    std::map<std::string, int> by_severity;

    int deleted_rows = 0;
    int blank_kind = 0;
    int blank_source = 0;
    int blank_confid = 0;
    int source_miner_rows = 0;
    int heuristic_rows = 0;
    int message_rows = 0;
    int orphan_cmdkey_rows = 0;
    int blank_text_rows = 0;
    int compact_set_family_cmdkey_rows = 0;
    int set_family_alias_rows = 0;
    std::map<std::string, int> compact_set_family_cmdkeys;
    int shown = 0;

    struct RowPreview {
        std::string id;
        std::string kind;
        std::string source;
        std::string confid;
        std::string cmdkey;
        std::string name;
        std::string text;
    };
    std::vector<RowPreview> previews;

    dbf.in.seekg(static_cast<std::streamoff>(dbf.rec0), std::ios::beg);
    std::vector<char> rec(dbf.hdr.rec_len);

    for (uint32_t r = 0; r < dbf.hdr.nrecs; ++r) {
        if (!read_exact(dbf.in, rec.data(), rec.size())) {
            break;
        }
        if (!rec.empty() && rec[0] == '*') {
            ++deleted_rows;
            continue;
        }

        const std::string kind = upper(trim_copy(read_cell(rec, dbf, ix_kind, dbt_path)));
        const std::string src  = upper(trim_copy(read_cell(rec, dbf, ix_source, dbt_path)));
        const std::string conf = upper(trim_copy(read_cell(rec, dbf, ix_confid, dbt_path)));
        const std::string sev  = upper(trim_copy(read_cell(rec, dbf, ix_severity, dbt_path)));
        const std::string key  = upper(trim_copy(read_cell(rec, dbf, ix_cmdkey, dbt_path)));
        const std::string name = upper(trim_copy(read_cell(rec, dbf, ix_name, dbt_path)));

        by_kind[kind.empty() ? "(blank)" : kind]++;
        by_source[src.empty() ? "(blank)" : src]++;
        by_confid[conf.empty() ? "(blank)" : conf]++;
        by_severity[sev.empty() ? "(blank)" : sev]++;

        if (kind.empty()) ++blank_kind;
        if (src.empty()) ++blank_source;
        if (conf.empty()) ++blank_confid;
        if (src == "SOURCE_MINER") ++source_miner_rows;
        if (conf == "HEURISTIC") ++heuristic_rows;
        if (kind == "MESSAGE") ++message_rows;

        size_t text_len = 0;
        std::string text = read_cell(rec, dbf, ix_text, dbt_path, &text_len, 160);
        if (is_compact_dot_set_family_cmdkey(key)) {
            ++compact_set_family_cmdkey_rows;
            compact_set_family_cmdkeys[key]++;
        }
        if (is_set_family_alias_row(kind, name, text)) {
            ++set_family_alias_rows;
        }
        if (text_len == 0 && trim_copy(text).empty()) {
            ++blank_text_rows;
        }

        if (!key.empty() && !valid_keys.empty() && valid_keys.count(key) == 0) {
            ++orphan_cmdkey_rows;
        }

        if (shown < limit) {
            RowPreview p;
            p.id = read_cell(rec, dbf, ix_id, dbt_path);
            p.kind = kind;
            p.source = src;
            p.confid = conf;
            p.cmdkey = key;
            p.name = read_cell(rec, dbf, ix_name, dbt_path);
            p.text = text;
            previews.push_back(std::move(p));
            ++shown;
        }
    }

    std::cout << "\nHELP DATA v2 artifact summary\n";
    std::cout << "  rows                 : " << dbf.hdr.nrecs << "\n";
    std::cout << "  deleted rows         : " << deleted_rows << "\n";
    std::cout << "  source-miner rows    : " << source_miner_rows << "\n";
    std::cout << "  heuristic rows       : " << heuristic_rows << "\n";
    std::cout << "  message rows         : " << message_rows << "\n";
    std::cout << "  blank text rows      : " << blank_text_rows << "\n";
    std::cout << "  orphan CMDKEY rows   : " << orphan_cmdkey_rows;
    if (valid_keys.empty()) {
        std::cout << "  (legacy command keys unavailable)";
    }
    std::cout << "\n";
    std::cout << "  blank KIND/SOURCE/CONFID: "
              << blank_kind << "/" << blank_source << "/" << blank_confid << "\n";

    const auto compact_command_keys = compact_set_family_command_keys(valid_keys);
    std::cout << "\nSET-family canonicalization\n";
    std::cout << "  compact DOT SET-family command keys : " << compact_command_keys.size() << "\n";
    std::cout << "  compact DOT SET-family artifact rows: " << compact_set_family_cmdkey_rows << "\n";
    std::cout << "  SET-family alias/variant rows       : " << set_family_alias_rows << "\n";
    if (!compact_command_keys.empty()) {
        std::cout << "  ERROR compact SET-family command keys must canonicalize upward:\n";
        for (const auto& key : compact_command_keys) {
            std::string expected;
            (void)is_compact_dot_set_family_cmdkey(key, &expected);
            std::cout << "    " << key << " -> " << expected << "\n";
        }
    }
    if (!compact_set_family_cmdkeys.empty()) {
        std::cout << "  ERROR compact SET-family artifact CMDKEY rows must use canonical DOT|SET * keys:\n";
        for (const auto& kv : compact_set_family_cmdkeys) {
            std::string expected;
            (void)is_compact_dot_set_family_cmdkey(kv.first, &expected);
            std::cout << "    " << kv.first << " rows=" << kv.second
                      << " expected=" << expected << "\n";
        }
    }

    std::cout << "\n";
    print_map("By KIND:", by_kind);
    std::cout << "\n";
    print_map("By SOURCE:", by_source);
    std::cout << "\n";
    print_map("By CONFID:", by_confid);
    std::cout << "\n";
    print_map("By SEVERITY:", by_severity);

    if (limit > 0) {
        std::cout << "\nPreview rows (limit " << limit << ")\n";
        std::cout << std::left
                  << std::setw(6)  << "ID"
                  << std::setw(16) << "KIND"
                  << std::setw(16) << "SOURCE"
                  << std::setw(12) << "CONFID"
                  << std::setw(28) << "CMDKEY"
                  << std::setw(22) << "NAME"
                  << "TEXT\n";
        std::cout << "------------------------------------------------------------------------------------------------------------\n";
        for (const auto& p : previews) {
            std::string key = p.cmdkey;
            if (key.size() > 27) key.resize(27);
            std::string name = p.name;
            if (name.size() > 21) name.resize(21);
            std::string text = p.text;
            for (auto& ch : text) {
                if (ch == '\n' || ch == '\r' || ch == '\t') ch = ' ';
            }
            if (text.size() > 100) text.resize(100);

            std::cout << std::left
                      << std::setw(6)  << p.id
                      << std::setw(16) << p.kind
                      << std::setw(16) << p.source
                      << std::setw(12) << p.confid
                      << std::setw(28) << key
                      << std::setw(22) << name
                      << text << "\n";
        }
    }

    std::cout << "\nDBT: " << dbt_path.string() << "\n";
}

static void print_cmdhelpchk_usage()
{
    std::cout << "Usage:\n"
              << "  CMDHELPCHK\n"
              << "  CMDHELPCHK USAGE\n"
              << "  CMDHELPCHK REF\n"
              << "  CMDHELPCHK REFLECT\n"
              << "  CMDHELPCHK ARTIFACTS [dir] [limit]\n"
              << "  CMDHELPCHK V2 [dir] [limit]\n"
              << "  CMDHELPCHK <dir> [limit]\n"
              << "\n"
              << "Modes:\n"
              << "  REF/REFLECT  Validate reflected command/function metadata.\n"
              << "  ARTIFACTS    Validate HELP DATA v2 help_artifacts.dbf/.dbt.\n"
              << "  <dir>        Validate legacy commands.dbf/.dbt in a help directory.\n";
}

} // anonymous namespace

void cmd_CMDHELPCHK(DbArea& /*area*/, std::istringstream& in)
{
    std::string rest;
    std::getline(in, rest);
    rest = trim_copy(rest);

    std::vector<std::string> words = split_words(rest);
    std::string first = words.empty() ? std::string() : upper(words[0]);

    if (first == "USAGE" || first == "HELP" || first == "/?" || first == "?") {
        print_cmdhelpchk_usage();
        return;
    }

    // ------------------------------------------------------------------------
    // HELP DATA v2 artifact validation mode
    //
    // Usage:
    //   CMDHELPCHK ARTIFACTS
    //   CMDHELPCHK ARTIFACTS .
    //   CMDHELPCHK ARTIFACTS . 20
    //   CMDHELPCHK V2 . 20
    // ------------------------------------------------------------------------
    if (first == "ARTIFACTS" || first == "ARTIFACT" || first == "V2") {
        std::string dir_arg;
        int limit = 10;

        if (words.size() >= 2) {
            dir_arg = words[1];
        }
        if (words.size() >= 3) {
            try {
                limit = std::max(0, std::stoi(words[2]));
            } catch (...) {
            }
        }

        try {
            run_artifacts_check(dir_arg, limit);
        } catch (const std::exception& ex) {
            std::cout << "CMDHELPCHK ARTIFACTS error: " << ex.what() << "\n";
        }
        return;
    }

    // ------------------------------------------------------------------------
    // Reflection-system mode
    //
    // Usage:
    //   CMDHELPCHK
    //   CMDHELPCHK REF
    //   CMDHELPCHK REFLECT
    // ------------------------------------------------------------------------
    if (rest.empty() || first == "REF" || first == "REFLECT") {
        using namespace refsys;

        ReferenceCollection rc = build_reference_collection();

        std::cout << "\n=== REFLECTION REPORTS ===\n\n";

        report_subcommands(rc, std::cout);
        report_commands(rc, std::cout);
        report_functions(rc, std::cout);

        std::vector<CheckIssue> issues;

        auto add = [&](std::vector<CheckIssue> more) {
            issues.insert(issues.end(), more.begin(), more.end());
        };

        add(check_unresolved_variant_targets(rc));
        add(check_duplicate_canonical_commands(rc));
        add(check_duplicate_subcommands(rc));
        add(check_missing_parent_commands(rc));
        add(check_set_family_canonicalization(rc));
        add(check_duplicate_functions(rc));
        add(check_invalid_function_arg_ranges(rc));
        add(check_missing_function_categories(rc));

        print_check_issues(issues, std::cout);
        return;
    }

    // ------------------------------------------------------------------------
    // Legacy DBF validation mode
    //
    // Usage:
    //   CMDHELPCHK <dir> [limit]
    // ------------------------------------------------------------------------
    std::string outdir = words.empty() ? std::string() : words[0];
    int limit = 5;
    if (words.size() >= 2) {
        try {
            limit = std::max(1, std::stoi(words[1]));
        } catch (...) {
        }
    }

    fs::path outdir_p = resolve_help_dir_arg(outdir);
    outdir = outdir_p.string();

    try {
        auto [dbf_path, dbt_path] = resolve_paths(outdir);
        auto dbf = open_dbf(dbf_path);

        int id_ix = -1;
        int cmd_ix = -1;
        int usage_ix = -1;
        int verbose_ix = -1;
        std::vector<int> memo_ix;

        for (int i = 0; i < static_cast<int>(dbf.cols.size()); ++i) {
            const auto n = upper(dbf.cols[i].name);
            if (n == "ID") {
                id_ix = i;
            } else if (n == "COMMAND") {
                cmd_ix = i;
            } else if (n == "USAGE") {
                usage_ix = i;
            } else if (n == "VERBOSE") {
                verbose_ix = i;
            }

            if (dbf.cols[i].type == 'M') {
                memo_ix.push_back(i);
            }
        }

        if (usage_ix < 0 && !memo_ix.empty()) {
            usage_ix = memo_ix[0];
        }
        if (verbose_ix < 0 && memo_ix.size() >= 2) {
            verbose_ix = memo_ix[1];
        }

        std::cout << "Opened " << dbf_path.string()
                  << " (" << dbf.hdr.nrecs << " rows)\n";
        std::cout << "Columns:";
        for (auto& c : dbf.cols) {
            std::cout << " [" << c.name << ":" << c.type << "," << int(c.len) << "]";
        }
        std::cout << "\n";

        if (id_ix < 0 || cmd_ix < 0 || usage_ix < 0) {
            std::cout << "Missing expected columns; need at least ID, COMMAND, and one memo (USAGE)\n";
            return;
        }

        std::cout << std::left
                  << std::setw(6)  << "ID"
                  << std::setw(20) << "COMMAND"
                  << std::setw(14) << (std::string(dbf.cols[usage_ix].name) + "(len)")
                  << "Memo preview\n";
        std::cout << "-----------------------------------------------------------------------------\n";

        dbf.in.seekg(static_cast<std::streamoff>(dbf.rec0), std::ios::beg);
        std::vector<char> rec(dbf.hdr.rec_len);

        int shown = 0;
        for (uint32_t r = 0; r < dbf.hdr.nrecs && shown < limit; ++r) {
            if (!read_exact(dbf.in, rec.data(), rec.size())) {
                break;
            }
            if (rec[0] == '*') {
                continue;
            }

            const auto& C_id = dbf.cols[id_ix];
            const auto& C_nm = dbf.cols[cmd_ix];
            const auto& C_u  = dbf.cols[usage_ix];

            const auto id_str  = read_char(rec, C_id);
            const auto cmd_str = read_char(rec, C_nm);
            const auto u_blk   = read_mptr(rec, C_u);

            size_t u_len = 0;
            const auto u_prev = memo_preview(dbt_path, u_blk, u_len);

            std::cout << std::left
                      << std::setw(6)  << id_str
                      << std::setw(20) << cmd_str
                      << std::setw(14) << std::to_string(u_len)
                      << u_prev << "\n";

            if (verbose_ix >= 0) {
                const auto v_blk = read_mptr(rec, dbf.cols[verbose_ix]);
                size_t v_len = 0;
                const auto v_prev = memo_preview(dbt_path, v_blk, v_len);
                if (!v_prev.empty()) {
                    std::cout << std::setw(26) << " "
                              << std::setw(14) << std::to_string(v_len)
                              << v_prev << "\n";
                }
            }

            ++shown;
        }

        if (shown == 0) {
            std::cout << "(no rows shown; try increasing limit)\n";
        }

        std::cout << "DBT: " << dbt_path.string() << "\n";
    } catch (const std::exception& ex) {
        std::cout << "CMDHELPCHK error: " << ex.what() << "\n";
    }
}
