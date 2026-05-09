// @dottalk.usage v1
// owner: DOT|PRN
// command: PRN
// category: output
// status: supported
// noargs: report
// effect: configure
// mutates: output-router
// usage-access: PRN USAGE
// summary:
//   Report or configure the PRN output destination used by the output router.
//
// usage:
//   PRN
//   PRN USAGE
//   PRN STATUS
//   PRN SHOW
//   PRN OFF
//   PRN TO CONSOLE
//   PRN TO SCREEN
//   PRN TO FILE <path>
//   PRN TO PRINTER
//   PRN TO PRINTER <name>
//   PRN TO NULL
//
// notes:
//   PRN with no arguments reports current output routing status.
//   PRN USAGE prints usage and does not change routing.
//   PRN OFF and PRN TO NULL route PRN output to NULL.
//   PRN TO FILE opens/truncates or creates the destination as owned by OutputRouter.
//   PRN TO PRINTER is staged only; OS handoff is disabled.
//   PRN does not mutate table data.
//
// risk:
//   mutates_output_router: yes except status/usage
//   writes_files: PRN TO FILE
//   mutates_table_data: no
//
// related:
//   ECHO
//   SET ALTERNATE
//   SET PRINTER
//

#include "cli/cmd_prn.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>

#include "cli/output_router.hpp"
#include "xbase.hpp"

namespace {

static inline std::string trim_copy(std::string s)
{
    const auto not_space = [](unsigned char ch) { return std::isspace(ch) == 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
}

static inline std::string up_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static inline std::string rest(std::istringstream& iss)
{
    return std::string(std::istreambuf_iterator<char>(iss),
                       std::istreambuf_iterator<char>());
}

static void show_usage(std::ostream& out)
{
    out
        << "Usage:\n"
        << "  PRN\n"
        << "  PRN USAGE\n"
        << "  PRN STATUS\n"
        << "  PRN OFF\n"
        << "  PRN TO CONSOLE\n"
        << "  PRN TO FILE <path>\n"
        << "  PRN TO PRINTER [name]\n"
        << "  PRN TO NULL\n";
}

static void show_status(cli::OutputRouter& R, std::ostream& out)
{
    out << "PRN: " << R.describe_dest() << "\n";

    if (R.dest() == cli::OutputDest::File) {
        out << "  File       : " << R.prn_file_path() << "\n";
    } else if (R.dest() == cli::OutputDest::Printer) {
        if (R.prn_uses_default_printer()) {
            out << "  Printer    : (system default)\n";
        } else {
            out << "  Printer    : " << R.prn_printer_name() << "\n";
        }
        out << "  Printer job: staged only (OS handoff disabled)\n";
    }

    out << "  Alternate  : "
        << (R.alternate_on() ? ("ON -> " + R.alternate_to_path()) : "OFF")
        << "\n";

    out << "  Paging     : " << (R.paging_on() ? "ON" : "OFF") << "\n";
}

} // namespace

void cmd_PRN(xbase::DbArea&, std::istringstream& in)
{
    auto& R = cli::OutputRouter::instance();
    auto& out = R.out();

    std::string tok;
    if (!(in >> tok)) {
        show_status(R, out);
        return;
    }

    tok = up_copy(tok);

    if (tok == "USAGE" || tok == "HELP" || tok == "?") {
        show_usage(out);
        return;
    }

    if (tok == "STATUS" || tok == "SHOW") {
        show_status(R, out);
        return;
    }

    if (tok == "OFF") {
        R.console_note("PRN: NULL");
        R.set_dest_null();
        return;
    }

    if (tok != "TO") {
        show_usage(out);
        return;
    }

    std::string mode;
    if (!(in >> mode)) {
        show_usage(out);
        return;
    }

    mode = up_copy(mode);

    if (mode == "CONSOLE" || mode == "SCREEN") {
        R.set_dest_console();
        R.console_note("PRN: CONSOLE");
        return;
    }

    if (mode == "NULL" || mode == "OFF") {
        R.console_note("PRN: NULL");
        R.set_dest_null();
        return;
    }

    if (mode == "FILE") {
        std::string path = trim_copy(rest(in));
        if (path.empty()) {
            out << "Usage: PRN TO FILE <path>\n";
            return;
        }

        if (!R.set_dest_file(path)) {
            out << "PRN: failed to open file: " << path << "\n";
            return;
        }

        R.console_note("PRN: FILE -> " + R.prn_file_path());
        return;
    }

    if (mode == "PRINTER") {
        std::string printer_name = trim_copy(rest(in));

        if (!R.set_dest_printer(printer_name)) {
            out << "PRN: failed to configure printer destination.\n";
            return;
        }

        if (R.prn_uses_default_printer()) {
            R.console_note("PRN: PRINTER -> (system default) [staged only]");
        } else {
            R.console_note("PRN: PRINTER -> " + R.prn_printer_name() + " [staged only]");
        }
        return;
    }

    show_usage(out);
}
