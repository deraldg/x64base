// src/cli/cmd_reindex.cpp
// REINDEX [INX|CNX|CDX|SIX|SCX|ALL|CUSTOM] [family-specific args...]
//
// Canonical rebuild dispatcher.
//
// Family policy:
// - REINDEX INX   -> rebuild INX
// - REINDEX CNX   -> rebuild CNX (via legacy REBUILD path)
// - REINDEX CDX   -> rebuild CDX/LMDB (via BUILDLMDB dev power tool)
// - REINDEX SIX   -> student single-tag stub index
// - REINDEX SCX   -> student compound stub index
// - REINDEX ALL   -> v32 table: INX + CNX, v64 table: CDX
// - REINDEX CUSTOM-> SIX + SCX
//
// Default policy:
// - REINDEX with no args chooses by open table flavor:
//     v64-like table -> CDX
//     v32-like table -> INX
// - If no table is open, fallback default is CDX.
//
// Notes:
// - CUSTOM is the command token; the internal enum name avoids "CUSTOM"
//   directly to dodge macro/name collisions on some builds.
// - Console output is ASCII-only (CP437-safe).
// - REINDEX ALL excludes student families by design.
//   Student families are opt-in through REINDEX CUSTOM.

// @dottalk.usage v1
// owner: DOT|REINDEX
// command: REINDEX
// category: index
// status: supported
// noargs: mutate
// effect: rebuild
// mutates: index-files table-stale-state
// usage-access: REINDEX USAGE
// summary:
//   Canonical rebuild dispatcher for INX, CNX, CDX/LMDB, and student index
//   families, choosing a default family by table flavor when no family is given.
//
// usage:
//   REINDEX USAGE
//   REINDEX
//   REINDEX INX
//   REINDEX INX <tagfile>
//   REINDEX CNX
//   REINDEX CNX <name-or-path.cnx>
//   REINDEX CDX
//   REINDEX CDX YES
//   REINDEX CDX AUTO
//   REINDEX CDX NOPROMPT
//   REINDEX CDX CLEAN
//   REINDEX CDX FORCE
//   REINDEX CDX QUIET
//   REINDEX SIX
//   REINDEX SIX <tagfile>
//   REINDEX SCX
//   REINDEX SCX <tagfile>
//   REINDEX ALL
//   REINDEX CUSTOM
//   REINDEX <tagfile>
//
// notes:
//   REINDEX with no arguments chooses the default family by open table flavor.
//   v64-like tables default to CDX through BUILDLMDB.
//   v32-like tables default to INX.
//   With no table open, the fallback default is CDX.
//   REINDEX INX rebuilds a legacy single-tag INX file.
//   REINDEX CNX delegates to REBUILD.
//   REINDEX CDX delegates to BUILDLMDB.
//   REINDEX ALL excludes SIX and SCX by design.
//   REINDEX CUSTOM runs SIX and SCX student families.
//   REINDEX <tagfile> is treated as REINDEX INX <tagfile> for compatibility.
//   Dirty TABLE buffers may prompt for COMMIT before supported rebuild paths.
//
// risk:
//   writes_index_files: yes
//   may_commit_buffered_table_data: yes when dirty TABLE is accepted
//   clears_stale_state: INX path on success
//   mutates_table_data: indirectly through COMMIT prompt only
//   delegates_to_rebuild: CNX
//   delegates_to_buildlmdb: CDX
//
// related:
//   REBUILD
//   BUILDLMDB
//   INDEX
//   CDX
//   CNX
//   COMMIT
//

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "cli/path_resolver.hpp"
#include "cli/cmd_setpath.hpp"
#include "cli/table_state.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using xbase::DbArea;

extern "C" xbase::XBaseEngine* shell_engine(void);

// forward declare (defined elsewhere)
void cmd_COMMIT(xbase::DbArea& A, std::istringstream& in);
void cmd_REBUILD(xbase::DbArea& A, std::istringstream& in);
#if DOTTALK_WITH_INDEX
void cmd_BUILDLMDB(xbase::DbArea& A, std::istringstream& in);
#endif

// ----------------------------- helpers ---------------------------------------

namespace {

enum class ReindexFamily {
    Default,
    INX,
    CNX,
    CDX,
    SIX,
    SCX,
    ALL,
    CustomGroup
};

static std::string trim_copy(const std::string& s) {
    size_t b = s.find_first_not_of(" \t\r\n");
    if (b == std::string::npos) return std::string();
    size_t e = s.find_last_not_of(" \t\r\n");
    return s.substr(b, e - b + 1);
}

static std::string upper_copy(std::string s) {
    for (auto& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

static bool prompt_yes_no(const std::string& prompt, bool default_no = true) {
    std::cout << prompt;
    std::cout << (default_no ? " (y/N) " : " (Y/n) ");
    std::string line;
    std::getline(std::cin, line);
    if (line.empty()) return !default_no;
    char c = static_cast<char>(std::toupper(static_cast<unsigned char>(line[0])));
    return c == 'Y';
}

static int resolve_current_index(xbase::DbArea& A) {
    if (auto* eng = shell_engine()) {
        for (int i = 0; i < xbase::MAX_AREA; ++i) {
            if (&eng->area(i) == &A) return i;
        }
    }
    return -1;
}

static bool ensure_clean_or_commit(xbase::DbArea& A, int area0, const char* verb) {
    if (area0 < 0) return true;

    if (!dottalk::table::is_enabled(area0)) return true;
    if (!dottalk::table::is_dirty(area0)) return true;

    std::ostringstream oss;
    oss << verb << ": TABLE has uncommitted changes. Commit now and continue?";
    if (!prompt_yes_no(oss.str(), true)) {
        cli::cmdout::print_prefixed_message(verb, dottalk::helpdata::MessageId::ReindexCanceledDirtyText);
        return false;
    }

    std::istringstream empty;
    cmd_COMMIT(A, empty);

    if (dottalk::table::is_dirty(area0)) {
        cli::cmdout::print_prefixed_message(verb, dottalk::helpdata::MessageId::ReindexStillDirtyText);
        return false;
    }

    return true;
}

// Canonicalize name: strip spaces/tabs/NUL, keep [A-Za-z0-9_], uppercase.
static std::string canon(const std::string& s) {
    size_t b = 0, e = s.size();
    while (b < e && (s[b] == ' ' || s[b] == '\0' || s[b] == '\t')) ++b;
    while (e > b && (s[e - 1] == ' ' || s[e - 1] == '\0' || s[e - 1] == '\t')) --e;

    std::string out;
    out.reserve(e - b);
    for (size_t i = b; i < e; ++i) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        if (std::isalnum(c) || c == '_')
            out.push_back(static_cast<char>(std::toupper(c)));
    }
    return out;
}

static bool is_hashnum(const std::string& s, int& n_out) {
    if (s.size() >= 2 && s[0] == '#') {
        std::string num = s.substr(1);
        if (!num.empty() && std::all_of(num.begin(), num.end(),
                [](unsigned char c){ return std::isdigit(c) != 0; })) {
            n_out = std::stoi(num);
            return true;
        }
    }
    return false;
}

// Heuristic default-family chooser using APIs that actually exist in xbase.hpp.
// versionByte() and tableFlags() are public. A classic 32-bit DBF is commonly 0x03.
// The 64-bit / extended formats in this codebase carry extended flags and/or a
// non-classic version byte. If in doubt, default to INX only for plain classic DBF.
static bool looks_like_v64_table(const DbArea& A)
{
    if (!A.isOpen()) return false;

    if (A.tableFlags() != 0) return true;

    const uint8_t ver = A.versionByte();

    // Treat plain classic dBASE III (0x03) as v32.
    // Everything else is safer to regard as extended/v64-like for default dispatch.
    return ver != 0x03;
}

static ReindexFamily default_family_for_area(const DbArea& A)
{
    if (!A.isOpen()) {
        return ReindexFamily::CDX; // no-table fallback
    }
    return looks_like_v64_table(A) ? ReindexFamily::CDX : ReindexFamily::INX;
}

static void print_reindex_help()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexUsageText);
}

// little-endian I/O
static void wr_u16(std::ofstream& out, uint16_t v) {
    unsigned char b[2] = {
        static_cast<unsigned char>( v        & 0xFF),
        static_cast<unsigned char>((v >> 8)  & 0xFF)
    };
    out.write(reinterpret_cast<const char*>(b), 2);
}
static void wr_u32(std::ofstream& out, uint32_t v) {
    unsigned char b[4] = {
        static_cast<unsigned char>( v        & 0xFF),
        static_cast<unsigned char>((v >> 8)  & 0xFF),
        static_cast<unsigned char>((v >> 16) & 0xFF),
        static_cast<unsigned char>((v >> 24) & 0xFF)
    };
    out.write(reinterpret_cast<const char*>(b), 4);
}
static void wr_i32(std::ofstream& out, int32_t v) {
    wr_u32(out, static_cast<uint32_t>(v));
}

static bool rd_u16(std::ifstream& in, uint16_t& v) {
    unsigned char b[2];
    if (!in.read(reinterpret_cast<char*>(b), 2)) return false;
    v = static_cast<uint16_t>(b[0] | (static_cast<uint16_t>(b[1]) << 8));
    return true;
}

static bool read_inx_expr_token(const fs::path& tagFile, std::string& exprTokOut, uint16_t& verOut) {
    std::ifstream in(tagFile, std::ios::binary);
    if (!in) return false;

    char magic[4]{};
    if (!in.read(magic, 4)) return false;

    if (std::memcmp(magic, "1INX", 4) == 0) {
        uint16_t ver = 0, nameLen = 0;
        if (!rd_u16(in, ver)) return false;
        if (!rd_u16(in, nameLen)) return false;

        std::string name;
        name.resize(nameLen);
        if (!in.read(name.data(), static_cast<std::streamsize>(nameLen))) return false;

        exprTokOut = name;
        verOut = ver;
        return true;
    }

    if (std::memcmp(magic, "2INX", 4) == 0) {
        uint16_t ver = 0, keylen = 0, nameLen = 0;
        if (!rd_u16(in, ver)) return false;
        if (!rd_u16(in, keylen)) return false;
        (void)keylen;
        if (!rd_u16(in, nameLen)) return false;

        std::string name;
        name.resize(nameLen);
        if (!in.read(name.data(), static_cast<std::streamsize>(nameLen))) return false;

        exprTokOut = name;
        verOut = ver;
        return true;
    }

    return false;
}

// Build (rewrite) the index file for the given expression token.
static bool build_inx(DbArea& A, const std::string& exprTok, const fs::path& outPath) {
    if (!A.isOpen()) { cli::cmdout::print_prefixed_message("REINDEX", dottalk::helpdata::MessageId::ReindexNoTableOpenText); return false; }

    const auto& Fs = A.fields();
    const int fcount = static_cast<int>(Fs.size());

    int fldIdx = -1;
    int hashN = 0;
    if (is_hashnum(exprTok, hashN) && hashN >= 1 && hashN <= fcount) {
        fldIdx = hashN;
    } else {
        const std::string want = canon(exprTok);
        for (int i = 0; i < fcount; ++i) {
            if (canon(Fs[static_cast<size_t>(i)].name) == want) { fldIdx = i + 1; break; }
        }
        if (fldIdx < 1) {
            cli::cmdout::print_prefixed_message("REINDEX", dottalk::helpdata::MessageId::ReindexUnknownFieldText, {{"token", exprTok}});
            return false;
        }
    }

    const auto& fdef = Fs[static_cast<size_t>(fldIdx - 1)];
    const uint16_t keylen = static_cast<uint16_t>(fdef.length);
    const char ftype = fdef.type;

    struct Entry { std::string key; uint32_t recno; };
    std::vector<Entry> ents;
    ents.reserve(static_cast<size_t>(std::max(0, A.recCount())));

    const int32_t total = A.recCount();
    for (int32_t rn = 1; rn <= total; ++rn) {
        if (!A.gotoRec(rn)) continue;
        if (!A.readCurrent()) continue;
        if (A.isDeleted()) continue;

        std::string k = A.get(fldIdx);
        if (ftype == 'C' || ftype == 'c') {
            k = upper_copy(k);
        }
        if (k.size() > keylen) k.resize(keylen);
        if (k.size() < keylen) k.append(static_cast<size_t>(keylen - k.size()), ' ');

        ents.push_back(Entry{ std::move(k), static_cast<uint32_t>(rn) });
    }

    std::sort(ents.begin(), ents.end(),
        [](const Entry& a, const Entry& b){
            if (a.key == b.key) return a.recno < b.recno;
            return a.key < b.key;
        });

    fs::path out = outPath;
    if (!out.has_extension()) out.replace_extension(".inx");

    std::ofstream outFile(out, std::ios::binary | std::ios::trunc);
    if (!outFile) {
        cli::cmdout::print_prefixed_message("REINDEX", dottalk::helpdata::MessageId::ReindexCannotWriteText, {{"path", out.string()}});
        return false;
    }

    std::vector<int32_t> pos_by_recno(static_cast<size_t>(total) + 1u, -1);
    for (uint32_t i = 0; i < static_cast<uint32_t>(ents.size()); ++i) {
        const uint32_t rn = ents[i].recno;
        if (rn <= static_cast<uint32_t>(total)) pos_by_recno[rn] = static_cast<int32_t>(i);
    }

    outFile.write("2INX", 4);
    wr_u16(outFile, 2);
    wr_u16(outFile, keylen);
    wr_u16(outFile, static_cast<uint16_t>(exprTok.size()));
    outFile.write(exprTok.data(), static_cast<std::streamsize>(exprTok.size()));
    wr_u32(outFile, static_cast<uint32_t>(ents.size()));
    wr_u32(outFile, static_cast<uint32_t>(total));

    for (const auto& e : ents) {
        outFile.write(e.key.data(), static_cast<std::streamsize>(e.key.size()));
        wr_u32(outFile, e.recno);
    }

    for (size_t i = 0; i < pos_by_recno.size(); ++i) {
        wr_i32(outFile, pos_by_recno[i]);
    }

    outFile.flush();

    cli::cmdout::print_prefixed_message("REINDEX", dottalk::helpdata::MessageId::ReindexWroteText,
        {{"file", out.filename().string()}, {"expr", exprTok}});
    return true;
}

static fs::path probe_default_inx_for_current(DbArea& A) {
    fs::path nm(A.name());
    std::string base = nm.stem().string();
    if (base.empty()) return {};

    fs::path p_indexes = dottalk::paths::resolve_index(base + ".inx");
    if (fs::exists(p_indexes)) return p_indexes;

    return p_indexes;
}

static bool run_reindex_inx(DbArea& A, const std::string& argRest)
{
    const int area0 = resolve_current_index(A);
    if (!ensure_clean_or_commit(A, area0, "REINDEX")) return false;

    if (!A.isOpen()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexNoTableOpenPlainText);
        return false;
    }

    fs::path tagPath;
    if (!argRest.empty()) {
        tagPath = dottalk::paths::resolve_index(argRest);
        tagPath = dottalk::paths::ensure_ext(std::move(tagPath), ".inx");
    } else {
        tagPath = probe_default_inx_for_current(A);
        if (tagPath.empty()) {
            cli::cmdout::print_prefixed_message("REINDEX", dottalk::helpdata::MessageId::ReindexCannotInferTagText);
            return false;
        }
    }

    if (!tagPath.has_extension()) tagPath.replace_extension(".inx");

    if (!fs::exists(tagPath)) {
        cli::cmdout::print_prefixed_message("REINDEX", dottalk::helpdata::MessageId::ReindexTagNotFoundText, {{"path", tagPath.string()}});
        cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexTagNotFoundHintText, {{"filename", tagPath.filename().string()}});
        return false;
    }

    std::string exprTok;
    uint16_t ver = 0;
    if (!read_inx_expr_token(tagPath, exprTok, ver)) {
        cli::cmdout::print_prefixed_message("REINDEX", dottalk::helpdata::MessageId::ReindexCannotReadExprText, {{"path", tagPath.string()}});
        return false;
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexInxBannerText);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexInxIndexFileText, {{"path", tagPath.string()}});
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexInxTagExprText, {{"expr", exprTok}});

    if (!build_inx(A, exprTok, tagPath)) {
        cli::cmdout::print_prefixed_message("REINDEX", dottalk::helpdata::MessageId::ReindexFailedText);
        return false;
    }

    if (area0 >= 0 && dottalk::table::is_enabled(area0)) {
        dottalk::table::set_stale(area0, false);
        dottalk::table::clear_stale_fields(area0);
        cli::cmdout::print_prefixed_message("REINDEX", dottalk::helpdata::MessageId::ReindexStaleClearedText);
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexRegeneratedNoteText);
    return true;
}

static bool run_reindex_cnx(DbArea& A, const std::string& argRest)
{
    std::istringstream in(argRest);
    cmd_REBUILD(A, in);
    return true;
}

static bool run_reindex_cdx(DbArea& A, const std::string& argRest)
{
#if DOTTALK_WITH_INDEX
    std::istringstream in(argRest);
    cmd_BUILDLMDB(A, in);
    return true;
#else
    (void)A;
    (void)argRest;
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexCdxRequiresLmdbText);
    return false;
#endif
}

static void run_reindex_six(DbArea& A, const std::string& argRest)
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexSixBannerText);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexTableLineText,
        {{"table", A.isOpen() ? A.name() : std::string("(no table open)")}});
    if (!argRest.empty()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexArgLineText, {{"arg", argRest}});
    }
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexStubStatusText);
}

static void run_reindex_scx(DbArea& A, const std::string& argRest)
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexScxBannerText);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexTableLineText,
        {{"table", A.isOpen() ? A.name() : std::string("(no table open)")}});
    if (!argRest.empty()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexArgLineText, {{"arg", argRest}});
    }
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexStubStatusText);
}

static bool dispatch_all(DbArea& A, const std::string& rest)
{
    if (default_family_for_area(A) == ReindexFamily::CDX) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexAllCdxText);
        return run_reindex_cdx(A, rest);
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexAllInxCnxText);

    bool ok_inx = run_reindex_inx(A, std::string());
    bool ok_cnx = run_reindex_cnx(A, rest);

    return ok_inx && ok_cnx;
}

static void dispatch_custom(DbArea& A, const std::string& rest)
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexCustomText);
    run_reindex_six(A, rest);
    run_reindex_scx(A, rest);
}

} // namespace

// ------------------------------- command -------------------------------------

void cmd_REINDEX(DbArea& A, std::istringstream& args) {
    std::string argRest;
    std::getline(args, argRest);
    argRest = trim_copy(argRest);

    if (argRest.empty()) {
        const ReindexFamily def = default_family_for_area(A);
        if (def == ReindexFamily::CDX) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexDefaultCdxText);
            run_reindex_cdx(A, std::string());
        } else {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexDefaultInxText);
            run_reindex_inx(A, std::string());
        }
        return;
    }

    std::istringstream peek(argRest);
    std::string firstTok;
    peek >> firstTok;
    const std::string firstUp = upper_copy(firstTok);

    std::string restAfterFirst;
    std::getline(peek, restAfterFirst);
    restAfterFirst = trim_copy(restAfterFirst);

    if (firstUp == "USAGE" || firstUp == "HELP" || firstUp == "?" || firstUp == "/?" ||
        firstUp == "-H" || firstUp == "--HELP") {
        print_reindex_help();
        return;
    }

    if (firstUp == "INX") {
        run_reindex_inx(A, restAfterFirst);
        return;
    }

    if (firstUp == "CNX") {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexCnxBannerText);
        run_reindex_cnx(A, restAfterFirst);
        return;
    }

    if (firstUp == "CDX") {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::ReindexCdxBuildlmdbText);
        run_reindex_cdx(A, restAfterFirst);
        return;
    }

    if (firstUp == "SIX") {
        run_reindex_six(A, restAfterFirst);
        return;
    }

    if (firstUp == "SCX") {
        run_reindex_scx(A, restAfterFirst);
        return;
    }

    if (firstUp == "ALL") {
        dispatch_all(A, restAfterFirst);
        return;
    }

    if (firstUp == "CUSTOM") {
        dispatch_custom(A, restAfterFirst);
        return;
    }

    // Backward-compatible legacy form:
    // REINDEX <tagfile> -> treat as INX operand.
    run_reindex_inx(A, argRest);
}
