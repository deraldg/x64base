// src/cli/cmd_pack.cpp
// PACK — physically removes deleted records by rewriting the DBF to a temp file
//         containing only non-deleted records, then atomically replaces the original.
//
// Memo-aware extension:
//   - legacy memo tables are still refused
//   - x64 M(8) memo tables are packed by rebuilding BOTH the DBF and the DTX sidecar
//   - x64 memo object ids are remapped to fresh ids in the new DTX
//
// POLICY (2026):
//   - Structural command (file-level operation)
//   - Leaves table CLOSED on success
//   - User must USE to reopen
//   - Indexes must be rebuilt/rebound after

// @dottalk.usage v1
// owner: DOT|PACK
// command: PACK
// category: destructive-table-structure
// status: supported
// noargs: destructive-current-table
// effect: compact-table-file
// mutates: table-file closes-table order-state memo-sidecar index-dirty-state
// usage-access: PACK USAGE
// summary:
//   Physically remove deleted records by rewriting the current DBF; x64 memo
//   tables rebuild both DBF and DTX sidecar with remapped memo ids.
//
// usage:
//   PACK USAGE
//   PACK
//
// examples:
//   PACK
//
// notes:
//   PACK USAGE prints usage before open-table checks.
//   PACK rewrites the current DBF with only non-deleted records and closes the table on success.
//   PACK supports x64 M(8) memo tables by rebuilding DBF and DTX together.
//   Legacy memo tables are refused.
//   Index containers must be rebuilt/rebound after PACK.
//
// risk:
//   requires_open_table: yes except usage
//   destructive_rewrite: yes
//   mutates_table_file: yes
//   mutates_memo_sidecar: x64 memo tables
//   closes_table: yes
//   clears_order_state: yes
//
// related:
//   TURBOPACK
//   ZAP
//   RECALL
//

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "textio.hpp"
#include "cli/command_output.hpp"
#include "cli/order_state.hpp"
#include "memo/memostore.hpp"
#include <cctype>

// Optional path slot support (SETPATH)
#if __has_include("cli/cmd_setpath.hpp")
  #include "cli/cmd_setpath.hpp"
  #define HAVE_SETPATH 1
#else
  #define HAVE_SETPATH 0
#endif

// Optional CNX dirty marking
#if __has_include("cnx/cnx.hpp")
  #include "cnx/cnx.hpp"
  #define HAVE_CNX 1
#else
  #define HAVE_CNX 0
#endif

namespace fs = std::filesystem;

namespace {

struct MemoFieldInfo {
    int field1 = 0;             // 1-based field number
    std::size_t row_offset = 0; // byte offset within record image
};

static inline fs::path resolve_dbf_slot_path(fs::path p)
{
    if (p.empty()) return p;
    if (p.is_absolute()) return p;

#if HAVE_SETPATH
    try {
        fs::path root = dottalk::paths::get_slot(dottalk::paths::Slot::DBF);
        if (!root.empty() && fs::exists(root)) {
            return root / p;
        }
    } catch (...) {}
#endif

    try {
        return fs::absolute(p);
    } catch (...) {
        return p;
    }
}

static inline bool ends_with_ci(const std::string& s, const char* suffix)
{
    const std::string suf = (suffix ? std::string(suffix) : std::string{});
    if (s.size() < suf.size()) return false;

    const std::size_t off = s.size() - suf.size();
    for (std::size_t i = 0; i < suf.size(); ++i) {
        const unsigned char a = static_cast<unsigned char>(s[off + i]);
        const unsigned char b = static_cast<unsigned char>(suf[i]);
        if (std::tolower(a) != std::tolower(b)) return false;
    }
    return true;
}

static inline std::string s8(const fs::path& p)
{
#if defined(_WIN32)
    auto u = p.u8string();
    return std::string(u.begin(), u.end());
#else
    return p.string();
#endif
}

static inline void set_dbf_last_updated_and_reccount(
    std::vector<std::uint8_t>& hdrBlock,
    std::uint32_t recCount)
{
    if (hdrBlock.size() < 32) return;

    std::time_t now = std::time(nullptr);
    std::tm tmv{};
#if defined(_WIN32)
    localtime_s(&tmv, &now);
#else
    tmv = *std::localtime(&now);
#endif

    const std::uint8_t yy = static_cast<std::uint8_t>(tmv.tm_year % 100);
    const std::uint8_t mm = static_cast<std::uint8_t>(tmv.tm_mon + 1);
    const std::uint8_t dd = static_cast<std::uint8_t>(tmv.tm_mday);

    hdrBlock[1] = yy;
    hdrBlock[2] = mm;
    hdrBlock[3] = dd;

    hdrBlock[4] = static_cast<std::uint8_t>( recCount        & 0xFF);
    hdrBlock[5] = static_cast<std::uint8_t>((recCount >> 8)  & 0xFF);
    hdrBlock[6] = static_cast<std::uint8_t>((recCount >> 16) & 0xFF);
    hdrBlock[7] = static_cast<std::uint8_t>((recCount >> 24) & 0xFF);
}

static inline void set_x64_ext_record_count(
    std::vector<std::uint8_t>& hdrBlock,
    std::uint64_t recCount)
{
    if (hdrBlock.empty()) return;
    if (hdrBlock[0] != xbase::DBF_VERSION_64) return;

    const std::size_t off =
        sizeof(xbase::VfpHeader) + offsetof(xbase::LargeHeaderExtension, record_count);

    if (hdrBlock.size() < off + sizeof(std::uint64_t)) return;

    std::memcpy(hdrBlock.data() + off, &recCount, sizeof(recCount));
}

static inline std::uint16_t read_le16(const std::uint8_t* p)
{
    return static_cast<std::uint16_t>(p[0] | (static_cast<std::uint16_t>(p[1]) << 8));
}

static inline std::uint32_t read_le32(const std::uint8_t* p)
{
    return static_cast<std::uint32_t>(
        p[0] |
        (static_cast<std::uint32_t>(p[1]) << 8) |
        (static_cast<std::uint32_t>(p[2]) << 16) |
        (static_cast<std::uint32_t>(p[3]) << 24)
    );
}

static inline std::uint64_t read_u64_le(const std::uint8_t* p)
{
    std::uint64_t v = 0;
    std::memcpy(&v, p, sizeof(v));
    return v;
}

static inline void write_u64_le(std::uint8_t* p, std::uint64_t v)
{
    std::memcpy(p, &v, sizeof(v));
}

static inline fs::path make_temp_path(const fs::path& orig, const std::string& /*tag*/)
{
    fs::path dir = orig.parent_path();
    std::string stem = orig.stem().string();
    std::string ext  = orig.extension().string();
    return dir / (stem + ".pack.tmp" + ext);
}

static inline fs::path make_bak_path(const fs::path& orig, const std::string& /*tag*/)
{
    fs::path dir = orig.parent_path();
    std::string stem = orig.stem().string();
    std::string ext  = orig.extension().string();
    return dir / (stem + ".pack.bak" + ext);
}

static inline fs::path dtx_path_for_dbf_path(const fs::path& dbf)
{
    fs::path p = dbf;
    p.replace_extension(".dtx");
    return p;
}

static void try_mark_index_dirty(const std::string& orderContainer)
{
    if (orderContainer.empty()) return;

    fs::path ip(orderContainer);
    std::string ext = textio::up(ip.extension().string());

#if HAVE_CNX && DOTTALK_HAS_XINDEX
    if (ext == ".CNX") {
        cnxfile::CNXHandle* h = nullptr;
        if (cnxfile::open(ip.string(), h) && h) {
            cnxfile::set_dirty(h, true);
            cnxfile::close(h);
            cli::cmdout::print_prefixed_message(
                "PACK", dottalk::helpdata::MessageId::PackCnxMarkedDirtyText,
                {{"file", s8(ip.filename())}});
            return;
        }
        cli::cmdout::print_prefixed_message(
            "PACK", dottalk::helpdata::MessageId::PackCnxCouldNotMarkText);
        return;
    }
#endif

    if (ext == ".INX" || ext == ".CDX") {
        cli::cmdout::print_prefixed_message(
            "PACK", dottalk::helpdata::MessageId::PackIndexRebuildText,
            {{"file", s8(ip.filename())}});
        return;
    }

    cli::cmdout::print_prefixed_message(
        "PACK", dottalk::helpdata::MessageId::PackOrderRebuildText,
        {{"file", s8(ip.filename())}});
}

static bool replace_file_with_backup(const fs::path& orig, const fs::path& tmp, const fs::path& bak)
{
    std::error_code ec;

    if (fs::exists(bak, ec)) {
        fs::remove(bak, ec);
    }

    fs::rename(orig, bak, ec);
    if (ec) {
        cli::cmdout::print_prefixed_message(
            "PACK", dottalk::helpdata::MessageId::PackFailedRenameBackupText,
            {{"detail", ec.message()}});
        return false;
    }

    fs::rename(tmp, orig, ec);
    if (ec) {
        cli::cmdout::print_prefixed_message(
            "PACK", dottalk::helpdata::MessageId::PackFailedReplaceText,
            {{"detail", ec.message()}});

        std::error_code ec2;
        fs::rename(bak, orig, ec2);
        if (ec2) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::PackRollbackFailedText,
                {{"detail", ec2.message()}});
        } else {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::PackOriginalRestoredText);
        }
        return false;
    }

    fs::remove(bak, ec);
    return true;
}

static bool replace_two_files_with_backup(const fs::path& origDbf,
                                          const fs::path& tmpDbf,
                                          const fs::path& bakDbf,
                                          const fs::path& origDtx,
                                          const fs::path& tmpDtx,
                                          const fs::path& bakDtx)
{
    std::error_code ec;

    if (fs::exists(bakDbf, ec)) fs::remove(bakDbf, ec);
    if (fs::exists(bakDtx, ec)) fs::remove(bakDtx, ec);

    fs::rename(origDbf, bakDbf, ec);
    if (ec) {
        cli::cmdout::print_prefixed_message(
            "PACK", dottalk::helpdata::MessageId::PackFailedRenameDbfBackupText,
            {{"detail", ec.message()}});
        return false;
    }

    ec.clear();
    if (fs::exists(origDtx)) {
        fs::rename(origDtx, bakDtx, ec);
        if (ec) {
            cli::cmdout::print_prefixed_message(
                "PACK", dottalk::helpdata::MessageId::PackFailedRenameDtxBackupText,
                {{"detail", ec.message()}});
            std::error_code ec2;
            fs::rename(bakDbf, origDbf, ec2);
            return false;
        }
    }

    ec.clear();
    fs::rename(tmpDbf, origDbf, ec);
    if (ec) {
        cli::cmdout::print_prefixed_message(
            "PACK", dottalk::helpdata::MessageId::PackFailedReplaceDbfText,
            {{"detail", ec.message()}});

        std::error_code ec2;
        if (fs::exists(bakDtx)) fs::rename(bakDtx, origDtx, ec2);
        ec2.clear();
        fs::rename(bakDbf, origDbf, ec2);
        return false;
    }

    ec.clear();
    fs::rename(tmpDtx, origDtx, ec);
    if (ec) {
        cli::cmdout::print_prefixed_message(
            "PACK", dottalk::helpdata::MessageId::PackFailedReplaceDtxText,
            {{"detail", ec.message()}});

        std::error_code ec2;
        fs::remove(origDbf, ec2);
        ec2.clear();
        fs::rename(bakDbf, origDbf, ec2);
        ec2.clear();
        if (fs::exists(bakDtx)) fs::rename(bakDtx, origDtx, ec2);
        return false;
    }

    fs::remove(bakDbf, ec);
    fs::remove(bakDtx, ec);
    return true;
}

static bool has_x64_memo_fields(const xbase::DbArea& a)
{
    if (a.versionByte() != xbase::DBF_VERSION_64) return false;

    for (const auto& f : a.fields()) {
        if ((f.type == 'M' || f.type == 'm') && f.length == 8) {
            return true;
        }
    }
    return false;
}

static std::vector<MemoFieldInfo> collect_x64_memo_fields(const xbase::DbArea& a)
{
    std::vector<MemoFieldInfo> out;
    if (a.versionByte() != xbase::DBF_VERSION_64) return out;

    std::size_t off = 1; // delete flag
    const auto& fsf = a.fields();
    for (std::size_t i = 0; i < fsf.size(); ++i) {
        const auto& f = fsf[i];
        if ((f.type == 'M' || f.type == 'm') && f.length == 8) {
            out.push_back(MemoFieldInfo{
                static_cast<int>(i) + 1,
                off
            });
        }
        off += f.length;
    }
    return out;
}

static bool compute_safe_record_count(const fs::path& origPath,
                                      std::uint16_t headerLen,
                                      std::uint16_t recordLen,
                                      std::uint32_t headerRecCount,
                                      std::uint32_t& actualRecCount,
                                      std::uint32_t& safeRecCount,
                                      std::string& err)
{
    actualRecCount = 0;
    safeRecCount = 0;
    err.clear();

    std::error_code ec;
    const auto fileSize = fs::file_size(origPath, ec);
    if (ec) {
        err = "failed to get file size: " + ec.message();
        return false;
    }

    if (fileSize < headerLen) {
        err = "file is smaller than header length";
        return false;
    }

    const std::uintmax_t payloadBytes = fileSize - static_cast<std::uintmax_t>(headerLen);
    std::uintmax_t usableBytes = payloadBytes;

    if (usableBytes > 0) {
        std::ifstream tail(origPath, std::ios::binary);
        if (tail) {
            tail.seekg(static_cast<std::streamoff>(fileSize - 1), std::ios::beg);
            char last = 0;
            tail.read(&last, 1);
            if (tail && static_cast<unsigned char>(last) == 0x1A) {
                --usableBytes;
            }
        }
    }

    actualRecCount = static_cast<std::uint32_t>(usableBytes / recordLen);
    safeRecCount = std::min(headerRecCount, actualRecCount);
    return true;
}

static bool pack_x64_memo_table(const fs::path& origPath,
                                const fs::path& tmpPath,
                                const fs::path& bakPath,
                                std::uint32_t& kept_out,
                                std::uint32_t& deleted_out,
                                std::string& err,
                                const std::vector<MemoFieldInfo>& memoFields)
{
    kept_out = 0;
    deleted_out = 0;
    err.clear();

    const fs::path origDtx = dtx_path_for_dbf_path(origPath);
    const fs::path tmpDtx  = make_temp_path(origDtx, "pack");
    const fs::path bakDtx  = make_bak_path(origDtx, "pack");

    if (!fs::exists(origDtx)) {
        err = "x64 memo sidecar not found: " + s8(origDtx);
        return false;
    }

    std::ifstream src(origPath, std::ios::binary);
    if (!src) {
        err = "cannot open original DBF for reading";
        return false;
    }

    std::uint8_t hdr32[32]{};
    src.read(reinterpret_cast<char*>(hdr32), 32);
    if (!src) {
        err = "failed to read first 32 bytes of DBF header";
        return false;
    }

    const std::uint32_t origRecCount = read_le32(hdr32 + 4);
    const std::uint16_t headerLen    = read_le16(hdr32 + 8);
    const std::uint16_t recordLen    = read_le16(hdr32 + 10);

    if (headerLen < 33 || recordLen < 1 || headerLen > 4096) {
        err = "invalid DBF header";
        return false;
    }

    std::uint32_t actualRecCount = 0;
    std::uint32_t safeRecCount = 0;
    if (!compute_safe_record_count(origPath, headerLen, recordLen, origRecCount,
                                   actualRecCount, safeRecCount, err)) {
        return false;
    }

    std::vector<std::uint8_t> headerBlock(headerLen);
    src.seekg(0, std::ios::beg);
    src.read(reinterpret_cast<char*>(headerBlock.data()), headerLen);
    if (!src) {
        err = "failed to read full DBF header block";
        return false;
    }
    src.close();

    if (headerBlock.size() > 0 && headerBlock.back() != xbase::HEADER_TERM_BYTE) {
        cli::cmdout::print_prefixed_message("Warning", dottalk::helpdata::MessageId::PackHeaderNoTerminatorText);
    }

    if (origRecCount != actualRecCount) {
        cli::cmdout::print_prefixed_message(
            "PACK", dottalk::helpdata::MessageId::PackHeaderCountMismatchText,
            {{"orig", std::to_string(origRecCount)},
             {"actual", std::to_string(actualRecCount)},
             {"safe", std::to_string(safeRecCount)}});
    }

    dottalk::memo::MemoStore oldStore;
    {
        const auto r = oldStore.open(origDtx.string(), dottalk::memo::OpenMode::OpenExisting);
        if (!r.ok) {
            err = r.error.empty() ? "failed to open original DTX sidecar" : r.error;
            return false;
        }
    }

    dottalk::memo::MemoStore newStore;
    {
        const auto r = newStore.open(tmpDtx.string(), dottalk::memo::OpenMode::TruncateAndCreate);
        if (!r.ok) {
            err = r.error.empty() ? "failed to create temporary DTX sidecar" : r.error;
            return false;
        }
    }

    std::ofstream out(tmpPath, std::ios::binary | std::ios::trunc);
    if (!out) {
        err = "cannot create temporary DBF";
        newStore.close();
        fs::remove(tmpDtx);
        return false;
    }

    set_dbf_last_updated_and_reccount(headerBlock, 0);
    set_x64_ext_record_count(headerBlock, 0);

    out.write(reinterpret_cast<const char*>(headerBlock.data()),
              static_cast<std::streamsize>(headerBlock.size()));
    if (!out) {
        err = "failed to write initial DBF header";
        out.close();
        fs::remove(tmpPath);
        newStore.close();
        fs::remove(tmpDtx);
        return false;
    }

    src.open(origPath, std::ios::binary);
    if (!src) {
        err = "cannot reopen original DBF for record copy";
        out.close();
        fs::remove(tmpPath);
        newStore.close();
        fs::remove(tmpDtx);
        return false;
    }

    src.seekg(static_cast<std::streamoff>(headerLen), std::ios::beg);

    std::vector<std::uint8_t> recbuf(recordLen);

    for (std::uint32_t i = 0; i < safeRecCount; ++i) {
        src.read(reinterpret_cast<char*>(recbuf.data()), recordLen);
        if (!src) {
            err = "failed while reading source records";
            src.close();
            out.close();
            fs::remove(tmpPath);
            newStore.close();
            fs::remove(tmpDtx);
            return false;
        }

        if (!recbuf.empty() && recbuf[0] == static_cast<std::uint8_t>(xbase::IS_DELETED)) {
            ++deleted_out;
            continue;
        }

        for (const auto& mf : memoFields) {
            if (mf.row_offset + 8 > recbuf.size()) {
                err = "memo field offset exceeds record length";
                src.close();
                out.close();
                fs::remove(tmpPath);
                newStore.close();
                fs::remove(tmpDtx);
                return false;
            }

            const std::uint64_t old_id = read_u64_le(recbuf.data() + mf.row_offset);

            if (old_id == 0) {
                write_u64_le(recbuf.data() + mf.row_offset, 0);
                continue;
            }

            std::string text;
            std::string memo_err;
            if (!oldStore.get_text_id(old_id, text, &memo_err)) {
                cli::cmdout::print_prefixed_message(
                    "PACK", dottalk::helpdata::MessageId::PackMemoNotFoundText,
                    {{"id", std::to_string(old_id)}});
                write_u64_le(recbuf.data() + mf.row_offset, 0);
                continue;
            }

            const std::uint64_t new_id = newStore.put_text_id(text, &memo_err);
            if (new_id == 0) {
                err = memo_err.empty()
                    ? ("failed to create new memo object for old id " + std::to_string(old_id))
                    : memo_err;
                src.close();
                out.close();
                fs::remove(tmpPath);
                newStore.close();
                fs::remove(tmpDtx);
                return false;
            }

            write_u64_le(recbuf.data() + mf.row_offset, new_id);
        }

        out.write(reinterpret_cast<const char*>(recbuf.data()), recordLen);
        if (!out) {
            err = "failed while writing packed DBF record";
            src.close();
            out.close();
            fs::remove(tmpPath);
            newStore.close();
            fs::remove(tmpDtx);
            return false;
        }

        ++kept_out;
    }

    const char eof_marker = static_cast<char>(0x1A);
    out.write(&eof_marker, 1);
    if (!out) {
        err = "failed writing EOF marker to packed DBF";
        src.close();
        out.close();
        fs::remove(tmpPath);
        newStore.close();
        fs::remove(tmpDtx);
        return false;
    }

    set_dbf_last_updated_and_reccount(headerBlock, kept_out);
    set_x64_ext_record_count(headerBlock, static_cast<std::uint64_t>(kept_out));

    out.seekp(0, std::ios::beg);
    out.write(reinterpret_cast<const char*>(headerBlock.data()),
              static_cast<std::streamsize>(headerBlock.size()));
    if (!out) {
        err = "failed to rewrite final DBF header";
        src.close();
        out.close();
        fs::remove(tmpPath);
        newStore.close();
        fs::remove(tmpDtx);
        return false;
    }

    out.flush();
    if (!out) {
        err = "failed to flush packed DBF";
        src.close();
        out.close();
        fs::remove(tmpPath);
        newStore.close();
        fs::remove(tmpDtx);
        return false;
    }

    const auto fr = newStore.flush();
    if (!fr.ok) {
        err = fr.error.empty() ? "failed to flush packed DTX" : fr.error;
        src.close();
        out.close();
        fs::remove(tmpPath);
        newStore.close();
        fs::remove(tmpDtx);
        return false;
    }

    src.close();
    out.close();
    newStore.close();
    oldStore.close();

    if (!replace_two_files_with_backup(origPath, tmpPath, bakPath, origDtx, tmpDtx, bakDtx)) {
        err = "failed replacing original DBF/DTX with packed pair";
        return false;
    }

    return true;
}

} // namespace

static void print_pack_usage_contract()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::PackUsageText);
}

static bool pack_usage_token_contract(std::string tok)
{
    std::transform(tok.begin(), tok.end(), tok.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return tok == "USAGE" || tok == "HELP" || tok == "?";
}
void cmd_PACK(xbase::DbArea& A, std::istringstream& in)
{
    // PACK_USAGE_CONTRACT_BRANCH
    {
        const std::streampos usage_pos = in.tellg();
        std::string usage_tok;
        if (in >> usage_tok) {
            in.clear();
            if (usage_pos != std::streampos(-1)) {
                in.seekg(usage_pos);
            }

            if (pack_usage_token_contract(usage_tok)) {
                print_pack_usage_contract();
                return;
            }
        } else {
            in.clear();
            if (usage_pos != std::streampos(-1)) {
                in.seekg(usage_pos);
            }
        }
    }

    if (!A.isOpen() || A.filename().empty()) {
        cli::cmdout::print_prefixed_message("PACK", dottalk::helpdata::MessageId::PackNoTableOpenText);
        return;
    }

    const bool x64_memo_pack =
        (A.versionByte() == xbase::DBF_VERSION_64) &&
        has_x64_memo_fields(A);

    if (A.memoKind() != xbase::DbArea::MemoKind::NONE && !x64_memo_pack) {
        cli::cmdout::print_prefixed_message("PACK", dottalk::helpdata::MessageId::PackMemoNotSupportedText);
        return;
    }

    std::string orderContainer;
    try { orderContainer = orderstate::orderName(A); } catch (...) {}

    std::string dbf_path_str = A.filename();
    const std::vector<MemoFieldInfo> memoFields = collect_x64_memo_fields(A);

    try { orderstate::clearOrder(A); } catch (...) {}
    try { A.close(); } catch (...) {}

    fs::path origPath = resolve_dbf_slot_path(fs::path(dbf_path_str));
    if (!ends_with_ci(s8(origPath), ".dbf")) {
        origPath.replace_extension(".dbf");
    }

    if (!fs::exists(origPath)) {
        cli::cmdout::print_prefixed_message(
            "PACK", dottalk::helpdata::MessageId::PackFileNotFoundText, {{"path", s8(origPath)}});
        return;
    }

    const fs::path tmpPath = make_temp_path(origPath, "pack");
    const fs::path bakPath = make_bak_path(origPath, "pack");

    std::uint32_t kept = 0;
    std::uint32_t deleted = 0;

    if (x64_memo_pack) {
        std::string err;
        if (!pack_x64_memo_table(origPath, tmpPath, bakPath, kept, deleted, err, memoFields)) {
            cli::cmdout::print_prefixed_message(
                "PACK", dottalk::helpdata::MessageId::PackDetailText, {{"detail", err}});
            cli::cmdout::print_prefixed_message(
                "PACK", dottalk::helpdata::MessageId::PackAbortedText);
            return;
        }
    } else {
        std::ifstream src(origPath, std::ios::binary);
        if (!src) {
            cli::cmdout::print_prefixed_message("PACK", dottalk::helpdata::MessageId::PackCannotOpenReadText);
            return;
        }

        std::uint8_t hdr32[32]{};
        src.read(reinterpret_cast<char*>(hdr32), 32);
        if (!src) {
            cli::cmdout::print_prefixed_message("PACK", dottalk::helpdata::MessageId::PackFailedRead32Text);
            return;
        }

        const std::uint32_t origRecCount = read_le32(hdr32 + 4);
        const std::uint16_t headerLen    = read_le16(hdr32 + 8);
        const std::uint16_t recordLen    = read_le16(hdr32 + 10);

        if (headerLen < 33 || recordLen < 1 || headerLen > 4096) {
            cli::cmdout::print_prefixed_message(
                "PACK", dottalk::helpdata::MessageId::PackInvalidHeaderText,
                {{"hl", std::to_string(headerLen)}, {"rl", std::to_string(recordLen)}});
            return;
        }

        std::uint32_t actualRecCount = 0;
        std::uint32_t safeRecCount = 0;
        std::string safeCountErr;
        if (!compute_safe_record_count(origPath, headerLen, recordLen, origRecCount,
                                       actualRecCount, safeRecCount, safeCountErr)) {
            cli::cmdout::print_prefixed_message(
                "PACK", dottalk::helpdata::MessageId::PackDetailText, {{"detail", safeCountErr}});
            return;
        }

        std::vector<std::uint8_t> headerBlock(headerLen);
        src.seekg(0, std::ios::beg);
        src.read(reinterpret_cast<char*>(headerBlock.data()), headerLen);
        if (!src) {
            cli::cmdout::print_prefixed_message("PACK", dottalk::helpdata::MessageId::PackFailedReadHeaderBlockText);
            return;
        }

        if (headerBlock.size() > 0 && headerBlock.back() != xbase::HEADER_TERM_BYTE) {
            cli::cmdout::print_prefixed_message("Warning", dottalk::helpdata::MessageId::PackHeaderNoTerminatorText);
        }

        if (origRecCount != actualRecCount) {
            cli::cmdout::print_prefixed_message(
                "PACK", dottalk::helpdata::MessageId::PackHeaderCountMismatchText,
                {{"orig", std::to_string(origRecCount)},
                 {"actual", std::to_string(actualRecCount)},
                 {"safe", std::to_string(safeRecCount)}});
        }

        src.close();

        std::ofstream out(tmpPath, std::ios::binary | std::ios::trunc);
        if (!out) {
            cli::cmdout::print_prefixed_message(
                "PACK", dottalk::helpdata::MessageId::PackCannotCreateTempText, {{"path", s8(tmpPath)}});
            return;
        }

        std::vector<std::uint8_t> recbuf(recordLen);

        set_dbf_last_updated_and_reccount(headerBlock, 0);
        set_x64_ext_record_count(headerBlock, 0); // x64 non-memo fix

        out.write(reinterpret_cast<const char*>(headerBlock.data()), headerLen);
        if (!out) {
            cli::cmdout::print_prefixed_message("PACK", dottalk::helpdata::MessageId::PackFailedWriteInitialHeaderText);
            out.close();
            fs::remove(tmpPath);
            return;
        }

        src.open(origPath, std::ios::binary);
        if (!src) {
            cli::cmdout::print_prefixed_message("PACK", dottalk::helpdata::MessageId::PackCannotReopenText);
            out.close();
            fs::remove(tmpPath);
            return;
        }

        src.seekg(static_cast<std::streamoff>(headerLen), std::ios::beg);

        for (std::uint32_t i = 0; i < safeRecCount; ++i) {
            src.read(reinterpret_cast<char*>(recbuf.data()), recordLen);
            if (!src) {
                cli::cmdout::print_prefixed_message("PACK", dottalk::helpdata::MessageId::PackFailedReadRecordsText);
                src.close();
                out.close();
                fs::remove(tmpPath);
                return;
            }

            if (!recbuf.empty() && recbuf[0] == static_cast<std::uint8_t>(xbase::IS_DELETED)) {
                ++deleted;
                continue;
            }

            out.write(reinterpret_cast<const char*>(recbuf.data()), recordLen);
            if (!out) {
                cli::cmdout::print_prefixed_message("PACK", dottalk::helpdata::MessageId::PackFailedWriteRecordsText);
                src.close();
                out.close();
                fs::remove(tmpPath);
                return;
            }

            ++kept;
        }

        const char eof_marker = static_cast<char>(0x1A);
        out.write(&eof_marker, 1);
        if (!out) {
            cli::cmdout::print_prefixed_message("PACK", dottalk::helpdata::MessageId::PackFailedWriteEofText);
            src.close();
            out.close();
            fs::remove(tmpPath);
            return;
        }

        set_dbf_last_updated_and_reccount(headerBlock, kept);
        set_x64_ext_record_count(headerBlock, static_cast<std::uint64_t>(kept)); // x64 non-memo fix

        out.seekp(0, std::ios::beg);
        out.write(reinterpret_cast<const char*>(headerBlock.data()), headerLen);
        if (!out) {
            cli::cmdout::print_prefixed_message("PACK", dottalk::helpdata::MessageId::PackFailedRewriteHeaderText);
            src.close();
            out.close();
            fs::remove(tmpPath);
            return;
        }

        out.flush();
        src.close();
        out.close();

        if (!replace_file_with_backup(origPath, tmpPath, bakPath)) {
            return;
        }
    }

    try_mark_index_dirty(orderContainer);

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::PackCompleteText,
        {{"kept", std::to_string(kept)}, {"deleted", std::to_string(deleted)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::PackReadyForUseText,
        {{"file", origPath.filename().string()}});
    if (x64_memo_pack) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::PackSidecarsRebuiltText);
    } else {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::PackSidecarsNoneText);
    }
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::PackReopenText,
        {{"stem", origPath.stem().string()}});
    cli::cmdout::print_message(dottalk::helpdata::MessageId::PackRebuildIndexesText);
}
