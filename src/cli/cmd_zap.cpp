// src/cli/cmd_zap.cpp
// ZAP — removes ALL records from the current DBF, preserving structure (header + field descriptors).
//       Rewrites the file with record count = 0, updated timestamp, and EOF marker.
//
// POLICY (2026):
//   - Structural command (file-level operation)
//   - Leaves table CLOSED on success
//   - User must USE to reopen
//   - Indexes must be rebuilt/rebound after

// @dottalk.usage v1
// owner: DOT|ZAP
// command: ZAP
// category: destructive-table
// status: supported
// noargs: destructive-current-table
// effect: remove-all-records
// mutates: table-file closes-table order-state
// usage-access: ZAP USAGE
// summary:
//   Remove all records from the current non-memo DBF while preserving structure.
//
// usage:
//   ZAP USAGE
//   ZAP
//
// examples:
//   ZAP
//
// notes:
//   ZAP USAGE prints usage before open-table checks.
//   ZAP rewrites the current DBF with zero records and closes the table on success.
//   ZAP currently refuses memo tables.
//   Index containers must be rebuilt/rebound afterward.
//
// risk:
//   requires_open_table: yes except usage
//   destructive: yes
//   mutates_table_file: yes
//   closes_table: yes
//   clears_order_state: yes
//
// related:
//   ERASE
//   PACK
//   RECALL
//

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

#if __has_include("cli/cmd_setpath.hpp")
  #include "cli/cmd_setpath.hpp"
  #define HAVE_SETPATH 1
#else
  #define HAVE_SETPATH 0
#endif

#if __has_include("cnx/cnx.hpp")
  #include "cnx/cnx.hpp"
  #define HAVE_CNX 1
#else
  #define HAVE_CNX 0
#endif

namespace fs = std::filesystem;

namespace {

static inline fs::path resolve_dbf_slot_path(fs::path p) {
    if (p.empty())                return p;
    if (p.is_absolute())          return p;

#if HAVE_SETPATH
    try {
        fs::path root = dottalk::paths::get_slot(dottalk::paths::Slot::DBF);
        if (!root.empty() && fs::exists(root)) {
            return fs::absolute(root / p);
        }
    } catch (...) {}
#endif

    try { return fs::absolute(p); } catch (...) { return p; }
}

static inline std::string s8(const fs::path& p) {
#if defined(_WIN32)
    auto u = p.u8string();
    return std::string(u.begin(), u.end());
#else
    return p.string();
#endif
}

static inline std::uint16_t read_le16(const std::uint8_t* p) {
    return static_cast<std::uint16_t>(p[0] | (static_cast<std::uint16_t>(p[1]) << 8));
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

    hdrBlock[4] = static_cast<std::uint8_t>(recCount & 0xFF);
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

static inline fs::path make_temp_path(const fs::path& orig) {
    fs::path dir  = orig.parent_path();
    std::string stem = orig.stem().string();
    std::string ext  = orig.extension().string();
    return dir / (stem + ".zap.tmp" + ext);
}

static inline fs::path make_bak_path(const fs::path& orig) {
    fs::path dir  = orig.parent_path();
    std::string stem = orig.stem().string();
    std::string ext  = orig.extension().string();
    return dir / (stem + ".zap.bak" + ext);
}

static bool replace_file_with_backup(const fs::path& orig, const fs::path& tmp, const fs::path& bak) {
    std::error_code ec;

    if (fs::exists(bak, ec)) {
        fs::remove(bak, ec);
    }

    fs::rename(orig, bak, ec);
    if (ec) {
        cli::cmdout::print_prefixed_message(
            "ZAP", dottalk::helpdata::MessageId::ZapFailedRenameBackupText,
            {{"detail", ec.message()}});
        return false;
    }

    fs::rename(tmp, orig, ec);
    if (ec) {
        cli::cmdout::print_prefixed_message(
            "ZAP", dottalk::helpdata::MessageId::ZapFailedReplaceText,
            {{"detail", ec.message()}});
        std::error_code ec2;
        fs::rename(bak, orig, ec2);
        if (ec2) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ZapRollbackFailedText);
        } else {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ZapOriginalRestoredText);
        }
        return false;
    }

    fs::remove(bak, ec);
    return true;
}

static void try_mark_index_dirty(const std::string& orderContainer) {
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
                "ZAP", dottalk::helpdata::MessageId::ZapCnxMarkedDirtyText,
                {{"file", s8(ip.filename())}});
            return;
        }
        cli::cmdout::print_prefixed_message(
            "ZAP", dottalk::helpdata::MessageId::ZapCnxCouldNotMarkText);
        return;
    }
#endif

    if (ext == ".INX" || ext == ".CDX") {
        cli::cmdout::print_prefixed_message(
            "ZAP", dottalk::helpdata::MessageId::ZapIndexRebuildText,
            {{"file", s8(ip.filename())}});
        return;
    }

    cli::cmdout::print_prefixed_message(
        "ZAP", dottalk::helpdata::MessageId::ZapOrderRebuildText,
        {{"file", s8(ip.filename())}});
}

} // namespace

static void print_zap_usage_contract()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ZapUsageText);
}
void cmd_ZAP(xbase::DbArea& A, std::istringstream& in) {
    // ZAP_USAGE_CONTRACT_BRANCH
    {
        const std::streampos usage_pos = in.tellg();
        std::string usage_tok;
        if (in >> usage_tok) {
            in.clear();
            if (usage_pos != std::streampos(-1)) {
                in.seekg(usage_pos);
            }

            const std::string u = textio::up(usage_tok);
            if (u == "USAGE" || u == "HELP" || u == "?") {
                print_zap_usage_contract();
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
        cli::cmdout::print_prefixed_message("ZAP", dottalk::helpdata::MessageId::ZapNoTableOpenText);
        return;
    }

    if (A.memoKind() != xbase::DbArea::MemoKind::NONE) {
        cli::cmdout::print_prefixed_message("ZAP", dottalk::helpdata::MessageId::ZapCannotZapMemoText);
        return;
    }

    std::string orderContainer;
    try { orderContainer = orderstate::orderName(A); } catch (...) {}

    std::string orig_filename = A.filename();

    try { orderstate::clearOrder(A); } catch (...) {}
    try { A.close(); } catch (...) {}

    fs::path origPath = resolve_dbf_slot_path(fs::path(orig_filename));
    if (!textio::ends_with_ci(s8(origPath), ".dbf")) {
        origPath.replace_extension(".dbf");
    }

    if (!fs::exists(origPath)) {
        cli::cmdout::print_prefixed_message(
            "ZAP", dottalk::helpdata::MessageId::ZapFileNotFoundText, {{"path", s8(origPath)}});
        return;
    }

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ZapZappingText, {{"path", s8(origPath)}});

    const fs::path tmpPath = make_temp_path(origPath);
    const fs::path bakPath = make_bak_path(origPath);

    std::ifstream src(origPath, std::ios::binary);
    if (!src) {
        cli::cmdout::print_prefixed_message("ZAP", dottalk::helpdata::MessageId::ZapCannotOpenReadText);
        return;
    }

    std::uint8_t hdr32[32]{};
    src.read(reinterpret_cast<char*>(hdr32), 32);
    if (!src) {
        cli::cmdout::print_prefixed_message("ZAP", dottalk::helpdata::MessageId::ZapFailedReadHeaderText);
        return;
    }

    const std::uint16_t headerLen = read_le16(hdr32 + 8);
    if (headerLen < 33 || headerLen > 4096) {
        cli::cmdout::print_prefixed_message(
            "ZAP", dottalk::helpdata::MessageId::ZapInvalidHeaderLenText,
            {{"len", std::to_string(headerLen)}});
        return;
    }

    std::vector<std::uint8_t> headerBlock(headerLen);
    src.seekg(0, std::ios::beg);
    src.read(reinterpret_cast<char*>(headerBlock.data()), headerLen);
    if (!src) {
        cli::cmdout::print_prefixed_message("ZAP", dottalk::helpdata::MessageId::ZapFailedReadHeaderBlockText);
        return;
    }

    if (headerBlock.back() != 0x0D) {
        cli::cmdout::print_prefixed_message("Warning", dottalk::helpdata::MessageId::ZapHeaderNoTerminatorText);
    }

    src.close();

    set_dbf_last_updated_and_reccount(headerBlock, 0);
    set_x64_ext_record_count(headerBlock, 0);

    std::ofstream out(tmpPath, std::ios::binary | std::ios::trunc);
    if (!out) {
        cli::cmdout::print_prefixed_message(
            "ZAP", dottalk::helpdata::MessageId::ZapCannotCreateTempText, {{"path", s8(tmpPath)}});
        return;
    }

    out.write(reinterpret_cast<const char*>(headerBlock.data()), headerLen);
    if (!out) {
        cli::cmdout::print_prefixed_message("ZAP", dottalk::helpdata::MessageId::ZapFailedWriteHeaderText);
        out.close();
        fs::remove(tmpPath);
        return;
    }

    const char eof_marker = static_cast<char>(0x1A);
    out.write(&eof_marker, 1);
    if (!out) {
        cli::cmdout::print_prefixed_message("ZAP", dottalk::helpdata::MessageId::ZapFailedWriteEofText);
        out.close();
        fs::remove(tmpPath);
        return;
    }

    out.flush();
    out.close();

    std::error_code ec_size;
    fs::resize_file(tmpPath, headerLen + 1, ec_size);

    if (!replace_file_with_backup(origPath, tmpPath, bakPath)) {
        fs::remove(tmpPath);
        return;
    }

    try_mark_index_dirty(orderContainer);

    cli::cmdout::print_message(dottalk::helpdata::MessageId::ZapCompleteText);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ZapReadyForUseText,
        {{"file", origPath.filename().string()}});
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ZapSidecarsNoneText);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ZapReopenText,
        {{"stem", origPath.stem().string()}});
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ZapRebuildIndexesText);
}
