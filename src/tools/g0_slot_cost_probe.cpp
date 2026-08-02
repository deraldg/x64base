// AIF-078 gate G0 -- measure the per-slot cost on the SHIPPING toolchain.
//
// Not a build target and not registered: this is a one-off measurement artifact
// kept with the lane package so the number in
// docs/maintenance/WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_LANE_V1.md sec 2a can be
// re-derived rather than trusted.
//
// The lane's first cap table was measured under g++/libstdc++ x86-64:
//     sizeof(DbArea) = 1088   sizeof(AreaState) = 176   ~1296 B/slot
// x64base is CROSS-PLATFORM, so that is one ROW of the table, not a draft of
// it. MSVC lays out std::string, std::multimap and std::fstream differently and
// will produce a different row; where the two differ, the difference is a
// finding. G0 records both and the cap ruling is made against the worst case
// PER AXIS -- and the axes disagree, because Windows has the smaller default
// stack (1 MB vs 8 MB) while libstdc++ tends to have the smaller structures.
//
// Build and run (either toolchain, through CMake -- no developer shell needed;
// cmake --build sets the compiler environment up itself):
//
//   cmake -S . -B build -DDOTTALK_BUILD_SLOT_COST_PROBE=ON
//   cmake --build build --target g0_slot_cost_probe --config Release
//   .\\build\\Release\\g0_slot_cost_probe.exe          (Windows; drop Release\\ on
//                                                      single-config generators)
//
// Tee the output to a transcript under labtalk/proofs/runs/ -- a proof row must
// cite a tracked artifact (AI_ENGINEERING_STANDARDS_SEED_V1.md sec 5c).

#include <cstdio>
#include <fstream>

#include "xbase.hpp"
#include "cli/table_state.hpp"

int main() {
    const double per_slot =
        static_cast<double>(sizeof(xbase::DbArea)) +
        sizeof(void*) +                                   // _areas[] unique_ptr
        static_cast<double>(sizeof(dottalk::table::AreaState)) +
        16.0 +                                            // workareas::WorkArea
        sizeof(void*);                                    // its owning pointer

    std::printf("AIF-078 G0 -- per-slot cost, this toolchain\n");
#if defined(_MSC_VER)
    std::printf("  toolchain          = MSVC _MSC_VER=%d\n", _MSC_VER);
#else
    std::printf("  toolchain          = non-MSVC\n");
#endif
    std::printf("  sizeof(DbArea)     = %zu\n", sizeof(xbase::DbArea));
    std::printf("  sizeof(AreaState)  = %zu\n", sizeof(dottalk::table::AreaState));
    std::printf("  sizeof(XBaseEngine)= %zu\n", sizeof(xbase::XBaseEngine));
    std::printf("  sizeof(std::fstream)=%zu\n", sizeof(std::fstream));
    std::printf("  MAX_AREA           = %d\n", xbase::MAX_AREA);
    std::printf("  approx bytes/slot  = %.0f\n", per_slot);
    std::printf("\n  cap        resident(idle)   engine stack frame\n");
    for (const int cap : {512, 1024, 4096, 16384, 65536}) {
        std::printf("  %6d   %10.2f MB   %10.1f KB\n",
                    cap,
                    cap * per_slot / 1048576.0,
                    (cap * static_cast<double>(sizeof(void*)) + 8) / 1024.0);
    }
    std::printf("\n  NOTE: the engine is a STACK LOCAL at src/cli/shell.cpp:527 and\n"
                "        no /STACK override exists in the build. Compare the frame\n"
                "        column against the 1 MB MSVC default before raising the cap.\n");
    return 0;
}
