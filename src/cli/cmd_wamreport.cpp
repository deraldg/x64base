// @dottalk.usage v1
// owner: DOT|WA
// command: WA
// category: diagnostics
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: WA USAGE
// summary:
//   Print the WorkAreaManager/engine bridge report and pointer identity checks.
//
// usage:
//   WA
//   WA USAGE
//
// examples:
//   WA
//   WA USAGE
//
// notes:
//   WA with no arguments prints the full WAM report.
//   WA USAGE prints usage without inspecting the WorkAreaManager bridge.
//   WA is read-only and does not mutate table data.
//
// risk:
//   reads_workspace_state: yes except usage
//   mutates_table_data: no
//
// related:
//   WSREPORT
//   AREA
//   WORKSPACE
//

#include "cli/cmd_wamreport.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "workspace/workarea_manager.hpp"

extern "C" xbase::XBaseEngine* shell_engine();

namespace
{


static std::string wamreport_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool wamreport_usage_request(std::istringstream& in)
{
    std::string tok;
    if (!(in >> tok)) {
        in.clear();
        in.seekg(0, std::ios::beg);
        return false;
    }

    const std::string u = wamreport_upper(tok);
    in.clear();
    in.seekg(0, std::ios::beg);
    return u == "USAGE" || u == "HELP" || u == "?";
}

static void print_wamreport_usage()
{
    std::cout
        << "Usage:\n"
        << "  WA\n"
        << "  WA USAGE\n"
        << "Notes:\n"
        << "  - WA prints the WorkAreaManager/engine bridge report.\n";
}

static inline bool open_truth(const xbase::DbArea& a)
{
    try {
        return !a.filename().empty();
    } catch (...) {
        return false;
    }
}

static std::string memo_kind_text(const xbase::DbArea& a)
{
    try {
        switch (a.memoKind()) {
            case xbase::DbArea::MemoKind::NONE: return "none";
            case xbase::DbArea::MemoKind::FPT:  return "fpt";
            case xbase::DbArea::MemoKind::DBT:  return "dbt";
            default:                            return "?";
        }
    } catch (...) {
        return "?";
    }
}

static std::string logical_name_text(const xbase::DbArea& a)
{
    try {
        const std::string s = a.logicalName();
        if (!s.empty()) return s;
    } catch (...) {}
    return "(empty)";
}

static std::string file_text(const xbase::DbArea& a)
{
    try {
        const std::string s = a.filename();
        if (!s.empty()) return s;
    } catch (...) {}
    return "(empty)";
}

static std::string ptr_text(const xbase::DbArea* p)
{
    std::ostringstream oss;
    oss << "0x"
        << std::uppercase
        << std::hex
        << reinterpret_cast<std::uintptr_t>(p);
    return oss.str();
}

} // namespace

void cmd_WAMREPORT(xbase::DbArea& /*A*/, std::istringstream& S)
{
    if (wamreport_usage_request(S)) {
        print_wamreport_usage();
        return;
    }

    using dottalk::workspace::WorkAreaManager;

    WorkAreaManager wam;
    xbase::XBaseEngine* eng = shell_engine();

    std::cout << "WAM Report\n";
    std::cout << "==========================================================================\n";

    if (!eng) {
        std::cout << "Engine               : (null)\n";
        std::cout << "Status               : FAIL - shell_engine() unavailable\n";
        return;
    }

    const int wam_count = wam.count();
    const int eng_current = [&]() -> int {
        try { return eng->currentArea(); } catch (...) { return -1; }
    }();
    const int wam_current = wam.current_slot();

    bool current_match = (eng_current == wam_current);
    bool identity_pass = true;
    int open_count = 0;

    std::cout << "Engine current area  : " << eng_current << "\n";
    std::cout << "WAM current area     : " << wam_current << "\n";
    std::cout << "WAM visible slots    : " << wam_count << "\n";
    std::cout << "Engine MAX_AREA      : " << xbase::MAX_AREA << "\n";
    if (xbase::MAX_AREA != wam_count) {
        std::cout << "Note                 : WAM is currently scoped to " << wam_count
                  << " slot(s), engine exposes " << xbase::MAX_AREA << ".\n";
    }

    std::cout << "--------------------------------------------------------------------------\n";
    std::cout << std::left
              << std::setw(4)  << "Cur"
              << std::setw(6)  << "Slot"
              << std::setw(6)  << "Open"
              << std::setw(18) << "Ptr"
              << std::setw(14) << "Logical"
              << std::setw(8)  << "Recno"
              << std::setw(6)  << "Memo"
              << std::setw(5)  << "X64"
              << "File\n";
    std::cout << "--------------------------------------------------------------------------\n";

    for (int i = 0; i < wam_count; ++i) {
        xbase::DbArea* p_wam = wam.dbarea(i);
        xbase::DbArea* p_eng = nullptr;

        try {
            p_eng = &eng->area(i);
        } catch (...) {
            p_eng = nullptr;
        }

        if (p_wam != p_eng) {
            identity_pass = false;
        }

        const bool is_current = (i == wam_current);
        const bool is_open = (p_wam != nullptr) && open_truth(*p_wam);
        if (is_open) ++open_count;

        std::string logical = "(empty)";
        std::string file = "(empty)";
        int recno = 0;
        std::string memo = "none";
        std::string x64 = "N";

        if (p_wam) {
            logical = logical_name_text(*p_wam);
            file = file_text(*p_wam);
            memo = memo_kind_text(*p_wam);
            try { recno = p_wam->recno(); } catch (...) { recno = 0; }
            try { x64 = (p_wam->versionByte() == 0x64) ? "Y" : "N"; } catch (...) { x64 = "?"; }
        }

        if (logical.size() > 13) logical.resize(13);

        std::cout << std::left
                  << std::setw(4)  << (is_current ? "*" : "")
                  << std::setw(6)  << i
                  << std::setw(6)  << (is_open ? "Y" : "N")
                  << std::setw(18) << (p_wam ? ptr_text(p_wam) : "(null)")
                  << std::setw(14) << logical
                  << std::right
                  << std::setw(8)  << recno
                  << std::setw(6)  << memo
                  << std::setw(5)  << x64
                  << "  " << file;

        if (p_wam != p_eng) {
            std::cout << "   [PTR MISMATCH]";
        }

        std::cout << "\n";
    }

    std::cout << "--------------------------------------------------------------------------\n";
    std::cout << "Open slots           : " << open_count << "\n";
    std::cout << "Current area match   : " << (current_match ? "PASS" : "FAIL") << "\n";
    std::cout << "Identity check       : " << (identity_pass ? "PASS" : "FAIL") << "\n";
    std::cout << "Status               : "
              << ((current_match && identity_pass) ? "OK" : "CHECK BRIDGE")
              << "\n";
    std::cout << "==========================================================================\n";
    std::cout.flush();
}
