// @dottalk.file v1
// subsystem: tests
// layer: test
// owns:
// project: project.x64base.runtime
// lane: AIF-078
// owner: member.derald
// status: supported

// src/tests/test_area_alloc.cpp
//
// THE FIRST FIXTURE THE IN FREE POLICY HAS EVER HAD.
//
// `find_free_area_for_workspace` was a `static` inside cmd_use.cpp that called
// shell_engine() and the process-global membership table. Nothing could reach
// it, so its two owner rulings -- "scoped" and "keep the areas contiguous" --
// were enforced only by whichever .dts script happened to exercise USE IN FREE
// with two workspaces open, which is to say by nothing. AIF-078 slot lane step
// 1 lifted it into workarea_util and made the engine, the table and the handle
// PARAMETERS. This file is what that buys.
//
// THE DISCRIMINATOR IS ARM A. A naive lowest-free sweep and the workspace-scoped
// policy return DIFFERENT NUMBERS there -- 2 versus 7 -- so the arm fails if the
// scoping is ever lost. Every other arm here would pass under either policy and
// says so where that is true.
//
// Uses its own WorkspaceTable rather than the process default, which is the
// other half of what step 1 bought: the policy now reads the table it is handed.

#include <cassert>
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase/workspace_membership.hpp"

#include "workarea_util.hpp"

// THIS BINARY IS ITS OWN SHELL. Two symbols the CLI layer expects from the
// shell process are supplied here rather than by linking the shell:
//
//   shell_engine()  -- returns NULL ON PURPOSE. Every arm below passes its
//                      engine EXPLICITLY, so a null process engine proves no
//                      arm is quietly falling back on a global. It is also what
//                      arm E asserts against. workareas_engine_bridge.cpp
//                      forwards workareas::shell_engine() to this, so that
//                      indirection is the real tree code, not a stub.
//
//   cmdout::print_line() -- INERT. workarea_util.cpp announces an ambiguous
//                      name resolution through it. Linking the real one drags
//                      in OutputRouter, dottalk::doc and helpdata for a
//                      function no arm here reaches. Nothing in this file
//                      resolves a name, so an inert sink is honest: if an arm
//                      ever starts printing, that is a fact this test would be
//                      hiding, and the assertion above it would have to change
//                      anyway.
extern "C" xbase::XBaseEngine* shell_engine() { return nullptr; }

namespace cli { namespace cmdout { void print_line(const std::string&) {} } }

namespace {

const char* kDbf = "area_alloc_test.dbf";

void make_table() {
    using namespace xbase::dbf_create;
    std::vector<FieldSpec> fields;
    FieldSpec f; f.name = "A"; f.type = 'C'; f.len = 8;
    fields.push_back(f);
    std::string err;
    const bool ok = create_dbf(kDbf, fields, Flavor::MSDOS, err);
    assert(ok && "fixture table must create");
    (void)ok;
}

void occupy(xbase::XBaseEngine& eng, int slot) {
    eng.area(slot).open(kDbf);
    assert(eng.area(slot).isOpen() && "fixture slot must report open");
}

} // namespace

int main() {
    namespace ws = xbase::workspace;

    make_table();

    xbase::XBaseEngine eng;

    // Engine state: slots 0, 1, 5, 6 taken. The LOWEST free slot is 2, and that
    // number is the whole point -- it is the wrong answer for a workspace whose
    // block starts at 5.
    occupy(eng, 0);
    occupy(eng, 1);
    occupy(eng, 5);
    occupy(eng, 6);

    ws::WorkspaceTable table;
    const std::uint64_t h = table.create("BLOCK_AT_FIVE");
    assert(table.join(h, 5) == 0);
    assert(table.join(h, 6) == 1);

    bool broke = true;   // seeded WRONG so a function that never writes it fails

    // --- Arm A. GROW MY OWN BLOCK. -----------------------------------------
    // THE DISCRIMINATOR. Lowest-free would say 2, which sits inside another
    // workspace's run. Scoped-and-contiguous says 7.
    {
        const int got = cli::find_free_area_for_workspace(&eng, table, h, broke);
        assert(got == 7  && "contiguous growth must extend this workspace's own block");
        assert(got != 2  && "a lowest-free sweep would have returned 2 -- scoping lost");
        assert(!broke    && "growing contiguously is not a contiguity break");
        std::cout << "area_alloc A: block {5,6} grew to " << got
                  << " (a lowest-free sweep would have said 2)\n";
    }

    // --- Arm B. BOXED IN, AND IT SAYS SO. ----------------------------------
    // With 7 taken the block cannot grow. The fallback is legal, but it is a
    // BROKEN INVARIANT and the flag is how the caller gets to announce it.
    {
        occupy(eng, 7);
        broke = false;   // seeded WRONG in the other direction for this arm
        const int got = cli::find_free_area_for_workspace(&eng, table, h, broke);
        assert(got == 2 && "boxed in, fall back to the lowest free slot anywhere");
        assert(broke    && "a non-contiguous placement MUST be reported");
        std::cout << "area_alloc B: boxed in -> " << got
                  << ", broke_contiguity reported\n";
    }

    // --- Arm C. STARTING A BLOCK IS NOT BREAKING ONE. ----------------------
    // A workspace with no members has no run to break. Same returned slot as
    // arm B; the DIFFERENCE IS THE FLAG, which is what this arm is for.
    {
        const std::uint64_t empty = table.create("NO_MEMBERS");
        broke = true;    // seeded WRONG
        const int got = cli::find_free_area_for_workspace(&eng, table, empty, broke);
        assert(got == 2 && "an empty workspace takes the lowest free slot");
        assert(!broke   && "a workspace with no run cannot have broken it");
        std::cout << "area_alloc C: empty workspace took " << got
                  << ", NOT reported as a break\n";
    }

    // --- Arm D. THE TABLE IS A PARAMETER. ----------------------------------
    // A SECOND table, same engine, same handle number, different members ->
    // different answer. Before the lift this could not be written at all: the
    // membership table was a process global the function reached for.
    {
        ws::WorkspaceTable other;
        const std::uint64_t h2 = other.create("BLOCK_AT_ZERO");
        assert(h2 == h && "both tables mint the same first handle -- that is the point");
        assert(other.join(h2, 0) == 0);
        broke = true;
        const int got = cli::find_free_area_for_workspace(&eng, other, h2, broke);
        assert(got == 2 && "slot 1 is taken, so this block cannot grow either");
        assert(broke    && "block at 0 boxed in by slot 1 -- reported");
        std::cout << "area_alloc D: same handle in a second table -> " << got
                  << " (the table is read, not a global)\n";
    }

    // --- Arm E. NO ENGINE, NO SLOT. ----------------------------------------
    // R3 -- failure travels in the return value. Note shell_engine() is null in
    // this binary, so the convenience wrapper must reach here too.
    {
        broke = true;
        const int got = cli::find_free_area_for_workspace(nullptr, table, h, broke);
        assert(got == -1 && "no engine, no answer");
        assert(!broke    && "a refusal is not a contiguity break");

        broke = true;
        const int shell = cli::find_free_area_for_current_workspace(broke);
        assert(shell == -1 && "the shell wrapper must refuse a null engine too");
        std::cout << "area_alloc E: null engine refused in the return value\n";
    }

    // --- Arm F. UNKNOWN IS TAKEN. ------------------------------------------
    // area_is_open_safe's bias, stated in its header comment, asserted here so
    // the comment is not the only thing holding it.
    {
        assert(cli::area_is_open_safe(nullptr, 0)              && "null engine -> taken");
        assert(cli::area_is_open_safe(&eng, -1)                && "negative slot -> taken");
        assert(cli::area_is_open_safe(&eng, xbase::MAX_AREA)   && "past the end -> taken");
        assert(cli::area_is_open_safe(&eng, 0)                 && "an open slot is taken");
        assert(!cli::area_is_open_safe(&eng, 2)                && "a free slot is free");
        std::cout << "area_alloc F: unknown counts as taken\n";
    }

    std::remove(kDbf);
    std::cout << "PASS: dottalkpp area allocator (IN FREE policy)\n";
    return 0;
}
