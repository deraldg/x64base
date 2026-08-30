// @dottalk.file v1
// subsystem: cli
// layer: command
// owns:
// project: project.x64base.runtime
// lane: AIF-066
// owner: member.derald
// status: supported

// @dottalk.usage v1
// owner: DOT|AREA51
// command: AREA51
// category: diagnostics
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: AREA51 USAGE
// summary:
//   Report the current work-area slot and its cursor/order state WITHOUT
//   invoking the full AREA command and WITHOUT triggering relation refresh.
//
// usage:
//   AREA51
//
// notes:
//   AREA51 is a developer/debug status probe, not a member of the AREA family.
//   The name is a joke on the crowded AREA namespace (AREA, DBAREA, DBAREAS,
//   WA, WAMREPORT); it is deliberately NOT "AREA 51" and takes no arguments.
//   Unlike AREA it does NOT call relations_api::refresh_if_enabled(), which is
//   the entire point: it observes engine state without perturbing it. Use it
//   when a relation refresh would itself change what you are trying to look at.
//   Reports "(no file open)" rather than failing when the current area is empty.
//   Order/tag reporting is best-effort; a throwing order-state query is
//   swallowed and the remaining lines still print.
//
// risk:
//   reads_table_records: no
//   reads_engine_state: yes
//   mutates_table_data: no
//   mutates_cursor: no
//   triggers_relation_refresh: no
//
// related:
//   AREA
//   DBAREA
//   DBAREAS
//   WAMREPORT
//   STATUS
//   GPS
//

// Extracted from an inline lambda in src/cli/shell_commands.cpp on 2026-07-27
// (AIF-066 follow-on). Behaviour is byte-for-byte the same; only its home moved.
//
// WHY IT MOVED. AREA51 was registered inline, so it had no source file of its
// own and therefore no @dottalk.usage contract. Everything downstream of the
// contract is keyed on that: SYSCMD had no row for it, CMDHELP had no topic,
// and stack_audit's DOTREF_COV counted it among 55 "uncovered" dotref entries
// -- correctly, but for a reason no one could see from the catalog.
//
// The same structural gap produced DOT|SET LANGUAGE and DOT|SET LOCALE as
// orphaned locale-fixture topics, and lists REL ENUM / SET VAR in dotref.hpp
// with nowhere to resolve. A command handled inline in a parent's file is
// invisible to the documentation chain. Giving it a file gives it an identity.

#include "cli/shell_commands.hpp"

#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "cli/order_state.hpp"          // orderstate helpers

// Provided by the shell; the same accessor cmd_wamreport.cpp uses to reach
// engine state from a standalone command translation unit.
extern "C" xbase::XBaseEngine* shell_engine();

// Signature matches every other registry command for consistency. Both
// parameters are deliberately unused: AREA51 reports on the ENGINE's current
// area, not on whichever DbArea the dispatcher happened to hand over, and it
// takes no arguments.
void cmd_AREA51(DbArea&, std::istringstream&) {
    xbase::XBaseEngine* eng = shell_engine();
    if (!eng) {
        std::cout << "AREA51: engine unavailable\n";
        return;
    }

    const int i = eng->currentArea();
    DbArea& cur = eng->area(i);

    std::cout << "Current area: " << i << "\n";
    if (!cur.isOpen()) {
        std::cout << "  (no file open)\n";
        return;
    }

    std::cout << "  File: "   << cur.name()
              << "  Recs: "   << cur.recCount()
              << "  Recno: "  << cur.recno() << "\n";
    try {
        const bool asc = orderstate::isAscending(cur);
        const std::string idx = orderstate::hasOrder(cur)
                              ? orderstate::orderName(cur) : std::string("(none)");
        const std::string tag = orderstate::hasOrder(cur)
                              ? orderstate::activeTag(cur) : std::string("(none)");
        // AIF-148 residue: this line had NO ORDER PREDICATE AT ALL, so it read
        // the DIRECTION flag and printed it as the order.  isAscending()
        // deliberately defaults true when no order state exists, so a table
        // with no index reported ASCEND beside `Index file  : (none)` -- a
        // probe contradicting itself two lines apart.  The `Order: ASCEND`
        // with an empty index was OBSERVED on screen in the 2026-08-29 suite
        // run; WHICH of the residue sites emitted that particular line was
        // not pinned down, and this comment does not claim it was this one.
        // The defect here is read off the code and needs no transcript: there
        // is no order predicate on the line at all.
        //
        // A grep for hasOrder() could never find this site -- that is how it
        // survived the first residue sweep.  The question that finds it is
        // WHO PRINTS AN ORDER WORD.
        //
        // AREA51 is a HAND COPY of orderreport::print_area_report's format --
        // same three lines, same indents, same "(none)" -- which is why it did
        // not inherit that function's fix.  It keeps that function's word,
        // NATURAL.  Each site keeps its own vocabulary and only the PREDICATE
        // moves: STATUS says PHYSICAL, the tuple-stream hint says "physical",
        // this and the area report say NATURAL.
        //
        // hasOrder() still gates idx and tag above, correctly: those ask IS A
        // CONTAINER ATTACHED, and an attached .cdx with no tag has a filename
        // worth printing.
        std::cout << "  Order: "        << (orderstate::isNaturalOrder(cur)
                                            ? "NATURAL"
                                            : (asc ? "ASCEND" : "DESCEND")) << "\n"
                  << "  Index file  : " << idx << "\n"
                  << "  Active tag  : " << tag << "\n";
    } catch (...) {
        // Best-effort, as before: an order-state query that throws must not
        // cost the caller the area/record lines already printed.
    }
}
