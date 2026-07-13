// @dottalk.usage v1
// owner: DOT|CMDHELP
// command: CMDHELP
// category: help
// status: supported
// noargs: report
// effect: build-report
// mutates: helpdata
// usage-access: CMDHELP USAGE
// summary:
//   Build or report the current HELP DATA catalogs and their legacy compatibility views.
//
// usage:
//   CMDHELP
//   CMDHELP USAGE
//   CMDHELP BUILD
//   CMDHELP BUILD V2
//   CMDHELP BUILD LEGACY
//   CMDHELP LEGACY
//   CMDHELP <topic> PREVIEW LOCALE <locale>
//   CMDHELP <topic> LOCALE <locale>
//
// notes:
//   CMDHELP BUILD writes the current HELP DATA DBFs.
//   CMDHELP BUILD V2 is a silent compatibility alias for CMDHELP BUILD.
//   CMDHELP BUILD LEGACY drives the old commands.dbf/cmd_args.dbf builder path.
//   CMDHELP with no arguments reports current HELP DATA from help_line.dbf.
//   CMDHELP LEGACY reports the old commands.dbf/cmd_args.dbf surface.
//   Locale preview is explicit-only and does not change normal CMDHELP behavior.
//   Preview falls back to canonical/source HELP text when locale rows are missing or blocked.
//   The legacy writer/reader remains in this file only as an explicit compatibility path.
//   It is no longer the default build/report surface.
//
// risk:
//   reads_help_metadata: yes
//   mutates_table_data: yes
//   mutates_session: yes
//
// related:
//   HELP
//   CMDHELPCHK
//   DOTHELP
//   FOXHELP
//
#include "cmdhelp.hpp"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "xbase.hpp"
#include "xbase_field_getters.hpp"
#include "cli/command_output.hpp"
#include "cli/output_router.hpp"
#include "edref.hpp"
#include "helpdata_cmdhelp_bridge.hpp"
#include "memo/memo_auto.hpp"
#include "memo/memo_ref.hpp"

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

namespace { // ==== utils & miners ==================================================

static fs::path help_root_dir() {
#if HAVE_PATHS
    try {
        namespace paths = dottalk::paths;
        return paths::get_slot(paths::Slot::HELP);
    } catch (...) {}
#endif
    std::error_code ec;
    fs::path cand = fs::current_path(ec) / "help";
    if (!ec && fs::exists(cand, ec) && fs::is_directory(cand, ec)) return cand;
    fs::path cwd = fs::current_path(ec);
    return ec ? fs::path{} : cwd;
}

// Resolve an output/read directory argument for help DBFs.
// - empty / "." => HELP slot directory
// - absolute => unchanged
// - relative => interpreted relative to HELP slot directory
static fs::path resolve_help_dir_arg(const std::string& argRaw) {
    std::string a = argRaw;
    while (!a.empty() && std::isspace(static_cast<unsigned char>(a.front()))) a.erase(a.begin());
    while (!a.empty() && std::isspace(static_cast<unsigned char>(a.back()))) a.pop_back();
    if (a.empty() || a == ".") return help_root_dir();
    fs::path p(a);
    if (p.is_absolute()) return p;
    return fs::weakly_canonical(help_root_dir() / p);
}

std::string up(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

static std::string to_string_or_empty(const char* p) {
    return p ? std::string(p) : std::string();
}

static std::string make_cmdkey(const std::string& catalog, const std::string& command) {
    return up(catalog) + "|" + up(command);
}

static std::vector<std::string> split_words(const std::string& s) {
    std::vector<std::string> out;
    std::istringstream ss(s);
    std::string w;
    while (ss >> w) out.push_back(w);
    return out;
}

static bool contains_space_char(const std::string& s) {
    return std::any_of(s.begin(), s.end(),
                       [](unsigned char ch) { return std::isspace(ch) != 0; });
}

static std::string compact_set_query_token(std::string s) {
    s = up(std::move(s));
    s.erase(std::remove_if(s.begin(), s.end(),
                           [](unsigned char ch) {
                               return std::isspace(ch) != 0 || ch == '_' || ch == '-';
                           }),
            s.end());
    return s;
}

static std::string canonical_set_family_query(const std::string& query) {
    const std::string q = up(query);
    // A spaced query like SET ORDER is already canonical and should resolve
    // naturally.  Compact legacy spellings like SETORDER and SET_UNIQUE are
    // aliases into the spaced SET * topic.
    if (contains_space_char(q)) {
        return {};
    }

    static const std::unordered_map<std::string, std::string> kMap = {
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

    const auto it = kMap.find(compact_set_query_token(q));
    return it == kMap.end() ? std::string{} : it->second;
}

static bool is_expression_function_name(const std::string& name) {
    static const std::unordered_set<std::string> names = {
        "ABS","ACOS","ALLTRIM","ASC","ASIN","AT","ATAN","ATC","BETWEEN",
        "CDOW","CEILING","CHR","CHRTRAN","CMONTH","CONCAT","COS","CTOD",
        "DATE","DATEADD","DATEDIFF","DATETIME","DAY","DOW","DTOC","DTOS",
        "EMPTY","EXP","FLOOR","GOMONTH","INT","LEFT","LEN","LIKE","LOG",
        "LOG10","LOWER","LTRIM","MAX","MIN","MOD","MONTH","NOW","RAND",
        "RAT","REPLICATE","RIGHT","ROUND","RTRIM","SECONDS","SIN","SOUNDEX",
        "SPACE","SQRT","STR","STRTRAN","SUBSTR","TAN","TIME","TODAY",
        "TRANSFORM","TRIM","UPPER","VAL","YEAR"
    };
    return names.count(up(name)) != 0;
}

static bool is_developer_surface_name(const std::string& name) {
    const std::string n = up(name);
    return n.find("LMDB") != std::string::npos ||
           n.find("_BUFFER") != std::string::npos ||
           n == "TABLE_BUFFER" ||
           n == "SCAN_BUFFER" ||
           n == "LOOP_BUFFER" ||
           n == "WHILE_BUFFER" ||
           n == "UNTIL_BUFFER";
}

static std::string generated_pending_summary(const std::string& name) {
    const std::string n = up(name);
    if (is_expression_function_name(n)) {
        return {};
    }
    if (is_developer_surface_name(n)) {
        return n + " is a developer/diagnostic command surface; curated DOTREF help is pending.";
    }
    return n + " is a registered DotTalk++ command; curated DOTREF support status and help summary are pending.";
}

// FoxRef syntax -> likely switches
std::vector<std::string> switches_from_syntax(const std::string& syntax) {
    static const std::unordered_set<std::string> IGN = {
        "USE","FIELDS","INDEX","SETINDEX","LIST","FIND","SEEK","GOTO","TOP","BOTTOM","APPEND","APPEND BLANK",
        "REPLACE","DELETE","RECALL","PACK","EXPORT","IMPORT","STRUCT","STATUS","COUNT","SET","ORDER","TO","INTO",
        "<TABLE>","<FLD>","<FIELD>","<VALUE>","<CSV>","<N>","<TAG>","<EXPR>","#N","<SPEC>","<NAME>","<RECNO>",
        "<VAL>","<FIELD|#N>","<TAG|PATH>","<OP>","<AREA>","IN","BY","WHERE","GROUP","UNIQUE","ASC","DESC","ALIAS"
    };
    static const std::unordered_set<std::string> LIKELY = {
        "ALL","VERBOSE","TAG","INDEX","NOINDEX","FOR","WHILE","NEXT","RECORD","REST",
        "ASC","DESC","UNIQUE","FIELDS","ALIAS","ON","OFF"
    };

    std::vector<std::string> out;
    std::string t;
    for (char c : syntax) {
        if (std::isalnum(static_cast<unsigned char>(c)) || c == '_') {
            t.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(c))));
        } else {
            if (!t.empty()) {
                if (!IGN.count(t) && LIKELY.count(t)) out.push_back(t);
                t.clear();
            }
        }
    }
    if (!t.empty()) {
        if (!IGN.count(t) && LIKELY.count(t)) out.push_back(t);
    }

    std::sort(out.begin(), out.end());
    out.erase(std::unique(out.begin(), out.end()), out.end());
    return out;
}

std::string command_hint_from_path(const fs::path& p) {
    std::regex rx(R"(cmd_([a-zA-Z0-9_]+))");
    std::smatch m;
    const std::string base = p.stem().string();
    if (std::regex_search(base, m, rx) && m.size() > 1) {
        std::string n = m[1].str();
        std::replace(n.begin(), n.end(), '_', ' ');
        return up(n);
    }
    return {};
}

// Broader mining: tokens, NO* toggles, SET <OPT> ON|OFF, string flags.
// This is legacy cmd_args support only.  Current HELP DATA mining lives in
// src/help/helpdata_source_miner.cpp.
std::unordered_map<std::string, std::set<std::string>>
scan_sources_for_switches(const std::vector<std::string>& roots)
{
    const std::regex rx_case_token(R"(\bcase\s+(?:Token::|TOK_|TOKEN_)([A-Z][A-Z0-9_]+)\b)");
    const std::regex rx_token(R"(\b(?:Token::|TOK_|TOKEN_)([A-Z][A-Z0-9_]+)\b)");
    const std::regex rx_str(R"(["']([A-Z][A-Z0-9_]{1,24})["'])");
    const std::regex rx_has(R"(\b(?:hasSwitch|hasFlag|is_kw|has_kw|seenSwitch)\s*\(\s*(?:["']([A-Z][A-Z0-9_]{1,24})["']|(?:Token::|TOK_|TOKEN_)([A-Z][A-Z0-9_]+))\s*\))");
    const std::regex rx_reg(R"(register_?command\s*\(\s*["']([A-Z][A-Z0-9_ ]+)["'])");
    const std::regex rx_set(R"(\bSET\s+([A-Z][A-Z0-9_]+)\s+(ON|OFF)\b)");
    const std::regex rx_no(R"(\bNO([A-Z][A-Z0-9_]+)\b)");

    static const std::unordered_set<std::string> SWITCHLIKE = {
        "ALL","VERBOSE","TAG","INDEX","NOINDEX","FOR","WHILE","NEXT","RECORD","REST",
        "ASC","DESC","UNIQUE","FIELDS","ALIAS","INTO","TO","OFF","ON"
    };
    static const std::unordered_set<std::string> EXCLUDE_CMDS = {
        "USE","SCAN","ENDSCAN","SELECT","DELETE","REPLACE","INSERT","UPDATE","BROWSE","COUNT","SET","ORDER",
        "TOP","BOTTOM","GOTO","SEEK","FIND","APPEND","STRUCT","STATUS","PACK","ZAP","INDEX","SETINDEX"
    };

    std::unordered_map<std::string, std::set<std::string>> per_cmd;

    auto consider = [&](const std::string& cmd, const std::string& tok) {
        if (cmd.empty()) return;
        std::string t = up(tok);
        if (EXCLUDE_CMDS.count(t)) return;
        if (t.rfind("NO", 0) == 0 || SWITCHLIKE.count(t)) per_cmd[cmd].insert(t);
    };

    for (const auto& root : roots) {
        fs::path rp(root);
        if (!fs::exists(rp)) continue;

        for (auto it = fs::recursive_directory_iterator(rp);
             it != fs::recursive_directory_iterator();
             ++it) {
            if (!it->is_regular_file()) continue;

            const auto& p = it->path();
            const auto ext = up(p.extension().string());
            if (ext != ".CPP" && ext != ".HPP" && ext != ".H" && ext != ".CC" && ext != ".CXX") continue;

            std::ifstream fin(p, std::ios::in | std::ios::binary);
            if (!fin) continue;
            std::string s((std::istreambuf_iterator<char>(fin)), std::istreambuf_iterator<char>());

            std::string cmd = {};
            std::smatch mreg;
            if (std::regex_search(s, mreg, rx_reg) && mreg.size() > 1) cmd = up(mreg[1].str());
            if (cmd.empty()) cmd = command_hint_from_path(p);
            if (cmd.empty()) continue;

            for (auto it2 = std::sregex_iterator(s.begin(), s.end(), rx_case_token);
                 it2 != std::sregex_iterator(); ++it2) consider(cmd, (*it2)[1].str());

            for (auto it2 = std::sregex_iterator(s.begin(), s.end(), rx_token);
                 it2 != std::sregex_iterator(); ++it2) consider(cmd, (*it2)[1].str());

            for (auto it2 = std::sregex_iterator(s.begin(), s.end(), rx_has);
                 it2 != std::sregex_iterator(); ++it2) {
                if ((*it2)[1].matched) consider(cmd, (*it2)[1].str());
                else if ((*it2)[2].matched) consider(cmd, (*it2)[2].str());
            }

            for (auto it2 = std::sregex_iterator(s.begin(), s.end(), rx_str);
                 it2 != std::sregex_iterator(); ++it2) consider(cmd, (*it2)[1].str());

            for (auto it2 = std::sregex_iterator(s.begin(), s.end(), rx_set);
                 it2 != std::sregex_iterator(); ++it2) {
                consider(cmd, (*it2)[1].str());
                consider(cmd, (*it2)[2].str());
            }

            for (auto it2 = std::sregex_iterator(s.begin(), s.end(), rx_no);
                 it2 != std::sregex_iterator(); ++it2) consider(cmd, "NO" + (*it2)[1].str());
        }
    }

    return per_cmd;
}

// ==== minimal DBF/DBT writer =================================================

#pragma pack(push,1)
struct DbfHeader {
    uint8_t  version{0x03};
    uint8_t  y{0}, m{0}, d{0};
    uint32_t nrecs{0};
    uint16_t header_len{0};
    uint16_t rec_len{0};
    uint8_t  reserved[20]{};
};

struct DbfField {
    char     name[11]{};
    char     type{'C'};
    uint32_t data_addr{0};
    uint8_t  length{0};
    uint8_t  decimals{0};
    uint8_t  reserved[14]{};
};
#pragma pack(pop)

static void put_name(char dst[11], const std::string& s) {
    std::memset(dst, 0, 11);
    std::strncpy(dst, s.c_str(), 10);
}

static DbfField fieldC(const std::string& name, uint8_t len) {
    DbfField f{};
    put_name(f.name, name);
    f.type = 'C';
    f.length = len;
    return f;
}

static DbfField fieldL(const std::string& name) {
    DbfField f{};
    put_name(f.name, name);
    f.type = 'L';
    f.length = 1;
    return f;
}

static DbfField fieldN(const std::string& name, uint8_t len) {
    DbfField f{};
    put_name(f.name, name);
    f.type = 'N';
    f.length = len;
    f.decimals = 0;
    return f;
}

static DbfField fieldM(const std::string& name) {
    DbfField f{};
    put_name(f.name, name);
    f.type = 'M';
    f.length = 10;
    return f;
}

static uint16_t u16_clamp_size(size_t v) {
    return static_cast<uint16_t>(std::min<size_t>(v, 65535));
}

class DBTWriter {
public:
    explicit DBTWriter(const std::string& path)
        : path_(path), blockSize_(512), nextBlock_(1)
    {
        out_.open(path_, std::ios::binary | std::ios::trunc);
        if (!out_) throw std::runtime_error("cannot open " + path_);
        write_header();
    }

    uint32_t append(const std::string& text) {
        const uint32_t start = nextBlock_;

        std::string payload;
        payload.resize(4);

        const uint32_t len = static_cast<uint32_t>(text.size());
        payload[0] = static_cast<char>((len >>  0) & 0xFF);
        payload[1] = static_cast<char>((len >>  8) & 0xFF);
        payload[2] = static_cast<char>((len >> 16) & 0xFF);
        payload[3] = static_cast<char>((len >> 24) & 0xFF);

        payload += text;
        payload.push_back(0x1A);

        size_t total = payload.size();
        size_t blocks = (total + blockSize_ - 1) / blockSize_;
        payload.resize(blocks * blockSize_, 0x00);

        out_.seekp(static_cast<std::streamoff>(start) * static_cast<std::streamoff>(blockSize_), std::ios::beg);
        out_.write(payload.data(), static_cast<std::streamsize>(payload.size()));

        nextBlock_ += static_cast<uint32_t>(blocks);
        flush_header();
        return start;
    }

    void close() {
        if (out_.is_open()) {
            flush_header();
            out_.flush();
            out_.close();
        }
    }

    ~DBTWriter() { close(); }

private:
    void write_header() {
        std::string hdr(blockSize_, 0x00);
        hdr[0] = static_cast<char>((nextBlock_ >>  0) & 0xFF);
        hdr[1] = static_cast<char>((nextBlock_ >>  8) & 0xFF);
        hdr[2] = static_cast<char>((nextBlock_ >> 16) & 0xFF);
        hdr[3] = static_cast<char>((nextBlock_ >> 24) & 0xFF);
        out_.seekp(0, std::ios::beg);
        out_.write(hdr.data(), static_cast<std::streamsize>(hdr.size()));
    }

    void flush_header() {
        std::string hdr(blockSize_, 0x00);
        hdr[0] = static_cast<char>((nextBlock_ >>  0) & 0xFF);
        hdr[1] = static_cast<char>((nextBlock_ >>  8) & 0xFF);
        hdr[2] = static_cast<char>((nextBlock_ >> 16) & 0xFF);
        hdr[3] = static_cast<char>((nextBlock_ >> 24) & 0xFF);
        out_.seekp(0, std::ios::beg);
        out_.write(hdr.data(), static_cast<std::streamsize>(hdr.size()));
    }

    std::string   path_;
    std::ofstream out_;
    const uint32_t blockSize_;
    uint32_t nextBlock_;
};

static void write_dbf_with_memo(const std::string& dbf_path,
                                const std::string& dbt_path,
                                const std::vector<DbfField>& fields,
                                const std::vector<std::vector<std::string>>& rows)
{
    DBTWriter dbt(dbt_path);

    const uint16_t header_len = u16_clamp_size(sizeof(DbfHeader) + (fields.size() * sizeof(DbfField)) + 1);
    uint16_t rec_len = 1;
    for (auto& f : fields) rec_len = static_cast<uint16_t>(rec_len + f.length);

    auto today = std::chrono::floor<std::chrono::days>(std::chrono::system_clock::now());
    std::chrono::year_month_day ymd{today};

    DbfHeader hdr{};
    hdr.y = static_cast<uint8_t>(int(ymd.year()) % 100);
    hdr.m = static_cast<uint8_t>(unsigned(ymd.month()));
    hdr.d = static_cast<uint8_t>(unsigned(ymd.day()));
    hdr.nrecs = static_cast<uint32_t>(rows.size());
    hdr.header_len = header_len;
    hdr.rec_len = rec_len;

    std::ofstream out(dbf_path, std::ios::binary | std::ios::trunc);
    if (!out) throw std::runtime_error("cannot open " + dbf_path);

    out.write(reinterpret_cast<const char*>(&hdr), sizeof(hdr));
    for (auto f : fields) out.write(reinterpret_cast<const char*>(&f), sizeof(f));
    const char term = 0x0D;
    out.write(&term, 1);

    auto write_fixed = [&](const std::string& s, uint8_t len) {
        std::string buf(len, ' ');
        std::memcpy(&buf[0], s.c_str(), std::min<size_t>(len, s.size()));
        out.write(buf.data(), len);
    };

    auto write_memo_ptr = [&](uint32_t block) {
        std::string ptr = std::to_string(block);
        if (ptr.size() < 10) ptr.append(10 - ptr.size(), ' ');
        else if (ptr.size() > 10) ptr = ptr.substr(0, 10);
        out.write(ptr.data(), 10);
    };

    for (const auto& r : rows) {
        const char not_deleted = ' ';
        out.write(&not_deleted, 1);

        for (size_t i = 0; i < fields.size(); ++i) {
            const auto& f = fields[i];
            std::string cell = (i < r.size() ? r[i] : "");

            switch (f.type) {
                case 'L': {
                    const char v = (!cell.empty() && (cell[0] == 'Y' || cell == "1" ||
                                                      cell[0] == 'y' || cell[0] == 'T' || cell[0] == 't')) ? 'T' : 'F';
                    std::string tmp(1, v);
                    write_fixed(tmp, f.length);
                    break;
                }
                case 'N': {
                    std::string buf = cell;
                    if (buf.size() < f.length) buf = std::string(f.length - buf.size(), ' ') + buf;
                    else if (buf.size() > f.length) buf = buf.substr(buf.size() - f.length);
                    out.write(buf.data(), f.length);
                    break;
                }
                case 'M': {
                    uint32_t block = 0;
                    if (!cell.empty()) block = dbt.append(cell);
                    write_memo_ptr(block);
                    break;
                }
                default: {
                    if (cell.size() < f.length) cell.append(f.length - cell.size(), ' ');
                    else if (cell.size() > f.length) cell = cell.substr(0, f.length);
                    out.write(cell.data(), f.length);
                    break;
                }
            }
        }
    }

    const char eof = 0x1A;
    out.write(&eof, 1);
}

// ==== minimal DBF/DBT reader (for SHOW/report mode) ==========================

class DBTReader {
public:
    explicit DBTReader(const std::string& path)
        : path_(path), blockSize_(512)
    {
        if (!path_.empty()) {
            in_.open(path_, std::ios::binary);
        }
        valid_ = in_.good();
    }

    bool valid() const { return valid_; }

    std::string read_block_string(uint32_t start_block) {
        if (!valid_ || start_block == 0) return {};

        const std::streamoff off =
            static_cast<std::streamoff>(start_block) * static_cast<std::streamoff>(blockSize_);

        in_.seekg(off, std::ios::beg);

        char lenb[4]{};
        in_.read(lenb, 4);
        if (!in_) return {};

        uint32_t len = (static_cast<unsigned char>(lenb[0])      ) |
                       (static_cast<unsigned char>(lenb[1]) <<  8) |
                       (static_cast<unsigned char>(lenb[2]) << 16) |
                       (static_cast<unsigned char>(lenb[3]) << 24);

        std::string s(len, '\0');
        in_.read(&s[0], static_cast<std::streamsize>(len));
        return s;
    }

private:
    std::string   path_;
    std::ifstream in_;
    const uint32_t blockSize_;
    bool          valid_{false};
};

struct DbfTable {
    std::vector<DbfField> fields;
    std::vector<std::vector<std::string>> rows;
};

static bool read_dbf_with_memo(const std::string& dbf_path,
                               const std::string& dbt_path,
                               DbfTable& out)
{
    std::ifstream in(dbf_path, std::ios::binary);
    if (!in) return false;

    DbfHeader hdr{};
    in.read(reinterpret_cast<char*>(&hdr), sizeof(hdr));
    if (!in) return false;

    const int nfields = (hdr.header_len - sizeof(DbfHeader) - 1) / sizeof(DbfField);
    if (nfields <= 0) return false;

    out.fields.resize(nfields);
    for (int i = 0; i < nfields; ++i) {
        in.read(reinterpret_cast<char*>(&out.fields[i]), sizeof(DbfField));
    }

    char term{};
    in.read(&term, 1);

    DBTReader dbt(dbt_path);

    auto read_fixed = [&](uint8_t len) -> std::string {
        std::string buf(len, '\0');
        in.read(&buf[0], len);
        if (!in) return {};
        while (!buf.empty() && buf.back() == ' ') buf.pop_back();
        return buf;
    };

    out.rows.clear();
    out.rows.reserve(hdr.nrecs);

    for (uint32_t r = 0; r < hdr.nrecs; ++r) {
        char delFlag = 0;
        in.read(&delFlag, 1);
        (void)delFlag;

        std::vector<std::string> row;
        row.reserve(nfields);

        for (int i = 0; i < nfields; ++i) {
            const auto& f = out.fields[i];
            if (f.type == 'M') {
                std::string ptr = read_fixed(10);
                uint32_t blk = 0;
                if (!ptr.empty()) {
                    try { blk = static_cast<uint32_t>(std::stoul(ptr)); }
                    catch (...) { blk = 0; }
                }
                row.push_back(dbt.read_block_string(blk));
            } else {
                row.push_back(read_fixed(f.length));
            }
        }

        out.rows.push_back(std::move(row));
    }

    return true;
}

static int dbf_field_index(const DbfTable& tbl, const char* wanted) {
    const std::string W = up(wanted);
    for (int i = 0; i < static_cast<int>(tbl.fields.size()); ++i) {
        std::string fn(tbl.fields[static_cast<size_t>(i)].name,
                       tbl.fields[static_cast<size_t>(i)].name +
                           strnlen(tbl.fields[static_cast<size_t>(i)].name, 11));
        if (up(fn) == W) return i;
    }
    return -1;
}

static std::string dbf_cell(const std::vector<std::string>& row, int ix) {
    if (ix < 0 || ix >= static_cast<int>(row.size())) return {};
    return row[static_cast<size_t>(ix)];
}

// ==== end utils ==============================================================

} // namespace

namespace cmdhelp {

inline std::ostream& out() {
    return cli::OutputRouter::instance().out();
}

// === catalog & args ==========================================================

std::vector<CommandInfo> collect_commands() {
    // Reference-header policy:
    // - FOX catalog rows are compatibility/history-facing, but when a real
    //   cmd_*.cpp implementation exists their syntax/summary should reflect the
    //   current DotTalk++ runtime truth, not stale FoxPro prose.
    // - DOT catalog rows describe the native DotTalk++ help identity.
    // - CMDHELP merges registry + FOX + DOT + ED catalogs; it does not treat
    //   legacy wording as authoritative over a live implementation contract.
    std::unordered_set<std::string> implemented;
    for (const auto& kv : dli::map()) implemented.insert(up(kv.first));

    std::vector<CommandInfo> out;
    out.reserve(foxref::catalog().size() + dotref::catalog().size() + edref::catalog().size() + implemented.size());
    int next_id = 1;

    std::unordered_set<std::string> seen_keys;

    auto add_catalog_item = [&](const std::string& catalog_name,
                                const std::string& name,
                                bool supported,
                                const std::string& usage,
                                const std::string& verbose)
    {
        const std::string key = catalog_name + "|" + name;
        if (!seen_keys.insert(key).second) return;

        CommandInfo ci;
        ci.id = next_id++;
        ci.catalog = catalog_name;
        ci.name = name;
        ci.implemented = implemented.count(name) > 0;
        ci.supported = supported;
        ci.usage = usage;
        ci.verbose = verbose;
        out.push_back(std::move(ci));
    };

    for (const auto& it : foxref::catalog()) {
        add_catalog_item("FOX", up(it.name), it.supported,
                         to_string_or_empty(it.syntax),
                         to_string_or_empty(it.summary));
    }

    for (const auto& it : dotref::catalog()) {
        add_catalog_item("DOT", up(it.name), it.supported,
                         to_string_or_empty(it.syntax),
                         to_string_or_empty(it.summary));
    }

    for (const auto& it : edref::catalog()) {
        add_catalog_item("ED", up(it.topic), it.supported,
                         to_string_or_empty(it.syntax),
                         to_string_or_empty(it.summary));
    }

    for (const auto& key : implemented) {
        bool seen_any = false;
        if (seen_keys.count("FOX|" + key)) seen_any = true;
        if (seen_keys.count("DOT|" + key)) seen_any = true;
        if (seen_keys.count("ED|"  + key)) seen_any = true;

        if (!seen_any) {
            if (is_expression_function_name(key)) {
                // Expression/function names are reflected through the function
                // catalog, not as unsupported DOT command placeholders.
                continue;
            }

            CommandInfo ci;
            ci.id = next_id++;
            ci.catalog = "DOT";
            ci.name = key;
            ci.implemented = true;
            ci.supported = false;
            ci.usage.clear();
            ci.verbose = generated_pending_summary(key);
            out.push_back(std::move(ci));
        }
    }

    std::sort(out.begin(), out.end(), [](const CommandInfo& a, const CommandInfo& b) {
        if (a.catalog != b.catalog) return a.catalog < b.catalog;
        if (a.implemented != b.implemented) return a.implemented > b.implemented;
        return a.name < b.name;
    });

    return out;
}

std::vector<ArgInfo> collect_args(const std::vector<CommandInfo>& cmds,
                                  const std::vector<std::string>& source_roots)
{
    std::unordered_map<std::string, const foxref::Item*> fox_by_name;
    for (const auto& it : foxref::catalog()) fox_by_name.emplace(up(it.name), &it);

    std::unordered_map<std::string, const dotref::Item*> dot_by_name;
    for (const auto& it : dotref::catalog()) dot_by_name.emplace(up(it.name), &it);

    std::unordered_map<std::string, const edref::Item*> ed_by_name;
    for (const auto& it : edref::catalog()) ed_by_name.emplace(up(it.topic), &it);

    std::unordered_map<std::string, std::set<std::string>> per_cmd;

    for (const auto& c : cmds) {
        std::string key = c.catalog + "|" + c.name;

        if (c.catalog == "FOX") {
            auto it = fox_by_name.find(c.name);
            if (it != fox_by_name.end() && it->second->syntax) {
                for (const auto& sw : switches_from_syntax(it->second->syntax)) {
                    per_cmd[key].insert(sw);
                }
            }
        } else if (c.catalog == "DOT") {
            auto it = dot_by_name.find(c.name);
            if (it != dot_by_name.end() && it->second->syntax) {
                for (const auto& sw : switches_from_syntax(it->second->syntax)) {
                    per_cmd[key].insert(sw);
                }
            }
        } else if (c.catalog == "ED") {
            auto it = ed_by_name.find(c.name);
            if (it != ed_by_name.end() && it->second->syntax) {
                for (const auto& sw : switches_from_syntax(it->second->syntax)) {
                    per_cmd[key].insert(sw);
                }
            }
        }

        // Legacy cmd_args compatibility kept exactly as broad scope rows.
        for (auto k : {"FOR","WHILE","NEXT","RECORD","REST"}) {
            per_cmd[key].insert(k);
        }
    }

    auto mined = scan_sources_for_switches(source_roots);
    for (const auto& c : cmds) {
        auto mit = mined.find(c.name);
        if (mit == mined.end()) continue;
        auto& dst = per_cmd[c.catalog + "|" + c.name];
        dst.insert(mit->second.begin(), mit->second.end());
    }

    std::vector<ArgInfo> out;
    int next_id = 1;

    for (const auto& c : cmds) {
        const std::string key = c.catalog + "|" + c.name;
        const auto it = per_cmd.find(key);
        if (it == per_cmd.end()) continue;

        std::string usage_seed;
        std::string verb_seed;

        if (c.catalog == "FOX") {
            auto fit = fox_by_name.find(c.name);
            if (fit != fox_by_name.end()) {
                usage_seed = fit->second->syntax ? fit->second->syntax : "";
                verb_seed  = fit->second->summary ? fit->second->summary : "";
            }
        } else if (c.catalog == "DOT") {
            auto dit = dot_by_name.find(c.name);
            if (dit != dot_by_name.end()) {
                usage_seed = dit->second->syntax ? dit->second->syntax : "";
                verb_seed  = dit->second->summary ? dit->second->summary : "";
            }
        } else if (c.catalog == "ED") {
            auto eit = ed_by_name.find(c.name);
            if (eit != ed_by_name.end()) {
                usage_seed = eit->second->syntax ? eit->second->syntax : "";
                verb_seed  = eit->second->summary ? eit->second->summary : "";
            }
        }

        for (const auto& sw : it->second) {
            ArgInfo ai;
            ai.id = next_id++;
            ai.catalog = c.catalog;
            ai.command = c.name;
            ai.arg = sw;
            ai.usage = usage_seed;
            ai.verbose = verb_seed;
            out.push_back(std::move(ai));
        }
    }

    std::sort(out.begin(), out.end(), [](const ArgInfo& a, const ArgInfo& b) {
        if (a.catalog != b.catalog) return a.catalog < b.catalog;
        if (a.command != b.command) return a.command < b.command;
        return a.arg < b.arg;
    });

    return out;
}

// === reporting ==============================================================

void print_commands_report(std::ostream& os, const std::vector<CommandInfo>& cmds) {
    os << "Commands (registry U foxref U dotref U edref)\n";
    os << "-----------------------------------------------------------------------\n";
    os << std::left << std::setw(4)  << "ID"
       << " " << std::setw(8)  << "CAT"
       << " " << std::setw(18) << "NAME"
       << " " << std::setw(12) << "IMPLEMENTED"
       << " " << std::setw(10) << "SUPPORTED"
       << " " << "SUMMARY/USAGE\n";

    for (const auto& c : cmds) {
        os << std::left << std::setw(4)  << c.id
           << " " << std::setw(8)  << c.catalog
           << " " << std::setw(18) << c.name
           << " " << std::setw(12) << (c.implemented ? "yes" : "no")
           << " " << std::setw(10) << (c.supported ? "yes" : "no")
           << " " << (c.verbose.empty() ? c.usage : c.verbose)
           << "\n";
    }
}

// === legacy DBF export with memo =============================================

DbfWriteCounts export_dbfs(const std::string& out_dir,
                           const std::vector<std::string>& source_roots)
{
    const auto cmds = collect_commands();
    const auto args = collect_args(cmds, source_roots);

    fs::create_directories(out_dir);

    std::vector<DbfField> f_cmd = {
        fieldN("ID",        10),
        fieldC("CATALOG",   8),
        fieldC("COMMAND",   24),
        fieldC("CMDKEY",    40),
        fieldL("IMPLEMENT"),
        fieldL("SUPPORTED"),
        fieldM("USAGE"),
        fieldM("VERBOSE"),
    };

    std::vector<std::vector<std::string>> rows_cmd;
    rows_cmd.reserve(cmds.size());

    for (const auto& c : cmds) {
        rows_cmd.push_back({
            std::to_string(c.id),
            c.catalog,
            c.name,
            make_cmdkey(c.catalog, c.name),
            c.implemented ? "Y" : "N",
            c.supported ? "Y" : "N",
            c.usage,
            c.verbose
        });
    }

    write_dbf_with_memo((fs::path(out_dir) / "commands.dbf").string(),
                        (fs::path(out_dir) / "commands.dbt").string(),
                        f_cmd, rows_cmd);

    std::vector<DbfField> f_arg = {
        fieldN("ID",        10),
        fieldC("CATALOG",   8),
        fieldC("COMMAND",   24),
        fieldC("CMDKEY",    40),
        fieldC("ARG",       24),
        fieldM("USAGE"),
        fieldM("VERBOSE"),
    };

    std::vector<std::vector<std::string>> rows_arg;
    rows_arg.reserve(args.size());

    for (const auto& a : args) {
        rows_arg.push_back({
            std::to_string(a.id),
            a.catalog,
            a.command,
            make_cmdkey(a.catalog, a.command),
            a.arg,
            a.usage,
            a.verbose
        });
    }

    write_dbf_with_memo((fs::path(out_dir) / "cmd_args.dbf").string(),
                        (fs::path(out_dir) / "cmd_args.dbt").string(),
                        f_arg, rows_arg);

    return { static_cast<int>(rows_cmd.size()), static_cast<int>(rows_arg.size()) };
}

// === legacy SHOW (read existing commands/cmd_args DBFs) ======================

class CmdDbfLoader {
public:
    static bool load(const std::string& dir, std::vector<CommandInfo>& out_cmds, int& out_arg_rows) {
        DbfTable tbl_cmd;
        const std::string dbf = (fs::path(dir) / "commands.dbf").string();
        const std::string dbt = (fs::path(dir) / "commands.dbt").string();
        if (!read_dbf_with_memo(dbf, dbt, tbl_cmd)) return false;

        auto idx_of = [&](const char* name) -> int {
            std::string U = up(name);
            for (size_t i = 0; i < tbl_cmd.fields.size(); ++i) {
                std::string fn(tbl_cmd.fields[i].name,
                               tbl_cmd.fields[i].name + strnlen(tbl_cmd.fields[i].name, 11));
                if (up(fn) == U) return static_cast<int>(i);
            }
            return -1;
        };

        const int ixID   = idx_of("ID");
        const int ixCAT  = idx_of("CATALOG");
        const int ixCMD  = idx_of("COMMAND");
        const int ixKEY  = idx_of("CMDKEY");
        const int ixIMPL = idx_of("IMPLEMENT");
        const int ixSUP  = idx_of("SUPPORTED");
        const int ixUSE  = idx_of("USAGE");
        const int ixVER  = idx_of("VERBOSE");
        (void)ixKEY;

        if (ixID < 0 || ixCAT < 0 || ixCMD < 0 || ixIMPL < 0 || ixSUP < 0 || ixUSE < 0 || ixVER < 0) {
            return false;
        }

        out_cmds.clear();
        out_cmds.reserve(tbl_cmd.rows.size());

        for (const auto& r : tbl_cmd.rows) {
            CommandInfo ci;
            try { ci.id = std::stoi(r[ixID]); }
            catch (...) { ci.id = 0; }

            ci.catalog = up(r[ixCAT]);
            ci.name = up(r[ixCMD]);

            auto impl = r[ixIMPL];
            ci.implemented = (!impl.empty() && (impl[0] == 'T' || impl[0] == 't' || impl[0] == 'Y' || impl == "1"));

            auto supp = r[ixSUP];
            ci.supported = (!supp.empty() && (supp[0] == 'T' || supp[0] == 't' || supp[0] == 'Y' || supp == "1"));

            ci.usage   = r[ixUSE];
            ci.verbose = r[ixVER];
            out_cmds.push_back(std::move(ci));
        }

        DbfTable tbl_args;
        const std::string adb = (fs::path(dir) / "cmd_args.dbf").string();
        const std::string adt = (fs::path(dir) / "cmd_args.dbt").string();
        out_arg_rows = read_dbf_with_memo(adb, adt, tbl_args) ? static_cast<int>(tbl_args.rows.size()) : 0;

        std::sort(out_cmds.begin(), out_cmds.end(), [](const CommandInfo& a, const CommandInfo& b) {
            if (a.catalog != b.catalog) return a.catalog < b.catalog;
            if (a.implemented != b.implemented) return a.implemented > b.implemented;
            return a.name < b.name;
        });

        return true;
    }
};

// === current HELP DATA report ================================================

static bool load_help_line_table(const std::string& dir, DbfTable& out) {
    const std::string dbf = (fs::path(dir) / "help_line.dbf").string();
    return read_dbf_with_memo(dbf, std::string(), out);
}

static std::string topic_suffix(const std::string& topickey);
static int catalog_rank(const std::string& key);
static int kind_rank(const std::string& kind_raw);
static int source_rank(const std::string& source_raw);

static void print_count_map(const std::string& title, const std::unordered_map<std::string, int>& counts) {
    std::vector<std::pair<std::string, int>> rows(counts.begin(), counts.end());
    std::sort(rows.begin(), rows.end(), [](const auto& a, const auto& b) {
        return a.first < b.first;
    });

    out() << "\n" << title << ":\n";
    for (const auto& kv : rows) {
        out() << "  " << std::left << std::setw(18) << kv.first << " " << kv.second << "\n";
    }
}

static std::vector<std::string> sorted_topic_keys(const std::set<std::string>& topics) {
    std::vector<std::string> out(topics.begin(), topics.end());
    std::sort(out.begin(), out.end(), [](const std::string& a, const std::string& b) {
        const int ca = catalog_rank(a);
        const int cb = catalog_rank(b);
        if (ca != cb) return ca < cb;
        const std::string as = topic_suffix(a);
        const std::string bs = topic_suffix(b);
        if (as != bs) return as < bs;
        return a < b;
    });
    return out;
}

static void print_current_help_topics(const std::string& dir) {
    DbfTable tbl;
    if (!load_help_line_table(dir, tbl)) {
        cli::cmdout::print_prefixed_message(
            "CMDHELP",
            dottalk::helpdata::MessageId::CmdHelpCurrentReadFailed,
            {{"dir", dir}});
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpCurrentExpectedFile);
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpBuildTip);
        return;
    }

    const int ix_topic_key = dbf_field_index(tbl, "TOPICKEY");
    if (ix_topic_key < 0) {
        cli::cmdout::print_prefixed_message(
            "CMDHELP",
            dottalk::helpdata::MessageId::CmdHelpCurrentMissingColumns);
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpCurrentNeedColumns);
        return;
    }

    std::set<std::string> topics;
    for (const auto& r : tbl.rows) {
        const std::string topic = dbf_cell(r, ix_topic_key);
        if (!topic.empty()) topics.insert(topic);
    }

    out() << "CMDHELP Topics (current HELP DATA)\n"
          << "  directory : " << dir << "\n"
          << "  topics    : " << topics.size() << "\n\n";

    for (const auto& topic : sorted_topic_keys(topics)) {
        out() << "  " << topic << "\n";
    }
}

enum class CurrentHelpGroupMode {
    Kind,
    Source
};

static void print_current_help_grouped(const std::string& dir, CurrentHelpGroupMode mode) {
    DbfTable tbl;
    if (!load_help_line_table(dir, tbl)) {
        cli::cmdout::print_prefixed_message(
            "CMDHELP",
            dottalk::helpdata::MessageId::CmdHelpCurrentReadFailed,
            {{"dir", dir}});
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpCurrentExpectedFile);
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpBuildTip);
        return;
    }

    const int ix_topic_key = dbf_field_index(tbl, "TOPICKEY");
    const int ix_group = dbf_field_index(tbl, mode == CurrentHelpGroupMode::Kind ? "KIND" : "SOURCE");
    if (ix_topic_key < 0 || ix_group < 0) {
        cli::cmdout::print_prefixed_message(
            "CMDHELP",
            dottalk::helpdata::MessageId::CmdHelpCurrentMissingColumns);
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpCurrentNeedColumns);
        return;
    }

    struct Bucket {
        int line_count{0};
        std::set<std::string> topics;
    };
    std::unordered_map<std::string, Bucket> grouped;

    for (const auto& r : tbl.rows) {
        const std::string topic = dbf_cell(r, ix_topic_key);
        const std::string group = dbf_cell(r, ix_group);
        auto& bucket = grouped[group.empty() ? "(blank)" : group];
        ++bucket.line_count;
        if (!topic.empty()) bucket.topics.insert(topic);
    }

    std::vector<std::pair<std::string, Bucket>> rows(grouped.begin(), grouped.end());
    std::sort(rows.begin(), rows.end(),
              [&](const auto& a, const auto& b) {
                  const int ra = (mode == CurrentHelpGroupMode::Kind)
                      ? kind_rank(a.first)
                      : source_rank(a.first);
                  const int rb = (mode == CurrentHelpGroupMode::Kind)
                      ? kind_rank(b.first)
                      : source_rank(b.first);
                  if (ra != rb) return ra < rb;
                  return a.first < b.first;
              });

    out() << "CMDHELP "
          << (mode == CurrentHelpGroupMode::Kind ? "KIND" : "SOURCE")
          << " view (current HELP DATA)\n"
          << "  directory : " << dir << "\n"
          << "  buckets   : " << rows.size() << "\n\n";

    for (const auto& row : rows) {
        out() << row.first
              << "  [lines=" << row.second.line_count
              << ", topics=" << row.second.topics.size() << "]\n";
        for (const auto& topic : sorted_topic_keys(row.second.topics)) {
            out() << "  - " << topic << "\n";
        }
        out() << "\n";
    }
}

static void print_current_help_report(const std::string& dir) {
    DbfTable tbl;
    if (!load_help_line_table(dir, tbl)) {
        cli::cmdout::print_prefixed_message(
            "CMDHELP",
            dottalk::helpdata::MessageId::CmdHelpCurrentReadFailed,
            {{"dir", dir}});
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpCurrentExpectedFile);
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpBuildTip);
        return;
    }

    const int ix_topic_key = dbf_field_index(tbl, "TOPICKEY");
    const int ix_kind      = dbf_field_index(tbl, "KIND");
    const int ix_source    = dbf_field_index(tbl, "SOURCE");
    const int ix_confid    = dbf_field_index(tbl, "CONFID");
    const int ix_role      = dbf_field_index(tbl, "ROLE");
    const int ix_text      = dbf_field_index(tbl, "TEXT");

    if (ix_topic_key < 0 || ix_kind < 0 || ix_source < 0 || ix_text < 0) {
        cli::cmdout::print_prefixed_message(
            "CMDHELP",
            dottalk::helpdata::MessageId::CmdHelpCurrentMissingColumns);
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpCurrentNeedColumns);
        return;
    }

    std::set<std::string> topics;
    std::unordered_map<std::string, int> by_kind;
    std::unordered_map<std::string, int> by_source;

    for (const auto& r : tbl.rows) {
        const std::string topic = dbf_cell(r, ix_topic_key);
        const std::string kind = dbf_cell(r, ix_kind);
        const std::string source = dbf_cell(r, ix_source);

        if (!topic.empty()) topics.insert(topic);
        by_kind[kind.empty() ? "(blank)" : kind]++;
        by_source[source.empty() ? "(blank)" : source]++;
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpCurrentReportTitle);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::CmdHelpCurrentDirectoryLine,
        {{"dir", dir}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::CmdHelpCurrentLineRowsLine,
        {{"count", std::to_string(tbl.rows.size())}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::CmdHelpCurrentTopicsLine,
        {{"count", std::to_string(topics.size())}});

    print_count_map(cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpByKindTitle), by_kind);
    print_count_map(cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpBySourceTitle), by_source);

    out() << "\n";
    cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpPreviewRowsTitle);
    out() << std::left
          << std::setw(20) << cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpPreviewTopicKeyHeader)
          << std::setw(14) << cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpPreviewKindHeader)
          << std::setw(16) << cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpPreviewSourceHeader)
          << std::setw(14) << cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpPreviewConfidHeader)
          << std::setw(10) << cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpPreviewRoleHeader)
          << cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpPreviewTextHeader) << "\n";
    out() << cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpPreviewDivider) << "\n";

    int shown = 0;
    for (const auto& r : tbl.rows) {
        if (shown >= 24) break;

        std::string text = dbf_cell(r, ix_text);
        for (char& ch : text) {
            if (ch == '\n' || ch == '\r' || ch == '\t') ch = ' ';
        }
        if (text.size() > 100) text.resize(100);

        out() << std::left
              << std::setw(20) << dbf_cell(r, ix_topic_key).substr(0, 19)
              << std::setw(14) << dbf_cell(r, ix_kind).substr(0, 13)
              << std::setw(16) << dbf_cell(r, ix_source).substr(0, 15)
              << std::setw(14) << dbf_cell(r, ix_confid).substr(0, 13)
              << std::setw(10) << dbf_cell(r, ix_role).substr(0, 9)
              << text << "\n";
        ++shown;
    }
}


// === current topic rendering =================================================

struct HelpLineView {
    std::string topic_key;
    std::string topic;
    std::string kind;
    std::string source;
    std::string confid;
    std::string role;
    int line_no{0};
    int part_no{0};
    std::string text;
};

struct HelpTopicLocaleView {
    std::string topic_key;
    std::string locale_id;
    std::string source_title;
    std::string localized_title;
    std::string transl_status;
    std::string review_status;
};

struct HelpLineLocaleView {
    std::string topic_key;
    std::string kind;
    std::string role;
    int line_order{0};
    std::string locale_id;
    std::string localized_label;
    std::string source_text;
    std::string localized_text;
    std::string transl_status;
    std::string review_status;
};

static std::string make_line_locale_group_key(const std::string& topic_key,
                                              const std::string& kind,
                                              const std::string& role) {
    return up(topic_key) + "|" + up(kind) + "|" + up(role);
}

static int safe_int_cell(const std::vector<std::string>& row, int ix) {
    try {
        const std::string s = dbf_cell(row, ix);
        if (s.empty()) return 0;
        return std::stoi(s);
    } catch (...) {
        return 0;
    }
}

static std::string topic_suffix(const std::string& topickey) {
    const auto pos = topickey.find('|');
    if (pos == std::string::npos) return up(topickey);
    return up(topickey.substr(pos + 1));
}

static std::string topic_catalog(const std::string& topickey) {
    const auto pos = topickey.find('|');
    if (pos == std::string::npos) return {};
    return up(topickey.substr(0, pos));
}

static int catalog_rank(const std::string& key) {
    const std::string c = topic_catalog(key);
    if (c == "DOT") return 0;
    if (c == "FOX") return 1;
    if (c == "ED")  return 2;
    if (c == "FUNC") return 3;
    if (c == "MSG") return 4;
    return 9;
}

static int kind_rank(const std::string& kind_raw) {
    const std::string k = up(kind_raw);
    if (k == "SUMMARY")     return 10;
    if (k == "USAGE")       return 20;
    if (k == "SYNTAX")      return 30;
    if (k == "ARGUMENT")    return 40;
    if (k == "EXAMPLE")     return 50;
    if (k == "NOTE")        return 60;
    if (k == "WARNING")     return 70;
    if (k == "ERROR")       return 80;
    if (k == "RELATED")     return 90;
    if (k == "DEPRECATION") return 100;
    if (k == "HINT")        return 110;
    if (k == "STATUS")      return 900;
    if (k == "SOURCE_FACT") return 910;
    return 500;
}

static int source_rank(const std::string& source_raw) {
    const std::string s = up(source_raw);
    if (s == "USAGE_CONTRACT") return 0;
    if (s == "CURATED_DOC")    return 1;
    if (s == "DOTREF")         return 2;
    if (s == "FOXREF")         return 3;
    if (s == "EDREF")          return 4;
    if (s == "REGISTRY")       return 5;
    if (s == "SHARED_MSG")     return 6;
    if (s == "SOURCE_MINER")   return 9;
    return 7;
}

enum class TopicRenderMode {
    Full,
    Usage
};

static std::vector<std::string> resolve_topic_keys_from_lines(const std::vector<HelpLineView>& lines,
                                                              const std::string& query_raw);
static void cmdhelp_usage();

static bool render_kind_default(const std::string& kind_raw) {
    const std::string k = up(kind_raw);
    return k == "SUMMARY" ||
           k == "USAGE" ||
           k == "SYNTAX" ||
           k == "EXAMPLE" ||
           k == "NOTE" ||
           k == "WARNING" ||
           k == "ERROR" ||
           k == "RELATED" ||
           k == "DEPRECATION" ||
           k == "HINT";
}

static bool render_kind_usage(const std::string& kind_raw) {
    const std::string k = up(kind_raw);
    return k == "USAGE" ||
           k == "SYNTAX" ||
           k == "EXAMPLE";
}

static bool starts_with_ci(const std::string& text, const std::string& prefix) {
    if (prefix.size() > text.size()) return false;
    return up(text.substr(0, prefix.size())) == up(prefix);
}

static std::string trimmed_copy_local(std::string s) {
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static bool contains_ci(const std::string& text, const std::string& needle) {
    return up(text).find(up(needle)) != std::string::npos;
}

static bool is_source_evidence_text(const std::string& raw) {
    const std::string s = trimmed_copy_local(raw);
    const std::string u = up(s);

    if (s.empty()) return true;

    // Source/evidence rows are useful for CMDHELPCHK and future DETAILS mode,
    // but they should not be user-facing topic help.
    if (contains_ci(s, " pattern=")) return true;
    if (contains_ci(s, "pattern=")) return true;
    if (contains_ci(s, " version=")) return true;
    if (contains_ci(s, " function=")) return true;
    if (contains_ci(s, "Mined from command-local usage/help output")) return true;

    // Windows / POSIX source path evidence, e.g. d:/code/... or src/cli/...
    if (contains_ci(s, ":/code/")) return true;
    if (contains_ci(s, ":\\code\\")) return true;
    if (starts_with_ci(s, "src/") || starts_with_ci(s, "./src/")) return true;
    if (starts_with_ci(s, "d:/") || starts_with_ci(s, "c:/")) return true;

    // Contract metadata should not leak into rendered USAGE.
    if (starts_with_ci(s, "owner=")) return true;
    if (starts_with_ci(s, "command=")) return true;
    if (starts_with_ci(s, "category=")) return true;
    if (starts_with_ci(s, "status=")) return true;
    if (starts_with_ci(s, "noargs=")) return true;
    if (starts_with_ci(s, "usage-access=")) return true;
    if (starts_with_ci(s, "source=")) return true;
    if (starts_with_ci(s, "confidence=")) return true;

    if (u == "COMMAND-OWNED @DOTTALK.USAGE V1 SUMMARY.") return true;

// @dottalk.locale-preview-contract v1 PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT
// CMDHELP <topic> PREVIEW LOCALE <locale> is the explicit-only locale preview surface.
// Default CMDHELP behavior remains unchanged until a separately authorized runtime implementation patch.
// Locale rows with DRAFT_PLACEHOLDER or NEEDS_REVIEW fall back to source/default text.


    return false;
}

static bool usage_or_syntax_line_looks_runnable(const HelpLineView& h) {
    std::string s = trimmed_copy_local(h.text);
    if (s.empty()) return false;

    const std::string cmd = topic_suffix(h.topic_key);
    const std::string cmdU = up(cmd);
    const std::string sU = up(s);

    // Evidence/metadata has already been filtered separately, but keep this
    // guard local because usage/syntax sections are the most visible.
    if (is_source_evidence_text(s)) return false;

    // Suppress labels/descriptions that were mined too broadly.
    if (sU == cmdU + " SYNTAX") return false;
    if (sU == cmdU + " USAGE") return false;
    if (sU == "SYNTAX" || sU == "USAGE" || sU == "SUBCOMMANDS:" || sU == "EXAMPLES:") return false;

    // Preferred form: full topic suffix starts the row.
    // Examples: "SET ORDER TO <tag>", "REL LIST [ALL]".
    if (starts_with_ci(s, cmd)) {
        return true;
    }

    // Enforced convention: compact SET-family verbs such as SETORDER are
    // aliases of canonical spaced SET topics such as SET ORDER.  Contract
    // harvesting stores the canonical topic while preserving compact usage
    // forms, so allow those rows to render under the canonical topic.
    if (starts_with_ci(cmd, "SET ")) {
        std::string compact = cmd;
        compact.erase(std::remove_if(compact.begin(), compact.end(),
                                     [](unsigned char ch) { return std::isspace(ch) != 0; }),
                      compact.end());
        if (!compact.empty() && starts_with_ci(s, compact)) {
            return true;
        }
    }

    // Fallback for compound topics and compatibility aliases:
    // use the first word of the topic.  This lets DOT|REL_ENUM show REL...
    // but still blocks arbitrary note lines like "asymmetric relation".
    const auto words = split_words(cmd);
    if (!words.empty() && starts_with_ci(s, words.front() + " ")) {
        return true;
    }

    return false;
}

static bool should_render_topic_line(const HelpLineView& h, TopicRenderMode mode) {
    const std::string k = up(h.kind);
    const std::string source = up(h.source);

    if (is_source_evidence_text(h.text)) {
        return false;
    }

    // Source facts, registry status, and mined argument candidates are
    // validator material, not ordinary topic help.
    if (k == "SOURCE_FACT" || k == "STATUS" || k == "ARGUMENT") {
        return false;
    }

    if (mode == TopicRenderMode::Usage) {
        if (!render_kind_usage(k)) return false;
    } else {
        if (!render_kind_default(k)) return false;
    }

    if (k == "USAGE" || k == "SYNTAX") {
        if (!usage_or_syntax_line_looks_runnable(h)) {
            return false;
        }
    }

    // In topic rendering, SOURCE_MINER is allowed only when it found a
    // recognizable runnable form.  Broader source-mined notes/evidence stay
    // available to CMDHELPCHK instead of polluting user help.
    if (source == "SOURCE_MINER" && !(k == "USAGE" || k == "SYNTAX" || k == "EXAMPLE")) {
        return false;
    }

    return true;
}


static std::string join_words_range(const std::vector<std::string>& words, size_t first, size_t last_exclusive) {
    std::string out;
    for (size_t i = first; i < last_exclusive && i < words.size(); ++i) {
        if (!out.empty()) out += ' ';
        out += words[i];
    }
    return out;
}

static std::vector<HelpLineView> load_current_help_lines(const std::string& dir) {
    DbfTable tbl;
    if (!load_help_line_table(dir, tbl)) {
        return {};
    }

    const int ix_topic_key = dbf_field_index(tbl, "TOPICKEY");
    const int ix_topic     = dbf_field_index(tbl, "TOPIC");
    const int ix_kind      = dbf_field_index(tbl, "KIND");
    const int ix_source    = dbf_field_index(tbl, "SOURCE");
    const int ix_confid    = dbf_field_index(tbl, "CONFID");
    const int ix_role      = dbf_field_index(tbl, "ROLE");
    const int ix_line_no   = dbf_field_index(tbl, "LINE_NO");
    const int ix_part_no   = dbf_field_index(tbl, "PART_NO");
    const int ix_text      = dbf_field_index(tbl, "TEXT");

    if (ix_topic_key < 0 || ix_kind < 0 || ix_source < 0 || ix_text < 0) {
        return {};
    }

    std::vector<HelpLineView> lines;
    lines.reserve(tbl.rows.size());

    for (const auto& r : tbl.rows) {
        HelpLineView h;
        h.topic_key = dbf_cell(r, ix_topic_key);
        h.topic     = dbf_cell(r, ix_topic);
        h.kind      = dbf_cell(r, ix_kind);
        h.source    = dbf_cell(r, ix_source);
        h.confid    = dbf_cell(r, ix_confid);
        h.role      = dbf_cell(r, ix_role);
        h.line_no   = safe_int_cell(r, ix_line_no);
        h.part_no   = safe_int_cell(r, ix_part_no);
        h.text      = dbf_cell(r, ix_text);

        if (!h.topic_key.empty() && !h.text.empty()) {
            lines.push_back(std::move(h));
        }
    }

    return lines;
}

static bool area_has_memo_fields(const xbase::DbArea& area) {
    for (const auto& field : area.fields()) {
        if (field.type == 'M' || field.type == 'm') {
            return true;
        }
    }
    return false;
}

static std::string normalize_help_locale_text(std::string value) {
    const auto nul = value.find('\0');
    if (nul != std::string::npos) {
        value.erase(nul);
    }
    return trimmed_copy_local(std::move(value));
}

static std::optional<std::string> resolve_area_memo_text(xbase::DbArea& area, const std::string& raw_token) {
    auto* backend = cli_memo::memo_backend_for(area);
    if (backend == nullptr) {
        return std::nullopt;
    }

    dottalk::memo::MemoRef ref{};
    if (!dottalk::memo::parse_memo_ref(trimmed_copy_local(raw_token), ref)) {
        return std::nullopt;
    }

    auto result = backend->get_text(ref);
    if (!result.ok) {
        return std::nullopt;
    }

    return result.text;
}

static bool open_help_locale_area(const std::string& dir,
                                  const std::string& dbf_name,
                                  xbase::DbArea& area) {
    const fs::path dbf = fs::path(dir) / dbf_name;

    try {
        area.open(dbf.string());
    } catch (...) {
        return false;
    }

    std::string memo_err;
    if (!cli_memo::memo_auto_on_use(area, dbf.string(), area_has_memo_fields(area), memo_err)) {
        cli_memo::memo_auto_on_close(area);
        area.close();
        return false;
    }

    return true;
}

static bool is_locale_preview_blocked(const std::string& transl_status_raw,
                                      const std::string& review_status_raw) {
    const std::string transl = up(trimmed_copy_local(transl_status_raw));
    const std::string review = up(trimmed_copy_local(review_status_raw));

    if (transl.find("DRAFT") != std::string::npos) return true;
    if (transl.find("NEEDS_REVIEW") != std::string::npos) return true;
    if (transl == "MISSING") return true;
    if (review.find("NEEDS_REVIEW") != std::string::npos) return true;
    if (review.find("REJECT") != std::string::npos) return true;
    return false;
}

static std::vector<HelpTopicLocaleView> load_help_topic_locale_rows(const std::string& dir) {
    xbase::DbArea area;
    if (!open_help_locale_area(dir, "HELP_TOPIC_LOCALE.dbf", area)) {
        return {};
    }

    std::vector<HelpTopicLocaleView> rows;
    rows.reserve(static_cast<std::size_t>(std::max<std::int32_t>(area.recCount(), 0)));

    for (int32_t recno = 1; recno <= area.recCount(); ++recno) {
        if (!area.gotoRec(recno) || !area.readCurrent()) {
            continue;
        }

        HelpTopicLocaleView row;
        row.topic_key = normalize_help_locale_text(xfg::getFieldForDisplay(area, "TOPICKEY"));
        row.locale_id = normalize_help_locale_text(xfg::getFieldForDisplay(area, "LOCALE_ID"));
        row.source_title = normalize_help_locale_text(xfg::getFieldForDisplay(area, "SOURCE_TITLE"));
        row.localized_title = normalize_help_locale_text(xfg::getFieldForDisplay(area, "LOCALIZED_TITLE"));
        row.transl_status = normalize_help_locale_text(xfg::getFieldForDisplay(area, "TRANSL_STATUS"));
        row.review_status = normalize_help_locale_text(xfg::getFieldForDisplay(area, "REVIEW_STATUS"));
        if (!row.topic_key.empty() && !row.locale_id.empty()) {
            rows.push_back(std::move(row));
        }
    }

    cli_memo::memo_auto_on_close(area);
    area.close();
    return rows;
}

static std::vector<HelpLineLocaleView> load_help_line_locale_rows(const std::string& dir) {
    xbase::DbArea area;
    if (!open_help_locale_area(dir, "HELP_LINE_LOCALE.dbf", area)) {
        return {};
    }

    std::vector<HelpLineLocaleView> rows;
    rows.reserve(static_cast<std::size_t>(std::max<std::int32_t>(area.recCount(), 0)));

    for (int32_t recno = 1; recno <= area.recCount(); ++recno) {
        if (!area.gotoRec(recno) || !area.readCurrent()) {
            continue;
        }

        HelpLineLocaleView row;
        row.topic_key = normalize_help_locale_text(xfg::getFieldForDisplay(area, "TOPICKEY"));
        row.kind = normalize_help_locale_text(xfg::getFieldForDisplay(area, "KIND"));
        row.role = normalize_help_locale_text(xfg::getFieldForDisplay(area, "ROLE"));
        row.line_order = static_cast<int>(xfg::tryGetFieldAsInt64(area, "LINE_ORDER").value_or(0));
        row.locale_id = normalize_help_locale_text(xfg::getFieldForDisplay(area, "LOCALE_ID"));
        row.localized_label = normalize_help_locale_text(xfg::getFieldForDisplay(area, "LOCALIZED_LABEL"));
        row.source_text = normalize_help_locale_text(
            resolve_area_memo_text(area, xfg::getFieldRawString(area, "SOURCE_TEXT")).value_or(std::string{}));
        row.localized_text = normalize_help_locale_text(
            resolve_area_memo_text(area, xfg::getFieldRawString(area, "LOCALIZED_TEXT")).value_or(std::string{}));
        row.transl_status = normalize_help_locale_text(xfg::getFieldForDisplay(area, "TRANSL_STATUS"));
        row.review_status = normalize_help_locale_text(xfg::getFieldForDisplay(area, "REVIEW_STATUS"));
        if (!row.topic_key.empty() && !row.locale_id.empty()) {
            rows.push_back(std::move(row));
        }
    }

    cli_memo::memo_auto_on_close(area);
    area.close();
    return rows;
}

struct LocalePreviewRequest {
    bool requested{false};
    std::string query;
    std::string locale;
};

static LocalePreviewRequest parse_locale_preview_request(const std::vector<std::string>& words) {
    LocalePreviewRequest req{};
    if (words.size() < 3) {
        return req;
    }

    const std::string last = up(words.back());
    const std::string prev = up(words[words.size() - 2]);

    if (prev == "LOCALE") {
        if (words.size() >= 4 && up(words[words.size() - 3]) == "PREVIEW") {
            req.requested = true;
            req.query = join_words_range(words, 0, words.size() - 3);
            req.locale = words.back();
            return req;
        }

        req.requested = true;
        req.query = join_words_range(words, 0, words.size() - 2);
        req.locale = words.back();
        return req;
    }

    (void)last;
    return req;
}

static void render_current_topic_help_locale_preview(const std::string& dir,
                                                     const std::string& query_raw,
                                                     const std::string& locale_raw,
                                                     TopicRenderMode mode) {
    std::string query = trimmed_copy_local(query_raw);
    std::string locale = trimmed_copy_local(locale_raw);

    if (query.empty() || locale.empty()) {
        cmdhelp_usage();
        return;
    }

    const auto lines = load_current_help_lines(dir);
    if (lines.empty()) {
        cli::cmdout::print_prefixed_message(
            "CMDHELP",
            dottalk::helpdata::MessageId::CmdHelpCurrentLoadFailed,
            {{"dir", dir}});
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpBuildTip);
        return;
    }

    const auto keys = resolve_topic_keys_from_lines(lines, query);
    if (keys.empty()) {
        cli::cmdout::print_prefixed_message(
            "CMDHELP",
            dottalk::helpdata::MessageId::CmdHelpNoTopicMatched,
            {{"topic", query}});
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpSummaryTip);
        return;
    }

    const auto topic_locale_rows = load_help_topic_locale_rows(dir);
    const auto line_locale_rows = load_help_line_locale_rows(dir);

    std::unordered_map<std::string, HelpTopicLocaleView> topic_locale_by_key;
    for (const auto& row : topic_locale_rows) {
        if (up(row.locale_id) != up(locale)) continue;
        const std::string key = up(row.topic_key);
        if (!topic_locale_by_key.count(key)) {
            topic_locale_by_key.emplace(key, row);
        }
    }

    std::unordered_map<std::string, std::vector<HelpLineLocaleView>> line_locale_groups;
    for (const auto& row : line_locale_rows) {
        if (up(row.locale_id) != up(locale)) continue;
        line_locale_groups[make_line_locale_group_key(row.topic_key, row.kind, row.role)].push_back(row);
    }

    for (auto& it : line_locale_groups) {
        auto& rows = it.second;
        std::sort(rows.begin(), rows.end(), [](const HelpLineLocaleView& a, const HelpLineLocaleView& b) {
            if (a.line_order != b.line_order) return a.line_order < b.line_order;
            return a.localized_text < b.localized_text;
        });
    }

    std::unordered_set<std::string> keyset;
    for (const auto& k : keys) keyset.insert(up(k));

    std::vector<HelpLineView> picked;
    for (const auto& h : lines) {
        if (!keyset.count(up(h.topic_key))) continue;
        if (!should_render_topic_line(h, mode)) continue;
        picked.push_back(h);
    }

    std::sort(picked.begin(), picked.end(), [](const HelpLineView& a, const HelpLineView& b) {
        const int ca = catalog_rank(a.topic_key);
        const int cb = catalog_rank(b.topic_key);
        if (ca != cb) return ca < cb;

        const std::string ak = up(a.topic_key);
        const std::string bk = up(b.topic_key);
        if (ak != bk) return ak < bk;

        const int ka = kind_rank(a.kind);
        const int kb = kind_rank(b.kind);
        if (ka != kb) return ka < kb;

        const int sa = source_rank(a.source);
        const int sb = source_rank(b.source);
        if (sa != sb) return sa < sb;

        if (a.line_no != b.line_no) return a.line_no < b.line_no;
        if (a.part_no != b.part_no) return a.part_no < b.part_no;
        return a.text < b.text;
    });

    out() << "CMDHELP LOCALE PREVIEW - not default command behavior\n";
    out() << "  query            : " << up(query) << "\n";
    out() << "  requested locale : " << locale << "\n";
    out() << "  default behavior : CMDHELP <topic> remains canonical/source HELP\n";

    if (keys.size() > 1) {
        out() << "  matched topics   :";
        for (const auto& k : keys) out() << " " << k;
        out() << "\n";
    }

    std::string last_key;
    std::string last_kind;
    std::set<std::string> seen_line;
    std::unordered_map<std::string, size_t> line_locale_group_pos;
    int localized_lines = 0;
    int fallback_lines = 0;

    for (const auto& h : picked) {
        const std::string keyU = up(h.topic_key);
        const std::string kindU = up(h.kind);
        const std::string dedupe = keyU + "|" + kindU + "|" + up(h.text);
        if (!seen_line.insert(dedupe).second) {
            continue;
        }

        const std::string locale_group_key = make_line_locale_group_key(h.topic_key, h.kind, h.role);
        const HelpLineLocaleView* locale_row = nullptr;
        bool locale_row_blocked = false;

        const auto itGroup = line_locale_groups.find(locale_group_key);
        if (itGroup != line_locale_groups.end() && !itGroup->second.empty()) {
            auto& pos = line_locale_group_pos[locale_group_key];
            if (pos < itGroup->second.size()) {
                locale_row = &itGroup->second[pos++];
            } else {
                locale_row = &itGroup->second.back();
            }
            locale_row_blocked = is_locale_preview_blocked(locale_row->transl_status, locale_row->review_status);
        }

        if (keyU != last_key) {
            last_key = keyU;
            last_kind.clear();

            out() << "\n" << h.topic_key << " [" << locale << "]\n";
            out() << std::string(h.topic_key.size() + locale.size() + 3, '=') << "\n";

            const auto itTopicLoc = topic_locale_by_key.find(keyU);
            if (itTopicLoc != topic_locale_by_key.end()) {
                const auto& row = itTopicLoc->second;
                const bool blocked = is_locale_preview_blocked(row.transl_status, row.review_status);
                const std::string preview_title =
                    (!blocked && !trimmed_copy_local(row.localized_title).empty())
                        ? row.localized_title
                        : (!trimmed_copy_local(row.source_title).empty() ? row.source_title : topic_suffix(h.topic_key));

                out() << "title  : " << preview_title << "\n";
                out() << "status : transl=" << row.transl_status
                      << " review=" << row.review_status
                      << " decision=" << (blocked ? "fallback" : "localized-preview") << "\n";
            } else {
                out() << "title  : " << topic_suffix(h.topic_key) << "\n";
                out() << "status : no locale topic row; fallback\n";
            }
        }

        if (kindU != last_kind) {
            last_kind = kindU;
            const std::string kind_label =
                (locale_row && !locale_row_blocked && !trimmed_copy_local(locale_row->localized_label).empty())
                    ? locale_row->localized_label
                    : kindU;
            out() << "\n" << kind_label << "\n";
            out() << std::string(kind_label.size(), '-') << "\n";
        }

        std::string render_text = h.text;
        if (locale_row != nullptr) {
            if (!locale_row_blocked && !trimmed_copy_local(locale_row->localized_text).empty()) {
                render_text = locale_row->localized_text;
                ++localized_lines;
            } else {
                ++fallback_lines;
            }
        } else {
            ++fallback_lines;
        }

        out() << render_text << "\n";
    }

    if (picked.empty()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpTopicNoRenderableSections);
    }

    out() << "\npreview summary\n";
    out() << "---------------\n";
    out() << "localized lines : " << localized_lines << "\n";
    out() << "fallback lines  : " << fallback_lines << "\n";
    out() << "normal CMDHELP output unchanged\n";
}

static std::vector<std::string> sorted_limited_topic_keys(std::set<std::string> keys) {
    std::vector<std::string> out(keys.begin(), keys.end());
    std::sort(out.begin(), out.end(), [](const std::string& a, const std::string& b) {
        const int ca = catalog_rank(a);
        const int cb = catalog_rank(b);
        if (ca != cb) return ca < cb;
        return up(a) < up(b);
    });

    if (out.size() > 8) {
        out.resize(8);
    }
    return out;
}

static std::vector<std::string> resolve_topic_keys_from_lines(const std::vector<HelpLineView>& lines,
                                                              const std::string& query_raw) {
    const std::string q = up(query_raw);

    // Enforced Phase 4b convention: compact SET-family queries are aliases into
    // canonical spaced SET * topics.  Prefer the canonical topic if it exists;
    // fall back to legacy compact topics only if the current HELP DATA lacks the
    // canonical rows.
    if (q.find('|') == std::string::npos) {
        const std::string set_canon = canonical_set_family_query(q);
        if (!set_canon.empty()) {
            std::set<std::string> canonical_exact;
            for (const auto& h : lines) {
                const std::string topicU = up(h.topic);
                const std::string suffU = topic_suffix(h.topic_key);
                if (suffU == set_canon || topicU == set_canon) {
                    canonical_exact.insert(h.topic_key);
                }
            }
            if (!canonical_exact.empty()) {
                return sorted_limited_topic_keys(std::move(canonical_exact));
            }
        }
    }

    std::set<std::string> exact;
    std::set<std::string> suffix;

    for (const auto& h : lines) {
        const std::string keyU = up(h.topic_key);
        const std::string topicU = up(h.topic);
        const std::string suffU = topic_suffix(h.topic_key);

        if (q.find('|') != std::string::npos) {
            if (keyU == q) exact.insert(h.topic_key);
        } else {
            if (suffU == q || topicU == q) exact.insert(h.topic_key);
            else if ((up(h.kind) == "ALIAS" || up(h.kind) == "VARIANT") && up(h.text) == q) exact.insert(h.topic_key);
            else if (suffU.find(q) != std::string::npos || topicU.find(q) != std::string::npos) suffix.insert(h.topic_key);
        }
    }

    if (!exact.empty()) {
        return sorted_limited_topic_keys(std::move(exact));
    }
    return sorted_limited_topic_keys(std::move(suffix));
}

static void render_current_topic_help(const std::string& dir,
                                      const std::string& query_raw,
                                      TopicRenderMode mode) {
    std::string query = query_raw;
    while (!query.empty() && std::isspace(static_cast<unsigned char>(query.front()))) query.erase(query.begin());
    while (!query.empty() && std::isspace(static_cast<unsigned char>(query.back()))) query.pop_back();

    if (query.empty()) {
        print_current_help_report(dir);
        return;
    }

    const auto lines = load_current_help_lines(dir);
    if (lines.empty()) {
        cli::cmdout::print_prefixed_message(
            "CMDHELP",
            dottalk::helpdata::MessageId::CmdHelpCurrentLoadFailed,
            {{"dir", dir}});
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpBuildTip);
        return;
    }

    const auto keys = resolve_topic_keys_from_lines(lines, query);
    if (keys.empty()) {
        cli::cmdout::print_prefixed_message(
            "CMDHELP",
            dottalk::helpdata::MessageId::CmdHelpNoTopicMatched,
            {{"topic", query}});
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpSummaryTip);
        return;
    }

    std::unordered_set<std::string> keyset;
    for (const auto& k : keys) keyset.insert(up(k));

    std::vector<HelpLineView> picked;
    for (const auto& h : lines) {
        if (!keyset.count(up(h.topic_key))) continue;

        if (!should_render_topic_line(h, mode)) {
            continue;
        }

        picked.push_back(h);
    }

    std::sort(picked.begin(), picked.end(), [](const HelpLineView& a, const HelpLineView& b) {
        const int ca = catalog_rank(a.topic_key);
        const int cb = catalog_rank(b.topic_key);
        if (ca != cb) return ca < cb;

        const std::string ak = up(a.topic_key);
        const std::string bk = up(b.topic_key);
        if (ak != bk) return ak < bk;

        const int ka = kind_rank(a.kind);
        const int kb = kind_rank(b.kind);
        if (ka != kb) return ka < kb;

        const int sa = source_rank(a.source);
        const int sb = source_rank(b.source);
        if (sa != sb) return sa < sb;

        if (a.line_no != b.line_no) return a.line_no < b.line_no;
        if (a.part_no != b.part_no) return a.part_no < b.part_no;
        return a.text < b.text;
    });

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::CmdHelpQueryLine,
        {
            {"qualifier", (mode == TopicRenderMode::Usage ? std::string("USAGE ") : std::string())},
            {"query", up(query)}
        });

    if (keys.size() > 1) {
        out() << cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpMatchedTopicsLabel);
        for (const auto& k : keys) out() << " " << k;
        out() << "\n";
    }

    std::string last_key;
    std::string last_kind;
    std::set<std::string> seen_line;

    for (const auto& h : picked) {
        const std::string keyU = up(h.topic_key);
        const std::string kindU = up(h.kind);
        const std::string dedupe = keyU + "|" + kindU + "|" + up(h.text);
        if (!seen_line.insert(dedupe).second) {
            continue;
        }

        if (keyU != last_key) {
            last_key = keyU;
            last_kind.clear();
            out() << "\n" << h.topic_key << "\n";
            out() << std::string(h.topic_key.size(), '=') << "\n";
        }

        if (kindU != last_kind) {
            last_kind = kindU;
            out() << "\n" << kindU << "\n";
            out() << std::string(kindU.size(), '-') << "\n";
        }

        out() << h.text << "\n";
    }

    if (picked.empty()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpTopicNoRenderableSections);
    }
}

static void cmdhelp_usage() {
    cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpUsageTitle);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpUsageBodyText);
    out() << "  CMDHELP REPORT TOPICS\n";
    out() << "  CMDHELP REPORT KIND\n";
    out() << "  CMDHELP REPORT SOURCE\n";
    out() << "  CMDHELP TOPICS\n";
    out() << "  CMDHELP KIND\n";
    out() << "  CMDHELP SOURCE\n";
    out() << "  CMDHELP <topic> PREVIEW LOCALE <locale>\n";
    out() << "  CMDHELP <topic> LOCALE <locale>\n";
    out() << "\n";
    cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpNotesTitle);
    out() << "  "
          << cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpUsageNoteBuild)
          << "\n";
    out() << "  "
          << cli::cmdout::message_text(dottalk::helpdata::MessageId::CmdHelpUsageNoteLegacy)
          << "\n";
    out() << "  REPORT TOPICS lists current HELP DATA topic keys.\n";
    out() << "  REPORT KIND groups current HELP DATA by KIND and shows topic membership.\n";
    out() << "  REPORT SOURCE groups current HELP DATA by SOURCE and shows topic membership.\n";
    out() << "  Locale preview is explicit-only; plain CMDHELP remains canonical/source HELP.\n";
}

static void build_current_helpdata(const std::string& outdir,
                                   const std::vector<std::string>& roots) {
    auto list = collect_commands();

    // The bridge owns detailed counters and may evolve.  CMDHELPCHK ARTIFACTS
    // is the detailed validator/report surface.
    auto counts = export_helpdata_v2_dbfs(outdir, list, roots);

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::CmdHelpCurrentBuildWritten,
        {{"dir", outdir}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::CmdHelpArtifactsMinedFrom,
        {{"root", (roots.empty() ? std::string("./src") : roots.front())}});

    if (counts.usage_contract_files > 0 || counts.usage_contract_rows > 0) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::CmdHelpUsageContractsMined,
            {
                {"rows", std::to_string(counts.usage_contract_rows)},
                {"files", std::to_string(counts.usage_contract_files)}
            });
    }

    print_current_help_report(outdir);
}

static void build_legacy_helpdata(const std::string& outdir,
                                  const std::vector<std::string>& roots) {
    auto counts = export_dbfs(outdir, roots);
    auto list = collect_commands();

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::CmdHelpLegacyBuildWritten,
        {
            {"commands", std::to_string(counts.commands)},
            {"args", std::to_string(counts.args)},
            {"dir", outdir}
        });
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::CmdHelpSwitchesMinedFrom,
        {{"root", (roots.empty() ? std::string("./src") : roots.front())}});
    out() << "\n";
    print_commands_report(out(), list);
}

static void report_legacy_helpdata(const std::string& dir) {
    std::vector<CommandInfo> cmds;
    int arg_rows = 0;

    if (!CmdDbfLoader::load(dir, cmds, arg_rows)) {
        cli::cmdout::print_prefixed_message(
            "CMDHELP",
            dottalk::helpdata::MessageId::CmdHelpLegacyReadFailed,
            {{"dir", dir}});
        cli::cmdout::print_message(dottalk::helpdata::MessageId::CmdHelpLegacyBuildTip);
        return;
    }

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::CmdHelpLegacyReportLine,
        {
            {"commands", std::to_string(cmds.size())},
            {"args", std::to_string(arg_rows)},
            {"dir", dir}
        });
    out() << "\n";
    print_commands_report(out(), cmds);
}

// === CLI =====================================================================

void cmd_COMMANDSHELP(DbArea& /*area*/, std::istringstream& in) {
    auto trim_inplace = [](std::string& s) {
        auto issp = [](unsigned char c){ return std::isspace(c) != 0; };
        s.erase(s.begin(), std::find_if(s.begin(), s.end(), [&](unsigned char c){ return !issp(c); }));
        while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    };

    std::string rest;
    std::getline(in, rest);
    trim_inplace(rest);

    const auto words = split_words(rest);
    const std::string firstU = words.empty() ? std::string() : up(words[0]);

    if (firstU.empty()) {
        print_current_help_report(resolve_help_dir_arg(".").string());
        return;
    }

    if (firstU == "USAGE" || firstU == "HELP" || firstU == "?") {
        if (words.size() >= 2) {
            render_current_topic_help(resolve_help_dir_arg(".").string(),
                                      join_words_range(words, 1, words.size()),
                                      TopicRenderMode::Usage);
        } else {
            cmdhelp_usage();
        }
        return;
    }

    if (firstU == "LEGACY") {
        const std::string dir_arg = (words.size() >= 2) ? words[1] : ".";
        report_legacy_helpdata(resolve_help_dir_arg(dir_arg).string());
        return;
    }

    if (firstU == "REPORT") {
        if (words.size() >= 2 && up(words[1]) == "LEGACY") {
            const std::string dir_arg = (words.size() >= 3) ? words[2] : ".";
            report_legacy_helpdata(resolve_help_dir_arg(dir_arg).string());
            return;
        }
        if (words.size() >= 2) {
            const std::string mode = up(words[1]);
            if (mode == "TOPICS") {
                const std::string dir_arg = (words.size() >= 3) ? words[2] : ".";
                print_current_help_topics(resolve_help_dir_arg(dir_arg).string());
                return;
            }
            if (mode == "KIND") {
                const std::string dir_arg = (words.size() >= 3) ? words[2] : ".";
                print_current_help_grouped(resolve_help_dir_arg(dir_arg).string(), CurrentHelpGroupMode::Kind);
                return;
            }
            if (mode == "SOURCE") {
                const std::string dir_arg = (words.size() >= 3) ? words[2] : ".";
                print_current_help_grouped(resolve_help_dir_arg(dir_arg).string(), CurrentHelpGroupMode::Source);
                return;
            }
        }
        const std::string dir_arg = (words.size() >= 2) ? words[1] : ".";
        print_current_help_report(resolve_help_dir_arg(dir_arg).string());
        return;
    }

    if (firstU == "TOPICS") {
        const std::string dir_arg = (words.size() >= 2) ? words[1] : ".";
        print_current_help_topics(resolve_help_dir_arg(dir_arg).string());
        return;
    }

    if (firstU == "KIND") {
        const std::string dir_arg = (words.size() >= 2) ? words[1] : ".";
        print_current_help_grouped(resolve_help_dir_arg(dir_arg).string(), CurrentHelpGroupMode::Kind);
        return;
    }

    if (firstU == "SOURCE") {
        const std::string dir_arg = (words.size() >= 2) ? words[1] : ".";
        print_current_help_grouped(resolve_help_dir_arg(dir_arg).string(), CurrentHelpGroupMode::Source);
        return;
    }

    if (firstU == "BUILD") {
        size_t pos = 1;
        bool legacy = false;

        if (pos < words.size()) {
            const std::string mode = up(words[pos]);
            if (mode == "V2") {
                // Silent compatibility.  V2 is the current build now.
                ++pos;
            } else if (mode == "LEGACY") {
                legacy = true;
                ++pos;
            }
        }

        const std::string outdir_arg = (pos < words.size()) ? words[pos++] : ".";
        const std::string srcroot = (pos < words.size()) ? words[pos++] : std::string();

        const std::string outdir = resolve_help_dir_arg(outdir_arg).string();
        const std::vector<std::string> roots =
            srcroot.empty() ? std::vector<std::string>{"./src"} : std::vector<std::string>{srcroot};

        if (legacy) {
            build_legacy_helpdata(outdir, roots);
        } else {
            build_current_helpdata(outdir, roots);
        }
        return;
    }

    const auto locale_preview = parse_locale_preview_request(words);
    if (locale_preview.requested) {
        render_current_topic_help_locale_preview(
            resolve_help_dir_arg(".").string(),
            locale_preview.query,
            locale_preview.locale,
            TopicRenderMode::Full);
        return;
    }

    if (words.size() >= 2 && up(words.back()) == "USAGE") {
        render_current_topic_help(resolve_help_dir_arg(".").string(),
                                  join_words_range(words, 0, words.size() - 1),
                                  TopicRenderMode::Usage);
        return;
    }

    render_current_topic_help(resolve_help_dir_arg(".").string(), rest, TopicRenderMode::Full);
}

} // namespace cmdhelp

void cmd_CMDHELP(DbArea& area, std::istringstream& in)
{
    cmdhelp::cmd_COMMANDSHELP(area, in);
}
