// @dottalk.file v1
// subsystem: tools
// layer: test
// owns:
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

// gui/uidef/wx_stream_harness.cpp -- AIF-120 R70.
//
// A generated `--stream` frontend needs exactly ONE thing from its host that it
// cannot declare for itself: the engine. `src/cli/db_tuple_stream.cpp` reaches the
// open work areas through
//
//     extern "C" xbase::XBaseEngine* shell_engine();
//
// which `src/cli/shell.cpp` defines. Linking shell.cpp into a GUI would drag in the
// whole REPL, so a wx host supplies the same seam itself. This file is the smallest
// honest version of that host: it defines the seam and opens the two tables the
// FRAMEDEMO document's SOURCE declares -- the exact equivalent of
//
//     SELECT 1 / USE STUDENTS / SELECT 2 / USE ENROLL
//
// in the shell. The RELATION is deliberately NOT set here: R70.5 is the finding
// that the relation must come from the document, and the generated file emits it
// through relations_api. A harness that set it would hide the defect this file
// exists to have exposed.
//
// This is glue of the kind the charter allows: it CALLS the house surface rather
// than re-deriving it. Nothing here reimplements a spec parser, a cursor or a lock.
//
// Build (see AIF120_GRID_STREAM_BINDING_V1.md section 5c for the object closure):
//     R70_DBF=<dir with STUDENTS.dbf and ENROLL.dbf> ./framedemo_stream

#include <cstdlib>
#include <iostream>
#include <string>

#include "xbase.hpp"

static xbase::XBaseEngine* g_eng = nullptr;

extern "C" xbase::XBaseEngine* shell_engine() { return g_eng; }

extern "C" void r70_open_source(const char* dir)
{
    static xbase::XBaseEngine eng;
    g_eng = &eng;
    const std::string d(dir);
    try {
        eng.selectArea(0);
        eng.area(0).open(d + "/STUDENTS.dbf");
        eng.selectArea(1);
        eng.area(1).open(d + "/ENROLL.dbf");
        eng.selectArea(0);
        std::cout << "r70_harness: STUDENTS recs=" << eng.area(0).recCount64()
                  << "  ENROLL recs=" << eng.area(1).recCount64() << "\n";
    } catch (const std::exception& e) {
        std::cout << "r70_harness: open failed: " << e.what() << "\n";
    }
}

namespace {
// Static init runs before wxApp::OnInit, which is where the generated file
// constructs its streams. R70_DBF names the directory the shell would have
// reached through SET PATH DBF.
struct R70Boot {
    R70Boot() {
        const char* d = std::getenv("R70_DBF");
        if (d && *d) r70_open_source(d);
    }
} g_r70_boot;
} // namespace
