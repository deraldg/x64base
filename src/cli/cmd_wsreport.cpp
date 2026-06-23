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
//   Print a workspace/status report covering open areas, LMDB/order summary,
//   and table-buffer state.
//
// usage:
//   WSREPORT
//   WSREPORT USAGE
//   WSREPORT ALL
//
// notes:
//   WSREPORT with no arguments reports the current workspace and current area.
//   WSREPORT ALL includes all open work areas in the area/index summary.
//   WSREPORT USAGE prints usage and does not inspect areas.
//   WSREPORT is read-only.
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

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xindex/index_manager.hpp"
#include "workareas.hpp"
#include "workspace/workarea_utils.hpp"
#include "index_summary.hpp"
#include "cli/order_report.hpp"
#include "cli/settings.hpp"
#include "cli/output_router.hpp"
#include "cli/path_resolver.hpp"
#include "cli/cmd_setpath.hpp"
#include "cli/table_state.hpp"

using dottalk::IndexSummary;

namespace {

// --------------------------------------------------
// HELPERS
// --------------------------------------------------

static std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool has_token(const std::string& hay, const char* tok) {
    return hay.find(tok) != std::string::npos;
}

static std::string trim_copy(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

static bool wsreport_usage_request(const std::string& raw)
{
    const std::string u = upper_copy(trim_copy(raw));
    return u == "USAGE" || u == "HELP" || u == "?";
}

static void print_wsreport_usage(std::ostream& os)
{
    os << "Usage:\n"
       << "  WSREPORT\n"
       << "  WSREPORT USAGE\n"
       << "  WSREPORT ALL\n"
       << "Notes:\n"
       << "  - WSREPORT prints workspace, order/LMDB, table-buffer, and area summaries.\n"
       << "  - WSREPORT ALL includes all open work areas.\n";
}

static std::string basename_of(const std::string& path) {
    try { return std::filesystem::path(path).filename().string(); }
    catch (...) { return path; }
}

static std::string nz(const std::string& s, const char* empty = "(none)") {
    return s.empty() ? std::string(empty) : s;
}

static std::string safe_area_label(const workareas::WorkArea& wa) {
    try { return wa.label(); } catch (...) { return {}; }
}

static std::string safe_area_filename(const workareas::WorkArea& wa) {
    try { return wa.file_name(); } catch (...) { return {}; }
}

static bool same_slot(const workareas::WorkArea& a,
                      const workareas::WorkArea& b) noexcept {
    return a.slot() == b.slot();
}

static void print_kv(std::ostream& os, const char* k, const std::string& v) {
    os << "  " << std::left << std::setw(18) << k << ": " << v << "\n";
}

static std::string capacity_desc() {
    std::ostringstream out;
    const std::size_t n = workareas::count();
    if (n == 0) out << "{}";
    else out << "{0.." << (n - 1) << "}";
    return out.str();
}

// --------------------------------------------------
// WORKSPACE BLOCK
// --------------------------------------------------

static void print_workspace_block(std::ostream& os) {
    const auto areas = workareas::all();
    const auto* cur  = workareas::current();

    os << "Workspace\n";
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

static void print_lmdb_block(std::ostream& os) {
    const auto areas = workareas::all();
    const auto* cur  = workareas::current();

    for (auto* wa : areas) {
        if (!wa || !wa->is_open()) continue;

        xbase::DbArea* A = wa->get();
        if (!A) continue;

        const auto* im = A->indexManagerPtr();
        if (!im || !im->hasBackend() || !im->isCdx()) continue;

        os << "Area " << wa->slot();
        if (cur && same_slot(*wa, *cur)) os << " [current]";
        os << "\n";

        print_kv(os, "FILE", nz(safe_area_filename(*wa)));
        print_kv(os, "TAG",  nz(im->activeTag()));
        os << "\n";
    }
}

// --------------------------------------------------
// TABLE BUFFER BLOCK
// --------------------------------------------------

static std::size_t unique_recnos_in_tb(const dottalk::table::TableBuffer& tb) {
    std::set<int> recnos;
    for (const auto& pair : tb.changes) {
        recnos.insert(pair.first);
    }
    return recnos.size();
}

static void print_table_buffer_block(std::ostream& os) {
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

static void print_area_index_block(std::ostream& os,
                                   const workareas::WorkArea& wa,
                                   bool isCurrent,
                                   bool /*verbose*/) {
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

static std::string wsreport_usage_upper_hotfix(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static bool wsreport_usage_request_hotfix(std::istringstream& args)
{
    std::string tok;
    if (!(args >> tok)) {
        args.clear();
        args.seekg(0, std::ios::beg);
        return false;
    }

    const std::string u = wsreport_usage_upper_hotfix(tok);
    args.clear();
    args.seekg(0, std::ios::beg);

    return u == "USAGE" || u == "HELP" || u == "?";
}

static void print_wsreport_usage_hotfix()
{
    std::cout
        << "Usage:\n"
        << "  WSREPORT\n"
        << "  WSREPORT USAGE\n"
        << "  WSREPORT ALL\n"
        << "Notes:\n"
        << "  - WSREPORT prints workspace, order/LMDB, table-buffer, and area summaries.\n"
        << "  - WSREPORT ALL includes all open work areas.\n";
}
void cmd_WSREPORT(xbase::DbArea&, std::istringstream& args) {
    if (wsreport_usage_request_hotfix(args)) {
        print_wsreport_usage_hotfix();
        return;
    }
    auto& out = cli::OutputRouter::instance().out();

    const std::string arg_text = args.str();
    if (wsreport_usage_request(arg_text)) {
        print_wsreport_usage(out);
        out.flush();
        return;
    }

    const std::string raw = upper_copy(arg_text);
    const bool wantAll = has_token(raw, "ALL");

    const auto areas = workareas::all();
    const auto* cur  = workareas::current();

    out << "DotTalk Status Report\n\n";

    print_workspace_block(out);
    print_lmdb_block(out);
    print_table_buffer_block(out);

    out << "Areas / Index Summary\n";
    out << "----------------------------------------\n";

    if (wantAll) {
        for (auto* wa : areas) {
            if (!wa || !wa->is_open()) continue;
            print_area_index_block(out, *wa,
                cur && same_slot(*wa, *cur),
                false);
        }
    } else {
        if (cur && cur->is_open()) {
            print_area_index_block(out, *cur, true, false);
        } else {
            out << "(no current area)\n";
        }
    }

    out.flush();
}