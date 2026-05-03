// src/cli/cmd_turbo_pack.cpp
// TURBOPACK — fast, low-level DBF compaction (byte-oriented)
// Removes physically deleted records (* flag) by rewriting only live ones.
//
// Scope / contract:
//   - Fast path for plain DBF tables only.
//   - Memo tables are explicitly refused.
//   - X64 tables are explicitly refused for now.
//
// POLICY (2026):
//   - Structural command (file-level operation)
//   - Leaves table CLOSED on success
//   - User must USE to reopen
//   - Indexes should be rebuilt/rebound after

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <system_error>
#include <vector>

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "cli/order_state.hpp"

#if __has_include("cli/path_resolver.hpp") && __has_include("cli/cmd_setpath.hpp")
  #include "cli/path_resolver.hpp"
  #include "cli/cmd_setpath.hpp"
  #define HAVE_PATHS 1
#else
  #define HAVE_PATHS 0
#endif

namespace {
    namespace fs = std::filesystem;
    using u8  = std::uint8_t;
    using u16 = std::uint16_t;
    using u32 = std::uint32_t;

    inline u16 le16(const u8* p) {
        return u16(p[0]) | (u16(p[1]) << 8);
    }

    inline u32 le32(const u8* p) {
        return u32(p[0]) | (u32(p[1]) << 8) | (u32(p[2]) << 16) | (u32(p[3]) << 24);
    }

    inline void put_le32(u8* p, u32 v) {
        p[0] = u8(v & 0xFF);
        p[1] = u8((v >> 8)  & 0xFF);
        p[2] = u8((v >> 16) & 0xFF);
        p[3] = u8((v >> 24) & 0xFF);
    }

    static std::string s8(const fs::path& p) {
#if defined(_WIN32)
        auto u = p.u8string();
        return std::string(u.begin(), u.end());
#else
        return p.string();
#endif
    }

    static bool ends_with_ci(std::string_view s, std::string_view suf) {
        if (s.size() < suf.size()) return false;
        for (size_t i = 0; i < suf.size(); ++i) {
            if (std::toupper(static_cast<unsigned char>(s[s.size() - suf.size() + i])) !=
                std::toupper(static_cast<unsigned char>(suf[i]))) {
                return false;
            }
        }
        return true;
    }

#if HAVE_PATHS
    namespace paths = dottalk::paths;
    static fs::path dbf_root() {
        try { return paths::get_slot(paths::Slot::DBF); }
        catch (...) { return fs::current_path(); }
    }
#else
    static fs::path dbf_root() { return fs::current_path(); }
#endif

    static fs::path resolve_dbf_slot(const fs::path& p) {
        if (p.is_absolute()) return p;
        return fs::weakly_canonical(dbf_root() / p);
    }

    static fs::path temp_target_for(const fs::path& src) {
        auto dir = src.parent_path();
        auto stem = src.stem().string();
        auto ext = src.extension().string();
        return dir / (stem + ".turbo.tmp" + ext);
    }

    static std::optional<fs::path> derive_current_dbf_path(xbase::DbArea& A) {
        if (!A.filename().empty()) {
            return fs::weakly_canonical(fs::path(A.filename()));
        }

        std::string base = A.dbfBasename();
        if (base.empty()) base = A.logicalName();
        if (base.empty()) return std::nullopt;

        fs::path guess = resolve_dbf_slot(base + ".dbf");
        if (fs::exists(guess) && fs::is_regular_file(guess)) return guess;

        std::string lower = base;
        std::transform(lower.begin(), lower.end(), lower.begin(),
                       [](unsigned char c){ return std::tolower(c); });
        guess = resolve_dbf_slot(lower + ".dbf");
        if (fs::exists(guess) && fs::is_regular_file(guess)) return guess;

        return std::nullopt;
    }

    static void update_header_timestamp_and_count(std::string& header, u32 new_count) {
        if (header.size() < 32) return;

        std::time_t now = std::time(nullptr);
        std::tm tmv{};
    #if defined(_WIN32)
        localtime_s(&tmv, &now);
    #else
        tmv = *std::localtime(&now);
    #endif

        u8 yy = static_cast<u8>(tmv.tm_year % 100);
        u8 mm = static_cast<u8>(tmv.tm_mon + 1);
        u8 dd = static_cast<u8>(tmv.tm_mday);

        header[1] = static_cast<char>(yy);
        header[2] = static_cast<char>(mm);
        header[3] = static_cast<char>(dd);

        put_le32(reinterpret_cast<u8*>(&header[4]), new_count);
    }

    static bool compute_safe_record_count(const fs::path& srcP,
                                          u16 headerLen,
                                          u16 recLen,
                                          u32 headerCount,
                                          u32& actualCount,
                                          u32& safeCount,
                                          std::string& err)
    {
        actualCount = 0;
        safeCount = 0;
        err.clear();

        std::error_code ec;
        const auto fileSize = fs::file_size(srcP, ec);
        if (ec) {
            err = "failed to get file size: " + ec.message();
            return false;
        }

        if (fileSize < headerLen) {
            err = "file is smaller than header length";
            return false;
        }

        std::uintmax_t payload = fileSize - static_cast<std::uintmax_t>(headerLen);

        if (payload > 0) {
            std::ifstream tail(srcP, std::ios::binary);
            if (tail) {
                tail.seekg(static_cast<std::streamoff>(fileSize - 1), std::ios::beg);
                char last = 0;
                tail.read(&last, 1);
                if (tail && static_cast<unsigned char>(last) == 0x1A) {
                    --payload;
                }
            }
        }

        actualCount = static_cast<u32>(payload / recLen);
        safeCount   = std::min(headerCount, actualCount);
        return true;
    }
}

void cmd_TURBOPACK(xbase::DbArea& A, std::istringstream& /*S*/)
{
    using namespace std;

    if (!A.isOpen()) {
        cout << "TURBOPACK: No table open.\n";
        return;
    }

    if (A.memoKind() != xbase::DbArea::MemoKind::NONE) {
        cout << "TURBOPACK: Memo tables not supported. Use PACK instead.\n";
        return;
    }

    if (A.versionByte() == xbase::DBF_VERSION_64) {
        cout << "TURBOPACK: X64 tables not supported. Use PACK instead.\n";
        return;
    }

    auto srcOpt = derive_current_dbf_path(A);
    if (!srcOpt) {
        cout << "TURBOPACK: Cannot determine DBF file path.\n";
        return;
    }

    fs::path srcP = *srcOpt;
    string srcStr = s8(srcP);

    if (!ends_with_ci(srcStr, ".dbf")) {
        cout << "TURBOPACK: Not a .dbf file: " << srcStr << "\n";
        return;
    }

    if (!fs::exists(srcP) || !fs::is_regular_file(srcP)) {
        cout << "TURBOPACK: File not found: " << srcStr << "\n";
        return;
    }

    string origOrder;
    try { origOrder = orderstate::orderName(A); } catch (...) {}

    try { orderstate::clearOrder(A); } catch (...) {}
    try { A.close(); } catch (...) {}

    cout << "TURBOPACK processing: " << srcStr << "\n";

    ifstream in(srcStr, ios::binary);
    if (!in) {
        cout << "TURBOPACK: Cannot open source file.\n";
        return;
    }

    u8 hdr32[32]{};
    in.read(reinterpret_cast<char*>(hdr32), 32);
    if (!in) {
        cout << "TURBOPACK: Cannot read header.\n";
        in.close();
        return;
    }

    u16 headerLen = le16(&hdr32[8]);
    u16 recLen    = le16(&hdr32[10]);
    u32 origCount = le32(&hdr32[4]);

    if (headerLen < 33 || recLen < 1 || headerLen > 4096) {
        cout << "TURBOPACK: Invalid header lengths.\n";
        in.close();
        return;
    }

    u32 actualCount = 0;
    u32 safeCount   = 0;
    string safeErr;
    if (!compute_safe_record_count(srcP, headerLen, recLen, origCount,
                                   actualCount, safeCount, safeErr)) {
        cout << "TURBOPACK: " << safeErr << "\n";
        in.close();
        return;
    }

    string header(headerLen, '\0');
    in.seekg(0, ios::beg);
    in.read(&header[0], headerLen);
    if (!in || static_cast<unsigned char>(header.back()) != 0x0D) {
        cout << "TURBOPACK: Invalid or incomplete header (missing 0x0D terminator).\n";
        in.close();
        return;
    }

    if (origCount != actualCount) {
        cout << "TURBOPACK: Warning — header count (" << origCount
             << ") does not match physical count (" << actualCount
             << "); using safe count " << safeCount << ".\n";
    }

    if (safeCount == 0 && origCount > 0) {
        cout << "TURBOPACK: Warning — no valid physical records detected; table may be corrupt.\n";
    }

    in.seekg(static_cast<std::streamoff>(headerLen), ios::beg);

    fs::path tmpP = temp_target_for(srcP);
    ofstream out(s8(tmpP), ios::binary | ios::trunc);
    if (!out) {
        cout << "TURBOPACK: Cannot create temp file " << s8(tmpP) << "\n";
        in.close();
        return;
    }

    update_header_timestamp_and_count(header, 0);
    out.write(header.data(), headerLen);
    if (!out) {
        cout << "TURBOPACK: Failed writing header to temp.\n";
        out.close();
        in.close();
        fs::remove(tmpP);
        return;
    }

    vector<char> rec(recLen);
    u32 kept = 0;

    for (u32 i = 0; i < safeCount; ++i) {
        in.read(rec.data(), recLen);
        if (!in) {
            cout << "TURBOPACK: Read error at source record " << (i + 1)
                 << " after " << kept << " kept records.\n";
            out.close();
            in.close();
            fs::remove(tmpP);
            return;
        }

        if (static_cast<u8>(rec[0]) != xbase::IS_DELETED) {
            rec[0] = xbase::NOT_DELETED;
            out.write(rec.data(), recLen);
            if (!out) {
                cout << "TURBOPACK: Write error after " << kept << " kept records.\n";
                out.close();
                in.close();
                fs::remove(tmpP);
                return;
            }
            ++kept;
        }
    }

    in.close();

    update_header_timestamp_and_count(header, kept);
    out.seekp(0, ios::beg);
    out.write(header.data(), headerLen);
    if (!out) {
        cout << "TURBOPACK: Failed to update header with final count.\n";
        out.close();
        fs::remove(tmpP);
        return;
    }

    char eofc = char(0x1A);
    out.write(&eofc, 1);
    out.flush();
    out.close();

    auto expected_size = uint64_t(headerLen) + uint64_t(kept) * recLen + 1;
    error_code ec_trunc;
    fs::resize_file(tmpP, expected_size, ec_trunc);

    fs::path bakP = srcP;
    bakP.replace_extension(".turbo.bak");

    error_code ec;
    fs::remove(bakP, ec);

    fs::rename(srcP, bakP, ec);
    if (ec) {
        cout << "TURBOPACK: Cannot create backup: " << ec.message() << "\n";
        fs::remove(tmpP);
        return;
    }

    fs::rename(tmpP, srcP, ec);
    if (ec) {
        cout << "TURBOPACK: Cannot replace original file: " << ec.message() << "\n";
        error_code ec2;
        fs::rename(bakP, srcP, ec2);
        if (ec2) {
            cout << "  Rollback also failed. Original may be lost.\n";
        }
        return;
    }

    fs::remove(bakP, ec);

    cout << "TURBOPACK complete. Kept " << kept << " of " << origCount << " records.\n";
    cout << srcP.filename().string() << " ready for use.\n";
    cout << "Sidecar(s): none.\n";
    cout << "Table is closed. Reopen with: USE " << srcP.stem().string() << "\n";
    if (!origOrder.empty()) {
        cout << "Reindex recommended. Previous order '" << origOrder << "' detached.\n";
    } else {
        cout << "Reindex recommended.\n";
    }
}