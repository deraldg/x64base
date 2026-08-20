// AIF-120 R63 -- does the lane's LOCK path work at a record number past 2^31?
//
// Build and run (needs the engine archives; creates a 19 GB LOGICAL file that
// occupies 8 KB on disk -- the gap is a sparse hole):
//
//   B=build/wsl-core-vcpkg
//   g++ -std=c++17 -Iinclude -I$B/generated gui/uidef/lock_boundary_probe.cpp \
//       $B/src/xbase/libxbase.a $B/src/memo/libmemo.a $B/src/xexpr/libxexpr.a \
//       $B/src/libdottalk_value.a $B/src/libdottalk_inx_payload.a -o /tmp/b31 -pthread
//   /tmp/b31
//
// On a filesystem without sparse-file support this would try to allocate 19 GB.
//
// R57 chose a.recno64() over a.recno() from a header comment. This proves it, and
// the proof is visible rather than inferred: xbase::locks NAMES the lock file after
// the record number, so a wrong accessor writes `.lock.-1` on disk.
//
// The fixture is built the ENGINE'S way -- create_dbf(Flavor::X64) and the 64-bit
// record_count at file offset 32 -- following src/tests/test_recno64_sparse_e2e.cpp.
// An earlier attempt patched the CLASSIC count at bytes 4-7 of a VFP-flavour table
// and read back zero (R61.5): wrong field, wrong flavour, invalid fixture.
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase_locks.hpp"
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

static bool sparse_write_at(const std::string& p, std::uint64_t off,
                            const char* d, std::size_t n) {
    std::FILE* f = std::fopen(p.c_str(), "r+b");
    if (!f) return false;
    if (fseeko(f, (off_t)off, SEEK_SET) != 0) { std::fclose(f); return false; }
    const std::size_t w = std::fwrite(d, 1, n, f);
    std::fclose(f);
    return w == n;
}

int main() {
    const std::uint64_t I32MAX = 2147483647ull;
    const std::uint64_t RA = I32MAX + 1;      // 2147483648
    const std::uint64_t RB = I32MAX + 2;      // 2147483649
    const std::string path = "/tmp/r63_sparse.dbf";
    std::remove(path.c_str());

    {   using namespace xbase::dbf_create;
        std::vector<FieldSpec> fields;
        FieldSpec f; f.name = "TAG"; f.type = 'C'; f.len = 8; fields.push_back(f);
        std::string err;
        if (!create_dbf(path, fields, Flavor::X64, err)) {
            std::printf("create_dbf FAILED: %s\n", err.c_str()); return 2; }
    }
    std::uint64_t ds = 0, rs = 0;
    { xbase::DbArea a; a.open(path); ds = a.dataStart64(); rs = a.recLength64(); }
    auto off = [&](std::uint64_t r) { return ds + (r - 1) * rs; };
    auto rec = [rs](const char* t) {
        std::string r(1, ' '); r.append(t, 8);
        if (r.size() < rs) r.append(rs - r.size(), ' ');
        return r; };

    {   unsigned char le[8]; std::uint64_t v = RB;
        for (int i = 0; i < 8; ++i) { le[i] = (unsigned char)(v & 0xFF); v >>= 8; }
        if (!sparse_write_at(path, 32, (const char*)le, 8)) { std::printf("patch FAILED\n"); return 2; } }
    const std::string r1 = rec("FIRSTREC"), rA = rec("PAST31_A"), rB = rec("PAST31_B");
    sparse_write_at(path, off(1),  r1.data(), r1.size());
    sparse_write_at(path, off(RA), rA.data(), rA.size());
    sparse_write_at(path, off(RB), rB.data(), rB.size());

    xbase::DbArea a;
    a.open(path);
    std::printf("recCount64() : %llu\n", (unsigned long long)a.recCount64());
    std::printf("recCount()   : %d   <-- legacy signals overflow\n", a.recCount());
    if (!a.gotoRec64(RA)) { std::printf("gotoRec64(%llu) FAILED\n", (unsigned long long)RA); return 2; }
    std::printf("gotoRec64(%llu): recno64()=%llu  recno()=%d\n",
                (unsigned long long)RA, (unsigned long long)a.recno64(), a.recno());

    std::string err;
    const bool ok = xbase::locks::try_lock_record(
        a, a.recno64(), xbase::locks::current_owner(), &err);
    std::printf("\ntry_lock_record(recno64()) : %s%s\n", ok ? "ok" : "FAILED ", err.c_str());
    // Sequenced. R57 correction 38 was exactly this, and I wrote it into a ruling
    // and then did it again here -- argument evaluation order is unspecified, so
    // who.c_str() ran before the call that fills `who`.
    std::string who;
    const bool held = xbase::locks::is_record_locked(a, a.recno64(), &who);
    std::printf("is_record_locked(recno64()): %s (%s)\n", held ? "yes" : "NO", who.c_str());
    std::printf("\n  the lock file the engine created is named after the record number.\n");
    std::printf("  correct  : %s.lock.%llu\n", path.c_str(), (unsigned long long)a.recno64());
    std::printf("  recno()  : %s.lock.%d   <-- what R57 would have written\n", path.c_str(), a.recno());
    xbase::locks::unlock_record(a, a.recno64(), xbase::locks::current_owner(), &err);
    return 0;
}
