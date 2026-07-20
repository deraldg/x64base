// src/tests/test_x64_record_limit.cpp
//
// Proves the X64_MAX_RECORD_SIZE (16 MiB) hard guard rejects an over-ceiling
// record at CREATE time. This is the path the .dts limits canaries CANNOT reach:
// the CLI CREATE parser caps an X64 C field at 4096 bytes (~512 KiB max record),
// so only a direct create_dbf() call can drive the record width past 16 MiB.
//
// Complements dottalkpp/data/scripts/limits/limits_record_advisory_shakedown.dts
// (which proves the 64 KiB soft advisory, the CLI-reachable half).

#include <cassert>
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

#include "xbase/dbf_create.hpp"
#include "xbase.hpp"   // xbase::X64_MAX_RECORD_SIZE

int main() {
    using namespace xbase::dbf_create;

    // --- Case 1: a single C field wider than the 16 MiB ceiling must be rejected.
    {
        std::vector<FieldSpec> fields;
        FieldSpec big;
        big.name = "BIG";
        big.type = 'C';
        big.len  = static_cast<std::uint32_t>(xbase::X64_MAX_RECORD_SIZE) + 4096u;
        fields.push_back(big);

        std::string err;
        const bool ok = create_dbf("x64_record_limit_over.dbf", fields, Flavor::X64, err);

        assert(!ok && "create_dbf must reject a record over X64_MAX_RECORD_SIZE");
        assert(err.find("maximum") != std::string::npos &&
               "rejection error should mention the maximum");
        std::cout << "x64_record_limit: over-ceiling rejected -> " << err << "\n";

        // Guard fires before any file is written; nothing to clean, but be safe.
        std::remove("x64_record_limit_over.dbf");
    }

    // --- Case 2 (control): a modest record must still create successfully.
    {
        std::vector<FieldSpec> fields;
        FieldSpec a; a.name = "A"; a.type = 'C'; a.len = 50; fields.push_back(a);

        std::string err;
        const bool ok = create_dbf("x64_record_limit_ok.dbf", fields, Flavor::X64, err);

        assert(ok && "a small x64 record must still create");
        std::cout << "x64_record_limit: control record created OK\n";

        std::remove("x64_record_limit_ok.dbf");
    }

    std::cout << "x64_record_limit: PASS\n";
    return 0;
}
