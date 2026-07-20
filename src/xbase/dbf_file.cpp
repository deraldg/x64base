// File: src/xbase/dbf_file.cpp
// Purpose: DBF open/read/write/runtime-flavor plumbing for the core xBase
//          engine.
// Boundary: This unit owns physical table behavior; command messaging, help
//           text, and shell policy belong above the engine layer.
// Notes: ASCII only.

#include "xbase.hpp"
#include "xbase_vfp.hpp"
#include "xbase_64.hpp"
// NOTE: removed "utils.hpp" include to avoid current header parser issue

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstddef>
#include <cerrno>
#include <filesystem>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#endif

#include "xbase/index_hooks.hpp"

namespace xbase {

// --- local, self-contained ends_with_ci (so we don't need utils.hpp right now)
static inline bool ends_with_ci_local(const std::string& s, const std::string& suf) noexcept {
    if (s.size() < suf.size()) return false;
    const size_t off = s.size() - suf.size();
    for (size_t i = 0; i < suf.size(); ++i) {
        const unsigned char a_uc = static_cast<unsigned char>(s[off + i]);
        const unsigned char b_uc = static_cast<unsigned char>(suf[i]);
        const int a = std::tolower(static_cast<int>(a_uc));
        const int b = std::tolower(static_cast<int>(b_uc));
        if (a != b) return false;
    }
    return true;
}

static inline std::size_t checked_record_buffer_size_(const DbArea& area)
{
    const auto len64 = area.recLength64();
    if (len64 == 0 ||
        len64 > static_cast<std::uint64_t>(std::numeric_limits<std::size_t>::max())) {
        throw std::runtime_error("DbArea: record length exceeds addressable buffer size");
    }
    if (len64 > X64_MAX_RECORD_SIZE) {
        throw std::runtime_error("DbArea: record length exceeds maximum record size");
    }
    return static_cast<std::size_t>(len64);
}

static inline std::streampos checked_record_pos_(const DbArea& area, std::uint64_t recno64)
{
    if (recno64 < 1) {
        throw std::runtime_error("DbArea: invalid record number");
    }

    const auto data_start = area.dataStart64();
    const auto rec_len = area.recLength64();
    const auto row_index = recno64 - 1;

    if (rec_len != 0 &&
        row_index > ((std::numeric_limits<std::uint64_t>::max() - data_start) / rec_len)) {
        throw std::runtime_error("DbArea: record offset overflow");
    }

    const auto offset64 = data_start + row_index * rec_len;
    if (offset64 > static_cast<std::uint64_t>(std::numeric_limits<std::streamoff>::max())) {
        throw std::runtime_error("DbArea: record offset exceeds stream range");
    }

    return static_cast<std::streampos>(static_cast<std::streamoff>(offset64));
}

// ---- helpers exposed in header ----
std::string dbNameWithExt(std::string s) {
    while (!s.empty() && s.back() == ' ') s.pop_back();
    if (!ends_with_ci_local(s, ".dbf")) s += ".dbf";
    return s;
}

// ---- DbArea: file/open/structure/navigation ----

void DbArea::open(const std::string& filename)
{
    close();

    namespace fs = std::filesystem;

    fs::path p(filename);
    if (!p.is_absolute()) p = fs::absolute(p);

    // Normalize without full canonicalization.
    const fs::path norm = p.lexically_normal();
    const std::string abs = norm.string();

    if (!fs::exists(norm)) {
        throw std::runtime_error("DbArea: file does not exist: " + abs);
    }
    if (!fs::is_regular_file(norm)) {
        throw std::runtime_error("DbArea: not a regular file: " + abs);
    }

    const auto sz = fs::file_size(norm);
    if (sz < static_cast<std::uintmax_t>(sizeof(HeaderRec))) {
        throw std::runtime_error("DbArea: invalid DBF header (file too small): " + abs);
    }

    // Canonical contract (xbase.hpp): compute + store absolute DBF path + derived names.
    _compute_paths_and_names_(abs);

    // Open using the canonical absolute path (single source of truth).
    // IMPORTANT: Do not auto-create files here. USE/OPEN must never create files.
    _fp.clear();
    errno = 0;
    _fp.open(_dbf_abs_path, std::ios::in | std::ios::out | std::ios::binary);
    if (!_fp.is_open()) {
        std::string detail = "DbArea: cannot open file (access denied/locked?): " + _dbf_abs_path;
        if (errno != 0) {
            detail += " errno=" + std::to_string(errno);
        }
#ifdef _WIN32
        const fs::path winp(_dbf_abs_path);
        HANDLE h = ::CreateFileW(
            winp.c_str(),
            GENERIC_READ | GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            nullptr,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            nullptr);
        if (h == INVALID_HANDLE_VALUE) {
            detail += " gle=" + std::to_string(::GetLastError());
        } else {
            detail += " createfile=ok";
            ::CloseHandle(h);
        }
#endif
        throw std::runtime_error(detail);
    }

    readHeader();
    readFields();

    // Enforce single runtime source of truth for record count.
    // Classic/VFP tables use the 32-bit compatible header count.
    // x64 tables have already loaded the authoritative 64-bit count in
    // x64_loader::readHeader(); do not collapse it back to the 32-bit mirror.
    if (_hdr.num_of_recs < 0) {
        _rec_count64 = 0;
        _hdr.num_of_recs = 0;
    } else if (_dbf_version_byte != DBF_VERSION_64) {
        _rec_count64 = static_cast<std::uint64_t>(_hdr.num_of_recs);
    }

    _recbuf.assign(checked_record_buffer_size_(*this), ' ');

    // 1-based field values
    _fd.assign(_fields.size() + 1, std::string{});
    _fd_snapshot.assign(_fields.size() + 1, std::string{});

    // Fresh open must not inherit any externally attached index state.
    index_hooks::detach(*this);

    // Start at record 1 if non-empty; otherwise remain at BOF.
    if (_rec_count64 > 0) {
        _crn64 = 1;
        _crn = 1;
        if (!readCurrent()) {
            throw std::runtime_error("DbArea: failed to read first record after open: " + _dbf_abs_path);
        }
    } else {
        _crn = 0;
        _crn64 = 0;
        _del = NOT_DELETED;
    }
}

void DbArea::readHeader()
{
    if (!_fp.is_open()) {
        throw std::runtime_error("DbArea: file not open in readHeader");
    }

    _fp.clear();
    _fp.seekg(0, std::ios::beg);

    const std::uint8_t ver = vfp_loader::peekVersion(_fp);

    if (ver == DBF_VERSION_64) {
        x64_loader::readHeader(*this, _fp);
        return;
    }

    // Use the VFP/legacy loader for classic, Fox26, and VFP DBFs.
    vfp_loader::readHeader(*this, _fp);
}

void DbArea::readFields()
{
    if (!_fp.is_open()) {
        throw std::runtime_error("DbArea: file not open in readFields");
    }

    _fp.clear();
    _fp.seekg(0, std::ios::beg);

    const std::uint8_t ver = vfp_loader::peekVersion(_fp);
    std::vector<VfpFieldExtras> extras;

    if (ver == DBF_VERSION_64) {
        x64_loader::readFields(*this, _fp, extras);
        return;
    }

    // Current vfp_loader::readFields() contract:
    // caller positions the stream just after the 32-byte header.
    // This applies to classic (0x03/0x83/0xF5) and VFP (0x30/0x31/0x32),
    // since both use 32-byte headers in the current implementation.
    _fp.seekg(sizeof(HeaderRec), std::ios::beg);
    vfp_loader::readFields(*this, _fp, extras);

    // extras currently remain loader-local by design.
    // If/when VFP nullable/binary/autoinc metadata becomes first-class runtime
    // state, store them on DbArea here rather than re-parsing elsewhere.
}

// Authoritative 64-bit record positioning (RECNO64). Offset math is already
// 64-bit (checked_record_pos_); this removes the int32 gate on the entry point.
bool DbArea::gotoRec64(std::uint64_t recno) {
    if (recno < 1) return false;
    if (recno > _rec_count64) return false;

    _crn64 = recno;
    // Keep the legacy 32-bit mirror honest: exact when it fits, clamped (never
    // silently wrong past the boundary — x64 callers read _crn64/recno64()).
    _crn = (recno > static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max()))
        ? std::numeric_limits<int32_t>::max()
        : static_cast<int32_t>(recno);

    const std::streampos pos = checked_record_pos_(*this, recno);

    _fp.seekg(pos, std::ios::beg);
    return readCurrent();
}

// 32-bit compatibility adapter. Correct for classic/VFP (format-bounded to a
// 32-bit count); for x64 tables prefer gotoRec64.
bool DbArea::gotoRec(int32_t recno) {
    if (recno < 1) return false;
    return gotoRec64(static_cast<std::uint64_t>(recno));
}

bool DbArea::top() {
    if (_rec_count64 == 0) return false;
    return gotoRec(1);
}

bool DbArea::bottom() {
    if (_rec_count64 == 0) return false;
    return gotoRec64(_rec_count64);
}

bool DbArea::skip(int delta) {
    if (_crn64 == 0) return false;

    const std::int64_t want64 = static_cast<std::int64_t>(_crn64) + static_cast<std::int64_t>(delta);
    if (want64 < 1) return false;
    if (static_cast<std::uint64_t>(want64) > _rec_count64) return false;

    return gotoRec64(static_cast<std::uint64_t>(want64));
}

bool DbArea::appendBlank() {
    // Empty freshly-opened tables can leave the stream in fail/eof state because
    // open() positions to BOF when num_of_recs == 0.
    _fp.clear();

    std::vector<char> blank(checked_record_buffer_size_(*this), ' ');
    blank[0] = NOT_DELETED;

    // For an empty DBF created with a trailing 0x1A EOF marker, append should
    // overwrite that marker with the new record and then write a new EOF marker.
    _fp.seekg(0, std::ios::end);
    const std::streamoff fileSize = _fp.tellg();

    std::streamoff recPos = fileSize;

    if (fileSize > 0) {
        char last = 0;
        _fp.seekg(fileSize - 1, std::ios::beg);
        _fp.read(&last, 1);
        _fp.clear();

        if (static_cast<unsigned char>(last) == 0x1A) {
            recPos = fileSize - 1;
        }
    }

    _fp.seekp(recPos, std::ios::beg);
    _fp.write(blank.data(), static_cast<std::streamsize>(blank.size()));

    const char eof = static_cast<char>(0x1A);
    _fp.write(&eof, 1);

    if (!_fp) return false;

    // Runtime truth first.
    ++_rec_count64;

    // Mirror into legacy 32-bit field where possible.
    if (_rec_count64 > static_cast<std::uint64_t>(std::numeric_limits<int32_t>::max())) {
        _hdr.num_of_recs = std::numeric_limits<int32_t>::max();
    } else {
        _hdr.num_of_recs = static_cast<int32_t>(_rec_count64);
    }

    // Do not rewrite the entire 32-byte header through HeaderRec for VFP/x64.
    // That would clobber dialect-specific tail bytes.
    // Patch the common 32-bit record count at offset 4.
    _fp.clear();
    _fp.seekp(4, std::ios::beg);
    _fp.write(reinterpret_cast<const char*>(&_hdr.num_of_recs), sizeof(_hdr.num_of_recs));

    // x64 dialect also keeps the authoritative record count in the extension block
    // immediately after the 32-byte VFP-style header.
    if (_dbf_version_byte == DBF_VERSION_64) {
        const std::uint64_t rc64 = _rec_count64;
        _fp.seekp(static_cast<std::streamoff>(sizeof(VfpHeader)) +
                      static_cast<std::streamoff>(offsetof(LargeHeaderExtension, record_count)),
                  std::ios::beg);
        _fp.write(reinterpret_cast<const char*>(&rc64), sizeof(rc64));
    }

    _fp.flush();

    if (!_fp) return false;

    _fp.clear();

    // Defensive reset: do not let the previous current record leak into the
    // newly appended blank row if the decode path is imperfect.
    _recbuf.assign(checked_record_buffer_size_(*this), ' ');
    _fd.assign(_fields.size() + 1, std::string{});
    _fd_snapshot.assign(_fields.size() + 1, std::string{});
    _del = NOT_DELETED;

    const bool ok = gotoRec64(_rec_count64);

    // NOTE:
    // DbArea should not perform command-policy index mutation on its own.
    // APPEND/DELETE/RECALL lifecycle belongs to command/index-management policy.
    // Keep DbArea focused on table/session truth.

    return ok;
}

bool DbArea::deleteCurrent() {
    if (_crn64 == 0) return false;
    _del = IS_DELETED;

    // NOTE:
    // DbArea no longer updates indexes implicitly here.
    // Higher-level command paths own index mutation policy.
    return writeCurrent();
}

XBaseEngine::XBaseEngine() {
    for (auto& p : _areas) p = std::make_unique<DbArea>();
}

} // namespace xbase
