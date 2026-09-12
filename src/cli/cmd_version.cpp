// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// @dottalk.usage v1
// owner: DOT|VERSION
// command: VERSION
// category: report
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: VERSION USAGE
// summary:
//   Report the DotTalk++ version label and build date/time.
//
// usage:
//   VERSION
//   VERSION USAGE
//
// notes:
//   VERSION with no arguments reports version and build information.
//   VERSION USAGE prints usage.
//   VERSION is read-only and does not mutate table data or session state.
//
// risk:
//   mutates_table_data: no
//   mutates_session: no
//
// related:
//   ABOUT
//   SQLVER
//

#include "cmd_version.hpp"
#include "cli/command_output.hpp"
#include "dottalk/build_stamp.hpp"
#include "dottalk/version.hpp"
#include "help/helpdata_messages.hpp"
#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>

// <chrono>, <filesystem>, <iomanip>, <vector> and the per-platform executable
// headers left with version_build_stamp() on 2026-09-11. <windows.h> in
// particular is why that implementation moved to a .cpp of its own: it defines
// min, max and several hundred other names into every TU that pulls it in, and
// this file no longer needs any of it.

namespace {
static std::string version_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string version_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_version_usage_request(const std::string& raw)
{
    std::string t = version_upper(version_trim(raw));
    if (t.rfind("VERSION ", 0) == 0) {
        t = version_upper(version_trim(t.substr(8)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_version_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::VersionUsageText);
}

// version_executable_path() and version_build_stamp() MOVED OUT, 2026-09-11.
// They now live in src/cli/build_stamp.cpp behind dottalk/build_stamp.hpp,
// because a regression log needs the same answer and two build stamps wearing
// one name is this tree's most repeated defect. The behaviour is unchanged:
// the running executable's mtime, formatted the same way, with the same
// __DATE__/__TIME__ fallback.
} // namespace

void cmd_VERSION(xbase::DbArea& area, std::istringstream& args) {
    (void)area;
    if (is_version_usage_request(args.str())) {
        print_version_usage();
        return;
    }

    const std::string stamp = dottalk::build_stamp();
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::VersionBannerLineText,
        {{"version", dottalk::version::display_version()}, {"stamp", stamp}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::VersionBuildLineText,
        {{"stamp", stamp}});
}
 


