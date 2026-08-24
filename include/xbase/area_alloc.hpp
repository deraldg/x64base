// @dottalk.file v1
// subsystem: xbase
// layer: header
// owns:
// project: project.x64base.runtime
// lane: application-ui-dsl
// owner: member.derald
// status: supported

#pragma once
// @dottalk.contract
// file: include/xbase/area_alloc.hpp
// subsystem: xbase
// role: IN FREE -- which engine slot a workspace should open into
// authority: canonical-header-contract
// mutation: token-authorized
//
// TOKEN for the 2026-08-23 creation: AIF-078 slot lane, steward ruling in
// session -- "unblock step 2 with me", then the allocator placed in xbase
// against the three alternatives (grow the GUI's cherry-pick list, retire the
// cherry-picks wholesale, or rule the whole seam first). See
// claude/AIF078_FINDING_GUI_CANNOT_REACH_THE_ALLOCATOR.md.

// WHY THIS LIVES IN xbase, AND NOT IN cli WHERE IT WAS BORN.
//
// The policy was lifted out of cmd_use.cpp into src/cli/workarea_util.cpp on
// 2026-08-23 (slot lane step 1) and that was the wrong home, for a reason
// nobody had measured: `dottalk_gui_core` cannot link it. The GUI compiles two
// CLI translation units into its own library and workarea_util is not one of
// them; adding it does not work either, because workarea_util.o needs THREE
// shell symbols -- cli::cmdout::print_line, workareas::shell_engine, and
// ::shell_engine -- and `grep -rn shell_engine src/gui/` returns NOTHING. The
// GUI process has no such function, which is the very reason
// Session::Impl::Area holds a DbArea BY VALUE and the reason the slot lane
// exists at all.
//
// NONE OF THOSE THREE SYMBOLS BELONGS TO THE POLICY. They come from the
// ambiguity ledger and the work-area array walk that share the translation
// unit. The functions below depend on xbase.hpp and workspace_membership.hpp
// and nothing else. They were not stuck because of what they do; they were
// stuck because of their ROOMMATES.
//
// The measurement that settled the placement: the two files the GUI already
// cherry-picks -- order_iterator.cpp and order_state.cpp -- have no shell
// dependency either. order_state.cpp includes five std headers and xbase.hpp.
// That list is not the GUI reaching into the shell; it is a list of ENGINE CODE
// FILED UNDER src/cli, and the cherry-pick is how the GUI reaches code that was
// never shell code. Placing the allocator here rather than beside them keeps
// that list from growing by a third hand-maintained entry -- the
// enumeration-by-convention trap WORKSPACE WRITEBACK already paid for.
//
// It is also where the array is. The free slot is a position in
// XBaseEngine::_areas, DbArea::open() already registers workspace membership
// from inside xbase for the choke-point reason workspace_membership.hpp gives,
// and allocation and registration are two halves of one act. Both consumers
// already link xbase, so neither needs a build change: src/xbase/CMakeLists.txt
// globs its sources, and dottalk_gui_core links xbase PUBLIC.
//
// WHAT STAYED BEHIND, deliberately: cli::find_free_area_for_current_workspace,
// in workarea_util. That one calls shell_engine() and the process-global
// membership table, so it IS shell code -- it is the shell's spelling of the
// question, and cmd_use.cpp's single call site did not move again.

#include <cstdint>

#include "xbase.hpp"
#include "xbase/workspace_membership.hpp"

namespace xbase {

// Is engine slot `slot` occupied? UNKNOWN COUNTS AS TAKEN -- a null engine, an
// out-of-range index, or a throwing area() all answer true, so an allocator
// built on this can never hand out a slot it failed to inspect. That bias is
// the whole point of the name: it is not "is open", it is "is open, safely".
bool area_is_open_safe(XBaseEngine* eng, int slot);

// IN FREE -- an unoccupied area, chosen for the workspace `handle` names.
//
// NAMED FREE AND NOT NEXT (owner ruling 2026-08-22): NEXT implies forward
// adjacency and this may return a slot BEHIND the cursor. A name that promises
// an order the code does not keep is worse than no name.
//
// WORKSPACE-SCOPED, AND THAT IS THE POINT (owner ruling 2026-08-22, "scoped").
// The first cut swept 0..MAX_AREA globally, which with one workspace open is
// indistinguishable from correct and stops being so the moment there are two:
// a global sweep hands out the lowest free ENGINE slot, and that slot can sit
// INSIDE ANOTHER WORKSPACE'S RUN. The owner's design rule for this lane is
// that a workspace's areas stay contiguous -- "keep the areas contiguous",
// fractal to the same rule for tables under one root -- so an allocator that
// can drop an area into the middle of a neighbour's block is a contiguity
// violation armed and waiting.
//
// So: GROW MY OWN BLOCK FIRST. If this workspace already holds areas, the slot
// after its highest member keeps the run unbroken. Only when that is taken do
// we fall back to the lowest free slot anywhere -- and we SAY SO, because a
// silently broken invariant is the shape this whole lane exists to remove.
// `broke_contiguity` carries that fact back to the caller rather than printing
// from down here, so the message lands with the rest of the caller's output.
//
// THE ENGINE AND THE TABLE ARE PARAMETERS, not things this function reaches
// for. Returns -1 when nothing is free.
int find_free_area_for_workspace(XBaseEngine* eng,
                                 workspace::WorkspaceTable& table,
                                 std::uint64_t handle,
                                 bool& broke_contiguity);

} // namespace xbase
