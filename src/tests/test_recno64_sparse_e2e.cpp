// src/tests/test_recno64_sparse_e2e.cpp
//
// RECNO64 M4-5 — the REAL end-to-end boundary proof (the "gumption" test).
//
// Instead of fabricating cursor state, this builds an actual x64 table on disk whose
// record_count is set past 2^31, writes real records at recno 1, 2^31+1, and 2^31+2,
// then reopens it through the engine and confirms gotoRec64() positions to those
// records and reads them DISTINCTLY. The ~19 GB gap between record 1 and record
// 2^31+1 is a SPARSE-FILE hole: the filesystem allocates only the few blocks we
// actually write, so the file's logical size is ~19 GB but its physical footprint is
// a few KB. This is the difference between "the accessor arithmetic is right"
// (test_recno64_boundary) and "the engine really reads a record past 2^31 off disk".
//
// Sparse mechanics: NTFS via FSCTL_SET_SPARSE (Win32); POSIX filesystems (ext4, etc.)
// create holes automatically when you seek past EOF and write.
//
// NOTE: the file will show a ~19 GB *logical* size in a directory listing; its
// on-disk (compressed/allocated) size is tiny. It is removed at start and end.

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xbase/dbf_create.hpp"

#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#  include <winioctl.h>   // FSCTL_SET_SPARSE
#endif

namespace {

// Write n bytes at absolute offset `off`, leaving the preceding gap as a sparse hole.
bool sparse_write_at(const std::string& path, std::uint64_t off,
                     const char* data, std::size_t n) {
#ifdef _WIN32
    HANDLE h = CreateFileA(path.c_str(), GENERIC_READ | GENERIC_WRITE,
                           0, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (h == INVALID_HANDLE_VALUE) return false;
    DWORD br = 0;
    // Idempotent: mark the file sparse before any high-offset write so the gap is a hole.
    DeviceIoControl(h, FSCTL_SET_SPARSE, nullptr, 0, nullptr, 0, &br, nullptr);
    LARGE_INTEGER li; li.QuadPart = static_cast<LONGLONG>(off);
    if (!SetFilePointerEx(h, li, nullptr, FILE_BEGIN)) { CloseHandle(h); return false; }
    DWORD written = 0;
    const BOOL ok = WriteFile(h, data, static_cast<DWORD>(n), &written, nullptr);
    CloseHandle(h);
    return ok && written == n;
#else
    std::FILE* f = std::fopen(path.c_str(), "r+b");
    if (!f) return false;
    const int sk = fseeko(f, static_cast<off_t>(off), SEEK_SET);
    if (sk != 0) { std::fclose(f); return false; }
    const std::size_t w = std::fwrite(data, 1, n, f);
    std::fclose(f);
    return w == n;
#endif
}

} // namespace

int main() {
    const std::uint64_t I32MAX = 2147483647ull;
    const std::uint64_t RA     = I32MAX + 1;   // 2147483648 — first record past 2^31
    const std::uint64_t RB     = I32MAX + 2;   // 2147483649 — a distinct record past 2^31
    const std::uint64_t BIG    = RB;           // record_count = 2^31 + 2

    const std::string path = "recno64_sparse_e2e.dbf";
    std::remove(path.c_str());

    // 1) A valid x64 table with one C(8) field.
    {
        using namespace xbase::dbf_create;
        std::vector<FieldSpec> fields;
        FieldSpec f; f.name = "TAG"; f.type = 'C'; f.len = 8; fields.push_back(f);
        std::string err;
        const bool ok = create_dbf(path, fields, Flavor::X64, err);
        assert(ok && "create_dbf x64 must succeed");
    }

    // 2) Learn the real geometry from the fresh (empty) table.
    std::uint64_t data_start = 0, rec_size = 0;
    {
        xbase::DbArea a;
        a.open(path);
        data_start = a.dataStart64();
        rec_size   = a.recLength64();
        assert(rec_size >= 9 && "x64 C(8) record is at least 1 flag + 8 field bytes");
    }

    auto rec_offset = [&](std::uint64_t recno) {
        return data_start + (recno - 1) * rec_size;   // 64-bit offset math
    };
    auto make_rec = [rec_size](const char* tag8) {
        std::string r(1, ' ');                       // live (not-deleted) flag
        r.append(tag8, 8);                           // 8 field bytes for the C(8) field
        if (r.size() < rec_size) r.append(rec_size - r.size(), ' ');  // pad to full record
        return r;                                    // full record so file end == count*rec_size
    };

    // 3) Patch record_count (little-endian, file offset 32) past 2^31, then write the
    //    three real records into the sparse file.
    {
        unsigned char le[8];
        std::uint64_t v = BIG;
        for (int i = 0; i < 8; ++i) { le[i] = static_cast<unsigned char>(v & 0xFFu); v >>= 8; }
        assert(sparse_write_at(path, 32, reinterpret_cast<const char*>(le), 8) &&
               "patch 64-bit record_count at file offset 32");
    }

    const std::string r1 = make_rec("FIRSTREC");
    const std::string rA = make_rec("PAST31_A");
    const std::string rB = make_rec("PAST31_B");
    assert(sparse_write_at(path, rec_offset(1),  r1.data(), r1.size()) && "write recno 1");
    assert(sparse_write_at(path, rec_offset(RA), rA.data(), rA.size()) && "write recno 2^31+1");
    assert(sparse_write_at(path, rec_offset(RB), rB.data(), rB.size()) && "write recno 2^31+2");

    // 4) Reopen through the engine and prove 64-bit positioning + distinct reads.
    {
        xbase::DbArea a;
        a.open(path);

        assert(a.recCount64() == BIG && "engine must read the 64-bit record count");
        assert(a.recCount()   == -1  && "legacy recCount() must signal 32-bit overflow");

        assert(a.gotoRec64(RA) && a.readCurrent() && "position + read at recno 2^31+1");
        assert(a.recno64() == RA);
        assert(a.recno()   == -1);
        const std::string ga = a.get(1);
        assert(ga.find("PAST31_A") != std::string::npos && "record content at recno 2^31+1");

        assert(a.gotoRec64(RB) && a.readCurrent() && "position + read at recno 2^31+2");
        assert(a.recno64() == RB);
        const std::string gb = a.get(1);
        assert(gb.find("PAST31_B") != std::string::npos && "record content at recno 2^31+2");

        // The decisive result: two records past 2^31 are distinct records on disk,
        // not one saturated INT_MAX slot.
        assert(ga != gb && "records past 2^31 must read distinctly");

        // Sanity: record 1 still resolves.
        assert(a.gotoRec64(1) && a.readCurrent());
        assert(a.get(1).find("FIRSTREC") != std::string::npos);

        std::cout << "recno64_sparse_e2e: read '" << ga << "' at recno " << RA
                  << " and '" << gb << "' at recno " << RB
                  << " from a sparse x64 table (record_count=" << BIG
                  << ", record offset ~" << (rec_offset(RA) / (1024ull * 1024 * 1024))
                  << " GiB). 64-bit on-disk positioning past 2^31 PROVEN. PASS\n";
    }

    std::remove(path.c_str());
    return 0;
}
