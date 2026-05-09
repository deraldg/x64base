// src/cli/cmd_area.cpp
// @dottalk.usage v1
// owner: DOT|AREA
// command: AREA
// category: workspace
// status: supported
// noargs: report
// effect: report
// mutates: no
// usage-access: AREA USAGE
// summary:
//   Report the current work-area slot and current area file/session state.
//
// usage:
//   AREA
//   AREA USAGE
//
// notes:
//   AREA with no arguments reports the current work-area number, open file,
//   record count, current record, DBF flavor, runtime kind, logical name,
//   absolute path, and active order/index line.
//   AREA is read-only; it reports current area state and does not mutate table data.
//
// related:
//   DBAREA
//   DBAREAS
//   STATUS
//   STRUCT
//   WORKSPACE
//

#include <iostream>
#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>
#include <filesystem>

#include "xbase.hpp"
#include "xbase/area_kind_util.hpp"
#include "cli/order_state.hpp"
#include "cli/order_report.hpp"
#include "workspace/workarea_utils.hpp"

using namespace xbase;
namespace fs = std::filesystem;

// Provided by shell.cpp
extern "C" XBaseEngine* shell_engine();


static std::string area_upper(std::string s)
{
    std::transform(
        s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); }
    );
    return s;
}

static void print_area_usage()
{
    std::cout
        << "Usage:\n"
        << "  AREA                   (Report current work-area state)\n"
        << "  AREA USAGE             (Show this usage)\n"
        << "Notes:\n"
        << "  - AREA is read-only; it reports the current area slot/file/order state.\n";
}

static int resolve_current_index(DbArea& A)
{
    XBaseEngine* eng = shell_engine();
    if (!eng) return -1;

    for (int i = 0; i < MAX_AREA; ++i) {
        if (&eng->area(i) == &A) return i;
    }
    return -1;
}

static std::string area_file_label(const DbArea& A)
{
    std::string s = A.logicalName();
    if (!s.empty()) return s;

    s = A.dbfBasename();
    if (!s.empty()) return s;

    const std::string& f = A.filename();
    if (!f.empty()) {
        fs::path p(f);
        auto stem = p.stem().string();
        if (!stem.empty()) return stem;
    }

    return "(unknown)";
}

void cmd_AREA(DbArea& A, std::istringstream& args)
{
    const std::string raw = area_upper(args.str());
    if (raw.find("USAGE") != std::string::npos ||
        raw.find("HELP")  != std::string::npos ||
        raw.find("?")     != std::string::npos) {
        print_area_usage();
        return;
    }

    const int idx = resolve_current_index(A);

    if (idx >= 0)
        std::cout << "Current area: " << idx
                  << " of " << workareas::occupied_desc() << "\n";
    else
        std::cout << "Current area: (unknown)\n";

    if (!A.isOpen()) {
        std::cout << "  (no file open in Area)\n";
        return;
    }

    const std::string label = area_file_label(A);

    std::cout << "  File: " << label
              << "  Recs: " << A.recCount()
              << "  Recno: " << A.recno() << "\n";

    const std::string& abs = A.filename();
    std::cout << "  DBF (abs)           : " << (abs.empty() ? "(unknown)" : abs) << "\n";
    std::cout << "  DBF Flavor          : " << xbase::dbf_version_token(A.versionByte()) << "\n";
    std::cout << "  Runtime kind        : " << xbase::area_kind_token(A.kind()) << "\n";

    const std::string ln = A.logicalName();
    std::cout << "  Logical name        : " << (ln.empty() ? "(unknown)" : ln) << "\n";

    const std::string legacy = A.name();
    std::cout << "  Legacy name()       : " << (legacy.empty() ? "(unknown)" : legacy) << "\n";

    if (!abs.empty()) {
        std::cout << "  Path: " << abs << "\n";
    }

    orderreport::print_area_one_line(std::cout, A);
}
