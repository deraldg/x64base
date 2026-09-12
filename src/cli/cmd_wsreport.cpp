// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// ================================
// FILE: src/cli/cmd_wsreport.cpp
// ================================

// @dottalk.usage v1
// owner: DOT|WSREPORT
// command: WSREPORT
// category: diagnostics
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: WSREPORT USAGE
// summary:
//   Print a session status report: open workspaces and their areas, the
//   order/LMDB summary, table-buffer state, and per-area index detail.
//
// usage:
//   WSREPORT
//   WSREPORT USAGE
//   WSREPORT ALL
//
// notes:
//   WSREPORT with no arguments reports the whole desk and the current area.
//   WSREPORT ALL includes every open work area in the area/index summary.
//   WSREPORT USAGE prints usage and inspects nothing.
//   WSREPORT is read-only. It reports an invariant violation; it repairs none.
//   The WORKSPACES section names workspaces. Until 2026-09-11 a section headed
//   `Workspace` showed only work-area slots and never called the workspace
//   table, so it read identically whether every area sat in DEFAULT or was
//   spread across five named workspaces. That block is now `Work Areas`, which
//   is what it always was.
//
// risk:
//   reads_workspace_state: yes except usage
//   writes_console: yes
//   mutates_table_data: no
//
// related:
//   AREA
//   STATUS
//   WORKSPACE
//
// THE WORKSPACE LEVEL IS NOT COMPUTED HERE, and that is the change.
// `cli::workdesk::observe()` walks the workspace table and the engine's areas
// and returns the join; `cli::workdesk::render()` prints it. This file routes
// output and owns the three blocks that are genuinely its own. Before that
// split, three places each built the same workspace/area pairing privately --
// cmd_workspace.cpp inline, this file (badly, by omitting it), and
// cli::AmbiguityHit, whose ws_handles/engine_slots pair IS this join under
// another name. A fourth private walk is the thing to avoid, not a fourth
// report.

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <limits>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xindex/index_manager.hpp"
#include "xindex/attach.hpp"
#include "workareas.hpp"
#include "workspace/workarea_utils.hpp"
#include "index_summary.hpp"
#include "cli/order_report.hpp"
#include "cli/settings.hpp"
#include "cli/output_router.hpp"
#include "cli/path_resolver.hpp"
#include "cli/cmd_setpath.hpp"
#include "cli/table_state.hpp"
#include "cli/cmd_workdesk.hpp"

using dottalk::IndexSummary;

namespace {

// --------------------------------------------------
// HELPERS
// --------------------------------------------------

std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

// Kept: the argument path no longer needs it, but removing a helper in the
// same change that fixes a live regression widens the diff for no gain.
[[maybe_unused]] std::string trim_copy(std::string s) {
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

// ARGUMENTS ARE TOKENS, NOT A SUBSTRING SEARCH.
//
// The old test was `raw.find("ALL") != npos` over the whole argument text, so
// any argument CONTAINING those three letters turned ALL mode on -- `WSREPORT
// FALLBACK` enabled it, silently, because F-A-L-L-B-A-C-K contains ALL. A
// report that quietly answers a question nobody asked is the defect this file
// is being rewritten to stop committing.
// THE ARGUMENT STREAM IS PAST THE VERB; ITS BUFFER IS NOT.
//
// shell_api.cpp builds one istringstream over the whole line, reads the verb
// out of it, and hands the SAME stream to the handler -- so `args >> tok`
// yields the first ARGUMENT, while `args.str()` yields the WHOLE LINE with the
// verb still on the front.
//
// This has now cost twice. cmd_wsreport.cpp carried two usage checks: a
// `_hotfix` pair reading the stream (which worked) and a router-bound pair
// comparing args.str() to "USAGE" (which could not). On 2026-09-11 the two
// were "consolidated" onto the buffer -- the broken half -- and WSREPORT USAGE
// stopped working; WORKDESK USAGE was written the same way the same hour and
// answered "unknown argument 'workdesk'" on its first run. The duplicate was
// real, and the copy that was kept was the wrong one.
//
// Read the STREAM. Never the buffer.
std::vector<std::string> tokens_upper(std::istringstream& args) {
    std::vector<std::string> out;
    std::string tok;
    while (args >> tok) out.push_back(upper_copy(tok));
    return out;
}

bool has_word(const std::vector<std::string>& toks, const char* word) {
    return std::find(toks.begin(), toks.end(), std::string(word)) != toks.end();
}

std::string basename_of(const std::string& path) {
    try { return std::filesystem::path(path).filename().string(); }
    catch (...) { return path; }
}

std::string nz(const std::string& s, const char* empty = "(none)") {
    return s.empty() ? std::string(empty) : s;
}

std::string safe_area_label(const workareas::WorkArea& wa) {
    try { return wa.label(); } catch (...) { return {}; }
}

std::string safe_area_filename(const workareas::WorkArea& wa) {
    try { return wa.file_name(); } catch (...) { return {}; }
}

bool same_slot(const workareas::WorkArea& a,
               const workareas::WorkArea& b) noexcept {
    return a.slot() == b.slot();
}

void print_kv(std::ostream& os, const char* k, const std::string& v) {
    os << "  " << std::left << std::setw(18) << k << ": " << v << "\n";
}

std::string capacity_desc() {
    std::ostringstream out;
    const std::size_t n = workareas::count();
    if (n == 0) out << "{}";
    else        out << "{0.." << (n - 1) << "}";
    return out.str();
}

// --------------------------------------------------
// USAGE -- ONE COPY, ONE PATH
//
// There were two: a router-bound pair and a `_hotfix` pair that ran FIRST and
// wrote to std::cout directly, bypassing OutputRouter -- so the same text was
// captured or not depending on which copy answered. Two declarations of one
// string is the drift this house keeps paying for; the console-only one is
// gone, and every byte below leaves through the router.
// --------------------------------------------------

bool usage_requested(const std::vector<std::string>& toks) {
    if (toks.empty()) return false;
    const std::string& u = toks.front();
    return u == "USAGE" || u == "HELP" || u == "?";
}

void print_usage(std::ostream& os) {
    os << "Usage:\n"
       << "  WSREPORT\n"
       << "  WSREPORT USAGE\n"
       << "  WSREPORT ALL\n"
       << "Notes:\n"
       << "  - WSREPORT prints workspaces, order/LMDB, table-buffer, and area summaries.\n"
       << "  - WSREPORT ALL includes all open work areas.\n";
}

// --------------------------------------------------
// WORK AREAS BLOCK
//
// Renamed from `Workspace`, which is what it was called while containing no
// workspace. The CONTENT was never wrong -- occupied slots, open count,
// capacity, current slot and the slot table are all area facts, correctly
// reported. Only the heading lied.
// --------------------------------------------------

void print_work_areas_block(std::ostream& os) {
    const auto areas = workareas::all();
    const auto* cur  = workareas::current();

    os << "Work Areas\n";
    os << "----------------------------------------\n";
    os << "  Occupied: " << workareas::occupied_desc() << "\n";
    os << "  Open     : " << workareas::open_count() << "\n";
    os << "  Capacity : " << capacity_desc() << "\n";
    os << "  Current  : "
       << (cur && cur->is_open() ? std::to_string(cur->slot()) : "(none)")
       << "\n\n";

    for (auto* wa : areas) {
        if (!wa || !wa->is_open()) continue;

        os << "  "
           << wa->slot() << " "
           << (cur && same_slot(*wa, *cur) ? "*" : " ")
           << " "
           << nz(safe_area_label(*wa))
           << " "
           << nz(basename_of(safe_area_filename(*wa)))
           << "\n";
    }

    os << "\n";
}

// --------------------------------------------------
// LMDB BLOCK
// --------------------------------------------------

void print_lmdb_block(std::ostream& os) {
    os << "Order / Index\n";
    os << "----------------------------------------\n";
#if DOTTALK_HAS_XINDEX
    const auto areas = workareas::all();
    const auto* cur  = workareas::current();

    bool any = false;

    for (auto* wa : areas) {
        if (!wa || !wa->is_open()) continue;

        xbase::DbArea* A = wa->get();
        if (!A) continue;

        const auto* im = xindex::manager_if_attached(*A);
        if (!im || !im->hasBackend() || !im->isCdx()) continue;

        any = true;

        os << "Area " << wa->slot();
        if (cur && same_slot(*wa, *cur)) os << " [current]";
        os << "\n";

        print_kv(os, "FILE", nz(safe_area_filename(*wa)));
        print_kv(os, "TAG",  nz(im->activeTag()));
        os << "\n";
    }

    // SAYS SO. This block printed NOTHING when no area had an attached CDX
    // manager -- a silent empty section, which reads exactly like a section
    // that ran and found everything in order.
    if (!any) {
        os << "  (no area has an attached CDX index)\n\n";
    }
#else
    os << "  Index engine: not compiled (table-only build)\n\n";
#endif
}

// --------------------------------------------------
// TABLE BUFFER BLOCK
// --------------------------------------------------

std::size_t unique_recnos_in_tb(const dottalk::table::TableBuffer& tb) {
    std::set<std::uint64_t> recnos;
    for (const auto& pair : tb.changes) {
        recnos.insert(pair.first);
    }
    return recnos.size();
}

void print_table_buffer_block(std::ostream& os) {
    using namespace dottalk::table;

    const int enabled = count_enabled();
    const int dirty   = count_dirty();
    const int stale   = count_stale();

    os << "Table Buffer\n";
    os << "----------------------------------------\n";
    os << "  enabled : " << enabled << "\n";
    os << "  dirty   : " << dirty << "\n";
    os << "  stale   : " << stale << "\n\n";

    const auto areas = workareas::all();
    const auto* cur  = workareas::current();

    bool any_detail = false;

    for (auto* wa : areas) {
        if (!wa || !wa->is_open()) continue;

        const auto slot = wa->slot();
        if (slot > static_cast<decltype(slot)>(std::numeric_limits<int>::max())) {
            continue;
        }

        const int a = static_cast<int>(slot);
        if (!is_enabled(a) && !is_dirty(a) && !is_stale(a)) {
            continue;
        }

        any_detail = true;

        os << "  Area " << a;
        if (cur && same_slot(*wa, *cur)) os << " [current]";
        os << "\n";

        os << "    buffer : " << (is_enabled(a) ? "ON" : "OFF")
           << " | " << (is_dirty(a) ? "DIRTY" : "clean")
           << " | " << (is_stale(a) ? "STALE" : "fresh");

        const auto& tb = get_tb_const(a);
        if (!tb.empty()) {
            os << " | changes: " << tb.changes.size()
               << " (" << unique_recnos_in_tb(tb) << " recnos)";
        }

        os << "\n";
    }

    if (!any_detail) {
        os << "  (no active table buffer state)\n";
    }

    os << "\n";
}

// --------------------------------------------------
// AREA INDEX BLOCK
// --------------------------------------------------

void print_area_index_block(std::ostream& os,
                            const workareas::WorkArea& wa,
                            bool isCurrent) {
    const xbase::DbArea* A = wa.get();
    if (!A) return;

    os << "Area " << wa.slot();
    if (isCurrent) os << " [current]";
    os << "\n";

    print_kv(os, "FILE", nz(wa.file_name()));
    print_kv(os, "Records", std::to_string(A->recCount()));
    print_kv(os, "Recno", std::to_string(A->recno()));
    os << "\n";
}

} // namespace

// --------------------------------------------------
// COMMAND
// --------------------------------------------------

void cmd_WSREPORT(xbase::DbArea&, std::istringstream& args) {
    auto& out = cli::OutputRouter::instance().out();

    const std::vector<std::string> toks = tokens_upper(args);

    if (usage_requested(toks)) {
        print_usage(out);
        out.flush();
        return;
    }

    const bool wantAll = has_word(toks, "ALL");

    out << "DotTalk Status Report\n\n";

    // The desk is observed ONCE and rendered ONCE. Nothing below re-walks the
    // workspace table.
    const cli::workdesk::Desk desk = cli::workdesk::observe();
    cli::workdesk::render(desk, out);

    print_work_areas_block(out);
    print_lmdb_block(out);
    print_table_buffer_block(out);

    out << "Areas / Index Summary\n";
    out << "----------------------------------------\n";

    const auto areas = workareas::all();
    const auto* cur  = workareas::current();

    if (wantAll) {
        for (auto* wa : areas) {
            if (!wa || !wa->is_open()) continue;
            print_area_index_block(out, *wa, cur && same_slot(*wa, *cur));
        }
    } else {
        if (cur && cur->is_open()) {
            print_area_index_block(out, *cur, true);
        } else {
            out << "(no current area)\n";
        }
    }

    out.flush();
}
